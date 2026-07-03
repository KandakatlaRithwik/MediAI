# ============================================================
# Stage 1: Dependency builder
# Keeps build tools out of the final image.
# ============================================================
FROM python:3.12-slim AS builder

# System packages needed to compile some Python wheels
# (psycopg2, bcrypt, opencv, easyocr, tesseract).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt


# ============================================================
# Stage 2: Runtime image
# ============================================================
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="Medical Assistant Backend"
LABEL org.opencontainers.image.description="AI-Powered Medical Assistant — FastAPI backend"
LABEL org.opencontainers.image.version="1.5.0"

# Runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built Python packages from builder stage.
COPY --from=builder /install/deps /usr/local

# Create a non-root user for security.
RUN groupadd --gid 1001 medapp && \
    useradd  --uid 1001 --gid medapp --shell /bin/bash --create-home medapp

WORKDIR /app

# Copy application code.
COPY --chown=medapp:medapp . .

# Create runtime directories that must exist before the app starts.
RUN mkdir -p /app/logs /app/uploads /app/chroma_db && \
    chown -R medapp:medapp /app/logs /app/uploads /app/chroma_db

USER medapp

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8000

# Health check: hits the lightweight /health endpoint.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
