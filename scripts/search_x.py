"""Search X/Twitter for people by expertise using web search as proxy."""

import httpx
import os
import re


def search_x(query: str, limit: int = 10) -> list[dict]:
    """Search for people on X talking about a topic."""

    # Use xAI API if available (same as last30days)
    xai_key = os.getenv("XAI_API_KEY", "")

    if xai_key:
        return _search_xai(query, xai_key, limit)

    # Fallback: use web search to find X profiles
    return _search_web_proxy(query, limit)


def _search_xai(query: str, api_key: str, limit: int) -> list[dict]:
    """Search X via xAI Grok API."""
    try:
        resp = httpx.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-3-mini-fast",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Find {limit} real X/Twitter accounts of people who are experts in: {query}. For each person return their @handle, name, bio, follower count, and why they're relevant. Format as a list.",
                    }
                ],
                "max_tokens": 500,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            return []

        text = resp.json()["choices"][0]["message"]["content"]

        # Parse handles from response
        handles = re.findall(r"@(\w+)", text)
        results = []
        for h in handles[:limit]:
            results.append(
                {
                    "platform": "x",
                    "username": h,
                    "name": h,
                    "bio": "",
                    "url": f"https://x.com/{h}",
                    "followers": 0,
                    "score": 50,
                    "raw_context": text,
                }
            )
        print(f"[x] Found {len(results)} people via xAI")
        return results
    except Exception as e:
        print(f"[x] xAI error: {e}")
        return []


def _search_web_proxy(query: str, limit: int) -> list[dict]:
    """Fallback: search web for X profiles related to a query."""
    # This is a placeholder - in production, use the bird-search client from last30days
    print(f"[x] Web proxy search for: {query}")
    return []


if __name__ == "__main__":
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "react developer"
    for p in search_x(q, 5):
        print(f"  @{p['username']} — {p.get('bio', '')[:60]}")
