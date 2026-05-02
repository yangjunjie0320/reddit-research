# Report Module Library

Each module is a self contained section of the final report. Pick 5 to 8 modules based on the keyword profile. Always start with M01 and end with M14.

The report shape adapts to the keyword by selecting different modules; the modules themselves are stable.

---

## M01_one_line

**Purpose**: A single sentence conclusion that the rest of the report supports.

**Required aggregates**: All. Read everything before writing.

**Format**:

```markdown
## 一句话结论

A single sentence that captures the strongest finding. No hedging, no preamble.
```

**Example**:

```
## 一句话结论
四天工作制在 Reddit 上的真实讨论里支持率约 7 比 3，但反对方的论据更具体、更难反驳，主要集中在客户响应延迟和小企业现金流。
```

---

## M02_pain_point_chart

**Purpose**: Top complaints with frequency and a representative quote.

**Required aggregates**: `claim_frequency`, `quote_pool`.

**Best for**: product, service, health_topic.

**Format**:

```markdown
## 核心痛点 Top 5

| 排名 | 痛点 | 提及频次 | 代表原话 |
| --- | --- | --- | --- |
| 1 | <claim cluster label> | N posts | <under 15 word quote> |
| 2 | ... | ... | ... |

简短的解读段落：哪些痛点出乎意料，哪些与常识一致。
```

---

## M03_price_psychology

**Purpose**: Price ceiling, floor, and anchor brands. Surfaces what users will and will not pay.

**Required aggregates**: `evidence_pool` (filtered to price mentions), `entity_frequency`.

**Best for**: product, service.

**Format**:

```markdown
## 价格心理区间

* **心理价位**: $X to $Y (based on N price mentions)
* **价格天花板**: 高于 $Z 时频繁出现拒绝信号
* **锚定品牌**: <Brand A> at $X, <Brand B> at $Y

简短解读：是否存在价格断层，是否有溢价空间。
```

---

## M04_entity_landscape

**Purpose**: Brands, alternatives, or named players, with share of voice.

**Required aggregates**: `entity_frequency`.

**Best for**: product, service, controversy.

**Format**:

```markdown
## 实体格局 / 竞品格局

| 实体 | 提及次数 | 主导情绪 | 主要场景 |
| --- | --- | --- | --- |
| <Entity> | N | positive / mixed / negative | what context they show up in |

简短解读：谁占据心智高地，谁是挑战者，谁是被嘲讽的对象。
```

---

## M05_opportunity_score

**Purpose**: 1 to 10 score with four dimension breakdown. Specific to product evaluation.

**Required aggregates**: `claim_frequency`, `entity_frequency`, `evidence_pool`.

**Best for**: product.

**Format**:

```markdown
## 机会评分: N/10

| 维度 | 评分 | 理由 |
| --- | --- | --- |
| 需求真实度 | N/10 | based on volume and specificity of pain points |
| 价格空间 | N/10 | based on ceiling vs current market |
| 竞争烈度 | N/10 | inverted: 10 means weak competition |
| 差异化难度 | N/10 | inverted: 10 means easy to differentiate |

综合判断段落：进入是否值得，关键风险是什么。

评分参考标尺：
9 to 10 强需求加清晰价格空间加弱竞争加易差异化
7 to 8 强需求加适度空间加部分竞争加可识别差异
5 to 6 真实需求但已商品化或竞争激烈 (大多数品类落在这里)
3 to 4 需求弱或市场饱和
1 to 2 没有真正机会
```

---

## M06_stance_distribution

**Purpose**: For / against / neutral / mixed proportion across the dataset.

**Required aggregates**: `stance_distribution`.

**Best for**: controversy, social_event, policy.

**Format**:

```markdown
## 立场分布

* 支持: X% (N posts)
* 反对: Y% (N posts)
* 中立: Z% (N posts)
* 复杂态度: W% (N posts)

(说明本次研究在 N 个样本上有效统计了立场，未能判定立场的 M 个样本已剔除)

简短解读：是否一边倒，是否存在沉默多数，按 subreddit 分组后分布如何变化。
```

---

## M07_argument_pairs

**Purpose**: Strongest argument from each side, paired for comparison.

**Required aggregates**: `claim_frequency` filtered by stance, `quote_pool` filtered by stance.

**Best for**: controversy, policy.

**Format**:

```markdown
## 核心论点对照

### 支持方最有力的三个论点
1. **<argument label>**: <one paragraph elaboration with specifics from the data>
   原话: <under 15 word quote>
2. ...
3. ...

### 反对方最有力的三个论点
1. **<argument label>**: ...
   原话: ...
2. ...
3. ...

简短解读：两边是否在同一个层面交锋，还是在自说自话。
```

---

## M08_quote_wall

**Purpose**: 6 to 10 representative voices, grouped by mood or theme.

**Required aggregates**: `quote_pool`.

**Best for**: cultural_trend, social_event, public_figure.

