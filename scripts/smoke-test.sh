#!/bin/bash
# ============================================
# Post-Deploy Smoke Test
# ============================================
# Validates that critical endpoints respond correctly
# after a Dokploy deployment.
#
# Usage:
#   API_URL=https://legalops-api.apexneural.cloud \
#   APP_URL=https://legalops.apexneural.cloud \
#   ./scripts/smoke-test.sh
#
# Exit code 0 = all checks passed

set -euo pipefail

API_URL="${API_URL:-https://legalops-api.apexneural.cloud}"
APP_URL="${APP_URL:-https://legalops.apexneural.cloud}"
TIMEOUT=15
PASS=0
FAIL=0

check() {
    local name="$1"
    local url="$2"
    local expect_field="$3"
    
    echo -n "  Checking ${name}... "
    
    response=$(curl -sf --max-time "${TIMEOUT}" "${url}" 2>&1) || {
        echo "FAIL (HTTP error or timeout)"
        FAIL=$((FAIL + 1))
        return
    }
    
    if [ -n "${expect_field}" ]; then
        echo "${response}" | python3 -c "import sys,json; d=json.load(sys.stdin); assert '${expect_field}' in d, 'missing field'" 2>/dev/null || {
            echo "FAIL (missing field: ${expect_field})"
            FAIL=$((FAIL + 1))
            return
        }
    fi
    
    echo "OK"
    PASS=$((PASS + 1))
}

echo "=========================================="
echo "  Legal-Ops Smoke Test"
echo "=========================================="
echo ""
echo "Backend:  ${API_URL}"
echo "Frontend: ${APP_URL}"
echo ""

echo "[Backend API]"
check "Health (liveness)"    "${API_URL}/health"    "status"
check "Healthz (liveness)"   "${API_URL}/healthz"   "status"
check "Readyz (readiness)"   "${API_URL}/readyz"    "ready"
check "Root"                 "${API_URL}/"           "version"

echo ""
echo "[Frontend]"
check "Frontend health"      "${APP_URL}/health"     ""
check "Frontend root"        "${APP_URL}/"            ""

echo ""
echo "=========================================="
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "=========================================="

if [ "${FAIL}" -gt 0 ]; then
    echo "SMOKE TEST FAILED"
    exit 1
fi

echo "SMOKE TEST PASSED"
exit 0
