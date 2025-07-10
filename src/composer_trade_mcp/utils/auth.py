"""
Authentication utilities for Composer MCP Server.
"""
import os
from typing import Dict


def get_optional_headers() -> Dict[str, str]:
    """
    Get headers for optional authentication (read-only operations).
    Always includes x-origin. Only includes API key and secret if both are present.
    """
    headers = {"x-origin": "public-api"}
    api_key = os.getenv("COMPOSER_API_KEY")
    secret_key = os.getenv("COMPOSER_SECRET_KEY")

    # Only include both keys if both are present
    if api_key and secret_key:
        headers["x-api-key-id"] = api_key
        headers["Authorization"] = f"Bearer {secret_key}"

    return headers


def get_required_headers() -> Dict[str, str]:
    """
    Get headers for required authentication (write operations).
    Requires both API key and secret key to be present.
    """
    api_key = os.getenv("COMPOSER_API_KEY")
    secret_key = os.getenv("COMPOSER_SECRET_KEY")

    if not api_key:
        raise ValueError("COMPOSER_API_KEY environment variable is required but not set")
    if not secret_key:
        raise ValueError("COMPOSER_SECRET_KEY environment variable is required but not set")

    headers = {
        "x-origin": "public-api",
        "x-api-key-id": api_key,
        "Authorization": f"Bearer {secret_key}"
    }
    return headers
