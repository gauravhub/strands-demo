# UI Contract: Strands Reasoning Chatbot

**Branch**: `003-strands-reasoning-chatbot` | **Date**: 2026-03-09

This document defines the behavioural contract for the Streamlit chatbot UI — what each component must do and how it responds to state changes. This is the interface contract for the frontend.

---

## Page Layout Contract

```
┌─────────────────────────────────────┐
│  🤖 Strands Demo   [user@email]     │
│  ─────────────────────────────────  │
│                                     │
│  [Chat history — scrollable]        │
│  ┌─── User Message ───────────────┐ │
│  │ user text                      │ │
│  └────────────────────────────────┘ │
│  ┌─── Assistant Turn ─────────────┐ │
│  │  🔍 Reasoning                  │ │
│  │  (thinking text or             │ │
│  │   "No reasoning for this       │ │
│  │    response.")                 │ │
│  │                                │ │
│  │  🛠 Tools Used                 │ │
│  │  Tool: tavily_search           │ │
│  │  Input: {query: "..."}         │ │
│  │  Result: "..."                 │ │
│  │                                │ │
│  │  💬 Response                   │ │
│  │  answer text                   │ │
│  └────────────────────────────────┘ │
│                                     │
│  [Input field]          [Send]      │
└─────────────────────────────────────┘
```

---

## Component Contracts

### ChatInput

| Condition | Behaviour |
|-----------|-----------|
| `is_streaming == False` | Input field and Send button are **enabled** |
| `is_streaming == True` | Input field and Send button are **disabled** |
| User submits empty string | No request sent; show hint text in input placeholder |
| User submits valid message | Append user `ChatMessage` to `messages`; set `is_streaming = True`; start streaming |

### ReasoningSection (per assistant turn)

| Condition | Behaviour |
|-----------|-----------|
| Reasoning tokens arriving | Section visible; text updates incrementally (streaming) |
| No reasoning tokens produced | Section visible; displays "No reasoning for this response." |
| Streaming in progress | Section renders partial content |
| Turn complete | Section frozen with final content |

### ToolsSection (per assistant turn)

| Condition | Behaviour |
|-----------|-----------|
| No tools invoked | Section absent OR shows "No tools used." |
| Tool call started | Section appears with tool name and streaming input |
| Tool result received | Result appended below tool input in same section |
| Multiple tools in sequence | Each tool displayed as a separate labelled block |

### ResponseSection (per assistant turn)

| Condition | Behaviour |
|-----------|-----------|
| Text tokens arriving | Text updates incrementally (streaming) |
| Stream complete | Text frozen; input re-enabled |
| Stream error mid-way | Partial text shown + inline error notice appended |

---

## Streaming Error Contract

| Error Scenario | User-Facing Behaviour |
|----------------|-----------------------|
| API key missing/invalid at startup | `st.error(...)` shown; `st.stop()` called — app halts with clear message |
| Stream fails mid-response | Partial content preserved; inline error appended: "⚠️ Response interrupted: {reason}" |
| Network unreachable | Same as stream failure above |
| Empty response (no tokens received) | Inline error: "⚠️ No response received." |

---

## Session State Contract

Components MUST read from and write to `st.session_state` using these keys only:

| Key | Read by | Written by |
|-----|---------|------------|
| `messages` | Chat history renderer, agent | Input handler, streaming loop |
| `is_streaming` | ChatInput (disabled check) | Streaming loop (set True on start, False on stop) |

No component may write to arbitrary `st.session_state` keys outside this contract.
