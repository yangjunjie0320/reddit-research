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
        subreddit: str | None = None,
        num_results: int = 10,
        time_filter: str = "all",
    ) -> list[dict]:
        """Return Reddit post result dicts with url, title, snippet, rank, source."""
        site = f"site:reddit.com/r/{subreddit}" if subreddit else "site:reddit.com"
        q = f"{site} {query}"

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

    with open(profile_path, encoding="utf-8") as f:
        profile = yaml.safe_load(f)

    subreddits: list[str] = profile["recommended_subreddits"]
    queries: list[str] = profile["keyword_groups"]
    fetch_cfg: dict = profile.get("fetch", {})
    limit = args.limit or fetch_cfg.get("posts_per_keyword", 25)
    time_filter: str = fetch_cfg.get("time_filter", "year")

    client = build_search_client()
    all_discovered: list[dict] = []
    seen_ids: set[str] = set()

    request_count = 0
    for sub in subreddits:
        for query in queries:
            # Delay between requests to respect API rate limits
            if request_count > 0:
                time.sleep(1.5)
            request_count += 1
            log.info("  [%d] searching r/%s: %r", request_count, sub, query)
            try:
                results = client.search(
                    query,
                    subreddit=sub,
                    num_results=limit,
                    time_filter=time_filter,
                )
            except Exception as e:
                log.warning("    search error (skipping): %s", e)
                continue

            added = 0
            for r in results:
                pid = extract_post_id(r["url"])
                if not pid or pid in seen_ids:
                    continue
                seen_ids.add(pid)
                all_discovered.append(
                    {
                        "url": r["url"],
                        "post_id": pid,
                        "subreddit": extract_subreddit(r["url"]) or sub,
                        "title": r["title"],
                        "snippet": r["snippet"],
                        "source": r.get("source", "unknown"),
                        "query": query,
                        "rank": r["rank"],
                    }
                )
                added += 1
            log.info("    +%d new URLs", added)

    if not all_discovered:
        log.error("No valid Reddit post URLs discovered.")
        sys.exit(1)

    log.info("\nTotal: %d unique posts discovered.", len(all_discovered))

    if run_dir:
        out_path = run_dir / "discovered_posts.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            for rec in all_discovered:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        log.info("Written to %s", out_path)
    else:
        for rec in all_discovered:
            print(json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
