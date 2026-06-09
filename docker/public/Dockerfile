FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

COPY data/public/ data/public/

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["uvicorn", "public.main:app", "--host", "0.0.0.0", "--port", "8080"]
