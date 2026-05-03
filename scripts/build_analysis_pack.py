#!/usr/bin/env python3
"""
build_analysis_pack.py

Assemble filtered posts and profile context into a single Markdown file
that the LLM reads during Stage 4 (semantic analysis).

Usage:
    uv run python scripts/build_analysis_pack.py --run runs/{run_id}
"""

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

from log_utils import get_logger, load_jsonl, update_run_meta

_log = logging.getLogger(__name__)


def _format_date(utc: int | float) -> str:
    if not utc:
        return "unknown"
    return datetime.fromtimestamp(utc, tz=timezone.utc).strftime("%Y-%m-%d")


def _subreddit_distribution(posts: list[dict]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for p in posts:
        sub = p.get("subreddit", "unknown")
        counts[sub] = counts.get(sub, 0) + 1
    return sorted(counts.items(), key=lambda x: -x[1])


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [truncated]"


def build_pack(run_dir: Path) -> tuple[str, int]:
    profile_path = run_dir / "profile.yaml"
    filtered_path = run_dir / "filtered_posts.jsonl"

    if not profile_path.exists():
        raise FileNotFoundError(profile_path)
    if not filtered_path.exists():
        raise FileNotFoundError(f"{filtered_path} — run filter_posts.py first")

    with open(profile_path, encoding="utf-8") as f:
        profile = yaml.safe_load(f)

    posts = load_jsonl(filtered_path)
    if not posts:
        raise ValueError("filtered_posts.jsonl is empty")

    # --- Header ---
    keyword = profile.get("keyword", "")
    slug = profile.get("slug", "")
    intent = profile.get("research_intent", "").strip()
    categorization = profile.get("categorization", {})
    emphasis = profile.get("analysis_emphasis", [])
    report_modules = profile.get("report_modules", [])

    cat_str = ", ".join(f"{k}: {v}" for k, v in categorization.items())
    emphasis_str = ", ".join(emphasis)
    modules_str = ", ".join(report_modules)

    # --- Stats ---
    sub_dist = _subreddit_distribution(posts)
    sub_dist_str = ", ".join(f"r/{s} ({n})" for s, n in sub_dist)

    timestamps = [p.get("created_utc", 0) for p in posts if p.get("created_utc")]
    earliest = _format_date(min(timestamps)) if timestamps else "unknown"
    latest = _format_date(max(timestamps)) if timestamps else "unknown"

    quality_counts: dict[str, int] = {}
    for p in posts:
        q = p.get("fetch_quality", "unknown")
        quality_counts[q] = quality_counts.get(q, 0) + 1
    quality_str = ", ".join(f"{k}: {v}" for k, v in quality_counts.items())

    # --- Build markdown ---
    lines: list[str] = []
    lines.append(f"# Analysis Pack: {keyword}\n")
    lines.append("## Research Context\n")
    lines.append(f"- **Keyword**: {keyword}")
    lines.append(f"- **Slug**: {slug}")
    lines.append(f"- **Intent**: {intent}")
    lines.append(f"- **Categorization**: {cat_str}")
    lines.append(f"- **Analysis Emphasis**: {emphasis_str}")
    lines.append(f"- **Report Modules**: {modules_str}")
    lines.append("")
    lines.append("## Dataset Summary\n")
    lines.append(f"- **Total posts**: {len(posts)}")
    lines.append(f"- **Subreddit distribution**: {sub_dist_str}")
    lines.append(f"- **Time range**: {earliest} to {latest}")
    lines.append(f"- **Fetch quality**: {quality_str}")
    lines.append("")
    lines.append("## Posts\n")

    for i, post in enumerate(posts, 1):
        pid = post.get("id", "?")
        title = post.get("title", "(no title)")
        subreddit = post.get("subreddit", "?")
        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)
        url = post.get("url", "")
        date = _format_date(post.get("created_utc", 0))
        quality = post.get("fetch_quality", "unknown")
        sources = ", ".join(post.get("sources_used", []))
        selftext = post.get("selftext", "")
        comments = post.get("top_comments", [])

        lines.append(
            f"### Post {i}: {title} "
            f"[r/{subreddit}] [score: {score}] [comments: {num_comments}]"
        )
        lines.append(
            f"ID: {pid} | URL: {url} | Date: {date} | "
            f"Quality: {quality} | Sources: {sources}"
        )
        lines.append("")

        if selftext:
            lines.append("**Body:**")
            lines.append(_truncate(selftext, 2000))
            lines.append("")

        if comments:
            lines.append(f"**Top Comments ({len(comments)}):**")
            for j, c in enumerate(comments[:10], 1):
                c_score = c.get("score", 0)
                c_body = _truncate(c.get("body", ""), 500)
                submitter = " [OP]" if c.get("is_submitter") else ""
                lines.append(f"{j}. [score: {c_score}]{submitter} {c_body}")
            lines.append("")

        lines.append("---\n")

    return "\n".join(lines), len(posts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build analysis pack from filtered posts."
    )
    parser.add_argument("--run", required=True, help="Run directory path")
    args = parser.parse_args()

    run_dir = Path(args.run)
    log = get_logger(__name__, run_dir)
    pack_md, post_count = build_pack(run_dir)

    out_path = run_dir / "analysis_pack.md"
    out_path.write_text(pack_md, encoding="utf-8")
    log.info("Written %s (%d chars)", out_path, len(pack_md))

    update_run_meta(run_dir, {"analysis_pack_posts": post_count})


if __name__ == "__main__":
    main()
