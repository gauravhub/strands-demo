"""Strands Demo — Streamlit entry point with Cognito authentication."""

import logging

import streamlit as st
from dotenv import load_dotenv

from src.auth.config import load_config
from src.auth.oauth import exchange_code, generate_auth_request, parse_id_token
from src.auth.session import clear_session, get_user, is_authenticated, store_session

logger = logging.getLogger(__name__)

# ── Startup ────────────────────────────────────────────────────────────────────

load_dotenv()
logging.basicConfig(level=logging.INFO)

try:
    config = load_config()
except EnvironmentError as e:
    st.error(f"Configuration error: {e}")
    st.stop()

st.set_page_config(page_title="Strands Demo", page_icon="🤖")


# ── UI Helpers ─────────────────────────────────────────────────────────────────


def show_landing(error_msg: str | None = None) -> None:
    """Render the unauthenticated landing page with an optional error message."""
    st.title("🤖 Strands Demo")
    st.write("A demo application using AWS Strands Agents.")
    st.divider()

    if error_msg:
        st.error(error_msg)

    if st.button("Login", type="primary", use_container_width=True):
        auth_url = generate_auth_request(config)
        # Meta-refresh redirect — works in Streamlit without custom components
        st.markdown(
            f'<meta http-equiv="refresh" content="0;url={auth_url}">',
            unsafe_allow_html=True,
        )
        st.stop()


def show_main_app() -> None:
    """Render the main application view for authenticated users."""
    user = get_user()
    st.title("🤖 Strands Demo")
    st.caption(f"Logged in as **{user.get('username', 'unknown')}**")
    st.divider()
    st.info("Welcome to Strands Demo — AWS Strands Agents with Cognito authentication.")

    # US3: Logout button
    if st.button("Logout", type="secondary"):
        clear_session()
        logout_url = (
            f"{config.logout_endpoint}"
            f"?client_id={config.client_id}"
            f"&logout_uri={config.redirect_uri}"
        )
        st.markdown(
            f'<meta http-equiv="refresh" content="0;url={logout_url}">',
            unsafe_allow_html=True,
        )
        st.stop()


# ── Routing ────────────────────────────────────────────────────────────────────

query_params = st.query_params

if is_authenticated():
    # Already logged in — show main app (US1 acceptance scenario 3)
    show_main_app()

elif "error" in query_params:
    # US2: Auth error callback — user cancelled or identity provider returned error
    error_code = query_params.get("error", "unknown_error")
    logger.info("Auth error callback received: %s", error_code)
    st.query_params.clear()
    st.session_state.pop("oauth_pending", None)
    show_landing(error_msg="Login was cancelled or failed. Please try again.")

elif "code" in query_params:
    # US1: Authorization code callback — exchange code for tokens
    code = query_params["code"]
    state = query_params.get("state", "")
    st.query_params.clear()

    try:
        tokens = exchange_code(code, state, config)
        user_info = parse_id_token(tokens["id_token"])
        store_session(tokens, user_info)
        st.rerun()
    except Exception as exc:
        logger.error("Auth callback failed: %s", exc)
        show_landing(error_msg="Authentication failed. Please try again.")

else:
    # Not authenticated, no callback — show landing page
    show_landing()
