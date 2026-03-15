# Tasks: EKS MCP Server Integration

**Input**: Design documents from `/specs/007-eks-mcp-server/`
**Prerequisites**: plan.md (required), spec.md (required), research.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Dependencies & Configuration)

**Purpose**: Add new dependencies and environment configuration

<!-- parallel-group: 1 (max 3 concurrent) -->
- [x] T001 [P] Add `mcp-proxy-for-aws>=1.0.0` to dependencies in pyproject.toml (check PyPI for latest stable version and pin minimum)
- [x] T002 [P] Add `mcp-proxy-for-aws>=1.0.0` to container dependencies in infra/agentcore/requirements-agent.txt (same version constraint as T001)
- [x] T003 [P] Add EKS MCP section to .env.example — append after the AgentCore section: a comment header `# ── EKS MCP Server (feature 007) ───`, then `# Optional: override auto-detected region for EKS MCP Server.`, then `# Leave unset to use AWS_REGION (from AgentCore config) or AWS_DEFAULT_REGION.`, then `# EKS_MCP_REGION=us-west-2`

---

## Phase 2: Foundational (MCP Tools Module + IAM)

**Purpose**: Create the MCP tools module and CloudFormation IAM permissions that all user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

<!-- parallel-group: 2 (max 2 concurrent) -->
- [x] T004 [P] Create MCP tools module in src/agent/mcp_tools.py — implement `get_eks_mcp_tools()` function that: (1) resolves region using `os.getenv("EKS_MCP_REGION") or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")` (use `or` chaining so empty strings from CloudFormation defaults are treated as unset), (2) if no region resolved, log warning and return (None, []), (3) creates `aws_iam_streamablehttp_client` factory for endpoint `https://eks-mcp.{region}.api.aws/mcp` with `aws_service="eks-mcp"`, (4) creates MCPClient with the factory, (5) calls `mcp_client.__enter__()` to open the connection (do NOT use a `with` block — the caller manages lifecycle because tools must remain usable after this function returns), (6) calls `list_tools_sync()` to get tools, (7) returns tuple of (mcp_client, tools_list), (8) handles connection errors gracefully by logging warning and returning (None, empty list). Import from `mcp_proxy_for_aws.client` and `strands.tools.mcp.mcp_client`. Note: research.md R4 shows a `with MCPClient(...)` example — that pattern is illustrative only; here we must keep the client open so the agent can invoke tools after `get_eks_mcp_tools()` returns.
- [x] T005 [P] Add EKS MCP IAM policies and environment variable to infra/agentcore/template.yaml — (A) Add EksMcpAccess inline policy to AgentExecutionRole with actions: `eks-mcp:InvokeMcp`, `eks-mcp:CallReadOnlyTool` on Resource `"*"`. (B) Add EksReadAccess policy with actions: `eks:DescribeCluster`, `eks:ListClusters`, `eks:ListNodegroups`, `eks:DescribeNodegroup`, `eks:ListAddons`, `eks:DescribeAddon`, `eks:ListAccessEntries`, `eks:DescribeAccessEntry`, `eks:AccessKubernetesApi`, `eks:DescribeInsight`, `eks:ListInsights` on Resource `"*"`. (C) Add EksSupportingReadAccess policy with actions: `logs:StartQuery`, `logs:GetQueryResults`, `cloudwatch:GetMetricData`, `sts:GetCallerIdentity`, `iam:GetRole`, `iam:ListAttachedRolePolicies`, `iam:ListRolePolicies`, `iam:GetRolePolicy` on Resource `"*"`. (D) Add new `EksMcpRegion` parameter (Type: String, Default: empty string, Description: "Region for EKS MCP Server. Leave empty to auto-detect from deployment region."). (E) Add `EKS_MCP_REGION: !Ref EksMcpRegion` to AgentRuntime EnvironmentVariables.

**Checkpoint**: MCP tools module and IAM permissions ready — user story implementation can begin

---

## Phase 3: User Story 1 — Query EKS Clusters via Chat (Priority: P1) MVP

**Goal**: Users can ask natural language questions about their EKS clusters and get accurate answers

**Independent Test**: Ask the agent "What EKS clusters do I have?" and verify it returns cluster names and status from the AWS account

### Implementation for User Story 1

<!-- parallel-group: 3 (max 2 concurrent) -->
- [x] T006 [P] [US1] Integrate MCP tools into local agent in src/agent/chatbot.py — modify `create_agent()` to: (1) import `get_eks_mcp_tools` from `src.agent.mcp_tools`, (2) call `get_eks_mcp_tools()` to get `(mcp_client, eks_tools)`, (3) create Agent with `tools=[tavily, *eks_tools]`, (4) store mcp_client reference for cleanup, (5) log the number of EKS MCP tools loaded. If `get_eks_mcp_tools()` returns empty tools, log a warning and create agent with only tavily (graceful degradation).
- [x] T007 [P] [US1] Integrate MCP tools into AgentCore agent in src/agentcore/app.py — call `get_eks_mcp_tools()` BEFORE entering the async generator in `invoke()` (at the top of the function, before the `try` block) to avoid blocking the event loop inside the generator. Steps: (1) import `get_eks_mcp_tools` from `src.agent.mcp_tools`, (2) call `get_eks_mcp_tools()` to get `(mcp_client, eks_tools)`, (3) create Agent with `tools=[tavily, *eks_tools]`, (4) wrap the entire async generator body in try/finally to call `mcp_client.stop()` on cleanup (note: in async generators, finally runs when the generator is closed or garbage-collected), (5) log the number of EKS MCP tools loaded. If `get_eks_mcp_tools()` returns empty tools, log a warning and create agent with only tavily.

