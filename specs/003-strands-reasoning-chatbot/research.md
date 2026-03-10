# Research: Strands Reasoning Chatbot

**Branch**: `003-strands-reasoning-chatbot` | **Date**: 2026-03-09

---

## Decision 1: Anthropic Provider Configuration

**Decision**: Use `AnthropicModel` from `strands.models.anthropic` with `model_id="claude-sonnet-4-6"` and adaptive extended thinking.

**Rationale**: Strands SDK v1.29.0 (installed) includes `AnthropicModel` out of the box. The `claude-sonnet-4-6` model supports adaptive thinking (`"type": "adaptive"`) which is the recommended mode for Sonnet 4.6 — it lets the model decide when and how much to reason based on problem complexity, avoiding wasted token budgets on simple queries.

**Pattern**:
```python
from strands.models.anthropic import AnthropicModel

model = AnthropicModel(
    client_args={"api_key": os.getenv("ANTHROPIC_API_KEY")},
    max_tokens=16000,
    model_id="claude-sonnet-4-6",
    params={
        "thinking": {"type": "enabled", "budget_tokens": 10000}
    },
)
```

**Alternatives considered**:
- `"type": "adaptive"` with `"effort"` param — supported on Opus 4.6 and Sonnet 4.6, but may not emit explicit reasoning tokens in streaming events; explicit `budget_tokens` is more predictable for demo purposes.
- Bedrock provider — ruled out; user explicitly specified direct Anthropic API.

**Env var required**: `ANTHROPIC_API_KEY`

---

## Decision 2: Streaming API

**Decision**: Use `agent.stream_async(prompt)` — the async generator that yields typed event dicts.

**Rationale**: This is the only native streaming API in Strands SDK. It yields events with discriminated keys, making it straightforward to separate reasoning, tool, and text content.

**Event discrimination pattern**:
```python
async for event in agent.stream_async(user_message):
    if event.get("reasoning") and "reasoningText" in event:
        # Reasoning/thinking token chunk
        reasoning_buffer += event["reasoningText"]

    elif event.get("type") == "tool_use_stream":
        # Tool being called (streaming input)
        current_tool = event["current_tool_use"]

    elif event.get("type") == "tool_result":
        # Tool execution result
        tool_result = event["tool_result"]

    elif "data" in event:
        # Final response text chunk
        response_buffer += event["data"]

    elif "stop" in event:
        # Stream complete — contains stop_reason, message, usage, metrics
        pass
```

**Key source files** (in installed package):
- `strands/agent/agent.py` — `stream_async()` method
- `strands/event_loop/streaming.py` — event emission logic
- `strands/types/_events.py` — typed event classes

**Alternatives considered**:
- Synchronous `agent(prompt)` — no streaming, response only available at completion; ruled out per requirement.
- Callback handlers — alternative pattern but async generator is cleaner for Streamlit.

---

## Decision 3: Web Search Tool

**Decision**: Use Tavily (`from strands_tools import tavily`) with `TAVILY_API_KEY`.

**Rationale**: Tavily is the primary real-time web search tool in `strands-agents-tools`. It provides AI-optimized relevance ranking and requires a single API key. Exa offers semantic search but Tavily is simpler for a demo chatbot where real-time factual search is the primary use case.

**Pattern**:
```python
from strands_tools import tavily

agent = Agent(model=model, tools=[tavily])
```

**Env var required**: `TAVILY_API_KEY`

**Alternatives considered**:
- Exa — neural + keyword search, requires `EXA_API_KEY`; better for semantic search but more complex; ruled out for simplicity.
- Browser tool — interactive browsing via Chromium; too heavy for a chatbot demo.

---

## Decision 4: Streamlit Streaming Pattern

**Decision**: Use `asyncio.run()` wrapping `stream_async()` with `st.empty()` placeholder containers updated incrementally, within a single synchronous Streamlit callback.

**Rationale**: Streamlit runs synchronously; `asyncio.run()` bridges the async generator to the sync Streamlit render loop. Each section (Reasoning, Tools, Response) gets its own `st.empty()` container updated in place during streaming.

**Pattern**:
```python
import asyncio

reasoning_placeholder = st.empty()
tools_placeholder = st.empty()
response_placeholder = st.empty()

async def stream():
    reasoning = ""
    response = ""
    async for event in agent.stream_async(user_message):
        if event.get("reasoning") and "reasoningText" in event:
            reasoning += event["reasoningText"]
            reasoning_placeholder.markdown(f"**Reasoning**\n\n{reasoning}")
        elif "data" in event:
            response += event["data"]
            response_placeholder.markdown(response)

asyncio.run(stream())
```

**Alternatives considered**:
- `st.write_stream()` — only works with synchronous generators returning plain strings; cannot handle multi-section display.
- Threading — unnecessary complexity.

---

## Decision 5: New Dependencies

No new top-level dependencies are required. All needed packages are already declared:
- `strands-agents>=0.1.0` — includes `AnthropicModel`
- `strands-agents-tools>=0.1.0` — includes `tavily`

New **env vars** required (not secrets stored in code):
- `ANTHROPIC_API_KEY` — Anthropic direct API access
- `TAVILY_API_KEY` — Tavily web search API
