# AI Research Assistant Platform - Production Deployment Guide

## Version 1.0 Release Candidate

This document provides step-by-step instructions for deploying the **AI Research Assistant Platform** (Architecture Version 1.0) into production environments using Docker, Docker Compose, or Kubernetes.

---

## 1. System Requirements & Prerequisites

- **Python**: 3.10+ (Python 3.13 recommended)
- **Container Runtime**: Docker 20.10+ / Containerd
- **Orchestration**: Kubernetes 1.25+ / Docker Compose 2.0+
- **Memory**: Minimum 2 GB RAM (4 GB recommended)
- **Storage**: Minimum 10 GB disk space for persistent artifacts

---

## 2. Environment Configuration Reference

Configure the following environment variables in `.env` or your secret store:

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` | Deployment environment (`development`, `staging`, `production`) |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `PORT` | `8000` | HTTP service listening port |
| `MAX_CONCURRENT_WORKFLOWS` | `20` | Maximum parallel workflow tasks |

---

## 3. Docker Container Deployment

### Local Docker Build & Run
```bash
# Build image
docker build -t ai-research-assistant:1.0.0 .

# Run container
docker run -d --name ai_assistant -p 8000:8000 --env-file .env ai-research-assistant:1.0.0
```

### Docker Compose Deployment
```bash
docker-compose up -d --build
```

---

## 4. Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f deployment/k8s-manifests.yaml

# Verify pod status and readiness
kubectl get pods -l app=ai-research-assistant
```
