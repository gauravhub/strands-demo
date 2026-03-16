# Tasks: AWS API MCP Server Integration

**Input**: Design documents from `/specs/008-aws-api-mcp-server/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: Not explicitly requested in feature specification. Test tasks omitted.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project setup needed — feature extends existing files. This phase is intentionally empty.

**Checkpoint**: Proceed directly to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the AWS API MCP tool loader function that all subsequent phases depend on.

<!-- sequential -->
- [x] T001 Add `get_aws_api_mcp_tools()` function to `src/agent/mcp_tools.py` — follow the identical pattern as `get_eks_mcp_tools()`: resolve region from `AWS_API_MCP_REGION` → `AWS_REGION` → `AWS_DEFAULT_REGION`, construct endpoint `https://aws-api.{region}.api.aws/mcp`, create SigV4 client via `aws_iam_streamablehttp_client(endpoint=endpoint, aws_region=region, aws_service="aws-api")`, wrap in `MCPClient`, call `list_tools_sync()`, return `(mcp_client, tools)` tuple. On failure log warning and return `(None, [])`. Update the module docstring to reflect both EKS and AWS API MCP tools.

**Checkpoint**: `get_aws_api_mcp_tools()` is callable and returns `(None, [])` gracefully when AWS API MCP Server is not reachable (or `(client, tools)` when it is).

---

## Phase 3: User Story 1 — Query AWS Resources via Chat (Priority: P1) 🎯 MVP

**Goal**: Users can ask the agent about AWS resources (S3, Lambda, IAM, etc.) and receive answers using AWS API MCP tools, alongside existing EKS MCP and Tavily tools.

**Independent Test**: Ask the agent "What S3 buckets do I have?" and verify it uses AWS API MCP tools to answer.

### Implementation for User Story 1

<!-- parallel-group: 1 (max 3 concurrent) -->
- [x] T002 [P] [US1] Update `src/agent/chatbot.py` — import `get_aws_api_mcp_tools` from `src/agent/mcp_tools`, call it alongside `get_eks_mcp_tools()`, merge tools as `tools = [tavily, *eks_tools, *aws_api_tools]`, track the AWS API MCP client for cleanup in the except/finally blocks, update the return type to return both MCP clients (or a list of clients), update docstring and log messages to reflect all three tool sets.
- [x] T003 [P] [US1] Update `src/agentcore/app.py` — import `get_aws_api_mcp_tools` from `src/agent/mcp_tools`, call it before the async generator (same as EKS MCP pattern), merge tools as `tools = [tavily, *eks_tools, *aws_api_tools]`, add cleanup for the AWS API MCP client in the `finally` block, update log messages to reflect all three tool sets.

**Checkpoint**: The agent (both local mode and AgentCore mode) loads AWS API MCP tools alongside EKS MCP and Tavily. Asking about AWS resources returns answers via AWS API MCP tools.

---

## Phase 4: User Story 3 — Infrastructure Permissions via CloudFormation (Priority: P1)

**Goal**: The AgentCore Runtime IAM role has permissions to invoke the AWS API MCP Server, managed entirely through CloudFormation.

**Independent Test**: Deploy the updated CloudFormation stack and verify the agent can connect to the AWS API MCP Server without permission errors.

### Implementation for User Story 3

<!-- sequential -->
- [x] T004 [US3] Update `infra/agentcore/template.yaml` — add a new `AwsApiMcpRegion` parameter (String, default `""`, description mirrors `EksMcpRegion`). Add a new `AwsApiMcpAccess` IAM policy on the `AgentExecutionRole` resource with `aws-api:InvokeMcp` action on `Resource: "*"` (same pattern as `EksMcpAccess`). Add `AWS_API_MCP_REGION: !Ref AwsApiMcpRegion` to the `EnvironmentVariables` section of the `AgentRuntime` resource. Update the `AgentRuntime` `Description` property to mention AWS API MCP tools alongside EKS MCP and Tavily.

**Checkpoint**: CloudFormation template is valid and includes the new IAM policy and environment variable.

---

## Phase 5: User Story 4 — Deployment and Runtime Update (Priority: P1)

**Goal**: Deploy the updated agent to AgentCore Runtime, forcing a container restart while preserving all existing configuration including Cognito JWT authorizer.

**Independent Test**: Deploy the update and confirm the agent responds with AWS API MCP tools available alongside EKS MCP and Tavily, and that authentication still works (no 403 errors).

### Implementation for User Story 4

