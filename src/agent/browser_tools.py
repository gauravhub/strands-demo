"""Lightweight AgentCore Browser tools using BrowserClient + CDP over WebSocket.

No Playwright dependency — uses websockets sync client to send Chrome DevTools
Protocol commands directly to the AgentCore Browser automation stream.
"""

from __future__ import annotations

import json
import logging
import os
import time
from itertools import count

from strands import tool

logger = logging.getLogger(__name__)

_id_counter = count(1)


def _cdp(ws, method: str, params: dict | None = None) -> dict:
    """Send a CDP command over WebSocket and return the result."""
    msg_id = next(_id_counter)
    payload: dict = {"id": msg_id, "method": method}
    if params:
        payload["params"] = params

    ws.send(json.dumps(payload))

    # Read messages until we get the response for our ID
    while True:
        raw = ws.recv()
        msg = json.loads(raw)
        if msg.get("id") == msg_id:
            if "error" in msg:
                raise RuntimeError(f"CDP error in {method}: {msg['error']}")
            return msg.get("result", {})
        # Ignore CDP events (method-only messages) and other responses


def _browse(url: str, capture_screenshot: bool = True) -> dict:
    """Start browser session, navigate to URL, optionally screenshot, then stop.

    Returns dict with keys: title, content, screenshot_b64 (if requested).
    """
    from bedrock_agentcore.tools.browser_client import BrowserClient
    from websockets.sync.client import connect

    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    client = BrowserClient(region=region)

    try:
        client.start(session_timeout_seconds=300)
        ws_url, headers = client.generate_ws_headers()

        with connect(ws_url, additional_headers=headers, open_timeout=30) as ws:
            # Enable page events
            _cdp(ws, "Page.enable")

            # Navigate
            _cdp(ws, "Page.navigate", {"url": url})
            time.sleep(5)  # Wait for page load

            # Get page title
            title_result = _cdp(ws, "Runtime.evaluate", {"expression": "document.title"})
            title = title_result.get("result", {}).get("value", "Unknown page")

            # Get text content (first 3000 chars)
            content_result = _cdp(ws, "Runtime.evaluate", {
                "expression": "document.body.innerText.substring(0, 3000)"
            })
            content = content_result.get("result", {}).get("value", "")

            result = {"title": title, "content": content}

            # Take screenshot if requested
            if capture_screenshot:
                screenshot_result = _cdp(ws, "Page.captureScreenshot", {"format": "png"})
                result["screenshot_b64"] = screenshot_result.get("data", "")

            return result

    finally:
        try:
            client.stop()
        except Exception:
            logger.warning("Failed to stop browser session", exc_info=True)


@tool
def take_screenshot(url: str) -> str:
    """Navigate to a URL and take a screenshot of the webpage.

    Use this tool when the user asks to screenshot, capture, or visually inspect
    a website. Returns a base64 PNG image that will be displayed inline in the chat.

    Args:
        url: The full URL to navigate to and screenshot (e.g. https://example.com).
    """
    try:
        result = _browse(url, capture_screenshot=True)
        b64 = result.get("screenshot_b64", "")
        title = result.get("title", "")
        content = result.get("content", "")[:500]

        parts = [f"Screenshot of '{title}':"]
        if b64:
            parts.append(f"\ndata:image/png;base64,{b64}")
        if content:
            parts.append(f"\nPage content preview:\n{content}")
        return "\n".join(parts)

    except Exception as e:
        logger.error("Browser screenshot failed: %s", e, exc_info=True)
        return f"Error taking screenshot of {url}: {type(e).__name__}: {e}"


@tool
def browse_webpage(url: str) -> str:
    """Navigate to a URL and return a text description of the page content.

    Use this tool when the user asks to browse, read, or describe what's on a
    webpage without needing a visual screenshot.

    Args:
        url: The full URL to browse (e.g. https://example.com).
    """
    try:
        result = _browse(url, capture_screenshot=False)
        title = result.get("title", "")
        content = result.get("content", "")
        return f"Page: {title}\n\nContent:\n{content}"

    except Exception as e:
        logger.error("Browser browse failed: %s", e, exc_info=True)
        return f"Error browsing {url}: {type(e).__name__}: {e}"


def load_browser_tools() -> list:
    """Return the browser tools list for the agent.

    Returns empty list if dependencies are unavailable (graceful degradation).
    """
    try:
        # Verify dependencies are importable
        from bedrock_agentcore.tools.browser_client import BrowserClient  # noqa: F401
        from websockets.sync.client import connect  # noqa: F401

        tools = [take_screenshot, browse_webpage]
        logger.info("AgentCore Browser tools loaded: tool_count=%d (lightweight CDP)", len(tools))
        return tools

    except Exception as e:
        logger.error(
            "Failed to load AgentCore Browser tools — "
            "browser capabilities will not be available: %s: %s",
            type(e).__name__, e,
            exc_info=True,
        )
        return []
