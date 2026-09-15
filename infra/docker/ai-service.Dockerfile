FROM python:3.12-slim AS build

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/ai-service/requirements.txt .

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV HF_HOME="/opt/huggingface"
ENV TRANSFORMERS_CACHE="/opt/huggingface"

RUN pip install --upgrade pip \
    && pip install --retries 10 --timeout 120 -r requirements.txt
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# ---- Stage 2: Runtime ----

FROM python:3.12-slim

RUN groupadd --system --gid 1000 fastapi \
    && useradd --system --uid 1000 --gid fastapi --no-create-home fastapi

COPY --from=build /opt/venv /opt/venv
COPY --from=build /opt/huggingface /opt/huggingface

ENV PATH="/opt/venv/bin:$PATH"
ENV HF_HOME="/opt/huggingface"
ENV TRANSFORMERS_CACHE="/opt/huggingface"

WORKDIR /app

RUN mkdir -p /app/uploads \
    && chown -R fastapi:fastapi /app/uploads

COPY --chown=fastapi:fastapi services/ai-service/app ./app
COPY --chown=fastapi:fastapi services/ai-service/models ./models

# alembic.ini and alembic/ are required for the ai-migrate Job
# (`alembic upgrade head`) to run inside this same image - without
# these, the alembic package is installed but has no config/versions
# to find. Not needed by the running ai-service app itself, but
# copying them here means this one image serves both purposes rather
# than needing a second, migration-only image to maintain.
COPY --chown=fastapi:fastapi services/ai-service/alembic.ini ./alembic.ini
COPY --chown=fastapi:fastapi services/ai-service/alembic ./alembic

USER fastapi

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]