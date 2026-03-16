# Data Model: AgentCore Gateway Integration

**Date**: 2026-03-16 | **Feature**: 010-agentcore-gateway

## CloudFormation Resources

### New Resources

| Resource | Type | Purpose |
|----------|------|---------|
| `AgentCoreGateway` | `AWS::BedrockAgentCore::Gateway` | MCP endpoint for tool access |
| `TavilyLambdaRole` | `AWS::IAM::Role` | Execution role for Tavily Lambda |
| `TavilyLambdaFunction` | `AWS::Lambda::Function` | Wraps Tavily API as MCP target |
| `TavilyGatewayTarget` | `AWS::BedrockAgentCore::GatewayTarget` | Registers Lambda with Gateway |

### Modified Resources

| Resource | Change |
|----------|--------|
| `AgentRuntime` | Add `AGENTCORE_GATEWAY_URL` env var, remove `TAVILY_API_KEY` |

### New Output

- `AgentCoreGatewayUrl` — the Gateway MCP endpoint URL

### New File

- `infra/agentcore/tavily_lambda/index.py` — Lambda handler code
