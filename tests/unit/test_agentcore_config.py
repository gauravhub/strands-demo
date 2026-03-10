"""Unit tests for src/agentcore/config.py."""

import pytest

from src.agentcore.config import AgentCoreConfig, load_agentcore_config

_VALID_ARN = "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent"


def test_returns_none_when_env_var_absent(monkeypatch):
    """load_agentcore_config() returns None when AGENTCORE_RUNTIME_ARN is not set."""
    monkeypatch.delenv("AGENTCORE_RUNTIME_ARN", raising=False)
    assert load_agentcore_config() is None


def test_raises_on_malformed_arn(monkeypatch):
    """load_agentcore_config() raises EnvironmentError when ARN is malformed."""
    monkeypatch.setenv("AGENTCORE_RUNTIME_ARN", "not-an-arn")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    with pytest.raises(EnvironmentError, match="invalid format"):
        load_agentcore_config()


def test_raises_when_region_missing(monkeypatch):
    """load_agentcore_config() raises EnvironmentError when AWS_REGION is absent."""
    monkeypatch.setenv("AGENTCORE_RUNTIME_ARN", _VALID_ARN)
    monkeypatch.delenv("AWS_REGION", raising=False)
    with pytest.raises(EnvironmentError, match="AWS_REGION"):
        load_agentcore_config()


def test_returns_valid_config(monkeypatch):
    """load_agentcore_config() returns correct AgentCoreConfig with valid env vars."""
    monkeypatch.setenv("AGENTCORE_RUNTIME_ARN", _VALID_ARN)
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    result = load_agentcore_config()

    assert isinstance(result, AgentCoreConfig)
    assert result.runtime_arn == _VALID_ARN
    assert result.region == "us-east-1"
    assert result.qualifier == "DEFAULT"
