# Feature Specification: Deploy Streamlit App to Streamlit Community Cloud

**Feature Branch**: `005-streamlit-cloud-deploy`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Deploy streamlit app to Streamlit Community Cloud"

## Scope & Architecture Boundary

**In scope — Streamlit Community Cloud:**
- The Streamlit frontend application (`app.py`) and all supporting Python source code
- Secrets configuration (API keys, Cognito settings, AgentCore ARN) in Streamlit Community Cloud
- GitHub repository setup to enable Streamlit Community Cloud deployment

**Out of scope — remains on AWS (unchanged):**
- Amazon Bedrock AgentCore Runtime (deployed in feature 004, hosted on AWS)
- AWS Cognito User Pool and hosted UI (deployed in feature 002, hosted on AWS)
- ECR, IAM roles, CodeBuild pipeline (all AWS infrastructure from feature 004)

The Streamlit app is a **stateless frontend** that calls the AgentCore Runtime over HTTPS using a Cognito JWT Bearer token. No AWS infrastructure is moved or replicated — only the frontend changes hosting location.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — App Accessible on Public URL (Priority: P1)

A developer deploys the Strands Demo Streamlit app to Streamlit Community Cloud so that users can access it from a stable public HTTPS URL without running the app locally.

**Why this priority**: This is the core goal — making the app publicly accessible. All other stories depend on the app being live.

**Independent Test**: Access the public Streamlit Community Cloud URL in a browser and verify the landing page loads with the Login button visible.

**Acceptance Scenarios**:

1. **Given** the app is deployed to Streamlit Community Cloud, **When** a user visits the public URL, **Then** the Strands Demo landing page renders with the robot emoji title and Login button.
2. **Given** the app is live, **When** the user clicks Login, **Then** they are redirected to the Cognito hosted UI.
3. **Given** the app is deployed, **When** the Streamlit Community Cloud runner starts the app, **Then** no missing environment variable errors appear and the app does not crash on startup.

---

### User Story 2 — Secrets Securely Configured in Cloud (Priority: P2)

A developer configures all required secrets (API keys, Cognito settings, AgentCore ARN) in Streamlit Community Cloud's secrets management so the app runs identically to the local setup.

**Why this priority**: The app will not function without secrets. Secure configuration is a prerequisite for any user interaction.

**Independent Test**: After configuring secrets in Streamlit Community Cloud, restart the app and confirm it loads without error and all integrations (Cognito redirect, AgentCore invocation) work end to end.

**Acceptance Scenarios**:

1. **Given** secrets are configured in Streamlit Community Cloud, **When** the app starts, **Then** it reads all required values without raising errors.
2. **Given** `AGENTCORE_RUNTIME_ARN` is set in cloud secrets, **When** a logged-in user sends a chat message, **Then** the message is routed to AgentCore Runtime and a streaming response is returned.
3. **Given** secrets are stored in Streamlit Community Cloud, **When** viewed by a collaborator, **Then** secret values are masked and never exposed in logs or the UI.

---

### User Story 3 — Cognito Redirect URI Updated for Cloud URL (Priority: P3)

A developer registers the Streamlit Community Cloud public URL as an allowed redirect URI in the Cognito App Client so that the OAuth2 login callback works correctly after deployment.

**Why this priority**: Without updating Cognito, the login flow will fail with an OAuth redirect mismatch error, blocking all authenticated users.

**Independent Test**: Complete a full login flow on the deployed cloud URL — click Login, authenticate in Cognito hosted UI, and verify successful redirect back to the app with an active session.

**Acceptance Scenarios**:

1. **Given** the cloud URL is registered in Cognito, **When** a user completes login via the Cognito hosted UI, **Then** they are redirected back to the Streamlit Community Cloud URL with a valid session.
2. **Given** the Cognito callback URL matches the cloud URL, **When** the OAuth2 code exchange completes, **Then** the user sees the main chatbot interface with their username displayed.
3. **Given** only the cloud URL is registered, **When** a developer tries to log in from `localhost:8501` without its own registration, **Then** Cognito rejects the redirect with a clear mismatch error.

---

### Edge Cases

