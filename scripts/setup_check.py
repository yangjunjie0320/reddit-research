#!/usr/bin/env python3
"""
setup_check.py

Verify Reddit API credentials and required Python packages are in place
before running fetch_reddit.py.

Exits 0 on success, 1 on any failure with a clear remediation message.
"""

import os
import sys
import importlib


REQUIRED_PACKAGES = ["praw", "yaml"]
REQUIRED_ENV = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"]


def check_packages():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[FAIL] Missing Python packages: {', '.join(missing)}")
        pip_names = {"yaml": "pyyaml"}
        install = [pip_names.get(p, p) for p in missing]
        print(f"  Install with: pip install {' '.join(install)}")
        return False
    print("[OK] Python packages present")
    return True


def check_env():
    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        print(f"[FAIL] Missing environment variables: {', '.join(missing)}")
        print("  Get credentials at https://www.reddit.com/prefs/apps")
        print("  Create a script type app, then export:")
        for v in REQUIRED_ENV:
            print(f"    export {v}=...")
        return False
    print("[OK] Reddit credentials present in environment")
    return True


def check_connectivity():
    try:
        import praw
    except ImportError:
        return False
    try:
        reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent=os.environ["REDDIT_USER_AGENT"],
        )
        # A cheap read only call to verify auth.
        next(reddit.subreddit("AskReddit").hot(limit=1))
        print("[OK] Reddit API reachable, credentials valid")
        return True
    except Exception as e:
        print(f"[FAIL] Reddit API call failed: {type(e).__name__}: {e}")
        return False


def main():
    ok = True
    ok = check_packages() and ok
    ok = check_env() and ok
    if ok:
        ok = check_connectivity() and ok
    if not ok:
        sys.exit(1)
    print("\nAll checks passed. Ready to run fetch_reddit.py.")


if __name__ == "__main__":
    main()
