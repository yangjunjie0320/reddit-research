#!/usr/bin/env python3
"""
url_utils.py

Reddit URL normalization and field extraction utilities.

Provides:
    extract_post_id(url)      - base36 post ID
    extract_subreddit(url)    - subreddit name without r/ prefix
    extract_comment_id(url)   - comment ID if present
    normalize_reddit_url(url) - canonical https://www.reddit.com form
    parse_reddit_url(url)     - all components as a dict
"""

import re

# Matches Reddit post URLs (www / old / new / bare).
# Groups: (1) subreddit  (2) post_id  (3) slug  (4) comment_id
REDDIT_URL_RE = re.compile(
    r"https?://(?:www\.|old\.|new\.)?reddit\.com"
    r"/r/(\w+)/comments/([A-Za-z0-9_]+)"
    r"(?:/([^/?\s]*))?"
    r"(?:/([A-Za-z0-9_]+))?"
)


def extract_post_id(url: str) -> str | None:
    """Return the base36 post ID from a Reddit URL, or None."""
    m = REDDIT_URL_RE.search(url)
    return m.group(2) if m else None


def extract_subreddit(url: str) -> str | None:
    """Return the subreddit name (without r/ prefix), or None."""
    m = REDDIT_URL_RE.search(url)
    return m.group(1) if m else None


def extract_comment_id(url: str) -> str | None:
    """Return the comment ID from a Reddit comment URL, or None."""
    m = REDDIT_URL_RE.search(url)
    if m and m.group(4):
        return m.group(4)
    return None


def normalize_reddit_url(url: str) -> str:
    """Normalize a Reddit URL to https://www.reddit.com canonical form.

    Returns the original URL unchanged if it is not a recognized Reddit URL.
    """
    m = REDDIT_URL_RE.search(url)
    if not m:
        return url
    subreddit = m.group(1)
    post_id = m.group(2)
    base = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"
    comment_id = m.group(4)
    if comment_id:
        slug = m.group(3) or "_"
        base += f"{slug}/{comment_id}/"
    return base


def parse_reddit_url(url: str) -> dict | None:
    """Parse a Reddit URL into its components.

    Returns a dict with keys: subreddit, post_id, comment_id, canonical_url.
    Returns None if the URL is not a recognized Reddit post URL.
    """
    m = REDDIT_URL_RE.search(url)
    if not m:
        return None
    return {
        "subreddit": m.group(1),
        "post_id": m.group(2),
        "comment_id": m.group(4),
        "canonical_url": normalize_reddit_url(url),
    }
