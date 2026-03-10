"""Session management helpers — thin wrappers around st.session_state."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    pass

_SESSION_KEY = "user_session"
_PENDING_KEY = "oauth_pending"


def store_session(tokens: dict, user_info: dict) -> None:
    """Store authenticated session in Streamlit session state.

    Args:
        tokens: Token response from Cognito (access_token, id_token, etc.)
        user_info: Decoded claims from the ID token (username, email)
    """
    st.session_state[_SESSION_KEY] = {
        "access_token": tokens["access_token"],
        "id_token": tokens["id_token"],
        "refresh_token": tokens.get("refresh_token", ""),
        "expires_at": int(time.time()) + int(tokens.get("expires_in", 3600)),
        "username": user_info.get("cognito:username") or user_info.get("username", ""),
        "email": user_info.get("email", ""),
    }


def is_authenticated() -> bool:
    """Return True if a valid session exists in session state."""
    return _SESSION_KEY in st.session_state and bool(st.session_state[_SESSION_KEY])


def get_user() -> dict:
    """Return the current user info dict, or empty dict if not authenticated."""
    return st.session_state.get(_SESSION_KEY, {})


def clear_session() -> None:
    """Clear the authenticated session and any pending OAuth state."""
    st.session_state.pop(_SESSION_KEY, None)
    st.session_state.pop(_PENDING_KEY, None)
