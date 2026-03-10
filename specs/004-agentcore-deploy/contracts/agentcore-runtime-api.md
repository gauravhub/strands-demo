# Contract: AgentCore Runtime Invocation API

**Feature**: `004-agentcore-deploy` | **Date**: 2026-03-10
**Direction**: Streamlit app (caller) → AgentCore Runtime endpoint (agent)

---

## Inbound Invocation (Streamlit → AgentCore)

### Endpoint

```
POST https://bedrock-agentcore.{AWS_REGION}.amazonaws.com/runtimes/{url_encoded_runtime_arn}/invocations?qualifier=DEFAULT
```

Where `{url_encoded_runtime_arn}` is the URL-percent-encoded form of the Runtime ARN:
```
arn:aws:bedrock-agentcore:{region}:{account}:runtime/{runtime-id}
→ arn%3Aaws%3Abedrock-agentcore%3A...
```

### Request Headers

| Header | Required | Value |
|---|---|---|
| `Authorization` | Yes | `Bearer {cognito_access_token}` |
| `Content-Type` | Yes | `application/json` |
| `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id` | Yes | UUID v4 string (36 chars, ≥33 required) |

### Request Body

```json
{
  "prompt": "string — the user's message for this turn"
}
```

### Success Response

**Status**: `200 OK`
**Content-Type**: `text/event-stream`

SSE stream of events, each on its own line prefixed `data: `, followed by `\n\n`:

```
data: {"type": "reasoning", "data": "Let me think about..."}\n\n
data: {"type": "tool_start", "tool_use_id": "tu_123", "name": "tavily", "input": {"query": "..."}}\n\n
data: {"type": "tool_result", "tool_use_id": "tu_123", "result": "search results text"}\n\n
data: {"type": "text", "data": "Based on "}\n\n
data: {"type": "text", "data": "the results..."}\n\n
data: {"type": "done"}\n\n
```

### Error Responses

| Status | Condition | Streamlit Behavior |
|---|---|---|
| `401 Unauthorized` | Expired or invalid Cognito token | Clear session → redirect to login with "session expired" message |
| `403 Forbidden` | Token from wrong pool/client | Display auth error; do not clear session |
| `503 Service Unavailable` | Runtime temporarily unavailable | Display "Service temporarily unavailable. Please try again." |
| `504 Gateway Timeout` | Agent execution exceeded timeout | Display "Request timed out. Please try again with a shorter query." |

---

## SSE Event Schema (Container → Client)

All events are JSON objects on `data:` lines. The `type` field discriminates the event.

### `text` event

Emitted for each response token.

```json
{"type": "text", "data": "token string"}
```

### `reasoning` event

Emitted for each extended thinking token (Claude's internal reasoning).

```json
{"type": "reasoning", "data": "reasoning token string"}
```

### `tool_start` event

Emitted when the agent begins a tool invocation.

```json
{
  "type": "tool_start",
  "tool_use_id": "tooluse_abc123",
  "name": "tavily",
  "input": {"query": "search query"}
}
```

### `tool_result` event

Emitted when a tool returns its result.

```json
{
  "type": "tool_result",
  "tool_use_id": "tooluse_abc123",
  "result": "tool output text"
}
```

### `error` event

Emitted if the agent encounters an unrecoverable error during execution.

```json
{"type": "error", "message": "description of what went wrong"}
```

### `done` event

Emitted as the final event in the stream, signalling completion.

```json
{"type": "done"}
```

---

## AgentCore Runtime Container Contract

The container exposes port 8080 with the following built-in endpoints (managed by `BedrockAgentCoreApp`):

| Path | Method | Purpose |
|---|---|---|
| `/invocations` | `POST` | Main agent entrypoint — receives the payload, runs the agent |
| `/ping` | `GET` | Health check — returns `HEALTHY` or `HEALTHY_BUSY` |

The container `CMD` MUST be wrapped with `opentelemetry-instrument` for OTEL tracing:

```
CMD ["opentelemetry-instrument", "python", "app.py"]
```

The container MUST be built for `linux/arm64` (ARM64) architecture.

---

## CloudFormation Stack Interface

### Input Parameters

| Parameter | Type | Description |
|---|---|---|
| `CognitoUserPoolId` | String | Cognito User Pool ID from 002 stack |
| `CognitoClientId` | String | Cognito App Client ID from 002 stack |
| `CognitoRegion` | String | AWS region of the Cognito pool |
| `AnthropicApiKey` | String (NoEcho) | Anthropic API key for the agent model |
| `TavilyApiKey` | String (NoEcho) | Tavily API key for the web search tool |
| `ImageTag` | String | ECR image tag; default `latest` |

### Outputs

| Output | Description | Used By |
|---|---|---|
| `AgentRuntimeArn` | Full ARN of the deployed AgentCore Runtime | Streamlit `.env` → `AGENTCORE_RUNTIME_ARN` |
| `AgentRuntimeId` | Short runtime ID | Monitoring, log group lookup |
| `ECRRepositoryUri` | ECR repository URI | CI/CD image push |

### Streamlit Environment Variables (from stack outputs)

```ini
# .env additions for 004-agentcore-deploy
AGENTCORE_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/...
AWS_REGION=us-east-1
```

When `AGENTCORE_RUNTIME_ARN` is set, `app.py` routes agent invocations to AgentCore. When absent, the app falls back to local agent execution (backward compatible for development).