- What happens when Streamlit Community Cloud restarts the app while a user is mid-conversation? (Session state is in-memory — user must log in again; no data is lost.)
- What if required secrets are missing or misconfigured in the cloud environment? (App must show a clear startup error message, not crash silently.)
- What if the AgentCore Runtime is unavailable when a user sends a message? (App must show a user-friendly "service unavailable" message and not hang indefinitely.)
- What happens if the GitHub repository is private and Streamlit Community Cloud cannot access it? (Deployment fails with a clear permission error rather than a silent timeout.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Streamlit frontend application MUST be deployable to Streamlit Community Cloud from the project's GitHub repository without modifying application logic. The AgentCore Runtime, Cognito User Pool, and all other AWS infrastructure MUST remain hosted on AWS and are out of scope for this feature.
- **FR-002**: The app MUST read all configuration (API keys, Cognito settings, AgentCore ARN) from the hosting platform's secrets management — not from committed files.
- **FR-003**: The Cognito App Client MUST have the Streamlit Community Cloud public URL registered as an allowed callback URI and logout URI.
- **FR-004**: The app MUST start successfully on Streamlit Community Cloud with all Python package dependencies resolvable from the project's dependency manifest.
- **FR-005**: The deployed app MUST preserve all existing functionality: Cognito login/logout, AgentCore chat routing, and local agent fallback when `AGENTCORE_RUNTIME_ARN` is unset.
- **FR-006**: The `.env` file MUST NOT be committed to the repository; all secrets MUST be supplied exclusively through the cloud platform's secrets mechanism.
- **FR-007**: The app MUST display a clear, user-friendly error if required secrets are missing at startup rather than crashing silently.
- **FR-008**: The OAuth2 redirect URI MUST be configurable per environment (local vs. cloud) without code changes — driven solely by the `COGNITO_REDIRECT_URI` secret value.
- **FR-009**: The project MUST have a public GitHub remote repository so Streamlit Community Cloud can pull the source code for deployment without additional authorization.

### Key Entities

- **Deployment Configuration**: The complete set of environment variables required to run the app (`COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET`, `COGNITO_DOMAIN`, `COGNITO_REDIRECT_URI`, `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, `AGENTCORE_RUNTIME_ARN`, `AWS_REGION`, `LOG_LEVEL`).
- **Cognito App Client**: The OAuth2 client registered in AWS Cognito; holds the list of allowed redirect URIs and logout URIs for each environment.
- **Streamlit Community Cloud App**: The hosted instance identified by its stable public URL (e.g., `https://<app-name>.streamlit.app`).
- **GitHub Repository**: The remote source control repository that Streamlit Community Cloud monitors for changes and pulls from on each deployment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Strands Demo landing page loads at the public Streamlit Community Cloud URL within 15 seconds of a cold start.
- **SC-002**: A new user can complete the full login flow (landing → Cognito → callback → chatbot) in under 60 seconds on the deployed URL.
- **SC-003**: 100% of required secrets are supplied via the cloud platform's secrets mechanism with zero secrets committed to the repository.
- **SC-004**: The deployed app passes the full functional smoke test: landing page renders, Login redirects to Cognito, authenticated user can send a message and receive an AgentCore response.
- **SC-005**: Updating a secret in Streamlit Community Cloud takes effect within one app restart with no manual infrastructure changes required.

## Assumptions

- Streamlit Community Cloud free tier supports the app's Python dependencies and memory requirements for a demo workload.
- The project repository will be pushed to GitHub (a remote must be created if not already present) for Streamlit Community Cloud to connect to.
- AWS credentials are NOT needed in Streamlit Community Cloud; the app uses API keys (Anthropic, Tavily) and the AgentCore Runtime ARN with JWT Bearer token — no IAM credentials required at runtime.
- The existing `COGNITO_REDIRECT_URI` environment variable fully controls the OAuth2 callback URL; changing its value to the cloud URL requires no code changes.
- Streamlit Community Cloud provisions a stable `*.streamlit.app` subdomain that persists across redeployments.
- Local development continues to use `localhost:8501` as a separately registered Cognito redirect URI.
- The `requirements.txt` file (or equivalent derived from `pyproject.toml`) will be added to the repository root for Streamlit Community Cloud's dependency installer.

## Clarifications

### Session 2026-03-10

- Q: Should the GitHub repository be public or private for Streamlit Community Cloud? → A: Public — no sensitive source code in the repo (secrets are in SCC secrets manager), and public repos connect to SCC without additional OAuth authorization.

## Dependencies

- **Feature 002 (Cognito login)**: Cognito User Pool App Client must be updated to allow the new cloud redirect URI and logout URI.
- **Feature 004 (AgentCore deploy)**: `AGENTCORE_RUNTIME_ARN` output from the AgentCore CloudFormation stack is required as a cloud secret.
- **GitHub remote**: Repository must be pushed to GitHub as a **public** repository before connecting to Streamlit Community Cloud.
