FROM python:3.11-slim

WORKDIR /app

# Install dependencies first — this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source and data are copied after so code changes don't bust the dep cache.
COPY src/ src/
COPY data/private/ data/private/

ENV PYTHONPATH=/app/src

EXPOSE 8080

# Seed the private Chroma index from the bundled data files on every start.
# The emptyDir volume is fresh each time, so ingest must run before the server.
CMD ["sh", "-c", "python -m private.ingest && uvicorn orchestrator.main:app --host 0.0.0.0 --port 8080"]
