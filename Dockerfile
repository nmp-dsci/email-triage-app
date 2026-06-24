# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

RUN pip install --no-cache-dir "uv>=0.5,<1"

WORKDIR /build

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project


FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    HOST=0.0.0.0 \
    PORT=8000 \
    RUNS_DIR=/app/runs

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libmagic1 \
        poppler-utils \
        tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app --create-home app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app app ./app

RUN mkdir -p /app/runs && chown -R app:app /app

USER app

EXPOSE 8000
VOLUME ["/app/runs"]

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
