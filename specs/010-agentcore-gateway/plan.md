# Implementation Plan: AgentCore Gateway Integration

**Branch**: `010-agentcore-gateway` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)

## Summary

Replace direct Tavily SDK usage with AgentCore Gateway — a managed MCP endpoint that centralizes tool access with authentication, observability, and semantic discovery. A Lambda function wraps the Tavily API as a Gateway target. The Gateway shares the same Cognito JWT auth as the Runtime. Graceful degradation falls back to direct Tavily SDK when Gateway is not configured.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: strands-agents>=0.1.0, bedrock-agentcore>=0.1.0, mcp (for streamablehttp_client), tavily-python (Lambda)
**Storage**: N/A
**Testing**: pytest
**Target Platform**: AWS AgentCore Runtime + Streamlit Cloud
**Project Type**: Web service

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | PASS | Uses managed Gateway service, Lambda wraps existing Tavily SDK |
| II. Iterative & Independent Delivery | PASS | Graceful degradation preserves current behavior |
| III. Python-Native Patterns | PASS | All Python 3.11+ |
| IV. Security by Design | PASS | Same Cognito auth for Gateway and Runtime, API key in Lambda env |
| V. Observability & Debuggability | PASS | Log delivery + tracing enabled for Gateway |

## Project Structure

### Source Code (repository root)

```text
src/
├── agent/
│   ├── chatbot.py             # MODIFY: Add gateway_url/access_token params, conditional Gateway vs direct Tavily
│   ├── mcp_tools.py           # MODIFY: Add get_gateway_tools() function
│   └── model.py               # NO CHANGE
├── agentcore/
│   ├── app.py                 # MODIFY: Read AGENTCORE_GATEWAY_URL, propagate access token, load Gateway tools
│   ├── client.py              # MODIFY: Add access_token to payload
│   └── config.py              # NO CHANGE
├── chat/
│   └── ui.py                  # MODIFY: Pass access_token to agent invocation
└── auth/                      # NO CHANGE

app.py                         # MODIFY: Pass gateway_url and access_token to create_agent()

infra/agentcore/
├── template.yaml              # MODIFY: Add Gateway, Lambda, GatewayTarget, Lambda IAM role, env var, output
  # NOTE: No Lambda needed — Tavily uses built-in Gateway integration template
├── Dockerfile                 # NO CHANGE
└── requirements-agent.txt     # NO CHANGE
```

## Architecture

### Gateway Integration Pattern

1. **Gateway MCP Tools Loader** (`src/agent/mcp_tools.py`): New `get_gateway_tools()` that:
   - Takes `gateway_url` and `access_token`
   - Uses `MCPClient` with `streamablehttp_client` transport and Bearer auth headers
   - Calls `list_tools_sync()` to discover tools
   - Returns `(mcp_client, tools)` or `(None, [])` on failure

2. **Agent Factory** (`src/agent/chatbot.py`): Add `gateway_url` and `access_token` params. When `gateway_url` is set, load tools via `get_gateway_tools()` instead of importing `strands_tools.tavily`. When not set, fall back to direct `tavily` import.

3. **AgentCore Entrypoint** (`src/agentcore/app.py`): Read `AGENTCORE_GATEWAY_URL` from env. For access token in AgentCore mode, propagate the JWT from the `Authorization` header (configure header allowlist) or use workload identity token. Pass to agent creation.

4. **CloudFormation** (`infra/agentcore/template.yaml`):
   - `AWS::BedrockAgentCore::Gateway` with CustomJWTAuthorizer (same Cognito)
   - `AGENTCORE_GATEWAY_URL` env var on Runtime (using `!GetAtt Gateway.GatewayUrl`)
   - Output: `AgentCoreGatewayUrl`
   - NOTE: Tavily target uses built-in integration template (added via Console, not CFN)
   - API key stored via AgentCore Identity credential provider

5. **Observability**: Post-deployment CLI commands to enable log delivery + tracing (same pattern as Memory resource).

### Access Token Flow

```
AgentCore Mode:
  User login → Cognito access token → Streamlit → AgentCore Runtime (JWT auth)
  Runtime → propagate token via Authorization header allowlist → Gateway (same JWT auth)

Local Mode:
  User login → Cognito access token → st.session_state["user"]["access_token"]
  create_agent(gateway_url=..., access_token=access_token) → MCPClient with Bearer header
```

## Complexity Tracking

No constitution violations.
