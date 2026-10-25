FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PHISHGUARD_MODEL_PATH=/app/artifacts/model.joblib

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install .

COPY artifacts/model.joblib ./artifacts/model.joblib

EXPOSE 8000

CMD ["uvicorn", "phishguard.api:app", "--host", "0.0.0.0", "--port", "8000"]
