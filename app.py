"""Strands Demo — Streamlit entry point with Cognito authentication."""

import logging
import os
import uuid

import streamlit as st
from dotenv import load_dotenv

from src.agent.chatbot import create_agent
from src.agentcore.config import load_agentcore_config
from src.auth.config import load_config
from src.auth.oauth import exchange_code, generate_auth_request, parse_id_token
from src.auth.session import clear_session, get_user, is_authenticated, store_session
from src.chat.ui import render_chatbot, render_chatbot_agentcore

logger = logging.getLogger(__name__)

# ── Startup ────────────────────────────────────────────────────────────────────

load_dotenv()
log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(level=log_level)

# Validate required env vars before anything else
_missing = [k for k in ("ANTHROPIC_API_KEY",) if not os.getenv(k)]
if _missing:
    st.error(
        f"Missing required environment variables: {', '.join(_missing)}. "
        "Add them to your .env file and restart."
    )
    st.stop()

# Gateway configuration — optional; when set, Tavily tools are loaded from Gateway.
_gateway_url = os.getenv("AGENTCORE_GATEWAY_URL", "")

try:
    config = load_config()
except EnvironmentError as e:
    st.error(f"Configuration error: {e}")
    st.stop()

# AgentCore configuration — optional; None = local fallback mode.
# Set AGENTCORE_RUNTIME_ARN in .env to route invocations to AgentCore.
try:
    _agentcore_config = load_agentcore_config()
except EnvironmentError as e:
    st.error(f"AgentCore configuration error: {e}")
    st.stop()

if _agentcore_config:
    logger.info("AgentCore mode: runtime_arn=%s", _agentcore_config.runtime_arn)
else:
    logger.info("Local agent mode (AGENTCORE_RUNTIME_ARN not set)")

st.set_page_config(page_title="Amazon Bedrock AgentCore Demo", page_icon="🤖", layout="wide")


# ── UI Helpers ─────────────────────────────────────────────────────────────────


def show_landing(error_msg: str | None = None) -> None:
    """Render the unauthenticated landing page with an optional error message."""
    st.title("Amazon Bedrock AgentCore Demo")
    st.markdown("An AI agent demo powered by **AWS Strands Agents SDK** and **Amazon Bedrock AgentCore**.")
    st.divider()

    if error_msg:
        st.error(error_msg)

    # Generate auth URL eagerly so st.link_button renders a direct <a> tag.
    # No JS redirect needed — works on SCC, localhost, and headless browsers.
    auth_url = generate_auth_request(config)
    st.link_button("Sign In with AWS Cognito", auth_url, type="primary", use_container_width=False)


def show_main_app() -> None:
    """Render the main application view for authenticated users."""
    user = get_user()
    username = user.get("username", "unknown")

    if _agentcore_config:
        session_id = st.session_state.setdefault(
            "agentcore_session_id", str(uuid.uuid4())
        )
        mode_label = "AgentCore"
    else:
        session_id = st.session_state.setdefault(
            "local_session_id", str(uuid.uuid4())
        )
        mode_label = "Local"

    logout_url = (
        f"{config.logout_endpoint}"
        f"?client_id={config.client_id}"
        f"&logout_uri={config.redirect_uri}"
    )

    # Header bar: title on the left, user info + logout on the right
    header_left, header_right = st.columns([3, 1])
    with header_left:
        st.title("Amazon Bedrock AgentCore Demo")
    with header_right:
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 16px;">
                <span style="font-size: 0.9em; color: #555;">
                    <strong>{username}</strong> &nbsp;|&nbsp; Mode: {mode_label}
                </span>
                <br/>
                <span style="font-size: 0.8em; color: #888;">
                    Session: <code>{session_id}</code>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button("Sign Out", logout_url, type="secondary", use_container_width=True)

    st.divider()

    memory_id = os.getenv("AGENTCORE_MEMORY_ID", "")

    if _agentcore_config:
        render_chatbot_agentcore(
            config=_agentcore_config,
            access_token=user["access_token"],
            session_id=session_id,
            username=user["username"],
        )
    else:
        # Local fallback mode — run agent in-process (feature 003 behaviour)
        try:
            agent, _mcp_clients, _session_mgr = create_agent(
                memory_id=memory_id or None,
                session_id=session_id,
                actor_id=user["username"],
                gateway_url=_gateway_url or None,
                access_token=user["access_token"] if _gateway_url else None,
            )
        except EnvironmentError as e:
            st.error(str(e))
            st.stop()
        render_chatbot(agent)


# ── Routing ────────────────────────────────────────────────────────────────────

query_params = st.query_params

# Handle AgentCore token-expiry signal — reactive re-login redirect
if st.session_state.pop("agentcore_auth_expired", False):
    clear_session()
    show_landing(error_msg="Your session has expired, please log in again.")

elif is_authenticated():
    # Already logged in — show main app
    show_main_app()

elif "error" in query_params:
    # Auth error callback — user cancelled or identity provider returned error
    error_code = query_params.get("error", "unknown_error")
    logger.info("Auth error callback received: %s", error_code)
    st.query_params.clear()
    st.session_state.pop("oauth_pending", None)
    show_landing(error_msg="Login was cancelled or failed. Please try again.")

elif "code" in query_params:
    # Authorization code callback — exchange code for tokens
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
