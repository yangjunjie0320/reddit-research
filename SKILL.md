---
name: reddit-research
description: Use this skill when the user wants to research a topic, product, social event, public figure, policy, or cultural trend by mining real discussions on Reddit. Trigger on any keyword based research request, including 选品分析, 买家痛点研究, 舆论分析, sentiment research, opinion mining, niche evaluation, trend analysis, 痛点挖掘. The user provides a single keyword or short phrase. The skill auto profiles the keyword, recommends subreddits and queries, fetches and filters posts, performs semantic analysis with a unified schema, and assembles a modular memo report whose shape adapts to the keyword.
---

# Reddit Research

A keyword in, structured memo out workflow. The user supplies one keyword. Claude profiles the keyword, runs a fixed data pipeline, and assembles a report whose modules adapt to whatever the keyword turned out to be.

## Design Principle

One pipeline, soft adaptation. The fetch and filter stages are identical for every keyword. The keyword profile, generated in Stage 1, is a soft signal that biases the analysis prompt and the report module selection. Hard category routing is avoided because most real keywords are multi label (a product is also a policy, a person is also a controversy).

## Workflow at a Glance

```
keyword
   │
   ▼
[1] Profile generation         ← LLM auto profiles the keyword
   │   produces: profile.yaml
   ▼
[2] Reddit fetch                ← script, identical for all keywords
   │   produces: raw_posts.jsonl
   ▼
[3] Rule based filter           ← script, identical for all keywords
   │   produces: candidates.jsonl
   ▼
[4] Semantic analysis           ← LLM, unified schema, profile aware emphasis
   │   produces: analysis.jsonl + aggregates
   ▼
[5] Modular report assembly     ← LLM picks modules from library based on profile
       produces: report.md
```

All artifacts live under `research/<slug>/`. The slug is derived from the keyword in Stage 1.

## Stage 1: Profile Generation

Ask the user for the keyword if not yet provided. Then generate a profile YAML by reasoning over the keyword. Save to `research/<slug>/profile.yaml`. Use `templates/profile_template.yaml` as the structure.

The profile contains seven blocks:

1. **slug**: kebab case identifier derived from the keyword.
2. **categorization**: multi label tags with weights summing to 1.0. Tag vocabulary: `product`, `service`, `policy`, `social_event`, `public_figure`, `cultural_trend`, `controversy`, `health_topic`, `tech_phenomenon`, `lifestyle`, `media_work`, `other`. Multiple tags allowed, e.g. `{product: 0.5, controversy: 0.3, lifestyle: 0.2}`.
3. **research_intent**: one sentence inferred guess at what decision or insight the user is after. Confirm with the user before proceeding.
4. **recommended_subreddits**: 4 to 8 subreddits. Use REFERENCE.md as a starting point. Always include 1 to 2 broad subreddits (e.g. r/AskReddit, r/changemyview) and 2 to 4 narrow topical ones.
5. **keyword_groups**: 6 to 10 search queries. Mix the angles below in proportion to the categorization weights.
6. **analysis_emphasis**: which fields in the unified schema deserve extra attention. See Stage 4.
7. **report_modules**: 5 to 8 module IDs from `templates/report_modules.md` to assemble in Stage 5.

### Keyword group angles

* **Problem oriented**: `<keyword> problem`, `<keyword> broken`, `<keyword> issue`, `<keyword> hate`
* **Comparison oriented**: `best <keyword>`, `<keyword> vs <alternative>`, `alternative to <keyword>`
* **Experience oriented**: `<keyword> review`, `tried <keyword>`, `<keyword> after one year`
* **Stance oriented**: `<keyword> change my mind`, `unpopular opinion <keyword>`, `<keyword> overrated`
* **Discovery oriented**: `<keyword> recommendation`, `is <keyword> worth it`

For a product heavy keyword, weight problem and comparison angles. For a controversy heavy keyword, weight stance angles. For a cultural trend, weight experience and discovery angles.

### Confirmation step

Present the generated profile to the user. Show categorization weights, research intent, subreddit list, and keyword group list. Ask for one of:

* Confirm and proceed
* Adjust specific items (user names them)
* Add or remove subreddits or queries

Iterate until the user confirms.

## Stage 2: Reddit Fetch

Verify Reddit API credentials:

```bash
python scripts/setup_check.py
```

If credentials are missing, instruct the user to create a script type app at https://www.reddit.com/prefs/apps and export `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`.

Then fetch:

```bash
python scripts/fetch_reddit.py --profile research/<slug>/profile.yaml
```

Output: `research/<slug>/raw_posts.jsonl`. Each line is one post, with metadata and top comments inline.

The fetcher is profile agnostic. It reads only the subreddit list, keyword groups, posts_per_keyword, comments_per_post, and time_filter from the profile. Resume safe; rerunning skips post IDs already saved.

Typical yield: 80 to 200 posts.

## Stage 3: Rule Based Filter

```bash
python scripts/filter_posts.py --input research/<slug>/raw_posts.jsonl --output research/<slug>/candidates.jsonl
```

Default rules (override via flags if needed):

* `score >= 5`
* `num_comments >= 3`
* selftext length >= 100 chars OR top comment length >= 200 chars
* posted within the last 24 months
* not stickied, locked, or removed
* not a pure link post unless it has substantive comments

Typical yield: 20 to 40 candidates.

## Stage 4: Semantic Analysis

Read `candidates.jsonl` directly. For each candidate, do the analysis yourself, no external API call.

