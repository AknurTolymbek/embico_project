"""
Модель 2: time-lapse морфокинетика + исследовательский ранг бластоцисты.

Перенос analyze_embryo из ml-model/time-lapse-last-version.ipynb (v0.4):
  кадры (3 фокальные плоскости → RGB) → ConvNeXt-Tiny (+ TTA flip)
  → [BiGRU] → HMM/Витерби (только переходы вперёд) → времена событий
  → коррекция смещения → морфокинетика → флаги вне нормы
  → классификатор бластоцисты (только при видео >= 72 ч).

numpy/pandas/torch/timm/joblib импортируются внутри функций.
"""
from __future__ import annotations

import io
import json
import logging
import math
from pathlib import Path
from typing import Any, Sequence

from app.ml import constants as C

logger = logging.getLogger(__name__)

_BATCH = 32


# ---------------------------------------------------------------------------
# Чистые функции (numpy) — 1-в-1 из ноутбука
# ---------------------------------------------------------------------------
def viterbi(P, logA, lam: float = 1.0, eps: float = 1e-6):
    """Декодирование Витерби: стадии могут только идти вперёд (верхнетреугольная матрица)."""
    import numpy as np

    T, k = P.shape
    L = np.log(P + eps)
    forbid = np.where(np.triu(np.ones((k, k))) > 0, 0.0, -np.inf)
    trans = lam * logA + forbid
    D = L[0].copy()
    B = np.zeros((T, k), dtype=int)
    for t in range(1, T):
        S = D[:, None] + trans
        B[t] = S.argmax(0)
        D = S.max(0) + L[t]
    path = np.zeros(T, dtype=int)
    path[-1] = int(D.argmax())
    for t in range(T - 1, 0, -1):
        path[t - 1] = B[t, path[t]]
    return path


def events_from_path(path, hours) -> dict[str, float]:
    """Время (ч) первого кадра каждой стадии."""
    import numpy as np

    ev: dict[str, float] = {}
    for k in range(C.K):
        idx = np.where(path == k)[0]
        if len(idx):
            ev[C.PHASES[k]] = float(hours[idx[0]])
    return ev


def correct(ev: dict[str, float], bias: dict[str, float]) -> dict[str, float]:
    """Вычитаем систематическое смещение модели по событиям."""
    return {k: v - bias.get(k, 0.0) for k, v in ev.items()}


def morpho(ev: dict[str, float], until: float = math.inf) -> dict[str, float]:
    """Морфокинетические признаки по событиям до момента until."""
    nan = float("nan")
    e = {k: v for k, v in ev.items() if v <= until}
    g = lambda k: e.get(k, nan)  # noqa: E731
    f = {k: g(k) for k in ("t2", "t3", "t4", "t5", "t8")}
    f.update(
        cc2=f["t3"] - f["t2"],
        s2=f["t4"] - f["t3"],
        s3=f["t8"] - f["t5"],
        t5_t2=f["t5"] - f["t2"],
        stage_reached=float(max((C.PIDX[k] for k in e if k in C.PIDX), default=-1)),
    )
    return f


def flags(f: dict[str, float], ref: dict[str, tuple[float, float]]) -> list[str]:
    """Отклонения от референсных диапазонов (p05–p95)."""
    out = []
    for k, (lo, hi) in ref.items():
        v = f.get(k, float("nan"))
        if not math.isnan(v) and not (lo <= v <= hi):
            out.append(f"{k} = {v:.1f} ч вне нормы ({lo:.1f}–{hi:.1f} ч)")
    cc2 = f.get("cc2", float("nan"))
    if not math.isnan(cc2) and cc2 < 5:
        out.append(C.MSG_DIRECT_CLEAVAGE)
    return out


def _nan_to_none(x: float) -> float | None:
    return None if x is None or math.isnan(x) else round(float(x), 1)


# ---------------------------------------------------------------------------
# BiGRU (лениво, нужен torch)
# ---------------------------------------------------------------------------
def _build_seq_model(d_in: int, k: int, h: int = 192):
    import torch
    from torch import nn
    from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

    class SeqModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.inp = nn.Sequential(nn.LayerNorm(d_in), nn.Dropout(0.3), nn.Linear(d_in, h), nn.GELU())
            self.gru = nn.GRU(h + 1, h, num_layers=2, batch_first=True, bidirectional=True, dropout=0.2)
            self.out = nn.Sequential(nn.Dropout(0.2), nn.Linear(2 * h, k))

        def forward(self, x, hrs, lens):
            z = torch.cat([self.inp(x), (hrs / 100.0).unsqueeze(-1)], -1)
            packed = pack_padded_sequence(z, lens.cpu(), batch_first=True, enforce_sorted=False)
            o, _ = self.gru(packed)
            o, _ = pad_packed_sequence(o, batch_first=True, total_length=x.shape[1])
            return self.out(o)

    return SeqModel()


