# Quickstart: Enable AgentCore Observability

**Branch**: `006-agentcore-observability` | **Date**: 2026-03-10

## Prerequisites

- AWS CLI v2 installed and configured with appropriate permissions
- AgentCore Runtime `strands_demo_agent` deployed (feature 004)
- Cognito JWT authorizer configured (feature 002)
- Know your: `RUNTIME_ARN`, `RUNTIME_ID`, `IDENTITY_ARN`, `AWS_REGION`, `AWS_ACCOUNT_ID`

### Caller IAM Permissions for Log Delivery Setup

The IAM user/role running these commands needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LogDeliveryActions",
      "Effect": "Allow",
      "Action": [
        "logs:GetDelivery", "logs:GetDeliverySource",
        "logs:PutDeliveryDestination", "logs:PutDeliverySource",
        "logs:CreateDelivery", "logs:DeleteDelivery",
        "logs:GetDeliveryDestination", "logs:DeleteDeliverySource",
        "logs:DeleteDeliveryDestination", "logs:UpdateDeliveryConfiguration"
      ],
      "Resource": [
        "arn:aws:logs:*:*:delivery:*",
        "arn:aws:logs:*:*:delivery-source:*",
        "arn:aws:logs:*:*:delivery-destination:*"
      ]
    },
    {
      "Sid": "LogDeliveryListActions",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeDeliveryDestinations",
        "logs:DescribeDeliverySources",
        "logs:DescribeDeliveries",
        "logs:DescribeConfigurationTemplates"
      ],
      "Resource": "*"
    },
    {
      "Sid": "XRayTransactionSearch",
      "Effect": "Allow",
      "Action": [
        "xray:PutResourcePolicy", "xray:ListResourcePolicies",
        "xray:GetTraceSegmentDestination",
        "xray:UpdateTraceSegmentDestination",
        "xray:UpdateIndexingRule"
      ],
      "Resource": "*"
    }
  ]
}
```

## Step 1: Update CloudFormation Stack (Log Groups) + Verify Transaction Search

The CFN stack update handles:
- CloudWatch Log Group pre-creation for observability (Runtime app/usage logs, Identity app logs)
- Log group ARN outputs for use in delivery configuration

**Note**: Transaction Search (`AWS::Logs::ResourcePolicy` + `AWS::XRay::TransactionSearchConfig`) is an account-level singleton. If already enabled via CLI (see fallback below), the CFN resources are not needed. The current template omits them to avoid `AlreadyExists` errors. Verify with `aws xray get-trace-segment-destination`.

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
    ParameterKey=BuildSourceKey,UsePreviousValue=true \
    ParameterKey=ImageTag,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for stack update to complete
aws cloudformation wait stack-update-complete --stack-name strands-demo-agentcore
```

### Transaction Search CLI Fallback

If `AWS::XRay::TransactionSearchConfig` is not yet available in your region, use these CLI commands instead:

```bash
# 1a. Grant X-Ray service permission to write spans to CloudWatch Logs
aws logs put-resource-policy \
  --policy-name TransactionSearchXRayAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "TransactionSearchXRayAccess",
      "Effect": "Allow",
      "Principal": {"Service": "xray.amazonaws.com"},
      "Action": "logs:PutLogEvents",
      "Resource": [
        "arn:aws:logs:'${AWS_REGION}':'${AWS_ACCOUNT_ID}':log-group:aws/spans:*",
        "arn:aws:logs:'${AWS_REGION}':'${AWS_ACCOUNT_ID}':log-group:/aws/application-signals/data:*"
      ],
      "Condition": {
        "ArnLike": {"aws:SourceArn": "arn:aws:xray:'${AWS_REGION}':'${AWS_ACCOUNT_ID}':*"},
        "StringEquals": {"aws:SourceAccount": "'${AWS_ACCOUNT_ID}'"}
      }
    }]
  }'

# 1b. Route trace segments to CloudWatch Logs
aws xray update-trace-segment-destination --destination CloudWatchLogs

# 1c. Set 100% sampling (demo project — full visibility)
aws xray update-indexing-rule --name "Default" \
  --rule '{"Probabilistic": {"DesiredSamplingPercentage": 100}}'

# Verify
aws xray get-trace-segment-destination
# Expected: {"Destination": "CloudWatchLogs", "Status": "ACTIVE"}
```

## Step 2: Enable Runtime Tracing

Runtime tracing is enabled by configuring a TRACES delivery via the vended logs pattern (Step 3g-3i below). There is no separate "enable tracing" API toggle — creating a TRACES delivery source and linking it to an XRAY destination activates tracing.

> **Note**: The `bedrock-agentcore-control update-agent-runtime` API does not currently expose a tracing configuration flag. The Console toggle (AgentCore → Runtime → Edit → Tracing → Enable) uses the same vended logs delivery pattern under the hood.

## Step 3: Configure Runtime Log Delivery

Uses the CloudWatch Logs Vended Logs 3-step pattern: source → destination → delivery.

