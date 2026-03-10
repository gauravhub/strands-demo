# Phase 0 Research: Deploy Strands Agent to AgentCore

**Branch**: `004-agentcore-deploy` | **Date**: 2026-03-10

## Decision 1: Invocation Protocol (Streamlit → AgentCore)

**Decision**: Raw HTTPS + `requests` library with `stream=True` (SSE), NOT boto3 SDK.

**Rationale**: When an AgentCore Runtime has an OAuth/JWT authorizer configured, the AWS SDK (`invoke_agent_runtime`) cannot be used — it only signs requests with IAM SigV4. The official AWS documentation explicitly states: *"If you're integrating your agent with OAuth, you can't use the AWS SDK to call InvokeAgentRuntime. Instead, make a HTTPS request."* Since this feature requires Cognito Bearer token auth, raw HTTP is mandatory.

**HTTP request format**:
```
POST https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{url-encoded-arn}/invocations?qualifier=DEFAULT
Content-Type: application/json
Authorization: Bearer {cognito_access_token}
X-Amzn-Bedrock-AgentCore-Runtime-Session-Id: {session_id}   # min 33 chars
```

**Streaming**: Use `requests.post(..., stream=True)` and `response.iter_lines()` to consume SSE events. The response `Content-Type` will be `text/event-stream`. Each SSE line is prefixed `data: `.

**Alternatives considered**:
- `boto3.client('bedrock-agentcore').invoke_agent_runtime(...)` — blocked by JWT authorizer incompatibility
- `httpx` with async streaming — works but adds a dependency; `requests` is simpler and already familiar
- `sseclient-py` wrapper — not needed; `iter_lines()` on requests StreamingBody is sufficient for SSE parsing

---

## Decision 2: Agent-Side SDK Package

**Decision**: Use `bedrock-agentcore` (pip package) for the container entrypoint; `bedrock-agentcore-starter-toolkit` for developer CLI/deployment tooling only.

**Rationale**: Two distinct packages exist with completely different roles:
- `bedrock-agentcore` — runtime SDK; provides `BedrockAgentCoreApp`, `RequestContext`; installed *inside the container*.
- `bedrock-agentcore-starter-toolkit` — developer/CI tool; provides the `agentcore` CLI and `Runtime` deployment class; NOT needed at runtime.

**Confirmed import path**: `from bedrock_agentcore.runtime import BedrockAgentCoreApp`

**Streaming entrypoint pattern**: An async generator decorated with `@app.entrypoint` automatically produces SSE output — each `yield` becomes a `data:` line in the SSE stream.

**Alternatives considered**: N/A — these are the only official packages.

---

## Decision 3: Streaming Event Format (Container → Client)

**Decision**: Container yields structured JSON events over SSE, matching the semantic categories already handled by `src/chat/ui.py`.

**Rationale**: The existing `_stream_turn()` function in `src/chat/ui.py` handles 5 event types (`reasoning`, `tool_start`, `tool_result`, `text`, `done`). By forwarding structured events with the same schema, the Streamlit rendering logic can be reused with minimal changes, preserving the reasoning expander and tool call visualizations from feature 003.

**SSE event schema** (emitted by container, consumed by Streamlit client):
```json
{"type": "text",        "data": "token string"}
{"type": "reasoning",   "data": "reasoning token"}
{"type": "tool_start",  "tool_use_id": "...", "name": "tavily", "input": {...}}
{"type": "tool_result", "tool_use_id": "...", "result": "..."}
{"type": "error",       "message": "error string"}
{"type": "done"}
```

**Alternatives considered**:
- Pass raw Strands events — serialization issues (Strands events contain non-JSON-serializable objects); would require deep coupling to Strands internals
- Text-only streaming — loses reasoning and tool call visibility, degrades observability for users; violates Constitution Principle V

---

## Decision 4: CloudFormation Resource Types and Stack Architecture

**Decision**: One CFN stack containing: `AWS::ECR::Repository`, `AWS::IAM::Role` (execution + CodeBuild + Lambda), `AWS::CodeBuild::Project` (ARM64), `AWS::Lambda::Function` (custom resource trigger), `AWS::CloudFormation::CustomResource` (triggers build), `AWS::BedrockAgentCore::Runtime`.

**Rationale**: `AWS::BedrockAgentCore::Runtime` is a confirmed native CFN resource type (added 2025-09-22). There is no native CFN type for the CodeBuild→ECR build pipeline; the standard pattern is CodeBuild + a Lambda-backed custom resource that triggers the build and waits for completion. Cognito IDs are input parameters (not cross-stack imports) per the clarification decision.

