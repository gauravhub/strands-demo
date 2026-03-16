# Tasks: AgentCore Gateway Integration

**Input**: Design documents from `/specs/010-agentcore-gateway/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Organization**: Tasks grouped by user story.

**Key discovery**: Tavily is a **built-in integration template** in AgentCore Gateway — no Lambda function needed. The Gateway routes requests directly to `https://api.tavily.com` with API key outbound auth. The Tavily template provides two tools: `TavilySearchPost` (/search) and `TavilySearchExtract` (/extract).

**Limitation**: Built-in integration templates can only be added via the **AWS Management Console**, not via CloudFormation API. The Gateway itself is created via CFN, but the Tavily target is added as a manual post-deployment step via Console.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Foundational — Gateway Tools Loader

**Purpose**: Add the function to load tools from AgentCore Gateway.

<!-- sequential -->
- [ ] T001 Add `get_gateway_tools()` function to `src/agent/mcp_tools.py` — takes `gateway_url: str` and `access_token: str` parameters. Uses `MCPClient` from `strands.tools.mcp.mcp_client` with `streamablehttp_client` from `mcp.client.streamable_http` transport. Creates the client factory lambda with Bearer token auth headers: `headers={"Authorization": f"Bearer {access_token}"}`. Calls `list_tools_sync()` to discover tools. Returns `(mcp_client, tools)` tuple. On failure logs warning and returns `(None, [])`. Follow the same pattern as `get_eks_mcp_tools()` but using `streamablehttp_client` instead of `aws_iam_streamablehttp_client`.

**Checkpoint**: `get_gateway_tools()` is callable and handles failures gracefully.

---

## Phase 2: User Story 1 — Tavily Tools via Gateway (Priority: P1) 🎯 MVP

**Goal**: Agent uses Tavily tools from Gateway instead of direct SDK.

<!-- parallel-group: 1 (max 3 concurrent) -->
- [ ] T002 [P] [US1] Update `src/agent/chatbot.py` — add `gateway_url: str | None = None` and `access_token: str | None = None` parameters to `create_agent()`. When `gateway_url` is set, call `get_gateway_tools(gateway_url, access_token)` to load Tavily tools from Gateway instead of importing `strands_tools.tavily`. When not set, fall back to `from strands_tools import tavily` (current behavior). Merge Gateway tools into tool list alongside EKS MCP and AWS MCP tools. Track the Gateway MCP client for cleanup. Remove the `TAVILY_API_KEY` validation check when Gateway is used (the API key is managed by the Gateway target, not the agent).
- [ ] T003 [P] [US1] Update `src/agentcore/app.py` — read `AGENTCORE_GATEWAY_URL` from environment. Extract access token from `context.request_headers.get('Authorization')` (strip "Bearer " prefix). Pass `gateway_url` and `access_token` to agent creation. If Gateway tools fail to load, fall back to direct `strands_tools.tavily`. Add Gateway MCP client cleanup in finally block.
- [ ] T004 [P] [US1] Update `src/agentcore/client.py` — add `access_token_raw: str = ""` parameter to `invoke_streaming()` (the raw Cognito token for Gateway use). Include it in the JSON payload as `"access_token"`. Update docstring.

<!-- sequential -->
- [ ] T005 [US1] Update `src/chat/ui.py` — pass `access_token` through to `_stream_turn_agentcore()` and `invoke_streaming()` so the agent backend receives it for Gateway auth. The access_token is already available in the `render_chatbot_agentcore()` function params.
- [ ] T006 [US1] Update `app.py` — read `AGENTCORE_GATEWAY_URL` from environment. In local mode, pass `gateway_url` and `access_token` (from `user["access_token"]`) to `create_agent()`. In AgentCore mode, pass `access_token` to `render_chatbot_agentcore()` (already done) and ensure it flows to the payload.

**Checkpoint**: Agent loads Tavily tools from Gateway in both modes. Falls back to direct SDK when Gateway not configured.

---

## Phase 3: User Story 2 — CloudFormation Infrastructure (Priority: P1)

**Goal**: Gateway resource provisioned via CloudFormation. Tavily target added manually via Console.

