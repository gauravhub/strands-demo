# Research: AWS API MCP Server Integration

**Date**: 2026-03-16 | **Feature**: 008-aws-api-mcp-server

## R1: AWS API MCP Server Endpoint and SigV4 Service Name

- **Decision**: Endpoint `https://aws-api.{region}.api.aws/mcp`, SigV4 service `"aws-api"`
- **Rationale**: Explicitly provided by user; follows the same pattern as EKS MCP Server (`eks-mcp.{region}.api.aws/mcp` with service `"eks-mcp"`)
- **Alternatives considered**: None — the endpoint pattern is defined by AWS

## R2: IAM Permissions for AWS API MCP Server

- **Decision**: Grant `aws-api:InvokeMcp` on the AgentExecutionRole via CloudFormation
- **Rationale**: Mirrors the EKS MCP pattern (`eks-mcp:InvokeMcp`, `eks-mcp:CallReadOnlyTool`). The AWS API MCP Server uses its own IAM action namespace (`aws-api:*`). Since the AWS API MCP Server acts as a proxy to underlying AWS APIs, the specific service permissions (e.g., `s3:ListBuckets`) may also be needed — but the MCP server itself handles the authorization chain. Start with `aws-api:InvokeMcp` and add underlying service permissions only if needed.
- **Alternatives considered**: Granting broad `aws-api:*` — rejected in favor of least-privilege `aws-api:InvokeMcp`

## R3: Region Resolution for AWS API MCP Server

- **Decision**: Follow the same priority chain as EKS MCP: `AWS_API_MCP_REGION` → `AWS_REGION` → `AWS_DEFAULT_REGION`
- **Rationale**: Consistent with existing pattern. Allows per-service override while defaulting to deployment region.
- **Alternatives considered**: Shared `MCP_REGION` env var for all MCP servers — rejected because different MCP servers could be in different regions

## R4: MCP Client Cleanup with Multiple Clients

- **Decision**: Track both MCP clients (EKS and AWS API) independently; clean up both in `finally` blocks
- **Rationale**: Each client has its own connection lifecycle. Both `chatbot.py` and `agentcore/app.py` need to manage two client references.
- **Alternatives considered**: Single wrapper managing all MCP clients — rejected per Simplicity First principle (YAGNI)

## R5: Deployment — update-agent-runtime Configuration Preservation

- **Decision**: When calling `update-agent-runtime`, explicitly pass ALL existing configuration including `authorizerConfiguration` (Cognito JWT), `networkConfiguration`, `protocolConfiguration`, `roleArn`, and environment variables
- **Rationale**: The `update-agent-runtime` API replaces the entire configuration — omitting any field resets it to defaults. This was identified as a critical risk: losing `authorizerConfiguration` would cause 403 errors for all users.
- **Alternatives considered**: Using CloudFormation to trigger the runtime update — rejected because CloudFormation doesn't detect changes when the ContainerUri `latest` tag doesn't change
