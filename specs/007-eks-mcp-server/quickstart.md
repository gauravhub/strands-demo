# Quickstart: EKS MCP Server Integration

**Branch**: `007-eks-mcp-server` | **Date**: 2026-03-14

## Prerequisites

- Python 3.11+
- AWS credentials configured (CLI or environment variables)
- EKS clusters in your AWS account (for testing)
- Existing `.env` file with Cognito + Anthropic + Tavily keys configured

## Setup

### 1. Install Dependencies

```bash
pip install -e ".[dev]"
```

This installs `mcp-proxy-for-aws` alongside existing dependencies.

### 2. Configure Environment

Add to your `.env` file:

```env
# EKS MCP Server region (optional — auto-detects from AWS_REGION if not set)
# EKS_MCP_REGION=us-west-2
```

### 3. Run Locally

```bash
streamlit run app.py
```

The agent now has EKS tools available alongside web search. Try asking:
- "What EKS clusters do I have?"
- "Describe my cluster named X"
- "Show me recent events in cluster Y"

### 4. Deploy to AgentCore

Update the CloudFormation stack to grant EKS MCP permissions:

```bash
aws cloudformation update-stack \
  --stack-name strands-demo-agentcore \
  --template-body file://infra/agentcore/template.yaml \
  --parameters \
    ParameterKey=CognitoUserPoolId,UsePreviousValue=true \
    ParameterKey=CognitoClientId,UsePreviousValue=true \
    ParameterKey=CognitoRegion,UsePreviousValue=true \
    ParameterKey=AnthropicApiKey,UsePreviousValue=true \
    ParameterKey=TavilyApiKey,UsePreviousValue=true \
    ParameterKey=BuildSourceBucket,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM
```

## Validation

### Local Mode

1. Start the app: `streamlit run app.py`
2. Log in via Cognito
3. Ask: "List my EKS clusters"
4. Verify: Agent returns cluster names and status from your AWS account

### AgentCore Mode

1. Deploy updated CloudFormation stack
2. Rebuild and push container image
3. Set `AGENTCORE_RUNTIME_ARN` in `.env`
4. Start the app and ask about EKS clusters
5. Verify: Same results as local mode, served via AgentCore Runtime

### Error Handling

1. Remove AWS credentials and ask about EKS clusters
2. Verify: Agent shows a user-friendly error, not a stack trace
3. Verify: Agent still responds to non-EKS questions (Tavily search works)
