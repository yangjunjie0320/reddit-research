#!/usr/bin/env python3
"""
search_client.py

Search discovery layer for reddit-research. Unified interface over
Serper and Brave Search API. Returns Reddit post URLs with metadata.

When both SERPER_API_KEY and BRAVE_API_KEY are configured, both backends
are queried and results merged (deduplicated by post_id).

CLI usage:
    uv run python scripts/search_client.py --profile examples/product_water_bottle.yaml --limit 10
    uv run python scripts/search_client.py --run runs/{run_id}
"""

import argparse
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

import requests
import yaml

from log_utils import get_logger
from url_utils import extract_post_id, extract_subreddit

_log = logging.getLogger(__name__)

# Maps profile time_filter values to backend-specific codes.
_SERPER_TIME = {"year": "qdr:y", "month": "qdr:m", "week": "qdr:w"}
_BRAVE_TIME = {"year": "py", "month": "pm", "week": "pw"}


def _request(method: str, url: str, **kwargs: object) -> requests.Response:
    for attempt in range(3):
        try:
            resp = requests.request(method, url, timeout=15, **kwargs)  # type: ignore[arg-type]
            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                _log.warning(
                    "429 rate limit, waiting %ss (attempt %d/3)", wait, attempt + 1
                )
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            if attempt == 2:
                raise RuntimeError(
                    f"Search API request failed after 3 attempts ({url}): {e}. "
                    "Check network connectivity or see docs/SETUP.md."
                ) from e
            time.sleep(2**attempt)
    raise RuntimeError("Search API failed after 3 rate-limit retries")


# Serper rate limiter -- 1 QPS hard limit, shared across all instances.
_serper_lock = threading.Lock()
_serper_last_request_at: float = 0.0
_SERPER_MIN_INTERVAL = 1.0


def _serper_throttle() -> None:
    global _serper_last_request_at
    with _serper_lock:
        elapsed = time.monotonic() - _serper_last_request_at
        if elapsed < _SERPER_MIN_INTERVAL:
            time.sleep(_SERPER_MIN_INTERVAL - elapsed)
        _serper_last_request_at = time.monotonic()


class SerperClient:
    """Google Search via Serper API."""

    URL = "https://google.serper.dev/search"

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def search(
        self,
        query: str,
        num_results: int = 10,
        time_filter: str = "all",
    ) -> list[dict]:
        results: list[dict] = []
        page = 1
        tbs = _SERPER_TIME.get(time_filter)
        while len(results) < num_results:
            payload: dict[str, object] = {
                "q": query,
                "num": min(10, num_results - len(results)),
                "page": page,
            }
            if tbs:
                payload["tbs"] = tbs
            _serper_throttle()
            resp = _request(
                "POST",
                self.URL,
                json=payload,
                headers={"X-API-KEY": self._key, "Content-Type": "application/json"},
            )
            batch = []
            for item in resp.json().get("organic", []):
                link = item.get("link", "")
                if "reddit.com/r/" in link and "/comments/" in link:
                    batch.append(
                        {
                            "url": link,
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "rank": item.get("position", 0),
                        }
                    )
            if not batch:
                break
            results.extend(batch)
            page += 1
        return results[:num_results]


# Brave API rate limiter -- 1 QPS hard limit, shared across all instances.
_brave_lock = threading.Lock()
_brave_last_request_at: float = 0.0
_BRAVE_MIN_INTERVAL = 1.0


def _brave_throttle() -> None:
    global _brave_last_request_at
    with _brave_lock:
        elapsed = time.monotonic() - _brave_last_request_at
        if elapsed < _BRAVE_MIN_INTERVAL:
            time.sleep(_BRAVE_MIN_INTERVAL - elapsed)
        _brave_last_request_at = time.monotonic()


