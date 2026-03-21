#!/usr/bin/env python3
"""
Cercle — People Search Engine
"Perplexity for People"

Searches GitHub, HN, X, and Reddit to find the right person for any need.
"""

import json
import sys
import concurrent.futures
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))

from search_github import search_github
from search_hn import search_hn
from search_x import search_x

from dotenv import load_dotenv

load_dotenv()


def parse_query(raw: str) -> dict:
    """Parse a natural language query into structured search params."""
    # Extract location if present
    location = ""
    query = raw

    location_markers = [" in ", " from ", " based in ", " located in "]
    for marker in location_markers:
        if marker in raw.lower():
            parts = raw.lower().split(marker, 1)
            query = parts[0].strip()
            location = parts[1].strip().rstrip(".")
            break

    return {"query": query, "location": location, "raw": raw}


def search_all(query: str, location: str = "", limit: int = 5) -> dict:
    """Search all platforms in parallel."""

    print(f"\n{'=' * 60}")
    print("  CERCLE — People Search")
    print(f"  Query: {query}")
    if location:
        print(f"  Location: {location}")
    print(f"{'=' * 60}\n")

    results = {"github": [], "hn": [], "x": []}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(search_github, query, location, limit): "github",
            executor.submit(search_hn, query, limit): "hn",
            executor.submit(search_x, query, limit): "x",
        }

        for future in concurrent.futures.as_completed(futures):
            platform = futures[future]
            try:
                results[platform] = future.result()
            except Exception as e:
                print(f"[{platform}] Error: {e}")
                results[platform] = []

    # Cross-reference: find people who appear on multiple platforms
    cross_ref = {}
    for platform, people in results.items():
        for p in people:
            # Try to match by username or name
            key = p.get("username", "").lower()
            if key not in cross_ref:
                cross_ref[key] = {"platforms": [], "data": {}}
            cross_ref[key]["platforms"].append(platform)
            cross_ref[key]["data"][platform] = p

    # Score and rank
    ranked = []
    seen = set()

    for platform, people in results.items():
        for p in people:
            username = p.get("username", "").lower()
            if username in seen:
                continue
            seen.add(username)

            # Boost score for multi-platform presence
            ref = cross_ref.get(username, {})
            platform_count = len(ref.get("platforms", [1]))
            p["cross_platform"] = platform_count
            p["score"] = p.get("score", 0) * (1 + (platform_count - 1) * 0.5)
            ranked.append(p)

    ranked.sort(key=lambda x: x["score"], reverse=True)

    return {
        "query": query,
        "location": location,
        "results": ranked[: limit * 2],
        "by_platform": {k: len(v) for k, v in results.items()},
        "total": sum(len(v) for v in results.values()),
    }


def format_results(data: dict) -> str:
    """Format results for display."""
    lines = []
    lines.append(
        f"\nFound {data['total']} people across {sum(1 for v in data['by_platform'].values() if v > 0)} platforms"
    )
    lines.append(
        f"GitHub: {data['by_platform'].get('github', 0)} | HN: {data['by_platform'].get('hn', 0)} | X: {data['by_platform'].get('x', 0)}"
    )
    lines.append("")

    for i, p in enumerate(data["results"][:10], 1):
        platform = p["platform"].upper()
        username = p.get("username", "?")
        name = p.get("name", username)
        score = p.get("score", 0)
        location = p.get("location", "")
        bio = p.get("bio", "")[:100]
        url = p.get("url", "")

        lines.append(f"{i}. [{platform}] @{username} — {name}")
        if location:
            lines.append(f"   Location: {location}")
        if bio:
            lines.append(f"   Bio: {bio}")

        # Platform-specific details
        if p["platform"] == "github":
            followers = p.get("followers", 0)
            stars = p.get("total_stars", 0)
            repos = p.get("top_repos", [])
            lines.append(
                f"   {followers} followers | {stars}★ total | {p.get('public_repos', 0)} repos"
            )
            if repos:
                repo_str = ", ".join(f"{r['name']}({r['stars']}★)" for r in repos[:3])
                lines.append(f"   Top repos: {repo_str}")
            if p.get("hireable"):
                lines.append("   ✅ Open to work")
            if p.get("email"):
                lines.append(f"   Email: {p['email']}")
            if p.get("twitter"):
                lines.append(f"   X: @{p['twitter']}")

        elif p["platform"] == "hn":
            karma = p.get("karma", 0)
            comments = p.get("comment_count", 0)
            lines.append(f"   {karma} karma | {comments} comments on topic")
            if p.get("about"):
                lines.append(f"   About: {p['about'][:100]}")
            if p.get("top_comment"):
                lines.append(f'   Recent: "{p["top_comment"][:100]}..."')

        elif p["platform"] == "x":
            if p.get("followers"):
                lines.append(f"   {p['followers']} followers")

        lines.append(f"   {url}")
        lines.append(f"   Score: {score:.0f}")
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 cercle.py 'React developer in Vienna'")
        sys.exit(1)

    raw_query = " ".join(sys.argv[1:])
    parsed = parse_query(raw_query)
    data = search_all(parsed["query"], parsed["location"])
    print(format_results(data))

    # Save results
    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "last_search.json"
    out_file.write_text(json.dumps(data, indent=2, default=str))
    print(f"Results saved to {out_file}")


if __name__ == "__main__":
    main()
