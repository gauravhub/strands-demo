# Design Review: AgentCore Gateway Integration (010-agentcore-gateway)

**Reviewer**: Cross-model design reviewer (Sonnet 4.6)
**Date**: 2026-03-16
**Feature Branch**: `010-agentcore-gateway`
**Artifacts reviewed**: spec.md, plan.md, tasks.md, research.md, data-model.md, checklists/requirements.md, constitution.md

---

## Summary Table

| # | Dimension | Verdict | Key Finding |
|---|-----------|---------|-------------|
| 1 | Spec-Plan Alignment | WARN | Stale Lambda sentence in plan.md summary; API key storage inconsistency |
| 2 | Plan-Tasks Completeness | WARN | Missing task for `mcp` dependency; missing `TAVILY_API_KEY` validation update in T006 |
| 3 | Dependency Ordering | PASS | All phases correctly ordered |
| 4 | Parallelization Correctness | PASS | T002/T003/T004 operate on distinct files |
| 5 | Feasibility & Risk | WARN | CFN resource type availability unverified; `RequestHeaderAllowlist` undocumented |
| 6 | Standards Compliance | WARN | `app.py` startup `TAVILY_API_KEY` validation will break Gateway mode |
| 7 | Implementation Readiness | PASS | Tasks are specific and actionable |

**Overall Verdict: READY WITH WARNINGS**

---

## Required Fixes Before Implementation

1. **plan.md line 7**: Remove "A Lambda function wraps the Tavily API as a Gateway target" — replace with built-in integration template description.
2. **data-model.md**: Replace stale Lambda resource table with correct resources (Gateway CFN resource only; no Lambda).
3. **research.md R2**: Update "Tavily Lambda Target" entry to document the built-in integration template decision.
4. **tasks.md T006**: Add instruction to make `TAVILY_API_KEY` startup validation conditional on `AGENTCORE_GATEWAY_URL` not being set.
5. **tasks.md**: Add a task to verify/add `mcp` package to `requirements-agent.txt`.
6. **tasks.md T011**: Add a config backup step before the Runtime update.

---

## Detailed Reviews

### 1. Spec-Plan Alignment — WARN

- All 10 functional requirements have corresponding plan elements.
- **Issue**: plan.md summary (line 7) still says "A Lambda function wraps the Tavily API as a Gateway target" — stale Lambda reference not caught by analyze phase.
- **Issue**: Spec assumption hedges on API key storage ("Lambda env var, Identity deferred") while plan commits to Identity credential provider unconditionally.

### 2. Plan-Tasks Completeness — WARN

- All plan architecture items have corresponding tasks.
- **Gap**: No task ensures `mcp` package is added to `requirements-agent.txt`.
- **Gap**: T006 does not mention updating `TAVILY_API_KEY` startup validation in `app.py` to be conditional.
- T010 complexity is understated — bundles Console target creation with AgentCore Identity credential provider setup.

### 3. Dependency Ordering — PASS

- T001 → T002+T003+T004 (parallel) → T005 → T006 correctly ordered.
- T007 (CFN) correctly independent of T001-T006.
- T008 → T009 → T010 → T011 → T012 deployment chain correct.
- T013 correctly depends on T009 (needs Gateway resource ID).

### 4. Parallelization Correctness — PASS

- T002 (chatbot.py), T003 (app.py), T004 (client.py) — all distinct files, no shared state.
- No file conflicts possible with concurrent execution.

### 5. Feasibility & Risk — WARN

- **HIGH RISK**: `AWS::BedrockAgentCore::Gateway` CFN resource type availability unverified. No pre-flight check task.
- **HIGH RISK**: `RequestHeaderAllowlist` for JWT propagation is undocumented. No fallback specified.
- **MEDIUM RISK**: T007 hedges on `GatewayUrl` attribute name ("verify correct attribute name").
- **MEDIUM RISK**: No config backup step before T011 Runtime update.

### 6. Standards Compliance — WARN

- Constitution principles I-V are generally satisfied.
- **Critical gap**: `app.py` currently validates `TAVILY_API_KEY` as required at startup. In Gateway mode, this key is managed by the Gateway target, not the agent. Without making this validation conditional, the app will crash on startup when Gateway is configured but `TAVILY_API_KEY` env var is not set.

### 7. Implementation Readiness — PASS

- Tasks specify exact file paths, function signatures, import paths, and parameter names.
- Two minor gaps: dependency file update and T006 scope for validation logic.

---

## Stale Artifact Check

- **data-model.md**: Still lists `TavilyLambdaRole`, `TavilyLambdaFunction`, `TavilyGatewayTarget`, and `infra/agentcore/tavily_lambda/index.py`. All stale — Lambda approach was superseded.
- **research.md R2**: Still describes "Tavily Lambda Target" with Lambda-based architecture. Stale.
- **plan.md summary**: Still references Lambda. Stale.