```bash
# 3a. Register Runtime as a delivery source for APPLICATION_LOGS
aws logs put-delivery-source \
  --name "strands-demo-runtime-app-logs" \
  --resource-arn ${RUNTIME_ARN} \
  --log-type APPLICATION_LOGS

# 3b. Register destination (CloudWatch Logs group)
aws logs put-delivery-destination \
  --name "strands-demo-runtime-app-logs-dest" \
  --delivery-destination-type CWL \
  --delivery-destination-configuration \
    "destinationResourceArn=arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:log-group:/aws/vendedlogs/bedrock-agentcore/runtimes/${RUNTIME_ID}/application-logs"

# 3c. Create delivery (link source to destination)
aws logs create-delivery \
  --delivery-source-name "strands-demo-runtime-app-logs" \
  --delivery-destination-arn "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:delivery-destination:strands-demo-runtime-app-logs-dest"

# 3d. Register Runtime for USAGE_LOGS
aws logs put-delivery-source \
  --name "strands-demo-runtime-usage-logs" \
  --resource-arn ${RUNTIME_ARN} \
  --log-type USAGE_LOGS

# 3e. Register usage logs destination
aws logs put-delivery-destination \
  --name "strands-demo-runtime-usage-logs-dest" \
  --delivery-destination-type CWL \
  --delivery-destination-configuration \
    "destinationResourceArn=arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:log-group:/aws/vendedlogs/bedrock-agentcore/runtimes/${RUNTIME_ID}/usage-logs"

# 3f. Create usage logs delivery
aws logs create-delivery \
  --delivery-source-name "strands-demo-runtime-usage-logs" \
  --delivery-destination-arn "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:delivery-destination:strands-demo-runtime-usage-logs-dest"

# 3g. Register Runtime for TRACES (X-Ray destination)
aws logs put-delivery-source \
  --name "strands-demo-runtime-traces" \
  --resource-arn ${RUNTIME_ARN} \
  --log-type TRACES

# 3h. Register traces destination (X-Ray)
aws logs put-delivery-destination \
  --name "strands-demo-runtime-traces-dest" \
  --delivery-destination-type XRAY

# 3i. Create traces delivery
aws logs create-delivery \
  --delivery-source-name "strands-demo-runtime-traces" \
  --delivery-destination-arn "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:delivery-destination:strands-demo-runtime-traces-dest"
```

## Step 4: Enable Identity Tracing and Log Delivery

```bash
# 4a. Enable tracing on the Identity (WorkloadIdentity) resource
# Identity tracing is enabled by configuring a TRACES delivery for the Identity ARN
aws logs put-delivery-source \
  --name "strands-demo-identity-traces" \
  --resource-arn ${IDENTITY_ARN} \
  --log-type TRACES

aws logs put-delivery-destination \
  --name "strands-demo-identity-traces-dest" \
  --delivery-destination-type XRAY

aws logs create-delivery \
  --delivery-source-name "strands-demo-identity-traces" \
  --delivery-destination-arn "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:delivery-destination:strands-demo-identity-traces-dest"

# 4b. Register Identity as a delivery source for APPLICATION_LOGS
aws logs put-delivery-source \
  --name "strands-demo-identity-app-logs" \
  --resource-arn ${IDENTITY_ARN} \
  --log-type APPLICATION_LOGS

# 4c. Register Identity logs destination
aws logs put-delivery-destination \
  --name "strands-demo-identity-app-logs-dest" \
  --delivery-destination-type CWL \
  --delivery-destination-configuration \
    "destinationResourceArn=arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:log-group:/aws/vendedlogs/bedrock-agentcore/identity/application-logs"

# 4d. Create Identity logs delivery
aws logs create-delivery \
  --delivery-source-name "strands-demo-identity-app-logs" \
  --delivery-destination-arn "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:delivery-destination:strands-demo-identity-app-logs-dest"
```

## Step 5: Rebuild Container with OTEL (strands-agents[otel])

```bash
# Upload updated source (with modified requirements-agent.txt)
zip -r source.zip . --exclude '.venv/*' 'specs/*' '.git/*'
aws s3 cp source.zip s3://${BUILD_SOURCE_BUCKET}/source.zip

# Trigger CodeBuild to rebuild the container image
aws codebuild start-build --project-name strands-demo-agent-build

# Wait for build to complete
aws codebuild batch-get-builds --ids <build-id> | jq '.builds[0].buildStatus'

# The Runtime picks up the new :latest image on next invocation
```

## Step 6: Smoke Test

```bash
# Invoke the agent to generate traces and logs
# Use the Streamlit app or direct AgentCore API invocation

# Then verify in CloudWatch:
# 1. CloudWatch → Transaction Search → search for traces from strands_demo_agent
# 2. CloudWatch → GenAI Observability → Agents View → verify strands_demo_agent appears
# 3. CloudWatch → Log Groups → check application and usage log groups
# 4. CloudWatch → Metrics → Bedrock-AgentCore namespace → Identity metrics
```

## Troubleshooting

- **No traces visible**: Ensure Transaction Search is enabled (Step 1) AND Runtime tracing is enabled (Step 2). Both are required. Verify with `aws xray get-trace-segment-destination`.
- **No application logs**: Verify log delivery source, destination, and delivery are all created (Step 3). Check the log group exists. Use `aws logs describe-deliveries` to verify.
- **No Strands-specific spans**: Ensure `strands-agents[otel]` is in the container (Step 5). Generic OTEL spans come from `aws-opentelemetry-distro`; Strands-specific spans require the `[otel]` extra.
- **IAM permission errors**: Check the execution role has X-Ray and CloudWatch Logs permissions (already in template.yaml). For log delivery setup, the caller needs the permissions listed in Prerequisites.
- **Identity tracing not showing**: Identity observability is configured at the associated resource level. Ensure tracing is enabled via the Runtime's Identity tab or equivalent API call (Step 4a).
