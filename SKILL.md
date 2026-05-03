---
name: reddit-research
description: 用于研究话题、产品、社会事件、公众人物、政策或文化趋势的技能。通过挖掘 Reddit 真实讨论获取洞察。触发词包括：选品分析、买家痛点研究、舆论分析、sentiment research、opinion mining、niche evaluation、trend analysis、痛点挖掘、市场调研、用户反馈分析。用户提供一个关键词或短语，技能自动生成画像、推荐子版块和查询词、抓取并过滤帖子、进行语义分析，最后组装一份模块化的调研报告。
---

# Reddit 调研

关键词输入，结构化报告输出。

## 工作流程

```
关键词 → [1] 画像 → [2] 搜索 → [3] 补全 → [4] 过滤 → [5] 分析包 → [6] 语义分析 → [7] 报告
```

所有产出文件存放在 `runs/{run_id}/` 目录下。

## 检查

触发技能时先验证环境：

```bash
uv run python scripts/setup_check.py
```

未通过时按提示操作。凭证缺失时引导用户运行：

```bash
uv run python scripts/save_credentials.py
```

详细环境配置步骤见 `docs/SETUP.md`。

## 第一阶段：画像生成

通过推理生成画像 YAML，保存到 `runs/{run_id}/profile.yaml`。

画像结构模板见 `templates/profile_template.yaml`，包含：
- `slug`：kebab-case 标识符
- `categorization`：多标签分类（权重之和 1.0）
- `research_intent`：一句话研究意图，需与用户确认
- `keyword_groups`：搜索关键词（包含原文、译文和补充词，强制在遇到容易产生歧义的词时自动追加否定词（如 `-dealership`），不超过 `fetch.max_keywords`）
- `analysis_emphasis`：统一 schema 中重点关注的字段
- `report_modules`：报告模块 ID 列表（参考 `docs/REPORT_MODULES.md`）
- `fetch`：抓取参数（`max_keywords`、`posts_per_keyword`、`comments_per_post`、`time_filter`）
- `discovery`：搜索发现参数（`max_results`，默认 200）
- `filter_overrides`：过滤阈值覆盖

画像生成的详细规则（双语策略、分类词汇表）见 `docs/PROFILE.md`。

生成后向用户展示并确认，循环直到用户满意。

## 第二阶段：搜索发现

```bash
uv run python scripts/search_client.py --run runs/{run_id}
```

产出：`discovered_posts.jsonl`。每行包含 url、post_id、subreddit、title、snippet、source、query、rank。

## 第三阶段：数据补全

```bash
uv run python scripts/fetch_reddit.py --run runs/{run_id}
```

产出：`hydrated_posts.jsonl` + `run_meta.json`。每行包含完整帖子数据和 top comments。支持断点续传。

## 第四阶段：规则过滤

```bash
uv run python scripts/filter_posts.py --run runs/{run_id}
```

产出：`filtered_posts.jsonl`。默认规则：score >= 5, comments >= 3, 正文 >= 100 字符或首评论 >= 200 字符, 24 个月内, 非置顶/未锁定。

## 第五阶段：生成分析包

```bash
uv run python scripts/build_analysis_pack.py --run runs/{run_id}
```

产出：`analysis_pack.md`。将过滤后的帖子和 profile 上下文组装为一个 Markdown 文件，供下一步语义分析使用。

## 第六阶段：语义分析

直接阅读 `analysis_pack.md`，对每个帖子分析。使用 `templates/analysis_schema.json` 中的统一 schema。分析流程详见 `templates/analysis_prompt.md`。

产出保存到 `runs/{run_id}/analysis.jsonl`（relevance >= 6 的记录）和 `runs/{run_id}/aggregates.json`。

帖子较多时分批处理（每批 10-15 个），防止输出截断。

## 第七阶段：模块化报告

从 `docs/REPORT_MODULES.md` 的模块库中，按 profile.report_modules 列表组装报告。始终以 M01 开头，并以 M14、M15、M16 结尾。

产出：`runs/{run_id}/report.md`。向用户内联展示。

## 输出规范

- 报告语言跟随关键词语言
- 论述观点时必须列出相关原帖的超链接作为依据
- Reddit 引用不超过 15 词，加入原文的超链接
- 剥离所有 Reddit 用户名
- 报告末尾必须包含：M15 值得阅读的帖子（Featured Posts）和 M16 活跃的子版块（Active Subreddits）
- 数字合理四舍五入

## 常见失败模式

- **数据稀疏**（< 10 候选）：扩大时间窗口 → 增加子版块 → 放宽阈值
- **离题噪音**（大量低相关）：收紧查询词
- **单一子版块主导**（> 60%）：扩大子版块列表并补充抓取
- **中文命中率低**：加重英文查询权重，报告中说明

## 本技能包含的文件

- `SKILL.md`（本文件）：执行指南
- `docs/SETUP.md`：环境配置
- `docs/REFERENCE.md`：子版块速查表
- `docs/PROFILE.md`：画像生成详细规则
- `docs/REPORT_MODULES.md`：报告模块库
- `scripts/`：Python 数据管道脚本
- `templates/`：画像模板、分析 schema、分析提示词
- `examples/`：示例画像
