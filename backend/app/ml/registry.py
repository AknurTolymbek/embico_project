"""
Реестр ML-моделей: ленивая загрузка (при первом запросе) и кеш в памяти.

Модели тяжёлые (сотни МБ), поэтому грузим их один раз на процесс.
Lock защищает от одновременной загрузки из двух потоков.
"""
from __future__ import annotations

import importlib.util
import logging
import threading
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.ml import constants as C

logger = logging.getLogger(__name__)

ML_DEPENDENCIES = ("torch", "torchvision", "timm", "numpy", "pandas", "sklearn", "joblib", "PIL")


class MLModelUnavailable(RuntimeError):
    """Модель нельзя использовать: ML выключен, нет зависимостей или файлов весов."""


_lock = threading.Lock()
_blastocyst = None
_timelapse = None


def models_dir() -> Path:
    return Path(settings.ML_MODELS_DIR).expanduser().resolve()


def missing_dependencies() -> list[str]:
    return [m for m in ML_DEPENDENCIES if importlib.util.find_spec(m) is None]


def _check_available() -> None:
    if not settings.ML_ENABLED:
        raise MLModelUnavailable("ML-модуль отключён (ML_ENABLED=false)")
    missing = missing_dependencies()
    if missing:
        raise MLModelUnavailable(
            f"Не установлены ML-зависимости: {', '.join(missing)}. "
            "Установите: pip install -r requirements-ml.txt"
        )


def _load(loader) -> Any:
    try:
        return loader(models_dir(), settings.ML_DEVICE)
    except FileNotFoundError as e:
        raise MLModelUnavailable(str(e)) from e
    except ImportError as e:
        raise MLModelUnavailable(f"Ошибка импорта ML-зависимостей: {e}") from e


def get_blastocyst_predictor():
    """Модель 1 (Гарднер по фото). Бросает MLModelUnavailable."""
    global _blastocyst
    if _blastocyst is None:
        _check_available()
        with _lock:
            if _blastocyst is None:
                from app.ml.blastocyst import BlastocystPredictor

                _blastocyst = _load(BlastocystPredictor.load)
    return _blastocyst


def get_timelapse_predictor():
    """Модель 2 (time-lapse). Бросает MLModelUnavailable."""
    global _timelapse
    if _timelapse is None:
        _check_available()
        with _lock:
            if _timelapse is None:
                from app.ml.timelapse import TimelapsePredictor

                _timelapse = _load(TimelapsePredictor.load)
    return _timelapse


def reset() -> None:
    """Сбросить кеш (для тестов или после замены весов)."""
    global _blastocyst, _timelapse
    with _lock:
        _blastocyst = _timelapse = None


def status() -> dict[str, Any]:
    """Состояние ML-модуля без загрузки моделей."""
    d = models_dir()
    from app.ml.blastocyst import find_weight_files

    mode, gardner_files = find_weight_files(d) if d.is_dir() else (None, [])
    tl_required = [C.TL_FILE_CNN, C.TL_FILE_LOGA, C.TL_FILE_CLF]
    tl_optional = [C.TL_FILE_GRU, C.TL_FILE_CONFIG, C.TL_FILE_REF, C.TL_FILE_BIAS, C.TL_FILE_TRAIN_SCORES]
    tl_missing = [f for f in tl_required if not (d / f).is_file()]

    return {
        "enabled": settings.ML_ENABLED,
        "device": settings.ML_DEVICE,
        "models_dir": str(d),
        "models_dir_exists": d.is_dir(),
        "missing_dependencies": missing_dependencies(),
        "blastocyst": {
            "loaded": _blastocyst is not None,
            "weights_found": bool(gardner_files),
            "mode": mode,
            "files": [p.name for p in gardner_files],
            "missing_files": [] if gardner_files else [C.GARDNER_WEIGHTS_PATTERN.format(mode="strict", fold="N")],
        },
        "timelapse": {
            "loaded": _timelapse is not None,
            "weights_found": not tl_missing,
            "mode": getattr(_timelapse, "best_model", None),
            "files": [f for f in tl_required + tl_optional if (d / f).is_file()],
            "missing_files": tl_missing,
        },
    }
