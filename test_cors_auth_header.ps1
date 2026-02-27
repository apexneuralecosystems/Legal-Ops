# Test CORS with Authorization header specifically
# This tests the exact scenario from the browser error

Write-Host "Testing CORS with Authorization header" -ForegroundColor Cyan

$baseUrl = "https://legalops-api.apexneural.cloud"
$origin = "https://legalops.apexneural.cloud"

$endpoints = @(
    "/api/matters/stats",
    "/api/matters/",
    "/api/ai-tasks/tasks?limit=10"
)

Write-Host "Testing endpoints with Authorization header in preflight..." -ForegroundColor Yellow

foreach ($endpoint in $endpoints) {
    Write-Host "`nTesting: $endpoint" -ForegroundColor Green
    
    # Test OPTIONS preflight with Authorization header specifically
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl$endpoint" -Method OPTIONS -Headers @{
            "Origin" = $origin
            "Access-Control-Request-Method" = "GET"
            "Access-Control-Request-Headers" = "authorization,content-type"  # Lowercase as browser sends
        } -TimeoutSec 10
        
        Write-Host "  ✅ OPTIONS Status: $($response.StatusCode)" -ForegroundColor Green
        
        # Check all CORS headers
        $headers = @("Access-Control-Allow-Origin", "Access-Control-Allow-Methods", "Access-Control-Allow-Headers", "Access-Control-Allow-Credentials")
        foreach ($header in $headers) {
            if ($response.Headers.ContainsKey($header)) {
                Write-Host "  ✅ $header : $($response.Headers[$header])" -ForegroundColor DarkGreen
            } else {
                Write-Host "  ❌ Missing $header" -ForegroundColor Red
            }
        }
        
    } catch {
        Write-Host "  ❌ OPTIONS Failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "  📊 Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
            
            # Check if there are any CORS headers in the error response
            if ($_.Exception.Response.Headers) {
                $errorHeaders = $_.Exception.Response.Headers
                Write-Host "  📋 Error Response Headers:" -ForegroundColor Yellow
                foreach ($header in $errorHeaders.Keys) {
                    if ($header -like "*cors*" -or $header -like "*access*") {
                        Write-Host "    $header : $($errorHeaders[$header])" -ForegroundColor Yellow
                    }
                }
            }
        }
    }
}

Write-Host "`n✨ Test Summary" -ForegroundColor Cyan
Write-Host "If OPTIONS requests return 200 with Authorization in Access-Control-Allow-Headers, the fix is working!" -ForegroundColor Green