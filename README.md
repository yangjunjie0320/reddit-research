# Reddit Research

通过挖掘 Reddit 真实讨论，快速获取产品、话题、趋势的用户洞察。

## 这是什么？

一个 Claude Code 技能，让你只需提供一个关键词，就能自动：

1. 分析关键词类型，生成研究画像
2. 从相关 Reddit 子版块抓取讨论帖子
3. 过滤低质量内容
4. 对帖子进行语义分析
5. 生成结构化的调研报告

## 快速开始

### 1. 安装 Claude Code

如果还没安装，先安装 Claude Code CLI：

```bash
npm install -g @anthropic-ai/claude-code
```

### 2. 进入项目目录

```bash
cd reddit-research
```

### 3. 开始使用

运行 Claude Code：

```bash
claude
```

然后直接告诉它你想研究什么：

```
帮我研究 mechanical keyboard
```

Claude 会自动检查环境，如果是首次使用会引导你完成设置（安装依赖、配置 Reddit API 凭证）。

## 使用示例

- `帮我研究 mechanical keyboard` - 产品调研
- `分析一下四天工作制的舆论` - 政策/社会话题
- `调研 Stanley cup 的用户痛点` - 产品痛点挖掘
- `研究 AI companion 的市场反应` - 趋势分析

## 多语言支持

支持多种语言的关键词：英语、中文、日语、韩语、西班牙语、德语。

## 输出示例

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

## 依赖

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) - Python 包管理器
- Reddit API 凭证（免费，Claude 会引导你获取）

## 文档

- [SKILL.md](SKILL.md) - 完整工作流程文档
- [docs/REFERENCE.md](docs/REFERENCE.md) - Reddit 子版块速查表

## License

MIT
