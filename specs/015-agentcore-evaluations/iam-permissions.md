# IAM Permissions: AgentCore Evaluations

## Overview

The evaluation execution role is **auto-created** by the `agentcore eval online create` CLI command. It is a **separate role** from the agent's runtime execution role (`AgentExecutionRole` defined in `infra/agentcore/template.yaml`). The CLI provisions the role, attaches the necessary policies, and associates it with the evaluation configuration automatically.

## Role Naming

```
AgentCoreEvalsSDK-{region}-{hash}
```

- `{region}` is the AWS region (e.g., `us-west-2`)
- `{hash}` is a deterministic value derived from the agent name

## Trust Policy

The role trusts the `bedrock-agentcore.amazonaws.com` service principal:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Required Permissions

All permissions below are auto-provisioned by the CLI when the evaluation configuration is created.

### CloudWatch Logs -- Read (Observability Data)

Access to read agent observability log groups used as evaluation data sources:

- `logs:GetLogEvents`
- `logs:DescribeLogGroups`
- `logs:DescribeLogStreams`

### Bedrock Model Invoke (LLM-as-a-Judge)

Permissions to invoke foundation models for LLM-as-a-judge evaluation:

- `bedrock:InvokeModel`
- `bedrock:InvokeModelWithResponseStream`

### CloudWatch Logs -- Write (Evaluation Results)

Write access to the evaluation results log group:

- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

Target log group pattern:

```
/aws/bedrock-agentcore/evaluations/results/{config-id}
```

## CloudFormation Impact

**No changes needed** to `infra/agentcore/template.yaml`. The evaluation role is fully managed by the CLI, not by CloudFormation. The existing `AgentExecutionRole` in the stack already has `AdministratorAccess` for runtime operations and is unrelated to the evaluation role.

## Deployed Role Details

- **Role Name**: `AgentCoreEvalsSDK-us-east-1-70d2f5e255`
- **Role ARN**: `arn:aws:iam::829040135710:role/AgentCoreEvalsSDK-us-east-1-70d2f5e255`
- **Inline Policy**: `AgentCoreEvaluationPolicy-us-east-1-70d2f5e255`
- **Attached Managed Policies**: None
- **Created By**: `agentcore eval online create` CLI (auto-created during T005)
- **Associated Config**: `strands_demo_eval-aRaiodB5tF`
