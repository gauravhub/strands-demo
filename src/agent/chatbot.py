"""Strands Agent factory with Tavily web search, EKS MCP, and AWS API MCP tools."""

from __future__ import annotations

import logging
import os
from typing import Any

from strands import Agent
from strands_tools import tavily

from src.agent.model import create_model
from src.agent.mcp_tools import get_aws_api_mcp_tools, get_eks_mcp_tools

logger = logging.getLogger(__name__)


def create_agent(
    *,
    memory_id: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
) -> tuple[Agent, list, Any | None]:
    """Return a configured Strands Agent with Tavily, EKS MCP, and AWS API MCP tools.

    Args:
        memory_id: AgentCore Memory resource ID. When set, enables memory.
        session_id: Session identifier for short-term memory scoping.
        actor_id: User identifier (Cognito username) for per-user memory isolation.

    Returns:
        Tuple of (agent, mcp_clients, session_manager). The caller is responsible
        for closing each MCP client and the session_manager when done.
        session_manager may be None if memory is not configured.

    Raises:
        EnvironmentError: If TAVILY_API_KEY is not set.
    """
    if not os.getenv("TAVILY_API_KEY"):
        raise EnvironmentError(
            "TAVILY_API_KEY is not set. "
            "Add it to your .env file or environment. "
            "Obtain a free key at https://app.tavily.com"
        )

    mcp_clients: list = []

    eks_client, eks_tools = get_eks_mcp_tools()
    if eks_client is not None:
        mcp_clients.append(eks_client)
    if eks_tools:
        logger.info("EKS MCP tools loaded: count=%d", len(eks_tools))
    else:
        logger.warning("EKS MCP tools not available")

    aws_api_client, aws_api_tools = get_aws_api_mcp_tools()
    if aws_api_client is not None:
        mcp_clients.append(aws_api_client)
    if aws_api_tools:
        logger.info("AWS MCP tools loaded: count=%d", len(aws_api_tools))
    else:
        logger.warning("AWS MCP tools not available")

    # Create session manager for AgentCore Memory (optional)
    session_manager = None
    if memory_id:
        try:
            from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
            from bedrock_agentcore.memory.integrations.strands.session_manager import (
                AgentCoreMemorySessionManager,
            )

            config = AgentCoreMemoryConfig(
                memory_id=memory_id,
                session_id=session_id or "default-session",
                actor_id=actor_id or "anonymous",
            )
            session_manager = AgentCoreMemorySessionManager(
                agentcore_memory_config=config,
                region_name=os.getenv("AWS_REGION", "us-east-1"),
            )
            logger.info(
                "AgentCore Memory enabled: memory_id=%s actor_id=%s session_id=%s",
                memory_id,
                actor_id,
                session_id,
            )
        except Exception:
            logger.warning("Failed to initialize AgentCore Memory — agent will operate without memory", exc_info=True)
            session_manager = None
    else:
        logger.info("AgentCore Memory not configured — agent will operate without memory")

    try:
        tools = [tavily, *eks_tools, *aws_api_tools]
        agent_kwargs: dict[str, Any] = {"model": create_model(), "tools": tools}
        if session_manager is not None:
            agent_kwargs["session_manager"] = session_manager

        agent = Agent(**agent_kwargs)
        logger.info(
            "Strands Agent created: tools=[tavily + %d EKS MCP + %d AWS MCP] memory=%s",
            len(eks_tools),
            len(aws_api_tools),
            "enabled" if session_manager else "disabled",
        )
        return agent, mcp_clients, session_manager
    except Exception:
        for client in mcp_clients:
            try:
                client.__exit__(None, None, None)
            except Exception:
                pass
        if session_manager is not None:
            try:
                session_manager.close()
            except Exception:
                pass
        logger.error("Failed to create Strands Agent", exc_info=True)
        raise
