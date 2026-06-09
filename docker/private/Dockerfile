FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# Copy manifest and lockfile. The dep-install layer is only re-run when
# pyproject.toml or uv.lock changes (i.e. a dependency is added/removed).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --system

# Source and data only invalidate the fast layers below.
COPY src/ src/
COPY data/private/ data/private/

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8080"]
