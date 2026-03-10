"""AgentCore HTTP SSE client — calls AgentCore Runtime with Cognito Bearer token."""

from __future__ import annotations

import json
import logging
import urllib.parse
from collections.abc import Generator
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ── Exceptions ─────────────────────────────────────────────────────────────────


class AgentCoreError(Exception):
    """Base exception for AgentCore Runtime invocation errors."""


class AgentCoreAuthError(AgentCoreError):
    """Raised when AgentCore rejects the request due to authentication failure (HTTP 401).

    Callers should clear the session and redirect the user to re-login.
    """


class AgentCoreUnavailableError(AgentCoreError):
    """Raised when AgentCore Runtime is temporarily unavailable (HTTP 503/504)."""


# ── Client ─────────────────────────────────────────────────────────────────────

_AGENTCORE_HOST = "https://bedrock-agentcore.{region}.amazonaws.com"
_SESSION_ID_HEADER = "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"


def invoke_streaming(
    runtime_arn: str,
    region: str,
    qualifier: str,
    session_id: str,
    access_token: str,
    prompt: str,
) -> Generator[dict[str, Any], None, None]:
    """Call the AgentCore Runtime endpoint and yield parsed SSE events.

    Args:
        runtime_arn: Full ARN of the AgentCore Runtime resource.
        region: AWS region (e.g. "us-east-1").
        qualifier: Runtime version qualifier (e.g. "DEFAULT").
        session_id: Session identifier (UUID v4, ≥33 chars).
        access_token: Cognito access token — sent as Bearer in Authorization header.
        prompt: User message text for this turn.

    Yields:
        Parsed SSE event dicts: {"type": "text"|"reasoning"|"tool_start"|
                                  "tool_result"|"error"|"done", ...}

    Raises:
        AgentCoreAuthError: HTTP 401 — token expired or invalid.
        AgentCoreUnavailableError: HTTP 503 or 504 — runtime temporarily unavailable.
        AgentCoreError: Any other non-200 response.
        requests.Timeout: Connection or read timeout exceeded.
    """
    encoded_arn = urllib.parse.quote(runtime_arn, safe="")
    host = _AGENTCORE_HOST.format(region=region)
    url = f"{host}/runtimes/{encoded_arn}/invocations?qualifier={qualifier}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        _SESSION_ID_HEADER: session_id,
    }

    logger.debug(
        "AgentCore invoke: url=%s session_id=%s prompt_len=%d",
        url,
        session_id,
        len(prompt),
    )

    response = requests.post(
        url,
        headers=headers,
        json={"prompt": prompt},
        stream=True,
        timeout=(5, 120),  # (connect_timeout, read_timeout) in seconds
    )

    if response.status_code == 401:
        raise AgentCoreAuthError(
            "Authentication rejected by AgentCore Runtime (HTTP 401). "
            "The Cognito access token may be expired or invalid."
        )
    if response.status_code in (503, 504):
        raise AgentCoreUnavailableError(
            f"AgentCore Runtime is temporarily unavailable (HTTP {response.status_code}). "
            "Please try again in a few moments."
        )
    if response.status_code != 200:
        raise AgentCoreError(
            f"AgentCore Runtime returned an unexpected status code: "
            f"{response.status_code}. Body: {response.text[:200]}"
        )

    # Consume the SSE stream line by line
    for raw_line in response.iter_lines():
        if not raw_line:
            continue  # blank lines are SSE separators

        if isinstance(raw_line, bytes):
            line = raw_line.decode("utf-8")
        else:
            line = raw_line

        if not line.startswith("data: "):
            continue  # skip comment lines or other SSE fields

        data_str = line[len("data: "):]
        try:
            event = json.loads(data_str)
        except json.JSONDecodeError:
            logger.warning("Skipping non-JSON SSE data: %r", data_str[:120])
            continue

        yield event
