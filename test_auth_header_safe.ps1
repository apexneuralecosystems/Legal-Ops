Write-Host "Testing CORS Authorization Header" -ForegroundColor Cyan

$baseUrl = "https://legalops-api.apexneural.cloud"
$origin = "https://legalops.apexneural.cloud"

$tests = @(
    @{ path = "/api/matters/stats"; method = "GET" },
    @{ path = "/api/matters/"; method = "GET" },
    @{ path = "/api/ai-tasks/tasks?limit=10"; method = "GET" },
    @{ path = "/api/auth/verify"; method = "POST" }
)

foreach ($test in $tests) {
    $endpoint = $test.path
    $method = $test.method
    Write-Host "Testing: $endpoint" -ForegroundColor Green
    
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl$endpoint" -Method OPTIONS -Headers @{
            "Origin" = $origin
            "Access-Control-Request-Method" = $method
            "Access-Control-Request-Headers" = "authorization,content-type"
        } -UseBasicParsing -TimeoutSec 10
        
        Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
        
        # Check if Authorization is allowed
        if ($response.Headers.ContainsKey("Access-Control-Allow-Headers")) {
            $allowedHeaders = $response.Headers["Access-Control-Allow-Headers"]
            Write-Host "  Allowed Headers: $allowedHeaders" -ForegroundColor Yellow
            
            if ($allowedHeaders -like "*authorization*" -or $allowedHeaders -like "*Authorization*") {
                Write-Host "  ✅ Authorization header allowed!" -ForegroundColor Green
            } else {
                Write-Host "  ❌ Authorization header NOT allowed" -ForegroundColor Red
            }
        } else {
            Write-Host "  ❌ No Access-Control-Allow-Headers found" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "Test complete" -ForegroundColor Cyan
