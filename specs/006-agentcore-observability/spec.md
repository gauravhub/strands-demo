# Feature Specification: Enable AgentCore Observability

**Feature Branch**: `006-agentcore-observability`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Enable comprehensive AgentCore observability — OTEL tracing for agents, CloudWatch logs and tracing for Runtime and Identity primitives"

## Scope & Architecture Boundary

**In scope:**
- Enabling CloudWatch Transaction Search (one-time account setup) for trace/span ingestion
- Enabling tracing on the AgentCore Runtime resource (currently disabled in AWS Console)
- Enabling application log delivery for the AgentCore Runtime resource to CloudWatch Logs
- Enabling tracing on Identity (WorkloadIdentity) resources associated with the Runtime
- Enabling application log delivery for Identity resources to CloudWatch Logs
- Adding `strands-agents[otel]` and `aws-opentelemetry-distro` to the agent container so the Strands agent emits OTEL traces
- Updating the agent's entrypoint to run under `opentelemetry-instrument` for automatic instrumentation
- Updating the IAM execution role to permit OTEL-related CloudWatch and X-Ray actions
- Validating that traces, spans, and metrics appear in the CloudWatch GenAI Observability dashboard

**Out of scope:**
- Memory, Gateway, or Built-in Tools observability (project does not use these primitives)
- Third-party observability platforms (Dynatrace, Datadog, etc.)
- Custom CloudWatch dashboards or alarms (can be added later)
- Changes to the Streamlit frontend — this feature is backend/infrastructure only

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Runtime Traces Visible in CloudWatch (Priority: P1)

A developer enables tracing on the AgentCore Runtime so that every agent invocation produces traces and spans visible in the CloudWatch GenAI Observability dashboard, including runtime metrics (invocations, latency, errors, token usage).

**Why this priority**: Without tracing enabled, the developer has zero visibility into agent execution in production. This is the foundational observability capability.

**Independent Test**: Invoke the agent on the deployed Runtime, then open CloudWatch GenAI Observability → Agents View and confirm the agent appears with traces, spans showing the full execution path (LLM call, tool calls, response), and runtime metrics (invocations, latency).

**Acceptance Scenarios**:

1. **Given** CloudWatch Transaction Search is enabled and tracing is turned on for the Runtime, **When** a user sends a chat message through the deployed app, **Then** a trace appears in CloudWatch Transaction Search within 5 minutes containing spans for the agent invocation.
2. **Given** tracing is enabled, **When** the developer opens the CloudWatch GenAI Observability Agents View, **Then** the `strands_demo_agent` is listed with runtime metrics (invocations, latency, errors, session count).
3. **Given** OTEL instrumentation is active in the agent container, **When** the agent executes a tool call (e.g., Tavily web search), **Then** the trace includes child spans for the tool invocation with timing data.

---

### User Story 2 — Runtime Application Logs in CloudWatch (Priority: P2)

A developer configures application log delivery for the AgentCore Runtime so that structured logs (request/response payloads, session IDs, trace IDs) are stored in a CloudWatch Logs group for debugging and audit.

**Why this priority**: Traces show execution flow but logs provide the detailed payloads needed for debugging specific issues. Together with traces, logs complete the observability picture for the Runtime.

**Independent Test**: Invoke the agent, then check CloudWatch Logs for the Runtime log group and confirm structured log records are present with request payload, response payload, session ID, and trace ID.

**Acceptance Scenarios**:

1. **Given** application log delivery is configured for the Runtime, **When** a user invokes the agent, **Then** a structured log record appears in the configured CloudWatch Logs group containing the request payload, response payload, and trace/span IDs.
2. **Given** log delivery is active, **When** the developer searches the log group by session ID, **Then** all log records for that session are returned.
3. **Given** usage log delivery is enabled, **When** the agent processes requests, **Then** resource usage logs (CPU, memory) appear at session-level granularity.

---

### User Story 3 — Identity Observability Enabled (Priority: P3)

A developer enables tracing and log delivery for the Identity (WorkloadIdentity) resources associated with the Runtime so that authentication/authorization operations are visible in CloudWatch — including token fetch success/failure rates and latency.

