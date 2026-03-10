# Feature Specification: Deploy Strands Agent to Amazon Bedrock AgentCore

**Feature Branch**: `004-agentcore-deploy`
**Created**: 2026-03-10
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Authenticated Chat via AgentCore (Priority: P1)

An authenticated Streamlit user sends a message to the Strands agent. The Streamlit app forwards the user's existing Cognito access token to the AgentCore Runtime endpoint. AgentCore validates the token against the Cognito pool and, if valid, routes the request to the deployed agent. The agent responds and the result is displayed in the Streamlit UI — exactly as before, but now execution happens in the managed AgentCore Runtime environment instead of locally.

**Why this priority**: This is the core integration — it proves the end-to-end flow from browser login through token-secured invocation to agent response. All other stories depend on this working.

**Independent Test**: Log in to the Streamlit app with a valid Cognito account, send a chat message, and confirm a valid agent response is returned (without any AWS credential config on the client side).

**Acceptance Scenarios**:

1. **Given** a user is logged in to Streamlit (Cognito access token held in session), **When** they send a chat message, **Then** the message is forwarded to the AgentCore Runtime endpoint, the Cognito token is accepted, and a valid agent response is returned and displayed in the UI.
2. **Given** a valid Cognito access token, **When** the token is used to call the AgentCore Runtime endpoint directly (e.g., via CLI), **Then** the runtime responds with the agent output.
3. **Given** an expired or missing Cognito token, **When** the AgentCore Runtime endpoint is called, **Then** the request is rejected with an authentication error and the user sees an appropriate message in the Streamlit UI.
4. **Given** a Cognito token issued for a different User Pool or client, **When** it is used to call the AgentCore Runtime endpoint, **Then** the request is rejected.

---

### User Story 2 — Observability: Traces and Logs Visible to Operators (Priority: P2)

An operator or developer can see end-to-end traces and logs for every agent invocation in AWS CloudWatch. Traces capture the full lifecycle of a request (reception, agent reasoning steps, tool calls, response). Logs capture runtime output and errors. Both are accessible from the AWS Console without any additional tooling setup.

**Why this priority**: Operational visibility is essential for debugging agent behavior and diagnosing failures in production. This is particularly important for agent workloads where LLM reasoning steps are otherwise opaque.

**Independent Test**: Invoke the AgentCore Runtime endpoint with a test prompt and confirm a corresponding trace and log entries appear in CloudWatch within 60 seconds.

**Acceptance Scenarios**:

1. **Given** an agent invocation completes successfully, **When** an operator opens CloudWatch, **Then** a trace is visible showing the request lifecycle, latency breakdown, and any tool calls made.
2. **Given** an agent invocation fails (e.g., model error, tool error), **When** an operator inspects CloudWatch logs, **Then** the error is logged with enough context to diagnose the root cause.
3. **Given** multiple concurrent agent invocations, **When** an operator views CloudWatch, **Then** traces are distinct and correctly correlated to their respective requests.
4. **Given** the system has been running for several invocations, **When** an operator views the GenAI Observability dashboard, **Then** aggregate metrics (latency, request count, error rate) are visible.

---

### User Story 3 — Infrastructure Provisioned via CloudFormation (Priority: P3)

The AgentCore Runtime endpoint, IAM roles, Cognito JWT authorizer configuration, and observability permissions are all provisioned and reproducible via a CloudFormation stack. No manual console clicks are required after initial deployment to stand up a new environment.

**Why this priority**: Reproducibility and auditability of infrastructure are project requirements. However, the agent itself can still be tested (Story 1) before CloudFormation automation is fully polished.

**Independent Test**: Delete and re-deploy the CloudFormation stack from scratch; confirm the end-to-end Story 1 flow works after stack deployment completes.

**Acceptance Scenarios**:

1. **Given** a clean AWS environment with the existing Cognito pool already present, **When** the CloudFormation stack is deployed, **Then** the AgentCore Runtime endpoint is available and secured with the Cognito JWT authorizer.
2. **Given** the stack is deployed, **When** the stack is deleted, **Then** all created resources are removed without orphaned resources.
3. **Given** the stack outputs, **When** they are referenced by the Streamlit app configuration, **Then** the app correctly targets the deployed AgentCore Runtime endpoint.

