---
name: reddit-research
description: 用于研究话题、产品、社会事件、公众人物、政策或文化趋势的技能。通过挖掘 Reddit 真实讨论获取洞察。触发词包括：选品分析、买家痛点研究、舆论分析、sentiment research、opinion mining、niche evaluation、trend analysis、痛点挖掘、市场调研、用户反馈分析。用户提供一个关键词或短语，技能自动生成画像、推荐子版块和查询词、抓取并过滤帖子、进行语义分析，最后组装一份模块化的调研报告。
---

# Reddit 调研

关键词输入，结构化报告输出。用户提供一个关键词，Claude 自动生成画像、运行固定的数据管道，并组装一份根据关键词特性自适应的报告。

## 设计原则

一条管道，柔性适配。抓取和过滤阶段对所有关键词完全相同。第一阶段生成的关键词画像是一个软信号，用于引导分析提示词和报告模块选择。避免硬分类路由，因为大多数真实关键词都是多标签的（一个产品同时也是一个政策议题，一个人物同时也是一个争议话题）。

## 工作流程概览

```
关键词
   │
   ▼
[1] 画像生成         ← LLM 自动分析关键词
   │   产出: profile.yaml
   ▼
[2] Reddit 抓取      ← 脚本，所有关键词通用
   │   产出: raw_posts.jsonl
   ▼
[3] 规则过滤         ← 脚本，所有关键词通用
   │   产出: candidates.jsonl
   ▼
[4] 语义分析         ← LLM，统一 schema，画像感知的侧重点
   │   产出: analysis.jsonl + aggregates
   ▼
[5] 模块化报告组装   ← LLM 根据画像从模块库中选择
       产出: report.md
```

所有产出文件存放在 `research/<slug>/` 目录下。slug 在第一阶段从关键词派生。

## 检查

当用户触发此技能时，Claude 需要先检查环境是否就绪。按以下顺序检查并引导用户完成设置：

### 检查步骤

**1. 检查 uv 是否安装**

```bash
which uv
```

如果未安装，告诉用户：
> uv 尚未安装。请运行以下命令安装：
> ```bash
> curl -LsSf https://astral.sh/uv/install.sh | sh
> ```
> 安装后请重新打开终端或运行 `source ~/.bashrc`

**2. 检查 Python 虚拟环境**

```bash
uv sync
```

如果失败，检查 Python 版本或网络问题。成功后会创建 `.venv/` 目录。

**3. 检查 Reddit API 凭证**

```bash
uv run python scripts/setup_check.py
```

根据输出判断缺失的内容：

- 如果缺少环境变量，引导用户获取凭证
- 如果凭证无效，引导用户检查并重新设置

### 引导用户获取 Reddit API 凭证

当检测到凭证缺失时，向用户说明：

> 需要 Reddit API 凭证才能继续。请按以下步骤操作：
>
> 1. 打开浏览器访问 https://www.reddit.com/prefs/apps
> 2. 滚动到底部，点击 "create another app..." 或 "are you a developer? create an app..."
> 3. 填写表单：
>    - **name**: 随意填写，如 `reddit-research`
>    - **类型**: 选择 **script**（重要！）
>    - **redirect uri**: 填写 `http://localhost:8080`
> 4. 点击 "create app"
> 5. 创建后记录以下信息：
>    - **Client ID**: 在 "personal use script" 下方的字符串
>    - **Client Secret**: 标记为 "secret" 的字符串
>
> 请告诉我你的 Client ID 和 Client Secret，我来帮你设置。

### 保存凭证

用户提供凭证后，帮助用户保存到环境，写入 .env 文件：

创建 `.env` 文件：

```bash
cat > .env << 'EOF'
export REDDIT_CLIENT_ID="用户提供的ID"
export REDDIT_CLIENT_SECRET="用户提供的密钥"
export REDDIT_USER_AGENT="python:reddit-research:v1.0 (by /u/anonymous)"
EOF
```

然后加载：

```bash
source .env
```

### 验证设置

设置完成后，再次运行检查：

```bash
uv run python scripts/setup_check.py
```

看到 "All checks passed" 表示设置成功，可以开始研究。

### 设置完成后

告诉用户：
> 设置完成！现在你可以告诉我想研究的关键词了。
> 例如：
> - "帮我研究 mechanical keyboard"
> - "分析一下四天工作制的舆论"
> - "调研 Stanley cup 的用户痛点"

## 第一阶段：画像生成

