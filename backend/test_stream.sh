
# Test streaming endpoint
# usage: ./test_stream.sh <MATTER_ID>

MATTER_ID="${1:-MAT-20251231-6e95ef90}"

echo "Testing streaming for matter: $MATTER_ID"

curl -N -X POST "http://localhost:8006/api/matters/$MATTER_ID/draft/stream" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d '{
    "template_id": "TPL-HighCourt-EN-v2",
    "issues_selected": [{"id": "ISS-01", "title": "Test Issue"}],
    "prayers_selected": [{"text_en": "Test Prayer"}]
  }'
