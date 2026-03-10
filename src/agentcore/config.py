"""AgentCore Runtime configuration — loaded from environment variables."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

_ARN_PATTERN = re.compile(
    r"^arn:aws(-[^:]+)?:bedrock-agentcore:[a-z0-9-]+:\d{12}:runtime/.+$"
)


@dataclass(frozen=True)
class AgentCoreConfig:
    """Immutable configuration for calling an AgentCore Runtime endpoint."""

    runtime_arn: str
    region: str
    qualifier: str = field(default="DEFAULT")


def load_agentcore_config() -> AgentCoreConfig | None:
    """Load AgentCore endpoint configuration from environment variables.

    Returns:
        AgentCoreConfig if AGENTCORE_RUNTIME_ARN is set and valid.
        None if AGENTCORE_RUNTIME_ARN is not set (local fallback mode).

    Raises:
        EnvironmentError: If AGENTCORE_RUNTIME_ARN is set but malformed,
            or if AWS_REGION is missing when the ARN is present.
    """
    runtime_arn = os.environ.get("AGENTCORE_RUNTIME_ARN")
    if not runtime_arn:
        return None

    if not _ARN_PATTERN.match(runtime_arn):
        raise EnvironmentError(
            f"AGENTCORE_RUNTIME_ARN is set but has an invalid format: {runtime_arn!r}\n"
            "Expected format: arn:aws:bedrock-agentcore:{region}:{account}:runtime/{id}\n"
            "Check your .env file or environment configuration."
        )

    region = os.environ.get("AWS_REGION")
    if not region:
        raise EnvironmentError(
            "AWS_REGION must be set when AGENTCORE_RUNTIME_ARN is configured.\n"
            "Add AWS_REGION to your .env file."
        )

    return AgentCoreConfig(runtime_arn=runtime_arn, region=region)
