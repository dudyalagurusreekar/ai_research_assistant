# ARA v1.0 Sprint 3 Architecture Document — Core Backend API Platform

## 1. Executive Summary

Sprint 3 builds the production-grade **Core Backend REST API Platform** for the AI Research Assistant (ARA v1.0). Following Clean Architecture principles, it isolates API Controllers/Routers (`services/api/routes/`), Business Domain Services (`services/api/services/`), Database Repositories (`infrastructure/database/repositories/`), and Pydantic DTOs.

It introduces standardized request/response envelopes (`ResponseEnvelope[T]`), `X-Correlation-ID` request tracing, global exception handling, OpenAPI/Swagger (`/docs`) and ReDoc (`/redoc`) auto-generation, and full integration with the PostgreSQL, Redis, MinIO, and authentication infrastructure established in Sprints 1 & 2.

---

## 2. Clean Architecture Layer Diagram

```mermaid
graph TD
    WEB[Next.js Frontend / API Client] -->|HTTP / JSON| CORR[CorrelationIDMiddleware]
    CORR --> ROUTER[FastAPI REST Routers<br>/api/v1/*]
    ROUTER --> DEP[FastAPI Security & DB Dependencies]
    DEP --> SVC[Domain Services Layer<br>ProjectService, ResearchService, DocumentService, ReportService, BrowserWorkflowService, WorkflowService, UserSettingService]
    
    subgraph Data & Storage Layer (Sprints 1 & 2)
        SVC --> REPO[Database Repositories<br>PostgreSQL DDL & pgvector]
        SVC --> MINIO[(MinIO S3 Object Storage<br>8 Dedicated Buckets)]
        SVC --> REDIS[(Redis Cache & Session State)]
    end
    
    ROUTER --> ENV[Standardized JSON Envelope & Global Exception Handler]
    ENV -->|ResponseEnvelope[T]| WEB
```

---

## 3. Core API Endpoint Matrix

| Domain Module | Route Prefix | Method | Description |
|---|---|---|---|
| **Authentication** | `/api/v1/auth` | `POST` | `/register`, `/login`, `/logout`, `/refresh`, `/verify-email`, `/forgot-password`, `/reset-password` |
| **User Profile & Admin** | `/api/v1/users` | `GET/PATCH` | `/me`, `/me/change-password`, `GET /` (Admin), `PATCH /{user_id}/role` (Admin) |
| **Projects & Workspaces** | `/api/v1/projects` | `GET/POST/PATCH/DELETE` | `/`, `/{id}`, `/{id}/workspaces` |
| **Research Sessions** | `/api/v1/research/sessions` | `GET/POST` | `/`, `/{id}`, `/{id}/conversations` |
| **Conversations & Messages**| `/api/v1/conversations` | `GET/POST` | `/{id}/messages` |
| **Knowledge Base & RAG** | `/api/v1/workspaces/{id}/documents` | `POST/GET` | `/upload`, `/`, `/search` (Hybrid Vector RAG via `gemini-embedding-2`) |
| **Reports & Exports** | `/api/v1/reports` | `GET/POST` | `/research/sessions/{id}/reports`, `/{id}`, `/{id}/download` (Presigned URL) |
| **Browser Automation** | `/api/v1/browser` | `POST` | `/sessions`, `/sessions/{id}/navigate`, `/sessions/{id}/screenshot` |
| **Workflows & Executions** | `/api/v1/workflows` | `GET/POST` | `/`, `/{id}/execute`, `/workflow-executions/{id}` |
| **Settings & Preferences** | `/api/v1/settings` | `GET/PATCH` | `/system`, `/user` |
| **Health & Monitoring** | `/health` | `GET` | `/liveness`, `/readiness`, `/metrics` |

---

## 4. Response Envelope Specification

Every endpoint returns a standardized JSON structure:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total_items": 100,
    "total_pages": 5
  },
  "error": null,
  "correlation_id": "req-9a8b7c6d5e4f"
}
```

---

## 5. Verification & Test Pass Matrix

- **Sprint 3 API Test Suite**: `tests/api/` (**6 test files, 15 API integration test cases, 100% pass rate**)
- **Sprint 2 Auth Test Suite**: `tests/auth/` (**5 test files, 16 auth test cases, 100% pass rate**)
- **Full Workspace Test Suite**: `pytest evaluation/tests tests/decision_intelligence tests/infrastructure tests/auth tests/api` (**74/74 workspace tests passed**)