<!-- sequential -->
- [ ] T007 [US2] Update `infra/agentcore/template.yaml` — add Gateway resources:
  1. `AgentCoreGateway` (`AWS::BedrockAgentCore::Gateway`) — name `strands_demo_gateway`, ProtocolType `MCP`, RoleArn from `AgentExecutionRole`, AuthorizerConfiguration with `CustomJWTAuthorizer` using same Cognito discovery URL and AllowedClients as Runtime (reuse `CognitoUserPoolId`, `CognitoRegion`, `CognitoClientId` parameters). Enable semantic search if supported.
  2. Add `AGENTCORE_GATEWAY_URL` to AgentRuntime `EnvironmentVariables` using `!Sub "${AgentCoreGateway.GatewayUrl}/mcp"` or `!GetAtt AgentCoreGateway.GatewayUrl` (verify correct attribute name).
  3. Add output `AgentCoreGatewayUrl` exporting the Gateway URL.
  4. Configure Runtime `RequestHeaderAllowlist` to pass `Authorization` header through to agent code (needed for Gateway auth in AgentCore mode).
  NOTE: The Tavily target is NOT created via CFN — it uses a built-in integration template that can only be added via the Console. This is a post-deployment manual step (T009).

**Checkpoint**: CloudFormation template is valid with Gateway resource.

---

## Phase 4: User Story 5 — Deployment (Priority: P1)

<!-- sequential -->
- [ ] T008 [US5] Upload source zip to S3 and trigger CodeBuild rebuild. Wait for build completion.
- [ ] T009 [US5] Update CloudFormation stack with all existing params preserved. Wait for completion. Verify Gateway resource is created.
- [ ] T010 [US5] Add Tavily target to Gateway via Console — navigate to the AgentCore Gateway in AWS Console, add the Tavily Search built-in template as a target. Configure outbound auth with API key (use the existing Tavily API key). This is a manual step because built-in templates can only be added via Console. Use AgentCore Identity to create an API key credential provider for the Tavily API key, then reference it in the target's outbound auth configuration.
- [ ] T011 [US5] Force Runtime to pull new container image — call `aws bedrock-agentcore-control get-agent-runtime` then `aws bedrock-agentcore-control update-agent-runtime` with ALL config preserved (authorizerConfiguration, environmentVariables including new AGENTCORE_GATEWAY_URL, etc.). Wait for READY.
- [ ] T012 [US5] Verify end-to-end via Streamlit app — confirm Tavily tools are served through Gateway (tool names will be prefixed, e.g., `TavilySearch___TavilySearchPost`), web search works, auth works, all existing tools (EKS MCP, AWS MCP) still function.

**Checkpoint**: Deployed agent uses Gateway tools. All existing functionality preserved.

---

## Phase 5: User Story 4 — Observability (Priority: P2)

<!-- sequential -->
- [ ] T013 [US4] Enable observability for Gateway — create CloudWatch log group `/aws/vendedlogs/bedrock-agentcore/{gateway-id}`, configure delivery sources (APPLICATION_LOGS + TRACES), delivery destinations (CWL + XRAY), and create deliveries. Same pattern as Memory resource observability. Use Gateway ID from CloudFormation output.

**Checkpoint**: Gateway logs and traces appear in CloudWatch.

---

## Dependencies & Execution Order

- T001 → T002+T003+T004 (parallel) → T005 → T006 → Code ready
- T007 (CloudFormation) can run in parallel with T001-T006
- T008 → T009 → T010 (manual Console step) → T011 → T012 (sequential deployment)
- T013 after T009 (needs Gateway resource ID)

## Notes

- Total: 13 tasks across 5 phases
- **No Lambda function needed** — Tavily is a built-in Gateway integration template
- T010 is a **manual Console step** — built-in templates cannot be added via API/CFN
- T011 is highest-risk (update-agent-runtime must preserve all config)
- Graceful degradation (US3) is handled within T002/T003 — no separate tasks needed
- The Tavily API key is stored via AgentCore Identity credential provider (API key type), not as an env var on the Runtime