**Why this priority**: Identity observability is critical for diagnosing authentication failures (e.g., expired tokens, misconfigured Cognito JWT authorizer) but is lower priority because it builds on top of Runtime observability.

**Independent Test**: Invoke the agent with a valid Cognito JWT, then check CloudWatch for Identity spans showing the JWT authorization operation with success status. Also verify Identity metrics (WorkloadAccessTokenFetchSuccess) appear in CloudWatch Metrics.

**Acceptance Scenarios**:

1. **Given** Identity tracing is enabled on the Runtime's Identity tab, **When** a user authenticates and invokes the agent, **Then** Identity spans appear in the `aws/spans` log group showing the authorization operation.
2. **Given** Identity log delivery is configured, **When** authentication operations occur, **Then** structured application logs for Identity appear in the configured CloudWatch Logs group with operation, request ID, and trace ID.
3. **Given** Identity observability is active, **When** the developer checks CloudWatch Metrics under the Bedrock-AgentCore namespace, **Then** Identity authorization metrics (success, failure, throttle counts) are present.

---

### User Story 4 — Agent OTEL Instrumentation in Container (Priority: P4)

A developer adds OpenTelemetry instrumentation to the agent container image so that the Strands agent emits detailed OTEL traces (LLM interactions, tool calls, token usage) that appear in the CloudWatch GenAI Observability dashboard alongside the Runtime-level traces.

**Why this priority**: This provides the deepest visibility into agent internals (individual LLM calls, tool invocations, reasoning steps) but requires container image changes. The Runtime-level traces (US1) already provide invocation-level visibility without code changes.

**Independent Test**: After deploying the updated container with OTEL instrumentation, invoke the agent and verify that CloudWatch shows detailed Strands-level spans (agent loop iterations, model calls, tool calls) nested under the Runtime invocation span.

**Acceptance Scenarios**:

1. **Given** the agent container includes `strands-agents[otel]` and `aws-opentelemetry-distro`, **When** the agent processes a request, **Then** OTEL traces are emitted containing Strands-specific spans (agent invocation, LLM call, tool call).
2. **Given** the container entrypoint uses `opentelemetry-instrument`, **When** the agent runs on AgentCore Runtime, **Then** traces are automatically exported to CloudWatch without additional code changes in agent logic.
3. **Given** OTEL instrumentation is active, **When** a session ID is set via OpenTelemetry baggage, **Then** all spans within that session are correlated and visible in the CloudWatch Sessions View.

---

### Edge Cases

