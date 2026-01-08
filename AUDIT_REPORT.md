# Legal-Ops Codebase Audit Report

## 1. Executive Summary
A comprehensive deep-dive audit was performed on both the frontend (Next.js) and backend (FastAPI/Python) services. The overall architecture is robust, utilizing a microservices-style structure with agentic workflows. However, several critical configuration issues, potential unhandled crashes, and leftover debug code were identified.

## 2. Backend Audit (FastAPI)

### 2.1. Critical Issues & Fixes
- **Unhandled Intake Crashes (FIXED)**: The `start_intake_workflow` endpoint in `routers/matters.py` lacked a comprehensive `try-except` block. Any orchestrator failure would cause a `500 Internal Server Error` and crash the thread.
    - *Action Taken*: Wrapped the entire logic in a `try-except` block to capture errors and return a structured JSON error response.
- **Webhook Reliability**: `routers/webhooks.py` relies on email matching for subscription updates (`User.email == subscriber_email`). This is fragile if the PayPal email differs from the app email.
    - *Recommendation*: Update payment metadata to include `user_id` as a strict reference.

### 2.2. Security & Architecture
- **Auth Implementation**: Uses `apex-saas-framework` for authentication. Good separation of concerns.
- **Pydantic Validation**: Strong use of Pydantic models for request validation in all routers.
- **Hardcoded Secrets**: No direct hardcoded secrets found in source code (good usage of `.env` implied).

## 3. Frontend Audit (Next.js)

### 3.1. Critical Configuration Issues
- **API URL Configuration (CRITICAL)**: In `lib/api.ts`, the `API_URL` is hardcoded to an empty string `''`.
    - `const API_URL = ''`
    - This creates a relative path `baseURL: '/api'`, which fails unless a proxy is configured in `next.config.js`. If no proxy exists, the frontend attempts to call endpoints on port 3000 instead of the backend port 8006.
    - *Action Required*: Restore the environment variable logic: `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8006'`.

### 3.2. Code Quality & State
- **Console Logs**: Leftover debug code found in `components/ParallelViewer.tsx`: `console.log('Flagging segment for review:', segmentId)`.
- **Hardcoded URLs**: `layout.tsx` and `api.ts` contain references to `localhost`. These should be replaced with environment variables for production deployment.

## 4. Remediation Plan

1. **Fix `frontend/lib/api.ts`**: Restore dynamic API URL configuration.
2. **Clean `frontend/components/ParallelViewer.tsx`**: Remove debug logs.
3. **Verify `next.config.js`**: Confirm if a proxy exists. If not, the API URL fix is mandatory.
4. **Backend Webhooks**: (Low Priority) Add robust `user_id` tracking in payment metadata.

## 5. Conclusion
Key backend stability issues have been patched. The primary remaining risk is the frontend API configuration (`api.ts`), which checks out as "fragile". Fixing this will ensure smoother deployment and local development.
