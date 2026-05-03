#!/usr/bin/env python3
"""
arctic_shift_client.py

Client for the Arctic Shift Reddit archive API.
https://arctic-shift.photon-reddit.com/

Fetches posts and comments by post ID. Enforces a global 1 QPS rate limit
as required by the service. All callers share the same rate limiter, so
fetch_reddit.py does not need additional throttling.

Note: Arctic Shift score and num_comments values are accurate approximately
36 hours after a post is archived. Very recent posts may show 0 for these
fields; filter_posts.py will drop them on the min_score check, which is
expected behavior.
"""

import logging
import threading
import time

import requests

_log = logging.getLogger(__name__)

BASE_URL = "https://arctic-shift.photon-reddit.com/api"

_rate_lock = threading.Lock()
_last_request_at: float = 0.0
_MIN_INTERVAL = 1.0  # 1 QPS hard limit


def _throttle() -> None:
    global _last_request_at
    with _rate_lock:
        elapsed = time.monotonic() - _last_request_at
        if elapsed < _MIN_INTERVAL:
            time.sleep(_MIN_INTERVAL - elapsed)
        _last_request_at = time.monotonic()


def _get(path: str, params: dict[str, object]) -> dict:
    for attempt in range(3):
        _throttle()
        try:
            resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=20)
        except requests.RequestException as e:
            if attempt == 2:
                raise RuntimeError(
                    f"Arctic Shift request failed after 3 attempts: {e}. "
                    "Check network connectivity."
                ) from e
            time.sleep(2**attempt)
            continue

        if resp.status_code == 404:
            return {"data": []}
        if resp.status_code == 429:
            wait = 5 * (2**attempt)
            _log.warning(
                "429 rate limited; waiting %ss before retry %d/3", wait, attempt + 1
            )
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            if attempt == 2:
                raise RuntimeError(
                    f"Arctic Shift returned {resp.status_code} after 3 attempts. "
                    "The service may be temporarily unavailable; try again later."
                )
            time.sleep(2**attempt)
            continue

        resp.raise_for_status()
        return resp.json()

    raise RuntimeError("Arctic Shift: exhausted retries without a successful response")


def fetch_post(post_id: str) -> dict | None:
    """Fetch a single post by base36 ID.

    Returns None if the post is not in the Arctic Shift archive (deleted,
    too recent, or not covered by the current dump).
    """
    # Strip t3_ prefix if present; the API accepts either form.
    pid = post_id.removeprefix("t3_")
    data = _get("/posts/ids", {"ids": pid})
    items = data.get("data", [])
    return items[0] if items else None


def fetch_comments(post_id: str, limit: int = 15) -> list[dict]:
    """Fetch comments for a post, returning up to limit entries by score.

    Fetches up to limit*3 comments (capped at 100) and returns the top
    limit sorted by score descending, since the Arctic Shift search
    endpoint sorts by date rather than score.
    """
    pid = post_id.removeprefix("t3_")
    batch = min(limit * 3, 100)
    data = _get("/comments/search", {"link_id": pid, "limit": batch})
    comments: list[dict] = data.get("data", [])
    comments.sort(key=lambda c: c.get("score", 0), reverse=True)
    return comments[:limit]
