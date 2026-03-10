# Implementation Plan: Strands Reasoning Chatbot

**Branch**: `003-strands-reasoning-chatbot` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-strands-reasoning-chatbot/spec.md`

## Summary

Build a Strands agent chatbot powered by Claude Sonnet 4.6 (via direct Anthropic API) with extended thinking enabled, Tavily web search as its tool, and a Streamlit UI that streams and displays reasoning tokens, tool calls, and final responses in three visually distinct sections. The chatbot is gated behind the existing Cognito authentication flow from feature 002.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `strands-agents>=0.1.0` (includes `AnthropicModel`), `strands-agents-tools>=0.1.0` (includes `tavily`), `streamlit>=1.35.0`, `python-dotenv>=1.0.0`
**Storage**: None — all state held in `st.session_state` (in-memory, per tab)
**Testing**: `pytest>=8.0`
**Target Platform**: Local development server (Streamlit, `streamlit run app.py`)
**Project Type**: Web application (Streamlit single-page app)
**Performance Goals**: First streamed token within 3 seconds of submit (SC-001)
**Constraints**: No new top-level dependencies needed; no persistent storage; Cognito auth mandatory
**Scale/Scope**: Single authenticated user per session; 20+ turn conversation history

## Constitution Check

*GATE: Must pass before implementation. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | ✅ PASS | Minimal new files; no new dependencies; reuses existing auth |
| II. Iterative & Independent Delivery | ✅ PASS | Feature is independently runnable; app remains launchable at all times |
| III. Python-Native Patterns | ✅ PASS | Python 3.11+, type hints, `pyproject.toml`, `uv` |
| IV. Security by Design | ✅ PASS | Cognito auth enforced (FR-010); `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` from env; no hardcoded secrets |
| V. Observability & Debuggability | ✅ PASS | Streaming events surfaced in UI; structured `logging` with `LOG_LEVEL` env var; no silent failures |

**Result**: All gates PASS. Proceed to implementation.

## Project Structure

### Documentation (this feature)

```text
specs/003-strands-reasoning-chatbot/
├── plan.md              # This file
├── research.md          # Phase 0 research decisions
├── data-model.md        # Entity and session state schema
├── quickstart.md        # Setup and run instructions
├── contracts/
│   └── ui-contract.md   # Streamlit UI behavioural contract
└── tasks.md             # Phase 2 output (/speckit.tasks — not yet created)
```

### Source Code

```text
src/
├── __init__.py
├── auth/                        # Existing — no changes
│   ├── __init__.py
│   ├── config.py
│   ├── oauth.py
│   └── session.py
├── agent/                       # NEW
│   ├── __init__.py
│   ├── model.py                 # AnthropicModel factory (extended thinking config)
│   └── chatbot.py               # Agent instantiation with Tavily tool
└── chat/                        # NEW
    ├── __init__.py
    └── ui.py                    # Streamlit chatbot UI (streaming display, session state)

tests/
└── (no new test files — tests not requested for this feature)

app.py                           # MODIFIED: replace show_main_app() with chatbot UI
.env                             # MODIFIED: add ANTHROPIC_API_KEY, TAVILY_API_KEY
```

**Structure Decision**: Single-project layout extending the existing `src/` tree. New `agent/` module encapsulates model and agent setup. New `chat/` module encapsulates all Streamlit UI rendering and session state. `app.py` delegates to `chat/ui.py` for the authenticated view.

## Implementation Approach

### Agent Module (`src/agent/`)

**`model.py`** — Factory function returning a configured `AnthropicModel`:
```python
from strands.models.anthropic import AnthropicModel

def create_model() -> AnthropicModel:
    return AnthropicModel(
        client_args={"api_key": os.getenv("ANTHROPIC_API_KEY")},
        max_tokens=16000,
        model_id="claude-sonnet-4-6",
        params={"thinking": {"type": "enabled", "budget_tokens": 10000}},
    )
```
Raises `EnvironmentError` if `ANTHROPIC_API_KEY` is not set.

**`chatbot.py`** — Factory function returning a configured `Agent`:
```python
from strands import Agent
from strands_tools import tavily

def create_agent() -> Agent:
    return Agent(model=create_model(), tools=[tavily])
```
Raises `EnvironmentError` if `TAVILY_API_KEY` is not set (validated at import).

### Chat UI Module (`src/chat/`)

**`ui.py`** — All Streamlit rendering logic:

1. **`init_session()`** — Initialise `st.session_state.messages = []` and `is_streaming = False` on first load.
2. **`render_chat_history()`** — Iterate `messages` and render each turn (user bubble + assistant turn with three sections).
3. **`render_assistant_turn(msg)`** — Render three sections for an assistant message:
   - `st.expander("🔍 Reasoning")` with reasoning text or "No reasoning for this response."
   - `st.expander("🛠 Tools Used")` with tool call blocks (hidden if no tools)
   - Final response text in the main flow
4. **`run_streaming_turn(agent, user_message)`** — Async function wrapping `agent.stream_async()`:
   - Discriminates event types (reasoning / tool_use_stream / tool_result / data / stop)
   - Updates live `st.empty()` placeholders incrementally
   - On error: preserves partial content, appends inline error notice
   - Sets `is_streaming = False` on completion or error
5. **`render_input(agent)`** — Text input + Submit button (disabled during `is_streaming`); calls `asyncio.run(run_streaming_turn(...))` on submit.

### app.py Changes

Replace the body of `show_main_app()` with a call to `src.chat.ui.render_chatbot()`. Auth routing logic remains unchanged.

### Logging

All agent module functions emit structured `logging` at `INFO` level:
- Agent creation (model_id, tools)
- Stream start / stop (with token counts from `stop` event usage metrics)
- Tool invocations (tool name, input summary)
- Errors (full exception with traceback at `ERROR` level)

Log level configurable via `LOG_LEVEL` env var.

## Complexity Tracking

No constitution violations. No complexity justification table needed.
