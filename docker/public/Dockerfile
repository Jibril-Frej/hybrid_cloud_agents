FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# Copy only the manifest and install dependencies (not the project source).
# This heavy layer is cached until pyproject.toml changes.
COPY pyproject.toml .
RUN uv pip install --system --no-cache --no-install-project .

# Source and data only invalidate the fast layers below.
COPY src/ src/
COPY data/public/ data/public/

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["uvicorn", "public.main:app", "--host", "0.0.0.0", "--port", "8080"]