---

### Edge Cases

- What happens when the Cognito access token expires mid-session in Streamlit? The Streamlit app detects the authentication rejection from AgentCore (reactive), clears the session state, and redirects the user to the Cognito login page with a clear "Your session has expired, please log in again" message.
- What happens when the AgentCore Runtime is temporarily unavailable? The Streamlit UI should display a meaningful error message rather than hanging indefinitely.
- What happens when the agent execution times out (long-running reasoning)? The timeout should be surfaced gracefully to the user.
- What happens when the container image fails to build or deploy to AgentCore? The CloudFormation stack should roll back cleanly and the failure reason should be logged.
- What happens when a tool call inside the agent fails? The error should be captured in traces and logs without crashing the agent session.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Strands agent MUST be deployed to and executed within Amazon Bedrock AgentCore Runtime as a managed service (not run locally or on self-managed compute).
- **FR-001a**: The AgentCore Runtime endpoint MUST support streaming responses (Server-Sent Events), delivering agent output token-by-token to the Streamlit UI — matching the real-time streaming experience of the current local-execution mode.
- **FR-002**: The AgentCore Runtime endpoint MUST be secured using the existing AWS Cognito User Pool as the identity provider, accepting Cognito-issued access tokens as Bearer tokens for inbound authentication.
- **FR-003**: The Streamlit application MUST forward the user's Cognito access token (obtained at login) to the AgentCore Runtime endpoint on every agent invocation — no separate login or credential exchange is required for the end user.
- **FR-004**: Users who are not authenticated (no valid Cognito token) MUST be rejected at the AgentCore Runtime endpoint with a clear authentication error.
- **FR-005**: The system MUST emit distributed traces for every agent invocation, capturing at minimum: request receipt, agent reasoning steps, tool calls, and response delivery.
- **FR-006**: The system MUST emit structured logs for every agent invocation to CloudWatch, including successful completions and errors with sufficient context to diagnose failures.
- **FR-007**: Traces and logs MUST be accessible from the AWS CloudWatch console within 60 seconds of an invocation completing.
- **FR-008**: The AgentCore Runtime, IAM execution role, Cognito JWT authorizer binding, and observability permissions MUST all be provisioned exclusively via CloudFormation — no manual AWS Console configuration steps. The stack MUST accept the existing Cognito User Pool ID and App Client ID as input parameters.
- **FR-009**: The container image for the agent MUST be built and published to a managed container registry as part of the deployment pipeline (automated, not manual).
- **FR-010**: The Streamlit application MUST read the AgentCore Runtime endpoint identifier from configuration (not hardcoded), sourced from CloudFormation stack outputs or environment variables.
- **FR-011**: The existing Streamlit Cognito login flow MUST remain unchanged from the user's perspective — only the backend invocation target changes from local execution to AgentCore.
- **FR-012**: The system MUST surface a user-friendly error message in the Streamlit UI when the AgentCore endpoint rejects a request due to authentication failure or when the endpoint is unavailable.
- **FR-013**: When AgentCore returns an authentication rejection (e.g., expired token), the Streamlit app MUST clear the user's session state and redirect to the Cognito login page with a message indicating the session has expired — no proactive token refresh is required.

### Key Entities

