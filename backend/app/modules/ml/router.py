"""
API ML-моделей.

- GET  /ml/status               — состояние модулей (веса, зависимости)
- POST /ml/blastocyst/predict   — оценка бластоцисты по фото (шкала Гарднера)
- POST /ml/timelapse/predict    — морфокинетика по кадрам time-lapse + исследовательский ранг

Результаты носят исследовательский характер и требуют проверки эмбриологом.
"""
from __future__ import annotations

import io
import json
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.modules.ml.inference import registry
from app.modules.ml.inference.registry import MLModelUnavailable
from app.modules.ml.schemas import (
    BlastocystPredictionResponse,
    MLStatusResponse,
    TimelapsePredictionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------
def _unavailable(e: MLModelUnavailable) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


def _bad_request(msg: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


async def _read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    """Читаем файл, не больше max_bytes (защита от слишком больших загрузок)."""
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл {upload.filename!r} больше {max_bytes // (1024 * 1024)} МБ",
        )
    if not data:
        raise _bad_request(f"Файл {upload.filename!r} пустой")
    return data


def _check_image(data: bytes, name: str | None) -> None:
    """Проверяем, что байты — читаемое изображение (PIL уже установлен, раз модель загружена)."""
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as e:
        raise _bad_request(f"Файл {name!r} не является изображением") from e


def parse_hours(raw: str) -> list[float]:
    """hours: JSON-список "[0.25, 0.5, ...]" или строка через запятую "0.25,0.5,..."."""
    raw = raw.strip()
    try:
        values = json.loads(raw) if raw.startswith("[") else [x for x in raw.split(",") if x.strip()]
        hours = [float(x) for x in values]
    except (ValueError, TypeError) as e:
        raise _bad_request("hours: ожидается JSON-список чисел или числа через запятую") from e
    if not hours:
        raise _bad_request("hours: пустой список")
    if any(h != h or h < 0 for h in hours):  # h != h — проверка на NaN
        raise _bad_request("hours: значения должны быть неотрицательными числами")
    if any(b <= a for a, b in zip(hours, hours[1:])):
        raise _bad_request("hours: значения должны строго возрастать")
    return hours


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/status", response_model=MLStatusResponse)
async def ml_status():
    """Состояние ML-модуля: включён ли, найдены ли веса и зависимости, загружены ли модели."""
    return registry.status()


@router.post("/blastocyst/predict", response_model=BlastocystPredictionResponse)
async def predict_blastocyst(
    image: UploadFile = File(..., description="Фото бластоцисты (JPG/PNG/TIFF)"),
):
    """
    Оценка бластоцисты по шкале Гарднера: степень экспансии (EXP1–5),
    ВКМ (A/B/C) и трофэктодерма (A/B/C) — для экспансии ≥ 2.

    Ансамбль 5 моделей EfficientNet-B2 + TTA. При низкой уверенности или
    низком разрешении status = "no_recommendation".
    """
    try:
        predictor = await run_in_threadpool(registry.get_blastocyst_predictor)
    except MLModelUnavailable as e:
        raise _unavailable(e) from e

    data = await _read_limited(image, settings.ML_MAX_IMAGE_MB * 1024 * 1024)
    _check_image(data, image.filename)

    from PIL import Image

    def _run():
        with Image.open(io.BytesIO(data)) as im:
            return predictor.predict(im)

    try:
        return await run_in_threadpool(_run)
    except Exception as e:
        logger.exception("Ошибка инференса модели Гарднера")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Ошибка инференса модели") from e


@router.post("/timelapse/predict", response_model=TimelapsePredictionResponse)
async def predict_timelapse(
    frames: list[UploadFile] = File(
        ..., description="Кадры центральной фокальной плоскости (F0) в хронологическом порядке"
    ),
    hours: str = Form(
        ...,
        description="Время каждого кадра в часах после оплодотворения: JSON-список или через запятую",
    ),
    frames_fm: list[UploadFile] | None = File(
        None, description="Необязательно: кадры плоскости F-15 (тот же порядок и количество)"
    ),
    frames_fp: list[UploadFile] | None = File(
        None, description="Необязательно: кадры плоскости F+15 (тот же порядок и количество)"
    ),
):
    """
    Анализ time-lapse: распознавание стадий по каждому кадру (ConvNeXt [+ BiGRU]),
    сглаживание HMM/Витерби → время событий (t2, t3, …, tB), морфокинетика,
    флаги отклонений и исследовательский ранг вероятности бластоцисты
    (доступен, если видео ≥ 72 ч).
    """
    parsed_hours = parse_hours(hours)
    n = len(frames)
    if n > settings.ML_MAX_TIMELAPSE_FRAMES:
        raise _bad_request(f"Слишком много кадров: {n} > {settings.ML_MAX_TIMELAPSE_FRAMES}")
    if len(parsed_hours) != n:
        raise _bad_request(f"Количество hours ({len(parsed_hours)}) не совпадает с количеством кадров ({n})")
    for name, extra in (("frames_fm", frames_fm), ("frames_fp", frames_fp)):
        if extra and len(extra) != n:
            raise _bad_request(f"{name}: {len(extra)} кадров, ожидалось {n}")

    try:
        predictor = await run_in_threadpool(registry.get_timelapse_predictor)
    except MLModelUnavailable as e:
        raise _unavailable(e) from e

    max_bytes = settings.ML_MAX_IMAGE_MB * 1024 * 1024

    async def _read_all(files: list[UploadFile] | None) -> list[bytes] | None:
        if not files:
            return None
        out = []
        for f in files:
            data = await _read_limited(f, max_bytes)
            _check_image(data, f.filename)
            out.append(data)
        return out

    f0 = await _read_all(frames)
    fm = await _read_all(frames_fm)
    fp = await _read_all(frames_fp)

    try:
        return await run_in_threadpool(predictor.analyze, f0, parsed_hours, fm, fp)
    except Exception as e:
        logger.exception("Ошибка инференса time-lapse модели")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Ошибка инференса модели") from e
