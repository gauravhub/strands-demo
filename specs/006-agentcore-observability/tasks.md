# Tasks: Enable AgentCore Observability

**Input**: Design documents from `/specs/006-agentcore-observability/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, quickstart.md

**Tests**: Not requested — no test tasks generated.

**Organization**: Tasks grouped by user story. This feature spans CloudFormation (IaC), AWS CLI (API-only toggles), and container dependency changes. No application code changes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (CloudFormation + Container Dependency)

**Purpose**: Update CloudFormation template with Transaction Search, log groups, and IAM. Update container dependency for OTEL.

<!-- sequential -->
- [x] T001 Add observability resources to /home/dhamijag/playground/strands-demo/infra/agentcore/template.yaml — (a) `AWS::Logs::ResourcePolicy` granting X-Ray write access to `aws/spans` and `/aws/application-signals/data`, (b) `AWS::XRay::TransactionSearchConfig` with IndexingPercentage: 100, (c) three `AWS::Logs::LogGroup` resources with RetentionInDays: 30 and DeletionPolicy: Delete: Runtime application logs `/aws/vendedlogs/bedrock-agentcore/runtimes/${AgentRuntimeId}/application-logs`, Runtime usage logs `/aws/vendedlogs/bedrock-agentcore/runtimes/${AgentRuntimeId}/usage-logs`, Identity application logs `/aws/vendedlogs/bedrock-agentcore/identity/application-logs`. Also add an output `IdentityArn` for the Identity resource ARN if available from the Runtime
- [x] T002 [P] Replace `strands-agents>=0.1.0` with `strands-agents[otel]>=0.1.0` in /home/dhamijag/playground/strands-demo/infra/agentcore/requirements-agent.txt to enable Strands-specific OTEL spans (agent loop, LLM call, tool call)
- [x] T003 Upload updated source zip to S3 by running `zip -r source.zip . --exclude '.venv/*' 'specs/*' '.git/*' && aws s3 cp source.zip s3://${BUILD_SOURCE_BUCKET}/source.zip` — this ensures CodeBuild uses the updated `requirements-agent.txt` with `strands-agents[otel]`

---

## Phase 2: Foundational (Stack Deploy + Container Rebuild)

**Purpose**: Deploy updated CloudFormation stack and rebuild container image — BLOCKS all observability CLI tasks

**⚠️ CRITICAL**: Transaction Search must be active and container must be rebuilt before enabling tracing/log delivery

<!-- sequential -->
- [x] T004 Deploy the updated CloudFormation stack by running `aws cloudformation update-stack --stack-name strands-demo-agentcore --template-body file://infra/agentcore/template.yaml --parameters ParameterKey=CognitoUserPoolId,UsePreviousValue=true ParameterKey=CognitoClientId,UsePreviousValue=true ParameterKey=CognitoRegion,UsePreviousValue=true ParameterKey=AnthropicApiKey,UsePreviousValue=true ParameterKey=TavilyApiKey,UsePreviousValue=true ParameterKey=BuildSourceBucket,UsePreviousValue=true ParameterKey=BuildSourceKey,UsePreviousValue=true ParameterKey=ImageTag,UsePreviousValue=true --capabilities CAPABILITY_NAMED_IAM` and wait for completion. This creates Transaction Search config and log groups. **Note**: The `TriggerImageBuild` custom resource only fires on Create or property-change to its own properties — adding unrelated resources will NOT automatically trigger a CodeBuild rebuild. T015 handles manual CodeBuild trigger if needed
- [x] T005 Verify Transaction Search is active by running `aws xray get-trace-segment-destination` — expected output includes `"Destination": "CloudWatchLogs"` and `"Status": "ACTIVE"`. If not active, fall back to CLI commands documented in /home/dhamijag/playground/strands-demo/specs/006-agentcore-observability/quickstart.md Step 1 fallback section
- [x] T005a Extract stack outputs by running `aws cloudformation describe-stacks --stack-name strands-demo-agentcore --query 'Stacks[0].Outputs'` and set shell variables: `RUNTIME_ID`, `RUNTIME_ARN` from outputs AgentRuntimeId and AgentRuntimeArn. For `IDENTITY_ARN`, derive from the Runtime resource or use `aws bedrock-agent-core get-agent-runtime --agent-runtime-id ${RUNTIME_ID}` to retrieve associated Identity ARN

**Checkpoint**: Transaction Search active, log groups created, stack outputs extracted — ready for per-resource observability

---

## Phase 3: User Story 1 — Runtime Traces Visible in CloudWatch (Priority: P1) 🎯 MVP

**Goal**: Enable tracing on the AgentCore Runtime so agent invocations produce visible traces and spans in CloudWatch GenAI Observability

**Independent Test**: Invoke the agent via the Streamlit app, then open CloudWatch GenAI Observability → Agents View and confirm `strands_demo_agent` appears with traces, spans, and runtime metrics

### Implementation for User Story 1