- **AgentCore Runtime**: The managed hosting environment for the Strands agent; identified by an ARN, accepts authenticated HTTP invocations on a stable endpoint.
- **Agent Container Image**: The packaged Strands agent code published to a container registry; the deployable artifact consumed by the Runtime.
- **Cognito JWT Authorizer**: The configuration binding the AgentCore Runtime to the Cognito User Pool, enabling inbound request authentication via Bearer tokens.
- **Invocation Session**: A stateful agent execution context identified by a session ID; supports multi-turn conversation within a single session.
- **Trace**: A structured record of an agent invocation lifecycle stored in CloudWatch, containing spans for each processing step (receipt, reasoning, tool calls, response).
- **Log Stream**: Time-ordered structured log entries for a Runtime instance stored in CloudWatch Logs, including runtime output and error details.
- **CloudFormation Stack**: The declarative infrastructure definition that provisions and wires together all AgentCore, container registry, IAM, and observability resources.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Authenticated Streamlit users can send messages to the agent and receive streaming responses token-by-token with no perceptible change in the interaction flow compared to the current local-execution experience.
- **SC-002**: Unauthenticated or invalidly-authenticated requests to the AgentCore Runtime are rejected 100% of the time with a meaningful error surfaced to the caller.
- **SC-003**: End-to-end traces for every agent invocation are visible in CloudWatch within 60 seconds of request completion.
- **SC-004**: Logs containing sufficient detail to diagnose errors are available in CloudWatch for every invocation, including failed ones.
- **SC-005**: The entire infrastructure (Runtime, IAM, container registry, observability wiring) can be stood up from scratch by running a single CloudFormation deployment command, with no additional manual steps.
- **SC-006**: A fresh environment can be reproduced end-to-end (deploy stack → build image → invoke agent) in under 30 minutes.
- **SC-007**: The Streamlit app correctly handles authentication failures and Runtime errors by displaying a user-facing message rather than an unhandled exception.

## Assumptions

- The existing Cognito User Pool and App Client from feature `002-cognito-login` are reused without modification. The 004 CloudFormation stack references them via input parameters (Cognito Pool ID and App Client ID supplied at deploy time) — no cross-stack `Fn::ImportValue` coupling.
- The AgentCore Runtime is deployed in the same AWS region as the existing Cognito User Pool.
- Observability (traces and logs) requires `aws-opentelemetry-distro` to be explicitly installed in the container image and the container CMD to use `opentelemetry-instrument` as a wrapper. AgentCore does not bundle OTEL in its base images; the Dockerfile must install and activate it.
- The agent container is built for the ARM64 architecture, consistent with AgentCore's default managed build pipeline.
- Network access for the AgentCore Runtime endpoint is public (no VPC private networking) for this iteration.
- The Streamlit app continues to run on local or simple hosted compute — no containerization or deployment change to the Streamlit layer is in scope for this feature.
- Session IDs for multi-turn conversations are generated by the Streamlit app and held in `st.session_state` (in-memory, per browser tab). Sessions are ephemeral — a page refresh or new tab starts a fresh conversation with no history restored. No backend session storage is required.
- The existing Strands agent logic (tools, model, system prompts) from feature `003-strands-reasoning-chatbot` is deployed without modification — only the hosting environment changes.
- AgentCore Identity is used solely to configure the inbound JWT authorizer (binding Cognito as the IdP); outbound token exchange to downstream services is out of scope for this iteration.

## Clarifications

### Session 2026-03-10

- Q: Will the Streamlit chat UI continue to stream agent responses token-by-token, or is a batch response acceptable for the AgentCore-hosted version? → A: Preserve streaming — agent responses stream token-by-token via SSE, matching the current 003 experience.
- Q: When the Cognito access token expires, should the app proactively refresh it or reactively detect rejection and redirect to re-login? → A: Reactive — detect 401/auth rejection from AgentCore, clear the session, and redirect the user to re-login with a friendly message.
- Q: How should the 004 CloudFormation stack reference the existing Cognito User Pool from 002? → A: Parameter-based — the 004 stack accepts Cognito Pool ID and Client ID as input parameters supplied at deploy time from 002 outputs; no cross-stack coupling.
- Q: Should agent conversation sessions persist across browser refreshes/tab reopens? → A: Ephemeral — each browser tab starts a fresh conversation; page refresh loses history (consistent with current 003 pattern).

## Dependencies

- **002-cognito-login**: Provides the Cognito User Pool ARN, Pool ID, region, and App Client ID required for configuring the JWT authorizer on the AgentCore Runtime.
- **003-strands-reasoning-chatbot**: Provides the Strands agent code to be containerized and deployed to AgentCore.
- **AWS Services**: Amazon Bedrock AgentCore Runtime, Amazon ECR, AWS CloudFormation, AWS CloudWatch (Logs, X-Ray Tracing, GenAI Observability dashboard), AWS IAM, AWS CodeBuild.
