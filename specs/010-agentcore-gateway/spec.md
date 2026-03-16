# Feature Specification: AgentCore Gateway Integration

**Feature Branch**: `010-agentcore-gateway`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "Integrate AgentCore Gateway to serve Tavily web search tools via managed MCP endpoint"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tavily Tools via Gateway (Priority: P1)

A user asks the agent to search the web. The agent uses Tavily tools served through the AgentCore Gateway (an MCP endpoint) instead of calling the Tavily SDK directly. The user experience is identical — the agent searches the web and returns results — but the tool is now centrally managed, authenticated, and observable through the Gateway.

**Why this priority**: This is the core value — centralizing tool access through a managed MCP endpoint with authentication, observability, and semantic discovery.

**Independent Test**: Ask the agent "Search for latest AWS re:Invent announcements" and verify it uses Gateway-served Tavily tools (tool names will be prefixed with the target name).

**Acceptance Scenarios**:

1. **Given** a user is authenticated, **When** they ask a web search question, **Then** the agent uses Tavily tools served via the AgentCore Gateway.
2. **Given** the Gateway is configured, **When** the agent lists its tools, **Then** Tavily tools appear with Gateway target prefix (e.g., `TavilyTarget___tavily_search`).
3. **Given** the Gateway uses the same Cognito auth as the Runtime, **When** a user's access token is used to call the Gateway, **Then** authentication succeeds without additional login.

---

### User Story 2 - Gateway Infrastructure via CloudFormation (Priority: P1)

The Gateway and its IAM configuration are provisioned through the existing CloudFormation template. The Tavily target is added as a post-deployment step via the AWS Console (built-in integration templates are Console-only).

**Why this priority**: Infrastructure as code ensures reproducibility. The Gateway must be co-deployed with the Runtime.

**Independent Test**: Deploy the updated CloudFormation stack and verify the Gateway is created. Then add the Tavily target via Console.

**Acceptance Scenarios**:

1. **Given** the updated template, **When** the stack deploys, **Then** the Gateway resource and its IAM configuration are created.
2. **Given** the Gateway is created, **When** its auth config is inspected, **Then** it uses the same Cognito User Pool and Client ID as the Runtime.
3. **Given** the Tavily target is added via Console, **When** its configuration is inspected, **Then** it uses the built-in Tavily integration template with outbound API key auth.

---

### User Story 3 - Gateway Required for Web Search (Priority: P1)

When `AGENTCORE_GATEWAY_URL` is configured, the agent loads Tavily tools from the Gateway. When it is not configured, web search tools are simply not available — no fallback to the direct Tavily SDK.

**Why this priority**: Gateway is the canonical path for tool access. Eliminating the fallback simplifies the code and ensures all tool invocations go through the managed, authenticated, observable Gateway.

**Independent Test**: Run the agent without `AGENTCORE_GATEWAY_URL` set and verify no web search tools are loaded (agent cannot search the web). Set `AGENTCORE_GATEWAY_URL` and verify Tavily tools appear via Gateway.

**Acceptance Scenarios**:

1. **Given** `AGENTCORE_GATEWAY_URL` is set, **When** the agent starts, **Then** it loads Tavily tools from the Gateway via MCP.
2. **Given** `AGENTCORE_GATEWAY_URL` is not set, **When** the agent starts, **Then** no web search tools are available (no fallback to direct SDK).
3. **Given** the Gateway is unavailable at runtime, **When** the agent tries to connect, **Then** it logs a warning and web search tools are unavailable.

---

### User Story 4 - Gateway Observability (Priority: P2)

The Gateway resource has log delivery and tracing enabled, providing visibility into tool invocations, authentication events, and errors.

**Why this priority**: Observability follows the project's constitution. Without it, Gateway issues are invisible.

**Independent Test**: Invoke a tool via the Gateway and verify logs appear in CloudWatch and traces in X-Ray.

**Acceptance Scenarios**:

1. **Given** observability is enabled, **When** a tool is invoked via the Gateway, **Then** application logs appear in the Gateway's CloudWatch log group.
2. **Given** tracing is enabled, **When** a tool is invoked, **Then** spans appear in CloudWatch Transaction Search.

---

### User Story 5 - Deployment and Runtime Update (Priority: P1)

