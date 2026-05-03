#!/usr/bin/env python3
"""
filter_posts.py

Apply rule-based filters to hydrated_posts.jsonl. Defaults remove low
engagement, very short, very old, or moderation-flagged posts. Thresholds
can be overridden via profile.yaml filter_overrides or CLI flags.

Usage:
    uv run python scripts/filter_posts.py --run runs/{run_id}
    uv run python scripts/filter_posts.py --run runs/{run_id} --min-score 10 --verbose
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import yaml

from log_utils import get_logger, update_run_meta

_log = logging.getLogger(__name__)

DEFAULTS = {
    "min_score": 5,
    "min_comments": 3,
    "min_selftext_chars": 100,
    "min_top_comment_chars": 200,
    "max_age_months": 24,
    "drop_stickied": True,
    "drop_locked": True,
    "drop_over_18": False,
}

_OVERRIDE_KEYS = set(DEFAULTS.keys())


def _load_profile_overrides(profile_path: Path) -> dict:
    try:
        with open(profile_path, encoding="utf-8") as f:
            profile = yaml.safe_load(f) or {}
        overrides = profile.get("filter_overrides") or {}
        if not isinstance(overrides, dict):
            return {}
        return {k: v for k, v in overrides.items() if k in _OVERRIDE_KEYS}
    except Exception as e:
        _log.warning("could not read filter_overrides: %s", e)
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

    selftext_lower = post.get("selftext", "").strip().lower()
    if (
        selftext_lower.startswith("[removed") or selftext_lower.startswith("[deleted")
    ) and not comments_ok:
        return False, "removed body, thin comments"

    return True, "kept"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter hydrated posts by engagement, age, and content."
    )
    parser.add_argument("--run", required=True, help="Run directory path")
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

    run_dir = Path(args.run)
    inp = run_dir / "hydrated_posts.jsonl"
    out = run_dir / "filtered_posts.jsonl"
    profile_path = run_dir / "profile.yaml"

    log = get_logger(__name__, run_dir)

    if not inp.exists():
        log.error("%s not found. Run fetch_reddit.py first.", inp)
        sys.exit(1)

    # Priority: CLI flag > profile filter_overrides > DEFAULTS.
    profile_overrides = {}
    if profile_path.exists():
        profile_overrides = _load_profile_overrides(profile_path)
        if profile_overrides:
            log.info("Loaded filter_overrides from profile: %s", profile_overrides)

    def _resolve(key: str, cli_val: object) -> object:
        if cli_val is not None:
            return cli_val
        return profile_overrides.get(key, DEFAULTS[key])

    cfg = {
        "min_score": _resolve("min_score", args.min_score),
        "min_comments": _resolve("min_comments", args.min_comments),
        "min_selftext_chars": _resolve("min_selftext_chars", args.min_selftext_chars),
        "min_top_comment_chars": _resolve(
            "min_top_comment_chars", args.min_top_comment_chars
        ),
        "max_age_months": _resolve("max_age_months", args.max_age_months),
        "drop_stickied": (
            False if args.keep_stickied else _resolve("drop_stickied", None)
        ),
        "drop_locked": (False if args.keep_locked else _resolve("drop_locked", None)),
        "drop_over_18": (True if args.drop_over_18 else _resolve("drop_over_18", None)),
    }

    now_utc = time.time()
    kept = 0
    dropped = 0
    drop_reasons: dict[str, int] = {}

    with (
        open(inp, encoding="utf-8") as fin,
        open(out, "w", encoding="utf-8") as fout,
    ):
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
                    log.info("  dropped %s: %s", post.get("id"), reason)

    log.info("Kept %d, dropped %d", kept, dropped)
    if drop_reasons:
        log.info("Drop reasons:")
        for r, n in sorted(drop_reasons.items(), key=lambda x: -x[1]):
            log.info("  %4d  %s", n, r)

    update_run_meta(run_dir, {"filtered_count": kept})


if __name__ == "__main__":
    main()
