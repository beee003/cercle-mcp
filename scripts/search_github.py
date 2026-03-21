"""Search GitHub for people by skills, language, location."""

import httpx
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def search_github(query: str, location: str = "", limit: int = 10) -> list[dict]:
    """Search GitHub users by skill/language and location."""

    # Build search query
    q_parts = [query]
    if location:
        q_parts.append(f"location:{location}")

    q = " ".join(q_parts)

    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    # Search users
    resp = httpx.get(
        "https://api.github.com/search/users",
        params={"q": q, "sort": "followers", "per_page": limit},
        headers=headers,
        timeout=15,
    )

    if resp.status_code != 200:
        print(f"[github] Error: {resp.status_code}")
        return []

    users = resp.json().get("items", [])
    results = []

    for u in users[:limit]:
        # Get detailed profile
        try:
            profile = httpx.get(
                f"https://api.github.com/users/{u['login']}",
                headers=headers,
                timeout=10,
            ).json()
        except Exception:
            profile = u

        # Get top repos
        try:
            repos_resp = httpx.get(
                f"https://api.github.com/users/{u['login']}/repos",
                params={"sort": "stars", "per_page": 3},
                headers=headers,
                timeout=10,
            )
            top_repos = [
                {
                    "name": r["name"],
                    "stars": r["stargazers_count"],
                    "language": r.get("language", ""),
                }
                for r in repos_resp.json()[:3]
                if isinstance(r, dict)
            ]
        except Exception:
            top_repos = []

        total_stars = sum(r["stars"] for r in top_repos)

        results.append(
            {
                "platform": "github",
                "username": u["login"],
                "name": profile.get("name", u["login"]),
                "bio": profile.get("bio", "") or "",
                "location": profile.get("location", "") or "",
                "company": profile.get("company", "") or "",
                "followers": profile.get("followers", 0),
                "public_repos": profile.get("public_repos", 0),
                "top_repos": top_repos,
                "total_stars": total_stars,
                "url": profile.get("html_url", u.get("html_url", "")),
                "email": profile.get("email", "") or "",
                "twitter": profile.get("twitter_username", "") or "",
                "hireable": profile.get("hireable", None),
                "score": profile.get("followers", 0) + total_stars * 2,
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"[github] Found {len(results)} people")
    return results


if __name__ == "__main__":
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "react"
    loc = sys.argv[2] if len(sys.argv) > 2 else ""
    for p in search_github(q, loc, 5):
        print(
            f"  @{p['username']} — {p['name']} — {p['location']} — {p['followers']} followers — {p['total_stars']}★"
        )
