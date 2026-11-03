# Веса моделей

Эта папка постоянно монтируется в контейнер как `/ml-model/weights` только для чтения. Файлы весов не входят в Docker-образ и не добавляются в Git.

Фото — один из наборов из пяти фолдов (не смешивайте разные обучающие запуски):

- `gardner_fold1.pt` … `gardner_fold5.pt` — ранний экспорт;
- `gardner_strict_fold1.pt` … `gardner_strict_fold5.pt`;
- `gardner_official_fold1.pt` … `gardner_official_fold5.pt`.

Time-lapse — обязательны:

- `cnn_convnext_best.pt`
- `hmm_logA.npy`
- `blastocyst_clf_research.joblib`

Скопируйте также доступные дополнительные файлы из того же запуска: `seq_bigru_best.pt`, `config_timelapse.json`, `morphokinetic_reference.json`, `timing_bias_correction.json`, `blastocyst_train_scores.npy`.

Из корня проекта: `bash scripts/start-ml.sh`. Скрипт включает ML-сборку в корневом `.env`, запускает сервисы и проверяет доступность зависимостей и файлов через API. Эта проверка не заменяет пробный расчёт: несовместимый или повреждённый checkpoint может обнаружиться только при загрузке модели.

После замены уже загруженных весов перезапустите backend: модели кешируются в памяти. Пересборка образа для замены весов не нужна. Если после добавления файлов контейнер их не видит, проверьте `ML_WEIGHTS_DIR` и пересоздайте backend через `docker-compose up -d --force-recreate backend`.
