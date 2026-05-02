#!/usr/bin/env python3
"""
interactive_setup.py

交互式引导用户完成首次设置，包括：
1. 检查 Python 依赖
2. 引导创建 Reddit API 凭证
3. 保存凭证到 .env 文件
4. 验证 API 连接
"""

import os
import sys
import importlib
from pathlib import Path


def print_header(text: str):
    """打印带格式的标题"""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50 + "\n")


def print_step(step: int, total: int, text: str):
    """打印步骤"""
    print(f"\n[{step}/{total}] {text}")
    print("-" * 40)


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    """询问是/否问题"""
    suffix = " [Y/n]: " if default else " [y/N]: "
    while True:
        answer = input(prompt + suffix).strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes", "是"):
            return True
        if answer in ("n", "no", "否"):
            return False
        print("请输入 y 或 n")


def ask_input(prompt: str, required: bool = True) -> str:
    """询问输入"""
    while True:
        answer = input(prompt + ": ").strip()
        if answer or not required:
            return answer
        print("此项为必填")


def check_packages() -> bool:
    """检查必要的 Python 包"""
    required = {"praw": "praw", "yaml": "pyyaml"}
    missing = []

    for module, pip_name in required.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"❌ 缺少 Python 包: {', '.join(missing)}")
        print(f"\n   请运行: uv sync")
        return False

    print("✅ Python 依赖已安装")
    return True


def guide_reddit_credentials():
    """引导用户获取 Reddit API 凭证"""
    print("""
要使用此工具，你需要 Reddit API 凭证。以下是获取步骤：

1. 打开浏览器，访问:
   https://www.reddit.com/prefs/apps

2. 滚动到页面底部，点击 "create another app..." 或 "are you a developer? create an app..."

3. 填写表单:
   - name: 随便填，如 "reddit-research"
   - 选择 "script" 类型（重要！）
   - description: 可留空
   - about url: 可留空
   - redirect uri: 填 http://localhost:8080

4. 点击 "create app"

5. 创建后你会看到:
   - client_id: 在 "personal use script" 下方的一串字符
   - client_secret: 标记为 "secret" 的一串字符
""")

    input("\n按 Enter 继续，当你准备好凭证后...")


def collect_credentials() -> dict:
    """收集用户的 API 凭证"""
    print("\n请输入你的 Reddit API 凭证:\n")

    client_id = ask_input("Client ID (personal use script 下方的字符串)")
    client_secret = ask_input("Client Secret")

    # User Agent 建议格式
    default_ua = "python:reddit-research:v1.0 (by /u/anonymous)"
    print(f"\nUser Agent 用于标识你的应用。")
    print(f"建议格式: python:app-name:version (by /u/your-username)")
    user_agent = ask_input(f"User Agent (直接回车使用默认值)", required=False)
    if not user_agent:
        user_agent = default_ua

    return {
        "REDDIT_CLIENT_ID": client_id,
        "REDDIT_CLIENT_SECRET": client_secret,
        "REDDIT_USER_AGENT": user_agent,
    }


def save_to_env(credentials: dict, env_path: Path) -> bool:
    """保存凭证到 .env 文件"""
    try:
        lines = []
        for key, value in credentials.items():
            lines.append(f'{key}="{value}"')

        env_path.write_text("\n".join(lines) + "\n")
        print(f"✅ 凭证已保存到 {env_path}")
        return True
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False


def verify_connection(credentials: dict) -> bool:
    """验证 API 连接"""
    try:
        import praw

        reddit = praw.Reddit(
            client_id=credentials["REDDIT_CLIENT_ID"],
            client_secret=credentials["REDDIT_CLIENT_SECRET"],
            user_agent=credentials["REDDIT_USER_AGENT"],
        )

        # 尝试一个简单的 API 调用
        subreddit = reddit.subreddit("AskReddit")
        next(subreddit.hot(limit=1))

        print("✅ Reddit API 连接成功！")
        return True
    except Exception as e:
        print(f"❌ API 连接失败: {type(e).__name__}: {e}")
        return False


def print_next_steps():
    """打印后续步骤"""
    print("""
🎉 设置完成！

接下来你可以:

1. 每次使用前加载环境变量:
   source .env  # 或在 shell 配置中添加

2. 验证设置:
   uv run python scripts/setup_check.py

3. 开始研究:
   告诉 Claude 你想研究的关键词，例如:
   - "帮我研究 mechanical keyboard"
   - "分析一下 four day workweek 的舆论"
   - "调研 Stanley cup 的用户痛点"

详细文档请参考 SKILL.md
""")


def main():
    print_header("Reddit Research 首次设置向导")

    print("欢迎使用 Reddit Research！")
    print("这个向导将帮助你完成首次设置。\n")

    # 确定项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    env_path = project_root / ".env"

    total_steps = 4

    # Step 1: 检查依赖
    print_step(1, total_steps, "检查 Python 依赖")
    if not check_packages():
        print("\n请先安装依赖后重新运行此脚本。")
        sys.exit(1)

    # Step 2: 检查是否已有凭证
    print_step(2, total_steps, "检查现有配置")

    env_vars = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"]
    existing = all(os.environ.get(v) for v in env_vars)

    if existing:
        print("检测到环境变量中已有 Reddit 凭证。")
        if not ask_yes_no("是否重新配置"):
            # 直接验证现有凭证
            print_step(4, total_steps, "验证 API 连接")
            creds = {v: os.environ[v] for v in env_vars}
            if verify_connection(creds):
                print_next_steps()
            sys.exit(0)
    elif env_path.exists():
        print(f"检测到 {env_path} 文件已存在。")
        if not ask_yes_no("是否覆盖现有配置"):
            print("设置已取消。")
            sys.exit(0)
    else:
        print("未检测到现有配置，将创建新配置。")

    # Step 3: 引导并收集凭证
    print_step(3, total_steps, "获取 Reddit API 凭证")
    guide_reddit_credentials()
    credentials = collect_credentials()

    # 保存到 .env
    print("\n正在保存配置...")
    if not save_to_env(credentials, env_path):
        sys.exit(1)

    # Step 4: 验证连接
    print_step(4, total_steps, "验证 API 连接")
    if not verify_connection(credentials):
        print("\n凭证可能有误，请检查后重新运行此脚本。")
        print(f"你可以编辑 {env_path} 手动修正。")
        sys.exit(1)

    print_next_steps()


if __name__ == "__main__":
    main()
