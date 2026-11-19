# EvalForge Local Runner Script (Windows PowerShell)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   EvalForge: LLM Evaluation & Observability Platform   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$baseDir = Split-Path -Parent $PSScriptRoot

# 1. Seed and start Backend
Write-Host "`n[1/2] Initializing database & seeding demo records..." -ForegroundColor Yellow
Set-Location "$baseDir\backend"
$env:PYTHONPATH = "."
python seed_data.py

Write-Host "`nStarting FastAPI backend server on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$baseDir\backend'; `$env:PYTHONPATH='.'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

# 2. Start Frontend
Write-Host "`n[2/2] Starting Next.js frontend on http://localhost:3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$baseDir\frontend'; npm run dev"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "EvalForge is launching!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "Backend API & Docs: http://127.0.0.1:8000/api/v1/docs" -ForegroundColor White
Write-Host "Demo Credentials: demo@evalforge.dev / evalforge123" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
