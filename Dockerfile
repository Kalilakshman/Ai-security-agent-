# Multi-stage secure Dockerfile for AI Security Orchestrator CLI
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt README.md ./
COPY app ./app
COPY core ./core
COPY plugins ./plugins
COPY memory ./memory
COPY reports ./reports
COPY config ./config

RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS final

WORKDIR /app

# Install security assessment binaries in container environment
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    whatweb \
    nikto \
    gobuster \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY config ./config

# Run as non-root unprivileged user for DevSecOps safety
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["security-ai"]
CMD ["--help"]
