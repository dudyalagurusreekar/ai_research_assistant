# ARA Version 3.0 Platform Dockerfile
FROM python:3.13-slim as base

WORKDIR /app

# Install platform system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true

COPY . .

EXPOSE 8000 9090

ENV PYTHONUNBUFFERED=1
ENV ARA_ENV=production

CMD ["python", "-m", "core.platform.engine"]
