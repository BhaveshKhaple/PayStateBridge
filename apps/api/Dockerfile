FROM python:3.12-slim

WORKDIR /app

# System deps (none heavy needed for sqlite/aiosqlite)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV APP_ENV=demo
ENV PORT=8000

# Seed the demo DB at build so the deployed instance has synthetic cases
RUN python -m app.db.seed || true

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
