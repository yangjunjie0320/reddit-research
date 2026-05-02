# 环境配置（一次性）

本文件仅在 `scripts/setup_check.py` 检测到环境未就绪时阅读。配置完成后无需再读本文件。

## 一、安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

安装后重新打开终端，或运行 `source ~/.bashrc`（或 `~/.zshrc`）。验证：

```bash
uv --version
```

## 二、安装依赖

在技能目录下运行：

```bash
uv sync
```

这会读取 `pyproject.toml`，创建 `.venv/` 并安装 PRAW 和 PyYAML。

## 三、获取 Reddit API 凭证

1. 浏览器打开 https://www.reddit.com/prefs/apps
2. 滚动到底部，点击「create another app...」
3. 填写表单：
   - **name**：随意，如 `reddit-research`
   - **类型**：必须选 **script**
   - **redirect uri**：填 `http://localhost:8080`
4. 点击 create app
5. 记录以下信息：
   - **Client ID**：在「personal use script」下方的字符串
   - **Client Secret**：标记为 secret 的字符串

## 四、保存凭证

将凭证告诉 Claude，Claude 会帮你写入 `.env` 文件：

```bash
cat > .env << 'EOF'
export REDDIT_CLIENT_ID="你的ID"
export REDDIT_CLIENT_SECRET="你的密钥"
export REDDIT_USER_AGENT="python:reddit-research:v1.0 (by /u/anonymous)"
EOF
```

然后加载：

```bash
source .env
```

## 五、验证

```bash
uv run python scripts/setup_check.py
```

看到 `All checks passed` 即配置成功。

## 排错

| 错误 | 原因 | 解决 |
|------|------|------|
| `uv sync` 网络超时 | 代理问题 | 配置 `UV_INDEX_URL` 指向国内镜像 |
| 401 Unauthorized | client_id/secret 错误或应用类型不是 script | 重新检查凭证 |
| 429 Too Many Requests | user_agent 太通用 | 改成 `python:reddit-research:v1.0 (by /u/yourname)` |
| ModuleNotFoundError | 没用 `uv run` 前缀 | 用 `uv run python scripts/...` |
