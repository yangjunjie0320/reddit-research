# 报告模块库

每个模块是最终报告的一个独立章节。根据关键词画像选 5-8 个模块。始终以 M01 开头、M14 结尾。

---

## M01_one_line

一句话结论。所有报告必选。

---

## M02_pain_point_chart

核心痛点 Top 5，含频次和代表引用。适合：product、service、health_topic。

需要聚合：`claim_frequency`、`quote_pool`。

---

## M03_price_psychology

价格心理区间、天花板、锚定品牌。适合：product、service。

需要聚合：`evidence_pool`（价格类）、`entity_frequency`。

---

## M04_entity_landscape

品牌/替代品声量份额。适合：product、service、controversy。

需要聚合：`entity_frequency`。

---

## M05_opportunity_score

1-10 分机会评分，4 维度拆解。适合：product。

需要聚合：`claim_frequency`、`entity_frequency`、`evidence_pool`。

评分维度：需求真实度、价格空间、竞争烈度（反转）、差异化难度（反转）。

---

## M06_stance_distribution

支持/反对/中立/混合占比。适合：controversy、social_event、policy。

需要聚合：`stance_distribution`。

---

## M07_argument_pairs

各方最强论点对照。适合：controversy、policy。

需要聚合：`claim_frequency`（按 stance 过滤）、`quote_pool`。

---

## M08_quote_wall

6-10 条代表性引用，按情绪分组。适合：cultural_trend、social_event、public_figure。

需要聚合：`quote_pool`。

---

## M09_theme_clusters

前 4-6 个主题聚类。适合：cultural_trend、tech_phenomenon。

需要聚合：`claim_frequency`（聚类到主题层）。

---

## M10_time_evolution

讨论随时间的演变。适合：>= 12 个月数据的关键词。

需要聚合：帖子按季度/半年分组、每期 claim_frequency。

---

## M11_emotion_temperature

情绪分布（均值、中位数、高强度占比）。适合：controversy、social_event、public_figure。

需要聚合：`emotion_histogram`。

---

## M12_credibility_notes

一手/二手/推测来源占比。适合：health_topic、controversy、policy。

需要聚合：`credibility_breakdown`。

---

## M13_action_directions

按 ROI 排序的行动建议。适合：product、service。

需要聚合：全部。

---

## M14_data_appendix

数据透明度附录。所有报告必选，放最后。

内容：关键词、研究意图、覆盖版块、搜索词组数、抓取/过滤/高相关样本数、时间窗口、研究日期、数据局限。

---

## 按分类快速选择

| 分类 | 推荐模块 |
|------|----------|
| product | M01, M02, M03, M04, M05, M13, M14 |
| service | M01, M02, M03, M04, M13, M14 |
| policy | M01, M06, M07, M11, M12, M14 |
| controversy | M01, M06, M07, M08, M11, M12, M14 |
| social_event | M01, M06, M08, M10, M11, M14 |
| public_figure | M01, M04, M08, M11, M12, M14 |
| cultural_trend | M01, M08, M09, M10, M14 |
| tech_phenomenon | M01, M04, M09, M10, M13, M14 |
| health_topic | M01, M02, M09, M11, M12, M14 |
| lifestyle | M01, M08, M09, M10, M14 |
| media_work | M01, M08, M11, M14 |

混合分类时取前两个标签模块的并集，去重后裁剪到 5-8 个。
