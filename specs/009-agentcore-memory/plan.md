# Implementation Plan: AgentCore Memory Integration

**Branch**: `009-agentcore-memory` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-agentcore-memory/spec.md`

## Summary

Integrate Amazon Bedrock AgentCore Memory into the Strands Demo agent using `AgentCoreMemorySessionManager` from the `bedrock-agentcore` SDK. The session manager plugs into the Strands Agent via the `session_manager` parameter and automatically handles short-term memory persistence (per-turn via `MessageAddedEvent` hook) and long-term memory retrieval (preferences, facts, summaries, episodes injected as `<user_context>` blocks). A CloudFormation `AWS::BedrockAgentCore::Memory` resource provisions the memory store with all four built-in strategies. Actor ID is the Cognito username (passed in the invocation payload from the Streamlit UI). Session ID is the existing UUID from `st.session_state`.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: strands-agents>=0.1.0, bedrock-agentcore>=0.1.0 (already in requirements-agent.txt), boto3
**Storage**: AgentCore Memory (managed service) — short-term events + long-term extracted records
**Testing**: pytest
**Target Platform**: AWS AgentCore Runtime (ARM64 container) + Streamlit Cloud (local mode)
**Project Type**: Web service (Streamlit frontend + AgentCore backend)
**Performance Goals**: Memory retrieval adds <2 seconds overhead per turn
**Constraints**: Must preserve existing MCP tool integration; graceful degradation when memory not configured
**Scale/Scope**: Per-user memory isolation via Cognito username as actor_id

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | PASS | Uses SDK-provided session manager — no custom memory logic. Single `session_manager` parameter on Agent constructor. |
| II. Iterative & Independent Delivery | PASS | Agent works without memory when `AGENTCORE_MEMORY_ID` is not set (graceful degradation). Feature is additive. |
| III. Python-Native Patterns | PASS | All code is Python 3.11+, uses standard SDK patterns. |
| IV. Security by Design | PASS | Memory isolated per user via Cognito username as actor_id. No hardcoded secrets — memory_id from env var. |
| V. Observability & Debuggability | PASS | Session manager logs memory operations. Existing OTEL instrumentation captures memory-related calls. |

## Project Structure

### Documentation (this feature)

```text
specs/009-agentcore-memory/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── tasks.md             # Phase 2 output (created by /speckit.tasks)
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
src/
├── agent/
│   ├── chatbot.py             # MODIFY: Add memory_id/session_id/actor_id params, create session manager
│   ├── mcp_tools.py           # NO CHANGE
│   └── model.py               # NO CHANGE
├── agentcore/
│   ├── app.py                 # MODIFY: Read AGENTCORE_MEMORY_ID, extract username from payload, pass to agent
│   ├── client.py              # MODIFY: Add username param to invoke_streaming, include in payload
│   └── config.py              # NO CHANGE
├── auth/                      # NO CHANGE
└── chat/
    └── ui.py                  # MODIFY: Pass username in render_chatbot_agentcore and _stream_turn_agentcore

app.py                         # MODIFY: Pass memory_id, session_id, actor_id to create_agent() in local mode

infra/agentcore/
├── template.yaml              # MODIFY: Add AWS::BedrockAgentCore::Memory resource, IAM permissions, env var
├── Dockerfile                 # NO CHANGE
└── requirements-agent.txt     # NO CHANGE (bedrock-agentcore already present)
```

**Structure Decision**: Extend existing files in-place. No new files needed.

## Architecture

### Integration Pattern

1. **Agent Factory** (`src/agent/chatbot.py`): Modify `create_agent()` to accept optional `memory_id`, `session_id`, `actor_id`. When `memory_id` is provided:
   - Create `AgentCoreMemoryConfig(memory_id=..., session_id=..., actor_id=...)`
   - Create `AgentCoreMemorySessionManager(agentcore_memory_config=config, region_name=...)`
   - Pass `session_manager=session_manager` to `Agent()` constructor
   - When `memory_id` is not set, omit `session_manager` (agent works without memory)

2. **AgentCore Entrypoint** (`src/agentcore/app.py`): Read `AGENTCORE_MEMORY_ID` from environment. Extract `username` from the invocation payload. Pass to agent creation. Use `with` block for session manager to ensure flush.

3. **Streamlit UI** (`src/chat/ui.py`): Pass `username` field in the invocation payload alongside `prompt`. The username comes from `st.session_state["user"]["username"]`.

4. **AgentCore Client** (`src/agentcore/client.py`): Add `username` parameter to `invoke_streaming()`, include it in the JSON payload sent to the Runtime.

5. **Local Mode** (`app.py`): Read `AGENTCORE_MEMORY_ID` from `.env`, pass it with username and session_id to `create_agent()`.

6. **CloudFormation** (`infra/agentcore/template.yaml`):
   - New `AWS::BedrockAgentCore::Memory` resource with all 4 strategies
   - New `AGENTCORE_MEMORY_ID` environment variable on AgentRuntime (referencing the Memory resource ID)
   - IAM permissions for AgentExecutionRole to call AgentCore Memory APIs

### Actor ID Decision

The Cognito `username` is used as the `actor_id` for memory isolation. In AgentCore mode, the username is passed explicitly in the invocation payload from the Streamlit UI (simpler than decoding the JWT token in the agent code, which would require adding `Authorization` to the header allowlist and `PyJWT` as a dependency). The username is already available in `st.session_state["user"]["username"]` from the Cognito OAuth flow.

Note: The JWT access token does contain `"username"` as a claim, so an alternative approach would be to decode the token in `app.py`. The payload approach was chosen for simplicity (no additional dependencies, no header allowlist configuration).

### Data Flow

```
User Chat → Streamlit UI
    │
    ├─ Local Mode:
    │   create_agent(memory_id=env, session_id=st.session_state, actor_id=username)
    │   Agent(session_manager=AgentCoreMemorySessionManager(...))
    │
    └─ AgentCore Mode:
        payload = {"prompt": "...", "username": "demo_user_1"}
        → AgentCore Runtime → app.py invoke()
            memory_id = os.getenv("AGENTCORE_MEMORY_ID")
            username = payload["username"]
            Agent(session_manager=AgentCoreMemorySessionManager(...))

Session Manager Hooks (automatic):
    MessageAddedEvent → append_message() [persist to short-term]
    MessageAddedEvent → retrieve_customer_context() [inject long-term memories]
    AfterInvocationEvent → _flush_messages() [flush buffer if batching]
```

### Memory Lifecycle

1. **Turn 1**: User sends message → persisted to short-term memory → long-term memory empty (new user)
2. **Turn 2+**: User sends message → long-term memories retrieved and injected → response generated → persisted
3. **Background**: AgentCore Memory asynchronously extracts preferences, facts, summaries, episodes from raw turns
4. **Next Session**: Long-term memories available immediately on first turn

## Complexity Tracking

No constitution violations. No complexity justifications needed.
