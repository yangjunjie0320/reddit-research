#!/usr/bin/env python3
"""
setup_check.py

Verify the reddit-research environment is ready.

Exit codes:
    0 - all checks passed
    1 - missing dependencies or invalid credentials (see docs/SETUP.md)
"""

import importlib
import os
import sys

from save_credentials import ENV_FILE, load_env

REQUIRED_PACKAGES = ["requests", "yaml"]


def check_packages() -> bool:
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[FAIL] Missing Python packages: {', '.join(missing)}")
        print("  Run: uv sync")
        return False
    print("[OK] Python dependencies installed")
    return True


def check_credentials() -> bool:
    serper_key = os.environ.get("SERPER_API_KEY", "")
    brave_key = os.environ.get("BRAVE_API_KEY", "")

    if not serper_key and not brave_key:
        print("[FAIL] No search API key configured")
        print("  At least one of SERPER_API_KEY or BRAVE_API_KEY is required.")
        print("  Run: uv run python scripts/save_credentials.py")
        print("  See docs/SETUP.md for how to obtain keys.")
        return False

    keys = []
    if serper_key:
        keys.append("SERPER_API_KEY")
    if brave_key:
        keys.append("BRAVE_API_KEY")
    print(f"[OK] Credentials loaded ({' + '.join(keys)})")
    return True


def check_search_connectivity() -> bool:
    try:
        import requests
    except ImportError:
        return False

    serper_key = os.environ.get("SERPER_API_KEY", "")
    brave_key = os.environ.get("BRAVE_API_KEY", "")

    # Try Serper first if available.
    if serper_key:
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                json={"q": "site:reddit.com python", "num": 1},
                headers={
                    "X-API-KEY": serper_key,
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            if resp.status_code == 401:
                print("[FAIL] Serper API key invalid (HTTP 401)")
                print("  Run: uv run python scripts/save_credentials.py")
                if not brave_key:
                    return False
                print("  Falling through to Brave check...")
            elif resp.status_code == 429:
                print("[WARN] Serper API quota exhausted (HTTP 429)")
                if brave_key:
                    print("  Brave fallback configured, will auto-switch.")
                else:
                    print("  No Brave fallback. Wait for quota reset or add BRAVE_API_KEY.")
                    return False
            else:
                resp.raise_for_status()
                print("[OK] Serper API connectivity OK")
                return True
        except Exception as e:
            print(f"[WARN] Serper connectivity failed: {type(e).__name__}: {e}")
            if not brave_key:
                return False

    # Try Brave if available.
    if brave_key:
        try:
            resp = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": "site:reddit.com python", "count": 1},
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": brave_key,
                },
                timeout=10,
            )
            if resp.status_code == 401:
                print("[FAIL] Brave API key invalid (HTTP 401)")
                print("  Run: uv run python scripts/save_credentials.py")
                return False
            if resp.status_code == 429:
                print("[FAIL] Brave API quota exhausted (HTTP 429)")
                return False
            resp.raise_for_status()
            print("[OK] Brave API connectivity OK")
            return True
        except Exception as e:
            print(f"[FAIL] Brave connectivity failed: {type(e).__name__}: {e}")
            return False

    return False


def main() -> None:
    load_env()
    if ENV_FILE.exists():
        print(f"[INFO] Loaded credentials from {ENV_FILE}")
    else:
        print(f"[INFO] Credential file not found ({ENV_FILE})")
        print("  Run: uv run python scripts/save_credentials.py")

    ok = True
    ok = check_packages() and ok
    ok = check_credentials() and ok
    if ok:
        ok = check_search_connectivity() and ok

    if not ok:
        sys.exit(1)

    print()
    print("All checks passed.")


if __name__ == "__main__":
    main()
