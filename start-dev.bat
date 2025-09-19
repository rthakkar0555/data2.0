@echo off
echo Starting Manual Retrieval System...
echo.

echo Starting Backend Server...
cd backend
start "Backend Server" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak > nul

echo.
echo Starting Frontend Server...
cd ..\..
start "Frontend Server" cmd /k "npm run dev"

echo.
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause > nul
