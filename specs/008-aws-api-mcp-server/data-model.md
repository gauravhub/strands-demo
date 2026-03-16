# Data Model: AWS API MCP Server Integration

**Date**: 2026-03-16 | **Feature**: 008-aws-api-mcp-server

## Entities

This feature introduces no new persistent data entities. All state is ephemeral (per-invocation MCP client connections and tool lists held in memory).

### AWS API MCP Client (runtime object)

- **Type**: Ephemeral connection object (per-invocation lifecycle)
- **Attributes**:
  - `endpoint`: `str` — `https://aws-api.{region}.api.aws/mcp`
  - `region`: `str` — resolved from `AWS_API_MCP_REGION` / `AWS_REGION` / `AWS_DEFAULT_REGION`
  - `aws_service`: `str` — always `"aws-api"` (for SigV4 signing)
- **Lifecycle**: Created → tools listed → used during invocation → closed in `finally`
- **Relationship**: One per agent invocation, alongside the existing EKS MCP Client

### Tool List (runtime object)

- **Type**: List of MCP tool descriptors merged into Agent constructor
- **Composition**: `[tavily, *eks_mcp_tools, *aws_api_mcp_tools]`
- **Attributes per tool**: name, description, input schema (provided by MCP server)

## CloudFormation Additions

### New Parameter

- `AwsApiMcpRegion` (String, default `""`) — optional region override for AWS API MCP Server

### New IAM Policy (on AgentExecutionRole)

- `AwsApiMcpAccess`:
  - `aws-api:InvokeMcp` on `Resource: "*"`

### New Environment Variable (on AgentRuntime)

- `AWS_API_MCP_REGION` — maps to `!Ref AwsApiMcpRegion`
