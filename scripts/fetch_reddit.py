#!/usr/bin/env python3
"""
fetch_reddit.py

Multi-source data hydration layer. Reads discovered_posts.jsonl from a
run directory, fetches full post data and comments via Arctic Shift,
and writes hydrated_posts.jsonl.

Resume-safe: rerunning skips post IDs already in the output file.

Usage:
    uv run python scripts/fetch_reddit.py --run runs/{run_id}
    uv run python scripts/fetch_reddit.py --run runs/{run_id} --dry-run
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from arctic_shift_client import fetch_comments, fetch_post
from log_utils import get_logger, load_jsonl, update_run_meta


def _existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if "id" in rec:
                    ids.add(rec["id"])
            except json.JSONDecodeError:
                continue
    return ids


def _normalize_post(post: dict, query: str) -> dict:
    post_id = post.get("id", "").removeprefix("t3_")
    subreddit = post.get("subreddit", "")
    selftext = post.get("selftext") or ""
    if selftext.strip().lower() in ("[removed]", "[deleted]"):
        selftext = ""

    permalink = post.get("permalink", "")
    if permalink:
        url = f"https://www.reddit.com{permalink}"
    else:
        url = (
            post.get("url")
            or f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"
        )

    return {
        "id": post_id,
        "subreddit": subreddit,
        "title": post.get("title", ""),
        "selftext": selftext,
        "url": url,
        "score": post.get("score", 0),
        "upvote_ratio": post.get("upvote_ratio"),
        "num_comments": post.get("num_comments", 0),
        "created_utc": post.get("created_utc", 0),
        "stickied": bool(post.get("stickied", False)),
        "locked": bool(post.get("locked", False)),
        "over_18": bool(post.get("over_18", False)),
        "is_self": bool(post.get("is_self", bool(selftext))),
        "link_flair_text": post.get("link_flair_text"),
        "fetched_via_query": query,
    }


def _normalize_comments(comments: list[dict], post_author: str) -> list[dict]:
    result = []
    for c in comments:
        body = c.get("body", "")
        if not body or body.strip().lower() in ("[deleted]", "[removed]"):
            continue
        result.append(
            {
                "id": c.get("id", ""),
                "body": body,
                "score": c.get("score", 0),
                "created_utc": c.get("created_utc", 0),
                "is_submitter": c.get("author", "") == post_author,
            }
        )
    return result


def main() -> None:
    from save_credentials import load_env

    load_env()

    parser = argparse.ArgumentParser(
        description="Hydrate Reddit posts via Arctic Shift archive."
    )
    parser.add_argument("--run", required=True, help="Run directory path")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan without making any API calls",
    )
    args = parser.parse_args()

    run_dir = Path(args.run)
    profile_path = run_dir / "profile.yaml"
    discovered_path = run_dir / "discovered_posts.jsonl"
    output_path = run_dir / "hydrated_posts.jsonl"

    log = get_logger(__name__, run_dir)
    get_logger("arctic_shift_client", run_dir)

    if not profile_path.exists():
        log.error("Profile not found: %s", profile_path)
        sys.exit(1)
    if not discovered_path.exists():
        log.error("%s not found. Run search_client.py --run first.", discovered_path)
        sys.exit(1)
    if not os.access(run_dir, os.W_OK):
        log.error(
            "Run directory is not writable: %s. Check permissions.",
            run_dir,
        )
        sys.exit(1)

    with open(profile_path, encoding="utf-8") as f:
        profile = yaml.safe_load(f)

    fetch_cfg = profile.get("fetch", {})
    comments_per_post: int = fetch_cfg.get("comments_per_post", 15)

    # Deduplicate discovered posts by post_id.
    discovered = load_jsonl(discovered_path)
    seen_plan: set[str] = set()
    unique: list[dict] = []
    for rec in discovered:
        pid = rec.get("post_id", "")
        if pid and pid not in seen_plan:
            seen_plan.add(pid)
            unique.append(rec)

    log.info("Discovered: %d records, %d unique posts", len(discovered), len(unique))
    log.info("  comments_per_post=%d", comments_per_post)

    if args.dry_run:
        log.info("[DRY RUN] No API calls made.")
        return

    existing = _existing_ids(output_path)
    to_fetch = [p for p in unique if p["post_id"] not in existing]
    log.info("Already hydrated: %d. To fetch: %d.", len(existing), len(to_fetch))

    fetch_cfg = profile.get("fetch", {})
    meta_base = {
        "keyword": profile.get("keyword", ""),
        "slug": profile.get("slug", ""),
        "fetch_backends": ["arctic_shift"],
        "posts_per_keyword": fetch_cfg.get("posts_per_keyword", 25),
        "comments_per_post": fetch_cfg.get("comments_per_post", 15),
        "time_filter": fetch_cfg.get("time_filter", "year"),
    }
    # Preserve created_at if already set.
    meta_path = run_dir / "run_meta.json"
    if not meta_path.exists():
        meta_base["created_at"] = datetime.now(timezone.utc).isoformat()

    if not to_fetch:
        log.info("Nothing new to fetch.")
        update_run_meta(
            run_dir,
            {
                **meta_base,
                "discovered_count": len(unique),
                "hydrated_count": len(existing),
            },
        )
        return

    total_new = 0
    with open(output_path, "a", encoding="utf-8") as out:
        for i, disc in enumerate(to_fetch):
            pid = disc["post_id"]
            query = disc.get("query", "")
            log.info("  [%d/%d] fetching %s...", i + 1, len(to_fetch), pid)

            try:
                post_data = fetch_post(pid)
            except Exception as e:
                log.warning("    failed to fetch post %s: %s", pid, e)
                continue

            if post_data is None:
                existing.add(pid)
                continue

            sources_used = ["arctic_shift"]
            fetch_quality = "full"

            try:
                comments_raw = fetch_comments(pid, comments_per_post)
            except Exception as e:
                log.warning("    failed to fetch comments for %s: %s", pid, e)
                comments_raw = []
                fetch_quality = "post_only"

            if comments_raw and len(comments_raw) < comments_per_post // 2:
                fetch_quality = "partial"

            record = _normalize_post(post_data, query)
            record["top_comments"] = _normalize_comments(
                comments_raw, post_data.get("author", "")
            )
            record["sources_used"] = sources_used
            record["fetch_quality"] = fetch_quality

            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            existing.add(pid)
            total_new += 1

    total = len(existing)
    log.info("\nDone. Added %d posts. Total hydrated: %d.", total_new, total)
    update_run_meta(
        run_dir,
        {**meta_base, "discovered_count": len(unique), "hydrated_count": total},
    )


if __name__ == "__main__":
    main()
