# Tasks: AgentCore Memory Integration

**Input**: Design documents from `/specs/009-agentcore-memory/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: Not explicitly requested in feature specification. Test tasks omitted.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project setup needed — feature extends existing files. This phase is intentionally empty.

**Checkpoint**: Proceed directly to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Modify the agent factory to accept memory parameters — all subsequent phases depend on this.

<!-- sequential -->
- [ ] T001 Modify `create_agent()` in `src/agent/chatbot.py` — add optional parameters `memory_id: str | None = None`, `session_id: str | None = None`, `actor_id: str | None = None`. When `memory_id` is provided (non-None, non-empty string): import `AgentCoreMemoryConfig` from `bedrock_agentcore.memory.integrations.strands.config` and `AgentCoreMemorySessionManager` from `bedrock_agentcore.memory.integrations.strands.session_manager` (lazy imports inside the if-block). Create config with `AgentCoreMemoryConfig(memory_id=memory_id, session_id=session_id, actor_id=actor_id)`. Create session manager with `AgentCoreMemorySessionManager(agentcore_memory_config=config, region_name=os.getenv("AWS_REGION", "us-east-1"))`. Pass `session_manager=session_manager` to the `Agent()` constructor. When `memory_id` is not provided, do not pass `session_manager` (existing behavior). Log whether memory is enabled or disabled. Update docstring and return type — return the session_manager alongside the agent and mcp_clients so callers can manage its lifecycle.

**Checkpoint**: `create_agent()` can be called with and without memory parameters. Without parameters, behavior is unchanged.

---

## Phase 3: User Story 1 — Contextual Conversation Within a Session (Priority: P1) 🎯 MVP

**Goal**: The agent remembers context from earlier turns in the same conversation.

**Independent Test**: Have a multi-turn conversation and verify the agent references earlier context.

### Implementation for User Story 1

<!-- parallel-group: 1 (max 3 concurrent) -->
- [ ] T002 [P] [US1] Update `src/agentcore/app.py` — read `AGENTCORE_MEMORY_ID` from `os.getenv("AGENTCORE_MEMORY_ID")`. Extract `username` from `payload.get("username", "anonymous")`. Import `create_agent` pattern from chatbot but adapt for AgentCore mode: create session manager with context manager (`with AgentCoreMemorySessionManager(...) as session_manager:`) when memory_id is set, pass it to the Agent constructor. Ensure both MCP clients and session manager are properly cleaned up in finally blocks. The session_id is already available from `context.session_id`.
- [ ] T003 [P] [US1] Update `src/agentcore/client.py` — add `username: str = ""` parameter to `invoke_streaming()`. Include it in the JSON payload: `json={"prompt": prompt, "username": username}`. Update docstring.
- [ ] T004 [P] [US1] Update `src/chat/ui.py` — modify `render_chatbot_agentcore()` to accept a `username: str` parameter. Pass it through to `_stream_turn_agentcore()`. Modify `_stream_turn_agentcore()` to accept `username: str` and pass it to `invoke_streaming(... username=username)`.

<!-- sequential -->
- [ ] T005 [US1] Update `app.py` — in the local mode path, read `AGENTCORE_MEMORY_ID` from environment (via `os.getenv("AGENTCORE_MEMORY_ID")`). Get the username from `st.session_state["user"]["username"]` and the session_id from `st.session_state.get("agentcore_session_id", "local-session")`. Pass `memory_id`, `session_id`, and `actor_id` to `create_agent()`. In the AgentCore mode path, pass the username to `render_chatbot_agentcore(... username=user["username"])`.

**Checkpoint**: The agent (both local and AgentCore mode) persists turns to short-term memory and maintains context within a session.

---

## Phase 4: User Story 4 — Infrastructure via CloudFormation (Priority: P1)

**Goal**: The memory resource and IAM permissions are managed through CloudFormation.

**Independent Test**: Deploy the updated stack and verify the memory resource is created.

### Implementation for User Story 4

<!-- sequential -->
- [ ] T006 [US4] Update `infra/agentcore/template.yaml` — add the `AWS::BedrockAgentCore::Memory` resource named `AgentCoreMemory` with all four strategies configured:
  ```
  Strategies:
    - summaryMemoryStrategy:
        name: SessionSummarizer
        namespaces: ["/summaries/{actorId}/{sessionId}/"]
    - userPreferenceMemoryStrategy:
        name: PreferenceLearner
        namespaces: ["/preferences/{actorId}/"]
    - semanticMemoryStrategy:
        name: FactExtractor
        namespaces: ["/facts/{actorId}/"]
    - episodicMemoryStrategy:
        name: EpisodeTracker
        namespaces: ["/episodes/{actorId}/"]
  ```
  Add `AGENTCORE_MEMORY_ID` to the AgentRuntime `EnvironmentVariables` section, referencing the Memory resource ID (`!GetAtt AgentCoreMemory.Id` or similar). Add a new output `AgentCoreMemoryId` exporting the memory resource ID. Note: The AgentExecutionRole already has `AdministratorAccess` managed policy, so no additional IAM permissions are needed for memory API access.

**Checkpoint**: CloudFormation template is valid and includes the memory resource with all four strategies.

---

## Phase 5: User Story 5 — Deployment and Runtime Update (Priority: P1)

**Goal**: Deploy the updated agent to AgentCore Runtime, preserving all config.

**Independent Test**: Deploy and confirm memory works in the deployed agent.

### Implementation for User Story 5

<!-- sequential -->
- [ ] T007 [US5] Upload source zip to S3 — run `zip -r /tmp/source.zip . --exclude '.venv/*' 'specs/*' '.git/*' '.specify/*' '__pycache__/*' '*.pyc' '.env' '*.egg-info/*' '.ruff_cache/*'` from repo root, then `aws s3 cp /tmp/source.zip s3://strands-demo-build-nty7ph9z/source.zip`.
- [ ] T008 [US5] Trigger CodeBuild to rebuild the container image — run `aws codebuild start-build --project-name strands-demo-agent-build` and wait for completion.
- [ ] T009 [US5] Update the CloudFormation stack — run `aws cloudformation update-stack` with the updated template and all existing parameter values preserved (UsePreviousValue=true). Wait for completion.
- [ ] T010 [US5] Force the AgentCore Runtime to pull the new container image — first call `aws bedrock-agentcore-control get-agent-runtime` to retrieve current config, then call `aws bedrock-agentcore-control update-agent-runtime` with ALL existing configuration preserved (authorizerConfiguration, networkConfiguration, protocolConfiguration, roleArn, environmentVariables including the new AGENTCORE_MEMORY_ID). Wait for READY status.
- [ ] T011 [US5] Verify end-to-end — invoke the agent via the Streamlit app (using browser testing) and confirm: (1) multi-turn conversation maintains context (short-term memory), (2) authentication still works, (3) existing tools (Tavily, EKS MCP, AWS MCP) still function.

