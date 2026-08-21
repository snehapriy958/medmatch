FROM python:3.12-slim AS build

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/ai-service/requirements.txt .

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ---- Stage 2: Runtime ----

FROM python:3.12-slim

RUN groupadd --system --gid 1000 fastapi \
    && useradd --system --uid 1000 --gid fastapi --no-create-home fastapi

COPY --from=build /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV HF_HOME="/tmp/huggingface"
ENV TRANSFORMERS_CACHE="/tmp/huggingface"

WORKDIR /app

COPY --chown=fastapi:fastapi services/ai-service/app ./app
COPY --chown=fastapi:fastapi services/ai-service/keys ./keys
COPY --chown=fastapi:fastapi services/ai-service/models ./models

USER fastapi

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]