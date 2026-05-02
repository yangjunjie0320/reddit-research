#!/usr/bin/env python3
"""
filter_posts.py

Apply rule based filters to raw_posts.jsonl. The defaults remove low
engagement, very short, very old, or moderation flagged posts. All
thresholds can be overridden via --profile (reads filter_overrides from
profile.yaml) or via explicit CLI flags (highest priority).

Usage:
    python filter_posts.py --input research/<slug>/raw_posts.jsonl \\
                           --output research/<slug>/candidates.jsonl

    # Let profile.yaml drive overrides:
    python filter_posts.py --profile research/<slug>/profile.yaml \\
                           --input research/<slug>/raw_posts.jsonl \\
                           --output research/<slug>/candidates.jsonl
"""

import argparse
import json
import sys
import time
from pathlib import Path

import yaml


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

# Keys in filter_overrides that map directly to cfg keys.
_OVERRIDE_KEY_MAP = {
    "min_score": "min_score",
    "min_comments": "min_comments",
    "min_selftext_chars": "min_selftext_chars",
    "min_top_comment_chars": "min_top_comment_chars",
    "max_age_months": "max_age_months",
    "drop_stickied": "drop_stickied",
    "drop_locked": "drop_locked",
    "drop_over_18": "drop_over_18",
}


def load_profile_overrides(profile_path: str) -> dict:
    """Read filter_overrides from a profile YAML. Returns empty dict on error."""
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f) or {}
        overrides = profile.get("filter_overrides") or {}
        if not isinstance(overrides, dict):
            return {}
        # Only keep recognised keys.
        return {k: v for k, v in overrides.items() if k in _OVERRIDE_KEY_MAP}
    except Exception as e:
        print(f"Warning: could not read filter_overrides from {profile_path}: {e}")
        return {}


def post_passes(post: dict, cfg: dict, now_utc: float) -> tuple[bool, str]:
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

    # Removed posts often have selftext starting with "[removed" or "[deleted".
    selftext_lower = post.get("selftext", "").strip().lower()
    if selftext_lower.startswith("[removed") or selftext_lower.startswith("[deleted"):
        if not comments_ok:
            return False, "removed body, thin comments"

    return True, "kept"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--profile",
        default=None,
        help="Path to profile.yaml; filter_overrides section is read as defaults",
    )
    parser.add_argument("--min-score", type=int, default=None)
    parser.add_argument("--min-comments", type=int, default=None)
    parser.add_argument("--min-selftext-chars", type=int, default=None)
    parser.add_argument("--min-top-comment-chars", type=int, default=None)
    parser.add_argument("--max-age-months", type=int, default=None)
    parser.add_argument("--keep-stickied", action="store_true")
    parser.add_argument("--keep-locked", action="store_true")
    parser.add_argument("--drop-over-18", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="Print drop reasons")
    args = parser.parse_args()

    # Priority: CLI flag > profile filter_overrides > DEFAULTS.
    profile_overrides = {}
    if args.profile:
        profile_overrides = load_profile_overrides(args.profile)
        if profile_overrides:
            print(f"Loaded filter_overrides from profile: {profile_overrides}")

    def _resolve(key: str, cli_val):
        """Return CLI value if explicitly set, else profile override, else default."""
        if cli_val is not None:
            return cli_val
        return profile_overrides.get(key, DEFAULTS[key])

    cfg = {
        "min_score": _resolve("min_score", args.min_score),
        "min_comments": _resolve("min_comments", args.min_comments),
        "min_selftext_chars": _resolve("min_selftext_chars", args.min_selftext_chars),
        "min_top_comment_chars": _resolve("min_top_comment_chars", args.min_top_comment_chars),
        "max_age_months": _resolve("max_age_months", args.max_age_months),
        "drop_stickied": False if args.keep_stickied else _resolve("drop_stickied", None),
        "drop_locked": False if args.keep_locked else _resolve("drop_locked", None),
        "drop_over_18": True if args.drop_over_18 else _resolve("drop_over_18", None),
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
