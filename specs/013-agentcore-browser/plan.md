# Implementation Plan: AgentCore Browser Integration

**Branch**: `013-agentcore-browser` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-agentcore-browser/spec.md`

## Summary

Add AgentCore Browser tools to the existing Strands agent so users can ask the agent to browse websites, take screenshots, and describe page content — all within the existing Streamlit chat interface. Uses the pre-built `strands_tools.browser.AgentCoreBrowser` tool from the `strands-agents-tools` package, which wraps the `bedrock-agentcore` SDK and Playwright for browser automation.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `strands-agents-tools>=0.1.0` (includes `AgentCoreBrowser`), `bedrock-agentcore>=0.1.0` (already installed), `playwright`, `nest-asyncio`, `streamlit>=1.35.0`
**Storage**: N/A — ephemeral browser sessions only
**Testing**: Manual validation via Streamlit chat interface
**Target Platform**: Streamlit Cloud / local dev (us-east-1)
**Project Type**: Web application — Streamlit frontend with Strands agent backend
**Performance Goals**: Screenshot captured and displayed within 30 seconds
**Constraints**: Additive change only — must not break existing agent tools or UI
**Scale/Scope**: 4 files modified, 1 new dependency installed, 1 env var added

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | PASS | Uses pre-built `AgentCoreBrowser` from strands-agents-tools — no custom browser wrapper needed. Single tool added to existing agent. |
| II. Iterative & Independent Delivery | PASS | Additive enhancement — existing agent continues working. Browser tools degrade gracefully if unavailable. |
| III. Python-Native Patterns | PASS | Python 3.11+, follows existing tool-loading patterns in `mcp_tools.py`. |
| IV. Security by Design | PASS | Cognito auth unchanged. Browser sessions are ephemeral and cleaned up after use. No new credentials stored. |
| V. Observability & Debuggability | PASS | Browser tool calls appear in Strands streaming events, rendered in existing "Tools Used" expander. Errors surfaced to user. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/013-agentcore-browser/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── agent/
│   ├── chatbot.py           # MODIFIED — add browser tool to agent's tool list
│   └── mcp_tools.py         # MODIFIED — add load_browser_tools() function
├── chat/
│   └── ui.py                # MODIFIED — detect and render base64 screenshot images inline
└── ...

pyproject.toml               # MODIFIED — add playwright, nest-asyncio dependencies
.env.example                 # MODIFIED — add RETAIL_STORE_URL
```

**Structure Decision**: Minimal modifications to 4 existing files. No new files needed — `AgentCoreBrowser` is a pre-built tool from the `strands-agents-tools` package.
