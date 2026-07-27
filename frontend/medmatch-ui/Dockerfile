# ==========================================================
# Stage 1 - Build
# ==========================================================
FROM node:22-alpine AS builder

WORKDIR /app

# Copy dependency files first for better layer caching
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application source
COPY . .

# Build production assets
RUN npm run build

# ==========================================================
# Stage 2 - Runtime
# ==========================================================
FROM nginx:1.29-alpine

LABEL org.opencontainers.image.title="MedMatch Frontend"
LABEL org.opencontainers.image.description="React Frontend for MedMatch"
LABEL org.opencontainers.image.vendor="MedMatch"
LABEL org.opencontainers.image.version="1.0.0"

# Remove default Nginx content
RUN rm -rf /usr/share/nginx/html/*

# Copy production build
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s \
            --timeout=5s \
            --start-period=10s \
            --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost || exit 1

CMD ["nginx", "-g", "daemon off;"]