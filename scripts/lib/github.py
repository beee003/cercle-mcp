"""GitHub people search — users, repos, stars, hireable status."""

from __future__ import annotations
import os
from .models import Person
from .http import get_client

TOKEN = os.getenv("GITHUB_TOKEN", "")


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def search(query: str, location: str = "", limit: int = 10) -> list[Person]:
    """Search GitHub users by skill keywords and location."""
    print("\u23f3 \033[95mGitHub\033[0m Searching for people...")

    q_parts = [query]
    if location:
        q_parts.append(f"location:{location}")

    client = get_client()
    headers = _headers()

    try:
        resp = client.get(
            "https://api.github.com/search/users",
            params={"q": " ".join(q_parts), "sort": "followers", "per_page": limit},
            headers=headers,
        )
        if resp.status_code != 200:
            print(f"\033[91m\u2717 GitHub\033[0m Error: {resp.status_code}")
            return []

        users = resp.json().get("items", [])
    except Exception as e:
        print(f"\033[91m\u2717 GitHub\033[0m {e}")
        return []

    results = []
    for u in users[:limit]:
        try:
            profile = client.get(
                f"https://api.github.com/users/{u['login']}",
                headers=headers,
            ).json()
        except Exception:
            profile = u

        # Top repos
        try:
            repos_resp = client.get(
                f"https://api.github.com/users/{u['login']}/repos",
                params={"sort": "stars", "per_page": 5},
                headers=headers,
            )
            repos = [
                {
                    "name": r["name"],
                    "stars": r["stargazers_count"],
                    "language": r.get("language", ""),
                }
                for r in repos_resp.json()[:5]
                if isinstance(r, dict)
            ]
        except Exception:
            repos = []

        total_stars = sum(r["stars"] for r in repos)
        languages = list({r["language"] for r in repos if r.get("language")})

        p = Person(
            username=u["login"],
            platform="github",
            name=profile.get("name", "") or u["login"],
            bio=(profile.get("bio", "") or "")[:200],
            location=profile.get("location", "") or "",
            company=profile.get("company", "") or "",
            url=profile.get("html_url", ""),
            email=profile.get("email", "") or "",
            followers=profile.get("followers", 0),
            github_stars=total_stars,
            github_repos=profile.get("public_repos", 0),
            github_top_repos=repos,
            github_hireable=bool(profile.get("hireable")),
            github_languages=languages,
            x_handle=profile.get("twitter_username", "") or "",
            score=profile.get("followers", 0)
            + total_stars * 2
            + (50 if profile.get("hireable") else 0),
            platforms_found=["github"],
        )
        results.append(p)

    results.sort(key=lambda x: x.score, reverse=True)
    print(f"\u2713 \033[95mGitHub\033[0m Found {len(results)} people")
    return results
