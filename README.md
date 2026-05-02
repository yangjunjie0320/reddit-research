# Reddit Research

通过挖掘 Reddit 真实讨论，快速获取产品、话题、趋势的用户洞察。

## 特性

- 🔍 **智能画像生成** - 自动识别关键词类型，生成研究画像
- 🌐 **中英双轨** - 中文关键词同时搜索中文和英文社区
- 📊 **模块化报告** - 根据话题类型自适应组装报告模块
- 🎯 **5 阶段流程** - 画像 → 抓取 → 过滤 → 分析 → 报告

## 安装

让你的 agent 安装这个技能：

```
请帮我安装 https://github.com/yangjunjie0320/reddit-research.git
```

## 快速开始

安装后，直接告诉 Claude 想研究的关键词：

```
帮我研究 mechanical keyboard
```

首次使用时，Claude 会引导你：
1. 安装 uv 和依赖
2. 获取 Reddit API 凭证
3. 验证环境

## 使用示例

| 关键词 | 类型 |
|--------|------|
| `mechanical keyboard` | 产品调研 |
| `四天工作制` | 政策/社会话题（中英双轨） |
| `Stanley cup` | 产品痛点挖掘 |
| `AI companion` | 趋势分析 |

## 输出示例

```
research/mechanical-keyboard/
├── profile.yaml          # 研究画像
├── raw_posts.jsonl       # 原始帖子
├── candidates.jsonl      # 筛选后的帖子
├── analysis.jsonl        # 语义分析结果
├── aggregates.json       # 聚合数据
└── report.md             # 最终报告
```

## 项目结构

```
reddit-research/
├── .claude-plugin/
│   └── plugin.json       # 插件清单
├── SKILL.md              # 完整工作流文档
├── docs/
│   ├── SETUP.md          # 环境配置指南
│   └── REFERENCE.md      # 子版块速查表
├── scripts/              # Python 脚本
├── templates/            # 模板文件
├── examples/             # 示例画像
├── pyproject.toml        # 项目配置
└── uv.lock               # 依赖锁定
```

## 技术栈

- **Python 3.10+** - 脚本语言
- **uv** - 依赖管理
- **PRAW** - Reddit API 客户端
- **Claude** - LLM 语义分析和报告生成

## 文档

- [SKILL.md](SKILL.md) - 完整工作流文档
- [docs/SETUP.md](docs/SETUP.md) - 环境配置指南
- [docs/REFERENCE.md](docs/REFERENCE.md) - 子版块速查表

## 依赖

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Reddit API 凭证（免费）

## License

MIT
