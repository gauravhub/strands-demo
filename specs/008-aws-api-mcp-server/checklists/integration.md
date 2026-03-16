# Integration Checklist: AWS API MCP Server

**Purpose**: Validate requirements quality for MCP server integration, IAM/CloudFormation, deployment safety, and graceful degradation
**Created**: 2026-03-16
**Feature**: [spec.md](../spec.md)
**Depth**: Standard | **Audience**: Reviewer (PR)

## Requirement Completeness

- [ ] CHK001 - Are the specific IAM actions required for `aws-api` service documented with the same granularity as the EKS MCP actions (`eks-mcp:InvokeMcp`, `eks-mcp:CallReadOnlyTool`)? [Completeness, Spec §FR-004]
- [ ] CHK002 - Are requirements for which underlying AWS service permissions (e.g., `s3:ListBuckets`, `lambda:ListFunctions`) the AgentCore role needs — beyond `aws-api:InvokeMcp` — specified or explicitly deferred? [Gap, Spec §FR-004]
- [ ] CHK003 - Is the MCP client cleanup requirement specified for the case where both EKS and AWS API clients are active simultaneously? [Completeness, Plan §MCP Client Lifecycle]
- [ ] CHK004 - Are requirements defined for the `update-agent-runtime` call specifying exactly which configuration fields must be preserved? [Completeness, Spec §FR-010]
- [ ] CHK005 - Is the full list of deployment steps documented as requirements (S3 upload, CodeBuild trigger, CFN update, runtime restart) with ordering dependencies? [Completeness, Spec §FR-009]

## Requirement Clarity

- [ ] CHK006 - Is "gracefully handle connection failures" quantified with specific behavior (log warning, return empty tools, continue with remaining tools)? [Clarity, Spec §FR-007]
- [ ] CHK007 - Is the region resolution priority chain (`AWS_API_MCP_REGION` → `AWS_REGION` → `AWS_DEFAULT_REGION`) explicitly stated as a requirement, not just an assumption? [Clarity, Spec §FR-006]
- [ ] CHK008 - Is "within 15 seconds" in SC-001 defined with specifics (p50, p95, p99) and measurement conditions (cold start vs warm)? [Clarity, Spec §SC-001]
- [ ] CHK009 - Is "all existing configuration" in FR-010 enumerated (authorizerConfiguration, networkConfiguration, protocolConfiguration, roleArn, environmentVariables)? [Clarity, Spec §FR-010]

## Requirement Consistency

- [ ] CHK010 - Are the graceful degradation requirements in FR-007 consistent with the edge case listing (line 79: "both EKS MCP and AWS API MCP unavailable")? [Consistency, Spec §FR-007 vs Edge Cases]
- [ ] CHK011 - Is the pattern described in FR-003 ("same pattern as existing EKS MCP tool loader") consistent with the plan's architecture section describing `get_aws_api_mcp_tools()`? [Consistency, Spec §FR-003 vs Plan §Architecture]
- [ ] CHK012 - Are the deployment requirements in FR-009 consistent with User Story 4 acceptance scenarios? [Consistency, Spec §FR-009 vs US4]

## Scenario Coverage

- [ ] CHK013 - Are requirements defined for the scenario where the AWS API MCP Server returns a partial tool list (some tools load, others fail)? [Coverage, Gap]
- [ ] CHK014 - Are requirements specified for concurrent invocations — can multiple agent invocations each create independent MCP clients without conflicts? [Coverage, Gap]
- [ ] CHK015 - Are requirements defined for the scenario where `update-agent-runtime` fails mid-update — is there a rollback or retry requirement? [Coverage, Edge Case]
- [ ] CHK016 - Are requirements specified for the case where the AWS API MCP Server is available but returns permission denied (IAM misconfiguration)? [Coverage, Spec §Edge Cases]

## Edge Case Coverage

- [ ] CHK017 - Is the behavior specified when no AWS region can be resolved (all three env vars unset)? [Edge Case, Spec §FR-006]
- [ ] CHK018 - Is the behavior defined when the MCP server endpoint URL is constructed but the service doesn't exist in that region? [Edge Case, Spec §Assumptions]
- [ ] CHK019 - Are rate limiting/throttling responses from AWS API MCP Server addressed with specific retry or backoff requirements? [Edge Case, Spec §Edge Cases line 80]

## Non-Functional Requirements

- [ ] CHK020 - Are OTEL observability requirements in FR-008 specific enough — are there defined trace attributes, span names, or log fields for AWS API MCP tool invocations? [Clarity, Spec §FR-008]
- [ ] CHK021 - Are logging requirements specified for AWS API MCP connection status (success/failure) with structured log fields? [Gap, Constitution §V]
- [ ] CHK022 - Is the least-privilege IAM principle in US3-AS3 measurable — are the exact permissions enumerated? [Measurability, Spec §US3]

## Dependencies & Assumptions

- [ ] CHK023 - Is the assumption that "mcp-proxy-for-aws already present in requirements-agent.txt" validated — is a minimum version specified? [Assumption, Plan §Source Code]
- [ ] CHK024 - Is the assumption that "AWS API MCP Server is available in the user's AWS region" documented with a fallback if the service is not yet available? [Assumption, Spec §Assumptions]
- [ ] CHK025 - Is the dependency on the existing EKS MCP integration being stable and unchanged documented? [Dependency, Gap]

## Notes

- Focus areas: Integration pattern fidelity, IAM/CloudFormation correctness, deployment safety (config preservation), graceful degradation
- The spec is well-structured and mirrors feature 007, which reduces ambiguity. Most items focus on gaps in enumeration (exact IAM actions, exact config fields) and edge case specificity.
- CHK002 is the highest-impact item: whether underlying AWS service permissions are needed beyond `aws-api:InvokeMcp` significantly affects CloudFormation scope.
