# Reddit Research

通过挖掘 Reddit 真实讨论，快速获取产品、话题、趋势的用户洞察。

## 特性

- **智能画像生成** - 自动识别关键词类型，生成研究画像
- **中英双轨** - 中文关键词同时搜索中文和英文社区
- **模块化报告** - 根据话题类型自适应组装报告模块
- **5 阶段流程** - 画像 → 搜索 → 补全 → 过滤 → 分析 → 报告

## 安装

手动克隆到对应的 skills 目录：

| 工具 | 全局安装路径 |
|------|------|
| Claude Code | `~/.claude/skills/reddit-research/` |
| Antigravity | `~/.gemini/antigravity/skills/reddit-research/` |
| Codex CLI | `~/.codex/skills/reddit-research/` |

```bash
# 以 Claude Code 为例，根据实际情况替换 SKILLS_DIR
export SKILLS_DIR="~/.claude/skills/reddit-research/"
git clone https://github.com/yangjunjie0320/reddit-research.git $SKILLS_DIR
```

## 快速开始

安装后，直接告诉 Claude 想研究的关键词：

```
帮我研究 mechanical keyboard
```

首次使用时，Claude 会引导你：
1. 安装 uv 和依赖
2. 获取搜索 API 凭证（Serper 或 Brave）
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
runs/{run_id}/
├── profile.yaml          # 研究画像
├── discovered_posts.jsonl # 搜索发现的帖子 URL
├── hydrated_posts.jsonl   # 补全后的帖子数据
├── filtered_posts.jsonl   # 筛选后的帖子
├── analysis_pack.md       # 分析包
├── analysis.jsonl         # 语义分析结果
├── aggregates.json        # 聚合数据
├── report.md              # 最终报告
└── run_meta.json          # 运行元数据
```

## 项目结构

```
reddit-research/
├── SKILL.md              # 工作流执行指南
├── docs/
│   ├── SETUP.md          # 环境配置指南
│   ├── REFERENCE.md      # 子版块速查表
│   ├── PROFILE.md        # 画像生成规则
│   └── REPORT_MODULES.md # 报告模块库
├── scripts/              # Python 数据管道
├── templates/            # 模板文件
├── examples/             # 示例画像
├── pyproject.toml        # 项目配置
└── uv.lock               # 依赖锁定
```

## 技术栈

- **Python 3.10+** - 脚本语言
- **uv** - 依赖管理
- **Serper / Brave** - Reddit 帖子搜索发现
- **Arctic Shift** - Reddit 帖子数据补全
- **Claude** - LLM 语义分析和报告生成

## 文档

- [SKILL.md](SKILL.md) - 工作流执行指南
- [docs/SETUP.md](docs/SETUP.md) - 环境配置指南
- [docs/REFERENCE.md](docs/REFERENCE.md) - 子版块速查表
- [docs/PROFILE.md](docs/PROFILE.md) - 画像生成规则
- [docs/REPORT_MODULES.md](docs/REPORT_MODULES.md) - 报告模块库

## 依赖

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- 搜索 API 凭证（Serper 或 Brave，免费额度即可）

## License

MIT
