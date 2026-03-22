"""Stack Overflow people search — find experts by tag and reputation."""

from __future__ import annotations
from .models import Person
from .http import get_client


def search(query: str, limit: int = 10) -> list[Person]:
    """Search Stack Overflow users by tag expertise."""
    print("\u23f3 \033[33mSO\033[0m Searching for people...")

    # Map query to likely SO tags
    tag = (
        query.lower().replace(" ", "-").split("-")[0]
    )  # e.g. "react" from "react developer"

    client = get_client()

    try:
        # Search by tag top users
        resp = client.get(
            "https://api.stackexchange.com/2.3/tags/{}/top-answerers/all_time".format(
                tag
            ),
            params={"site": "stackoverflow", "pagesize": limit},
        )
        if resp.status_code != 200:
            # Fallback: search users by name
            resp = client.get(
                "https://api.stackexchange.com/2.3/users",
                params={
                    "site": "stackoverflow",
                    "inname": query.split()[0],
                    "sort": "reputation",
                    "pagesize": limit,
                },
            )
            if resp.status_code != 200:
                print(f"\033[91m\u2717 SO\033[0m Error: {resp.status_code}")
                return []
            items = resp.json().get("items", [])
            return _parse_users(items, limit)

        items = resp.json().get("items", [])
    except Exception as e:
        print(f"\033[91m\u2717 SO\033[0m {e}")
        return []

    results = []
    for item in items[:limit]:
        user = item.get("user", item)
        uid = user.get("user_id", 0)
        name = user.get("display_name", "")
        rep = user.get("reputation", 0)
        answer_count = item.get("post_count", user.get("answer_count", 0))
        location = user.get("location", "") or ""
        link = user.get("link", f"https://stackoverflow.com/users/{uid}")

        p = Person(
            username=str(uid),
            platform="so",
            name=name,
            location=location,
            url=link,
            so_reputation=rep,
            so_answers=answer_count,
            so_tags=[tag],
            score=rep + answer_count * 5,
            platforms_found=["so"],
        )
        results.append(p)

    results.sort(key=lambda x: x.score, reverse=True)
    print(f"\u2713 \033[33mSO\033[0m Found {len(results)} people")
    return results


def _parse_users(items: list, limit: int) -> list[Person]:
    results = []
    for user in items[:limit]:
        uid = user.get("user_id", 0)
        p = Person(
            username=str(uid),
            platform="so",
            name=user.get("display_name", ""),
            location=user.get("location", "") or "",
            url=user.get("link", f"https://stackoverflow.com/users/{uid}"),
            so_reputation=user.get("reputation", 0),
            so_answers=user.get("answer_count", 0),
            score=user.get("reputation", 0),
            platforms_found=["so"],
        )
        results.append(p)
    print(f"\u2713 \033[33mSO\033[0m Found {len(results)} people")
    return results
