"""Shared HTTP client with timeouts."""

import httpx

_client: httpx.Client | None = None


def get_client(timeout: float = 15.0) -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Cercle/0.1 (people-search)"},
        )
    return _client


def get(url: str, **kwargs) -> httpx.Response:
    return get_client().get(url, **kwargs)


def post(url: str, **kwargs) -> httpx.Response:
    return get_client().post(url, **kwargs)
