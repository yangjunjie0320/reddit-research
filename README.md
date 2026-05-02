# Reddit Research

通过挖掘 Reddit 真实讨论，快速获取产品、话题、趋势的用户洞察。

## 安装（推荐）

使用 Claude Code 插件系统安装：

```bash
# 1. 添加插件源
/plugin marketplace add yangjunjie0320/reddit-research

# 2. 安装插件
/plugin install reddit-research
```

## 其他安装方式

### 手动安装到 skills 目录

```bash
# 克隆仓库
git clone https://github.com/yangjunjie0320/reddit-research.git

# 复制到全局 skills 目录
cp -r reddit-research/skills/reddit-research ~/.claude/skills/
```

### 直接在项目目录使用

```bash
git clone https://github.com/yangjunjie0320/reddit-research.git
cd reddit-research
claude
```

## 使用方法

安装后，在 Claude Code 中直接说：

```
帮我研究 mechanical keyboard
```

首次使用时，Claude 会自动引导你完成环境设置（安装依赖、配置 Reddit API 凭证）。

## 使用示例

- `帮我研究 mechanical keyboard` - 产品调研
- `分析一下四天工作制的舆论` - 政策/社会话题
- `调研 Stanley cup 的用户痛点` - 产品痛点挖掘
- `研究 AI companion 的市场反应` - 趋势分析

## 多语言支持

支持多种语言的关键词：英语、中文、日语、韩语、西班牙语、德语。

## 输出

研究完成后会生成：

```
research/<关键词>/
├── profile.yaml      # 研究画像
├── raw_posts.jsonl   # 原始帖子
├── candidates.jsonl  # 筛选后的帖子
├── analysis.jsonl    # 语义分析结果
├── aggregates.json   # 聚合数据
└── report.md         # 最终报告
```

## 项目结构

```
reddit-research/
├── .claude-plugin/
│   └── plugin.json           # 插件清单
├── skills/
│   └── reddit-research/
│       ├── SKILL.md          # 工作流文档
│       ├── docs/
│       ├── scripts/
│       ├── templates/
│       └── examples/
├── pyproject.toml
└── uv.lock
```

## 依赖

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Reddit API 凭证（免费，Claude 会引导你获取）

## 文档

- [SKILL.md](skills/reddit-research/SKILL.md) - 完整工作流程文档
- [REFERENCE.md](skills/reddit-research/docs/REFERENCE.md) - Reddit 子版块速查表

## License

MIT
