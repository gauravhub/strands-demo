# Research: Anthropic Prompt Caching

**Feature**: 016-prompt-caching
**Date**: 2026-03-18

## R1: Strands AnthropicModel Cache Support

**Decision**: Subclass AnthropicModel and override `format_request()` to convert the system prompt string into a list of TextBlockParam with cache_control.

**Rationale**: The strands-agents AnthropicModel (v0.1.x) passes the system prompt as a plain string via `{"system": system_prompt}`. The Anthropic SDK accepts either a string OR a list of `TextBlockParam` objects with optional `cache_control`. By overriding `format_request()`, we can inject cache_control without modifying the upstream library.

**Alternatives considered**:
- Monkey-patching AnthropicModel: Fragile, breaks on SDK updates.
- Modifying the installed package: Not version-controllable.
- Using `params` kwarg to inject system: Won't work — `system` is set explicitly in `format_request`.
- Waiting for upstream support: Strands already has `cachePoint` for message content but NOT for system prompts in AnthropicModel. Unknown timeline.

## R2: Cache Control Format

**Decision**: Use `{"type": "ephemeral", "ttl": "1h"}` on the last system prompt text block.

**Rationale**: Per the Anthropic API, cache_control must be placed on the last content block in a cacheable prefix. The system prompt is a single text block, so we add cache_control to it. The `ttl` field supports "5m" (default) and "1h" values.

**Key constraint**: Minimum 1024 tokens required for caching. The system prompt alone (~500 tokens) may be below threshold, but combined with tool definitions (thousands of tokens), the cacheable prefix easily exceeds it. The Anthropic API handles this gracefully — if below threshold, it simply doesn't cache (no error).

## R3: Tool Definition Caching

**Decision**: Add cache_control to the last tool definition in the tools array, so the entire tools prefix is cached.

**Rationale**: Per Anthropic's docs, cache breakpoints can be set at "the final tool definition in the tools array." This caches all tool schemas (50+ tools). Combined with the system prompt cache breakpoint, this creates two cache checkpoints.

**Implementation**: Override `format_request()` to add `cache_control` to the last tool in the formatted tools list.

## R4: Cache Observability

**Decision**: Log cache metrics from the streaming response's usage field in the SSE event mapping in app.py.

**Rationale**: The Anthropic API returns `cache_creation_input_tokens` and `cache_read_input_tokens` in the `message_start` event's `usage` field during streaming. The existing `_to_sse_event` function in app.py already processes streaming events. We add cache metric logging in the invocation summary log (the "Invocation complete" log line).

## R5: Compatibility with Extended Thinking

**Decision**: No special handling needed — cache_control and thinking params are independent.

**Rationale**: Cache_control is applied to system prompt and tool definitions (request-level). Extended thinking is a model parameter (`params.thinking`). They operate at different levels and don't conflict. The Anthropic API docs confirm prompt caching works with extended thinking.
