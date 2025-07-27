"""
Authentication utilities for Composer MCP Server.
"""

from fastmcp.server.dependencies import get_http_headers
from typing import Dict
import base64

def get_mcp_environment() -> str:
    """
    Get the environment of the MCP server.
    """
    headers = get_http_headers()
    return headers.get("x-composer-mcp-environment", "prod")

def _parse_authorization_header(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Parse the authorization header and extract API key and secret.
    Supports both Bearer and Basic authentication.
    
    For Bearer: expects x-api-key-id header and Bearer token in Authorization
    For Basic: expects base64(api_key:secret) in Authorization header
    """
    result_headers = headers.copy()
    auth_header = headers.get("authorization", "")
    
    if auth_header.startswith("Basic "):
        # Decode Basic auth: base64(api_key:secret)
        try:
            encoded_credentials = auth_header[6:]  # Remove "Basic " prefix
            decoded = base64.b64decode(encoded_credentials).decode('utf-8')
            api_key, secret = decoded.split(':', 1)
            result_headers["x-api-key-id"] = api_key
            # Convert to Bearer format for downstream compatibility
            result_headers["authorization"] = f"Bearer {secret}"
        except Exception:
            raise ValueError("Invalid basic auth header")
    
    return result_headers

def get_optional_headers() -> Dict[str, str]:
    """
    Get headers for optional authentication (read-only operations).
    Always includes x-origin. Only includes API key and secret if both are present.
    """
    headers = _parse_authorization_header(get_http_headers())
    headers["x-origin"] = "public-api"
    api_key = headers.get("x-api-key-id")
    secret_key = headers.get("authorization")
    if api_key and secret_key:
        return headers
    else:
        return {"x-origin": "public-api"}


def get_required_headers() -> Dict[str, str]:
    """
    Get headers for required authentication (write operations).
    Requires both API key and secret key to be present.
    """
    headers = _parse_authorization_header(get_http_headers())
    headers["x-origin"] = "public-api"
    api_key = headers.get("x-api-key-id")
    secret_key = headers.get("authorization")

    if not api_key:
        raise ValueError("X-Api-Key-Id header is required but not set")
    if not secret_key:
        raise ValueError("Authorization header is required but not set")

    return headers
