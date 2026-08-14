# AI Research Assistant (ARA) v1.0.0 — Production Deployment Guide

This guide provides step-by-step instructions for deploying **AI Research Assistant (ARA) v1.0.0** into production environments using Docker Compose, Nginx Reverse Proxy, PostgreSQL (pgvector), Redis, MinIO, Prometheus, Grafana, and Kubernetes.

---

## 1. System Requirements & Prerequisites

- **OS**: Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9), macOS, or Windows Server
- **Docker**: Docker Engine 24.0+ & Docker Compose v2.20+
- **Memory**: Minimum 4 GB RAM (8 GB recommended for heavy RAG & browser automation)
- **CPU**: 2+ vCPU cores
- **Disk**: 20 GB persistent storage for vector indices, database files, and MinIO artifacts

---

## 2. Production Docker Compose Stack

### Launch Production Stack
```bash
# 1. Clone repository
git clone https://github.com/dudyalagurusreekar/ai_research_assistant.git
cd ai_research_assistant

# 2. Configure production environment
cp .env.example .env

# 3. Launch full production multi-container stack
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify running containers
docker compose -f docker-compose.prod.yml ps
```

### Stack Components
- **Nginx Reverse Proxy** (`:80`): Rate-limiting, SSL/TLS, Security Headers, Proxying to API backend
- **ARA Application Server** (`:8000` internal): Multi-stage non-root Python container
- **PostgreSQL + pgvector** (`:5432`): Relational data and vector embedding storage
- **Redis Cache** (`:6379`): Session state and execution caching
- **MinIO Object Storage** (`:9000`, `:9001`): Report PDF, artifact, download, and screenshot storage
- **Prometheus** (`:9090`): Application metric scraper
- **Grafana** (`:3000`): Production dashboard visualization

---

## 3. Observability & Telemetry Verification

- **API Liveness Probe**: `curl -f http://localhost/health`
- **Prometheus Scrape Endpoint**: `curl http://localhost/metrics`
- **Grafana Dashboards**: Access `http://localhost:3000` (User: `admin`, Password: `admin_production_password`)

---

## 4. Automated Backup & Recovery Strategy

### Running Database & Object Storage Backups
```bash
# Execute automated backup script
python scripts/backup_db.py
```
Backups are saved to `.storage/backups/postgres_backup_<timestamp>.json` and `.storage/backups/minio_snapshot_<timestamp>.json`.

---

## 5. Security & Vulnerability Auditing

```bash
# Run security audit script
python scripts/security_scan.py
```
Validates zero hardcoded secrets, non-root container user compliance, and dependency security.
