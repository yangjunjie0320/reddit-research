# Reddit Research

通过挖掘 Reddit 真实讨论，快速获取产品、话题、趋势的用户洞察。

## 安装

### 方式一：插件安装（推荐）

```bash
/plugin marketplace add yangjunjie0320/reddit-research
/plugin install reddit-research
```

### 方式二：手动安装

```bash
# 克隆到 skills 目录
git clone https://github.com/yangjunjie0320/reddit-research.git ~/.claude/skills/reddit-research
```

### 方式三：直接使用

```bash
git clone https://github.com/yangjunjie0320/reddit-research.git
cd reddit-research
claude
```

## 使用

安装后，直接说出想研究的关键词：

```
帮我研究 mechanical keyboard
```

首次使用时，Claude 会引导你完成环境设置。

## 示例

- `帮我研究 mechanical keyboard` - 产品调研
- `分析一下四天工作制的舆论` - 政策/社会话题
- `调研 Stanley cup 的用户痛点` - 产品痛点
- `研究 AI companion 的市场反应` - 趋势分析

## 项目结构

```
reddit-research/
├── .claude-plugin/
│   └── plugin.json       # 插件清单
├── SKILL.md              # 工作流文档
├── docs/SETUP.md              # 环境配置指南
├── docs/
│   └── REFERENCE.md      # 子版块速查
├── scripts/
│   ├── setup_check.py
│   ├── fetch_reddit.py
│   └── filter_posts.py
├── templates/
├── examples/
├── pyproject.toml
└── uv.lock
```

## 依赖

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Reddit API 凭证

## 文档

- [SKILL.md](SKILL.md) - 完整工作流
- [docs/SETUP.md](docs/SETUP.md) - 环境配置
- [docs/REFERENCE.md](docs/REFERENCE.md) - 子版块速查

## License

MIT
