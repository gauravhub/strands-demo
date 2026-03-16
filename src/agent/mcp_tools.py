"""MCP Server tool loaders — connects to managed AWS MCP Servers via SigV4."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def get_eks_mcp_tools() -> tuple[Any | None, list]:
    """Load EKS MCP tools from the AWS-managed EKS MCP Server.

    Resolves the region from environment variables in order:
        EKS_MCP_REGION → AWS_REGION → AWS_DEFAULT_REGION

    Returns:
        Tuple of (mcp_client, tools_list). The caller is responsible for
        calling ``mcp_client.stop()`` when done.  On failure returns
        ``(None, [])``.
    """
    region = (
        os.getenv("EKS_MCP_REGION")
        or os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
    )
    if not region:
        logger.warning(
            "No AWS region configured for EKS MCP Server "
            "(set EKS_MCP_REGION, AWS_REGION, or AWS_DEFAULT_REGION). "
            "EKS tools will not be available."
        )
        return None, []

    endpoint = f"https://eks-mcp.{region}.api.aws/mcp"

    try:
        from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
        from strands.tools.mcp.mcp_client import MCPClient

        mcp_factory = lambda: aws_iam_streamablehttp_client(
            endpoint=endpoint,
            aws_region=region,
            aws_service="eks-mcp",
        )

        mcp_client = MCPClient(mcp_factory)
        mcp_client.__enter__()

        tools = mcp_client.list_tools_sync()
        logger.info(
            "EKS MCP tools loaded: region=%s endpoint=%s tool_count=%d",
            region,
            endpoint,
            len(tools),
        )
        return mcp_client, tools

    except Exception:
        logger.warning(
            "Failed to connect to EKS MCP Server at %s — "
            "EKS tools will not be available",
            endpoint,
            exc_info=True,
        )
        return None, []


def get_gateway_tools(gateway_url: str, access_token: str) -> tuple[Any | None, list]:
    """Load MCP tools from an AgentCore Gateway endpoint.

    Uses ``streamablehttp_client`` transport with Bearer token auth to connect
    to the Gateway and discover available tools (e.g. Tavily search).

    Args:
        gateway_url: Full Gateway MCP endpoint URL.
        access_token: Cognito access token — sent as Bearer in Authorization header.

    Returns:
        Tuple of (mcp_client, tools_list). The caller is responsible for
        calling ``mcp_client.__exit__()`` when done.  On failure returns
        ``(None, [])``.
    """
    if not gateway_url:
        logger.info("No Gateway URL configured — Gateway tools will not be available.")
        return None, []

    try:
        from mcp.client.streamable_http import streamablehttp_client
        from strands.tools.mcp.mcp_client import MCPClient

        mcp_factory = lambda: streamablehttp_client(
            url=gateway_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        mcp_client = MCPClient(mcp_factory)
        mcp_client.__enter__()

        tools = mcp_client.list_tools_sync()
        logger.info(
            "Gateway MCP tools loaded: url=%s tool_count=%d",
            gateway_url,
            len(tools),
        )
        return mcp_client, tools

    except Exception:
        logger.warning(
            "Failed to connect to AgentCore Gateway at %s — "
            "Gateway tools will not be available",
            gateway_url,
            exc_info=True,
        )
        return None, []


def get_aws_api_mcp_tools() -> tuple[Any | None, list]:
    """Load AWS MCP tools from the managed AWS MCP Server.

    Resolves the region from environment variables in order:
        AWS_MCP_REGION → AWS_REGION → AWS_DEFAULT_REGION

    Returns:
        Tuple of (mcp_client, tools_list). The caller is responsible for
        calling ``mcp_client.__exit__()`` when done.  On failure returns
        ``(None, [])``.
    """
    region = (
        os.getenv("AWS_MCP_REGION")
        or os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
    )
    if not region:
        logger.warning(
            "No AWS region configured for AWS MCP Server "
            "(set AWS_MCP_REGION, AWS_REGION, or AWS_DEFAULT_REGION). "
            "AWS MCP tools will not be available."
        )
        return None, []

    endpoint = f"https://aws-mcp.{region}.api.aws/mcp"

    try:
        from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
        from strands.tools.mcp.mcp_client import MCPClient

        mcp_factory = lambda: aws_iam_streamablehttp_client(
            endpoint=endpoint,
            aws_region=region,
            aws_service="aws-mcp",
        )

        mcp_client = MCPClient(mcp_factory)
        mcp_client.__enter__()

        tools = mcp_client.list_tools_sync()
        logger.info(
            "AWS MCP tools loaded: region=%s endpoint=%s tool_count=%d",
            region,
            endpoint,
            len(tools),
        )
        return mcp_client, tools

    except Exception:
        logger.warning(
            "Failed to connect to AWS MCP Server at %s — "
            "AWS MCP tools will not be available",
            endpoint,
            exc_info=True,
        )
        return None, []
