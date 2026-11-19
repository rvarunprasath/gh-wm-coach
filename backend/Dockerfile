# ==============================================================================
# GH Wealth Management AI Coach - Backend Dockerfile
# Optimized for Google Cloud Run (FastAPI + AlloyDB/PostgreSQL + Gemini AI)
# ==============================================================================
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies needed for compiling C extensions (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app
COPY run.py .

# Create non-root user for security best practice on Cloud Run
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /tmp

USER appuser

EXPOSE 8080

# Run FastAPI using uvicorn on $PORT (set dynamically by Cloud Run)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2"]
