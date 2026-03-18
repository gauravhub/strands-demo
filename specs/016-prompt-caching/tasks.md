# Tasks: Anthropic Prompt Caching

**Input**: Design documents from `/specs/016-prompt-caching/`
**Prerequisites**: plan.md (required), spec.md (required), research.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 — Reduced Cost on Repeated Prompts (Priority: P1)

**Goal**: Enable prompt caching on system prompt and tool definitions.

**Independent Test**: Invoke the agent twice. Second invocation should show cache_read_input_tokens > 0 in API response.

<!-- sequential -->
- [x] T001 [US1] In src/agent/model.py, create a subclass `CachedAnthropicModel(AnthropicModel)` that overrides `format_request()`. The override should: (1) call `super().format_request()` to get the base request dict, (2) if `system` key exists and is a string, convert it to a list with one TextBlockParam dict: `[{"type": "text", "text": <original string>, "cache_control": {"type": "ephemeral", "ttl": "1h"}}]`, (3) if `tools` list is non-empty, add `"cache_control": {"type": "ephemeral", "ttl": "1h"}` to the last tool dict, (4) return the modified request. Update `create_model()` to return `CachedAnthropicModel` instead of `AnthropicModel`. Add a logger.info line confirming caching is enabled. Keep all existing model configuration (model_id, max_tokens, thinking params) unchanged.

---

## Phase 2: User Story 2 — Cache Performance Observability (Priority: P2)

**Goal**: Log cache metrics so developers can verify caching is working.

**Independent Test**: Check application logs after an agent invocation for cache_creation_input_tokens and cache_read_input_tokens values.

<!-- sequential -->
- [x] T002 [US2] In src/agentcore/app.py, add cache metric extraction from streaming events. In the `_to_sse_event()` function or in the streaming loop in `invoke()`, capture cache metrics from events that contain usage data (the `message` event with usage field). Log cache metrics in the existing "Invocation complete" log line at the end of the `invoke()` function: add cache_creation_input_tokens and cache_read_input_tokens to the log format string. Initialize these counters to 0 at the start of the invocation and accumulate from streaming events that contain usage.cache_creation_input_tokens or usage.cache_read_input_tokens.

---

## Dependencies & Execution Order

- **T001**: No dependencies — can start immediately
- **T002**: No dependency on T001 (different file) — can run in parallel

### Parallel Opportunities

- T001 and T002 touch different files and have no dependencies — they CAN run in parallel, but the feature is so small (2 tasks) that sequential execution is fine.

---

## Implementation Strategy

### MVP (T001 only)

1. Complete T001: Enable prompt caching in model.py
2. **VALIDATE**: Invoke agent, check Anthropic API response for cache metrics

### Full Delivery

3. Complete T002: Add cache logging in app.py
4. **VALIDATE**: Check application logs for cache metrics

---

## Notes

- Only 2 files modified: src/agent/model.py and src/agentcore/app.py
- No new files, no new dependencies
- Agent behavior is unchanged — caching is transparent
- Total: 2 tasks across 2 phases
