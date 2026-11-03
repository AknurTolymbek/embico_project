# Backend EMBICO: FastAPI + Alembic
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Сначала только зависимости — чтобы Docker кешировал этот слой
COPY requirements.txt requirements-ml.txt ./
RUN pip install -r requirements.txt

# ML-зависимости включены по умолчанию; INSTALL_ML=false — лёгкая сборка без моделей.
# torch ставим CPU-версии, чтобы не тянуть CUDA.
ARG INSTALL_ML=true
RUN if [ "$INSTALL_ML" = "true" ]; then \
        pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision && \
        pip install -r requirements-ml.txt; \
    fi

# Потом код приложения
COPY . .
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
