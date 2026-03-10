"""Streamlit chatbot UI — streaming display, session state, and rendering."""

import asyncio
import logging

import streamlit as st
from strands import Agent

logger = logging.getLogger(__name__)


# ── Session State ──────────────────────────────────────────────────────────────


def init_session() -> None:
    """Initialise session state keys on first page load."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "is_streaming" not in st.session_state:
        st.session_state.is_streaming = False


# ── Streaming ──────────────────────────────────────────────────────────────────


async def _stream_turn(agent: Agent, user_message: str) -> None:
    """Run one streaming agent turn, updating session state incrementally."""
    msg: dict = {
        "role": "assistant",
        "content": "",
        "reasoning": "",
        "tool_calls": [],
        "error": None,
    }
    st.session_state.messages.append(msg)

    # Live placeholders — updated in place during streaming
    with st.chat_message("assistant"):
        reasoning_placeholder = st.empty()
        tools_placeholder = st.empty()
        response_placeholder = st.empty()

    logger.info("Stream start: user_message_len=%d", len(user_message))

    try:
        async for event in agent.stream_async(user_message):
            # ── Reasoning tokens ──────────────────────────────────────────
            if event.get("reasoning") and "reasoningText" in event:
                msg["reasoning"] += event["reasoningText"]
                reasoning_placeholder.expander(
                    "🔍 Reasoning", expanded=True
                ).markdown(msg["reasoning"])

            # ── Tool call streaming ───────────────────────────────────────
            # Events have no "type" key; tool streaming is detected by
            # presence of "current_tool_use" + "delta" keys.
            elif "current_tool_use" in event and "delta" in event:
                current = event["current_tool_use"]
                tool_id = current.get("toolUseId", "")
                existing = next(
                    (t for t in msg["tool_calls"] if t["tool_use_id"] == tool_id),
                    None,
                )
                raw_input = current.get("input", {})
                # input may arrive as partial JSON string during streaming
                if isinstance(raw_input, str):
                    try:
                        import json
                        raw_input = json.loads(raw_input)
                    except Exception:
                        raw_input = {"raw": raw_input}
                if existing is None:
                    entry: dict = {
                        "tool_use_id": tool_id,
                        "name": current.get("name", ""),
                        "input": raw_input,
                        "result": None,
                    }
                    msg["tool_calls"].append(entry)
                    logger.info("Tool invocation: name=%s input=%s", entry["name"], str(raw_input)[:80])
                else:
                    existing["input"] = raw_input
                _render_tools_live(msg["tool_calls"], tools_placeholder)

            # ── Tool results via message events ───────────────────────────
            # After each tool runs, Strands emits a message event with
            # role="user" containing toolResult content blocks.
            elif "message" in event:
                message = event["message"]
                if isinstance(message, dict) and message.get("role") == "user":
                    for block in message.get("content", []):
                        if not isinstance(block, dict):
                            continue
                        tr_data = block.get("toolResult") or block.get("tool_result")
                        if tr_data is None:
                            continue
                        # Extract text content from result
                        result_text = ""
                        for c in tr_data.get("content", []):
                            if isinstance(c, dict) and "text" in c:
                                result_text += c["text"]
                        # Also accept top-level toolUseId in the block
                        result_id = block.get("toolUseId") or tr_data.get("toolUseId", "")
                        # Match by ID, or fall back to first unresolved tool call
                        matched = False
                        if result_id:
                            for tc in msg["tool_calls"]:
                                if tc["tool_use_id"] == result_id:
                                    tc["result"] = result_text
                                    matched = True
                                    break
                        if not matched:
                            for tc in msg["tool_calls"]:
                                if tc["result"] is None:
                                    tc["result"] = result_text
                                    break
                        _render_tools_live(msg["tool_calls"], tools_placeholder)

            # ── Response text ─────────────────────────────────────────────
            elif "data" in event:
                msg["content"] += event["data"]
                response_placeholder.markdown(msg["content"])

            # ── Stream complete ───────────────────────────────────────────
            elif "result" in event or "stop" in event:
                stop_data = event.get("stop") or event.get("result")
                if isinstance(stop_data, tuple) and len(stop_data) >= 3:
                    usage = stop_data[2]
                    logger.info("Stream stop: usage=%s", usage)

    except Exception as exc:
        logger.error("Stream error", exc_info=True)
        msg["error"] = f"⚠️ Response interrupted: {exc}"
        response_placeholder.markdown(
            (msg["content"] or "") + "\n\n" + msg["error"]
        )


def _render_tools_live(tool_calls: list, placeholder: st.delta_generator.DeltaGenerator) -> None:
    """Render current tool calls into a live placeholder."""
    if not tool_calls:
        return
    with placeholder.expander("🛠 Tools Used", expanded=True):
        for tc in tool_calls:
            st.markdown(f"**{tc['name']}**")
            inp = tc["input"]
            if inp:
                if isinstance(inp, dict):
                    st.json(inp)
                else:
                    st.code(str(inp))
            if tc["result"] is not None:
                st.markdown(tc["result"])
            else:
                st.caption("Awaiting result…")


# ── Chat History Rendering ─────────────────────────────────────────────────────


def render_chat_history() -> None:
    """Render all completed messages from session state."""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                _render_reasoning_section(msg)
                _render_tools_section(msg)
                if msg["content"]:
                    st.markdown(msg["content"])
                if msg.get("error"):
                    st.error(msg["error"])


def _render_reasoning_section(msg: dict) -> None:
    """Always render the Reasoning expander for an assistant message."""
    with st.expander("🔍 Reasoning"):
        if msg["reasoning"]:
            st.markdown(msg["reasoning"])
        else:
            st.caption("*No reasoning for this response.*")


def _render_tools_section(msg: dict) -> None:
    """Render the Tools Used expander only when tools were invoked."""
    if not msg.get("tool_calls"):
        return
    with st.expander("🛠 Tools Used"):
        for tc in msg["tool_calls"]:
            st.markdown(f"**{tc['name']}**")
            inp = tc["input"]
            if inp:
                if isinstance(inp, dict):
                    st.json(inp)
                else:
                    st.code(str(inp))
            if tc["result"] is not None:
                st.markdown(tc["result"])
            else:
                st.caption("Awaiting result…")


# ── Input ──────────────────────────────────────────────────────────────────────


def render_input(agent: Agent) -> None:
    """Render the chat input field and handle submission."""
    user_message = st.chat_input(
        "Message…",
        disabled=st.session_state.is_streaming,
    )
    if user_message:
        # Append user turn
        st.session_state.messages.append(
            {"role": "user", "content": user_message}
        )
        st.session_state.is_streaming = True
        try:
            asyncio.run(_stream_turn(agent, user_message))
        finally:
            st.session_state.is_streaming = False
        st.rerun()


# ── Entry Point ────────────────────────────────────────────────────────────────


def render_chatbot(agent: Agent) -> None:
    """Main chatbot entry point — call from show_main_app()."""
    init_session()
    render_chat_history()
    render_input(agent)
