"""Reddit people search — find people from r/forhire, r/cscareerquestions, r/freelance, etc."""

from __future__ import annotations
import re
from .models import Person
from .http import get_client

# Subreddits where people post about themselves / offer services
HIRE_SUBS = [
    "forhire",
    "remotejs",
    "jobbit",
    "freelance",
    "cscareerquestions",
    "webdev",
    "learnprogramming",
    "startups",
    "cofounder",
    "hwstartups",
    "digitalnomad",
]


def search(query: str, limit: int = 10) -> list[Person]:
    """Search Reddit for people offering skills or looking for work."""
    print("\u23f3 \033[91mReddit\033[0m Searching for people...")

    client = get_client()
    results = []

    # Search across hiring subreddits
    for sub in ["forhire", "cofounder", "freelance"]:
        try:
            resp = client.get(
                f"https://www.reddit.com/r/{sub}/search.json",
                params={
                    "q": query,
                    "restrict_sr": "on",
                    "sort": "new",
                    "limit": 25,
                    "t": "month",
                },
                headers={"User-Agent": "Cercle/0.1"},
                timeout=10,
            )
            if resp.status_code != 200:
                continue

            posts = resp.json().get("data", {}).get("children", [])

            for post in posts:
                data = post.get("data", {})
                title = data.get("title", "")
                author = data.get("author", "")
                body = (data.get("selftext", "") or "")[:500]
                score = data.get("score", 0)
                url = f"https://reddit.com{data.get('permalink', '')}"
                flair = (data.get("link_flair_text", "") or "").lower()

                if not author or author in ("[deleted]", "AutoModerator"):
                    continue

                # Determine if this is someone offering services (not hiring)
                is_offering = any(
                    x in (title + flair).lower()
                    for x in [
                        "for hire",
                        "seeking work",
                        "available",
                        "looking for work",
                        "freelance",
                        "offering",
                        "open to",
                        "[for hire]",
                    ]
                )

                if not is_offering:
                    # Check if it's a co-founder post
                    is_cofounder = any(
                        x in (title + flair).lower()
                        for x in [
                            "co-founder",
                            "cofounder",
                            "looking for",
                            "seeking",
                        ]
                    )
                    if not is_cofounder and sub != "freelance":
                        continue

                # Extract location from body
                location = ""
                loc_match = re.search(
                    r"(?:location|based in|located in|from)[:\s]+([^\n,]+)",
                    body,
                    re.IGNORECASE,
                )
                if loc_match:
                    location = loc_match.group(1).strip()[:50]

                # Extract skills/tech from body
                tech_patterns = r"\b(Python|JavaScript|React|Node|TypeScript|Go|Rust|Java|C\+\+|Ruby|PHP|Swift|Kotlin|AWS|Docker|Kubernetes|PostgreSQL|MongoDB|Django|Flask|Next\.js|Vue|Angular|GraphQL|Redis|TensorFlow|PyTorch)\b"
                skills = list(set(re.findall(tech_patterns, body, re.IGNORECASE)))

                # Extract contact info
                email = ""
                email_match = re.search(
                    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", body
                )
                if email_match:
                    email = email_match.group()

                # Build bio from title + first part of body
                bio = title[:150]
                if body and len(body) > 20:
                    bio = f"{title} — {body[:100]}"

                p = Person(
                    username=author,
                    platform="reddit",
                    name=author,
                    bio=bio[:200],
                    location=location,
                    url=url,
                    email=email,
                    github_languages=skills[:5],
                    score=score + 20 + (10 if is_offering else 0) + len(skills) * 3,
                    platforms_found=["reddit"],
                )
                results.append(p)

        except Exception as e:
            print(f"\033[91m\u2717 Reddit r/{sub}\033[0m {e}")
            continue

    # Also search general Reddit for "[topic] developer" type posts
    try:
        resp = client.get(
            "https://www.reddit.com/search.json",
            params={
                "q": f"{query} (hiring OR hire OR freelance OR available)",
                "sort": "new",
                "limit": 15,
                "t": "month",
            },
            headers={"User-Agent": "Cercle/0.1"},
            timeout=10,
        )
        if resp.status_code == 200:
            posts = resp.json().get("data", {}).get("children", [])
            for post in posts:
                data = post.get("data", {})
                author = data.get("author", "")
                if author in ("[deleted]", "AutoModerator"):
                    continue
                title = data.get("title", "")
                body = (data.get("selftext", "") or "")[:300]

                if any(
                    x in (title).lower()
                    for x in ["for hire", "seeking work", "available for"]
                ):
                    p = Person(
                        username=author,
                        platform="reddit",
                        name=author,
                        bio=title[:200],
                        url=f"https://reddit.com{data.get('permalink', '')}",
                        score=data.get("score", 0) + 15,
                        platforms_found=["reddit"],
                    )
                    results.append(p)
    except Exception:
        pass

    # Deduplicate by username
    seen = set()
    unique = []
    for p in results:
        if p.username not in seen:
            seen.add(p.username)
            unique.append(p)

    unique.sort(key=lambda x: x.score, reverse=True)
    unique = unique[:limit]

    print(f"\u2713 \033[91mReddit\033[0m Found {len(unique)} people")
    return unique