如果用户尚未提供关键词，先询问。然后通过推理生成画像 YAML，保存到 `research/<slug>/profile.yaml`。使用 `templates/profile_template.yaml` 作为结构模板。

画像包含七个部分：

1. **slug**：从关键词派生的 kebab-case 标识符。
2. **categorization**：多标签分类，权重之和为 1.0。标签词汇表：`product`（产品）、`service`（服务）、`policy`（政策）、`social_event`（社会事件）、`public_figure`（公众人物）、`cultural_trend`（文化趋势）、`controversy`（争议）、`health_topic`（健康话题）、`tech_phenomenon`（科技现象）、`lifestyle`（生活方式）、`media_work`（媒体作品）、`other`（其他）。允许多标签，如 `{product: 0.5, controversy: 0.3, lifestyle: 0.2}`。
3. **research_intent**：一句话推测用户想要获得的决策或洞察。继续之前需与用户确认。
4. **recommended_subreddits**：4 到 8 个子版块。以 `docs/REFERENCE.md` 为起点。始终包含 1-2 个广泛子版块（如 r/AskReddit、r/changemyview）和 2-4 个垂直主题子版块。
5. **keyword_groups**：6 到 10 个搜索查询词组。按分类权重比例混合下列角度。
6. **analysis_emphasis**：统一 schema 中哪些字段需要重点关注。见第四阶段。
7. **report_modules**：从 `templates/report_modules.md` 中选择 5-8 个模块 ID，用于第五阶段组装。

### 关键词语言识别

本技能只区分两种情况：

* **含中文字符** → 视为中文关键词，启用中英双轨
* **其他所有情况** → 视为英文关键词，单轨

非中文的小语种关键词（日、韩、西、德、法等）一律按英文处理：直接使用关键词原文搜索，不做翻译。Reddit 上这些语言的讨论密度有限，专门支持的工程成本不划算。

### 中英双轨策略（仅中文关键词）

Reddit 主流是英文社区，中文圈以海外华人为主（r/China_irl、r/saraba1st 等）。若用户输入中文关键词：

1. 生成 5-7 条中文查询词组（命中中文区域社区）
2. 同时生成 5-7 条英文翻译查询词组（命中主流英文社区）
3. 子版块列表必须同时包含至少一个中文区域子版块和若干英文主流子版块
4. 翻译时贴近 Reddit 用户实际用词，避免直译。如「四天工作制」译为 `four day workweek` 而非 `four-day work system`

### 关键词组角度（中英双语模板）

#### 英语 (English)

| 角度 | 查询模板 |
|------|----------|
| 问题导向 | `<keyword> problem`, `<keyword> broken`, `<keyword> issue`, `<keyword> hate`, `<keyword> sucks` |
| 比较导向 | `best <keyword>`, `<keyword> vs`, `alternative to <keyword>`, `<keyword> competitor` |
| 体验导向 | `<keyword> review`, `tried <keyword>`, `<keyword> after one year`, `<keyword> experience` |
| 立场导向 | `<keyword> change my mind`, `unpopular opinion <keyword>`, `<keyword> overrated`, `<keyword> underrated` |
| 发现导向 | `<keyword> recommendation`, `is <keyword> worth it`, `should I buy <keyword>` |

#### 中文 (Chinese)

| 角度 | 查询模板 |
|------|----------|
| 问题导向 | `<keyword> 问题`, `<keyword> 缺点`, `<keyword> 坑`, `<keyword> 吐槽`, `<keyword> 踩雷` |
| 比较导向 | `<keyword> 推荐`, `<keyword> 对比`, `<keyword> 替代品`, `<keyword> 哪个好` |
| 体验导向 | `<keyword> 测评`, `<keyword> 使用感受`, `<keyword> 一年后`, `<keyword> 真实体验` |
| 立场导向 | `<keyword> 争议`, `<keyword> 被高估`, `<keyword> 真的好吗`, `<keyword> 值不值` |
| 发现导向 | `<keyword> 值得买吗`, `<keyword> 怎么选`, `<keyword> 入门` |

中文关键词记得**两套都生成**：先按中文模板出 5-7 条，再把关键词翻译成英文（贴近 Reddit 用语），按英文模板再出 5-7 条。

### 中文子版块

中文关键词必须额外加至少 1 个中文区域子版块：
- r/China_irl
- r/saraba1st
- r/real_China_irl
- r/Chinatown_irl

### 确认步骤

