# Research: Enable AgentCore Observability

**Branch**: `006-agentcore-observability` | **Date**: 2026-03-10

## R1: CloudWatch Transaction Search Setup

**Decision**: Use CloudFormation (`AWS::XRay::TransactionSearchConfig` + `AWS::Logs::ResourcePolicy`) as primary approach. CLI fallback available.

**Rationale**: Transaction Search is an account-level feature that must be enabled once before any traces become searchable. CloudFormation now supports this via two resource types, aligning with the IaC-first constraint.

**CloudFormation approach** (preferred):
1. `AWS::Logs::ResourcePolicy` — grant X-Ray service permission to write spans to CloudWatch Logs (`aws/spans` + `/aws/application-signals/data` log groups).
2. `AWS::XRay::TransactionSearchConfig` — enable Transaction Search with `IndexingPercentage: 100`.

**CLI fallback** (if CFN resources not available in region):
1. `aws logs put-resource-policy` — grant X-Ray write access.
2. `aws xray update-trace-segment-destination --destination CloudWatchLogs` — route segments.
3. `aws xray update-indexing-rule --name "Default" --rule '{"Probabilistic": {"DesiredSamplingPercentage": 100}}'` — set sampling.

**Verify**: `aws xray get-trace-segment-destination` → `{"Destination": "CloudWatchLogs", "Status": "ACTIVE"}`

**Alternatives considered**: Manual Console toggle — rejected per constraint (no manual steps).

## R2: Runtime Tracing Enable

**Decision**: Use AWS CLI to enable tracing on the AgentCore Runtime resource.

**Rationale**: The `AWS::BedrockAgentCore::Runtime` CloudFormation resource type does not currently expose a `TracingEnabled` property. Tracing must be toggled via the AgentCore API or Console. Since no manual Console steps are allowed, we use the `bedrock-agent-core update-runtime` API or equivalent CLI.

**API approach**: The AgentCore Console has an "Edit → Tracing → Enable" toggle. The underlying API is `bedrock-agentcore:UpdateAgentRuntime` or equivalent. If no direct CLI exists, use `aws bedrock-agent-core` CLI or fall back to boto3 script.

**Alternatives considered**: CloudFormation custom resource to wrap the API call — rejected (Simplicity First; a one-time CLI command is simpler).

## R3: Log Delivery Configuration

**Decision**: Use CloudWatch Logs Vended Logs delivery APIs via AWS CLI/boto3.

**Rationale**: AgentCore log delivery (APPLICATION_LOGS, USAGE_LOGS) uses the CloudWatch Logs Vended Logs pattern:
1. `put-delivery-source` — register the Runtime/Identity ARN as a log source with the log type.
2. `create-delivery` — link the delivery source to a CloudWatch Logs destination (log group).

Log groups can be pre-created via CloudFormation. The delivery source/delivery link configuration is API-only.

**Log types**:
- `APPLICATION_LOGS` — request/response payloads, session IDs, trace IDs
- `USAGE_LOGS` — CPU/memory consumption at session granularity

**Alternatives considered**: CloudFormation `AWS::Logs::DeliverySource` / `AWS::Logs::Delivery` — these exist but are relatively new and may not support all AgentCore-specific log types. CLI approach is more reliable and documented in AgentCore guides.

## R4: Identity Observability

**Decision**: Enable tracing and log delivery for Identity (WorkloadIdentity) resources via the same APIs used for Runtime, but targeting the Identity resource ARN.

**Rationale**: Identity observability is configured at the Identity resource level (accessible via the Runtime's Identity tab in Console). The same `put-delivery-source` / `create-delivery` pattern applies. Identity tracing is toggled similarly to Runtime tracing.

**Identity metrics**: Automatically published to `Bedrock-AgentCore` CloudWatch namespace when tracing is enabled:
- `WorkloadAccessTokenFetchSuccess`
- `WorkloadAccessTokenFetchFailure`
- `WorkloadAccessTokenFetchThrottle`

## R5: Agent OTEL Instrumentation (Container Changes)

**Decision**: Add `strands-agents[otel]` to `requirements-agent.txt`. The `aws-opentelemetry-distro` and `opentelemetry-instrument` CMD are already in place.

**Rationale**: The existing Dockerfile already has:
- `aws-opentelemetry-distro>=0.10.1` in `requirements-agent.txt`
- `CMD ["opentelemetry-instrument", "python", "app.py"]` in Dockerfile

What's missing is `strands-agents[otel]` which provides the Strands-specific OTEL instrumentation (agent loop spans, LLM call spans, tool call spans). Without it, only generic Python/HTTP spans are emitted.

**Change required**: Replace `strands-agents>=0.1.0` with `strands-agents[otel]>=0.1.0` in `requirements-agent.txt`.

**Alternatives considered**: Manual OTEL instrumentation in app.py — rejected (auto-instrumentation via extras is simpler and matches the existing pattern).

## R6: IAM Permissions Assessment

**Decision**: Existing IAM permissions are sufficient. Minor expansion may be needed for OTEL-specific log groups.

**Rationale**: The `AgentExecutionRole` in `template.yaml` already has:
- `xray:PutTraceSegments`, `xray:PutTelemetryRecords`, `xray:GetSamplingRules`, `xray:GetSamplingTargets` (XRayTracing policy)
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`, `logs:DescribeLogGroups`, `logs:DescribeLogStreams` scoped to `/aws/bedrock-agentcore/runtimes/*` (CloudWatchLogs policy)
- `cloudwatch:PutMetricData` for `bedrock-agentcore` namespace (CloudWatchMetrics policy)

The CloudWatch Logs scope may need to be expanded if OTEL exporter writes to a different log group path (e.g., `/aws/spans` or a custom group). However, the `aws-opentelemetry-distro` typically exports via X-Ray protocol (using the existing X-Ray permissions), not directly to CloudWatch Logs. The service-side writes spans to `aws/spans`.

**Potential expansion**: Add `logs:PutLogEvents` permission for the `aws/spans` log group if the OTEL exporter writes directly. In practice, the X-Ray service handles this server-side, so no change is likely needed.

## R7: CloudFormation vs CLI Boundary

**Decision**: CloudFormation for IAM and log group pre-creation; CLI for everything else.

**What goes in CloudFormation (`template.yaml`)**:
- IAM policy updates (if needed)
- CloudWatch Log Group pre-creation for observability log groups
- Container dependency update (`strands-agents[otel]`) — triggers CodeBuild rebuild

**What goes in CLI scripts (documented in `quickstart.md`)**:
- CloudWatch Transaction Search one-time setup (3 commands)
- Runtime tracing enable
- Runtime log delivery configuration (put-delivery-source + create-delivery for APPLICATION_LOGS and USAGE_LOGS)
- Identity tracing enable
- Identity log delivery configuration
