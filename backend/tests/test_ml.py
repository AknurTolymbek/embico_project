"""
Тесты ML-модуля.

Настоящие модели (torch + веса) в тестах не нужны: подменяем их фейками через monkeypatch.
Проверяем контракт API: валидацию входа, коды ошибок и формат ответа.
Тесты с картинками требуют Pillow, тесты чистых функций — numpy (иначе пропускаются).
"""
import io
import math

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.api.endpoints.ml import parse_hours
from app.core.config import settings
from app.main import app
from app.ml import constants as C
from app.ml import registry
from app.ml import timelapse as tl

ML = f"{settings.API_V1_PREFIX}/ml"


# ---------------------------------------------------------------------------
# Фикстуры и фейки
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _isolated_registry(monkeypatch, tmp_path):
    """Каждый тест — с пустой папкой весов и сброшенным кешем моделей."""
    monkeypatch.setattr(settings, "ML_MODELS_DIR", str(tmp_path))
    registry.reset()
    yield
    registry.reset()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def png_bytes(size=(64, 64)) -> bytes:
    """Синтетическое изображение (серый квадрат)."""
    Image = pytest.importorskip("PIL.Image")
    buf = io.BytesIO()
    Image.new("L", size, color=128).save(buf, format="PNG")
    return buf.getvalue()


BLASTOCYST_RESULT = {
    "model_version": "fake-strict-ens5",
    "task": "gardner_grading_photo",
    "expansion_class": 3,
    "probabilities": {"exp": [0.0, 0.05, 0.1, 0.8, 0.05], "icm": [0.7, 0.2, 0.1], "te": [0.2, 0.7, 0.1]},
    "icm": "A",
    "te": "B",
    "gardner": "EXP3-AB",
    "confidence": 0.7,
    "status": "ok",
    "warnings": [],
    "disclaimer": C.DISCLAIMER,
}


class FakeBlastocyst:
    def __init__(self):
        self.calls = 0

    def predict(self, image):
        self.calls += 1
        assert image.size == (64, 64)
        return BLASTOCYST_RESULT


class FakeTimelapse:
    def __init__(self):
        self.args = None

    def analyze(self, f0, hours, fm=None, fp=None):
        self.args = (f0, hours, fm, fp)
        return {
            "model_version": "fake-0.4",
            "model": "ConvNeXt-Tiny + HMM",
            "task": "timelapse_morphokinetics",
            "n_frames": len(f0),
            "video_hours": hours[-1],
            "events_hours": {"tPNf": 23.0, "t2": 26.0},
            "morphokinetics": {"t2": 26.0, "t3": None},
            "last_stage": "t2",
            "flags": [],
            "stage_confidence": 0.9,
            "blastocyst_rank_research": None,
            "blastocyst_rank_meaning": C.RANK_MEANING,
            "blastocyst_probability_research": None,
            "status": "no_recommendation",
            "warnings": ["видео короче 72 ч"],
            "disclaimer": C.DISCLAIMER,
        }


def _unavailable():
    raise registry.MLModelUnavailable("нет весов")


# ---------------------------------------------------------------------------
# GET /ml/status
# ---------------------------------------------------------------------------
async def test_status_without_weights(client, tmp_path):
    r = await client.get(f"{ML}/status")
    assert r.status_code == 200
    body = r.json()
    assert body["models_dir"] == str(tmp_path.resolve())
    assert body["models_dir_exists"] is True
    assert body["blastocyst"] == {
        "loaded": False,
        "weights_found": False,
        "mode": None,
        "files": [],
        "missing_files": ["gardner_strict_foldN.pt"],
    }
    assert body["timelapse"]["weights_found"] is False
    assert set(body["timelapse"]["missing_files"]) == {C.TL_FILE_CNN, C.TL_FILE_LOGA, C.TL_FILE_CLF}


async def test_status_finds_weight_files(client, tmp_path):
    for fold in (1, 2):
        (tmp_path / C.GARDNER_WEIGHTS_PATTERN.format(mode="official", fold=fold)).touch()
    for name in (C.TL_FILE_CNN, C.TL_FILE_LOGA, C.TL_FILE_CLF):
        (tmp_path / name).touch()

    body = (await client.get(f"{ML}/status")).json()
    assert body["blastocyst"]["weights_found"] is True
    assert body["blastocyst"]["mode"] == "official"
    assert len(body["blastocyst"]["files"]) == 2
    assert body["timelapse"]["weights_found"] is True
    assert body["timelapse"]["missing_files"] == []


