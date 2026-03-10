"""Unit tests for src/auth/config.py."""

import pytest

from src.auth.config import CognitoConfig, load_config

REQUIRED_VARS = {
    "AWS_REGION": "us-east-1",
    "COGNITO_USER_POOL_ID": "us-east-1_TestPool",
    "COGNITO_CLIENT_ID": "test-client-id",
    "COGNITO_CLIENT_SECRET": "test-client-secret",
    "COGNITO_DOMAIN": "https://test.auth.us-east-1.amazoncognito.com",
    "COGNITO_REDIRECT_URI": "http://localhost:8501",
}


def _set_all_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in REQUIRED_VARS.items():
        monkeypatch.setenv(key, value)


class TestLoadConfig:
    def test_succeeds_when_all_vars_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_all_vars(monkeypatch)
        cfg = load_config()
        assert isinstance(cfg, CognitoConfig)
        assert cfg.region == "us-east-1"
        assert cfg.client_id == "test-client-id"
        assert cfg.domain == "https://test.auth.us-east-1.amazoncognito.com"

    def test_strips_trailing_slash_from_domain(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_all_vars(monkeypatch)
        monkeypatch.setenv("COGNITO_DOMAIN", "https://test.auth.us-east-1.amazoncognito.com/")
        cfg = load_config()
        assert not cfg.domain.endswith("/")

    @pytest.mark.parametrize("missing_var", list(REQUIRED_VARS.keys()))
    def test_raises_when_var_missing(self, monkeypatch: pytest.MonkeyPatch, missing_var: str) -> None:
        _set_all_vars(monkeypatch)
        monkeypatch.delenv(missing_var, raising=False)
        with pytest.raises(EnvironmentError) as exc_info:
            load_config()
        assert missing_var in str(exc_info.value)

    def test_error_message_lists_all_missing_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for key in REQUIRED_VARS:
            monkeypatch.delenv(key, raising=False)
        with pytest.raises(EnvironmentError) as exc_info:
            load_config()
        # All missing vars should appear in the error message
        for key in REQUIRED_VARS:
            assert key in str(exc_info.value)


class TestCognitoConfigProperties:
    def test_token_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_all_vars(monkeypatch)
        cfg = load_config()
        assert cfg.token_endpoint == "https://test.auth.us-east-1.amazoncognito.com/oauth2/token"

    def test_authorize_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_all_vars(monkeypatch)
        cfg = load_config()
        assert cfg.authorize_endpoint == "https://test.auth.us-east-1.amazoncognito.com/oauth2/authorize"

    def test_logout_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_all_vars(monkeypatch)
        cfg = load_config()
        assert cfg.logout_endpoint == "https://test.auth.us-east-1.amazoncognito.com/logout"
