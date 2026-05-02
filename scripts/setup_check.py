#!/usr/bin/env python3
"""
setup_check.py

验证 reddit-research 技能的环境是否就绪。

退出码：
    0 - 一切正常，可以开始研究
    1 - 缺少依赖或凭证无效，参见 SETUP.md
"""

import importlib
import os
import re
import sys
from pathlib import Path


REQUIRED_PACKAGES = ["praw", "yaml"]
REQUIRED_ENV = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"]

# 支持多个 .env 位置
ENV_LOCATIONS = [
    Path.cwd() / ".env",
    Path(__file__).parent.parent / ".env",  # skills/reddit-research/.env
    Path(__file__).parent.parent.parent.parent / ".env",  # 项目根目录
]


def load_env_file():
    """从 .env 文件加载环境变量。

    支持格式：
        export FOO="bar"
        FOO=bar
    """
    for env_path in ENV_LOCATIONS:
        if env_path.exists():
            pattern = re.compile(
                r"""^(?:export\s+)?([A-Z_][A-Z0-9_]*)=(?:"([^"]*)"|'([^']*)'|(.*))$"""
            )
            for raw in env_path.read_text().splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                m = pattern.match(line)
                if not m:
                    continue
                key = m.group(1)
                value = m.group(2) or m.group(3) or m.group(4) or ""
                os.environ.setdefault(key, value)
            return env_path
    return None


def check_packages():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[FAIL] 缺少 Python 包: {', '.join(missing)}")
        print("  运行: uv sync")
        return False
    print("[OK] Python 依赖已安装")
    return True


def check_env():
    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        print(f"[FAIL] 缺少环境变量: {', '.join(missing)}")
        print("  请参考 SETUP.md 配置 Reddit API 凭证")
        return False
    print("[OK] Reddit 凭证已加载")
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
        next(reddit.subreddit("AskReddit").hot(limit=1))
        print("[OK] Reddit API 连接成功")
        return True
    except Exception as e:
        print(f"[FAIL] Reddit API 连接失败: {type(e).__name__}: {e}")
        print("  请检查凭证，参见 SETUP.md")
        return False


def main():
    env_path = load_env_file()
    if env_path:
        print(f"[INFO] 从 {env_path} 加载凭证")

    ok = True
    ok = check_packages() and ok
    ok = check_env() and ok
    if ok:
        ok = check_connectivity() and ok

    if not ok:
        sys.exit(1)

    print()
    print("All checks passed. 环境就绪。")


if __name__ == "__main__":
    main()