The updated agent is deployed to AgentCore Runtime with the Gateway URL as an environment variable. All existing config is preserved.

**Why this priority**: Deployment must be reliable and non-breaking.

**Acceptance Scenarios**:

1. **Given** the code is updated, **When** the deployment pipeline runs, **Then** the agent starts with Gateway tools available.
2. **Given** the Runtime update, **When** auth config is checked, **Then** Cognito JWT authorizer is preserved.

---

### Edge Cases

- What happens when the Gateway endpoint is unreachable but `AGENTCORE_GATEWAY_URL` is set?
- How does the agent handle Gateway authentication failures (expired token)?
- What happens when the Tavily Lambda function fails (API key invalid, rate limited)?
- How does the agent behave when Gateway is unavailable (no fallback)?
- What happens when the access token is not available in local mode for Gateway auth?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST serve Tavily web search tools through an AgentCore Gateway MCP endpoint.
- **FR-002**: System MUST authenticate Gateway requests using the same Cognito User Pool and Client ID as the AgentCore Runtime (same access token works for both).
- **FR-003**: System MUST use the Tavily built-in integration template as a Gateway target, routing requests to the Tavily API with outbound API key auth. The target is added via the AWS Console (built-in templates are not supported via CloudFormation).
- **FR-004**: System MUST provision the Gateway and its associated IAM resources via CloudFormation. The Tavily target MUST be added as a post-deployment manual step via the AWS Console (built-in integration templates are not CFN-supported).
- **FR-005**: When `AGENTCORE_GATEWAY_URL` is not configured, web search tools MUST NOT be loaded (no fallback to direct Tavily SDK). The agent operates without web search capability.
- **FR-006**: System MUST pass the user's access token from the Streamlit frontend to the agent for Gateway authentication.
- **FR-007**: System MUST export the Gateway URL as a CloudFormation output and inject it as `AGENTCORE_GATEWAY_URL` environment variable on the Runtime.
- **FR-008**: System MUST enable observability (log delivery + tracing) for the Gateway resource.
- **FR-009**: The deployment process MUST include S3 upload, CodeBuild rebuild, CloudFormation update, and Runtime restart preserving all config.
- **FR-010**: The Runtime update MUST preserve all existing configuration including authorizerConfiguration.

### Key Entities

- **Gateway**: An AgentCore Gateway MCP endpoint that routes tool calls to configured targets.
- **Gateway Target**: A built-in integration template registered with the Gateway that routes MCP tool calls to the Tavily API with outbound API key authentication. Provides TavilySearchPost and TavilySearchExtract tools.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can search the web via Gateway-served Tavily tools — results are identical to direct SDK usage.
- **SC-002**: The same Cognito access token authenticates both Runtime and Gateway requests — no additional login.
- **SC-003**: CloudFormation deploys all Gateway resources on the first attempt.
- **SC-004**: When `AGENTCORE_GATEWAY_URL` is not set, the agent starts without web search tools (no fallback to direct SDK).
- **SC-005**: Gateway tool invocations appear in CloudWatch logs and X-Ray traces.
- **SC-006**: The Runtime update preserves all existing configuration.

## Clarifications

### Session 2026-03-16

- No critical ambiguities. The Gateway integration pattern, authentication (shared Cognito), Lambda target approach, CloudFormation infrastructure, and deployment process are all explicitly specified.

## Assumptions

- The `AWS::BedrockAgentCore::Gateway` and `AWS::BedrockAgentCore::GatewayTarget` CloudFormation resource types are available in us-east-1.
- The Gateway endpoint URL follows the pattern `https://{gateway-id}.gateway.bedrock-agentcore.{region}.amazonaws.com/mcp`.
- The Strands `MCPClient` with `streamablehttp_client` transport can connect to the Gateway using Bearer token auth.
- The Gateway's `CustomJWTAuthorizer` configuration accepts the same Cognito discovery URL and client ID as the Runtime.
- Vended log delivery for Gateway observability is configured via CloudWatch Logs APIs (not CFN properties).
- The `TAVILY_API_KEY` will be stored in the Lambda environment variable (AgentCore Identity credential provider deferred if CFN resource type not available).
- In AgentCore mode, the access token can be propagated from the Runtime to the Gateway via the `Authorization` header allowlist, or passed in the payload. The simplest approach should be chosen during planning.