向用户展示生成的画像。显示分类权重、研究意图、子版块列表和关键词组列表。询问用户：

* 确认并继续
* 调整特定项目（用户指出）
* 添加或删除子版块或查询词

循环直到用户确认。

## 第二阶段：Reddit 抓取

验证 Reddit API 凭证：

```bash
python scripts/setup_check.py
```

如果凭证缺失，指导用户在 https://www.reddit.com/prefs/apps 创建一个 script 类型的应用，然后导出 `REDDIT_CLIENT_ID`、`REDDIT_CLIENT_SECRET`、`REDDIT_USER_AGENT`。

然后抓取：

```bash
python scripts/fetch_reddit.py --profile research/<slug>/profile.yaml
```

输出：`research/<slug>/raw_posts.jsonl`。每行是一个帖子，包含元数据和前几条评论。

抓取器与画像无关。它只读取画像中的子版块列表、关键词组、posts_per_keyword、comments_per_post 和 time_filter。支持断点续传；重新运行会跳过已保存的帖子 ID。

典型产出：80 到 200 个帖子。

## 第三阶段：规则过滤

```bash
python scripts/filter_posts.py --profile research/<slug>/profile.yaml --input research/<slug>/raw_posts.jsonl --output research/<slug>/candidates.jsonl
```

The `--profile` flag reads `filter_overrides` from the profile YAML. Explicit CLI flags (e.g. `--min-score 10`) take highest priority over profile overrides, which in turn override built-in defaults.

默认规则（如需可通过参数覆盖）：

* `score >= 5`
* `num_comments >= 3`
* 正文长度 >= 100 字符 或 首条评论长度 >= 200 字符
* 发布于最近 24 个月内
* 非置顶、未锁定、未删除
* 非纯链接帖，除非有实质性评论

典型产出：20 到 40 个候选帖子。

## 第四阶段：语义分析

直接读取 `candidates.jsonl`。对每个候选帖子自行分析，无需外部 API 调用。
**注意**：如果候选帖子数量较多（例如超过 15 个）且包含大量长评论，请**分批处理**（例如每批 10-15 个帖子）并多次追加写入 `analysis.jsonl`，以防止单次输出触发最大 Token 限制导致分析被截断。

使用 `templates/analysis_schema.json` 中的统一 schema。每条记录具有相同字段。profile.analysis_emphasis 告诉你哪些字段需要重点关注。其他字段在不适用时可留空或设为 null。

统一 schema 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| post_id | string | Reddit 帖子 ID |
| relevance_score | int 0-10 | 低于 6 则丢弃 |
| key_claims | 字符串列表 | 核心观点、抱怨、观察或论点。用动词+宾语形式表达。 |
| specific_evidence | 字符串列表 | 数字、日期、轶事、价格、时长等具体信息 |
| entities_mentioned | 字符串列表 | 品牌、产品、人物、组织、地点、替代品 |
| stance | 枚举或 null | `for`（支持）、`against`（反对）、`neutral`（中立）、`mixed`（混合）、`null`。无隐含立场时用 null。 |
| emotional_tone | int 0-10 | 0 为冷静/分析性，10 为愤怒/狂喜 |
| representative_quote | string | 原文引用，15 词以内。每帖一条。 |
| credibility_signals | 字符串列表 | 如 `claims_owner`（声称是用户）、`posted_photo`（发了照片）、`secondhand`（二手信息）、`speculation`（推测）、`professional_in_field`（专业人士） |

阅读 `templates/analysis_prompt.md` 中的提示词框架，在推理时注入用户画像的 profile.analysis_emphasis。

将保留的记录（relevance >= 6）保存到 `research/<slug>/analysis.jsonl`。

然后聚合。根据选定的报告模块需要构建以下聚合数据，跳过不需要的：

* **claim_frequency**：聚类近似的 `key_claims` 并计数。取前 15。
* **entity_frequency**：统计 `entities_mentioned`，降序排列。取前 15。
* **stance_distribution**：支持/反对/中立/混合的百分比（仅当 >= 50% 的记录有 stance 值时）。
* **evidence_pool**：展平 `specific_evidence`。按类型（价格、时间、数量、轶事）分组（如有规律）。
* **emotion_histogram**：`emotional_tone` 分数分布。
* **quote_pool**：所有 `representative_quote`，配对 stance 和 emotional_tone 以便后续筛选。
* **credibility_breakdown**：一手/二手/推测帖子各占多少。

将聚合数据保存到 `research/<slug>/aggregates.json`。

