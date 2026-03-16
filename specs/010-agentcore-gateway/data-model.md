# Data Model: AgentCore Gateway Integration

**Date**: 2026-03-16 | **Feature**: 010-agentcore-gateway

## CloudFormation Resources

### New Resources

| Resource | Type | Purpose |
|----------|------|---------|
| `AgentCoreGateway` | `AWS::BedrockAgentCore::Gateway` | MCP endpoint for tool access with CustomJWTAuthorizer |

### Console-Only Resources (post-deployment manual step)

| Resource | Type | Purpose |
|----------|------|---------|
| Tavily Target | Built-in integration template | Routes MCP tool calls to Tavily API with outbound API key auth |

### Modified Resources

| Resource | Change |
|----------|--------|
| `AgentRuntime` | Add `AGENTCORE_GATEWAY_URL` env var, add `Authorization` to RequestHeaderAllowlist |

### New Output

- `AgentCoreGatewayUrl` — the Gateway MCP endpoint URL
