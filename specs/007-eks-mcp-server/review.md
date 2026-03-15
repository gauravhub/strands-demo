# Pre-Implementation Review

**Feature**: EKS MCP Server Integration
**Artifacts reviewed**: spec.md, plan.md, tasks.md, checklists/requirements.md, checklists/integration.md, research.md
**Review model**: Claude Sonnet 4.6 (cross-model review)
**Generating model**: Claude Opus 4.6

## Summary

| Dimension | Verdict | Issues |
|-----------|---------|--------|
| Spec-Plan Alignment | WARN | FR-010 (OTEL) and FR-009 (read-only enforcement) have no implementation tasks; edge case for local-mode connection left implicit |
| Plan-Tasks Completeness | WARN | T009 references agent log output from T006, but T006 is local only; no test tasks |
| Dependency Ordering | PASS | Phase ordering is logical and dependency table is accurate |
| Parallelization Correctness | WARN | Research.md shows `with MCPClient(...)` context-manager pattern that contradicts T004's non-`with` instruction |
| Feasibility & Risk | WARN | MCP client lifecycle in `app.py` is problematic: `invoke()` is async generator; `list_tools_sync()` may block event loop |
| Constitution & Standards Compliance | PASS | Security by Design honored; least-privilege IAM; no hardcoded secrets; CloudFormation-managed |
| Implementation Readiness | WARN | T004 contradicts research.md on MCPClient lifecycle; validation tasks lack concrete pass/fail criteria; `mcp-proxy-for-aws` version pin absent |

**Overall**: READY WITH WARNINGS

## Findings

### Critical (FAIL)

None.

### Warnings (WARN)

**W1 — MCPClient lifecycle contradiction between research.md and T004**
research.md (R4) shows `with MCPClient(mcp_factory) as client:` but T004 says "MCPClient must be opened (not in a `with` block)." These directly contradict. The non-`with` pattern is correct (tools must outlive the block), but research.md should be annotated as illustrative-only.

**W2 — Async generator + blocking call in `app.py` (T007)**
`invoke()` is an `async def` generator. T007 calls `get_eks_mcp_tools()` which internally calls `list_tools_sync()` — a synchronous blocking method inside an async function that can block the event loop. The `try/finally` cleanup in an async generator has subtle semantics if the generator is abandoned.

**W3 — FR-009 (read-only enforcement) has no application-layer task**
Relies entirely on IAM for read-only enforcement. No Python-level tool filter. If IAM policy is misconfigured (e.g., `eks-mcp:*`), write tools would be available.

**W4 — FR-010 (OTEL) validation task lacks concrete criteria**
T011 says to "confirm OTEL spans" but provides no specific span names, attributes, or log patterns to check. No validation that Strands SDK auto-instruments MCPClient.

**W5 — `mcp-proxy-for-aws` has no version pin**
T001 and T002 add the package without a version constraint. Reproducibility risk.

**W6 — T003 (.env.example) is too vague**
No content specified for the lines to add.

**W7 — T009 references T006 (local only) for AgentCore validation**
Troubleshooting validation only covers local mode, not AgentCore.

### Observations (informational)

**O1** — Phase 4 (CloudFormation validation) delivers no new code; just validates T005.

**O2** — Dependency note says "T001 for imports in T004" but T001 is a pyproject.toml dependency, not a Python import. Need `pip install` between Phase 1 and Phase 2.

**O3** — `cloudwatch:GetMetricData` in new policy has no namespace condition (unlike existing `PutMetricData` policy). Intentional but worth noting for security review.

**O4** — No pytest tests planned for `mcp_tools.py`. For a function handling network I/O and error paths, unit tests would improve confidence.

**O5** — `EksMcpRegion` CloudFormation parameter defaults to `""` (empty string, not absent). Region resolution in `mcp_tools.py` must treat empty string as "not set" using `or` chaining.

**O6** — All 27 integration checklist items remain unchecked.

## Recommended Actions

- [ ] Resolve W1: Annotate research.md R4 as illustrative; add rationale in T004 for manual lifecycle management
- [ ] Address W2: Move `get_eks_mcp_tools()` call before the async generator in `app.py`, or use an async variant
- [ ] Address W3: Document IAM-only enforcement as conscious risk acceptance in tasks.md
- [ ] Address W4: Specify concrete OTEL span names/patterns in T011 for pass/fail criteria
- [ ] Address W5: Pin `mcp-proxy-for-aws` version in T001 and T002
- [ ] Address W5/O5: Update T004 to note empty-string handling in region resolution
- [ ] Address W6: Expand T003 with exact .env.example content
- [ ] Consider O4: Add pytest test task for `mcp_tools.py`