- What happens if CloudWatch Transaction Search is already enabled in the account? (The setup step is idempotent — no error, no duplicate configuration.)
- What if the IAM execution role lacks X-Ray or CloudWatch Logs permissions? (Traces silently fail to export. The role must be updated before enabling tracing.)
- What if the agent container does not include OTEL dependencies? (Runtime-level metrics and service-provided spans still work; only agent-internal OTEL traces are missing.)
- What happens if tracing is enabled but Transaction Search is not? (Spans are generated but not searchable/visible in CloudWatch Transaction Search. The one-time setup must be done first.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: CloudWatch Transaction Search MUST be enabled in the AWS account (one-time setup) with 100% trace sampling to ingest and display all OTEL spans and traces.
- **FR-002**: Tracing MUST be enabled on the AgentCore Runtime resource so that runtime-level spans are written to the `aws/spans` CloudWatch Logs group.
- **FR-003**: Application log delivery MUST be configured for the AgentCore Runtime resource, directing structured logs to a CloudWatch Logs group.
- **FR-004**: Usage log delivery MUST be enabled for the Runtime to capture session-level resource consumption (CPU, memory) in CloudWatch Logs.
- **FR-005**: Tracing MUST be enabled on the Identity (WorkloadIdentity) resources associated with the Runtime, via the Runtime's Identity tab.
- **FR-006**: Application log delivery MUST be configured for Identity resources associated with the Runtime, directing logs to a CloudWatch Logs group.
- **FR-007**: The agent container image MUST include `strands-agents[otel]` and `aws-opentelemetry-distro` dependencies so the Strands agent emits OTEL-compatible traces.
- **FR-008**: The agent container entrypoint MUST use `opentelemetry-instrument` to auto-instrument the agent code for OTEL trace export.
- **FR-009**: The IAM execution role for the AgentCore Runtime MUST have permissions for X-Ray trace submission (`xray:PutTraceSegments`, `xray:PutTelemetryRecords`) and CloudWatch Logs write access for observability log groups.
- **FR-010**: The existing agent functionality (Cognito auth, AgentCore chat routing, tool calls) MUST continue to work identically after enabling observability — no behavioral regressions.

### Key Entities

- **AgentCore Runtime Resource**: The deployed agent runtime (`strands_demo_agent`) — receives tracing and log delivery configuration.
- **Identity (WorkloadIdentity) Resource**: The authentication/authorization layer associated with the Runtime's JWT authorizer — receives tracing and log delivery configuration.
- **CloudWatch Transaction Search**: Account-level feature that ingests OTEL spans into structured logs for search and visualization.
- **CloudWatch GenAI Observability Dashboard**: The CloudWatch console page that displays agent traces, sessions, and metrics.
- **OTEL Instrumentation**: The OpenTelemetry auto-instrumentation layer added to the agent container for framework-level tracing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After enabling all observability features, 100% of agent invocations produce visible traces in CloudWatch Transaction Search within 5 minutes.
- **SC-002**: The CloudWatch GenAI Observability Agents View lists the `strands_demo_agent` with runtime metrics (invocations, latency, errors, session count).
- **SC-003**: Structured application logs for both Runtime and Identity operations are present in their respective CloudWatch Logs groups after an agent invocation.
- **SC-004**: Identity authorization metrics (success/failure/throttle counts) appear in the CloudWatch Metrics Bedrock-AgentCore namespace.
- **SC-005**: Agent-level OTEL traces include Strands-specific spans (agent loop, LLM call, tool call) visible in CloudWatch trace details.
- **SC-006**: All existing functionality (Cognito login, chat, AgentCore routing) continues to work without regression after observability is enabled.

## Clarifications

### Session 2026-03-10

- Q: Should observability be enabled via Console, CLI, CloudFormation, or a mix? → A: CloudFormation first (IAM permissions, container config, log groups), AWS CLI for features that are API-only toggles (Transaction Search, tracing enable, log delivery). No manual Console steps.
- Q: What Transaction Search sampling percentage should be configured? → A: 100% — every trace indexed. Demo project with low traffic; cost negligible. Ensures full visibility during development and smoke testing.

## Assumptions

- The AWS account has not yet enabled CloudWatch Transaction Search (the one-time setup will be performed as part of this feature).
- The AgentCore Runtime resource `strands_demo_agent` is already deployed and operational (feature 004).
- The existing IAM execution role already has basic CloudWatch Logs and X-Ray permissions (confirmed in the CloudFormation template) but may need expansion for OTEL-specific log groups.
- The Strands agents SDK supports OTEL via the `strands-agents[otel]` extra dependency.
- Enabling observability features via the AWS Console or CLI does not require redeployment of the agent Runtime — it takes effect on subsequent invocations.
- The OTEL container image changes require a new CodeBuild + Runtime update deployment cycle.

## Constraints

- **Infrastructure as Code first**: All observability configuration that CloudFormation supports MUST be declared in `infra/agentcore/template.yaml` (IAM permissions, container dependencies, CloudWatch log groups). Features not supported by CloudFormation (Transaction Search enable, Runtime tracing toggle, log delivery configuration) MUST be automated via AWS CLI commands documented in quickstart.md.
- **No manual Console steps**: Zero configuration steps should require manual AWS Console interaction. All steps must be scriptable and repeatable.

## Dependencies

- **Feature 004 (AgentCore deploy)**: The AgentCore Runtime must be deployed and operational.
- **Feature 002 (Cognito login)**: The Cognito JWT authorizer must be configured on the Runtime for Identity observability to have meaningful data.
- **AWS account permissions**: The IAM user/role running the setup commands must have permissions to enable Transaction Search, configure CloudWatch Logs delivery, and modify AgentCore resource settings.
