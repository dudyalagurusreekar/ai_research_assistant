"""FastAPI Application Server Assembly for ARA v1.0 Core Backend API Platform."""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from core.auth.routes import router as auth_router
from core.users.routes import router as users_router
from services.api.middleware.correlation import CorrelationIDMiddleware
from services.api.middleware.exception_handler import (
    http_exception_handler,
    permission_error_handler,
    unhandled_exception_handler,
    validation_exception_handler,
    value_error_handler,
)
from services.api.routes.analytics import router as analytics_router
from services.api.routes.browser import router as browser_router
from services.api.routes.documents import router as documents_router
from services.api.routes.health import router as health_router
from services.api.routes.orchestration import router as orchestration_router
from services.api.routes.planner import router as planner_router
from services.api.routes.projects import router as projects_router
from services.api.routes.rag import router as rag_router
from services.api.routes.reports import router as reports_router
from services.api.routes.research import router as research_router
from services.api.routes.settings import router as settings_router
from services.api.routes.workflows import router as workflows_router
from services.api.routes.knowledge import router as knowledge_router
from services.api.routes.evaluation import router as evaluation_router
from services.api.routes.connectors import router as connectors_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-Grade Clean Architecture Core API Platform for AI Research Assistant (ARA)",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. Attach Middleware
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.exceptions import HTTPException as StarletteHTTPException

# 2. Attach Global Exception Handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(PermissionError, permission_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# 3. Mount All REST API Routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(browser_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(planner_router, prefix="/api/v1")
app.include_router(orchestration_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(evaluation_router, prefix="/api/v1")
app.include_router(connectors_router, prefix="/api/v1")
app.include_router(health_router)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.api.app:app", host="0.0.0.0", port=8000, reload=True)
