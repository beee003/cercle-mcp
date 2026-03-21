---
description: Find people by skills, expertise, and location. Searches GitHub, HN, X, and Reddit. Use when the user wants to find a person — developer, designer, expert, freelancer, co-founder, investor, etc.
---

# Cercle — People Search Engine

When the user asks to find a person (developer, designer, expert, etc.), run the Cercle search engine.

## Usage

Run the search script:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cercle.py" "$ARGUMENTS"
```

## Examples

- `/cercle React developer in Vienna`
- `/cercle AI researcher in San Francisco`
- `/cercle plumber in Berlin`
- `/cercle YC founder working on climate tech`
- `/cercle freelance designer in London`

## After Results

Present the results to the user in a clean format:
1. Show the top 5-10 matches ranked by relevance
2. Highlight cross-platform matches (people found on multiple platforms)
3. Note who is "open to work" or "hireable"
4. Include contact info when available (email, X handle)
5. Ask if they want you to draft an outreach message

## Environment Variables

- `GITHUB_TOKEN` — Optional, increases GitHub API rate limit
- `XAI_API_KEY` — Optional, enables X/Twitter search via Grok
