# =============================================================================
# infra/docker/auth-service.Dockerfile
# Spring Boot 3.5.x / Java 21 auth-service
#
# ASSUMPTIONS (app source is currently empty — flagging what this Dockerfile
# assumes about project layout, since none of it could be verified):
#   - Maven project, pom.xml at build context root
#   - Standard Maven layout: src/main/java, src/main/resources
#   - Build produces a single executable jar under target/*.jar via
#     spring-boot-maven-plugin's repackage goal (standard for Spring Boot)
#   - Build context is the repo root, per the docker build examples given
#     (paths below assume auth-service source lives under a subdirectory —
#     adjust COPY paths if your actual repo layout differs)
#
# Build: docker build -f infra/docker/auth-service.Dockerfile -t medmatch/auth-service:v1.0.0 .
# =============================================================================

# ---- Stage 1: Build ----
# eclipse-temurin is the OpenJDK project's official successor to AdoptOpenJDK
# images; -jammy gives a full Ubuntu userland for the build stage where Maven
# and any native-compile transitive deps need a complete toolchain available.
FROM eclipse-temurin:21-jdk-jammy AS build

WORKDIR /build

# Copy only the POM first so Docker layer caching keeps dependency downloads
# cached across builds unless pom.xml itself changes — avoids re-downloading
# the full Maven dependency tree on every source change.
COPY services/auth-service/pom.xml .
COPY services/auth-service/.mvn/ .mvn/
COPY services/auth-service/mvnw .

RUN chmod +x mvnw && ./mvnw dependency:go-offline -B

COPY services/auth-service/src ./src

# Now copy source and build. Tests skipped in the Docker build per
# requirements — this assumes tests run in a separate CI stage before this
# image is ever built, not that testing is skipped entirely.
RUN ./mvnw clean package -DskipTests -B \
    && mv target/*.jar target/app.jar

# ---- Stage 2: Runtime ----
# JRE (not JDK) — no compiler, no build tooling needed at runtime, meaningfully
# smaller and reduces attack surface. -jammy (not -alpine) chosen deliberately:
# Alpine's musl libc has a history of subtle JVM compatibility issues
# (thread-stack sizing, DNS resolution edge cases); Temurin's official
# guidance favors glibc-based images for production JVM workloads.
FROM eclipse-temurin:21-jre-jammy

# Non-root user with no login shell and no home directory contents beyond
# what's needed — least privilege for the running container.
RUN groupadd --system --gid 1000 spring \
    && useradd --system --uid 1000 --gid spring --no-create-home spring

WORKDIR /app
COPY --from=build --chown=spring:spring /build/target/app.jar app.jar

USER spring
EXPOSE 8081

# No values are hardcoded here — SPRING_PROFILES_ACTIVE, SPRING_DATASOURCE_*,
# and JWT_PRIVATE_KEY/JWT_PUBLIC_KEY all arrive as environment variables
# injected by Kubernetes (auth-service/deployment.yaml's envFrom + env), per
# Spring Boot's relaxed environment-variable property binding — nothing in
# this image needs to know their values at build time.
ENTRYPOINT ["java", "-jar", "app.jar"]
