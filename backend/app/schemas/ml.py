"""
Pydantic-схемы ответов ML-модуля.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PredictionStatus = Literal["ok", "no_recommendation"]


class _Base(BaseModel):
    # поле model_version иначе конфликтует с защищённым префиксом "model_"
    model_config = ConfigDict(protected_namespaces=())


# ---------------------------------------------------------------------------
# Статус
# ---------------------------------------------------------------------------
class MLModelStatus(_Base):
    loaded: bool = Field(description="Модель уже загружена в память")
    weights_found: bool = Field(description="Найдены обязательные файлы весов")
    mode: str | None = None
    files: list[str] = []
    missing_files: list[str] = []


class MLStatusResponse(_Base):
    enabled: bool
    device: str
    models_dir: str
    models_dir_exists: bool
    missing_dependencies: list[str]
    blastocyst: MLModelStatus
    timelapse: MLModelStatus


# ---------------------------------------------------------------------------
# Модель 1: бластоциста по фото (Гарднер)
# ---------------------------------------------------------------------------
class GardnerProbabilities(_Base):
    exp: list[float] = Field(description="Вероятности степени экспансии 0..4 (EXP1..EXP5 → индексы)")
    icm: list[float] | None = Field(None, description="Вероятности ВКМ A/B/C (только при экспансии ≥ 2)")
    te: list[float] | None = Field(None, description="Вероятности трофэктодермы A/B/C (только при экспансии ≥ 2)")


class BlastocystPredictionResponse(_Base):
    model_version: str
    task: str
    expansion_class: int = Field(ge=0, le=4)
    probabilities: GardnerProbabilities
    icm: Literal["A", "B", "C"] | None
    te: Literal["A", "B", "C"] | None
    gardner: str = Field(description="Итоговая оценка, напр. EXP3-AB")
    confidence: float = Field(ge=0, le=1)
    status: PredictionStatus
    warnings: list[str]
    disclaimer: str


# ---------------------------------------------------------------------------
# Модель 2: time-lapse
# ---------------------------------------------------------------------------
class TimelapsePredictionResponse(_Base):
    model_version: str
    model: str = Field(description="Архитектура: ConvNeXt-Tiny + HMM или + BiGRU + HMM")
    task: str
    n_frames: int
    video_hours: float
    events_hours: dict[str, float] = Field(description="Время событий (часы после оплодотворения): t2, t3, … tB")
    morphokinetics: dict[str, float | None] = Field(description="Морфокинетические параметры: t2…t8, cc2, s2, s3, t5_t2")
    last_stage: str
    flags: list[str] = Field(description="Отклонения от референсных интервалов")
    stage_confidence: float
    blastocyst_rank_research: float | None = Field(
        None, description="Исследовательский ранг (0..1) по эмбрионам из обучения"
    )
    blastocyst_rank_meaning: str
    blastocyst_probability_research: float | None = None
    status: PredictionStatus
    warnings: list[str]
    disclaimer: str
