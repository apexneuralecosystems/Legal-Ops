# Comprehensive CORS Test Script for Legal-Ops API

Write-Host "🧪 Comprehensive CORS Test for Legal-Ops API" -ForegroundColor Cyan

$baseUrl = "https://legalops-api.apexneural.cloud"
$origin = "https://legalops.apexneural.cloud"

$endpoints = @(
    "/api/matters/",
    "/api/matters/stats", 
    "/api/ai-tasks/tasks?limit=10"
)

Write-Host "Testing endpoints from origin: $origin" -ForegroundColor Yellow

foreach ($endpoint in $endpoints) {
    Write-Host "`nTesting: $endpoint" -ForegroundColor Green
    
    # Test OPTIONS
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl$endpoint" -Method OPTIONS -Headers @{
            "Origin" = $origin
            "Access-Control-Request-Method" = "GET"
        } -TimeoutSec 10
        
        Write-Host "  OPTIONS Status: $($response.StatusCode)" -ForegroundColor Green
        
        # Check headers
        $headers = @("Access-Control-Allow-Origin", "Access-Control-Allow-Methods")
        foreach ($header in $headers) {
            if ($response.Headers.ContainsKey($header)) {
                Write-Host "  ✓ $header present" -ForegroundColor DarkGreen
            } else {
                Write-Host "  ✗ Missing $header" -ForegroundColor Red
            }
        }
        
    } catch {
        Write-Host "  ✗ OPTIONS Failed" -ForegroundColor Red
    }
}

Write-Host "`nDone! If OPTIONS return 200, CORS is working." -ForegroundColor Cyan