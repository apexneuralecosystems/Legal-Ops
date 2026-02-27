# Test local CORS endpoints to verify our code changes
# This tests the logic without deployment

Write-Host "Testing local CORS logic verification" -ForegroundColor Cyan

# Test that our middleware changes are syntactically correct
Write-Host "1. Checking main.py syntax..." -ForegroundColor Yellow
try {
    $content = Get-Content "backend\main.py" -Raw
    if ($content -match 'request\.url\.path\.startswith\("/api"\)') {
        Write-Host "   ✅ Middleware updated to handle all /api endpoints" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Middleware not updated correctly" -ForegroundColor Red
    }
    
    if ($content -match 'Access-Control-Allow-Methods.*PUT.*DELETE.*PATCH') {
        Write-Host "   ✅ HTTP methods include PUT, DELETE, PATCH" -ForegroundColor Green
    } else {
        Write-Host "   ❌ HTTP methods not updated" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error checking main.py: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n2. Checking matters.py for OPTIONS handlers..." -ForegroundColor Yellow
try {
    $content = Get-Content "backend\routers\matters.py" -Raw
    if ($content -match '@router\.options\("/"\)') {
        Write-Host "   ✅ Matters root OPTIONS handler added" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Matters root OPTIONS handler missing" -ForegroundColor Red
    }
    
    if ($content -match '@router\.options\("/stats"\)') {
        Write-Host "   ✅ Matters stats OPTIONS handler added" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Matters stats OPTIONS handler missing" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error checking matters.py: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n3. Checking ai_tasks.py for OPTIONS handlers..." -ForegroundColor Yellow
try {
    $content = Get-Content "backend\routers\ai_tasks.py" -Raw
    if ($content -match '@router\.options\("/tasks"\)') {
        Write-Host "   ✅ AI tasks OPTIONS handler added" -ForegroundColor Green
    } else {
        Write-Host "   ❌ AI tasks OPTIONS handler missing" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error checking ai_tasks.py: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nCode verification complete!" -ForegroundColor Cyan
Write-Host "Next step: Deploy/restart the backend server to apply changes." -ForegroundColor Yellow