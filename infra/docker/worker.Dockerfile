# =============================================================================
# infra/docker/worker.Dockerfile
# Celery worker — SAME codebase and dependencies as ai-service, per
# architecture requirements. This is intentionally near-identical to
# ai-service.Dockerfile: both build definitions are meant to produce the
# same final image (medmatch/ai-service:v1.0.0), just invoked with a
# different runtime command. Kubernetes' worker/deployment.yaml already
# overrides the container's `command` entirely, so the CMD below only
# matters if this image is ever run directly outside Kubernetes (e.g. local
# testing via `docker run`).
#
# ASSUMPTIONS: same as ai-service.Dockerfile — requirements.txt at
# ai-service/requirements.txt, application package at ai-service/app/, with
# the Celery app instance importable as app.celery.celery_app (this is the
# real path — see the flagged mismatch against worker/deployment.yaml's
# current placeholder, noted separately).
#
# Build: docker build -f infra/docker/worker.Dockerfile -t medmatch/ai-service:v1.0.0 .
# =============================================================================

# ---- Stage 1: Build dependencies ----
# Identical base and reasoning as ai-service.Dockerfile's build stage — see
# that file's comments for why slim+glibc over alpine.
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
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# ---- Stage 2: Runtime ----
FROM python:3.12-slim

RUN groupadd --system --gid 1000 celery \
    && useradd --system --uid 1000 --gid celery --no-create-home celery

COPY --from=build /opt/venv /opt/venv
COPY --from=build /opt/huggingface /opt/huggingface
ENV PATH="/opt/venv/bin:$PATH"
ENV HF_HOME="/opt/huggingface"
ENV TRANSFORMERS_CACHE="/opt/huggingface"

WORKDIR /app

COPY --chown=celery:celery services/ai-service/app ./app

USER celery

# No EXPOSE — a Celery worker doesn't accept inbound connections, it only
# pulls from the Redis broker, matching the "worker: no port" requirement.

# DATABASE_URL, DATABASE_USERNAME, DATABASE_PASSWORD, CELERY_BROKER_URL,
# CELERY_RESULT_BACKEND, LLM_API_KEY all arrive via Kubernetes envFrom/env
# (worker/deployment.yaml) — none are baked in here.
#
# This default CMD is overridden by Kubernetes' explicit `command:` in
# worker/deployment.yaml; kept here only so the image is runnable standalone.
CMD ["celery", "-A", "app.celery.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
