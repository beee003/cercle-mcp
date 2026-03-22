"""Person data model."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Person:
    username: str
    platform: str
    name: str = ""
    bio: str = ""
    location: str = ""
    company: str = ""
    url: str = ""
    email: str = ""
    score: float = 0.0

    # Platform-specific
    followers: int = 0
    github_stars: int = 0
    github_repos: int = 0
    github_top_repos: list = field(default_factory=list)
    github_hireable: bool = False
    github_languages: list = field(default_factory=list)

    hn_karma: int = 0
    hn_comment_count: int = 0
    hn_about: str = ""
    hn_top_comment: str = ""

    x_handle: str = ""
    x_followers: int = 0
    x_bio: str = ""

    so_reputation: int = 0
    so_answers: int = 0
    so_tags: list = field(default_factory=list)

    # Cross-platform
    platforms_found: list = field(default_factory=list)
    cross_platform_count: int = 1
    merged_from: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v}
