# Pre-Implementation Review

**Feature**: Enable AgentCore Observability
**Artifacts reviewed**: spec.md, plan.md, tasks.md, checklists/observability.md, constitution.md, template.yaml, Dockerfile, requirements-agent.txt
**Review model**: Claude Opus 4.6
**Date**: 2026-03-10

## Summary

| Dimension | Verdict | Issues |
|-----------|---------|--------|
| Spec-Plan Alignment | PASS | All 4 user stories addressed; IaC-first constraint correctly reflected |
| Plan-Tasks Completeness | WARN | Missing source zip upload step; T001/T002 same-file conflict |
| Dependency Ordering | WARN | Source zip must be uploaded before CFN deploy; no stack output extraction task |
| Parallelization Correctness | WARN | T001 and T002 both modify template.yaml but marked [P] in same group |
| Feasibility & Risk | PASS | Small scope, minimal code changes, well-understood AWS APIs |
| Standards Compliance | PASS | Constitution fully satisfied; no security concerns |
| Implementation Readiness | WARN | CLI commands use placeholder variables without extraction step |

**Overall**: READY WITH WARNINGS

## Findings

### Critical (FAIL — must fix before implementing)

None.

### Warnings (WARN — recommend fixing, can proceed)

1. **T001 and T002 same-file conflict.** Both edit `infra/agentcore/template.yaml` but are in parallel-group 1. Will conflict if executed concurrently. T003 (requirements-agent.txt) is truly independent.

2. **Missing source zip upload task.** CodeBuild pulls from S3 (`source.zip`). T003 modifies `requirements-agent.txt` locally but no task uploads updated source to S3 before T004. CodeBuild would use stale source.

3. **No stack output extraction task.** Tasks T006-T014 reference `${RUNTIME_ID}`, `${RUNTIME_ARN}`, `${IDENTITY_ARN}` without a task to run `aws cloudformation describe-stacks` to obtain them.

4. **Uncertain CLI API flags.** T006/T012 use `--tracing-configuration` and `--identity-tracing-configuration` that may not exist. Tasks include fallback language — acceptable but ambiguous.

5. **CodeBuild may not auto-trigger.** `TriggerImageBuild` custom resource fires on Create/property-change, not on unrelated resource additions. T004 description says it "triggers CodeBuild" which may be misleading. T015 handles manual trigger as fallback.

### Observations (informational)

1. FR-007/FR-008 describe changes already in place (Dockerfile CMD and aws-opentelemetry-distro). Only `strands-agents[otel]` is new.
2. Log group `/aws/vendedlogs/` prefix differs from IAM scope `/aws/bedrock-agentcore/runtimes/*` — vendedlogs IAM is service-managed, no change needed.
3. Checklist has 32 unchecked items — expected at this stage.
4. US1-US4 could run in parallel but sequential is reasonable for single implementer.

## Recommended Actions

- [ ] Merge T001 and T002 into a single task (both edit template.yaml), or make them sequential
- [ ] Add source zip upload task between Phase 1 and Phase 2
- [ ] Add stack output extraction task at start of Phase 3
- [ ] Clarify T004 description re: CodeBuild trigger behavior
