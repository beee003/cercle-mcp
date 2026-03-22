"""Render search results in compact format."""

from __future__ import annotations
from .models import Person


def render_compact(
    query: str, location: str, results: list[Person], platform_counts: dict
) -> str:
    """Render results like last30days compact output."""
    lines = []
    lines.append(
        f"## Cercle People Search: {query}" + (f" in {location}" if location else "")
    )
    lines.append("")

    active = {k: v for k, v in platform_counts.items() if v > 0}
    total = sum(active.values())
    platforms_str = " + ".join(f"{k.upper()}: {v}" for k, v in active.items())
    lines.append(
        f"**Found {total} people across {len(active)} platforms** ({platforms_str})"
    )
    lines.append("")

    for i, p in enumerate(results, 1):
        # Header line
        badges = []
        if p.github_stars:
            badges.append(f"GitHub: {p.github_stars}\u2605, {p.followers} followers")
        if p.hn_karma:
            badges.append(f"HN: {p.hn_karma} karma")
        if p.x_followers:
            badges.append(f"X: {p.x_followers:,} followers")
        if p.so_reputation:
            badges.append(f"SO: {p.so_reputation:,} rep")

        badge_str = f" [{' | '.join(badges)}]" if badges else ""
        lines.append(
            f"**P{i}** (score:{p.score:.0f}) @{p.username} \u2014 {p.name or p.username}{badge_str}"
        )

        # Details
        if p.bio:
            lines.append(f"  Bio: {p.bio[:120]}")
        if p.location:
            lines.append(f"  Location: {p.location}")
        if p.company:
            lines.append(f"  Company: {p.company}")

        # GitHub details
        if p.github_top_repos:
            repos = ", ".join(
                f"{r['name']}({r['stars']}\u2605)"
                for r in p.github_top_repos[:3]
                if r["stars"] > 0
            )
            if repos:
                lines.append(f"  Top repos: {repos}")
        if p.github_languages:
            lines.append(f"  Languages: {', '.join(p.github_languages[:5])}")
        if p.github_hireable:
            lines.append("  \u2705 Open to work")

        # HN details
        if p.hn_comment_count:
            lines.append(f"  HN: {p.hn_comment_count} comments on topic")
        if p.hn_about:
            lines.append(f"  About: {p.hn_about[:100]}")
        if p.hn_top_comment:
            lines.append(f'  Recent: "{p.hn_top_comment[:100]}..."')

        # SO details
        if p.so_answers:
            lines.append(
                f"  SO: {p.so_answers} answers, {p.so_reputation:,} reputation"
            )

        # Reddit details
        if p.platform == "reddit" and p.github_languages:
            lines.append(f"  Skills: {', '.join(p.github_languages[:8])}")

        # Contact
        contact = []
        if p.email:
            contact.append(f"Email: {p.email}")
        if p.x_handle:
            contact.append(f"X: @{p.x_handle}")
        if contact:
            lines.append(f"  Contact: {' | '.join(contact)}")

        # Links
        urls = [p.url]
        lines.append(f"  {p.url}")

        # Cross-platform
        if p.cross_platform_count > 1:
            lines.append(f"  *Cross-platform: {' + '.join(set(p.platforms_found))}*")

        lines.append("")

    return "\n".join(lines)


def render_json(results: list[Person]) -> str:
    """Render as JSON."""
    import json

    return json.dumps([p.to_dict() for p in results], indent=2, default=str)
