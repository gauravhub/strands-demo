"""Unit tests for src/agentcore/client.py."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.agentcore.client import (
    AgentCoreAuthError,
    AgentCoreError,
    AgentCoreUnavailableError,
    invoke_streaming,
)

_ARN = "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent"
_REGION = "us-east-1"
_QUALIFIER = "DEFAULT"
_SESSION_ID = "test-session-abcdefghijklmnopqrstuvwxyz"  # 36+ chars
_TOKEN = "eyJtest.token.here"
_PROMPT = "Hello agent"


def _make_mock_response(status_code: int, lines: list[str]) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = ""
    mock.iter_lines.return_value = [line.encode("utf-8") for line in lines]
    return mock


def test_url_encodes_arn():
    """invoke_streaming constructs a URL with the ARN percent-encoded."""
    mock_resp = _make_mock_response(200, ['data: {"type":"done"}'])
    with patch("src.agentcore.client.requests.post", return_value=mock_resp) as mock_post:
        list(invoke_streaming(_ARN, _REGION, _QUALIFIER, _SESSION_ID, _TOKEN, _PROMPT))
        called_url = mock_post.call_args[0][0]
    # Colons in the ARN must be percent-encoded as %3A
    assert "%3A" in called_url
    assert "invocations" in called_url
    assert f"qualifier={_QUALIFIER}" in called_url


def test_sets_auth_and_session_headers():
    """invoke_streaming sets Authorization Bearer and session-ID headers correctly."""
    mock_resp = _make_mock_response(200, ['data: {"type":"done"}'])
    with patch("src.agentcore.client.requests.post", return_value=mock_resp) as mock_post:
        list(invoke_streaming(_ARN, _REGION, _QUALIFIER, _SESSION_ID, _TOKEN, _PROMPT))
        headers = mock_post.call_args[1]["headers"]
    assert headers["Authorization"] == f"Bearer {_TOKEN}"
    assert headers["X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"] == _SESSION_ID
    assert headers["Content-Type"] == "application/json"


def test_raises_auth_error_on_401():
    """invoke_streaming raises AgentCoreAuthError on HTTP 401."""
    mock_resp = _make_mock_response(401, [])
    with patch("src.agentcore.client.requests.post", return_value=mock_resp):
        with pytest.raises(AgentCoreAuthError):
            list(invoke_streaming(_ARN, _REGION, _QUALIFIER, _SESSION_ID, _TOKEN, _PROMPT))


def test_raises_unavailable_error_on_503():
    """invoke_streaming raises AgentCoreUnavailableError on HTTP 503."""
    mock_resp = _make_mock_response(503, [])
    with patch("src.agentcore.client.requests.post", return_value=mock_resp):
        with pytest.raises(AgentCoreUnavailableError):
            list(invoke_streaming(_ARN, _REGION, _QUALIFIER, _SESSION_ID, _TOKEN, _PROMPT))


def test_raises_generic_error_on_unexpected_status():
    """invoke_streaming raises AgentCoreError on unexpected non-200 status."""
    mock_resp = _make_mock_response(500, [])
    mock_resp.text = "Internal Server Error"
    with patch("src.agentcore.client.requests.post", return_value=mock_resp):
        with pytest.raises(AgentCoreError):
            list(invoke_streaming(_ARN, _REGION, _QUALIFIER, _SESSION_ID, _TOKEN, _PROMPT))


def test_yields_parsed_sse_events():
    """invoke_streaming yields correctly parsed dicts from SSE data lines."""
    lines = [
        'data: {"type":"text","data":"hello"}',
        "",  # blank separator
        'data: {"type":"done"}',
    ]
    mock_resp = _make_mock_response(200, lines)
    with patch("src.agentcore.client.requests.post", return_value=mock_resp):
        events = list(invoke_streaming(_ARN, _REGION, _QUALIFIER, _SESSION_ID, _TOKEN, _PROMPT))

    assert len(events) == 2
    assert events[0] == {"type": "text", "data": "hello"}
    assert events[1] == {"type": "done"}


def test_skips_non_data_sse_lines():
    """invoke_streaming skips SSE lines that don't start with 'data: '."""
    lines = [
        ": this is a comment",
        "event: update",
        'data: {"type":"text","data":"hi"}',
        'data: {"type":"done"}',
    ]
    mock_resp = _make_mock_response(200, lines)
    with patch("src.agentcore.client.requests.post", return_value=mock_resp):
        events = list(invoke_streaming(_ARN, _REGION, _QUALIFIER, _SESSION_ID, _TOKEN, _PROMPT))

    assert len(events) == 2
    assert events[0]["type"] == "text"