# ---------------------------------------------------------------------------
# Загрузка вспомогательных файлов
# ---------------------------------------------------------------------------
def _load_ref(path: Path) -> dict[str, tuple[float, float]]:
    if not path.is_file():
        return dict(C.DEFAULT_REF)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {k: (float(v["p05"]), float(v["p95"])) for k, v in raw.items()}


def _load_bias(path: Path) -> dict[str, float]:
    if not path.is_file():
        return dict(C.DEFAULT_BIAS)
    return {k: float(v) for k, v in json.loads(path.read_text(encoding="utf-8")).items()}


def _load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


ImageLike = Any  # PIL.Image.Image | bytes


class TimelapsePredictor:
    """Модель time-lapse, загруженная в память."""

    def __init__(
        self,
        cnn,
        seq,
        logA,
        clf,
        ref: dict[str, tuple[float, float]],
        bias: dict[str, float],
        best_model: str,
        lam: float,
        train_scores,
        device: str,
        model_version: str = C.TL_MODEL_VERSION,
        early_hours: float = C.TL_EARLY_HOURS,
        img_size: int = C.TL_IMG_SIZE,
    ) -> None:
        self.cnn = cnn
        self.seq = seq
        self.logA = logA
        self.clf = clf
        self.ref = ref
        self.bias = bias
        self.best_model = best_model
        self.lam = lam
        self.train_scores = train_scores
        self.device = device
        self.model_version = model_version
        self.early_hours = early_hours
        self.img_size = img_size
        self._transform = self._make_transform(img_size)

    # ------------------------------------------------------------------ load
    @classmethod
    def load(cls, models_dir: Path, device: str = "cpu") -> "TimelapsePredictor":
        import joblib
        import numpy as np
        import timm
        import torch

        required = [C.TL_FILE_CNN, C.TL_FILE_LOGA, C.TL_FILE_CLF]
        missing = [f for f in required if not (models_dir / f).is_file()]
        if missing:
            raise FileNotFoundError(f"Не найдены файлы time-lapse модели в {models_dir}: {', '.join(missing)}")

        cfg = _load_config(models_dir / C.TL_FILE_CONFIG)
        backbone = cfg.get("backbone", C.TL_BACKBONE)
        best_model = cfg.get("best_model", C.LABEL_CNN_HMM)
        lam_cfg = cfg.get("lambda", {})
        lam_key = "ConvNeXt+BiGRU" if best_model == C.LABEL_CNN_GRU_HMM else "ConvNeXt"
        lam = float(lam_cfg.get(lam_key, 1.0)) if isinstance(lam_cfg, dict) else float(lam_cfg)

        cnn = timm.create_model(backbone, pretrained=False, num_classes=C.K)
        cnn.load_state_dict(torch.load(models_dir / C.TL_FILE_CNN, map_location=device))
        cnn.to(device).eval()

        seq = None
        if best_model == C.LABEL_CNN_GRU_HMM:
            gru_path = models_dir / C.TL_FILE_GRU
            if not gru_path.is_file():
                raise FileNotFoundError(f"Конфиг требует BiGRU, но нет файла {gru_path}")
            state = torch.load(gru_path, map_location=device)
            h, d_in = state["inp.2.weight"].shape
            seq = _build_seq_model(int(d_in), C.K, int(h))
            seq.load_state_dict(state)
            seq.to(device).eval()

        train_scores = None
        ts_path = models_dir / C.TL_FILE_TRAIN_SCORES
        if ts_path.is_file():
            train_scores = np.sort(np.load(ts_path))

        logger.info("Time-lapse модель загружена: %s, lambda=%.2f", best_model, lam)
        return cls(
            cnn=cnn,
            seq=seq,
            logA=np.load(models_dir / C.TL_FILE_LOGA),
            clf=joblib.load(models_dir / C.TL_FILE_CLF),
            ref=_load_ref(models_dir / C.TL_FILE_REF),
            bias=_load_bias(models_dir / C.TL_FILE_BIAS),
            best_model=best_model,
            lam=lam,
            train_scores=train_scores,
            device=device,
            model_version=cfg.get("model_version", C.TL_MODEL_VERSION),
            early_hours=float(cfg.get("early_hours", C.TL_EARLY_HOURS)),
            img_size=int(cfg.get("img_size", C.TL_IMG_SIZE)),
        )

    # ------------------------------------------------------------ preprocess
    @staticmethod
    def _make_transform(s: int):
        import torchvision.transforms as T

        return T.Compose([
            T.Resize(int(s * 1.12)),
            T.CenterCrop(s),
            T.ToTensor(),
            T.Normalize(C.IMAGENET_MEAN, C.IMAGENET_STD),
        ])

    def _gray(self, src: ImageLike, size: tuple[int, int] | None = None):
        """load_gray из ноутбука: быстрое декодирование в оттенки серого."""
        from PIL import Image

        im = Image.open(io.BytesIO(src)) if isinstance(src, (bytes, bytearray)) else src
        s = int(self.img_size * 1.2)
        try:
            im.draft("L", (s, s))
        except Exception:  # draft есть не у всех форматов
            pass
        im = im.convert("L")
        if size is not None and im.size != size:
            im = im.resize(size)
        return im

    def _frame(self, f0: ImageLike, fm: ImageLike | None, fp: ImageLike | None):
        """RGB = [F-, F0, F+]; если боковых плоскостей нет — используем F0."""
        from PIL import Image

        c = self._gray(f0)
        m = self._gray(fm, c.size) if fm is not None else c
        p = self._gray(fp, c.size) if fp is not None else c
        return Image.merge("RGB", [m, c, p])

    # ---------------------------------------------------------------- infer
    def _infer(self, frames: Sequence) -> tuple[Any, Any]:
        """CNN + TTA (горизонтальное отражение) → вероятности стадий и признаки."""
        import torch

        probs, feats = [], []
        with torch.no_grad():
            for i in range(0, len(frames), _BATCH):
                x = torch.stack([self._transform(im) for im in frames[i:i + _BATCH]]).to(self.device)
                f = (
                    self.cnn.forward_head(self.cnn.forward_features(x), pre_logits=True)
                    + self.cnn.forward_head(self.cnn.forward_features(x.flip(-1)), pre_logits=True)
                ) / 2
                lg = self.cnn.get_classifier()(f)
                probs.append(torch.softmax(lg.float(), 1).cpu())
                feats.append(f.float().cpu())
        return torch.cat(probs), torch.cat(feats)

    def _stage_probs(self, frames: Sequence, hours) -> Any:
        import torch

        P, feats = self._infer(frames)
        if self.seq is not None:
            with torch.no_grad():
                x = feats[None].to(self.device)
                h = torch.tensor(hours, dtype=torch.float32)[None].to(self.device)
                lens = torch.tensor([len(hours)])
                P = torch.softmax(self.seq(x, h, lens).float(), -1)[0].cpu()
        return P.numpy()

    # -------------------------------------------------------------- analyze
    def analyze(
        self,
        frames_0: Sequence[ImageLike],
        hours: Sequence[float],
        frames_m: Sequence[ImageLike] | None = None,
        frames_p: Sequence[ImageLike] | None = None,
    ) -> dict[str, Any]:
        import numpy as np
        import pandas as pd

        hours_arr = np.asarray(hours, dtype=float)
        frames = [
            self._frame(
                f0,
                frames_m[i] if frames_m else None,
                frames_p[i] if frames_p else None,
            )
            for i, f0 in enumerate(frames_0)
        ]
        P = self._stage_probs(frames, hours_arr)
        path = viterbi(P, self.logA, self.lam)
        ev = correct(events_from_path(path, hours_arr), self.bias)
        f_all = morpho(ev)
        f_early = morpho(ev, self.early_hours)
        fl = flags(f_all, self.ref)
        conf = float(P[np.arange(len(path)), path].mean())

        warnings: list[str] = []
        if len(frames) < C.TL_MIN_FRAMES:
            warnings.append(C.MSG_FEW_FRAMES)
        if hours_arr.max() < self.early_hours:
            warnings.append(C.MSG_SHORT_VIDEO)
        if conf < C.TL_MIN_STAGE_CONFIDENCE:
            warnings.append(C.MSG_LOW_STAGE_CONF)

        score = rank = None
        if hours_arr.max() >= self.early_hours:
            X = pd.DataFrame([f_early])[C.MORPHO_FEATURES]
            score = float(self.clf.predict_proba(X)[0, 1])
            if self.train_scores is not None and len(self.train_scores):
                rank = float(np.searchsorted(self.train_scores, score) / len(self.train_scores))
        if fl and rank is not None and rank > 0.5:
            warnings.append(C.MSG_FLAGS_HIGH_RANK)

        return {
            "model_version": self.model_version,
            "model": self.best_model,
            "task": "timelapse_morphokinetics",
            "n_frames": len(frames),
            "video_hours": round(float(hours_arr.max()), 1),
            "events_hours": {k: round(v, 1) for k, v in ev.items()},
            "morphokinetics": {k: _nan_to_none(v) for k, v in f_all.items() if k != "stage_reached"},
            "last_stage": C.PHASES[int(path[-1])],
            "flags": fl,
            "stage_confidence": round(conf, 3),
            "blastocyst_rank_research": None if rank is None else round(rank, 2),
            "blastocyst_rank_meaning": C.RANK_MEANING,
            # если нет файла с баллами обучения, отдаём сырую вероятность классификатора
            "blastocyst_probability_research": (
                round(score, 3) if score is not None and rank is None else None
            ),
            "status": "no_recommendation" if warnings else "ok",
            "warnings": warnings,
            "disclaimer": C.DISCLAIMER,
        }
