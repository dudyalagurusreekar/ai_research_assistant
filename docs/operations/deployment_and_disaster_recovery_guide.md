# ARA Version 3.0 — Deployment & Disaster Recovery Guide

## 1. Local & Containerized Deployment

### 1.1 Docker Compose Deployment
To launch the full ARA Version 3.0 Platform stack (ARA service + Redis + Prometheus):

```bash
cd deploy
docker-compose up -d --build
```

Endpoints exposed:
- **API Platform**: `http://localhost:8000`
- **Prometheus Metrics**: `http://localhost:9090`
- **Health Check (`/healthz`)**: `http://localhost:8000/healthz`
- **Readiness Check (`/readyz`)**: `http://localhost:8000/readyz`

---

## 2. Kubernetes Enterprise Deployment

### 2.1 Applying Kubernetes Manifests

```bash
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml
```

### 2.2 Pod Health & Probes
- Liveness Probe: `HTTP GET /healthz` (Port 8000, initial delay 10s)
- Readiness Probe: `HTTP GET /readyz` (Port 8000, initial delay 5s)

---

## 3. Disaster Recovery & Backup Restore Procedures

### 3.1 Creating Backup Snapshots
Snapshots can be created via `PlatformEngine.disaster_recovery` or `PlatformTool`:

```python
from core.platform_infra import PlatformEngine

engine = PlatformEngine()
snapshot = engine.disaster_recovery.create_snapshot(tenant_id="global")
print(f"Snapshot created: {snapshot.snapshot_id}")
```

Snapshots are persisted to `.backups/<snapshot_id>.json`.

### 3.2 Restoring from Backup Snapshot

```python
restored_data = engine.disaster_recovery.restore_snapshot(snapshot.snapshot_id)
print(f"Restored state data: {restored_data}")
```

---

## 4. Security & Access Control

- **JWT Secret Key Configuration**: Set `SECRET_KEY` environment variable in production.
- **RBAC Roles**:
  * `ADMIN`: Full system access (`read`, `write`, `execute`, `admin`, `delete`).
  * `RESEARCHER`: Standard research access (`read`, `write`, `execute`).
  * `VIEWER`: Read-only reporting access (`read`).
