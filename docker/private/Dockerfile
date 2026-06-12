# Orchestrator image — runs in the PRIVATE cluster.
# Build from the repo root: docker build -f docker/private/Dockerfile -t orchestrator:latest .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ src/
COPY data/private/ data/private/

RUN uv sync --frozen --no-dev

# `uv run` re-syncs (incl. dev deps) by default; skip that at container start.
ENV UV_NO_SYNC=1

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000"]
