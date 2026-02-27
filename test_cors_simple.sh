#!/bin/bash
# Simple CORS test script for Legal-Ops Backend

echo "🧪 Testing CORS for Legal-Ops Backend"
echo "====================================="

# Configuration
BASE_URL="https://legalops-api.apexneural.cloud"
FRONTEND_ORIGIN="https://legalops.apexneural.cloud"

echo "Testing OPTIONS request to /api/auth/login..."
echo ""

# Test OPTIONS request with curl
curl -X OPTIONS "$BASE_URL/api/auth/login" \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  -H "User-Agent: CORS-Test-Script/1.0" \
  -v \
  -w "\nHTTP Status: %{http_code}\n" \
  2>&1 | grep -E "(HTTP/|Access-Control-|Origin|Status)"

echo ""
echo "Testing actual POST request..."
echo ""

# Test actual POST request
curl -X POST "$BASE_URL/api/auth/login" \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Content-Type: application/json" \
  -H "User-Agent: CORS-Test-Script/1.0" \
  -d '{"email": "test@example.com", "password": "test123"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s \
  | grep -E "(HTTP/|Access-Control-|Origin|Status)" || echo "No CORS headers found"

echo ""
echo "✅ Test completed. Check the output above for CORS headers."
echo "Expected: HTTP 200 for OPTIONS, proper Access-Control-* headers"