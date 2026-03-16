"""Strands Agent factory with Tavily web search, EKS MCP, and AWS API MCP tools."""

import logging
import os

from strands import Agent
from strands_tools import tavily

from src.agent.model import create_model
from src.agent.mcp_tools import get_aws_api_mcp_tools, get_eks_mcp_tools

logger = logging.getLogger(__name__)


def create_agent() -> tuple[Agent, list]:
    """Return a configured Strands Agent with Tavily, EKS MCP, and AWS API MCP tools.

    Returns:
        Tuple of (agent, mcp_clients). The caller is responsible for closing
        each client in the list when done. The list may be empty if no MCP
        tools loaded (graceful degradation).

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

    try:
        tools = [tavily, *eks_tools, *aws_api_tools]
        agent = Agent(model=create_model(), tools=tools)
        logger.info(
            "Strands Agent created: tools=[tavily + %d EKS MCP + %d AWS MCP]",
            len(eks_tools),
            len(aws_api_tools),
        )
        return agent, mcp_clients
    except Exception:
        for client in mcp_clients:
            try:
                client.__exit__(None, None, None)
            except Exception:
                pass
        logger.error("Failed to create Strands Agent", exc_info=True)
        raise
