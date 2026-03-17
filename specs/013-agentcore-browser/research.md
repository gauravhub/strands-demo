# Research: AgentCore Browser Integration

**Date**: 2026-03-17 | **Branch**: `013-agentcore-browser`

## R1: Browser Tool Integration Approach

**Decision**: Use the pre-built `strands_tools.browser.AgentCoreBrowser` tool from `strands-agents-tools` package.

**Rationale**: The `strands-agents-tools` package already includes a fully-featured `AgentCoreBrowser` class that wraps `bedrock-agentcore` SDK + Playwright. It provides a `.browser` attribute that is a ready-to-use Strands tool — the agent can call it to start sessions, navigate, take screenshots, and extract content. This eliminates the need to write custom tool wrappers.

**Usage pattern**:
```python
from strands_tools.browser import AgentCoreBrowser
browser_tool = AgentCoreBrowser(region="us-east-1")
agent = Agent(tools=[*existing_tools, browser_tool.browser])
```

**Alternatives considered**:
- Custom Strands tools wrapping `BrowserClient` directly — rejected; the pre-built tool already does this with proper error handling, session lifecycle, and Playwright integration.
- MCP-based browser tools — rejected per constraint (use SDK, not MCP).

## R2: Missing Dependencies

**Decision**: Install `playwright` and `nest-asyncio` as additional dependencies.

**Rationale**: `strands_tools.browser` imports `nest_asyncio` at module load time and uses `playwright` for browser automation over CDP WebSocket. Both are required runtime dependencies that aren't currently installed.

**Installation**:
```bash
pip install playwright nest-asyncio
playwright install chromium  # Not needed — AgentCore provides the remote browser
```
Note: `playwright install` is NOT needed because the browser runs in AgentCore's cloud environment. Only the Playwright Python client library is needed for CDP connection.

**Alternatives considered**: None — these are hard dependencies of `strands_tools.browser`.

## R3: Screenshot Rendering in Chat UI

**Decision**: Detect base64 PNG data in tool results and render with `st.image()`.

**Rationale**: The `AgentCoreBrowser` tool returns screenshot data as base64-encoded PNG in the tool result. The existing UI in `src/chat/ui.py` renders tool results as markdown text. To display images, we need to detect when a tool result contains base64 image data and render it with `st.image()` instead of markdown.

**Detection heuristic**: Check if tool result string starts with `data:image/` or contains a base64 PNG prefix pattern. The browser tool returns images in a recognizable format.

**Alternatives considered**:
- Save screenshots to disk and use file paths — rejected; adds file management complexity and cleanup burden.
- Use `st.markdown` with embedded image — rejected; base64 images in markdown have size limits and render poorly.

## R4: System Prompt Enhancement

**Decision**: Add browser capability awareness to the agent's system prompt with the configurable `RETAIL_STORE_URL`.

**Rationale**: The agent needs to know it has browser tools available and how to use them. Including the retail store URL as a known target makes the demo experience smoother — users can say "screenshot the store" without specifying the full URL.

**Prompt addition**:
- Mention browser capabilities (navigate, screenshot, describe)
- Include `RETAIL_STORE_URL` as default browsing target
- Instruct to always stop browser sessions after use

**Alternatives considered**: Relying on tool descriptions alone — rejected; explicit system prompt guidance improves reliability.

## R5: Graceful Degradation Pattern

**Decision**: Follow the existing pattern in `chatbot.py` — wrap browser tool loading in try/except, return empty list on failure.

**Rationale**: The existing tool loaders (`get_gateway_tools`, `get_eks_mcp_tools`, `get_aws_api_mcp_tools`) all return `(None, [])` on failure and log a warning. The browser tool loader should follow the identical pattern, keeping the agent functional with its other tools.

**Alternatives considered**: None — matching existing patterns is the simplest approach.
