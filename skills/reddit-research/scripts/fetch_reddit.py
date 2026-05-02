#!/usr/bin/env python3
"""
fetch_reddit.py

Profile agnostic Reddit fetcher. Reads a profile YAML, searches each
keyword group across each listed subreddit, pulls top comments per
post, writes one JSON object per line to raw_posts.jsonl.

Resume safe: rerunning skips post IDs already saved.

Usage:
    python fetch_reddit.py --profile research/<slug>/profile.yaml
    python fetch_reddit.py --profile <path> --output <path>  # override output
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import praw
import yaml


def load_profile(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def existing_post_ids(output_path):
    if not output_path.exists():
        return set()
    ids = set()
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "id" in obj:
                    ids.add(obj["id"])
            except json.JSONDecodeError:
                continue
    return ids


def serialize_post(submission, comments_per_post):
    submission.comment_sort = "top"
    submission.comments.replace_more(limit=0)
    top_comments = []
    for c in submission.comments[:comments_per_post]:
        top_comments.append(
            {
                "id": c.id,
                "body": c.body,
                "score": c.score,
                "created_utc": c.created_utc,
                "is_submitter": c.is_submitter,
            }
        )
    return {
        "id": submission.id,
        "subreddit": str(submission.subreddit),
        "title": submission.title,
        "selftext": submission.selftext or "",
        "url": f"https://www.reddit.com{submission.permalink}",
        "score": submission.score,
        "upvote_ratio": submission.upvote_ratio,
        "num_comments": submission.num_comments,
        "created_utc": submission.created_utc,
        "stickied": submission.stickied,
        "locked": submission.locked,
        "over_18": submission.over_18,
        "is_self": submission.is_self,
        "link_flair_text": submission.link_flair_text,
        "fetched_via_query": None,  # filled by caller
        "top_comments": top_comments,
    }


def fetch(profile, output_path, *, dry_run: bool = False):
    subreddits = profile["recommended_subreddits"]
    queries = profile["keyword_groups"]
    fetch_cfg = profile.get("fetch", {})
    posts_per_keyword = fetch_cfg.get("posts_per_keyword", 25)
    comments_per_post = fetch_cfg.get("comments_per_post", 15)
    time_filter = fetch_cfg.get("time_filter", "year")

    total_searches = len(subreddits) * len(queries)
    print(f"Plan: {len(subreddits)} subreddits × {len(queries)} queries = {total_searches} searches")
    print(f"  posts_per_keyword={posts_per_keyword}, comments_per_post={comments_per_post}, time_filter={time_filter}")
    for sub_name in subreddits:
        print(f"  r/{sub_name}")

    if dry_run:
        print("\n[DRY RUN] No API calls made. Exiting.")
        return

    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )

    seen = existing_post_ids(output_path)
    print(f"Already have {len(seen)} posts in {output_path}; will skip duplicates.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "a", encoding="utf-8") as out:
        total_new = 0
        for sub_name in subreddits:
            sub = reddit.subreddit(sub_name)
            for query in queries:
                print(f"  searching r/{sub_name} for: {query}")
                results = []
                for attempt in range(3):
                    try:
                        results = list(
                            sub.search(
                                query,
                                sort="relevance",
                                time_filter=time_filter,
                                limit=posts_per_keyword,
                            )
                        )
                        break
                    except Exception as e:
                        print(f"    error: {type(e).__name__}: {e} (attempt {attempt + 1}/3)")
                        if attempt == 2:
                            print("    skipping after 3 attempts")
                        else:
                            time.sleep(2 ** attempt)
                
                if not results:
                    continue

                added_for_query = 0
                for submission in results:
                    if submission.id in seen:
                        continue
                    try:
                        record = serialize_post(submission, comments_per_post)
                        record["fetched_via_query"] = query
                        out.write(json.dumps(record, ensure_ascii=False) + "\n")
                        out.flush()
                        seen.add(submission.id)
                        added_for_query += 1
                        total_new += 1
                    except Exception as e:
                        print(f"    failed on post {submission.id}: {e}")
                print(f"    +{added_for_query} new")
                time.sleep(1)  # conservative interval to avoid rate limiting

        print(f"\nDone. Added {total_new} new posts. Total in file: {len(seen)}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, help="Path to profile.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Preview search plan without API calls")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSONL path (default: research/<slug>/raw_posts.jsonl)",
    )
    args = parser.parse_args()

    profile = load_profile(args.profile)
    if args.output:
        output_path = Path(args.output)
    else:
        slug = profile.get("slug")
        if not slug:
            print("Profile missing 'slug' field and no --output given.", file=sys.stderr)
            sys.exit(1)
        output_path = Path("research") / slug / "raw_posts.jsonl"

    fetch(profile, output_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
