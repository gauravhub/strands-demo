# Tasks: Strands Reasoning Chatbot

**Input**: Design documents from `/specs/003-strands-reasoning-chatbot/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ui-contract.md ✅

**Tests**: Not requested in spec — no test tasks generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new module directories and update environment configuration.

- [x] T001 Create `src/agent/__init__.py` (empty module marker)
- [x] T002 [P] Create `src/chat/__init__.py` (empty module marker)
- [x] T003 [P] Add `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` entries to `.env.example` with placeholder values and comments explaining where to obtain each key

**Checkpoint**: Directory structure exists; env var docs updated.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Agent and session infrastructure that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Implement `create_model()` factory in `src/agent/model.py` — instantiates `AnthropicModel` with `model_id="claude-sonnet-4-6"`, `max_tokens=16000`, `params={"thinking": {"type": "enabled", "budget_tokens": 10000}}`; reads `ANTHROPIC_API_KEY` from env; raises `EnvironmentError` with clear message if key is absent
- [x] T005 [P] Implement `create_agent()` factory in `src/agent/chatbot.py` — instantiates `Agent(model=create_model(), tools=[tavily])`; validates `TAVILY_API_KEY` is set (check `os.getenv`); raises `EnvironmentError` with clear message if absent; import: `from strands import Agent`, `from strands_tools import tavily`, `from src.agent.model import create_model`
- [x] T006 Implement `init_session()` in `src/chat/ui.py` — initialises `st.session_state.messages = []` and `st.session_state.is_streaming = False` if keys are not already present; call this at top of `render_chatbot()` entry point

**Checkpoint**: `create_agent()` can be called; session state initialises without error.

---

## Phase 3: User Story 1 — Basic Conversational Chat (Priority: P1) 🎯 MVP

**Goal**: User can type a message and receive a streamed text response. Conversation history persists across turns within the session.

**Independent Test**: Open app → log in → type "Hello, what can you do?" → verify response streams token by token in the chat window. Send a follow-up message and verify the agent references prior context.

### Implementation

- [x] T007 [US1] Implement `render_chat_history()` in `src/chat/ui.py` — iterates `st.session_state.messages` and renders each turn: user messages in `st.chat_message("user")`, assistant messages in `st.chat_message("assistant")` showing only `content` (no reasoning/tools yet — those come in US2/US3); renders inline error notice from `msg["error"]` if present
- [x] T008 [US1] Implement `run_streaming_turn(agent, user_message: str)` async function in `src/chat/ui.py` — initialises a new assistant message dict `{"role": "assistant", "content": "", "reasoning": "", "tool_calls": [], "error": None}` and appends to `st.session_state.messages`; iterates `agent.stream_async(user_message)`; on `"data"` event: accumulates text into `content`; on `"stop"` event: ends loop; on any exception mid-stream: appends `"⚠️ Response interrupted: {reason}"` to `msg["error"]`; sets `st.session_state.is_streaming = False` in a `finally` block
- [x] T009 [US1] Implement `render_input(agent)` in `src/chat/ui.py` — renders `st.chat_input("Message...")` disabled when `st.session_state.is_streaming == True`; on submit: appends user message to `st.session_state.messages`, sets `is_streaming = True`, calls `asyncio.run(run_streaming_turn(agent, user_message))`; import `asyncio`
- [x] T010 [US1] Implement `render_chatbot(agent)` entry-point function in `src/chat/ui.py` — calls `init_session()`, then `render_chat_history()`, then `render_input(agent)`
- [x] T011 [US1] Update `show_main_app()` in `app.py` — replace the placeholder `st.info(...)` body with agent instantiation and call to `render_chatbot(agent)`; wrap `create_agent()` in try/except `EnvironmentError` to show `st.error(...)` and `st.stop()` if env vars missing; import `from src.agent.chatbot import create_agent` and `from src.chat.ui import render_chatbot`
- [x] T012 [US1] Update app startup validation in `app.py` — after `load_dotenv()` and before `st.set_page_config(...)`, check that `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` are set; show `st.error(...)` and `st.stop()` if either is missing (same pattern as existing Cognito config check)

**Checkpoint**: `streamlit run app.py` → log in → chat works with streamed responses → follow-up messages use conversation context → empty submit shows no error.

---

## Phase 4: User Story 2 — Reasoning Token Visibility (Priority: P2)

**Goal**: Every assistant turn shows a "Reasoning" section. When the agent reasons, tokens stream in real time. When no reasoning occurs, the section shows "No reasoning for this response."

**Independent Test**: Submit "Solve step by step: if 17 apples are split equally among 3 baskets with remainder kept aside, how many apples per basket and how many remain?" → verify a "Reasoning" section appears and streams thinking tokens before the final answer appears.

### Implementation

- [x] T013 [US2] Update `run_streaming_turn()` in `src/chat/ui.py` — add handler for reasoning events: `if event.get("reasoning") and "reasoningText" in event: msg["reasoning"] += event["reasoningText"]`; update the live reasoning placeholder inside the stream loop; reasoning placeholder renders inside `st.expander("🔍 Reasoning", expanded=True)` using `st.empty()`
- [x] T014 [US2] Update `render_chat_history()` in `src/chat/ui.py` — inside the assistant `st.chat_message("assistant")` block, always render a `st.expander("🔍 Reasoning")` section: show `msg["reasoning"]` if non-empty, else show the italic text *"No reasoning for this response."*; reasoning section renders before the response text

**Checkpoint**: Every assistant turn now shows the Reasoning expander — streaming during live response, finalised on completion, "No reasoning" placeholder for trivial replies.

---

## Phase 5: User Story 3 — Tool Call Visibility (Priority: P3)

**Goal**: When the agent invokes the Tavily web search tool, a "Tools Used" section appears showing the tool name, input query, and result. If no tools are used, no Tools section appears.

**Independent Test**: Submit "What is the latest news about AWS Strands Agents?" → verify a "🛠 Tools Used" section appears showing `tavily_search`, the search query, and the result returned before the final response.

### Implementation

- [x] T015 [US3] Update `run_streaming_turn()` in `src/chat/ui.py` — add handlers for tool events:
  - `tool_use_stream`: extract `event["current_tool_use"]` — update or create a tool call entry in `msg["tool_calls"]` by `tool_use_id`; update the live tools placeholder
  - `tool_result`: find matching tool call by `tool_use_id` and populate its `result` field; update the live tools placeholder
- [x] T016 [US3] Update `render_chat_history()` in `src/chat/ui.py` — inside the assistant `st.chat_message("assistant")` block, render `st.expander("🛠 Tools Used")` only when `msg["tool_calls"]` is non-empty; for each tool call render: tool name as bold header, input as `st.json(tool_call["input"])`, result as `st.markdown(tool_call["result"])` (or "Awaiting result…" if result is None); tools section renders between Reasoning and Response sections

**Checkpoint**: Asking a current-events question triggers tool section display with name, input, and result. Non-web-search questions show no Tools section.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Observability, constitution compliance, and final validation.

- [x] T017 Add structured `logging` calls to `src/agent/model.py` — log at `INFO`: model_id and thinking config on `create_model()` call
- [x] T018 [P] Add structured `logging` calls to `src/agent/chatbot.py` — log at `INFO`: agent creation with model_id and tool names; log at `ERROR` with full traceback on any exception during agent creation (note: per-invocation tool logging happens in the streaming loop — see T020)
- [x] T019 [P] Add `LOG_LEVEL` env var support in `app.py` — update `logging.basicConfig(level=...)` to read from `os.getenv("LOG_LEVEL", "INFO")`; add `LOG_LEVEL` entry to `.env.example`
- [x] T020 Add `run_streaming_turn()` logging in `src/chat/ui.py` — log at `INFO`: stream start (user message length), each tool invocation (tool name and input summary from `tool_use_stream` events), stream stop (token counts from `stop` event usage metrics); log at `ERROR`: any mid-stream exception with full traceback
- [x] T021 Validate end-to-end against `quickstart.md` — follow all steps in `specs/003-strands-reasoning-chatbot/quickstart.md`; confirm: (1) app starts, (2) unauthenticated access redirects to login, (3) login works, (4) chat works with streamed responses, (5) time-to-first-token is under 3 seconds (note submit time vs first visible token), (6) Reasoning section appears on complex query, (7) Tools section appears on web-search query, (8) inline error notice appears when ANTHROPIC_API_KEY is temporarily unset and request is attempted

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — delivers MVP
- **Phase 4 (US2)**: Depends on Phase 3 — adds reasoning display
- **Phase 5 (US3)**: Depends on Phase 3 — adds tool display (US2 and US3 are independent of each other)
- **Phase 6 (Polish)**: Depends on all story phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational phase only — no story dependencies
- **US2 (P2)**: Depends on US1 (extends `run_streaming_turn` and `render_chat_history`)
- **US3 (P3)**: Depends on US1 (extends same functions); independent of US2

### Parallel Opportunities

- T001, T002, T003 — all parallel (different files)
- T004, T005 — parallel (different files; T006 depends on both)
- T007, T008, T009 — T008 before T009 (T009 calls T008); T007 and T008 parallel
- T013 and T014 — T013 before T014 (rendering depends on data populated by stream loop)
- T017, T018, T019 — all parallel (different files)

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch in parallel:
Task: T004 — "Implement create_model() in src/agent/model.py"
Task: T005 — "Implement create_agent() in src/agent/chatbot.py"
# Then sequentially:
Task: T006 — "Implement init_session() in src/chat/ui.py"
```