**Format**:

```markdown
## 真实声音

### 兴奋 / 拥护
> <quote, under 15 words>
> <quote, under 15 words>

### 失望 / 警惕
> <quote>
> <quote>

### 困惑 / 中间态度
> <quote>
> <quote>

(共 N 条，全部来自 relevance >= 6 的高质量讨论)
```

---

## M09_theme_clusters

**Purpose**: Top 4 to 6 thematic clusters of claims, each with description and example.

**Required aggregates**: `claim_frequency` clustered into themes (one level above raw claims).

**Best for**: cultural_trend, tech_phenomenon.

**Format**:

```markdown
## 主题聚类

### 主题 1: <theme label> (N% of relevant posts)
本主题下用户主要在讨论 ... 。代表性表述包括 <claim>、<claim>。
代表原话: <under 15 word quote>

### 主题 2: <theme label> (N% of relevant posts)
...
```

---

## M10_time_evolution

**Purpose**: How discussion shifted across the time window.

**Required aggregates**: posts grouped by quarter or half year, claim_frequency per period.

**Best for**: keywords with at least 12 months of data.

**Format**:

```markdown
## 时间演变

| 时段 | 讨论密度 | 主导主题 | 显著变化 |
| --- | --- | --- | --- |
| 2024 H1 | low | <theme> | (baseline) |
| 2024 H2 | medium | <theme> | new entity X enters discussion |
| 2025 H1 | high | <theme> | tone shifts from curiosity to skepticism |

简短解读：是否存在拐点事件，讨论是否还在升温或已经降温。
```

---

## M11_emotion_temperature

**Purpose**: Emotion distribution across the dataset.

**Required aggregates**: `emotion_histogram`.

**Best for**: controversy, social_event, public_figure.

**Format**:

```markdown
## 情绪温度

* 平均强度: X.X / 10
* 中位数: X / 10
* 高强度 (>= 7) 占比: Y%

分布特点：是否双峰 (强支持加强反对)，是否长尾 (大多数中性，少数极端)。

可能的解读：本话题的情绪表达是否被算法或情感化叙事放大。
```

---

## M12_credibility_notes

**Purpose**: Firsthand vs secondhand vs speculative breakdown, plus what to trust.

**Required aggregates**: `credibility_breakdown`.

**Best for**: health_topic, controversy, policy.

**Format**:

```markdown
## 可信度提示

* 第一手经验占比: X% (claims_owner 或 claims_user)
* 二手转述占比: Y% (secondhand)
* 推测或假设占比: Z% (speculation)
* 有照片或外链证据的样本数: N

阅读建议：本报告中的结论应主要基于第一手样本；标注为推测的部分仅作参考。
```

---

## M13_action_directions

**Purpose**: Concrete next steps the user can take, prioritized by ROI.

**Required aggregates**: All.

**Best for**: product, service. Optional for policy or trend if user wants strategy advice.

**Format**:

```markdown
## 改良方向 / 行动建议

| 优先级 | 行动 | 解决的痛点 | 成本估计 | 差异化潜力 |
| --- | --- | --- | --- | --- |
| 高 | <action> | <pain point> | low / mid / high | low / mid / high |

简短解读：哪一个行动是性价比最高的入场点，哪一个是长期布局。
```

---

## M14_data_appendix

**Purpose**: Transparency. Always last.

**Required aggregates**: counts from each pipeline stage.

**Best for**: all reports.

**Format**:

```markdown
## 本次研究数据

* 关键词: <keyword>
* 研究意图: <one line from profile.research_intent>
* 覆盖版块: r/<sub1>、r/<sub2>、...
* 搜索关键词组: N 组
* 抓取帖子: N 个
* 通过过滤: N 个
* 高相关样本 (relevance >= 6): N 个
* 时间窗口: <earliest date> 到 <latest date>
* 研究日期: <today>

数据局限：本研究只覆盖 Reddit 英文社区。中文 / 西语 / 日语等社区未纳入；不代表全网舆论。
```

---

## Module Selection Heuristics

By categorization weight (top tag):

* **product**: M01, M02, M03, M04, M05, M13, M14
* **service**: M01, M02, M03, M04, M13, M14
* **policy**: M01, M06, M07, M11, M12, M14
* **controversy**: M01, M06, M07, M08, M11, M12, M14
* **social_event**: M01, M06, M08, M10, M11, M14
* **public_figure**: M01, M04, M08, M11, M12, M14
* **cultural_trend**: M01, M08, M09, M10, M14
* **tech_phenomenon**: M01, M04, M09, M10, M13, M14
* **health_topic**: M01, M02, M09, M11, M12, M14
* **lifestyle**: M01, M08, M09, M10, M14
* **media_work**: M01, M08, M11, M14

For mixed categorization, take the union of the top two tag lists, deduplicate, then trim to 5 to 8 modules using the relative weights as a guide. Always keep M01 first and M14 last.
