#!/usr/bin/env bash
# Run on the machine that actually hosts the project and Docker.
set -euo pipefail
cd "$(dirname "$0")/.."

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  compose=(docker-compose)
else
  echo "Не найден Docker Compose. Установите/запустите Docker Desktop." >&2
  exit 1
fi

# Preserve existing credentials and unrelated settings. Never source .env as shell code.
python3 - <<'PY'
import re
from pathlib import Path

path = Path('.env')
text = path.read_text() if path.exists() else ''
for key in ('INSTALL_ML', 'ML_ENABLED'):
    pattern = rf'(?m)^(?:export\s+)?{key}\s*=.*$'
    if re.search(pattern, text):
        text = re.sub(pattern, f'{key}=true', text)
    else:
        text = text.rstrip('\n') + ('\n' if text else '') + f'{key}=true\n'
path.write_text(text)
print('В корневом .env закреплены INSTALL_ML=true и ML_ENABLED=true.')
PY

INSTALL_ML=true ML_ENABLED=true "${compose[@]}" up -d --build backend frontend

python3 - "${compose[@]}" <<'PY'
import json
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

url = 'http://localhost:8000/health'
for attempt in range(30):
    try:
        with urlopen(url, timeout=5) as response:
            json.load(response)
        break
    except (URLError, OSError, ValueError):
        if attempt == 29:
            sys.exit('Backend не ответил. Проверьте: docker-compose logs --tail=100 backend')
        time.sleep(1)

# /ml/status is now private. Inspect readiness inside the container without
# creating a public bypass or storing administrator tokens in a shell script.
command = sys.argv[1:] + ['exec', '-T', 'backend', 'python', '-c',
    'import json; from app.modules.ml.inference.registry import status; print(json.dumps(status()))']
status = json.loads(subprocess.check_output(command, text=True))
print('Папка весов внутри контейнера:', status['models_dir'])
missing = status['missing_dependencies']
if missing:
    print('Не найдены зависимости:', ', '.join(missing))
ready = status['enabled'] and not missing
if not status['enabled']:
    print('ML-модуль выключен.')
for name, label in (('blastocyst', 'Фото'), ('timelapse', 'Time-lapse')):
    model = status[name]
    available = status['enabled'] and not missing and model['weights_found']
    print(f'{label}: ' + ('зависимости и веса найдены' if available else 'не готова'))
    if model['missing_files']:
        print('  Не найдены:', ', '.join(model['missing_files']))
    if model['files']:
        print('  Файлы:', ', '.join(model['files']))
    ready = ready and available
if not ready:
    sys.exit('Проверьте папку ml-model/weights на ЭТОМ компьютере и ML_WEIGHTS_DIR в корневом .env.')
print('Подготовка завершена. Запустите пробный анализ фото и time-lapse в интерфейсе.')
PY
