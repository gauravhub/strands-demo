# Implementation Plan: Deploy Strands Agent to Amazon Bedrock AgentCore

**Branch**: `004-agentcore-deploy` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)

## Summary

Deploy the existing Strands agent (from feature 003) into Amazon Bedrock AgentCore Runtime as a managed, containerised service. The Streamlit frontend forwards the user's Cognito access token (Bearer) to the AgentCore HTTP endpoint, which validates it against the existing Cognito User Pool. Agent responses stream back token-by-token via Server-Sent Events. End-to-end observability (traces + logs) is enabled through OpenTelemetry auto-instrumentation wired to CloudWatch. All infrastructure is provisioned via a single CloudFormation stack that accepts the Cognito Pool ID and Client ID as input parameters.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- `bedrock-agentcore` (agent container SDK — `BedrockAgentCoreApp`, `RequestContext`)
- `aws-opentelemetry-distro>=0.10.1` (OTEL auto-instrumentation, Dockerfile only)
- `requests` (Streamlit HTTP SSE client)
- `strands-agents>=0.1.0`, `strands-agents-tools>=0.1.0` (existing, unchanged)
- `streamlit>=1.35.0`, `boto3>=1.34.0`, `authlib>=1.3.2` (existing, unchanged)
- `bedrock-agentcore-starter-toolkit` (developer CLI, not runtime dependency)
- CloudFormation resource types: `AWS::BedrockAgentCore::Runtime`, `AWS::ECR::Repository`, `AWS::CodeBuild::Project`, `AWS::IAM::Role`, `AWS::Lambda::Function`

**Storage**: None — all session state in `st.session_state` (ephemeral, per browser tab)
**Testing**: `pytest` (unit tests for client, config, SSE parsing logic)
**Target Platform**: ARM64 Linux container (AgentCore managed runtime)
**Performance Goals**: Streaming latency matches current local execution (no perceptible degradation per SC-001)
**Constraints**: OAuth JWT auth mandates raw HTTP (boto3 SDK cannot be used for invocation); container MUST be ARM64
**Scale/Scope**: Single-region demo; AgentCore manages scaling automatically; no explicit concurrency targets

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post-design.*

| Principle | Status | Evidence |
|---|---|---|
| I. Simplicity First | ✅ Pass | Minimal new files (`agentcore/app.py`, `agentcore/client.py`, `agentcore/config.py`); feature-flag approach (`AGENTCORE_RUNTIME_ARN` env var) preserves local fallback; no new abstractions beyond what's required |
| II. Iterative & Independent Delivery | ✅ Pass | Three user stories are independently testable; P1 (auth chat) can be demonstrated before P3 (CFN automation) is complete; local fallback keeps `streamlit run app.py` working at all times |
| III. Python-Native Patterns | ✅ Pass | All new code is Python 3.11+, PEP 8, type hints; new dependencies declared in `pyproject.toml` |
| IV. Security by Design | ✅ Pass | Cognito access token used as Bearer for AgentCore; no hardcoded secrets (API keys as CFN `NoEcho` parameters); IAM roles follow least-privilege; JWT authorizer enforces auth at the endpoint |
| V. Observability & Debuggability | ✅ Pass | OTEL auto-instrumentation (`aws-opentelemetry-distro`) in container; structured logging in both agent container and Streamlit client; auth errors surface as clear messages; no silent failures |

**No violations. No Complexity Tracking entries required.**

## Project Structure

### Documentation (this feature)

```text
specs/004-agentcore-deploy/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Runtime entities
├── quickstart.md        # Deployment guide
├── contracts/
│   └── agentcore-runtime-api.md   # HTTP/SSE contract
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── agent/
│   ├── chatbot.py       # Unchanged — local agent factory (003)
│   └── model.py         # Unchanged — AnthropicModel factory (003)
├── agentcore/           # NEW — AgentCore integration layer
│   ├── __init__.py
│   ├── app.py           # Container entrypoint: BedrockAgentCoreApp wrapping Strands agent
│   ├── client.py        # Streamlit → AgentCore HTTP SSE client
│   └── config.py        # AgentCore config loader (reads AGENTCORE_RUNTIME_ARN, AWS_REGION)
├── auth/                # Unchanged (002)
│   ├── config.py
│   ├── oauth.py
│   └── session.py
└── chat/
    └── ui.py            # MODIFIED — add agentcore streaming variant

infra/
├── cognito.yaml         # Unchanged (002)
└── agentcore/           # NEW — AgentCore infrastructure
    ├── Dockerfile       # ARM64 agent container image
    └── template.yaml    # CloudFormation stack

tests/
└── unit/
    ├── test_agentcore_client.py   # NEW — SSE client unit tests
    └── test_agentcore_config.py   # NEW — config validation unit tests

app.py                   # MODIFIED — route to AgentCore when AGENTCORE_RUNTIME_ARN is set
pyproject.toml           # MODIFIED — add bedrock-agentcore, requests
```

