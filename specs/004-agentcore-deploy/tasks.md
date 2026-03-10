# Tasks: Deploy Strands Agent to Amazon Bedrock AgentCore

**Input**: Design documents from `/specs/004-agentcore-deploy/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tech stack**: Python 3.11+, `bedrock-agentcore`, `requests`, `aws-opentelemetry-distro`, CloudFormation
**Tests**: Unit tests included for AgentCore config and client (per plan.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label — [US1], [US2], [US3]
- Exact file paths are included in every description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependencies and create directory skeletons before any implementation begins.

- [x] T001 Update `pyproject.toml` — add `"bedrock-agentcore>=0.1.0"` and `"requests>=2.31.0"` to `[project].dependencies`
- [x] T002 Create `src/agentcore/__init__.py` to establish the `agentcore` package (empty file with module docstring)
- [x] T003 [P] Create `infra/agentcore/requirements-agent.txt` with container-only dependencies: `strands-agents>=0.1.0`, `strands-agents-tools>=0.1.0`, `bedrock-agentcore>=0.1.0`, `anthropic>=0.40.0`, `python-dotenv>=1.0.0`, `aws-opentelemetry-distro>=0.10.1` — include OTEL from the start so the Dockerfile CMD (`opentelemetry-instrument`) is satisfied from the first container build

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core components required before any user story work can begin — the config loader is used by all three stories; the Dockerfile (with OTEL) is the container image foundation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Implement `src/agentcore/config.py` — `@dataclass(frozen=True) AgentCoreConfig` with fields `runtime_arn: str`, `region: str`, `qualifier: str = "DEFAULT"`; `load_agentcore_config() -> AgentCoreConfig | None` returns `None` when `AGENTCORE_RUNTIME_ARN` env var is absent, raises `EnvironmentError` with a clear message when the var is set but the ARN does not match `arn:aws:bedrock-agentcore:*` pattern
- [x] T005 Create `infra/agentcore/Dockerfile` — `FROM public.ecr.aws/docker/library/python:3.11-slim`, `WORKDIR /app`, `COPY infra/agentcore/requirements-agent.txt .`, `RUN pip install --no-cache-dir -r requirements-agent.txt`, `COPY src/ ./src/`, `COPY src/agentcore/app.py ./app.py`, `ENV PYTHONPATH=/app`, `CMD ["opentelemetry-instrument", "python", "app.py"]` (OTEL auto-instrumentation wrapper is included from day 1)

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Authenticated Chat via AgentCore (Priority: P1) 🎯 MVP

**Goal**: The Streamlit app forwards the user's Cognito access token to AgentCore Runtime; agent responds with streaming SSE output matching the current local-execution experience.

**Independent Test**: Log in to Streamlit with a valid Cognito account, send a chat message, and receive a streaming token-by-token response from the deployed AgentCore Runtime — no AWS credentials required on the client side.

### Implementation for User Story 1

- [x] T006 [P] [US1] Create `src/agentcore/app.py` — `BedrockAgentCoreApp` with an `async def invoke(payload: dict, context)` generator decorated with `@app.entrypoint`; inside, call `Agent(model=create_model(), tools=[tavily]).stream_async(payload.get("prompt",""))` and translate each Strands event to a typed SSE JSON dict using a `_to_sse_event(event)` helper that maps: `"data" in event → {"type":"text","data":...}`, `"reasoning" in event → {"type":"reasoning","data":...}`, `"current_tool_use"+"delta" → {"type":"tool_start","tool_use_id":...,"name":...,"input":...}`, tool result message events `→ {"type":"tool_result","tool_use_id":...,"result":...}`; catch all exceptions and yield `{"type":"error","message":str(e)}`; yield `{"type":"done"}` as final event; call `app.run()` in `if __name__ == "__main__":`
- [x] T007 [P] [US1] Create `src/agentcore/client.py` — define `AgentCoreError(Exception)`, `AgentCoreAuthError(AgentCoreError)`, `AgentCoreUnavailableError(AgentCoreError)`; implement `invoke_streaming(runtime_arn: str, region: str, qualifier: str, session_id: str, access_token: str, prompt: str) -> Generator[dict, None, None]` that: URL-encodes the ARN via `urllib.parse.quote(runtime_arn, safe="")`, constructs `POST https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier={qualifier}`, sets headers `Authorization: Bearer {access_token}` and `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id: {session_id}` and `Content-Type: application/json`, calls `requests.post(..., json={"prompt": prompt}, stream=True, timeout=(5, 120))`, raises `AgentCoreAuthError` on HTTP 401, raises `AgentCoreUnavailableError` on HTTP 503/504, raises `AgentCoreError` on other non-200 codes, then iterates `response.iter_lines()` stripping `b"data: "` prefix and JSON-decoding each non-empty line, yielding the resulting dict
- [x] T008 [US1] Update `src/chat/ui.py` — add `render_chatbot_agentcore(config: "AgentCoreConfig", access_token: str, session_id: str) -> None` function that: calls `init_session()`, calls `render_chat_history()`, renders the chat input field; on submission builds a `msg` dict (same structure as existing assistant messages), calls `invoke_streaming(...)` generator inside a try/except block, maps each yielded event by `type`: `"text"` → accumulate `msg["content"]` and update `response_placeholder`, `"reasoning"` → accumulate `msg["reasoning"]` and update `reasoning_placeholder`, `"tool_start"` → append to `msg["tool_calls"]` and call `_render_tools_live()`, `"tool_result"` → update matching tool call result and call `_render_tools_live()`, `"error"` → set `msg["error"]` and display in placeholder, `"done"` → stop; catch `AgentCoreAuthError` → set `st.session_state["agentcore_auth_expired"] = True` and call `st.rerun()`; catch other exceptions → set `msg["error"]` with user-friendly message
- [x] T009 [US1] Update `app.py` — at module level call `load_agentcore_config()` and store as `_agentcore_config`; add `"AGENTCORE_RUNTIME_ARN"` to the optional env var validation block (warn but don't stop if absent — local fallback mode); in `show_main_app()`: if `_agentcore_config` is set, generate UUID v4 session ID once per tab via `st.session_state.setdefault("agentcore_session_id", str(uuid.uuid4()))`, call `render_chatbot_agentcore(config=_agentcore_config, access_token=get_user()["access_token"], session_id=st.session_state["agentcore_session_id"])`, else call existing `render_chatbot(create_agent())`; in the main routing block check `st.session_state.pop("agentcore_auth_expired", False)` → if True call `clear_session()` and `show_landing(error_msg="Your session has expired, please log in again.")`
- [x] T010 [P] [US1] Create `tests/unit/test_agentcore_config.py` — three tests using `monkeypatch`: (1) `load_agentcore_config()` returns `None` when `AGENTCORE_RUNTIME_ARN` is not set; (2) raises `EnvironmentError` when `AGENTCORE_RUNTIME_ARN` is set to a malformed value (e.g., `"not-an-arn"`); (3) returns `AgentCoreConfig` with correct `runtime_arn`, `region`, `qualifier="DEFAULT"` when env var is a valid ARN and `AWS_REGION` is set
- [x] T011 [P] [US1] Create `tests/unit/test_agentcore_client.py` — five tests using `unittest.mock.patch("requests.post")`: (1) URL construction correctly URL-encodes the runtime ARN (assert `%3A` present in URL); (2) `Authorization: Bearer` and session-ID headers are set correctly; (3) mock returning status 401 raises `AgentCoreAuthError`; (4) mock returning status 503 raises `AgentCoreUnavailableError`; (5) mock returning a streaming response with `data: {"type":"text","data":"hello"}` and `data: {"type":"done"}` lines yields two dicts in order

**Checkpoint**: User Story 1 is fully functional — authenticated Streamlit users can chat via AgentCore with streaming responses

---

## Phase 4: User Story 2 — Observability: Traces and Logs (Priority: P2)

**Goal**: Every agent invocation emits structured logs and distributed traces visible in CloudWatch within 60 seconds of completion.

**Independent Test**: Deploy the agent container (manually via `agentcore deploy` CLI or after Phase 5 CFN); invoke the endpoint with a test prompt; confirm a trace and log entries appear in CloudWatch log group `/aws/bedrock-agentcore/runtimes/{runtime-id}-DEFAULT`.

### Implementation for User Story 2

- [x] T012 [US2] Update `src/agentcore/app.py` — add structured logging using `logging.getLogger(__name__)`; log at `INFO` on invocation start: `session_id`, `prompt_len=len(prompt)`; log at `INFO` for each tool call event: `tool_name`, `tool_use_id`; log at `INFO` on stream completion: counts of `text_events`, `tool_calls`, `errors`; log at `ERROR` with `exc_info=True` in the exception handler — these log lines are captured by the CloudWatch log group created by AgentCore Runtime
- [x] T013 [US2] Verify `infra/agentcore/Dockerfile` CMD is `["opentelemetry-instrument", "python", "app.py"]` and `infra/agentcore/requirements-agent.txt` contains `aws-opentelemetry-distro>=0.10.1` (both set in Phase 1/2); rebuild and redeploy the container image after T012 logging changes are complete to produce an image with both OTEL tracing and structured logging active

**Checkpoint**: Agent emits structured logs + X-Ray traces. CloudWatch GenAI Observability dashboard activates automatically after first traced invocation.

---

## Phase 5: User Story 3 — Infrastructure via CloudFormation (Priority: P3)

**Goal**: The entire AgentCore infrastructure (ECR, IAM, CodeBuild, Runtime with Cognito JWT authorizer) is reproducible from a single `aws cloudformation deploy` command.

**Independent Test**: Delete the stack and redeploy from scratch; confirm User Story 1 end-to-end flow works after stack completes.

### Implementation for User Story 3

- [ ] T014 [US3] Create `infra/agentcore/template.yaml` — add `AWSTemplateFormatVersion: "2010-09-09"`, `Description`, `Parameters` (CognitoUserPoolId, CognitoClientId, CognitoRegion as String; AnthropicApiKey and TavilyApiKey as String with `NoEcho: true`; ImageTag as String with `Default: latest`), and two resources: `ECRRepository` (`AWS::ECR::Repository`, `RepositoryName: strands-demo-agent`, **`EmptyOnDelete: true`** — required so CFN stack deletion succeeds even when images are present) and `AgentExecutionRole` (`AWS::IAM::Role`, `AssumeRolePolicyDocument` trusting `bedrock-agentcore.amazonaws.com`, inline policies for: CloudWatch Logs on `/aws/bedrock-agentcore/runtimes/*`, X-Ray on `*`, CloudWatch Metrics PutMetricData with namespace condition `bedrock-agentcore`, ECR pull actions `GetAuthorizationToken`+`BatchCheckLayerAvailability`+`GetDownloadUrlForLayer`+`BatchGetImage` on `*`)
- [ ] T015 [US3] Update `infra/agentcore/template.yaml` — add `CodeBuildRole` (`AWS::IAM::Role` trusting `codebuild.amazonaws.com`; ECR push: `GetAuthorizationToken`, `BatchCheckLayerAvailability`, `InitiateLayerUpload`, `UploadLayerPart`, `CompleteLayerUpload`, `PutImage`; CloudWatch Logs: `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`) and `AgentImageBuild` (`AWS::CodeBuild::Project`: `Environment.Type: ARM_CONTAINER`, `ComputeType: BUILD_GENERAL1_SMALL`, `Image: aws/codebuild/amazonlinux2-aarch64-standard:3.0`, `PrivilegedMode: true`; inline buildspec with phases: `install: pip install`, `pre_build: aws ecr get-login-password | docker login`, `build: docker buildx build --platform linux/arm64 -t {ECR_URI}:{IMAGE_TAG} -f infra/agentcore/Dockerfile .`, `post_build: docker push {ECR_URI}:{IMAGE_TAG}`)
- [ ] T016 [US3] Update `infra/agentcore/template.yaml` — add `BuildTriggerLambdaRole` (`AWS::IAM::Role` trusting `lambda.amazonaws.com`; `codebuild:StartBuild`, `codebuild:BatchGetBuilds`; CloudWatch Logs for Lambda), `BuildTriggerLambda` (`AWS::Lambda::Function`: Python 3.11, inline handler that calls `StartBuild`, polls `BatchGetBuilds` every 30s, calls `cfnresponse.send(SUCCESS/FAILED)`, `Timeout: 900`), and `TriggerImageBuild` (`AWS::CloudFormation::CustomResource`: `ServiceToken: !GetAtt BuildTriggerLambda.Arn`, `DependsOn: AgentImageBuild`)
- [ ] T017 [US3] Update `infra/agentcore/template.yaml` — add `AgentRuntime` (`AWS::BedrockAgentCore::Runtime`: `DependsOn: TriggerImageBuild`; `AgentRuntimeName: strands-demo-agent`; `AgentRuntimeArtifact.ContainerConfiguration.ContainerUri: !Sub "${ECRRepository.RepositoryUri}:${ImageTag}"`; `RoleArn: !GetAtt AgentExecutionRole.Arn`; `NetworkConfiguration.NetworkMode: PUBLIC`; `ProtocolConfiguration: HTTP`; `AuthorizerConfiguration.CustomJWTAuthorizer.DiscoveryUrl: !Sub "https://cognito-idp.${CognitoRegion}.amazonaws.com/${CognitoUserPoolId}/.well-known/openid-configuration"` and `AllowedClients: [!Ref CognitoClientId]`; `EnvironmentVariables: {ANTHROPIC_API_KEY: !Ref AnthropicApiKey, TAVILY_API_KEY: !Ref TavilyApiKey}`) and `Outputs` section: `AgentRuntimeArn: !GetAtt AgentRuntime.AgentRuntimeArn`, `AgentRuntimeId: !GetAtt AgentRuntime.AgentRuntimeId`, `ECRRepositoryUri: !GetAtt ECRRepository.RepositoryUri`

**Checkpoint**: All three user stories are independently functional and the full environment is reproducible from a single CloudFormation command.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T018 [P] Create or update `.env.example` at the repository root — add `AGENTCORE_RUNTIME_ARN=` (value to be populated from CFN stack output `AgentRuntimeArn`) and confirm `AWS_REGION=` is documented; add a comment block explaining: "Set AGENTCORE_RUNTIME_ARN to route chat to AgentCore; leave unset for local agent fallback"
- [x] T019 Run `pytest tests/unit/test_agentcore_config.py tests/unit/test_agentcore_client.py -v` from the project root and confirm all tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — no dependency on US2 or US3
- **US2 (Phase 4)**: Depends on Phase 2 — no dependency on US1 or US3 (tests independently with manually deployed runtime)
- **US3 (Phase 5)**: Depends on Phase 2 and US1 (Dockerfile + app.py must exist for the CodeBuild buildspec to succeed) — can reference US2 logging but does not depend on it
- **Polish (Phase 6)**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (P1)**: No cross-story dependencies. Independently testable as soon as Foundational phase is complete + the container is manually deployed via `agentcore deploy` CLI.
- **US2 (P2)**: T012 **depends on T006** (app.py must exist before it can be updated with logging). T013 has no code dependency on US1. Independently testable with any deployed AgentCore Runtime (manual or CFN).
- **US3 (P3)**: Depends on US1 code existing (app.py container entrypoint) and Dockerfile existing (Phase 2). Does not depend on US2 being complete.

### Within Each User Story

- T006 and T007 are parallel (different files, no cross-dependency)
- T008 depends on T007 (uses client.py types)
- T009 depends on T008 (calls render_chatbot_agentcore) and T004 (uses AgentCoreConfig)
- T010 and T011 are parallel (different test files)
- T014 → T015 → T016 → T017 are sequential (all append to the same template.yaml)

---

## Parallel Opportunities

### Phase 3 (US1) — can launch in parallel

```
Task T006: Create src/agentcore/app.py
Task T007: Create src/agentcore/client.py
Task T010: Create tests/unit/test_agentcore_config.py
Task T011: Create tests/unit/test_agentcore_client.py
```

### Phase 4 (US2) — can run in parallel with Phase 3

```
Task T012: Update src/agentcore/app.py (add logging)
Task T013: Update infra/agentcore/requirements-agent.txt
```

> Note: T012 modifies app.py which T006 creates — coordinate if running concurrently; T012 is an additive change (logging only) so merge conflicts are minimal.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — update dependencies, create directories
2. Complete Phase 2: Foundational — config loader + Dockerfile
3. Complete Phase 3: US1 — container entrypoint, HTTP client, Streamlit integration, unit tests
4. **STOP and VALIDATE**: Log in to Streamlit, send message, confirm streaming response from AgentCore
5. Demo ready

### Incremental Delivery

1. **Phases 1–2** → Foundation and container image ready
2. **Phase 3 (US1)** → Authenticated streaming chat via AgentCore (**MVP demo**)
3. **Phase 4 (US2)** → Observability: structured logs + X-Ray traces in CloudWatch
4. **Phase 5 (US3)** → Full CloudFormation reproducibility (single deploy command)
5. **Phase 6** → Polish, env documentation, test validation

### Feature-Flag Safety

`AGENTCORE_RUNTIME_ARN` acts as the feature flag throughout. When the variable is absent, `app.py` falls back to the existing local agent (feature 003 behaviour). This means:
- `streamlit run app.py` continues to work locally throughout development
- Any phase can be validated without the previous phase being deployed to AWS
