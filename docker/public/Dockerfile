FROM python:3.11-slim

WORKDIR /app

# Install dependencies first so this heavy layer is cached independently of
# source changes. It only re-runs when requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source and data invalidate only the fast layers below.
COPY src/ src/
COPY data/public/ data/public/

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["uvicorn", "public.main:app", "--host", "0.0.0.0", "--port", "8080"]
