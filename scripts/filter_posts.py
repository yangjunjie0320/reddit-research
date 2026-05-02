#!/usr/bin/env python3
"""
filter_posts.py

Apply rule based filters to raw_posts.jsonl. The defaults remove low
engagement, very short, very old, or moderation flagged posts. All
thresholds can be overridden via flags.

Usage:
    python filter_posts.py --input research/<slug>/raw_posts.jsonl \\
                           --output research/<slug>/candidates.jsonl
"""

import argparse
import json
import sys
import time
from pathlib import Path


DEFAULTS = {
    "min_score": 5,
    "min_comments": 3,
    "min_selftext_chars": 100,
    "min_top_comment_chars": 200,  # alternative path: short OP, rich comments
    "max_age_months": 24,
    "drop_stickied": True,
    "drop_locked": True,
    "drop_over_18": False,
}


def post_passes(post, cfg, now_utc):
    if cfg["drop_stickied"] and post.get("stickied"):
        return False, "stickied"
    if cfg["drop_locked"] and post.get("locked"):
        return False, "locked"
    if cfg["drop_over_18"] and post.get("over_18"):
        return False, "over_18"

    age_seconds = now_utc - post.get("created_utc", 0)
    age_months = age_seconds / (60 * 60 * 24 * 30.44)
    if age_months > cfg["max_age_months"]:
        return False, f"too old ({age_months:.1f} months)"

    if post.get("score", 0) < cfg["min_score"]:
        return False, "low score"
    if post.get("num_comments", 0) < cfg["min_comments"]:
        return False, "few comments"

    selftext_ok = len(post.get("selftext", "")) >= cfg["min_selftext_chars"]
    top_comments = post.get("top_comments", [])
    longest_comment = max((len(c.get("body", "")) for c in top_comments), default=0)
    comments_ok = longest_comment >= cfg["min_top_comment_chars"]

    if not selftext_ok and not comments_ok:
        return False, "thin content"

    # Removed posts often have selftext == "[removed]" or "[deleted]".
    if post.get("selftext", "").strip() in {"[removed]", "[deleted]"}:
        if not comments_ok:
            return False, "removed body, thin comments"

    return True, "kept"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-score", type=int, default=DEFAULTS["min_score"])
    parser.add_argument("--min-comments", type=int, default=DEFAULTS["min_comments"])
    parser.add_argument("--min-selftext-chars", type=int, default=DEFAULTS["min_selftext_chars"])
    parser.add_argument(
        "--min-top-comment-chars", type=int, default=DEFAULTS["min_top_comment_chars"]
    )
    parser.add_argument("--max-age-months", type=int, default=DEFAULTS["max_age_months"])
    parser.add_argument("--keep-stickied", action="store_true")
    parser.add_argument("--keep-locked", action="store_true")
    parser.add_argument("--drop-over-18", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="Print drop reasons")
    args = parser.parse_args()

    cfg = {
        "min_score": args.min_score,
        "min_comments": args.min_comments,
        "min_selftext_chars": args.min_selftext_chars,
        "min_top_comment_chars": args.min_top_comment_chars,
        "max_age_months": args.max_age_months,
        "drop_stickied": not args.keep_stickied,
        "drop_locked": not args.keep_locked,
        "drop_over_18": args.drop_over_18,
    }

    inp = Path(args.input)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    now_utc = time.time()
    kept = 0
    dropped = 0
    drop_reasons = {}

    with open(inp, "r", encoding="utf-8") as fin, open(out, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                post = json.loads(line)
            except json.JSONDecodeError:
                continue
            ok, reason = post_passes(post, cfg, now_utc)
            if ok:
                fout.write(json.dumps(post, ensure_ascii=False) + "\n")
                kept += 1
            else:
                dropped += 1
                drop_reasons[reason] = drop_reasons.get(reason, 0) + 1
                if args.verbose:
                    print(f"  dropped {post.get('id')}: {reason}")

    print(f"Kept {kept}, dropped {dropped}")
    if drop_reasons:
        print("Drop reasons:")
        for r, n in sorted(drop_reasons.items(), key=lambda x: -x[1]):
            print(f"  {n:4d}  {r}")


if __name__ == "__main__":
    main()
