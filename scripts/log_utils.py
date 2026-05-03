#!/usr/bin/env python3
"""
log_utils.py

Shared utilities for pipeline scripts: logging, JSONL loading, run metadata.
"""

import json
import logging
import sys
from pathlib import Path

_FILE_FMT = logging.Formatter(
    "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class _ConsoleFmt(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        if record.levelno >= logging.WARNING:
            return f"[{record.levelname}] {msg}"
        return msg


def get_logger(name: str, run_dir: Path | None = None) -> logging.Logger:
    """Return a named logger, adding handlers only once per logger instance.

    Safe to call multiple times with the same name — handlers are not
    duplicated on subsequent calls. Later calls with a new run_dir are ignored
    if the logger is already configured; scripts should call this once at the
    top of main().
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(_ConsoleFmt())
    logger.addHandler(sh)

    if run_dir is not None:
        run_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(run_dir / "run.log", encoding="utf-8", mode="a")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(_FILE_FMT)
        logger.addHandler(fh)

    return logger


def load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file, skipping blank lines and malformed entries."""
    if not path.exists():
        return []
    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def update_run_meta(run_dir: Path, updates: dict) -> None:
    """Merge `updates` into run_dir/run_meta.json, preserving existing keys."""
    meta_path = run_dir / "run_meta.json"
    meta: dict = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    meta.update(updates)
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
