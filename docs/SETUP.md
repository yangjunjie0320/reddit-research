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

这会读取 `pyproject.toml`，创建 `.venv/` 并安装 PyYAML 和 Requests。

## 三、获取搜索 API key（至少一个）

至少配置 Serper 或 Brave 其中一个。两个都配置时自动合并搜索结果。

### Serper（推荐）

免费额度 2500 次/月。

1. 浏览器打开 https://serper.dev
2. 注册账号并登录
3. 在 Dashboard 首页复制 API key

### Brave Search API（可选）

免费额度 2000 次/月。Serper 配额耗尽时自动 fallback。

1. 浏览器打开 https://brave.com/search/api/
2. 注册并订阅免费套餐
3. 在控制台复制 API key

## 四、保存凭证

运行交互式凭证保存脚本（key 不会显示在终端）：

```bash
uv run python scripts/save_credentials.py
```

脚本会将凭证保存到 `./.secrets/reddit-research.env`（权限 600）。

## 五、验证

```bash
uv run python scripts/setup_check.py
```

看到 `All checks passed` 即配置成功。

## 排错

| 错误 | 原因 | 解决 |
|------|------|------|
| `uv sync` 网络超时 | 代理问题 | 配置 `UV_INDEX_URL` 指向国内镜像 |
| `No search API key configured` | 凭证未保存 | 运行 `uv run python scripts/save_credentials.py` |
| `Serper API key invalid (HTTP 401)` | key 错误或已失效 | 重新运行 `save_credentials.py` |
| `API quota exhausted (HTTP 429)` | 本月免费额度用完 | 等待次月重置，或配置另一个后端 |
| `ModuleNotFoundError` | 没用 `uv run` 前缀 | 用 `uv run python scripts/...` |
| Arctic Shift 返回空结果 | 帖子已删除或不在 dump 中 | 正常现象，会被静默跳过 |
