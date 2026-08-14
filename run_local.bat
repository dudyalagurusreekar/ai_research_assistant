@echo off
echo =======================================================
echo     Starting AI Research Assistant Locally
echo =======================================================

echo.
echo [1/3] Starting local infrastructure (Postgres, Redis, MinIO)...
docker compose up -d

echo.
echo [2/3] Starting FastAPI Backend...
if not exist .venv (
    echo [ERROR] Virtual environment not found. Please create one and install requirements.txt
) else (
    start "ARA Backend" cmd /c ".venv\Scripts\uvicorn.exe services.api.app:app --host 127.0.0.1 --port 8000 --reload"
)

echo.
echo [3/3] Starting Next.js Frontend...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
)
start "ARA Frontend" cmd /c "npm run dev"
cd ..

echo.
echo =======================================================
echo All services are spinning up in separate windows!
echo - Backend API will be available at: http://localhost:8000
echo - Frontend UI will be available at: http://localhost:3000 (once compiled)
echo =======================================================
echo You can close this window now. The services will remain running in their respective command prompts.
pause
