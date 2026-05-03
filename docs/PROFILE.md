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

## 关键词语言识别

- **含中文字符** → 启用中英双轨
- **其他所有情况** → 英文单轨（含日、韩、西等小语种）

## 中英双轨策略（仅中文关键词）

Reddit 中文圈以海外华人为主（r/China_irl、r/saraba1st 等）。

1. 生成 5-7 条中文查询词组
2. 同时生成 5-7 条英文翻译查询词组（贴近 Reddit 用语）
3. 子版块列表必须包含至少一个中文区域子版块和若干英文主流子版块
4. 翻译时避免直译，如「四天工作制」→ `four day workweek`

中文区域子版块：r/China_irl、r/saraba1st、r/real_China_irl、r/Chinatown_irl

## 查询角度模板

### 英语

| 角度 | 查询模板 |
|------|----------|
| 问题导向 | `<keyword> problem`, `<keyword> issue`, `<keyword> hate` |
| 比较导向 | `best <keyword>`, `<keyword> vs`, `alternative to <keyword>` |
| 体验导向 | `<keyword> review`, `tried <keyword>`, `<keyword> after one year` |
| 立场导向 | `<keyword> change my mind`, `unpopular opinion <keyword>`, `<keyword> overrated` |
| 发现导向 | `<keyword> recommendation`, `is <keyword> worth it` |

### 中文

| 角度 | 查询模板 |
|------|----------|
| 问题导向 | `<keyword> 问题`, `<keyword> 缺点`, `<keyword> 坑`, `<keyword> 吐槽` |
| 比较导向 | `<keyword> 推荐`, `<keyword> 对比`, `<keyword> 替代品` |
| 体验导向 | `<keyword> 测评`, `<keyword> 使用感受`, `<keyword> 真实体验` |
| 立场导向 | `<keyword> 争议`, `<keyword> 被高估`, `<keyword> 值不值` |
| 发现导向 | `<keyword> 值得买吗`, `<keyword> 怎么选` |

中文关键词**两套都生成**。

## 子版块推荐

以 `docs/REFERENCE.md` 为起点。始终包含：
- 1-2 个广泛子版块（如 r/AskReddit、r/changemyview）
- 2-4 个垂直主题子版块

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
