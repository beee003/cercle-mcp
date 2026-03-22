---
description: "Find people by skills, expertise, and location. Searches GitHub, HN, X, and Stack Overflow in parallel. Use when the user wants to find a developer, designer, expert, freelancer, co-founder, investor, plumber, or any person."
---

# Cercle — People Search Engine

"Perplexity for People" — find anyone by skills, expertise, and location.

## When to use

Triggered when user asks to find a person:
- "find me a React developer in Vienna"
- "who are the best AI researchers in SF?"
- "I need a plumber in Berlin"
- "find a YC founder working on climate"
- "freelance designer with Figma skills"

## How to run

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cercle.py" "$ARGUMENTS" --emit=compact
```

Add `--quick` for fast results, `--deep` for comprehensive search.

Timeout: 120 seconds.

## After results

1. Present top 5-10 matches ranked by relevance score
2. Highlight people found on multiple platforms (strongest signal)
3. Note who is "open to work" or "hireable"
4. Show contact info when available (email, X handle, website)
5. Ask: "Want me to draft an outreach message to any of them?"

## Environment Variables

- `GITHUB_TOKEN` — Optional, increases GitHub rate limit from 10 to 30 req/min
- `XAI_API_KEY` — Optional, enables X/Twitter people search