<!-- sequential -->
- [x] T006 [US1] Enable tracing on the AgentCore Runtime resource by running `aws bedrock-agent-core update-agent-runtime --agent-runtime-id ${RUNTIME_ID} --tracing-configuration '{"enabled": true}'` — if the CLI does not support this flag, use the equivalent boto3 call or check the AgentCore SDK docs for the correct API. Document the exact command used in /home/dhamijag/playground/strands-demo/specs/006-agentcore-observability/quickstart.md Step 2
- [x] T007 [US1] Configure trace delivery for the Runtime by running the 3-step vended logs pattern: (1) `aws logs put-delivery-source --name strands-demo-runtime-traces --resource-arn ${RUNTIME_ARN} --log-type TRACES`, (2) `aws logs put-delivery-destination --name strands-demo-runtime-traces-dest --delivery-destination-type XRAY`, (3) `aws logs create-delivery --delivery-source-name strands-demo-runtime-traces --delivery-destination-arn <dest-arn>`. Document exact commands in /home/dhamijag/playground/strands-demo/specs/006-agentcore-observability/quickstart.md Step 3g-3i
- [x] T008 [US1] Smoke test: invoke the agent via the deployed Streamlit app or direct AgentCore API call, wait 5 minutes, then verify traces appear in CloudWatch Transaction Search and the agent is listed in CloudWatch GenAI Observability Agents View with runtime metrics (invocations, latency)

**Checkpoint**: Runtime tracing enabled — agent invocations produce visible traces in CloudWatch

---

## Phase 4: User Story 2 — Runtime Application Logs in CloudWatch (Priority: P2)

**Goal**: Configure application and usage log delivery for the Runtime so structured logs appear in CloudWatch

**Independent Test**: Invoke the agent, then check CloudWatch Logs groups for application logs (request/response payloads, session IDs, trace IDs) and usage logs (CPU, memory)

### Implementation for User Story 2

<!-- sequential -->
- [x] T009 [US2] Configure Runtime APPLICATION_LOGS delivery by running: (1) `aws logs put-delivery-source --name strands-demo-runtime-app-logs --resource-arn ${RUNTIME_ARN} --log-type APPLICATION_LOGS`, (2) `aws logs put-delivery-destination --name strands-demo-runtime-app-logs-dest --delivery-destination-type CWL --delivery-destination-configuration destinationResourceArn=<log-group-arn>`, (3) `aws logs create-delivery --delivery-source-name strands-demo-runtime-app-logs --delivery-destination-arn <dest-arn>`. Use the log group ARN from the CFN stack output for the application logs group
- [x] T010 [US2] Configure Runtime USAGE_LOGS delivery by running the same 3-step pattern with `--log-type USAGE_LOGS`, source name `strands-demo-runtime-usage-logs`, and the usage logs group ARN from the CFN stack
- [x] T011 [US2] Smoke test: invoke the agent, then check CloudWatch Logs groups — verify application logs contain request payload, response payload, session ID, and trace ID; verify usage logs contain session-level CPU/memory data

**Checkpoint**: Runtime log delivery active — structured application and usage logs in CloudWatch

---

## Phase 5: User Story 3 — Identity Observability Enabled (Priority: P3)

**Goal**: Enable tracing and log delivery for Identity (WorkloadIdentity) resources so authentication/authorization operations are visible in CloudWatch

**Independent Test**: Invoke the agent with a valid Cognito JWT, then check CloudWatch for Identity spans and Identity authorization metrics in the Bedrock-AgentCore CloudWatch Metrics namespace

### Implementation for User Story 3

<!-- sequential -->
- [x] T012 [US3] Enable Identity tracing by running `aws bedrock-agent-core update-agent-runtime --agent-runtime-id ${RUNTIME_ID} --identity-tracing-configuration '{"enabled": true}'` — if the CLI does not support this, use boto3 or the AgentCore SDK equivalent
- [x] T013 [US3] Configure Identity APPLICATION_LOGS delivery by running: (1) `aws logs put-delivery-source --name strands-demo-identity-app-logs --resource-arn ${IDENTITY_ARN} --log-type APPLICATION_LOGS`, (2) `aws logs put-delivery-destination --name strands-demo-identity-app-logs-dest --delivery-destination-type CWL --delivery-destination-configuration destinationResourceArn=<identity-log-group-arn>`, (3) `aws logs create-delivery --delivery-source-name strands-demo-identity-app-logs --delivery-destination-arn <dest-arn>`. Use the Identity log group ARN from the CFN stack
- [x] T014 [US3] Smoke test: invoke the agent with Cognito JWT auth, then verify (1) Identity spans appear in `aws/spans` log group showing authorization operations, (2) Identity authorization metrics (WorkloadAccessTokenFetchSuccess/Failure/Throttle) appear in CloudWatch Metrics under the Bedrock-AgentCore namespace

**Checkpoint**: Identity observability enabled — auth operations visible in CloudWatch traces, logs, and metrics

---

## Phase 6: User Story 4 — Agent OTEL Instrumentation in Container (Priority: P4)

