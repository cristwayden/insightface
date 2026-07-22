# start_server.ps1 - Auto kill port 5005 then start server

$PORT = 5005

Write-Host "Checking port $PORT..." -ForegroundColor Cyan

$existing = netstat -ano | findstr ":$PORT " | Where-Object { $_ -match "LISTENING" }

if ($existing) {
    $pid_match = $existing -replace '.*\s+(\d+)\s*$', '$1'
    Write-Host "Found process on port $PORT (PID: $pid_match). Killing..." -ForegroundColor Yellow
    taskkill /PID $pid_match /F | Out-Null
    Start-Sleep -Seconds 1
    Write-Host "Process killed." -ForegroundColor Green
} else {
    Write-Host "Port $PORT is free." -ForegroundColor Green
}

Write-Host "Starting server..." -ForegroundColor Cyan
python -m uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload --reload-dir app