## 第五阶段：模块化报告组装

阅读 `templates/report_modules.md`。它定义了一个报告模块库，每个模块有 ID、用途、输入需求（需要哪些聚合数据）和格式示例。

使用 profile.yaml 中的 `report_modules` 列表作为组装顺序。如果画像选择的模块所需的聚合数据缺失或稀疏，要么现在计算缺失的聚合，要么替换为相关模块。

标准模块 ID：

| ID | 用途 | 最适合 |
| --- | --- | --- |
| M01_one_line | 一句话结论 | 所有报告 |
| M02_pain_point_chart | 热门抱怨及频率和引用 | 产品、服务 |
| M03_price_psychology | 价格天花板、地板、锚定品牌 | 产品、服务 |
| M04_entity_landscape | 提及的品牌或替代品，声量份额 | 产品、服务、争议 |
| M05_opportunity_score | 1-10 分，含 4 个维度拆解 | 产品 |
| M06_stance_distribution | 支持/反对/中立饼图 | 争议、社会事件、政策 |
| M07_argument_pairs | 各方最强论点 | 争议、政策 |
| M08_quote_wall | 6-10 条代表性引用，分组展示 | 文化趋势、社会事件、公众人物 |
| M09_theme_clusters | 前 4-6 个主题性论点聚类 | 文化趋势、科技现象 |
| M10_time_evolution | 讨论在时间窗口内的演变 | 任何 >= 12 个月数据的情况 |
| M11_emotion_temperature | 情绪分布图及解读 | 争议、社会事件 |
| M12_credibility_notes | 一手 vs 二手来源比例，可信度说明 | 健康话题、争议 |
| M13_action_directions | 按 ROI 优先级排列的具体下一步行动 | 产品、服务 |
| M14_data_appendix | 子版块、查询词、帖子数量 | 所有报告 |

始终将 M01 放在最前，M14 放在最后。根据画像从中间选择 3-6 个模块。

将组装好的报告写入 `research/<slug>/report.md`。然后向用户内联展示。提供后续选项：

* 深入某个特定论点或实体
* 用不同的模块集重新组装报告（无需重新抓取）
* 与相关关键词对比
* 导出引用用于幻灯片或标注

## 输出规范

* 报告默认使用用户的语言（如果关键词是中文则用中文，否则用英文）。
* Reddit 引用保持在 15 词以内，以尊重版权。
* 报告中剥离所有 Reddit 用户名。用"一位用户"或"多位用户"指代评论者。
* 数字合理四舍五入；不要凭空增加数据不支持的精度。

## 常见失败模式

* **数据稀疏**：如果第三阶段产出少于 10 个候选帖子，先扩大时间窗口，再增加子版块，最后放宽分数和长度阈值。在报告的数据附录中说明这一限制。
* **离题噪音**：如果第四阶段很多记录得分低于 6，说明关键词组太宽泛。用引号包裹关键词或添加限定词来收紧查询。
* **单一子版块主导**：如果超过 60% 的候选帖子来自同一个子版块，扩大推荐子版块列表并重新抓取代表性不足的子版块。
* **抱团帖子**：如果争议报告显示极端的立场两极化且情绪分数很高，在 M11 中标记这一点，将其视为信号而非真相。
* **中文关键词命中率低**：如果中文查询命中很少，说明该话题在 Reddit 中文圈讨论稀疏。把更多权重放到英文查询词组上，并在报告中说明：本报告主要反映英文圈讨论。
* **中文圈样本偏差**：Reddit 中文社区以海外华人为主，他们的视角与国内用户存在系统性差异。如果研究目标是国内人群，Reddit 中文样本只能作为参考，结论应配合微博、小红书、知乎等平台数据交叉验证。在报告 M14 数据附录中明确标注此限制。

## 本技能包含的文件

* `SKILL.md`（本文件）：工作流程指南
* `SETUP.md`：环境配置一次性指南，仅在 setup_check.py 失败时阅读
* `docs/REFERENCE.md`：按主题分类的子版块速查表
* `scripts/setup_check.py`：环境和凭证检查脚本
* `scripts/fetch_reddit.py`：Reddit 抓取器
* `scripts/filter_posts.py`：规则过滤器
* `templates/profile_template.yaml`：画像 YAML 结构
* `templates/analysis_schema.json`：统一分析记录 schema
* `templates/analysis_prompt.md`：分析提示词框架
* `templates/report_modules.md`：模块库
* `examples/`：示例画像
