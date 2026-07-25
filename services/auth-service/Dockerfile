# ==========================================================
# Stage 1 - Build
# ==========================================================
FROM maven:3.9.11-eclipse-temurin-21 AS builder

WORKDIR /app

# Copy Maven wrapper and project metadata first for better layer caching
COPY pom.xml .
COPY mvnw .
COPY .mvn .mvn

RUN chmod +x mvnw

# Download dependencies
RUN ./mvnw dependency:go-offline --no-transfer-progress

# Copy source code
COPY src ./src

# Build application
RUN ./mvnw clean package \
    -DskipTests \
    --no-transfer-progress

# ==========================================================
# Stage 2 - Runtime
# ==========================================================
FROM eclipse-temurin:21-jre

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# OCI Image Metadata
LABEL org.opencontainers.image.title="MedMatch Auth Service"
LABEL org.opencontainers.image.description="Spring Boot Authentication Service for MedMatch"
LABEL org.opencontainers.image.vendor="MedMatch"
LABEL org.opencontainers.image.version="1.0.0"

WORKDIR /app

# Create a non-root user
RUN useradd --create-home --shell /bin/bash spring

# Copy the built JAR
COPY --from=builder /app/target/*.jar app.jar

# Set ownership
RUN chown spring:spring app.jar

USER spring

# Expose application port
EXPOSE 8081

# Spring profile
ENV SPRING_PROFILES_ACTIVE=prod

# Optional JVM options (can be overridden via Docker Compose)
ENV JAVA_OPTS=""

# Start application
ENV JAVA_OPTS=""

ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar app.jar"]