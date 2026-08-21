# =============================================================================
# infra/docker/frontend.Dockerfile
# React + Vite + TypeScript frontend, served via nginx
#
# ASSUMPTIONS (app source is currently empty):
#   - package.json / package-lock.json at frontend/ (build context root
#     subdirectory), standard Vite project layout
#   - `npm run build` outputs static assets to frontend/dist (Vite's default
#     output directory)
#   - Build context is the repo root, per the docker build examples given
#
# Build: docker build -f infra/docker/frontend.Dockerfile -t medmatch/frontend:v1.0.0 .
#
# NOTE ON VITE_* BUILD-TIME VARIABLES: this is exactly the assumption
# flagged when frontend/deployment.yaml was built — Vite bakes VITE_*
# variables into the JS bundle at THIS build step, not at container
# runtime. If VITE_API_BASE_URL needs to vary per-environment, it must be
# passed as a `--build-arg` here and consumed via ARG/ENV in Stage 1 below,
# NOT relied upon as a Kubernetes runtime env var (which currently has no
# effect on the built bundle). Left as a plain build with no build-arg for
# now since no CI/CD pipeline details were provided — add one if per-
# environment API URLs are required.
# =============================================================================

# ---- Stage 1: Build ----
# Node 22 per requirements. -alpine used ONLY for this throwaway build
# stage (never shipped in the final image) — smaller pull, and none of the
# musl-compatibility concerns that apply to Python ML libraries apply here,
# since npm/Vite tooling doesn't compile native extensions in the typical
# case.
FROM node:22-alpine AS build

WORKDIR /build

ARG VITE_AUTH_API_URL=/api/auth
ARG VITE_AI_API_URL=/api/ai

ENV VITE_AUTH_API_URL=$VITE_AUTH_API_URL
ENV VITE_AI_API_URL=$VITE_AI_API_URL

# Dependency layer cached separately from source, same rationale as the
# Maven/pip caching in the other Dockerfiles.
COPY frontend/medmatch-ui/package.json frontend/medmatch-ui/package-lock.json ./

RUN npm ci


COPY frontend/medmatch-ui/ .
RUN npm run build

# ---- Stage 2: Runtime ----
# nginx:1.27-alpine — small, well-maintained, standard choice for serving a
# static SPA build. Reconfigured below to run fully as a non-root user,
# which is why several defaults (pid path, cache dirs, listen port) are
# overridden rather than left at the image's defaults.
FROM nginx:1.27-alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY infra/docker/nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p \
    /tmp/nginx/client_temp \
    /tmp/nginx/proxy_temp \
    /var/cache/nginx \
    && touch /tmp/nginx.pid \
    && chown -R nginx:nginx \
       /tmp/nginx \
       /tmp/nginx.pid \
       /var/cache/nginx

COPY --from=build --chown=nginx:nginx /build/dist /usr/share/nginx/html

USER nginx

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]