## Parallel Example: Phase 6 (Polish)

```bash
# Launch in parallel:
Task: T017 — "Add logging to src/agent/model.py"
Task: T018 — "Add logging to src/agent/chatbot.py"
Task: T019 — "Add LOG_LEVEL env var support in app.py"
# Then sequentially:
Task: T020 — "Add stream logging to src/chat/ui.py"
Task: T021 — "End-to-end quickstart validation"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T006)
3. Complete Phase 3: User Story 1 (T007–T012)
4. **STOP and VALIDATE**: Log in, chat, verify streaming and conversation memory
5. Demo and get feedback before adding US2/US3

### Incremental Delivery

1. Setup + Foundational → agent and session infrastructure ready
2. US1 (T007–T012) → working chatbot MVP with streamed responses
3. US2 (T013–T014) → reasoning tokens visible in every response
4. US3 (T015–T016) → tool calls visible when web search is triggered
5. Polish (T017–T021) → observability and final validation

---

## Notes

- [P] tasks = different files, no incomplete-task dependencies — safe to run concurrently
- Each user story phase ends with a **Checkpoint** — verify independently before proceeding
- `run_streaming_turn()` grows incrementally across US1→US2→US3; each phase adds event handlers without breaking prior ones
- Cognito auth flow (app.py routing) is untouched — this feature only modifies `show_main_app()` body
- Commit after each checkpoint at minimum
