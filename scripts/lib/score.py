"""Cross-platform scoring and deduplication."""

from __future__ import annotations
from .models import Person


def deduplicate_and_score(
    all_results: dict[str, list[Person]], limit: int = 10
) -> list[Person]:
    """Merge people found on multiple platforms and boost their score."""

    # Index by normalized username
    index: dict[str, Person] = {}

    for platform, people in all_results.items():
        for p in people:
            # Try to match across platforms
            keys = _match_keys(p)

            merged = False
            for key in keys:
                if key in index:
                    # Merge into existing
                    existing = index[key]
                    existing.platforms_found.append(platform)
                    existing.cross_platform_count = len(set(existing.platforms_found))
                    _merge_fields(existing, p)
                    merged = True
                    break

            if not merged:
                for key in keys:
                    index[key] = p

    # Apply cross-platform bonus
    results = list({id(p): p for p in index.values()}.values())
    for p in results:
        multiplier = 1.0 + (p.cross_platform_count - 1) * 0.5
        p.score *= multiplier

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:limit]


def _match_keys(p: Person) -> list[str]:
    """Generate keys for cross-platform matching."""
    keys = []
    username = p.username.lower().strip()
    if username and username != "?" and len(username) > 2:
        keys.append(f"u:{username}")
    if p.x_handle:
        keys.append(f"u:{p.x_handle.lower()}")
    if p.email:
        keys.append(f"e:{p.email.lower()}")
    if p.name and len(p.name) > 4:
        keys.append(f"n:{p.name.lower().strip()}")
    return keys


def _merge_fields(existing: Person, new: Person):
    """Merge non-empty fields from new into existing."""
    if not existing.name and new.name:
        existing.name = new.name
    if not existing.bio and new.bio:
        existing.bio = new.bio
    if not existing.location and new.location:
        existing.location = new.location
    if not existing.email and new.email:
        existing.email = new.email
    if not existing.url and new.url:
        existing.url = new.url
    if not existing.x_handle and new.x_handle:
        existing.x_handle = new.x_handle

    # Platform-specific
    if new.platform == "github":
        existing.github_stars = new.github_stars
        existing.github_repos = new.github_repos
        existing.github_top_repos = new.github_top_repos
        existing.github_hireable = new.github_hireable
        existing.github_languages = new.github_languages
    elif new.platform == "hn":
        existing.hn_karma = new.hn_karma
        existing.hn_comment_count = new.hn_comment_count
        existing.hn_about = new.hn_about
        existing.hn_top_comment = new.hn_top_comment
    elif new.platform == "x":
        existing.x_followers = new.x_followers
        existing.x_bio = new.x_bio
    elif new.platform == "so":
        existing.so_reputation = new.so_reputation
        existing.so_answers = new.so_answers
        existing.so_tags = new.so_tags

    # Add new score
    existing.score += new.score