class BraveClient:
    """Brave Search API."""

    URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def search(
        self,
        query: str,
        num_results: int = 10,
        time_filter: str = "all",
    ) -> list[dict]:
        results: list[dict] = []
        offset = 0
        freshness = _BRAVE_TIME.get(time_filter)
        while len(results) < num_results:
            params: dict[str, object] = {
                "q": query,
                "count": min(20, num_results - len(results)),
                "offset": offset,
            }
            if freshness:
                params["freshness"] = freshness
            _brave_throttle()
            resp = _request(
                "GET",
                self.URL,
                params=params,
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self._key,
                },
            )
            batch = []
            for idx, item in enumerate(resp.json().get("web", {}).get("results", [])):
                url = item.get("url", "")
                if "reddit.com/r/" in url and "/comments/" in url:
                    batch.append(
                        {
                            "url": url,
                            "title": item.get("title", ""),
                            "snippet": item.get("description", ""),
                            "rank": offset + idx + 1,
                        }
                    )
            if not batch:
                break
            results.extend(batch)
            offset += 20
        return results[:num_results]


class SearchClient:
    """Unified search client. Merges results when both backends configured."""

    def __init__(
        self,
        serper_key: str | None = None,
        brave_key: str | None = None,
    ) -> None:
        self._serper = SerperClient(serper_key) if serper_key else None
        self._brave = BraveClient(brave_key) if brave_key else None
        if not self._serper and not self._brave:
            raise RuntimeError(
                "No search API key configured. At least one of SERPER_API_KEY "
                "or BRAVE_API_KEY must be set in ./.secrets/reddit-research.env. "
                "Run: uv run python scripts/save_credentials.py"
            )

    def search(
        self,
        query: str,
        num_results: int = 10,
        time_filter: str = "all",
    ) -> list[dict]:
        """Return Reddit post result dicts with url, title, snippet, rank, source."""
        q = f"site:reddit.com {query}"

        all_results: list[dict] = []

        if self._serper:
            try:
                for r in self._serper.search(q, num_results, time_filter):
                    r["source"] = "serper"
                    all_results.append(r)
            except RuntimeError as e:
                if not self._brave:
                    raise
                _log.warning("Serper error, using Brave only: %s", e)

        if self._brave:
            try:
                for r in self._brave.search(q, num_results, time_filter):
                    r["source"] = "brave"
                    all_results.append(r)
            except Exception as e:
                if not all_results:
                    raise
                _log.warning("Brave error (Serper results available): %s", e)

        # Deduplicate by post_id, first occurrence wins.
        seen: set[str] = set()
        deduped: list[dict] = []
        for r in all_results:
            pid = extract_post_id(r["url"])
            if pid and pid not in seen:
                seen.add(pid)
                deduped.append(r)

        return deduped[:num_results]


def build_search_client() -> SearchClient:
    """Construct a SearchClient from environment variables."""
    return SearchClient(
        serper_key=os.environ.get("SERPER_API_KEY"),
        brave_key=os.environ.get("BRAVE_API_KEY"),
    )


def _validate_profile(profile: dict, log: logging.Logger) -> None:
    """Validate required profile fields, exit with friendly message on error."""
    required = ["keyword_groups"]
    missing = [k for k in required if k not in profile]
    if missing:
        log.error(
            "profile.yaml is missing required fields: %s. "
            "See templates/profile_template.yaml for the expected schema.",
            ", ".join(missing),
        )
        sys.exit(1)
    if not isinstance(profile["keyword_groups"], list) or not profile["keyword_groups"]:
        log.error(
            "profile.yaml keyword_groups must be a non-empty list. "
            "See templates/profile_template.yaml for the expected schema."
        )
        sys.exit(1)


