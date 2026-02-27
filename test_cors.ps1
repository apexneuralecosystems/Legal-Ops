# PowerShell CORS Test Script for Legal-Ops Backend
Write-Host "🧪 Testing CORS for Legal-Ops Backend" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Configuration
$BASE_URL = "https://legalops-api.apexneural.cloud"
$FRONTEND_ORIGIN = "https://legalops.apexneural.cloud"

Write-Host "Testing OPTIONS request to /api/auth/login..." -ForegroundColor Yellow
Write-Host ""

try {
    # Test OPTIONS request
    $headers = @{
        "Origin" = $FRONTEND_ORIGIN
        "Access-Control-Request-Method" = "POST"
        "Access-Control-Request-Headers" = "Content-Type, Authorization"
        "User-Agent" = "CORS-Test-Script/1.0"
    }
    
    $response = Invoke-WebRequest -Uri "$BASE_URL/api/auth/login" -Method OPTIONS -Headers $headers -UseBasicParsing
    
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Cyan
    Write-Host "Headers:" -ForegroundColor Cyan
    $response.Headers.GetEnumerator() | ForEach-Object {
        if ($_.Key -like "*Access-Control*" -or $_.Key -like "*Origin*") {
            Write-Host "  $($_.Key): $($_.Value)" -ForegroundColor White
        }
    }
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ PASSED: OPTIONS request successful" -ForegroundColor Green
    } else {
        Write-Host "❌ FAILED: Expected 200, got $($response.StatusCode)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ FAILED: Error during OPTIONS request - $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Testing actual POST request..." -ForegroundColor Yellow
Write-Host ""

try {
    # Test POST request
    $headers = @{
        "Origin" = $FRONTEND_ORIGIN
        "Content-Type" = "application/json"
        "User-Agent" = "CORS-Test-Script/1.0"
    }
    
    $body = @{"email" = "test@example.com"; "password" = "test123"} | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$BASE_URL/api/auth/login" -Method POST -Headers $headers -Body $body -UseBasicParsing
    
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Cyan
    Write-Host "CORS Headers:" -ForegroundColor Cyan
    $response.Headers.GetEnumerator() | ForEach-Object {
        if ($_.Key -like "*Access-Control*" -or $_.Key -like "*Origin*") {
            Write-Host "  $($_.Key): $($_.Value)" -ForegroundColor White
        }
    }
    
    # We expect 401 for invalid credentials, but CORS should work
    if ($response.StatusCode -in @(200, 401)) {
        Write-Host "✅ PASSED: CORS working for POST request" -ForegroundColor Green
    } else {
        Write-Host "❌ FAILED: Unexpected status code $($response.StatusCode)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ FAILED: Error during POST request - $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode
        Write-Host "Status Code: $statusCode" -ForegroundColor Red
        
        # Check for CORS headers even in error response
        if ($_.Exception.Response.Headers) {
            Write-Host "CORS Headers in error response:" -ForegroundColor Yellow
            $_.Exception.Response.Headers.GetEnumerator() | ForEach-Object {
                if ($_.Key -like "*Access-Control*" -or $_.Key -like "*Origin*") {
                    Write-Host "  $($_.Key): $($_.Value)" -ForegroundColor White
                }
            }
        }
        
        # 401 is expected for invalid credentials
        if ($statusCode -eq 401) {
            Write-Host "⚠️  WARNING: Authentication failed but CORS may be working" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "=" * 50 -ForegroundColor Green
Write-Host "✅ Test completed. Check the output above for CORS headers." -ForegroundColor Green
Write-Host "Expected: HTTP 200 for OPTIONS, proper Access-Control-* headers" -ForegroundColor Green