"""Unit tests for src/auth/oauth.py."""

import base64
import json
import urllib.parse
from unittest.mock import MagicMock, patch

import pytest

import src.auth.oauth as oauth_module
from src.auth.config import CognitoConfig
from src.auth.oauth import exchange_code, generate_auth_request, parse_id_token

# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def config() -> CognitoConfig:
    return CognitoConfig(
        region="us-east-1",
        user_pool_id="us-east-1_TestPool",
        client_id="test-client-id",
        client_secret="test-client-secret",
        domain="https://test.auth.us-east-1.amazoncognito.com",
        redirect_uri="http://localhost:8501",
    )


@pytest.fixture(autouse=True)
def clear_pending_states() -> None:
    """Reset module-level _pending_states before each test."""
    oauth_module._pending_states.clear()
    yield
    oauth_module._pending_states.clear()


def _make_id_token(claims: dict) -> str:
    """Build a synthetic (unsigned) JWT with given claims."""
    header = base64.urlsafe_b64encode(b'{"alg":"RS256","typ":"JWT"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.fakesignature"


# ── generate_auth_request ──────────────────────────────────────────────────────


class TestGenerateAuthRequest:
    def test_returns_authorization_url(self, config: CognitoConfig) -> None:
        url = generate_auth_request(config)
        assert url.startswith("https://test.auth.us-east-1.amazoncognito.com/oauth2/authorize")

    def test_url_contains_required_params(self, config: CognitoConfig) -> None:
        url = generate_auth_request(config)
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        assert params["response_type"] == ["code"]
        assert params["client_id"] == ["test-client-id"]
        assert params["redirect_uri"] == ["http://localhost:8501"]
        assert params["scope"] == ["openid email profile"]
        assert "state" in params
        assert "code_challenge" in params
        assert params["code_challenge_method"] == ["S256"]

    def test_stores_pending_state(self, config: CognitoConfig) -> None:
        generate_auth_request(config)
        assert len(oauth_module._pending_states) == 1

    def test_state_param_matches_stored_state(self, config: CognitoConfig) -> None:
        url = generate_auth_request(config)
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        state = params["state"][0]
        assert state in oauth_module._pending_states


# ── exchange_code ──────────────────────────────────────────────────────────────


class TestExchangeCode:
    def _setup_pending(self, state: str = "valid-state", verifier: str = "verifier123") -> None:
        oauth_module._pending_states[state] = verifier

    def test_raises_value_error_on_state_mismatch(self, config: CognitoConfig) -> None:
        self._setup_pending(state="correct-state")
        with pytest.raises(ValueError, match="State mismatch"):
            exchange_code("auth-code", "wrong-state", config)

    def test_raises_value_error_when_no_pending_state(self, config: CognitoConfig) -> None:
        # No pending state registered
        with pytest.raises(ValueError, match="State mismatch"):
            exchange_code("auth-code", "any-state", config)

    def test_returns_token_response_on_success(self, config: CognitoConfig) -> None:
        self._setup_pending(state="my-state")
        token_response = {
            "access_token": "access-abc",
            "id_token": "id-abc",
            "refresh_token": "refresh-abc",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = token_response

        with patch("src.auth.oauth.requests.post", return_value=mock_resp):
            result = exchange_code("auth-code", "my-state", config)

        assert result["access_token"] == "access-abc"
        assert result["id_token"] == "id-abc"

    def test_raises_runtime_error_on_failed_token_exchange(self, config: CognitoConfig) -> None:
        self._setup_pending(state="my-state")
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 400
        mock_resp.text = "invalid_grant"

        with patch("src.auth.oauth.requests.post", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="Token exchange failed"):
                exchange_code("auth-code", "my-state", config)


# ── parse_id_token ─────────────────────────────────────────────────────────────


class TestParseIdToken:
    def test_extracts_cognito_username(self) -> None:
        claims = {"cognito:username": "demo_user_1", "email": "demo1@example.com"}
        token = _make_id_token(claims)
        result = parse_id_token(token)
        assert result["cognito:username"] == "demo_user_1"
        assert result["email"] == "demo1@example.com"

    def test_extracts_email(self) -> None:
        claims = {"cognito:username": "demo_user_2", "email": "demo2@example.com", "sub": "uuid-123"}
        token = _make_id_token(claims)
        result = parse_id_token(token)
        assert result["email"] == "demo2@example.com"

    def test_raises_on_invalid_token_format(self) -> None:
        with pytest.raises(ValueError, match="Invalid ID token"):
            parse_id_token("not.a.valid.jwt.format.extra")

    def test_raises_on_malformed_token(self) -> None:
        with pytest.raises((ValueError, Exception)):
            parse_id_token("only-one-part")
