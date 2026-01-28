# Lexis-Only Doc Chat Performance Report: "Good and Bad"

This report summarizes the evaluation of the "Doc Chat" feature following the transition to a Lexis Advance-exclusive legal research model.

## Executive Summary
The Lexis-only implementation significantly improves the **authority** and **citation accuracy** of the legal research agent by ensuring only verified Malaysian case law is used. However, it introduces significant **latency** and **stability challenges** due to the complex authentication requirements of the University of Malaya Library portal.

## The Good (Successes)
*   **Contextual Accuracy:** The RAG system for uploaded documents remains highly effective (95%+ accuracy), correctly identifying matter context (e.g., breach of settlement agreements) before initiating search.
*   **Citation Reliability:** By removing CommonLII and other secondary sources, the agent now produces high-quality citations in the official format (e.g., *Case Name [Year] Vol Report Page*).
*   **Legislative Integration:** The AGC Legislation Scraper continues to provide reliable statutory context (e.g., Contracts Act 1950) to supplement case law.
*   **Strategic Depth:** The "Devil's Advocate" mode effectively identifies evidentiary gaps and strategic risks based on the retrieved Lexis cases and uploaded documents.

## The Bad (Challenges)
*   **Authentication Fragility (OpenAthens Chaining):** The redirect chain from the UM Library to Lexis now frequently pauses at an OpenAthens "Institution Chooser" page. This creates an additional point of failure for browser automation.
*   **High Latency:** Lexis searches via browser automation typically take between 2 to 4 minutes due to the multiple redirect steps (UM Portal -> OpenAthens -> CAS -> EzProxy -> Lexis).
*   **Stale Sessions:** Optimistic search occasionally fails if a session is semi-expired, requiring a full 3-minute re-login flow which can frustrate users.
*   **Intermittent Redirect Failures:** The CAS login occasionally loses the `service` parameter during the OpenAthens transition, leading to "Unexpected Redirect" errors that stop the research process.

## Analysis of Recent Improvements
We have implemented the following patches to address the "Bad" results:
1.  **OpenAthens Chooser Handling:** Added logic to `LexisScraper` to detect and automatically click "UM Staff and Students" on the OpenAthens landing page.
2.  **Extended Timeouts:** Increased search and redirect timeouts to 3 minutes to accommodate slow Lexis response times.
3.  **Strict Enforcement & Transparency:** Updated the `LegalResearchAgent` to strictly avoid backup sources and explicitly warn users if a Lexis search fails, ensuring no "hallucinated" cases are presented as verified Lexis results.

## Recommendations
1.  **UI Verification Indicators:** Implement a visual "Lexis Verified" badge for citations that were confirmed via the tool.
2.  **Session Persistence:** Improve cookie preservation to avoid the 3-minute login flow on subsequent queries.
3.  **Hybrid Fallback Policy:** Consider allowing a "Verified Only" mode vs. an "Augmented" mode where the agent can uses general knowledge only if explicitly labeled.

---
*Report Generated: 2026-01-27*
*Confidential - Legal Ops Project*
