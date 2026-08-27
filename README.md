# Computer-Use Automation System (CUA)

An enterprise automation engine that uses an LLM/agent discovery loop to learn legacy web and desktop workflows, then compiles them into deterministic, reusable, and versioned **Capability Artifacts** for production execution without an LLM in the loop.

---

## Table of Contents
1. [Overview & Motivation](#overview--motivation)
2. [Key Capabilities & Architecture](#key-capabilities--architecture)
3. [Repository Structure](#repository-structure)
4. [Prerequisites & Installation](#prerequisites--installation)
5. [End-to-End Demo Execution](#end-to-end-demo-execution)
6. [Core System Mechanics](#core-system-mechanics)
   - [Structured Capability Schema](#1-structured-capability-schema)
   - [Deterministic Replay & Outcome Taxonomy](#2-deterministic-replay--outcome-taxonomy)
   - [Resilient Multi-Tier Locators](#3-resilient-multi-tier-locators)
   - [Human-in-the-Loop (HITL) Seam](#4-human-in-the-loop-hitl-seam)
   - [Safety & Policy Guardrails](#5-safety--policy-guardrails)
7. [Optional Stretch Goals Implemented](#optional-stretch-goals-implemented)
8. [Evidence & Trace Artifacts](#evidence--trace-artifacts)
9. [Design Report Reference](#design-report-reference)

---

## Overview & Motivation

US banks and credit unions rely on thousands of legacy, back-office vendor applications that lack modern APIs. Driving these applications via LLM visual reasoning every time introduces unacceptable latency, high inference costs, and potential for hallucination.

This system implements a **"Record Once, Replay Many"** paradigm:
1. **Discovery Loop:** An agent explores a hostile, non-semantic UI (e.g., nested tables, dynamic spinners, no test IDs), executes the multi-step transaction, and reaches a verified success checkpoint.
2. **Capability Artifact:** Discovered actions are parameterized and compiled into an immutable, versioned JSON contract.
3. **Deterministic Replay:** Upstream AI agents invoke the capability by name with typed arguments, executing deterministically in sub-second time without LLM calls.

---

## Key Capabilities & Architecture


```

```
                              [ Upstream AI Agent / Goal ]
                                           │
                   ┌───────────────────────┴───────────────────────┐
                   ▼                                               ▼
         [ 1. Discovery Agent ]                         [ 2. Capability Catalog ]
       (Observe-Decide-Act Loop)                       (Dynamic Tool Definitions)
                   │                                               │
                   ▼                                               ▼
        [ Capability Artifact ] ───────────────────────► [ 3. Replay Engine ]
         (Typed JSON Schema)                               (Deterministic Run)
                                                                   │
                                          ┌────────────────────────┼────────────────────────┐
                                          ▼                        ▼                        ▼
                                [ Multi-Tier Locators ]  [ Business Classifier ]   [ Human Handoff ]
                                (A11y -> Text -> XPath)  (Outcome vs Hard Fail)    (Live Session Seam)

```

````

- **Zero-LLM Production Execution:** Replay runs without models in the decision loop.
- **Rich Outcome Taxonomy:** Distinguishes between successful receipts, legitimate business outcomes (e.g., `MEMBER_NOT_FOUND`, `ACCOUNT_LOCKED`), recoverable transient delays, and hard failures.
- **Live Session Handoff:** If blocked, automation halts, retains the active browser session, presents diagnostic screenshots, and cedes control to a human before resuming.
- **Regulated Financial Data Safety:** Hardened origin allowlisting, action filtering, and RegEx-based PII/secret scrubbing.

---

## Repository Structure

```text
cua_banking_system/
├── README.md                          # Comprehensive setup, run, and architecture guide
├── REPORT.md                          # 7-section design report & trade-off defense
├── requirements.txt                   # Pinned runtime dependencies
├── run_demo.py                        # Catalog discovery, agent tool invocation & benchmark
├── mock_bank_app/
│   └── app.py                         # Stand-in legacy core-banking portal (FastAPI)
├── core/
│   ├── __init__.py                    # Core package marker
│   ├── models.py                      # Pydantic schemas (Capability, Locators, Outcomes)
│   ├── agent.py                       # Autonomous Discovery Agent (Observe-Decide-Act)
│   ├── engine.py                      # Deterministic Replay Engine
│   ├── catalog.py                     # Agent tool registry & multi-run stability benchmark
│   ├── locators.py                    # 4-tier resilient locator resolution engine
│   ├── hitl.py                        # Session-preserving Human-in-the-Loop seam
│   ├── guardrails.py                  # Domain allowlists, action policies & PII scrubbers
│   └── tracer.py                      # JSON-L event logger & screenshot evidence capture
├── capabilities/
│   └── open_subaccount_v1.json        # Compiled capability artifact
└── evidence/
    ├── discovery_run.log              # Discovery trace log
    ├── discovery_run_checkpoint_*.png # Visual checkpoint evidence
    ├── replay_success.json            # Deterministic replay success outcome
    ├── replay_business_error.json     # Handled domain exception outcome
    ├── replay_open_member_subaccount.log # Replay event log
    └── stability_report.json          # 5-run stability benchmark report

````

## Prerequisites & Installation

### Requirements

- **Python:** Version 3.11 or higher
- **OS:** macOS, Linux, or Windows (WSL2 / PowerShell)

### Setup Instructions

Bash

```
# 1. Clone repository and navigate to root
git clone [https://github.com/venkatsainathh/cua-banking-system.git](https://github.com/venkatsainathh/cua-banking-system.git)
cd cua-banking-system

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browser binaries
playwright install chromium

```

## End-to-End Demo Execution

### Step 1: Start the Target Core Banking Server

Open Terminal 1:

Bash

```
python mock_bank_app/app.py

```

*Starts the local legacy core-banking portal at **`http://127.0.0.1:8000`**.*

### Step 2: Run Autonomous Discovery

Open Terminal 2 (with `.venv` activated):

Bash

```
python -m core.agent

```

*Launches Chromium, navigates the interface, fulfills the goal, captures visual checkpoints, and serializes the capability artifact to **`capabilities/open_subaccount_v1.json`**.*

### Step 3: Run Deterministic Replay

In Terminal 2:

Bash

```
python -m core.engine

```

*Executes both a valid transaction (saving receipt to **`evidence/replay_success.json`**) and a business exception test (saving **`MEMBER_NOT_FOUND`** to **`evidence/replay_business_error.json`**).*

### Step 4: Run Agent Tool Invocation & Stability Benchmark

In Terminal 2:

Bash

```
python run_demo.py

```

*Demonstrates dynamic tool definition schema generation, direct capability invocation, and a 5-run stability benchmark writing to **`evidence/stability_report.json`**.*

## Core System Mechanics

### 1. Structured Capability Schema

The artifact (`capabilities/open_subaccount_v1.json`) represents a typed, versioned capability:

- **`input_schema`****:** Strongly-typed parameters required by the capability (`member_id`, `product_type`, `initial_deposit`).
- **`output_schema`****:** Strongly-typed extracted values (`confirmation_number`, `assigned_product`).
- **`steps`****:** Ordered execution steps with action types (`navigate`, `fill`, `click`, `select`, `extract`).
- **`business_branches`****:** Domain conditions mapped to structured outcome codes (`MEMBER_NOT_FOUND`, `ACCOUNT_LOCKED`).
- **`success_checkpoint`****:** Terminal assertion locator confirming successful execution.

### 2. Deterministic Replay & Outcome Taxonomy

The `DeterministicReplayEngine` (`core/engine.py`) classifies outcomes into four discrete states:

1. `SUCCESS`: Reached terminal checkpoint; outputs extracted and validated.
2. `BUSINESS_OUTCOME`: Target application returned a known domain outcome (e.g. member not found or account locked). Treated as a successful diagnostic return, not a system failure.
3. `RECOVERABLE_ERROR`: Transient network or UI delays resolved via automatic wait states.
4. `HARD_FAILURE`: Broken flows, unresolvable targets, or checkpoint mismatches; triggers full screenshot and log capture for auditing.

### 3. Resilient Multi-Tier Locators

To handle non-semantic, table-heavy, and legacy DOMs without `data-testid` attributes, `core/locators.py` resolves elements across a prioritized 4-tier hierarchy:

1. **Tier 1 (Accessibility Tree):** Role and accessible name (`get_by_role`).
2. **Tier 2 (Visible Text):** Text content matching (`get_by_text`).
3. **Tier 3 (CSS Fallback):** ID and class structure selectors.
4. **Tier 4 (XPath Fallback):** Hierarchical DOM paths.

### 4. Human-in-the-Loop (HITL) Seam

When automation encounters an unknown blocking dialog or unresolvable control:

1. `core/hitl.py` pauses execution while keeping the live Playwright browser context open.
2. Captures full-page screenshot evidence and logs the failure context.
3. Cedes control to the operator console.
4. The operator performs manual intervention on the live screen and presses `[ENTER]` in the terminal to resume automated replay seamlessly.

### 5. Safety & Policy Guardrails

`core/guardrails.py` enforces enterprise-grade safety:

- **Origin Allowlist:** Strictly restricts navigation to permitted hosts (`127.0.0.1:8000`).
- **Action Policy:** Blocks unauthorized action primitives; marks sensitive steps (`Submit & Authorize`) as `is_irreversible=True`.
- **Data Scrubbing:** Automatically scrubs SSNs (`\d{3}-\d{2}-\d{4}`), payment cards (`\d{16}`), and API credentials before writing to logs, traces, or artifacts.

## Optional Stretch Goals Implemented

### 1. Agent-Facing Capability Catalog (`core/catalog.py`)

- Exposes all saved capability artifacts as standard function-calling definitions compatible with upstream agent orchestration frameworks.
- Upstream agents can inspect capabilities dynamically and invoke them via `catalog.invoke(name, args)`.

### 2. Multi-Run Stability Benchmark & Flakiness Scoring

- Automated benchmarking harness (`catalog.evaluate_stability()`) replays capabilities across N headless runs.
- Tested over 5 consecutive runs: achieved **100.0% stability score** with an average execution time of **0.96s**, gating the artifact as approved for unattended production execution.

## Evidence & Trace Artifacts

The `/evidence/` directory contains verified artifacts from execution runs:

- `discovery_run.log` & `discovery_run_checkpoint_*.png`: Step-by-step discovery trace and visual confirmation.
- `replay_success.json`: Structured execution output of a successful run.
- `replay_business_error.json`: Handled domain outcome verifying `MEMBER_NOT_FOUND` classification.
- `stability_report.json`: Multi-run stability score, latency metrics, and approval gating.

## Design Report Reference

For detailed analysis of design decisions, trade-offs, surface abstractions, multi-tenant reuse strategies, and cut lines, refer to the accompanying [REPORT.md](REPORT.md) written against the 7 mandatory evaluation headings.