# Cercle — People Search Engine

Perplexity for People. Find anyone by skills, expertise, and location.

## Install as Claude Code Plugin

```
/plugin install cercle@cercle-marketplace
```

Then use:
```
/cercle React developer in Vienna
/cercle AI researcher in San Francisco
/cercle freelance designer with Figma expertise
```

## What it searches

| Platform | What it finds |
|----------|--------------|
| GitHub | Repos, stars, followers, languages, hireable status, email |
| Hacker News | Karma, expertise from comments, about section |
| X/Twitter | Handles, bios, follower count |

## How scoring works

- GitHub: followers + stars * 2
- HN: karma + comments on topic * 10
- X: followers + engagement
- Cross-platform bonus: people found on multiple platforms score higher
