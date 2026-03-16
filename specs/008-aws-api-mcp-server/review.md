# Cross-Model Review Report: Feature 008-aws-api-mcp-server

**Reviewer**: Claude Sonnet 4.6 (cross-model, read-only)
**Review Date**: 2026-03-16
**Artifacts Reviewed**: spec.md, plan.md, tasks.md, checklists/requirements.md, checklists/integration.md
**Source Code Reviewed**: src/agent/mcp_tools.py, src/agent/chatbot.py, src/agentcore/app.py, infra/agentcore/template.yaml
**Constitution Version**: 1.0.0

---

## Summary

| Dimension | Verdict | Notes |
|-----------|---------|-------|
| Spec-Plan Alignment | PASS | All 10 FRs and 7 SCs are addressed in the plan; no untraced plan elements detected |
| Plan-Tasks Completeness | WARN | Phase 6 (US2) has no implementation task — T010 is validation-only; integration checklist items (CHK001–CHK025) are all unchecked |
| Dependency Ordering | WARN | Phase 4 (CloudFormation, T004) is declared independent of Phase 3 but T004 adds `AWS_API_MCP_REGION` which is only meaningful once T001 exists; ordering is correct but rationale for parallelism is slightly misleading |
| Parallelization Correctness | PASS | T002 (`chatbot.py`) and T003 (`app.py`) touch different files; Phase 3 and Phase 4 touch code vs CloudFormation — correctly marked [P] |
| Feasibility & Risk | WARN | T008 is correctly flagged as highest-risk, but mitigation is incomplete: no rollback procedure specified if `update-agent-runtime` fails; CHK002 (underlying AWS service permissions) is unresolved |
| Standards Compliance | PASS | Plan complies with all five constitutional principles |
| Implementation Readiness | WARN | T002 has return type ambiguity; T003 cleanup pattern for two clients needs explicit guidance |

**Overall Verdict: READY WITH WARNINGS**

---

## Detailed Findings

### WARN — Plan-Tasks Completeness

**Finding 1: Integration checklist items are all unchecked**

CHK002 (highest-impact): "Are requirements for which underlying AWS service permissions the AgentCore role needs — beyond `aws-api:InvokeMcp` — specified or explicitly deferred?" The EKS MCP integration required both `eks-mcp:InvokeMcp` AND a separate `EksReadAccess` policy with specific EKS API actions. The AWS API MCP integration may follow the same pattern.

**Recommendation**: Before implementation, resolve CHK002. Either enumerate the underlying AWS service permissions or explicitly defer them with a note that they will be added reactively when permission errors are observed.

**Finding 2: US2 (Phase 6) has no implementation task**

Phase 6 is explicitly "validation checkpoint only" with T010 as the sole task. This is intentional and correctly noted. If T010 fails, there is no remediation path defined. Minor concern for a P2 story.

### WARN — Feasibility & Risk

**Finding 3: T008 mitigation is incomplete**

1. No explicit rollback step if the `update-agent-runtime` call fails
2. No specification of whether `update-agent-runtime` is idempotent
3. The new `AWS_API_MCP_REGION` env var must be added while preserving ALL existing env vars (`ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, `LOG_LEVEL`, `EKS_MCP_REGION`) — an LLM implementer focused on the new variable might accidentally drop existing ones

**Recommendation**: Add to T008: "Save the output of `get-agent-runtime` to a local file before issuing the update call (rollback reference). Ensure the `environmentVariables` payload includes ALL existing env vars plus the new `AWS_API_MCP_REGION`."

**Finding 4: CHK002 — Underlying AWS service permissions**

The existing CloudFormation template shows the EKS MCP integration required not just `EksMcpAccess` but also `EksReadAccess` (direct EKS API actions) and `EksSupportingReadAccess` (sts, iam, logs, cloudwatch). The AWS API MCP Server likely requires analogous underlying permissions for each service the user wants to query. T004 only adds `aws-api:InvokeMcp`.

**This is the most significant technical risk in the feature.** If the same pattern applies, T009 verification will fail with permission errors.

**Recommendation**: Research whether `aws-api:InvokeMcp` is sufficient or whether underlying service permissions must also be granted. If broad read access is needed, consider adding a `ReadOnlyAccess` managed policy.

### WARN — Implementation Readiness

**Finding 5: T002 return type ambiguity in chatbot.py**

Current signature: `def create_agent() -> tuple[Agent, object | None]`. Task does not specify the exact new signature. Call sites in the Streamlit app will break if the return type changes without coordination.

**Recommendation**: Specify the exact new return signature and identify all call sites that consume `create_agent()`'s return value.

**Finding 6: T003 cleanup pattern needs explicit guidance for two clients**

Should be two independent try/except blocks so failure to close one client does not prevent the other from being closed.

## Minor Observations (Not Blocking)

1. Spec assumption on endpoint pattern (`https://aws-api.{region}.api.aws/mcp`) is unconfirmed
2. FR-008 (OTEL) coverage is assumed automatic — worth verifying
3. No test tasks despite pytest in tech stack (consistent with spec but a gap relative to Constitution Principle V)
4. `mcp_client.__enter__()` / `__exit__()` direct usage is unusual but existing pattern — replicate exactly
5. Deployment tasks (T005-T009) assume manual CLI execution — consistent with feature 007 pattern

## Recommendations

| Priority | Recommendation | Affects |
|----------|---------------|---------|
| HIGH | Resolve CHK002 before T004: determine whether `aws-api:InvokeMcp` alone is sufficient or whether underlying AWS service permissions are needed | T004, T009 |
| HIGH | Strengthen T008: explicitly list all env vars to preserve; add pre-flight backup step | T008 |
| MEDIUM | Specify the exact new return signature for `create_agent()` in T002 and identify all call sites | T002 |
| MEDIUM | Add explicit "independent try/except per client" guidance to T003 cleanup | T003 |
| LOW | Add note to T001 confirming "no region resolved" returns `(None, [])` with warning log | T001 |
| LOW | Mark integration checklist items as resolved/deferred before implementation | checklists/integration.md |
