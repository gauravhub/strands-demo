# Implementation Plan: AWS API MCP Server Integration

**Branch**: `008-aws-api-mcp-server` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-aws-api-mcp-server/spec.md`

## Summary

Integrate the AWS-managed AWS API MCP Server into the existing Strands Agent, enabling users to query AWS resources (S3, Lambda, IAM, etc.) via natural language chat. The integration follows the identical pattern already established for EKS MCP Server: `mcp-proxy-for-aws` in library mode with SigV4 authentication, `MCPClient` factory lambda, `list_tools_sync()` for tool discovery, and tool list merging in the Agent constructor. CloudFormation updates add the required IAM permissions. Deployment includes S3 source upload, CodeBuild image rebuild, CloudFormation stack update, and an explicit `update-agent-runtime` call to force the container restart while preserving all existing configuration (including Cognito JWT authorizer).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: strands-agents>=0.1.0, strands-agents-tools>=0.1.0, mcp-proxy-for-aws>=1.0.0, bedrock-agentcore>=0.1.0, anthropic>=0.40.0, boto3
**Storage**: N/A — stateless, no persistent data
**Testing**: pytest
**Target Platform**: AWS AgentCore Runtime (ARM64 container) + Streamlit Cloud (local mode)
**Project Type**: Web service (Streamlit frontend + AgentCore backend)
**Performance Goals**: AWS API MCP tool responses within 15 seconds
**Constraints**: Must preserve existing EKS MCP + Tavily tools; must not break existing auth config during deployment
**Scale/Scope**: Single agent with 3 MCP tool sets (Tavily, EKS MCP, AWS API MCP)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | PASS | Follows identical pattern to existing EKS MCP integration — no new abstractions, no speculative features |
| II. Iterative & Independent Delivery | PASS | Feature is a standalone vertical slice: new MCP tool loader + CloudFormation IAM + deployment. Agent remains functional with or without AWS API MCP tools |
| III. Python-Native Patterns | PASS | All code is Python 3.11+, dependencies declared in requirements-agent.txt |
| IV. Security by Design | PASS | IAM permissions managed via CloudFormation (least-privilege), SigV4 auth for MCP endpoint, Cognito JWT preserved during deployment |
| V. Observability & Debuggability | PASS | MCP tool calls automatically traced via existing OTEL instrumentation; structured logging for connection status |

## Project Structure

### Documentation (this feature)

```text
specs/008-aws-api-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── tasks.md             # Phase 2 output (created by /speckit.tasks)
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
src/
├── agent/
│   ├── mcp_tools.py          # MODIFY: Add get_aws_api_mcp_tools()
│   ├── chatbot.py             # MODIFY: Import and merge AWS API MCP tools
│   └── model.py               # NO CHANGE
├── agentcore/
│   ├── app.py                 # MODIFY: Import and merge AWS API MCP tools
│   └── config.py              # NO CHANGE
├── auth/                      # NO CHANGE
└── chat/
    └── ui.py                  # NO CHANGE

infra/agentcore/
├── template.yaml              # MODIFY: Add AwsApiMcpAccess IAM policy + AWS_API_MCP_REGION env var
├── Dockerfile                 # NO CHANGE
└── requirements-agent.txt     # NO CHANGE (mcp-proxy-for-aws already present)
```

**Structure Decision**: Extend existing files in-place. No new files or directories needed — the AWS API MCP integration slots into the exact same locations as EKS MCP.

## Architecture

### Integration Pattern

The AWS API MCP Server integration is a direct mirror of the existing EKS MCP Server integration:

1. **Tool Loader** (`src/agent/mcp_tools.py`): New `get_aws_api_mcp_tools()` function that:
   - Resolves region via `AWS_API_MCP_REGION` → `AWS_REGION` → `AWS_DEFAULT_REGION`
   - Constructs endpoint `https://aws-api.{region}.api.aws/mcp`
   - Creates SigV4-authenticated client via `aws_iam_streamablehttp_client(aws_service="aws-api")`
   - Wraps in `MCPClient`, calls `list_tools_sync()`, returns `(client, tools)`
   - Graceful degradation on failure: returns `(None, [])`

2. **Agent Factory** (`src/agent/chatbot.py` and `src/agentcore/app.py`): Merge AWS API MCP tools into the existing tool list:
   - `tools = [tavily, *eks_tools, *aws_api_tools]`
   - Track both MCP clients for cleanup

3. **CloudFormation** (`infra/agentcore/template.yaml`):
   - New `AwsApiMcpAccess` IAM policy on `AgentExecutionRole` with `aws-api:InvokeMcp` permission
   - New `AWS_API_MCP_REGION` environment variable on `AgentRuntime`
   - New `AwsApiMcpRegion` parameter (same pattern as `EksMcpRegion`)

4. **Deployment**: Standard pipeline + explicit runtime restart:
   - Upload source zip to S3
   - Trigger CodeBuild to rebuild container image
   - Update CloudFormation stack
   - Call `update-agent-runtime` with ALL existing config preserved (including `authorizerConfiguration`)

### Data Flow

```
User Chat → Streamlit → Agent(tools=[tavily, *eks_tools, *aws_api_tools])
                                         ↓               ↓
                                    EKS MCP Server   AWS API MCP Server
                                    (eks-mcp SigV4)  (aws-api SigV4)
                                    eks-mcp.{r}.api  aws-api.{r}.api
                                        .aws/mcp         .aws/mcp
```

### MCP Client Lifecycle

Both MCP clients (EKS and AWS API) follow the same lifecycle:
- Created before agent invocation (outside async generator in AgentCore mode)
- Passed to Agent constructor as merged tool list
- Cleaned up in `finally` block after invocation completes

## Complexity Tracking

No constitution violations. No complexity justifications needed.
