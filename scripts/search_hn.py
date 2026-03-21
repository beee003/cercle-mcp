"""Search Hacker News for people by expertise."""

import httpx


def search_hn(query: str, limit: int = 10) -> list[dict]:
    """Search HN for active users discussing a topic."""

    # Search stories and comments about the topic
    resp = httpx.get(
        "https://hn.algolia.com/api/v1/search",
        params={"query": query, "tags": "comment", "hitsPerPage": 50},
        timeout=15,
    )

    if resp.status_code != 200:
        print(f"[hn] Error: {resp.status_code}")
        return []

    hits = resp.json().get("hits", [])

    # Aggregate by author
    authors = {}
    for h in hits:
        author = h.get("author", "")
        if not author:
            continue
        if author not in authors:
            authors[author] = {
                "platform": "hn",
                "username": author,
                "name": author,
                "comments": [],
                "total_points": 0,
                "comment_count": 0,
            }
        authors[author]["comments"].append(
            {
                "text": (h.get("comment_text", "") or "")[:200],
                "points": h.get("points", 0) or 0,
                "story_title": h.get("story_title", ""),
            }
        )
        authors[author]["total_points"] += h.get("points", 0) or 0
        authors[author]["comment_count"] += 1

    # Get user karma for top authors
    results = []
    sorted_authors = sorted(
        authors.values(), key=lambda x: x["comment_count"], reverse=True
    )

    for a in sorted_authors[:limit]:
        try:
            user_resp = httpx.get(
                f"https://hn.algolia.com/api/v1/users/{a['username']}",
                timeout=10,
            )
            if user_resp.status_code == 200:
                user_data = user_resp.json()
                a["karma"] = user_data.get("karma", 0)
                a["about"] = (user_data.get("about", "") or "")[:200]
            else:
                a["karma"] = 0
                a["about"] = ""
        except Exception:
            a["karma"] = 0
            a["about"] = ""

        a["url"] = f"https://news.ycombinator.com/user?id={a['username']}"
        a["score"] = a["karma"] + a["comment_count"] * 10
        a["top_comment"] = a["comments"][0]["text"][:150] if a["comments"] else ""
        results.append(a)

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"[hn] Found {len(results)} people")
    return results


if __name__ == "__main__":
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "react"
    for p in search_hn(q, 5):
        print(
            f"  {p['username']} — {p['karma']} karma — {p['comment_count']} comments on topic"
        )
