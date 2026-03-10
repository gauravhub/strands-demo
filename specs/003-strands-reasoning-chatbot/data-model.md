# Data Model: Strands Reasoning Chatbot

**Branch**: `003-strands-reasoning-chatbot` | **Date**: 2026-03-09

All state is held **in-memory** in `st.session_state` (per browser tab, reset on reload). No database or persistent storage.

---

## Entities

### ChatMessage

Represents a single turn in the conversation.

| Field | Type | Notes |
|-------|------|-------|
| `role` | `Literal["user", "assistant"]` | Sender of the message |
| `content` | `str` | Text of the message |
| `reasoning` | `str \| None` | Reasoning/thinking tokens (assistant only; `None` if not produced or user turn) |
| `tool_calls` | `list[ToolCall]` | Tool invocations during this turn (empty list if none) |
| `timestamp` | `datetime` | UTC time message was created |
| `error` | `str \| None` | Inline error notice if stream failed mid-way; `None` otherwise |

**Validation rules**:
- `role` must be `"user"` or `"assistant"` (no other values)
- `content` may be empty string if streaming errored before any text was received
- `reasoning` must be `None` for user turns
- `tool_calls` must be empty list for user turns

---

### ToolCall

Represents one invocation of a tool by the agent during a response turn.

| Field | Type | Notes |
|-------|------|-------|
| `tool_use_id` | `str` | Unique ID assigned by the model (e.g., `"toolu_..."`) |
| `name` | `str` | Tool name (e.g., `"tavily_search"`) |
| `input` | `dict` | Input arguments passed to the tool |
| `result` | `str \| None` | Tool output text; `None` while tool is still executing |

**Validation rules**:
- `name` must be non-empty
- `input` is a raw dict (not serialized string) once streaming input is complete
- `result` transitions from `None` → populated string when `tool_result` event is received

---

### ConversationSession

The in-memory conversation state for one browser tab.

| Field | Type | Notes |
|-------|------|-------|
| `messages` | `list[ChatMessage]` | Ordered list of all turns, oldest first |
| `is_streaming` | `bool` | `True` while a response is actively streaming |

**Constraints**:
- Initialised empty on first page load; reset to empty on full page reload
- `is_streaming` controls input field enabled/disabled state
- Up to 20+ turns supported (spec SC-005); no enforced hard cap

---

## Session State Schema

Keys written to `st.session_state`:

| Key | Type | Description |
|-----|------|-------------|
| `messages` | `list[dict]` | Serialised `ChatMessage` list (role, content, reasoning, tool_calls, error) |
| `is_streaming` | `bool` | Lock flag while streaming |

---

## State Transitions

```
ConversationSession:
  IDLE  ──[user submits]──►  STREAMING  ──[stream complete]──►  IDLE
                                         ──[stream error]──────►  IDLE (with error appended to last message)
```

```
ChatMessage (assistant turn):
  PENDING ──[first text/reasoning token]──► IN_PROGRESS ──[stop event]──► COMPLETE
                                                          ──[error mid-stream]──► PARTIAL_ERROR
```

```
ToolCall:
  CALLING ──[tool_use_stream events]──► INPUT_STREAMING ──[tool_result event]──► COMPLETE
```
