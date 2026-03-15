"""Strands Agent factory with Tavily web search and EKS MCP tools."""

import logging
import os

from strands import Agent
from strands_tools import tavily

from src.agent.model import create_model
from src.agent.mcp_tools import get_eks_mcp_tools

logger = logging.getLogger(__name__)


def create_agent() -> tuple[Agent, object | None]:
    """Return a configured Strands Agent with Tavily and EKS MCP tools.

    Returns:
        Tuple of (agent, mcp_client). The caller is responsible for calling
        ``mcp_client.stop()`` when done. mcp_client may be None if EKS MCP
        tools failed to load (graceful degradation).

    Raises:
        EnvironmentError: If TAVILY_API_KEY is not set.
    """
    if not os.getenv("TAVILY_API_KEY"):
        raise EnvironmentError(
            "TAVILY_API_KEY is not set. "
            "Add it to your .env file or environment. "
            "Obtain a free key at https://app.tavily.com"
        )

    mcp_client, eks_tools = get_eks_mcp_tools()

    if eks_tools:
        logger.info("EKS MCP tools loaded: count=%d", len(eks_tools))
    else:
        logger.warning(
            "EKS MCP tools not available — agent will operate with Tavily only"
        )

    try:
        tools = [tavily, *eks_tools]
        agent = Agent(model=create_model(), tools=tools)
        logger.info(
            "Strands Agent created: model=claude-sonnet-4-6, tools=[tavily + %d EKS MCP]",
            len(eks_tools),
        )
        return agent, mcp_client
    except Exception:
        if mcp_client is not None:
            try:
                mcp_client.__exit__(None, None, None)
            except Exception:
                pass
        logger.error("Failed to create Strands Agent", exc_info=True)
        raise
