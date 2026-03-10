"""Strands Agent factory with Tavily web search tool."""

import logging
import os

from strands import Agent
from strands_tools import tavily

from src.agent.model import create_model

logger = logging.getLogger(__name__)


def create_agent() -> Agent:
    """Return a configured Strands Agent with the Tavily web search tool.

    Raises:
        EnvironmentError: If TAVILY_API_KEY is not set.
    """
    if not os.getenv("TAVILY_API_KEY"):
        raise EnvironmentError(
            "TAVILY_API_KEY is not set. "
            "Add it to your .env file or environment. "
            "Obtain a free key at https://app.tavily.com"
        )

    try:
        agent = Agent(model=create_model(), tools=[tavily])
        logger.info(
            "Strands Agent created: model=claude-sonnet-4-6, tools=[tavily]"
        )
        return agent
    except Exception:
        logger.error("Failed to create Strands Agent", exc_info=True)
        raise
