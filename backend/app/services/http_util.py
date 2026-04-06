"""Shared HTTP client settings for outbound data fetchers."""

from __future__ import annotations

import httpx

DEFAULT_TIMEOUT = httpx.Timeout(25.0, connect=10.0)


def http_client() -> httpx.Client:
    return httpx.Client(
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": "LittleBuggy/1.0 (+https://github.com) surveillance fetcher"},
    )
