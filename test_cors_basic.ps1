Write-Host "Testing CORS for Legal-Ops API endpoints"

$baseUrl = "https://legalops-api.apexneural.cloud"
$origin = "https://legalops.apexneural.cloud"

$endpoints = @("/api/matters/", "/api/matters/stats", "/api/ai-tasks/tasks?limit=10")

foreach ($endpoint in $endpoints) {
    Write-Host "Testing: $endpoint"
    
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl$endpoint" -Method OPTIONS -Headers @{"Origin"=$origin} -TimeoutSec 10
        Write-Host "  OPTIONS Status: $($response.StatusCode)"
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  SUCCESS: CORS working for $endpoint" -ForegroundColor Green
        }
    } catch {
        Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "Test complete"