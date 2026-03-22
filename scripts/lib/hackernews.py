"""Hacker News people search — find experts from comments on a topic."""

from __future__ import annotations
from .models import Person
from .http import get_client


def search(query: str, limit: int = 10) -> list[Person]:
    """Find HN users who comment about a topic, ranked by karma."""
    print("\u23f3 \033[93mHN\033[0m Searching for people...")

    client = get_client()

    try:
        resp = client.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": "comment", "hitsPerPage": 50},
        )
        if resp.status_code != 200:
            print(f"\033[91m\u2717 HN\033[0m Error: {resp.status_code}")
            return []
        hits = resp.json().get("hits", [])
    except Exception as e:
        print(f"\033[91m\u2717 HN\033[0m {e}")
        return []

    # Aggregate by author
    authors: dict[str, dict] = {}
    for h in hits:
        author = h.get("author", "")
        if not author:
            continue
        if author not in authors:
            authors[author] = {"comments": [], "points": 0, "count": 0}
        text = (h.get("comment_text", "") or "")[:200]
        authors[author]["comments"].append(text)
        authors[author]["points"] += h.get("points", 0) or 0
        authors[author]["count"] += 1

    # Enrich top authors with karma
    sorted_authors = sorted(authors.items(), key=lambda x: x[1]["count"], reverse=True)
    results = []

    for username, data in sorted_authors[:limit]:
        karma = 0
        about = ""
        try:
            user_resp = client.get(
                f"https://hn.algolia.com/api/v1/users/{username}",
            )
            if user_resp.status_code == 200:
                ud = user_resp.json()
                karma = ud.get("karma", 0)
                about = (ud.get("about", "") or "")[:200]
        except Exception:
            pass

        p = Person(
            username=username,
            platform="hn",
            name=username,
            url=f"https://news.ycombinator.com/user?id={username}",
            hn_karma=karma,
            hn_comment_count=data["count"],
            hn_about=about,
            hn_top_comment=data["comments"][0][:150] if data["comments"] else "",
            score=karma + data["count"] * 10,
            platforms_found=["hn"],
        )
        results.append(p)

    results.sort(key=lambda x: x.score, reverse=True)
    print(f"\u2713 \033[93mHN\033[0m Found {len(results)} people")
    return results
