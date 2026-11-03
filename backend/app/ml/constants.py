"""
Константы ML-моделей. Перенесены 1-в-1 из ноутбуков ml-model/*.ipynb —
менять только вместе с переобучением моделей.
"""

DISCLAIMER = "Только для исследования и проверки эмбриологом. Не является клиническим решением."

# ---------------------------------------------------------------------------
# Модель 1: оценка бластоцисты по фото (blastosit-images.ipynb)
# ---------------------------------------------------------------------------
GARDNER_BACKBONE = "efficientnet_b2"
GARDNER_IMG_SIZE = 320
GARDNER_MIN_CONFIDENCE = 0.55
GARDNER_MODEL_VERSION = "gardner-photo-v0.2.1"
GARDNER_MODES = ("strict", "official")
GARDNER_N_FOLDS = 5
GARDNER_WEIGHTS_PATTERN = "gardner_{mode}_fold{fold}.pt"
GARDNER_MIN_SIDE_PX = 200
ICM_TE = {0: "A", 1: "B", 2: "C"}

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

MSG_LOW_RESOLUTION = "низкое разрешение снимка"
MSG_LOW_CONFIDENCE_PHOTO = "низкая уверенность модели — нужна оценка эмбриолога"

# ---------------------------------------------------------------------------
# Модель 2: time-lapse (time-lapse-last-version.ipynb, v0.4)
# ---------------------------------------------------------------------------
TL_BACKBONE = "convnext_tiny.fb_in22k_ft_in1k"
TL_IMG_SIZE = 224
TL_EARLY_HOURS = 72.0
TL_MODEL_VERSION = "timelapse-v0.4"
TL_MIN_FRAMES = 100
TL_MIN_STAGE_CONFIDENCE = 0.6

PHASES = [
    "tPB2", "tPNa", "tPNf", "t2", "t3", "t4", "t5", "t6", "t7", "t8",
    "t9+", "tM", "tSB", "tB", "tEB",
]
PIDX = {p: i for i, p in enumerate(PHASES)}
PIDX["tHB"] = PIDX["tEB"]
K = len(PHASES)  # 15
KEY_EVENTS = ["t2", "t3", "t4", "t5", "t8", "tSB", "tB"]

# Порядок признаков для классификатора бластоцисты (как в Xf.columns)
MORPHO_FEATURES = ["t2", "t3", "t4", "t5", "t8", "cc2", "s2", "s3", "t5_t2", "stage_reached"]

LABEL_CNN_HMM = "ConvNeXt-Tiny + HMM"
LABEL_CNN_GRU_HMM = "ConvNeXt-Tiny + BiGRU + HMM"

# Запасные значения, если в папке весов нет json-файлов
DEFAULT_REF = {
    "t2": (22.5, 35.0), "t3": (28.4, 47.8), "t4": (33.8, 50.0), "t5": (38.0, 61.0),
    "t8": (47.3, 81.0), "cc2": (1.5, 14.0), "s2": (0.5, 12.0), "s3": (1.4, 26.3),
    "t5_t2": (11.7, 30.9),
}
DEFAULT_BIAS = {"t4": -0.3, "t5": 0.2, "t8": -0.5, "tSB": -0.5}

# Файлы весов time-lapse
TL_FILE_CNN = "cnn_convnext_best.pt"
TL_FILE_GRU = "seq_bigru_best.pt"
TL_FILE_LOGA = "hmm_logA.npy"
TL_FILE_CLF = "blastocyst_clf_research.joblib"
TL_FILE_CONFIG = "config_timelapse.json"
TL_FILE_REF = "morphokinetic_reference.json"
TL_FILE_BIAS = "timing_bias_correction.json"
TL_FILE_TRAIN_SCORES = "blastocyst_train_scores.npy"  # необязательный

MSG_FEW_FRAMES = "мало кадров"
MSG_SHORT_VIDEO = "видео короче 72 ч — прогноз бластоцисты недоступен"
MSG_LOW_STAGE_CONF = "низкая уверенность распознавания стадий"
MSG_FLAGS_HIGH_RANK = "есть отклонения морфокинетики при среднем/высоком ранге — интерпретировать осторожно"
MSG_DIRECT_CLEAVAGE = "возможное прямое деление 2→3 клетки (t3 − t2 < 5 ч)"
RANK_MEANING = "доля эмбрионов из обучения с более низким баллом (0 — хуже всех, 1 — лучше всех)"
