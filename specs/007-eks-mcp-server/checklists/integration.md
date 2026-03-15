# EKS MCP Server Integration Checklist

**Purpose**: Validate requirements quality for EKS MCP Server integration, CloudFormation IAM permissions, and dual-mode agent operation
**Created**: 2026-03-14
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md)
**Depth**: Standard | **Audience**: Reviewer (PR)

## Requirement Completeness

- [ ] CHK001 - Are all 16 read-only EKS MCP tools explicitly enumerated or is the set defined by reference? [Completeness, Spec §FR-002]
- [ ] CHK002 - Are the specific IAM actions for underlying EKS read operations fully listed, or does "etc." leave scope ambiguous? [Completeness, Spec §FR-005]
- [ ] CHK003 - Are requirements defined for how MCP tools appear in the Streamlit UI (tool call display, result formatting)? [Gap]
- [ ] CHK004 - Is the MCP client lifecycle specified (when connection is established, how long it persists, when it's torn down)? [Gap]
- [ ] CHK005 - Are dependency version constraints specified for `mcp-proxy-for-aws`? [Completeness, Plan §Dependencies]

## Requirement Clarity

- [ ] CHK006 - Is "gracefully handle EKS MCP Server connection failures" quantified with specific behaviors (retry, fallback, error message format)? [Clarity, Spec §FR-008]
- [ ] CHK007 - Is "user-friendly error messages" defined with specific content or format criteria? [Clarity, Spec §SC-004]
- [ ] CHK008 - Is the "auto-detect region" fallback chain (EKS_MCP_REGION → AWS_REGION → AWS_DEFAULT_REGION) unambiguously ordered? [Clarity, Spec §FR-007]
- [ ] CHK009 - Is "accurate answers within 10 seconds" measured from user input to first response token, or to complete response? [Clarity, Spec §SC-001]
- [ ] CHK010 - Is "read-only tools only" enforcement mechanism specified (filter at tool load, IAM denial, or both)? [Clarity, Spec §FR-009]

## Requirement Consistency

- [ ] CHK011 - Are MCP tool integration requirements consistent between local mode (chatbot.py) and AgentCore mode (app.py)? [Consistency, Spec §FR-006]
- [ ] CHK012 - Is the region resolution logic consistent between local and AgentCore deployment modes? [Consistency, Spec §FR-007]
- [ ] CHK013 - Are error handling requirements consistent with the existing Tavily tool error patterns? [Consistency]

## Acceptance Criteria Quality

- [ ] CHK014 - Can SC-002 ("All 16 read-only tools available") be objectively verified without knowing which 16 tools exist? [Measurability, Spec §SC-002]
- [ ] CHK015 - Is "deploys successfully on the first attempt" a meaningful success criterion, or should it specify specific validation checks? [Measurability, Spec §SC-003]
- [ ] CHK016 - Are acceptance scenarios for User Story 2 (troubleshooting) testable without a specific cluster configuration? [Measurability, Spec §US-2]

## Scenario Coverage

- [ ] CHK017 - Are requirements defined for the scenario where EKS MCP Server is unavailable but other agent tools still work (graceful degradation)? [Coverage, Edge Case]
- [ ] CHK018 - Are requirements specified for concurrent MCP tool calls (can the agent invoke multiple EKS tools in parallel)? [Coverage, Gap]
- [ ] CHK019 - Are requirements defined for what happens when AWS credentials expire mid-session? [Coverage, Exception Flow]
- [ ] CHK020 - Are requirements specified for EKS clusters in a different region than the configured MCP region? [Coverage, Edge Case]

## Security & IAM Requirements

- [ ] CHK021 - Are IAM permission boundaries explicitly scoped to prevent privilege escalation beyond read-only? [Coverage, Spec §FR-004]
- [ ] CHK022 - Is the IAM resource scope defined (specific cluster ARNs vs. wildcard `*`)? [Clarity, Spec §FR-004]
- [ ] CHK023 - Are CloudTrail audit logging requirements for EKS MCP invocations specified? [Gap]
- [ ] CHK024 - Is the SigV4 credential chain for AgentCore mode documented (role assumption vs. instance profile)? [Clarity, Spec §Assumptions]

## Dependencies & Assumptions

- [ ] CHK025 - Is the assumption "EKS MCP Server (preview) is available in the user's AWS region" validated with a list of supported regions? [Assumption, Spec §Assumptions]
- [ ] CHK026 - Is the assumption that Strands SDK MCP instrumentation provides OTEL spans validated against SDK version? [Assumption, Spec §FR-010]
- [ ] CHK027 - Are requirements defined for behavior if `mcp-proxy-for-aws` package is unavailable or incompatible? [Dependency, Gap]