Use the unified schema in `templates/analysis_schema.json`. Every record has the same fields. The profile.analysis_emphasis tells you where to spend effort. Other fields can be left as null or empty arrays when not applicable.

Unified schema fields:

| Field | Type | Notes |
| --- | --- | --- |
| post_id | string | Reddit post ID |
| relevance_score | int 0 to 10 | Discard if below 6 |
| key_claims | list of strings | Core opinions, complaints, observations, or arguments. Phrase as verb plus object. |
| specific_evidence | list of strings | Numbers, dates, anecdotes, prices, durations, anything concrete |
| entities_mentioned | list of strings | Brands, products, people, organizations, places, alternatives |
| stance | enum or null | One of `for`, `against`, `neutral`, `mixed`, `null`. Use null when there is no implicit position to take. |
| emotional_tone | int 0 to 10 | 0 calm or analytical, 10 furious or euphoric |
| representative_quote | string | Verbatim, under 15 words. One per post. |
| credibility_signals | list of strings | E.g. `claims_owner`, `posted_photo`, `secondhand`, `speculation`, `professional_in_field` |

Read the prompt framing in `templates/analysis_prompt.md` and inject the profile.analysis_emphasis from the user's profile when reasoning.

Save kept records (relevance >= 6) to `research/<slug>/analysis.jsonl`.

Then aggregate. Build whichever of these aggregates the chosen report modules need; skip the rest:

* **claim_frequency**: cluster near duplicate `key_claims` and count. Top 15.
* **entity_frequency**: count `entities_mentioned`, sorted desc. Top 15.
* **stance_distribution**: percent for / against / neutral / mixed (only if stance is populated for >= 50% of records).
* **evidence_pool**: flatten `specific_evidence`. Group by type (price, time, count, anecdote) when patterns emerge.
* **emotion_histogram**: distribution of `emotional_tone` scores.
* **quote_pool**: all `representative_quote` strings, paired with stance and emotional_tone for later filtering.
* **credibility_breakdown**: how many posts are firsthand vs secondhand vs speculative.

Save aggregates to `research/<slug>/aggregates.json`.

## Stage 5: Modular Report Assembly

Read `templates/report_modules.md`. It defines a library of report modules, each with an ID, a purpose, an input requirement (which aggregates it needs), and a format example.

Use the `report_modules` list in profile.yaml as the assembly order. If the profile picked modules whose required aggregates are missing or thin, either compute the missing aggregate now or substitute a related module.

Standard module IDs:

| ID | Purpose | Best for |
| --- | --- | --- |
| M01_one_line | One sentence conclusion | All reports |
| M02_pain_point_chart | Top complaints with frequency and quote | product, service |
| M03_price_psychology | Price ceiling, floor, anchor brands | product, service |
| M04_entity_landscape | Brands or alternatives mentioned, share of voice | product, service, controversy |
| M05_opportunity_score | 1 to 10 with 4 dimension breakdown | product |
| M06_stance_distribution | For / against / neutral pie | controversy, social_event, policy |
| M07_argument_pairs | Strongest argument for each side | controversy, policy |
| M08_quote_wall | 6 to 10 representative quotes, grouped | cultural_trend, social_event, public_figure |
| M09_theme_clusters | Top 4 to 6 thematic clusters of claims | cultural_trend, tech_phenomenon |
| M10_time_evolution | How discussion shifted across the time window | any with >= 12 months data |
| M11_emotion_temperature | Emotion distribution chart and interpretation | controversy, social_event |
| M12_credibility_notes | Firsthand vs secondhand mix, what to trust | health_topic, controversy |
| M13_action_directions | Concrete next steps, prioritized by ROI | product, service |
| M14_data_appendix | Subreddits, queries, post counts | All reports |

Always include M01 first and M14 last. Pick 3 to 6 from the middle based on the profile.

Write the assembled report to `research/<slug>/report.md`. Then present it to the user inline. Offer follow ups:

* Drill into any specific claim or entity
* Reassemble report under a different module set, no refetch
* Compare to a sibling keyword
* Export quotes for a slide deck or annotation

## Output Conventions

* Reports default to the user's language (Chinese if the keyword is Chinese, English otherwise).
* Quotes from Reddit are kept under 15 words to respect copyright.
* All Reddit usernames are stripped from the report. Refer to commenters as `a poster` or `several users`.
* Numbers are rounded sensibly; do not invent precision the data does not support.

## Common Failure Modes

* **Sparse data**: if Stage 3 produces fewer than 10 candidates, expand the time window first, then add more subreddits, then loosen score and length thresholds. State the limitation in the report's data appendix.
* **Off topic noise**: if many Stage 4 records score below 6, the keyword groups were too broad. Tighten queries with the keyword in quotes or with an extra qualifier.
* **Single subreddit dominance**: if more than 60% of candidates come from one sub, broaden the recommended subreddit list and refetch the underrepresented ones.
* **Brigaded threads**: if a controversy report shows extreme stance polarization with very high emotional_tone, flag this in M11 and consider it a signal rather than ground truth.

## Files in This Skill

* `SKILL.md` (this file): workflow guide
* `REFERENCE.md`: subreddit speed lookup by topic family
* `scripts/setup_check.py`: PRAW credentials and dependency check
* `scripts/fetch_reddit.py`: Reddit fetcher
* `scripts/filter_posts.py`: rule based filter
* `templates/profile_template.yaml`: profile YAML structure
* `templates/analysis_schema.json`: unified analysis record schema
* `templates/analysis_prompt.md`: analysis prompt framing
* `templates/report_modules.md`: module library
* `examples/`: three worked profile examples covering product, controversy, trend
