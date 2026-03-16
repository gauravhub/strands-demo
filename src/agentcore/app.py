"""AgentCore Runtime entrypoint — BedrockAgentCoreApp wrapping the Strands agent.

This module is the container's main entry point (CMD python app.py).
It exposes the Strands reasoning chatbot over the AgentCore HTTP/SSE protocol.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands_tools import tavily

from src.agent.mcp_tools import get_aws_api_mcp_tools, get_eks_mcp_tools
from src.agent.model import create_model

logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()


# ── SSE event mapping ──────────────────────────────────────────────────────────


def _to_sse_event(event: dict[str, Any]) -> dict[str, Any] | None:
    """Map a raw Strands stream event to a typed SSE JSON dict.

    Returns None for events that should be silently skipped.
    """
    # Response text token
    if "data" in event:
        return {"type": "text", "data": event["data"]}

    # Extended thinking / reasoning token
    if event.get("reasoning") and "reasoningText" in event:
        return {"type": "reasoning", "data": event["reasoningText"]}

    # Tool invocation start (streaming input delta)
    if "current_tool_use" in event and "delta" in event:
        current = event["current_tool_use"]
        raw_input = current.get("input", {})
        if isinstance(raw_input, str):
            import json as _json
            try:
                raw_input = _json.loads(raw_input)
            except Exception:
                raw_input = {"raw": raw_input}
        return {
            "type": "tool_start",
            "tool_use_id": current.get("toolUseId", ""),
            "name": current.get("name", ""),
            "input": raw_input,
        }

    # Tool result arrives in a message event (role=user, toolResult content)
    if "message" in event:
        message = event["message"]
        if isinstance(message, dict) and message.get("role") == "user":
            for block in message.get("content", []):
                if not isinstance(block, dict):
                    continue
                tr_data = block.get("toolResult") or block.get("tool_result")
                if tr_data is None:
                    continue
                result_text = ""
                for c in tr_data.get("content", []):
                    if isinstance(c, dict) and "text" in c:
                        result_text += c["text"]
                tool_use_id = block.get("toolUseId") or tr_data.get("toolUseId", "")
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "result": result_text,
                }

    return None


# ── Agent entrypoint ───────────────────────────────────────────────────────────


@app.entrypoint
async def invoke(
    payload: dict[str, Any], context: Any
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream agent responses as typed SSE JSON events.

    Payload keys:
        prompt (str): The user's message for this turn.

    Emits events of types: text, reasoning, tool_start, tool_result, error, done.
    """
    prompt: str = payload.get("prompt", "")
    username: str = payload.get("username", "anonymous")
    session_id: str = getattr(context, "session_id", "unknown")
    memory_id: str = os.getenv("AGENTCORE_MEMORY_ID", "")

    logger.info(
        "Invocation start: session_id=%s username=%s memory=%s prompt_len=%d",
        session_id,
        username,
        "enabled" if memory_id else "disabled",
        len(prompt),
    )

    # Load MCP tools before entering the async generator to avoid
    # blocking the event loop with list_tools_sync() inside the generator.
    eks_client, eks_tools = get_eks_mcp_tools()
    if eks_tools:
        logger.info("EKS MCP tools loaded: count=%d", len(eks_tools))
    else:
        logger.warning("EKS MCP tools not available")

    aws_api_client, aws_api_tools = get_aws_api_mcp_tools()
    if aws_api_tools:
        logger.info("AWS MCP tools loaded: count=%d", len(aws_api_tools))
    else:
        logger.warning("AWS MCP tools not available")

    tools = [tavily, *eks_tools, *aws_api_tools]

    # Create session manager for AgentCore Memory (optional)
    session_manager = None
    if memory_id:
        try:
            from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
            from bedrock_agentcore.memory.integrations.strands.session_manager import (
                AgentCoreMemorySessionManager,
            )

            mem_config = AgentCoreMemoryConfig(
                memory_id=memory_id,
                session_id=session_id,
                actor_id=username,
            )
            session_manager = AgentCoreMemorySessionManager(
                agentcore_memory_config=mem_config,
                region_name=os.getenv("AWS_REGION", "us-east-1"),
            )
            session_manager.__enter__()
            logger.info("AgentCore Memory enabled: memory_id=%s actor_id=%s", memory_id, username)
        except Exception:
            logger.warning("Failed to initialize AgentCore Memory", exc_info=True)
            session_manager = None

    text_events = 0
    tool_call_count = 0
    error_count = 0

    try:
        agent_kwargs: dict[str, Any] = {"model": create_model(), "tools": tools}
        if session_manager is not None:
            agent_kwargs["session_manager"] = session_manager

        agent = Agent(**agent_kwargs)
        async for raw_event in agent.stream_async(prompt):
            sse = _to_sse_event(raw_event)
            if sse is None:
                continue

            if sse["type"] == "text":
                text_events += 1
            elif sse["type"] == "tool_start":
                tool_call_count += 1
                logger.info(
                    "Tool call: session_id=%s name=%s tool_use_id=%s",
                    session_id,
                    sse.get("name"),
                    sse.get("tool_use_id"),
                )
            elif sse["type"] == "error":
                error_count += 1

            yield sse

    except Exception as exc:
        error_count += 1
        logger.error(
            "Invocation error: session_id=%s error=%s",
            session_id,
            exc,
            exc_info=True,
        )
        yield {"type": "error", "message": str(exc)}

    finally:
        logger.info(
            "Invocation complete: session_id=%s text_events=%d tool_calls=%d errors=%d",
            session_id,
            text_events,
            tool_call_count,
            error_count,
        )
        if eks_client is not None:
            try:
                eks_client.__exit__(None, None, None)
            except Exception:
                logger.warning("Failed to close EKS MCP client", exc_info=True)
        if aws_api_client is not None:
            try:
                aws_api_client.__exit__(None, None, None)
            except Exception:
                logger.warning("Failed to close AWS MCP client", exc_info=True)
        if session_manager is not None:
            try:
                session_manager.__exit__(None, None, None)
            except Exception:
                logger.warning("Failed to close AgentCore Memory session manager", exc_info=True)

    yield {"type": "done"}


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=log_level)
    app.run()
