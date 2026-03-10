"""OAuth2 authorization code flow with PKCE — outbound and inbound handlers."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
import urllib.parse

import requests

from src.auth.config import CognitoConfig

logger = logging.getLogger(__name__)

# Server-side store mapping state_token → code_verifier.
# Keyed by the opaque `state` value that Cognito echoes back in the redirect,
# so we can retrieve the verifier without relying on st.session_state (which is
# reset when the browser navigates away to the Cognito Hosted UI and back).
_pending_states: dict[str, str] = {}


# ── Part A: Outbound (build authorization URL) ─────────────────────────────────


def _generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    code_verifier = secrets.token_urlsafe(64)  # 86 URL-safe chars — within 43-128 range
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


def generate_auth_request(config: CognitoConfig) -> str:
    """Build the Cognito authorization URL and store PKCE state server-side.

    Returns:
        Authorization URL to redirect the user's browser to.
    """
    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = _generate_pkce_pair()

    # Store verifier keyed by state — survives the browser redirect to Cognito
    _pending_states[state] = code_verifier

    params = {
        "response_type": "code",
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        "scope": "openid email profile",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{config.authorize_endpoint}?{urllib.parse.urlencode(params)}"


# ── Part B: Inbound (exchange code for tokens) ─────────────────────────────────


def exchange_code(code: str, state: str, config: CognitoConfig) -> dict:
    """Exchange authorization code for tokens.

    Args:
        code: Authorization code from Cognito callback (?code=...).
        state: State parameter from callback — validated against stored value.
        config: Cognito configuration.

    Returns:
        Parsed token response dict (access_token, id_token, refresh_token, expires_in).

    Raises:
        ValueError: If state does not match stored value (CSRF protection).
        RuntimeError: If token exchange request fails.
    """
    code_verifier = _pending_states.pop(state, None)

    if code_verifier is None:
        logger.error("CSRF state mismatch detected — possible replay attack")
        raise ValueError("State mismatch: possible CSRF attack. Please try logging in again.")

    response = requests.post(
        config.token_endpoint,
        data={
            "grant_type": "authorization_code",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "redirect_uri": config.redirect_uri,
            "code": code,
            "code_verifier": code_verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )

    if not response.ok:
        logger.error("Token exchange failed: %s", response.text)
        raise RuntimeError(f"Token exchange failed ({response.status_code}): {response.text}")

    return response.json()


def parse_id_token(id_token: str) -> dict:
    """Decode JWT ID token claims without signature verification (demo only).

    Args:
        id_token: JWT string from Cognito token response.

    Returns:
        Dict of claims (cognito:username, email, etc.)
    """
    # JWT structure: header.payload.signature — decode the payload (middle part)
    parts = id_token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid ID token format")

    # Add padding if needed for base64 decoding
    payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
    payload_bytes = base64.urlsafe_b64decode(payload_b64)
    return json.loads(payload_bytes)