**Goal**: Verify that the rebuilt container with `strands-agents[otel]` emits Strands-specific OTEL spans (agent loop, LLM call, tool call) visible in CloudWatch

**Independent Test**: Invoke the agent on the deployed Runtime with the updated container, then verify CloudWatch shows detailed Strands-level spans nested under the Runtime invocation span

### Implementation for User Story 4

<!-- sequential -->
- [x] T015 [US4] Verify the CodeBuild triggered by the CFN stack update (T004) completed successfully by running `aws codebuild list-builds-for-project --project-name strands-demo-agent-build --sort-order DESCENDING` and checking the latest build status is SUCCEEDED. If the build failed or was not triggered, manually trigger with `aws codebuild start-build --project-name strands-demo-agent-build` after uploading the updated source zip
- [x] T016 [US4] Smoke test: invoke the agent via the Streamlit app, then open CloudWatch trace details and verify Strands-specific spans are present — look for spans named for agent invocation, LLM model call, and tool call (e.g., tavily). Confirm these are nested under the Runtime invocation span. Also verify session ID correlation if OpenTelemetry baggage is set

**Checkpoint**: Agent OTEL instrumentation active — full trace depth from Runtime invocation down to individual LLM/tool calls

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and final validation

<!-- parallel-group: 2 (max 3 concurrent) -->
- [x] T017 [P] Update /home/dhamijag/playground/strands-demo/specs/006-agentcore-observability/quickstart.md with any corrected CLI commands, actual ARNs, or adjustments discovered during implementation
- [x] T018 [P] Run full end-to-end validation: invoke the agent, then verify ALL observability channels simultaneously — (1) traces in Transaction Search, (2) Strands OTEL spans in trace details, (3) Runtime application logs, (4) Runtime usage logs, (5) Identity spans, (6) Identity metrics in CloudWatch Metrics. Confirm existing functionality (Cognito login, chat, AgentCore routing) works without regression

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately. T001 (template.yaml) is sequential, T002 (requirements-agent.txt) can run in parallel with T001. T003 (source zip upload) depends on both T001 and T002.
- **Foundational (Phase 2)**: Depends on Phase 1 (CFN template and source zip must be updated before deploying). T004 → T005 → T005a sequential.
- **User Story 1 (Phase 3)**: Depends on Phase 2 (Transaction Search must be active). T006 → T007 → T008 sequential.
- **User Story 2 (Phase 4)**: Depends on Phase 2 (log groups must exist). Can run in parallel with US1 but shown sequentially for clarity. T009 → T010 → T011 sequential.
- **User Story 3 (Phase 5)**: Depends on Phase 2 (log groups must exist). Can run in parallel with US1/US2. T012 → T013 → T014 sequential.
- **User Story 4 (Phase 6)**: Depends on Phase 2 (container must be rebuilt). T015 → T016 sequential.
- **Polish (Phase 7)**: Depends on all user stories. T017 and T018 are parallel.

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 — delivers Runtime tracing (MVP)
- **US2 (P2)**: Depends on Phase 2 — delivers Runtime log delivery (can run in parallel with US1)
- **US3 (P3)**: Depends on Phase 2 — delivers Identity observability (can run in parallel with US1/US2)
- **US4 (P4)**: Depends on Phase 2 — validates container OTEL (can run in parallel with US1/US2/US3)

**Note**: US1-US4 are independent after Phase 2 — they configure different observability channels and can theoretically run in parallel. Shown sequentially for implementation clarity.

### Parallel Opportunities

- Phase 1: T001 (template.yaml) and T002 (requirements-agent.txt) can run in parallel (different files). T003 (source zip upload) runs after both complete
- Phase 3-6: User stories are independent after Phase 2 and could run concurrently
- Phase 7: Documentation and validation tasks (T017, T018) can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (update CFN template + requirements-agent.txt)
2. Complete Phase 2: Foundational (deploy stack, verify Transaction Search)
3. Complete Phase 3: User Story 1 (enable Runtime tracing, smoke test)
4. **STOP and VALIDATE**: Traces visible in CloudWatch GenAI Observability
5. Proceed to US2 (logs), US3 (Identity), US4 (OTEL verification) for full observability

### Incremental Delivery

1. Setup + Foundational → Transaction Search active, log groups created, container rebuilt
2. User Story 1 → Runtime tracing enabled (MVP!)
3. User Story 2 → Runtime application + usage logs flowing
4. User Story 3 → Identity tracing + logs enabled
5. User Story 4 → Strands OTEL spans verified
6. Polish → Full end-to-end validation, documentation finalized

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Zero application code changes — this feature is infrastructure configuration + container dependency only
- CLI commands in tasks reference variables (${RUNTIME_ID}, ${RUNTIME_ARN}, ${IDENTITY_ARN}) — substitute with actual values from CFN stack outputs
- Log group names use the AgentCore vended logs convention: `/aws/vendedlogs/bedrock-agentcore/...`
- Manual Console steps are explicitly prohibited — all steps are scriptable CLI commands
- Commit after Phase 1 completes (modified files: template.yaml, requirements-agent.txt)