# ---------------------------------------------------------------------------
# Недоступность модели → 503
# ---------------------------------------------------------------------------
async def test_status_finds_legacy_gardner_weights(client, tmp_path):
    for fold in range(1, 6):
        (tmp_path / f"gardner_fold{fold}.pt").touch()

    body = (await client.get(f"{ML}/status")).json()["blastocyst"]
    assert body["weights_found"] is True
    assert body["mode"] == "legacy"
    assert body["files"] == [f"gardner_fold{fold}.pt" for fold in range(1, 6)]
    assert body["missing_files"] == []


async def test_named_gardner_weights_take_priority_over_legacy(client, tmp_path):
    (tmp_path / "gardner_fold1.pt").touch()
    (tmp_path / "gardner_official_fold1.pt").touch()
    body = (await client.get(f"{ML}/status")).json()["blastocyst"]
    assert body["mode"] == "official"
    assert body["files"] == ["gardner_official_fold1.pt"]


async def test_disabled_ml_returns_503(client, monkeypatch):
    monkeypatch.setattr(settings, "ML_ENABLED", False)
    r = await client.post(f"{ML}/blastocyst/predict", files={"image": ("e.png", b"x", "image/png")})
    assert r.status_code == 503
    assert "ML_ENABLED" in r.json()["detail"]


async def test_missing_weights_returns_503(client, monkeypatch):
    monkeypatch.setattr(registry, "get_timelapse_predictor", _unavailable)
    r = await client.post(
        f"{ML}/timelapse/predict",
        files=[("frames", ("1.png", b"x", "image/png"))],
        data={"hours": "0.25"},
    )
    assert r.status_code == 503
    assert r.json()["detail"] == "нет весов"


# ---------------------------------------------------------------------------
# POST /ml/blastocyst/predict
# ---------------------------------------------------------------------------
async def test_blastocyst_predict_ok(client, monkeypatch):
    fake = FakeBlastocyst()
    monkeypatch.setattr(registry, "get_blastocyst_predictor", lambda: fake)
    r = await client.post(f"{ML}/blastocyst/predict", files={"image": ("e.png", png_bytes(), "image/png")})
    assert r.status_code == 200, r.text
    assert r.json()["gardner"] == "EXP3-AB"
    assert fake.calls == 1


async def test_blastocyst_rejects_non_image(client, monkeypatch):
    pytest.importorskip("PIL")
    monkeypatch.setattr(registry, "get_blastocyst_predictor", lambda: FakeBlastocyst())
    r = await client.post(f"{ML}/blastocyst/predict", files={"image": ("e.png", b"not an image", "image/png")})
    assert r.status_code == 422


async def test_blastocyst_rejects_empty_file(client, monkeypatch):
    monkeypatch.setattr(registry, "get_blastocyst_predictor", lambda: FakeBlastocyst())
    r = await client.post(f"{ML}/blastocyst/predict", files={"image": ("e.png", b"", "image/png")})
    assert r.status_code == 422


async def test_blastocyst_rejects_too_large(client, monkeypatch):
    monkeypatch.setattr(settings, "ML_MAX_IMAGE_MB", 0)
    monkeypatch.setattr(registry, "get_blastocyst_predictor", lambda: FakeBlastocyst())
    r = await client.post(f"{ML}/blastocyst/predict", files={"image": ("e.png", b"x", "image/png")})
    assert r.status_code == 413


