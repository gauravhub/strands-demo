"""Streamlit chatbot UI — streaming display, session state, and rendering."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import streamlit as st
from strands import Agent

if TYPE_CHECKING:
    from src.agentcore.config import AgentCoreConfig

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


# ── AgentCore SSE variant ──────────────────────────────────────────────────────


def _stream_turn_agentcore(
    config: "AgentCoreConfig",
    access_token: str,
    session_id: str,
    user_message: str,
    username: str = "",
) -> None:
    """Run one streaming turn via AgentCore HTTP SSE, updating session state."""
    from src.agentcore.client import (
        AgentCoreAuthError,
        AgentCoreError,
        invoke_streaming,
    )

    msg: dict = {
        "role": "assistant",
        "content": "",
        "reasoning": "",
        "tool_calls": [],
        "error": None,
    }
    st.session_state.messages.append(msg)

    with st.chat_message("assistant"):
        reasoning_placeholder = st.empty()
        tools_placeholder = st.empty()
        response_placeholder = st.empty()

    logger.info("AgentCore stream start: session_id=%s prompt_len=%d", session_id, len(user_message))

    try:
        for event in invoke_streaming(
            runtime_arn=config.runtime_arn,
            region=config.region,
            qualifier=config.qualifier,
            session_id=session_id,
            access_token=access_token,
            prompt=user_message,
            username=username,
        ):
            event_type = event.get("type")

            if event_type == "text":
                msg["content"] += event.get("data", "")
                response_placeholder.markdown(msg["content"])

            elif event_type == "reasoning":
                msg["reasoning"] += event.get("data", "")
                reasoning_placeholder.expander("🔍 Reasoning", expanded=True).markdown(
                    msg["reasoning"]
                )

            elif event_type == "tool_start":
                tool_use_id = event.get("tool_use_id", "")
                existing = next(
                    (t for t in msg["tool_calls"] if t["tool_use_id"] == tool_use_id),
                    None,
                )
                if existing is None:
                    msg["tool_calls"].append({
                        "tool_use_id": tool_use_id,
                        "name": event.get("name", ""),
                        "input": event.get("input", {}),
                        "result": None,
                    })
                else:
                    existing["input"] = event.get("input", existing["input"])
                _render_tools_live(msg["tool_calls"], tools_placeholder)

            elif event_type == "tool_result":
                tool_use_id = event.get("tool_use_id", "")
                result_text = event.get("result", "")
                matched = False
                for tc in msg["tool_calls"]:
                    if tc["tool_use_id"] == tool_use_id:
                        tc["result"] = result_text
                        matched = True
                        break
                if not matched:
                    for tc in msg["tool_calls"]:
                        if tc["result"] is None:
                            tc["result"] = result_text
                            break
                _render_tools_live(msg["tool_calls"], tools_placeholder)

            elif event_type == "error":
                msg["error"] = f"⚠️ Agent error: {event.get('message', 'Unknown error')}"
                response_placeholder.markdown(
                    (msg["content"] or "") + "\n\n" + msg["error"]
                )

            elif event_type == "done":
                break

    except AgentCoreAuthError:
        # Signal to app.py that the session has expired — it will clear + redirect
        logger.info("AgentCore auth expired: session_id=%s", session_id)
        st.session_state["agentcore_auth_expired"] = True
        st.rerun()

    except Exception as exc:
        logger.error("AgentCore stream error: session_id=%s", session_id, exc_info=True)
        user_msg = str(exc)
        if "timed out" in user_msg.lower() or "timeout" in user_msg.lower():
            user_msg = "The agent took too long to respond. Please try again with a shorter query."
        elif "unavailable" in user_msg.lower():
            user_msg = "The agent service is temporarily unavailable. Please try again in a moment."
        msg["error"] = f"⚠️ {user_msg}"
        response_placeholder.markdown((msg["content"] or "") + "\n\n" + msg["error"])


def render_chatbot_agentcore(
    config: "AgentCoreConfig",
    access_token: str,
    session_id: str,
    username: str = "",
) -> None:
    """AgentCore chatbot entry point — streams via HTTP SSE with Cognito Bearer token.

    Args:
        config: AgentCore endpoint configuration (ARN, region, qualifier).
        access_token: Cognito access token — forwarded as Bearer to AgentCore.
        session_id: UUID v4 session identifier (≥33 chars), per browser tab.
        username: Cognito username — passed to agent for memory actor_id.
    """
    init_session()
    render_chat_history()

    user_message = st.chat_input(
        "Message…",
        disabled=st.session_state.is_streaming,
    )
    if user_message:
        st.session_state.messages.append({"role": "user", "content": user_message})
        st.session_state.is_streaming = True
        try:
            _stream_turn_agentcore(config, access_token, session_id, user_message, username)
        finally:
            st.session_state.is_streaming = False
        st.rerun()
