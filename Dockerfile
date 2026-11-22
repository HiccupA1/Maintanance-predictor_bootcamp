# API image (ADR-0008). One image serves the API and runs migrations:
#   docker run ... image                      -> API on :8000
#   docker run ... image alembic upgrade head -> release-time migration
#
# Multi-stage: dependencies are built into a virtualenv in the builder, and
# the runtime stage copies only that venv and the source. It runs as a
# non-root user with a read-only-friendly layout.

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml README.md ./
COPY app ./app
COPY ml ./ml
# The ml extra is required for risk scoring (WP4).
RUN pip install ".[ml]"

FROM python:${PYTHON_VERSION}-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production \
    MODEL_STORE_DIR=/srv/model_store \
    OMP_NUM_THREADS=1
# Pick up Debian security fixes released after the base image was built
# (Trivy gates the image on fixable CRITICAL/HIGH CVEs).
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*
RUN groupadd --system app && useradd --system --gid app --home /srv app
WORKDIR /srv
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app app ./app
COPY --chown=app:app ml ./ml
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app scripts ./scripts
RUN mkdir -p /srv/model_store && chown app:app /srv/model_store
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/v1/health', timeout=2).status == 200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
