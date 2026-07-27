# AI Research Assistant Platform - Operational Runbook & Troubleshooting Guide

## Version 1.0 Release Candidate

This runbook outlines diagnostic procedures, health check monitoring, incident response steps, and recovery protocols for the AI Research Assistant Platform.

---

## 1. Health Probe Diagnostics

The platform exposes liveness and readiness health check endpoints via `HealthCheckManager`:

- **Liveness Probe**: `/health/liveness`
  - Returns `200 OK` if the process loop is responsive.
- **Readiness Probe**: `/health/readiness`
  - Evaluates health status across all 11 platform pillars (`core_foundation`, `shared_infrastructure`, `browser_tool`, `document_platform`, `search_platform`, `memory_platform`, `code_platform`, `vision_platform`, `integration_platform`, `workflow_engine`, `report_platform`).

---

## 2. Common Operational Issues & Remediation

### Issue 1: High Memory Usage during Document Parsing
- **Symptom**: Memory consumption spikes during large PDF / OCR processing.
- **Root Cause**: Large binary stream processing in memory.
- **Remediation**:
  - Verify chunked streaming in `DocumentToolFacade`.
  - Adjust worker process memory limits in Kubernetes deployment specs.

### Issue 2: External API Integration Timeouts
- **Symptom**: `IntegrationToolFacade` returns HTTP 504.
- **Root Cause**: Downstream REST / GraphQL endpoint delay.
- **Remediation**:
  - `RequestPipeline` automatically triggers retry and circuit breaking.
  - Inspect `integration.failed` domain events over `AsyncEventBus`.

---

## 3. Disaster Recovery & Snapshot Restoration

1. **State Checkpoints**: `WorkflowStateManager` automatically saves execution snapshots into `DiskStorage`.
2. **Restoration**: Pass the saved `checkpoint_id` into `WorkflowEngineFacade.resume_workflow(checkpoint_id)`.
