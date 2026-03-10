# Quickstart: Deploy Strands Agent to AgentCore

**Branch**: `004-agentcore-deploy` | **Date**: 2026-03-10

## Prerequisites

- AWS CLI configured (`aws configure`) with permissions to deploy CloudFormation, ECR, CodeBuild, IAM, and BedrockAgentCore
- Cognito User Pool already deployed (feature 002); have Pool ID and Client ID ready
- Docker installed locally (for local testing only — production build uses CodeBuild)
- `uv` or `pip` for Python dependency management

## Step 1: Install New Dependencies

```bash
cd /home/dhamijag/playground/strands-demo
uv add bedrock-agentcore requests
uv add --dev pytest-mock
```

Or with pip:
```bash
pip install bedrock-agentcore requests
```

## Step 2: Deploy the CloudFormation Stack

The stack provisions ECR, IAM roles, CodeBuild, and the AgentCore Runtime with Cognito JWT authorizer.

```bash
aws cloudformation deploy \
  --template-file infra/agentcore/template.yaml \
  --stack-name strands-demo-agentcore \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    CognitoUserPoolId=<your-pool-id> \
    CognitoClientId=<your-client-id> \
    CognitoRegion=<aws-region> \
    AnthropicApiKey=<your-anthropic-key> \
    TavilyApiKey=<your-tavily-key>
```

This will:
1. Create an ECR repository
2. Create a CodeBuild project configured for ARM64
3. Trigger a CodeBuild build via Lambda custom resource (builds and pushes the container image)
4. Create the AgentCore Runtime with Cognito JWT authorizer
5. Output the `AgentRuntimeArn` needed for Streamlit configuration

Stack deployment takes approximately 10–20 minutes (most time spent building the container image).

## Step 3: Configure Streamlit Environment

```bash
# Get the Runtime ARN from stack outputs
AGENT_ARN=$(aws cloudformation describe-stacks \
  --stack-name strands-demo-agentcore \
  --query 'Stacks[0].Outputs[?OutputKey==`AgentRuntimeArn`].OutputValue' \
  --output text)

# Add to .env file
echo "AGENTCORE_RUNTIME_ARN=${AGENT_ARN}" >> .env
echo "AWS_REGION=<your-region>" >> .env
```

## Step 4: Run the Streamlit App

```bash
streamlit run app.py
```

When `AGENTCORE_RUNTIME_ARN` is set in the environment, the app automatically routes agent invocations to AgentCore. When absent, it falls back to local execution.

## Step 5: Verify End-to-End

1. Open `http://localhost:8501`
2. Log in with a valid Cognito account
3. Send a chat message (e.g., "What is the capital of France?")
4. Verify streaming response appears token-by-token
5. Open AWS Console → CloudWatch → Application Signals / GenAI Observability dashboard
6. Verify a trace appears within 60 seconds showing the invocation lifecycle

## Step 6: Verify Observability

```bash
# Tail agent runtime logs
RUNTIME_ID=$(aws cloudformation describe-stacks \
  --stack-name strands-demo-agentcore \
  --query 'Stacks[0].Outputs[?OutputKey==`AgentRuntimeId`].OutputValue' \
  --output text)

aws logs tail /aws/bedrock-agentcore/runtimes/${RUNTIME_ID}-DEFAULT \
  --follow \
  --format short
```

## Step 7: Verify Auth Rejection

To verify unauthenticated access is blocked:

```bash
# Should return 401 Unauthorized
AGENT_ARN=<your-runtime-arn>
REGION=<your-region>
ESCAPED_ARN=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$AGENT_ARN', safe=''))")

curl -s -o /dev/null -w "%{http_code}" \
  -X POST \
  "https://bedrock-agentcore.${REGION}.amazonaws.com/runtimes/${ESCAPED_ARN}/invocations?qualifier=DEFAULT" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
# Expected output: 401
```

## Cleanup

```bash
aws cloudformation delete-stack --stack-name strands-demo-agentcore
# ECR images must be deleted manually before stack deletion succeeds
aws ecr batch-delete-image \
  --repository-name strands-demo-agent \
  --image-ids imageTag=latest
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Stack deployment stuck at CodeBuild stage | Build failure | Check `/aws/codebuild/strands-demo-agent-build` log group |
| `401 Unauthorized` from AgentCore in Streamlit | Expired Cognito token | Log out and log back in |
| `503` from AgentCore | Cold start / scaling | Retry after 10–30 seconds |
| No traces in CloudWatch | IAM permissions missing | Verify execution role has X-Ray and CloudWatch Logs permissions |
| Streaming not working | SSE not parsed | Check `AGENTCORE_RUNTIME_ARN` is set in `.env` |
