"""AnthropicModel factory for Claude Sonnet 4.6 with extended thinking."""

import logging
import os

from strands.models.anthropic import AnthropicModel

logger = logging.getLogger(__name__)


def create_model() -> AnthropicModel:
    """Return a configured AnthropicModel with extended thinking enabled.

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

    model = AnthropicModel(
        client_args={"api_key": api_key},
        max_tokens=16000,
        model_id="claude-sonnet-4-6",
        params={"thinking": {"type": "enabled", "budget_tokens": 10000}},
    )

    logger.info(
        "AnthropicModel created: model_id=claude-sonnet-4-6, "
        "thinking=enabled, budget_tokens=10000"
    )
    return model
