# Computer-Use Automation System Design Report

## 1. Architecture
The architecture cleanly separates **Discovery** from **Deterministic Replay**. During discovery, the agent drives the live surface, validates success states, and serializes the workflow into an immutable, versioned `CapabilityArtifact`. During replay, AI calling agents trigger the flow deterministically via `DeterministicReplayEngine` without LLM calls in the loop, achieving sub-second latency and zero hallucination risk.

## 2. Artifact Schema
The schema treats automated flows as strongly-typed capabilities:
- `input_schema` & `output_schema`: Explicit type contracts for calling agents.
- `steps`: Ordered actions referencing resilient `MultiTierLocator` targets.
- `business_branches`: Domain outcomes (e.g. record not found) evaluated distinctly from runtime errors.
- `success_checkpoint`: Terminal assertion guaranteeing valid completion.

## 3. Determinism & Error Handling
Replay determinism is achieved via:
- Multi-tier element resolution (Accessibility Tree -> Text Matching -> Structural Selectors).
- Explicit classification separating `BUSINESS_OUTCOME` (valid domain branches), `RECOVERABLE_ERROR` (transient loading delays), and `HARD_FAILURE` (broken flows triggering screenshot captures).

## 4. Heterogeneity & Multi-Tenant
- **Surface Abstraction:** Core action models (`CLICK`, `FILL`, `EXTRACT`) bind to Playwright for web targets and can map to OS Accessibility APIs (UIAutomation/pywinauto) for legacy desktop surfaces without modifying the capability artifact.
- **Multi-Tenant Specialization:** Artifacts support base capability templates with per-tenant overlay configurations to accommodate branding or layout variations without re-recording from scratch.

## 5. Escalation & Handoff
When element resolution fails or an unexpected dialog appears:
1. Automation halts while preserving the active browser context and authenticated session.
2. A diagnostic payload (URL, step ID, screenshot) is dispatched to an operator.
3. The operator performs manual intervention on the live page and signals completion to resume automated execution seamlessly.

## 6. Safety
- Configurable domain allowlists block navigations outside approved banking origins.
- Action validation distinguishes safe actions from irreversible transactions (`is_irreversible=True`).
- RegEx-based sanitizers scrub SSNs, payment card numbers, and API tokens prior to writing logs or artifacts.

## 7. Cuts
- **Deliberately Cut:** Full WebRTC co-browsing operator frontend (mocked via CLI console handoff with live browser persistence).
- **Next Steps:** Automated self-healing locator refinement using bounded single-step LLM intervention during replay regressions.