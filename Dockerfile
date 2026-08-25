FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && pip install "poetry==$POETRY_VERSION" \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN poetry lock

RUN poetry install --only main --no-root

COPY ./app ./app

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]