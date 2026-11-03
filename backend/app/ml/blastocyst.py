"""
Модель 1: оценка бластоцисты по фото по шкале Гарднера.

Перенос функции predict_embryo из ml-model/blastosit-images.ipynb:
ансамбль из 5 моделей EfficientNet-B2 (по фолдам) + TTA из 4 отражений.
torch/timm импортируются внутри методов — модуль можно импортировать без них.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.ml import constants as C

logger = logging.getLogger(__name__)


def _build_gardner_net(backbone: str):
    """Создаём класс GardnerNet лениво (нужен torch)."""
    import timm
    from torch import nn

    class GardnerNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            # pretrained=False: веса всё равно загружаем из state_dict
            self.body = timm.create_model(backbone, pretrained=False, num_classes=0)
            d = self.body.num_features
            self.drop = nn.Dropout(0.3)
            self.exp, self.icm, self.te = nn.Linear(d, 5), nn.Linear(d, 3), nn.Linear(d, 3)

        def forward(self, x):
            f = self.drop(self.body(x))
            return self.exp(f), self.icm(f), self.te(f)

    return GardnerNet()


def find_weight_files(models_dir: Path) -> tuple[str | None, list[Path]]:
    """Ищем веса: сначала режим strict, иначе official (как SERVE_MODE в ноутбуке)."""
    for mode in C.GARDNER_MODES:
        files = [
            models_dir / C.GARDNER_WEIGHTS_PATTERN.format(mode=mode, fold=f)
            for f in range(1, C.GARDNER_N_FOLDS + 1)
        ]
        files = [p for p in files if p.is_file()]
        if files:
            return mode, files
    return None, []


class BlastocystPredictor:
    """Ансамбль моделей Гарднера, загруженный в память."""

    def __init__(self, models: list, mode: str, device: str) -> None:
        self.models = models
        self.mode = mode
        self.device = device
        self._transform = self._make_transform()

    @classmethod
    def load(cls, models_dir: Path, device: str = "cpu") -> "BlastocystPredictor":
        import torch

        mode, files = find_weight_files(models_dir)
        if not files:
            raise FileNotFoundError(
                f"Не найдены веса gardner_strict_fold*.pt / gardner_official_fold*.pt в {models_dir}"
            )
        models = []
        for path in files:
            model = _build_gardner_net(C.GARDNER_BACKBONE)
            state = torch.load(path, map_location=device)
            model.load_state_dict(state)
            model.to(device).eval()
            models.append(model)
        logger.info("Модель Гарднера загружена: режим %s, %d фолдов", mode, len(models))
        return cls(models, mode, device)

    @staticmethod
    def _make_transform():
        import torchvision.transforms as T

        s = C.GARDNER_IMG_SIZE
        return T.Compose([
            T.Grayscale(3),
            T.Resize((s, s)),
            T.ToTensor(),
            T.Normalize(C.IMAGENET_MEAN, C.IMAGENET_STD),
        ])

    @property
    def model_version(self) -> str:
        return f"{C.GARDNER_MODEL_VERSION}-{self.mode}-ens{len(self.models)}"

    def predict(self, image) -> dict[str, Any]:
        """image — PIL.Image. Возвращает словарь в формате ноутбука."""
        import torch
        import torch.nn.functional as F

        img = image.convert("RGB")
        warnings: list[str] = []
        if min(img.size) < C.GARDNER_MIN_SIDE_PX:
            warnings.append(C.MSG_LOW_RESOLUTION)

        with torch.no_grad():
            x = self._transform(img).unsqueeze(0).to(self.device)
            views = [x, x.flip(-1), x.flip(-2), x.flip(-1).flip(-2)]
            outs = [[F.softmax(o.float(), 1) for o in m(v)] for m in self.models for v in views]
            pe, pi, pt = [
                torch.stack([o[k] for o in outs]).mean(0)[0].cpu().numpy() for k in range(3)
            ]

        exp = int(pe.argmax())
        conf = {"exp": float(pe.max())}
        out: dict[str, Any] = {
            "model_version": self.model_version,
            "task": "gardner_grading_photo",
            "expansion_class": exp,
            "probabilities": {"exp": pe.round(3).tolist()},
        }
        if exp >= 2:
            icm, te = int(pi.argmax()), int(pt.argmax())
            conf.update(icm=float(pi.max()), te=float(pt.max()))
            out.update(
                icm=C.ICM_TE[icm],
                te=C.ICM_TE[te],
                gardner=f"EXP{exp}-{C.ICM_TE[icm]}{C.ICM_TE[te]}",
            )
            out["probabilities"].update(icm=pi.round(3).tolist(), te=pt.round(3).tolist())
        else:
            out.update(icm=None, te=None, gardner=f"EXP{exp} (ICM/TE не оцениваются на этой стадии)")

        out["confidence"] = round(min(conf.values()), 3)
        if out["confidence"] < C.GARDNER_MIN_CONFIDENCE:
            warnings.append(C.MSG_LOW_CONFIDENCE_PHOTO)
        out.update(
            status="no_recommendation" if warnings else "ok",
            warnings=warnings,
            disclaimer=C.DISCLAIMER,
        )
        return out
