# Multi-Stage Production Dockerfile for AI Research Assistant Platform
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment / requirement files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production runtime stage
FROM python:3.13-slim AS runner

WORKDIR /app

# Create non-root user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10000 -g appgroup -s /bin/bash appuser

# Install Playwright browser dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy python site-packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy codebase
COPY . .

# Set permissions
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000

# Healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/liveness || exit 1

CMD ["python", "-m", "pytest", "tests/"]