**Checkpoint**: Deployed agent has working memory. All existing functionality preserved.

---

## Phase 6: User Story 2 — Personalized Experience Across Sessions (Priority: P2)

**Goal**: Returning users get personalized responses from long-term memory.

**Independent Test**: State a preference in one session, start a new session, verify the preference is recalled.

### Implementation for User Story 2

No additional code changes needed — long-term memory extraction and retrieval is handled automatically by the `AgentCoreMemorySessionManager` and the 4 configured strategies. This phase is a validation checkpoint only.

<!-- sequential -->
- [ ] T012 [US2] Validate long-term memory works — have a conversation where the user states preferences (e.g., "I prefer Python" or "I like us-west-2"), wait for background extraction to complete, then start a new session and verify the agent recalls those preferences without being reminded. Note: long-term extraction is asynchronous and may take a few minutes.

**Checkpoint**: All user stories functional. Agent provides personalized responses across sessions.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Empty — no setup needed
- **Phase 2 (Foundational)**: T001 must complete before any user story work
- **Phase 3 (US1 — Session Memory)**: Depends on T001. T002, T003, T004 can run in parallel. T005 depends on T002-T004.
- **Phase 4 (US4 — CloudFormation)**: Depends on Phase 2. Can run in parallel with Phase 3.
- **Phase 5 (US5 — Deployment)**: Depends on Phase 3 AND Phase 4. Sequential deployment steps.
- **Phase 6 (US2 — Cross-Session)**: Depends on Phase 5 (needs deployed agent).

### Parallel Opportunities

- T002, T003, T004 can run in parallel (different files: `app.py`, `client.py`, `ui.py`)
- Phase 3 and Phase 4 can run in parallel (code vs CloudFormation)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001 (Foundational — `chatbot.py`)
2. Complete T002 + T003 + T004 in parallel (AgentCore app + client + UI)
3. Complete T005 (Streamlit app.py integration)
4. **STOP and VALIDATE**: Test locally — agent maintains context within a session

### Full Delivery

1. T001 → T002 + T003 + T004 in parallel → T005 → Code ready
2. T006 in parallel with above → CloudFormation ready
3. T007 → T008 → T009 → T010 → T011 (sequential deployment)
4. T012 (validation of long-term memory)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Total: 12 tasks across 6 phases
- T001 is the key foundational task — modifies `create_agent()` signature
- T010 is the highest-risk task: `update-agent-runtime` must preserve all config
- US3 (per-user isolation) is inherently handled by using Cognito username as actor_id — no separate implementation tasks needed
- Long-term memory (US2) works automatically via the 4 configured strategies — no code beyond what US1 requires
