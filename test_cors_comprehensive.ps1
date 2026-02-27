# Comprehensive CORS Test Script for Legal-Ops API
# Tests all the endpoints that were failing with CORS issues

Write-Host "🧪 Comprehensive CORS Test for Legal-Ops API" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$baseUrl = "https://legalops-api.apexneural.cloud"
$origin = "https://legalops.apexneural.cloud"

# Test endpoints that were failing
$endpoints = @(
    "/api/matters/",
    "/api/matters/stats",
    "/api/ai-tasks/tasks?limit=10"
)

Write-Host "`n📍 Testing endpoints from origin: $origin" -ForegroundColor Yellow
Write-Host "📍 API Base URL: $baseUrl" -ForegroundColor Yellow

foreach ($endpoint in $endpoints) {
    Write-Host "`n🔍 Testing endpoint: $endpoint" -ForegroundColor Green
    
    # Test OPTIONS preflight request
    Write-Host "  📤 OPTIONS request..." -ForegroundColor Gray
    try {
        $optionsResponse = Invoke-WebRequest -Uri "$baseUrl$endpoint" -Method OPTIONS -Headers @{
            "Origin" = $origin
            "Access-Control-Request-Method" = "GET"
            "Access-Control-Request-Headers" = "Content-Type, Authorization"
        } -TimeoutSec 10
        
        Write-Host "  ✅ OPTIONS Status: $($optionsResponse.StatusCode)" -ForegroundColor Green
        
        # Check CORS headers
        $corsHeaders = @("Access-Control-Allow-Origin", "Access-Control-Allow-Methods", "Access-Control-Allow-Headers", "Access-Control-Allow-Credentials")
        foreach ($header in $corsHeaders) {
            if ($optionsResponse.Headers.ContainsKey($header)) {
                Write-Host "  ✅ $header : $($optionsResponse.Headers[$header])" -ForegroundColor DarkGreen
            } else {
                Write-Host "  ❌ Missing $header" -ForegroundColor Red
            }
        }
        
    } catch {
        Write-Host "  ❌ OPTIONS Failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "  📊 Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        }
    }
    
    # Test actual GET request (will likely fail with 401 but should have CORS headers)
    Write-Host "  📤 GET request..." -ForegroundColor Gray
    try {
        $getResponse = Invoke-WebRequest -Uri "$baseUrl$endpoint" -Method GET -Headers @{
            "Origin" = $origin
            "Content-Type" = "application/json"
        } -TimeoutSec 10
        
        Write-Host "  ✅ GET Status: $($getResponse.StatusCode)" -ForegroundColor Green
        
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  ⚠️  GET Status: $statusCode (expected for unauthorized request)" -ForegroundColor Yellow
        
        # Check if CORS headers are present in error response
        if ($_.Exception.Response.Headers) {
            $headers = $_.Exception.Response.Headers
            if ($headers.Contains("Access-Control-Allow-Origin")) {
                Write-Host "  ✅ CORS headers present in error response" -ForegroundColor DarkGreen
            } else {
                Write-Host "  ❌ CORS headers missing from error response" -ForegroundColor Red
            }
        }
    }
}

Write-Host "`n✨ Test Summary" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan
Write-Host "If OPTIONS requests return 200 with proper CORS headers, the fix is working!" -ForegroundColor Green
Write-Host "GET requests may return 401/403 due to missing auth, but should have CORS headers." -ForegroundColor Yellow