def main() -> None:
    from save_credentials import load_env

    load_env()

    parser = argparse.ArgumentParser(
        description="Search for Reddit posts via Serper / Brave."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", help="Run directory path")
    group.add_argument("--profile", help="Profile YAML (verification mode)")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    run_dir = Path(args.run) if args.run else None
    log = get_logger(__name__, run_dir)

    profile_path = run_dir / "profile.yaml" if run_dir else Path(args.profile)
    if not profile_path.exists():
        log.error("Profile not found: %s", profile_path)
        sys.exit(1)

    # Check output directory is writable.
    out_dir = run_dir or Path(".")
    if not os.access(out_dir, os.W_OK):
        log.error(
            "Output directory is not writable: %s. "
            "Check permissions or choose a different --run path.",
            out_dir,
        )
        sys.exit(1)

    with open(profile_path, encoding="utf-8") as f:
        profile = yaml.safe_load(f)

    _validate_profile(profile, log)

    queries: list[str] = profile["keyword_groups"]
    fetch_cfg: dict = profile.get("fetch", {})
    max_keywords: int = fetch_cfg.get("max_keywords", 15)
    if len(queries) > max_keywords:
        log.warning(
            "keyword_groups has %d entries, truncating to max_keywords=%d",
            len(queries),
            max_keywords,
        )
        queries = queries[:max_keywords]
    limit = args.limit or fetch_cfg.get("posts_per_keyword", 25)
    time_filter: str = fetch_cfg.get("time_filter", "year")
    discovery_cfg: dict = profile.get("discovery", {})
    max_results: int = discovery_cfg.get("max_results", 200)

    log.info(
        "Starting search: %d keywords, limit=%d per keyword, "
        "time_filter=%s, max_results=%d",
        len(queries),
        limit,
        time_filter,
        max_results,
    )

    client = build_search_client()
    all_discovered: list[dict] = []
    seen_ids: set[str] = set()

    # Per-source statistics for discovery summary.
    stats: dict[str, dict[str, int]] = {}
    total_raw = 0
    total_valid_before_dedupe = 0

    request_count = 0
    for query in queries:
        # Delay between requests to respect API rate limits
        if request_count > 0:
            time.sleep(1.5)
        request_count += 1
        log.info("  [%d] searching: %r", request_count, query)
        try:
            results = client.search(
                query,
                num_results=limit,
                time_filter=time_filter,
            )
        except Exception as e:
            log.warning("    search error (skipping): %s", e)
            continue

        added = 0
        for r in results:
            source = r.get("source", "unknown")
            if source not in stats:
                stats[source] = {"raw": 0, "valid": 0}
            stats[source]["raw"] += 1
            total_raw += 1

            pid = extract_post_id(r["url"])
            if not pid:
                continue
            stats[source]["valid"] += 1
            total_valid_before_dedupe += 1

            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            all_discovered.append(
                {
                    "url": r["url"],
                    "post_id": pid,
                    "subreddit": extract_subreddit(r["url"]) or "",
                    "title": r["title"],
                    "snippet": r["snippet"],
                    "source": source,
                    "query": query,
                    "rank": r["rank"],
                }
            )
            added += 1
        log.info("    +%d new URLs", added)

    if not all_discovered:
        log.error(
            "No valid Reddit post URLs discovered. "
            "Try broadening keyword_groups or adjusting time_filter in profile.yaml."
        )
        sys.exit(1)

    # Sort by rank (lower = more relevant) and apply max_results cap.
    all_discovered.sort(key=lambda r: r["rank"])
    retained = all_discovered[:max_results]

    # --- Discovery summary ---
    log.info("")
    log.info("Search discovery summary:")
    for src, counts in sorted(stats.items()):
        log.info("  %s raw URLs: %d", src.capitalize(), counts["raw"])
        log.info("  %s valid Reddit post URLs: %d", src.capitalize(), counts["valid"])
    log.info("  Total raw URLs: %d", total_raw)
    log.info("  Total valid Reddit post URLs before dedupe: %d", total_valid_before_dedupe)
    log.info("  Unique valid Reddit post URLs after dedupe: %d", len(all_discovered))
    log.info("  Final retained URLs: %d / %d", len(retained), max_results)

    if run_dir:
        out_path = run_dir / "discovered_posts.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            for rec in retained:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        log.info("Written to %s", out_path)
    else:
        for rec in retained:
            print(json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