**Key CFN constraints discovered**:
- `AgentRuntimeArtifact.ContainerConfiguration.ContainerUri` is **immutable** — updating the image requires resource replacement. Use stable image tags or `RuntimeEndpoint` for blue/green in future iterations.
- `AgentRuntimeName` changes cause resource replacement — use a stable, parameterized name.
- ARM64 is required: CodeBuild must use `ARM_CONTAINER` compute type and `amazonlinux2-aarch64-standard:3.0` image.

**CloudFormation parameters**:
| Parameter | Type | Description |
|---|---|---|
| `CognitoUserPoolId` | String | From 002 stack output |
| `CognitoClientId` | String | From 002 stack output |
| `CognitoRegion` | String | AWS region of the Cognito pool |
| `AnthropicApiKey` | String (NoEcho) | Passed as container env var |
| `TavilyApiKey` | String (NoEcho) | Passed as container env var |
| `ImageTag` | String | Default: `latest` |

**Alternatives considered**:
- Cross-stack `Fn::ImportValue` — rejected (per clarification decision; adds tight coupling)
- Pre-built image outside CFN — simpler but breaks the "single command" reproducibility requirement (SC-005/SC-006)
- `bedrock-agentcore-starter-toolkit` `Runtime` class instead of CFN — rejected (user requirement is CloudFormation only)

---

## Decision 5: Observability Configuration

**Decision**: Install `aws-opentelemetry-distro` in the Dockerfile; use `opentelemetry-instrument python app.py` as the container `CMD`. No CFN resource for GenAI Observability dashboard — it appears automatically.

**Rationale**: OTEL auto-instrumentation is NOT bundled in any AgentCore base image — it must be explicitly installed. The `CMD` must be wrapped with `opentelemetry-instrument` for traces to be emitted. There is no CFN resource for Transaction Search or the GenAI dashboard; both activate automatically once trace data flows through X-Ray.

**IAM permissions required on execution role**:
- CloudWatch Logs: `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`, `DescribeLogGroups`, `DescribeLogStreams` on `/aws/bedrock-agentcore/runtimes/*`
- X-Ray: `PutTraceSegments`, `PutTelemetryRecords`, `GetSamplingRules`, `GetSamplingTargets` on `*`
- CloudWatch Metrics: `PutMetricData` on `*` with condition `cloudwatch:namespace = bedrock-agentcore`
- ECR (for image pull): `GetAuthorizationToken`, `BatchCheckLayerAvailability`, `GetDownloadUrlForLayer`, `BatchGetImage`

**Alternatives considered**:
- `strands-agents[otel]` extra — also valid but `aws-opentelemetry-distro` is the AWS-recommended package; both can coexist
- Dynatrace — third-party, not needed for this iteration
- Manual CloudWatch log forwarding — superseded by OTEL auto-instrumentation

---

## Decision 6: Session ID Generation

**Decision**: Generate `str(uuid.uuid4())` (36 chars) per Streamlit browser tab, stored in `st.session_state`. Pass in `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id` header on every request.

**Rationale**: AgentCore requires session IDs of ≥33 characters. UUID v4 produces 36 characters (with hyphens) — safely above the minimum with no extra logic. Session is ephemeral (per clarification): a page refresh generates a new UUID and starts a fresh agent conversation.

**Idle session timeout**: 900 seconds default. No `LifecycleConfiguration` override needed for the demo.

**Alternatives considered**:
- `secrets.token_hex(20)` (40 chars) — also valid but less universally recognized
- User-scoped persistent session IDs (e.g., Cognito `sub` claim) — rejected per clarification (ephemeral sessions required)
- Sequential integers — too short (< 33 chars) and not unique across page refreshes

---

## Decision 7: Token Expiry Handling

**Decision**: Reactive — detect HTTP 401 response from AgentCore, call `clear_session()`, display "Your session has expired, please log in again" message, and redirect to login page.

**Rationale**: Per the clarification session, no proactive token refresh is required. The existing `clear_session()` in `src/auth/session.py` already handles session cleanup. The reactive approach is consistent with the existing error handling pattern in `app.py` and avoids the complexity of background refresh timers.

**Implementation**: The AgentCore HTTP client checks `response.status_code == 401` before attempting to parse the SSE stream. On 401, it raises a custom `AgentCoreAuthError` that `app.py` catches and handles by calling `clear_session()` and `st.rerun()`.

**Alternatives considered**:
- Proactive refresh using Cognito refresh token — rejected per clarification decision
- Ignore 401 and show generic error — rejected (violates FR-013 which requires session clearance and re-login redirect)
