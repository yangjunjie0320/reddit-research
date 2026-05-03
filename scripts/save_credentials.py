#!/usr/bin/env python3
"""
save_credentials.py

Interactively save API credentials to ./.secrets/reddit-research.env.
Uses getpass so keys are never echoed to the terminal or written to logs.

At least one of SERPER_API_KEY or BRAVE_API_KEY must be configured.

Usage:
    uv run python scripts/save_credentials.py
"""

import getpass
import os
import re
import stat
import sys
from pathlib import Path

ENV_DIR = Path(".secrets")
ENV_FILE = ENV_DIR / "reddit-research.env"

_PATTERN = re.compile(
    r"""^(?:export\s+)?([A-Z_][A-Z0-9_]*)=(?:"([^"]*)"|'([^']*)'|(.*))$"""
)


def load_env() -> None:
    """Load credentials from ./.secrets/reddit-research.env.

    Uses os.environ.setdefault so existing environment variables are not
    overridden. Safe to call multiple times.
    """
    if not ENV_FILE.exists():
        return
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _PATTERN.match(line)
        if not m:
            continue
        key = m.group(1)
        value = m.group(2) or m.group(3) or m.group(4) or ""
        os.environ.setdefault(key, value)


def _read_existing() -> dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    result: dict[str, str] = {}
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _PATTERN.match(line)
        if not m:
            continue
        key = m.group(1)
        value = m.group(2) or m.group(3) or m.group(4) or ""
        result[key] = value
    return result


def main() -> None:
    print("reddit-research credential setup")
    print(f"Saving to: {ENV_FILE}")
    print()

    existing = _read_existing()
    if existing:
        masked = {k: "***" for k in existing}
        print(f"Existing keys: {list(masked)}")
        print()

    serper_key = getpass.getpass(
        "SERPER_API_KEY (press Enter to keep existing or skip): "
    )
    if not serper_key and "SERPER_API_KEY" in existing:
        serper_key = existing["SERPER_API_KEY"]
        print("  Keeping existing SERPER_API_KEY.")

    brave_key = getpass.getpass(
        "BRAVE_API_KEY (press Enter to keep existing or skip): "
    )
    if not brave_key and "BRAVE_API_KEY" in existing:
        brave_key = existing["BRAVE_API_KEY"]
        print("  Keeping existing BRAVE_API_KEY.")

    if not serper_key and not brave_key:
        print(
            "[ERROR] At least one of SERPER_API_KEY or BRAVE_API_KEY is "
            "required.\n"
            "  Serper (free 2500/mo): https://serper.dev\n"
            "  Brave  (free 2000/mo): https://brave.com/search/api/",
            file=sys.stderr,
        )
        sys.exit(1)

    lines: list[str] = []
    if serper_key:
        lines.append(f'SERPER_API_KEY="{serper_key}"')
    if brave_key:
        lines.append(f'BRAVE_API_KEY="{brave_key}"')

    ENV_DIR.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ENV_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600

    print()
    print(f"Saved to {ENV_FILE} (mode 600).")
    print("Run `uv run python scripts/setup_check.py` to verify.")


if __name__ == "__main__":
    main()
