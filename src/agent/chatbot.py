"""Strands Agent factory with Gateway (Tavily), EKS MCP, AWS API MCP, and AgentCore Browser tools."""

from __future__ import annotations

import logging
import os
from typing import Any

from strands import Agent

from src.agent.model import create_model
from src.agent.browser_tools import load_browser_tools
from src.agent.mcp_tools import get_aws_api_mcp_tools, get_eks_mcp_tools, get_gateway_tools

logger = logging.getLogger(__name__)


def create_agent(
    *,
    memory_id: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    gateway_url: str | None = None,
    access_token: str | None = None,
) -> tuple[Agent, list, Any | None]:
    """Return a configured Strands Agent with Gateway, EKS MCP, and AWS API MCP tools.

    Args:
        memory_id: AgentCore Memory resource ID. When set, enables memory.
        session_id: Session identifier for short-term memory scoping.
        actor_id: User identifier (Cognito username) for per-user memory isolation.
        gateway_url: AgentCore Gateway MCP endpoint URL. When set, loads Tavily
            tools from the Gateway. When not set, no web search tools are loaded.
        access_token: Cognito access token for Gateway authentication.

    Returns:
        Tuple of (agent, mcp_clients, session_manager). The caller is responsible
        for closing each MCP client and the session_manager when done.
        session_manager may be None if memory is not configured.
    """
    mcp_clients: list = []

    # Load Gateway tools (Tavily via managed MCP endpoint)
    gateway_tools: list = []
    if gateway_url:
        gw_client, gateway_tools = get_gateway_tools(gateway_url, access_token or "")
        if gw_client is not None:
            mcp_clients.append(gw_client)
        if gateway_tools:
            logger.info("Gateway tools loaded: count=%d", len(gateway_tools))
        else:
            logger.warning("Gateway tools not available")
    else:
        logger.info("Gateway not configured — web search tools will not be available")

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

    # Load AgentCore Browser tools
    browser_tools = load_browser_tools()

    # Build system prompt with browser awareness
    retail_store_url = os.getenv(
        "RETAIL_STORE_URL",
        "http://k8s-ui-ui-6353f3da9d-613966318.us-east-1.elb.amazonaws.com",
    )
    system_prompt = (
        "You are a helpful AI assistant with access to web search, AWS management, "
        "and browser automation tools.\n\n"
        "## Browser Capabilities\n"
        "You can browse websites, take screenshots, and describe web page content "
        "using the browser tool. When users ask you to browse a website, take a "
        "screenshot, or describe what's on a page, use the browser tool.\n\n"
        f"The retail store demo is available at: {retail_store_url}\n"
        'When users mention "the retail store" or "the store", use this URL.\n\n'
        "IMPORTANT: Always ensure browser sessions are stopped after use. "
        "The browser tool handles session lifecycle automatically, but if you "
        "encounter errors, inform the user clearly.\n"
    )

    try:
        tools = [*gateway_tools, *eks_tools, *aws_api_tools, *browser_tools]
        agent_kwargs: dict[str, Any] = {
            "model": create_model(),
            "tools": tools,
            "system_prompt": system_prompt,
        }
        if session_manager is not None:
            agent_kwargs["session_manager"] = session_manager

        agent = Agent(**agent_kwargs)
        logger.info(
            "Strands Agent created: tools=[%d Gateway + %d EKS MCP + %d AWS MCP + %d Browser] memory=%s",
            len(gateway_tools),
            len(eks_tools),
            len(aws_api_tools),
            len(browser_tools),
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
