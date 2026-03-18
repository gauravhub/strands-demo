# Implementation Plan: Anthropic Prompt Caching

**Branch**: `016-prompt-caching` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-prompt-caching/spec.md`

## Summary

Enable Anthropic prompt caching by subclassing AnthropicModel to override `format_request()`, injecting `cache_control` on the system prompt and last tool definition. Add cache metric logging to the agent entrypoint. Two files modified, zero new files.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `strands-agents` (AnthropicModel), `anthropic` SDK (already installed)
**Storage**: N/A
**Testing**: Manual validation via log inspection (cache_creation_input_tokens, cache_read_input_tokens)
**Target Platform**: AgentCore Runtime (Linux ARM64 container)
**Project Type**: Enhancement to existing model configuration
**Performance Goals**: 50%+ reduction in billed input tokens on cache hits
**Constraints**: No behavior changes, no system prompt modifications, must coexist with extended thinking

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | PASS | Minimal change: subclass with one method override + 2 log lines. No new files, no new abstractions. |
| II. Iterative & Independent Delivery | PASS | Fully independent — caching is transparent. Agent works identically with or without it. |
| III. Python-Native Patterns | PASS | Python subclass, PEP 8, type hints. No new dependencies. |
| IV. Security by Design | PASS | No secrets, no auth changes. Cache is server-side at Anthropic. |
| V. Observability & Debuggability | PASS | Adds cache performance logging — improves observability. |

## Project Structure

### Source Code Changes

```text
src/agent/model.py          # MODIFIED: Subclass AnthropicModel with cache_control
src/agentcore/app.py         # MODIFIED: Add cache metric logging to invocation summary
```

**Structure Decision**: No new files. The subclass lives in the existing model.py (where create_model() already lives). Cache logging is added to the existing invocation summary log line in app.py.

## Architecture

### How It Works

```
create_model() → CachedAnthropicModel (subclass)
  │
  └─ format_request() override:
       1. Call super().format_request() to get standard request dict
       2. Convert system prompt string → list with cache_control
       3. Add cache_control to last tool definition
       4. Return modified request

Anthropic API receives request with cache_control →
  First call: caches system + tools (cache_creation_input_tokens > 0)
  Subsequent calls within TTL: reads from cache (cache_read_input_tokens > 0)
```

### Cache Breakpoints

| Breakpoint | Location | What Gets Cached |
|-----------|----------|-----------------|
| 1 | System prompt (last text block) | Full system prompt (~500 tokens) |
| 2 | Last tool definition | All tool schemas (50+ tools, thousands of tokens) |

### Request Format Change

**Before** (current):
```python
{"system": "You are a helpful AI assistant..."}
```

**After** (with caching):
```python
{"system": [{"type": "text", "text": "You are a helpful AI assistant...", "cache_control": {"type": "ephemeral", "ttl": "1h"}}]}
```

## Complexity Tracking

No violations — all items pass constitution check. No complexity tracking needed.
