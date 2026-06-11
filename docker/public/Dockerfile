# Public worker image — runs in the PUBLIC cluster.
# Build from the repo root: docker build -f docker/public/Dockerfile -t public-worker:latest .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ src/

RUN uv sync --frozen --no-dev

# `uv run` re-syncs (incl. dev deps) by default; skip that at container start.
ENV UV_NO_SYNC=1

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "public.main:app", "--host", "0.0.0.0", "--port", "8001"]