<!-- sequential -->
- [x] T005 [US4] Upload source zip to S3 — run `zip -r source.zip . --exclude '.venv/*' 'specs/*' '.git/*' '.specify/*' '__pycache__/*' '*.pyc'` from repo root, then `aws s3 cp source.zip s3://{BuildSourceBucket}/source.zip` (use the bucket name from the existing CloudFormation stack parameters).
- [x] T006 [US4] Trigger CodeBuild to rebuild the container image — run `aws codebuild start-build --project-name strands-demo-agent-build` and wait for the build to complete successfully. Monitor with `aws codebuild batch-get-builds --ids {build-id}`.
- [x] T007 [US4] Update the CloudFormation stack with the new template — run `aws cloudformation update-stack` with the updated `infra/agentcore/template.yaml` and all existing parameter values preserved. Wait for stack update to complete.
- [x] T008 [US4] Force the AgentCore Runtime to pull the new container image — call `aws bedrock-agentcore update-agent-runtime` with ALL existing configuration preserved: `agentRuntimeName`, `description`, `agentRuntimeArtifact` (with current ContainerUri), `roleArn`, `networkConfiguration`, `protocolConfiguration`, `authorizerConfiguration` (Cognito JWT — discoveryUrl + allowedClients), and `environmentVariables` (including the new `AWS_API_MCP_REGION`). First use `aws bedrock-agentcore get-agent-runtime` to retrieve the current full configuration, then pass it back with updates. This is critical: omitting `authorizerConfiguration` will cause the Runtime to lose its auth config and return 403 errors.
- [x] T009 [US4] Verify the deployed agent works end-to-end (PARTIAL: deployment successful, auth preserved, EKS MCP + Tavily tools work. AWS API MCP tools not available — `aws-api.us-east-1.api.aws` DNS does not resolve (NXDOMAIN). Service not yet available in us-east-1. Graceful degradation works correctly.) — invoke the agent via the Streamlit app (or directly via the AgentCore Runtime endpoint) and confirm: (1) AWS API MCP tools appear in tool invocations alongside EKS MCP and Tavily tools, (2) asking about AWS resources returns answers, (3) authentication still works (no 403 errors on authenticated requests, 403 on unauthenticated requests).

**Checkpoint**: The deployed agent is running with all three tool sets (AWS API MCP, EKS MCP, Tavily) and authentication is intact.

---

## Phase 6: User Story 2 — Combined Multi-Service Queries (Priority: P2)

**Goal**: The agent correctly uses both AWS API MCP and EKS MCP tools for cross-service queries.

**Independent Test**: Ask the agent "Give me an overview of my AWS infrastructure" and verify it uses tools from both MCP servers.

### Implementation for User Story 2

No additional code changes needed — this story is satisfied by the tool merging done in Phase 3 (T002, T003). The agent's LLM naturally selects the appropriate tools based on the query. This phase is a validation checkpoint only.

<!-- sequential -->
- [x] T010 [US2] Validate cross-service queries work (BLOCKED: AWS API MCP Server not available in us-east-1 — cannot validate cross-service queries until service launches. EKS MCP + Tavily tools work correctly.) — test that asking the agent questions spanning multiple AWS services (e.g., "Give me an overview of my AWS infrastructure" or "What IAM roles are associated with my EKS clusters?") results in the agent using tools from both AWS API MCP and EKS MCP servers in the same response.

**Checkpoint**: All user stories functional. Agent uses the correct tool set for each type of query.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Empty — no setup needed
- **Phase 2 (Foundational)**: T001 must complete before any user story work
- **Phase 3 (US1 — Query AWS Resources)**: Depends on T001. T002 and T003 can run in parallel.
- **Phase 4 (US3 — CloudFormation)**: Depends on Phase 2. Can run in parallel with Phase 3.
- **Phase 5 (US4 — Deployment)**: Depends on Phase 3 AND Phase 4 (code + CloudFormation must both be ready). Tasks T005→T006→T007→T008→T009 are strictly sequential.
- **Phase 6 (US2 — Combined Queries)**: Depends on Phase 5 (needs deployed agent to validate).

### User Story Dependencies

- **US1 (Query AWS Resources)**: Depends on Foundational only — core MVP
- **US3 (CloudFormation)**: Depends on Foundational only — can run in parallel with US1
- **US4 (Deployment)**: Depends on US1 + US3 — needs both code and IAM changes
- **US2 (Combined Queries)**: Depends on US4 — validation of deployed agent

### Parallel Opportunities

- T002 and T003 can run in parallel (different files: `chatbot.py` vs `app.py`)
- Phase 3 (US1) and Phase 4 (US3) can run in parallel (code vs CloudFormation)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001 (Foundational — `mcp_tools.py`)
2. Complete T002 + T003 in parallel (Local + AgentCore agent factory)
3. **STOP and VALIDATE**: Test locally — agent loads AWS API MCP tools

### Full Delivery

1. T001 → T002 + T003 in parallel → Code ready
2. T004 in parallel with above → CloudFormation ready
3. T005 → T006 → T007 → T008 → T009 (sequential deployment)
4. T010 (validation of combined queries)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Total: 10 tasks across 6 phases
- The feature is small and focused — most complexity is in deployment (T005–T009)
- T008 is the highest-risk task: incorrectly calling `update-agent-runtime` can break authentication for all users
- No new Python dependencies needed — `mcp-proxy-for-aws` is already in `requirements-agent.txt`
