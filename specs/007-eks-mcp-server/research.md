# Research: EKS MCP Server Integration

**Branch**: `007-eks-mcp-server` | **Date**: 2026-03-14

## R1: EKS MCP Server Connection Method

**Decision**: Use `mcp-proxy-for-aws` library mode with `aws_iam_streamablehttp_client`

**Rationale**: The fully managed EKS MCP Server (preview) requires SigV4-authenticated HTTP connections. The `mcp-proxy-for-aws` package provides a single-function API (`aws_iam_streamablehttp_client`) that handles SigV4 signing transparently. Strands SDK already includes `MCPClient` which accepts a client factory — the two compose naturally.

**Alternatives considered**:
- Open-source `awslabs.eks-mcp-server` (local stdio): Requires local installation, no managed infrastructure. Rejected — the managed service is preferred for AgentCore deployment.
- Direct HTTP + manual SigV4 signing: Too complex, error-prone. The proxy library exists for this purpose.

## R2: EKS MCP Server Endpoint Pattern

**Decision**: Endpoint URL: `https://eks-mcp.{region}.api.aws/mcp`

**Rationale**: This is the documented endpoint pattern for the AWS-managed EKS MCP Server. The service name for SigV4 signing is `eks-mcp`.

**Alternatives considered**: None — this is the only documented endpoint.

## R3: IAM Permissions for EKS MCP Server

**Decision**: Add three permission sets to `AgentExecutionRole`:
1. EKS MCP service actions: `eks-mcp:InvokeMcp`, `eks-mcp:CallReadOnlyTool`
2. Underlying EKS read actions: `eks:DescribeCluster`, `eks:ListClusters`, `eks:ListNodegroups`, `eks:DescribeNodegroup`, `eks:ListAddons`, `eks:DescribeAddon`, `eks:ListAccessEntries`, `eks:DescribeAccessEntry`, `eks:AccessKubernetesApi`, `eks:DescribeInsight`, `eks:ListInsights`
3. Supporting read actions: `logs:StartQuery`, `logs:GetQueryResults`, `cloudwatch:GetMetricData`, `sts:GetCallerIdentity`, `iam:GetRole`, `iam:ListAttachedRolePolicies`, `iam:ListRolePolicies`, `iam:GetRolePolicy`

**Rationale**: Least-privilege. Only read-only MCP actions and the underlying AWS actions those tools actually invoke. No write tools (`eks-mcp:CallPrivilegedTool`) are granted.

**Alternatives considered**:
- AWS managed policy `AmazonEKSMCPReadOnlyAccess`: Convenient but may be too broad or too narrow for our needs. Custom inline policy is more explicit and auditable.

## R4: Strands MCPClient Integration Pattern

**Decision**: Use the Strands `MCPClient` with a lambda factory pattern:

```python
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

mcp_factory = lambda: aws_iam_streamablehttp_client(
    endpoint=f"https://eks-mcp.{region}.api.aws/mcp",
    aws_region=region,
    aws_service="eks-mcp"
)

with MCPClient(mcp_factory) as client:
    tools = client.list_tools_sync()
    agent = Agent(tools=[tavily, *tools])
```

**Rationale**: This is the documented pattern for Strands + mcp-proxy-for-aws. MCPClient manages connection lifecycle. Tools are merged with existing Tavily tool.

**Alternatives considered**:
- Direct `ClientSession` usage: More verbose, less idiomatic for Strands. Rejected.

## R5: Region Auto-Detection

**Decision**: Resolve region in order: `EKS_MCP_REGION` env var → `AWS_REGION` env var → `AWS_DEFAULT_REGION` env var.

**Rationale**: Per clarification, auto-detect from deployment region. `AWS_REGION` is already required when `AGENTCORE_RUNTIME_ARN` is set (see `config.py`). Explicit override via `EKS_MCP_REGION` allows cross-region queries.

**Alternatives considered**: Parse region from `AGENTCORE_RUNTIME_ARN` — possible but fragile and doesn't help in local mode.

## R6: OTEL Observability

**Decision**: Rely on existing Strands SDK MCP instrumentation (`strands.tools.mcp.mcp_instrumentation`). No custom instrumentation code needed.

**Rationale**: The Strands SDK already instruments MCP tool calls with OTEL spans. Since feature 006 set up the OTEL pipeline and the container runs with `opentelemetry-instrument`, MCP tool calls will automatically appear in traces.

**Alternatives considered**: Custom span creation around MCP calls — unnecessary, SDK handles it.