**Structure Decision**: Single-project layout (Option 1), extending the existing `src/` tree with a new `agentcore/` subpackage. Infrastructure lives in `infra/agentcore/` alongside the existing `infra/cognito.yaml`. This mirrors the established convention and avoids any new top-level directories.

---

## Phase 0: Research

**Status**: Complete. See [research.md](research.md).

Key decisions resolved:
1. Raw HTTP (`requests`) for Streamlit → AgentCore invocation (boto3 incompatible with JWT auth)
2. `bedrock-agentcore` pip package for container SDK; `bedrock-agentcore-starter-toolkit` for dev tooling
3. Structured JSON SSE events (6 types: `text`, `reasoning`, `tool_start`, `tool_result`, `error`, `done`)
4. CFN stack: `AWS::BedrockAgentCore::Runtime` + CodeBuild + Lambda custom resource trigger
5. OTEL: `aws-opentelemetry-distro` installed in Dockerfile; `opentelemetry-instrument` as CMD wrapper
6. Session IDs: UUID v4 (36 chars), per browser tab, in `st.session_state`
7. Auth rejection: reactive (detect 401 → clear session → redirect to login)

---

## Phase 1: Design & Implementation Plan

### Component 1: AgentCore Container App (`src/agentcore/app.py`)

**Purpose**: Wraps the existing Strands agent in a `BedrockAgentCoreApp` ASGI entrypoint for deployment to AgentCore Runtime.

**Key design points**:
- Imports `BedrockAgentCoreApp` from `bedrock_agentcore.runtime`
- `@app.entrypoint` is an **async generator** (enables SSE streaming)
- Reuses `create_model()` from `src/agent/model.py`; recreates the Strands `Agent` per-invocation (stateless, thread-safe)
- Translates Strands `stream_async()` events into the 6-type SSE JSON schema defined in `contracts/agentcore-runtime-api.md`
- All exceptions are caught and emitted as `{"type": "error", "message": "..."}` events; no silent failures
- Reads `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` from container environment

**Entry point** (`src/agentcore/app.py`):
```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload: dict, context) -> AsyncGenerator[dict, None]:
    ...
    async for event in agent.stream_async(user_message):
        yield _to_sse_event(event)  # maps Strands events → SSE schema
    yield {"type": "done"}

if __name__ == "__main__":
    app.run()
```

---

### Component 2: AgentCore Client (`src/agentcore/client.py`)

**Purpose**: HTTP SSE client used by the Streamlit app to call the AgentCore Runtime endpoint and yield parsed events to the UI.

**Key design points**:
- `invoke_streaming(runtime_arn, region, session_id, access_token, prompt)` → `Generator[dict, None, None]`
- Constructs the invocation URL by URL-encoding the runtime ARN
- Sets `Authorization: Bearer {access_token}`, `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id: {session_id}` headers
- Uses `requests.post(..., stream=True)` with timeout (connect=5s, read=120s)
- Parses SSE lines: strips `data: ` prefix, JSON-decodes each event, yields to caller
- Raises `AgentCoreAuthError` on HTTP 401 (caller handles session clearance)
- Raises `AgentCoreUnavailableError` on HTTP 503/504
- Raises `AgentCoreError` for other non-200 responses

**Custom exceptions** (defined in `src/agentcore/client.py`):
- `AgentCoreError(Exception)` — base
- `AgentCoreAuthError(AgentCoreError)` — 401: token expired/invalid
- `AgentCoreUnavailableError(AgentCoreError)` — 503/504: runtime down

---

### Component 3: AgentCore Config (`src/agentcore/config.py`)

**Purpose**: Load and validate AgentCore endpoint configuration from environment variables.

**Key design points**:
- `@dataclass(frozen=True) AgentCoreConfig` with fields: `runtime_arn: str`, `region: str`, `qualifier: str = "DEFAULT"`
- `load_agentcore_config() -> AgentCoreConfig | None` — returns `None` if `AGENTCORE_RUNTIME_ARN` is not set (signals local fallback mode)
- Validates ARN format; raises `EnvironmentError` if set but malformed
- Used at Streamlit startup; returned config passed through to the client