async def test_blastocyst_inference_error_returns_500(client, monkeypatch):
    class Broken:
        def predict(self, image):
            raise RuntimeError("boom")

    monkeypatch.setattr(registry, "get_blastocyst_predictor", lambda: Broken())
    r = await client.post(f"{ML}/blastocyst/predict", files={"image": ("e.png", png_bytes(), "image/png")})
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# POST /ml/timelapse/predict
# ---------------------------------------------------------------------------
async def test_timelapse_predict_ok(client, monkeypatch):
    fake = FakeTimelapse()
    monkeypatch.setattr(registry, "get_timelapse_predictor", lambda: fake)
    img = png_bytes()
    r = await client.post(
        f"{ML}/timelapse/predict",
        files=[("frames", (f"{i}.png", img, "image/png")) for i in range(3)]
        + [("frames_fm", (f"m{i}.png", img, "image/png")) for i in range(3)],
        data={"hours": "[0.25, 0.5, 0.75]"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["n_frames"] == 3
    f0, hours, fm, fp = fake.args
    assert len(f0) == 3 and len(fm) == 3 and fp is None
    assert hours == [0.25, 0.5, 0.75]


async def test_timelapse_hours_count_mismatch(client, monkeypatch):
    fake = FakeTimelapse()
    monkeypatch.setattr(registry, "get_timelapse_predictor", lambda: fake)
    r = await client.post(
        f"{ML}/timelapse/predict",
        files=[("frames", (f"{i}.png", b"x", "image/png")) for i in range(2)],
        data={"hours": "0.25,0.5,0.75"},
    )
    assert r.status_code == 422
    assert "не совпадает" in r.json()["detail"]
    assert fake.args is None  # модель не вызывалась


async def test_timelapse_extra_plane_count_mismatch(client, monkeypatch):
    monkeypatch.setattr(registry, "get_timelapse_predictor", lambda: FakeTimelapse())
    r = await client.post(
        f"{ML}/timelapse/predict",
        files=[("frames", (f"{i}.png", b"x", "image/png")) for i in range(2)]
        + [("frames_fp", ("p0.png", b"x", "image/png"))],
        data={"hours": "0.25,0.5"},
    )
    assert r.status_code == 422
    assert "frames_fp" in r.json()["detail"]


async def test_timelapse_too_many_frames(client, monkeypatch):
    monkeypatch.setattr(settings, "ML_MAX_TIMELAPSE_FRAMES", 1)
    r = await client.post(
        f"{ML}/timelapse/predict",
        files=[("frames", (f"{i}.png", b"x", "image/png")) for i in range(2)],
        data={"hours": "0.25,0.5"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# parse_hours
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("[0.25, 0.5, 1]", [0.25, 0.5, 1.0]),
        ("0.25, 0.5,1", [0.25, 0.5, 1.0]),
        (" 0,1,2, ", [0.0, 1.0, 2.0]),
    ],
)
def test_parse_hours_ok(raw, expected):
    assert parse_hours(raw) == expected


@pytest.mark.parametrize("raw", ["", "[]", "a,b", "[1, 2", "1,1,2", "2,1", "-1,0", "NaN,1", '{"a": 1}'])
def test_parse_hours_invalid(raw):
    with pytest.raises(HTTPException) as e:
        parse_hours(raw)
    assert e.value.status_code == 422


# ---------------------------------------------------------------------------
# Чистые функции time-lapse (перенесены из ноутбука)
# ---------------------------------------------------------------------------
def test_viterbi_only_moves_forward():
    np = pytest.importorskip("numpy")
    # шумные вероятности: на кадре 2 «откат» к стадии 0 — Витерби не должен его допустить
    P = np.array([
        [0.9, 0.1, 0.0],
        [0.1, 0.9, 0.0],
        [0.6, 0.4, 0.0],
        [0.0, 0.2, 0.8],
    ])
    logA = np.log(np.full((3, 3), 1 / 3))
    path = tl.viterbi(P, logA)
    assert path.tolist() == sorted(path.tolist())
    assert path[0] == 0 and path[-1] == 2


def test_events_from_path():
    np = pytest.importorskip("numpy")
    path = np.array([0, 0, 1, 1, 2])
    hours = [10.0, 11.0, 12.0, 13.0, 14.0]
    ev = tl.events_from_path(path, hours)
    assert ev == {C.PHASES[0]: 10.0, C.PHASES[1]: 12.0, C.PHASES[2]: 14.0}


def test_correct_subtracts_bias():
    assert tl.correct({"t2": 26.0, "t3": 37.0}, {"t2": 1.0}) == {"t2": 25.0, "t3": 37.0}


def test_morpho_and_flags():
    ev = {"t2": 26.0, "t3": 29.0, "t4": 38.0, "t5": 49.0, "t8": 56.0, "tB": 110.0}
    f = tl.morpho(ev)
    assert f["cc2"] == pytest.approx(3.0)
    assert f["s2"] == pytest.approx(9.0)
    assert f["s3"] == pytest.approx(7.0)
    assert f["t5_t2"] == pytest.approx(23.0)

    out = tl.flags(f, {"t2": (22.0, 30.0), "t5": (40.0, 45.0)})
    assert any(s.startswith("t5 = 49.0") for s in out)
    assert not any(s.startswith("t2 =") for s in out)
    assert C.MSG_DIRECT_CLEAVAGE in out  # cc2 < 5 ч


def test_morpho_until_cuts_late_events():
    f = tl.morpho({"t2": 26.0, "t3": 37.0, "t8": 60.0}, until=40.0)
    assert f["t2"] == 26.0
    assert math.isnan(f["t8"])
    assert math.isnan(f["s3"])
