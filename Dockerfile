# Multi-stage image for the MAS marketing simulation.
#   docker build -t mas-marketing .                 -> runtime image
#   docker build --target test -t mas-test .        -> runs the unit tests during the build
ARG BASE_IMAGE=python:3.12-slim

# ---------- 1. builder: compile/download wheels once ----------
FROM ${BASE_IMAGE} AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY requirements.txt requirements-dev.txt ./
RUN pip wheel --wheel-dir /wheels -r requirements-dev.txt
COPY pyproject.toml ./
COPY src ./src
RUN pip wheel --no-deps --wheel-dir /wheels .

# ---------- 2. test: run pytest inside the container ----------
FROM ${BASE_IMAGE} AS test
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=builder /wheels /wheels
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-index --find-links=/wheels -r requirements-dev.txt mas-marketing
COPY tests ./tests
COPY pyproject.toml ./
RUN python -m pytest -q

# ---------- 3. runtime: minimal, non-root ----------
FROM ${BASE_IMAGE} AS runtime
LABEL org.opencontainers.image.title="mas-marketing" \
      org.opencontainers.image.description="Multi-agent simulation of marketing situations (BA network, 3 brands)" \
      org.opencontainers.image.source="https://github.com/blessedmysterio/Multi-Agent-Simulation-of-Marketing-Situations" \
      org.opencontainers.image.authors="Nadir <255276@astanait.edu.kz>"
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels numpy scipy networkx mas-marketing \
 && rm -rf /wheels \
 && mkdir -p /app/results && chown -R 10001:10001 /app
WORKDIR /app
USER 10001
VOLUME ["/app/results"]
ENTRYPOINT ["python", "-m", "mas_marketing"]
CMD ["--runs", "30", "--out", "/app/results"]