---

### Component 4: Chat UI Extension (`src/chat/ui.py`)

**Purpose**: Add an AgentCore streaming variant of `render_input()` that consumes HTTP SSE events instead of Strands events.

**Key design points**:
- New function `render_input_agentcore(config: AgentCoreConfig, access_token: str, session_id: str)`
- Consumes events from `invoke_streaming()` generator; maps each event type to existing Streamlit rendering:
  - `text` → `response_placeholder.markdown()`
  - `reasoning` → `reasoning_placeholder.expander()`
  - `tool_start` → append to `msg["tool_calls"]`, call `_render_tools_live()`
  - `tool_result` → update tool call result, call `_render_tools_live()`
  - `error` → display error in `response_placeholder`
  - `done` → stop iterating
- Catches `AgentCoreAuthError` → calls `clear_session()` + sets `st.session_state["auth_error"]` message + calls `st.rerun()`
- Catches `AgentCoreUnavailableError` and other errors → sets `msg["error"]` with user-friendly message

---

### Component 5: `app.py` Modifications

**Purpose**: Route agent invocations to AgentCore when configured; preserve local fallback.

**Key design points**:
- At startup: call `load_agentcore_config()` → store result in module-level `_agentcore_config`
- In `show_main_app()`:
  - If `_agentcore_config` is set: initialise/reuse a UUID v4 session ID in `st.session_state["agentcore_session_id"]`; call `render_chatbot_agentcore(config=_agentcore_config, access_token=get_user()["access_token"], session_id=session_id)`
  - If `_agentcore_config` is None: call existing `render_chatbot(create_agent())` (local mode, unchanged)
- Check `st.session_state.get("auth_error")` after each rerun; display using `show_landing(error_msg=...)` if set
- Add `AGENTCORE_RUNTIME_ARN` to the env var validation block

---

### Component 6: Dockerfile (`infra/agentcore/Dockerfile`)

**Purpose**: ARM64 container image for the agent; includes OTEL auto-instrumentation.

```dockerfile
FROM public.ecr.aws/docker/library/python:3.11-slim
WORKDIR /app

# Install agent dependencies
COPY requirements-agent.txt .
RUN pip install --no-cache-dir -r requirements-agent.txt

# Copy agent source
COPY src/ ./src/
COPY src/agentcore/app.py ./app.py

ENV PYTHONPATH=/app

# OTEL auto-instrumentation wraps the agent process
CMD ["opentelemetry-instrument", "python", "app.py"]
```

**`requirements-agent.txt`** (container-only, separate from main `pyproject.toml`):
```
strands-agents>=0.1.0
strands-agents-tools>=0.1.0
bedrock-agentcore>=0.1.0
aws-opentelemetry-distro>=0.10.1
anthropic>=0.40.0
python-dotenv>=1.0.0
```

---

### Component 7: CloudFormation Stack (`infra/agentcore/template.yaml`)

**Purpose**: Provision all AWS resources for the AgentCore deployment.

**Parameters**:
- `CognitoUserPoolId` (String)
- `CognitoClientId` (String)
- `CognitoRegion` (String)
- `AnthropicApiKey` (String, NoEcho)
- `TavilyApiKey` (String, NoEcho)
- `ImageTag` (String, Default: `latest`)

**Resources**:

1. **`AWS::ECR::Repository`** (`ECRRepository`): `strands-demo-agent`

2. **`AWS::IAM::Role`** (`AgentExecutionRole`):
   - Trust: `bedrock-agentcore.amazonaws.com`
   - Policies: CloudWatch Logs (`/aws/bedrock-agentcore/runtimes/*`), X-Ray (`*`), CloudWatch Metrics (namespace-scoped), ECR pull (`GetAuthorizationToken`, `BatchGetImage`, etc.), Bedrock model invocation

3. **`AWS::IAM::Role`** (`CodeBuildRole`):
   - Trust: `codebuild.amazonaws.com`
   - Policies: ECR push (full), CloudWatch Logs for build group

4. **`AWS::CodeBuild::Project`** (`AgentImageBuild`):
   - Environment: `ARM_CONTAINER`, `amazonlinux2-aarch64-standard:3.0`
   - Source: `NO_SOURCE` (inline buildspec)
   - Buildspec: clone repo from current commit, `docker buildx build --platform linux/arm64`, push to ECR

