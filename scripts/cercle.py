#!/usr/bin/env python3
"""
Cercle — People Search Engine
"Perplexity for People"

Usage:
    python3 cercle.py "React developer in Vienna" [options]

Options:
    --quick         Fewer results, faster (5 per platform)
    --deep          More results (15 per platform)
    --emit=MODE     compact|json (default: compact)
    --save-dir=DIR  Save results to directory
    --limit=N       Max final results (default: 10)
"""

import argparse
import json
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Add lib to path
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from dotenv import load_dotenv

load_dotenv()

from lib import github, hackernews, x_search, stackoverflow
from lib.score import deduplicate_and_score
from lib.render import render_compact, render_json

# Timeout profiles
PROFILES = {
    "quick": {"global": 60, "per_platform": 5},
    "default": {"global": 120, "per_platform": 10},
    "deep": {"global": 240, "per_platform": 15},
}

_timed_out = False


def _timeout_handler(signum, frame):
    global _timed_out
    _timed_out = True
    print(
        "\n\033[91m[TIMEOUT]\033[0m Global timeout exceeded. Returning partial results.\n"
    )
    raise TimeoutError("Global timeout")


def parse_query(raw: str) -> dict:
    """Parse natural language into structured search params."""
    location = ""
    query = raw

    for marker in [" in ", " from ", " based in ", " located in ", " near "]:
        if marker in raw.lower():
            idx = raw.lower().index(marker)
            query = raw[:idx].strip()
            location = raw[idx + len(marker) :].strip().rstrip(".")
            break

    return {"query": query, "location": location, "raw": raw}


def main():
    parser = argparse.ArgumentParser(description="Cercle — People Search Engine")
    parser.add_argument("query", nargs="+", help="Search query")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--emit", default="compact", choices=["compact", "json"])
    parser.add_argument("--save-dir", default="")
    parser.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()
    raw_query = " ".join(args.query)

    # Select profile
    if args.quick:
        profile = PROFILES["quick"]
        depth = "quick"
    elif args.deep:
        profile = PROFILES["deep"]
        depth = "deep"
    else:
        profile = PROFILES["default"]
        depth = "default"

    per_platform = profile["per_platform"]

    # Set global timeout
    try:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(profile["global"])
    except (AttributeError, ValueError):
        pass  # Windows or not main thread

    # Parse query
    parsed = parse_query(raw_query)
    query = parsed["query"]
    location = parsed["location"]

    print(f"/cercle \u00b7 searching: {raw_query}")
    print("\u23f3 Searching GitHub, HN, X, Stack Overflow...")

    # Search all platforms in parallel
    all_results = {"github": [], "hn": [], "x": [], "so": [], "reddit": []}

    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(github.search, query, location, per_platform): "github",
                executor.submit(hackernews.search, query, per_platform): "hn",
                executor.submit(x_search.search, query, per_platform): "x",
                executor.submit(stackoverflow.search, query, per_platform): "so",
                executor.submit(
                    __import__("lib.reddit", fromlist=["search"]).search,
                    query,
                    per_platform,
                ): "reddit",
            }

            for future in as_completed(futures, timeout=profile["global"] - 5):
                platform = futures[future]
                try:
                    all_results[platform] = future.result()
                except Exception as e:
                    print(f"\033[91m\u2717 {platform}\033[0m Error: {e}")
    except TimeoutError:
        pass
    except Exception as e:
        print(f"\033[91mSearch error:\033[0m {e}")

    # Cancel timeout
    try:
        signal.alarm(0)
    except (AttributeError, ValueError):
        pass

    # Deduplicate and score
    ranked = deduplicate_and_score(all_results, limit=args.limit)

    platform_counts = {k: len(v) for k, v in all_results.items()}
    total = sum(platform_counts.values())

    # Render output
    if args.emit == "json":
        output = render_json(ranked)
    else:
        output = render_compact(query, location, ranked, platform_counts)

    print(output)

    # Stats line
    print(f"\n\u2705 Search complete ({depth} mode)")
    active = {k: v for k, v in platform_counts.items() if v > 0}
    for k, v in active.items():
        icon = {
            "github": "\U0001f4bb",
            "hn": "\U0001f7e1",
            "x": "\U0001f535",
            "so": "\U0001f7e0",
            "reddit": "\U0001f7e0",
        }.get(k, "\u2022")
        print(f"  {icon} {k.upper()}: {v} people")
    print(f"  \U0001f465 Total: {total} found \u2192 {len(ranked)} ranked results")

    # Save
    if args.save_dir:
        save_dir = Path(args.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        slug = raw_query.lower().replace(" ", "-")[:50]
        save_path = save_dir / f"cercle-{slug}.json"
        save_path.write_text(
            json.dumps(
                {
                    "query": raw_query,
                    "parsed": parsed,
                    "results": [p.to_dict() for p in ranked],
                    "platform_counts": platform_counts,
                    "searched_at": datetime.utcnow().isoformat(),
                    "depth": depth,
                },
                indent=2,
                default=str,
            )
        )
        print(f"  \U0001f4ce {save_path}")


if __name__ == "__main__":
    main()
