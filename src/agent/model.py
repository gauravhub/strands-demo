"""AnthropicModel factory for Claude Sonnet 4.6 with extended thinking and prompt caching."""

from __future__ import annotations

import logging
import os
from typing import Any

from strands.models.anthropic import AnthropicModel
from strands.types.content import Messages
from strands.types.tools import ToolChoice, ToolSpec

logger = logging.getLogger(__name__)

CACHE_TTL = os.getenv("ANTHROPIC_CACHE_TTL", "1h")


class CachedAnthropicModel(AnthropicModel):
    """AnthropicModel subclass that enables prompt caching on system prompt and tools."""

    def format_request(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        tool_choice: ToolChoice | None = None,
    ) -> dict[str, Any]:
        """Format request with cache_control on system prompt and last tool definition."""
        request = super().format_request(messages, tool_specs, system_prompt, tool_choice)

        # Convert system prompt string to list with cache_control
        if "system" in request and isinstance(request["system"], str):
            request["system"] = [
                {
                    "type": "text",
                    "text": request["system"],
                    "cache_control": {"type": "ephemeral", "ttl": CACHE_TTL},
                }
            ]

        # Add cache_control to last tool definition
        if request.get("tools"):
            request["tools"][-1]["cache_control"] = {"type": "ephemeral", "ttl": CACHE_TTL}

        return request


def create_model() -> CachedAnthropicModel:
    """Return a configured CachedAnthropicModel with extended thinking and prompt caching.

    Raises:
        EnvironmentError: If ANTHROPIC_API_KEY is not set.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file or environment. "
            "Obtain a key at https://console.anthropic.com"
        )

    model = CachedAnthropicModel(
        client_args={"api_key": api_key},
        max_tokens=16000,
        model_id="claude-sonnet-4-6",
        params={"thinking": {"type": "enabled", "budget_tokens": 10000}},
    )

    logger.info(
        "CachedAnthropicModel created: model_id=claude-sonnet-4-6, "
        "thinking=enabled, budget_tokens=10000, cache_ttl=%s",
        CACHE_TTL,
    )
    return model