5. **`AWS::IAM::Role`** (`BuildTriggerLambdaRole`):
   - Trust: `lambda.amazonaws.com`
   - Policies: `codebuild:StartBuild`, `codebuild:BatchGetBuilds`, CloudWatch Logs for Lambda

6. **`AWS::Lambda::Function`** (`BuildTriggerLambda`):
   - Runtime: `python3.11`
   - Inline code: starts CodeBuild build, polls until complete, signals CloudFormation success/failure
   - Timeout: 900 seconds (15 minutes)

7. **`AWS::CloudFormation::CustomResource`** (`TriggerImageBuild`):
   - ServiceToken: `!GetAtt BuildTriggerLambda.Arn`
   - `DependsOn: AgentImageBuild`

8. **`AWS::BedrockAgentCore::Runtime`** (`AgentRuntime`):
   - `DependsOn: TriggerImageBuild`
   - `AgentRuntimeName: strands-demo-agent`
   - `AgentRuntimeArtifact.ContainerConfiguration.ContainerUri: !Sub "${ECRRepository.RepositoryUri}:${ImageTag}"`
   - `RoleArn: !GetAtt AgentExecutionRole.Arn`
   - `NetworkConfiguration.NetworkMode: PUBLIC`
   - `ProtocolConfiguration: HTTP`
   - `AuthorizerConfiguration.CustomJWTAuthorizer.DiscoveryUrl: !Sub "https://cognito-idp.${CognitoRegion}.amazonaws.com/${CognitoUserPoolId}/.well-known/openid-configuration"`
   - `AuthorizerConfiguration.CustomJWTAuthorizer.AllowedClients: [!Ref CognitoClientId]`
   - `EnvironmentVariables: {ANTHROPIC_API_KEY: !Ref AnthropicApiKey, TAVILY_API_KEY: !Ref TavilyApiKey}`

**Outputs**:
- `AgentRuntimeArn: !GetAtt AgentRuntime.AgentRuntimeArn`
- `AgentRuntimeId: !GetAtt AgentRuntime.AgentRuntimeId`
- `ECRRepositoryUri: !GetAtt ECRRepository.RepositoryUri`

---

### Component 8: `pyproject.toml` Update

Add to `[project].dependencies`:
```toml
"bedrock-agentcore>=0.1.0",
"requests>=2.31.0",
```

---

### Component 9: Unit Tests

**`tests/unit/test_agentcore_client.py`**:
- Test URL construction with ARN encoding
- Test SSE line parsing (`data: ...` → dict)
- Test `AgentCoreAuthError` raised on 401 response (mocked `requests.post`)
- Test `AgentCoreUnavailableError` raised on 503 response
- Test event generator yields correct sequence of typed events

**`tests/unit/test_agentcore_config.py`**:
- Test `load_agentcore_config()` returns `None` when env var absent
- Test raises `EnvironmentError` when ARN is malformed
- Test returns valid `AgentCoreConfig` with correct fields when env var is set

---

## Implementation Order (User Story Alignment)

| Story | Priority | Components | Deliverable |
|---|---|---|---|
| S1: Authenticated Chat | P1 | 1, 2, 3, 4, 5, 8 | Streamlit → AgentCore SSE streaming with Cognito Bearer token |
| S2: Observability | P2 | 6 (Dockerfile OTEL) | Traces + logs in CloudWatch per invocation |
| S3: CloudFormation | P3 | 7 | Full stack reproducibility in one command |
| Cross-cutting | — | 9 | Unit tests for client and config |

> **Sequencing note**: S1 can be validated manually (using `agentcore deploy` CLI or pre-existing runtime) before S3 (CFN) is complete, consistent with the spec's Independent Test criteria.

---

## Post-Design Constitution Re-check

| Principle | Status | Notes |
|---|---|---|
| I. Simplicity First | ✅ Pass | No new abstractions; no speculative features; feature-flag keeps local dev simple |
| II. Iterative Delivery | ✅ Pass | S1 demonstrable independently; app always runnable; Dockerfile + CFN are additive |
| III. Python-Native | ✅ Pass | All new files are Python 3.11+, typed, idiomatic; `pyproject.toml` updated correctly |
| IV. Security by Design | ✅ Pass | JWT authorizer enforces auth at network level; API keys as `NoEcho` CFN params; least-privilege IAM |
| V. Observability | ✅ Pass | OTEL auto-instrumentation in container; structured logging in client; auth errors surfaced clearly |