**Checkpoint**: User Story 1 complete — agent can query EKS clusters in both local and AgentCore modes

---

## Phase 4: User Story 3 — Infrastructure Permissions via CloudFormation (Priority: P1)

**Goal**: All IAM permissions are managed through CloudFormation — no manual IAM changes needed

**Independent Test**: Deploy the updated CloudFormation stack and verify the agent can successfully connect to the EKS MCP Server without permission errors

### Implementation for User Story 3

<!-- sequential -->
- [x] T008 [US3] Validate CloudFormation template syntax in infra/agentcore/template.yaml — run `aws cloudformation validate-template --template-body file://infra/agentcore/template.yaml` to ensure the updated template with EKS MCP IAM policies is syntactically valid. Fix any validation errors.

**Checkpoint**: User Story 3 complete — CloudFormation template validated with all required EKS MCP permissions (implementation done in Phase 2 task T005)

---

## Phase 5: User Story 2 — Troubleshoot EKS Clusters via Chat (Priority: P2)

**Goal**: Users can troubleshoot EKS cluster issues by asking about pod logs, events, insights, and metrics

**Independent Test**: Ask the agent "Show me recent events in cluster X" and verify it retrieves Kubernetes events

### Implementation for User Story 2

*No additional code changes required* — the 16 read-only MCP tools loaded in Phase 3 (T006/T007) already include troubleshooting tools (get_pod_logs, get_k8s_events, get_eks_insights, get_cloudwatch_logs, get_cloudwatch_metrics). This phase validates that troubleshooting scenarios work end-to-end.

<!-- sequential -->
- [x] T009 [US2] Validate troubleshooting tools are available — run the agent locally (T006 path) and verify that troubleshooting-related MCP tools (get_pod_logs, get_k8s_events, get_eks_insights, get_cloudwatch_logs, get_cloudwatch_metrics) are in the loaded tool list by checking the agent log output. The same tools are loaded in AgentCore mode (T007) since both paths call `get_eks_mcp_tools()` — local validation is sufficient to confirm tool availability for both modes.

**Checkpoint**: User Story 2 validated — troubleshooting tools confirmed available

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation updates

<!-- sequential -->
- [x] T010 Update AgentRuntime description in infra/agentcore/template.yaml — change the Description property to mention EKS MCP tools: "Strands reasoning chatbot with Tavily web search and EKS MCP tools, secured by Cognito JWT"
- [x] T011 Validate OTEL observability for MCP tool calls (FR-010) — run the agent with `opentelemetry-instrument python app.py` and invoke an EKS query. Pass criteria: (1) OTEL console exporter or CloudWatch traces show spans for MCP tool invocations (look for span names containing "tool" or the MCP tool name like "list_eks_resources"), (2) spans include attributes such as tool name and duration. If no MCP spans appear, check that `strands-agents[otel]` is installed and that `strands.tools.mcp.mcp_instrumentation` module exists in the installed SDK version. If the SDK does not auto-instrument MCP, document as a known gap for future work.
- [x] T012 Run quickstart.md validation — follow the validation steps in specs/007-eks-mcp-server/quickstart.md to verify local mode works end-to-end (start app, login, ask about EKS clusters, verify response)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 adds the dependency; run `pip install -e .` or `uv sync` after Phase 1 before T004 can import the package). T005 is independent of T004.
- **User Story 1 (Phase 3)**: Depends on T004 (mcp_tools module)
- **User Story 3 (Phase 4)**: Depends on T005 (IAM policies + env var in template)
- **User Story 2 (Phase 5)**: Depends on T006/T007 (tools loaded in agent)
- **Polish (Phase 6)**: Depends on all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2) — no dependencies on other stories
- **User Story 3 (P1)**: Depends on Foundational (Phase 2) — no dependencies on other stories, can run in parallel with US1
- **User Story 2 (P2)**: Depends on User Story 1 (needs tools loaded) — validation only, no new code

### Within Each User Story

- Models/modules before integration
- Core implementation before validation
- Commit after each task or logical group

### Parallel Opportunities

- Phase 1: All 3 tasks (T001-T003) run in parallel
- Phase 2: T004 and T005 run in parallel (different files)
- Phase 3: T006 and T007 run in parallel (different files)
- Phase 3 and Phase 4 can run in parallel (different concerns)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (3 tasks, parallel)
2. Complete Phase 2: Foundational (3 tasks, parallel)
3. Complete Phase 3: User Story 1 (2 tasks, parallel)
4. **STOP and VALIDATE**: Ask agent about EKS clusters
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. User Story 1 → Test independently → MVP!
3. User Story 3 → Validate CloudFormation → Infrastructure confirmed
4. User Story 2 → Validate troubleshooting → Full feature complete
5. Polish → Final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Total: 12 tasks across 6 phases (T001-T012)
- MCP tools are loaded once and provide all 16 read-only EKS tools — no per-story tool configuration needed
- Graceful degradation: if EKS MCP connection fails, agent still works with Tavily only
- Read-only enforcement (FR-009): IAM-only — the policy grants `eks-mcp:CallReadOnlyTool` but not `eks-mcp:CallPrivilegedTool`. Write tools may appear in the tool list but will fail at IAM level if invoked. No application-layer filter is applied (conscious risk acceptance — IAM is the security boundary)
