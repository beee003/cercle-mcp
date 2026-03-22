"""X/Twitter people search via xAI Grok API."""

from __future__ import annotations
import os
import re
from .models import Person
from .http import get_client

XAI_API_KEY = os.getenv("XAI_API_KEY", "")


def search(query: str, limit: int = 10) -> list[Person]:
    """Find people on X who are experts in a topic."""
    if not XAI_API_KEY:
        print("\033[90m\u2717 X\033[0m Skipped (no XAI_API_KEY)")
        return []

    print("\u23f3 \033[96mX\033[0m Searching for people...")

    prompt = (
        f"Find {limit} real, active X/Twitter accounts of people who are experts in: {query}.\n"
        f"For each person, provide:\n"
        f"- @handle\n"
        f"- Full name\n"
        f"- Short bio (what they do)\n"
        f"- Approximate follower count\n"
        f"- Why they're relevant to this search\n"
        f"Only include real accounts. Format each as: @handle | Name | Bio | ~Nk followers | Reason"
    )

    client = get_client()
    try:
        resp = client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-3-mini-fast",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            print(f"\033[91m\u2717 X\033[0m Error: {resp.status_code}")
            return []

        text = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"\033[91m\u2717 X\033[0m {e}")
        return []

    # Parse structured response
    results = []
    for line in text.split("\n"):
        handles = re.findall(r"@(\w+)", line)
        if not handles:
            continue

        handle = handles[0]
        parts = line.split("|")

        name = parts[1].strip() if len(parts) > 1 else handle
        bio = parts[2].strip() if len(parts) > 2 else ""
        followers_str = parts[3].strip() if len(parts) > 3 else "0"
        reason = parts[4].strip() if len(parts) > 4 else ""

        # Parse follower count
        followers = 0
        nums = re.findall(r"([\d.]+)\s*[kKmM]?", followers_str)
        if nums:
            n = float(nums[0])
            if "m" in followers_str.lower():
                followers = int(n * 1_000_000)
            elif "k" in followers_str.lower():
                followers = int(n * 1_000)
            else:
                followers = int(n)

        p = Person(
            username=handle,
            platform="x",
            name=name,
            bio=bio[:200],
            url=f"https://x.com/{handle}",
            x_handle=handle,
            x_followers=followers,
            x_bio=bio,
            followers=followers,
            score=followers + 50,
            platforms_found=["x"],
        )
        results.append(p)

    results = results[:limit]
    results.sort(key=lambda x: x.score, reverse=True)
    print(f"\u2713 \033[96mX\033[0m Found {len(results)} people")
    return results
