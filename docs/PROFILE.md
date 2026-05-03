# 画像生成详细规则

本文件记录 Stage 1 画像生成的完整规则。SKILL.md 只引用结果，细节在此维护。

## 分类词汇表

多标签分类，权重之和为 1.0：

| 标签 | 含义 |
|------|------|
| `product` | 产品 |
| `service` | 服务 |
| `policy` | 政策 |
| `social_event` | 社会事件 |
| `public_figure` | 公众人物 |
| `cultural_trend` | 文化趋势 |
| `controversy` | 争议 |
| `health_topic` | 健康话题 |
| `tech_phenomenon` | 科技现象 |
| `lifestyle` | 生活方式 |
| `media_work` | 媒体作品 |
| `other` | 其他 |

允许多标签，如 `{product: 0.5, controversy: 0.3, lifestyle: 0.2}`。

## 关键词双语策略

所有关键词均启用双语搜索：

1. 英文关键词翻译为中文，中文关键词翻译为英文
2. 补充 Agent 认为相关的关键词（同义词、近义词、常见变体）
3. 关键词总数不超过 `fetch.max_keywords`（默认 15）
4. 翻译时避免直译，贴近 Reddit 社区用语
5. 关键词直接作为搜索查询词，不再拼接子版块限定

中文关键词时，关键词列表应同时包含中文查询词和英文翻译查询词。
英文关键词时，关键词列表应同时包含英文查询词和中文翻译查询词。

Reddit 中文圈以海外华人为主（r/China_irl、r/saraba1st 等）。

## 子版块推荐

以 `docs/REFERENCE.md` 为起点。始终包含：
- 1-2 个广泛子版块（如 r/AskReddit、r/changemyview）
- 2-4 个垂直主题子版块

注意：`recommended_subreddits` 仅用于分析上下文和报告参考，不用于搜索限定。搜索始终使用 `site:reddit.com`。

## 分析重点 (analysis_emphasis)

从统一 schema 字段中选 3-5 个：`key_claims`、`specific_evidence`、`entities_mentioned`、`stance`、`emotional_tone`、`representative_quote`、`credibility_signals`

## 报告模块选择

从 `docs/REPORT_MODULES.md` 中选 5-8 个模块 ID。M01 在最前，M14 在最后。按分类权重选择中间模块。

## 确认步骤

向用户展示画像，询问：
- 确认并继续
- 调整特定项目
- 添加或删除子版块或查询词

循环直到用户确认。
