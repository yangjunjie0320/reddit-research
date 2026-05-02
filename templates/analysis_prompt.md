# Analysis Prompt Framing

Use this framing when reading each post in `candidates.jsonl` during Stage 4. You are doing the analysis yourself; this is not a prompt to send to another model. Treat it as a checklist for your own reasoning.

## Setup

For the current research run, load:

* The keyword and slug
* `profile.categorization` weights
* `profile.research_intent`
* `profile.analysis_emphasis` (list of fields to spend extra effort on)

## Per Post Procedure

For each post (a JSON object with `title`, `selftext`, and `top_comments`):

### Step 1: Relevance gate

Read the title and the first 200 chars of selftext. Ask: does this post substantively discuss the keyword, or only mention it in passing?

Score 0 to 10:

* 9 to 10: keyword is the post's central subject
* 7 to 8: keyword is a major sub theme; meaningful discussion present
* 5 to 6: keyword is mentioned with some context but is not central
* 0 to 4: passing mention or off topic

If below 6, record only `post_id`, `relevance_score`, and a one line `notes` field, then move on. Do not waste effort filling other fields.

### Step 2: Extract key claims

Read the full selftext and top comments. List every distinct opinion, complaint, observation, or argument expressed. Phrase each as verb plus object so claims can be clustered later. Examples:

* `lid leaks when bag tipped`
* `prefers four day workweek for mental health`
* `believes the policy hurts small businesses`
* `does not trust the brand after recall`

Avoid generic claims that say nothing concrete (`it is good`). If the post is purely a question with no claims, leave `key_claims` empty and rely on credibility_signals.

### Step 3: Extract specific evidence

Pull every concrete piece of evidence: prices, durations, dates, counts, anecdotes with specifics. Examples:

* `paid $42 in 2023`
* `lasted 3 months before handle broke`
* `study cited from BMJ 2022`
* `worked for 6 weeks on the trial`

Speculation and round number guesses do not count. If the post has none, leave empty.

### Step 4: Extract entities

Brands, product names, people, organizations, places, alternatives. Normalize obvious variants (`H Flask` to `Hydro Flask`, `iron-flask` to `Iron Flask`). When the post compares two things, list both.

### Step 5: Stance

Only assign stance when the post takes a position toward the keyword. Use `null` when the post is purely informational, a how-to question, or an open ended discussion with no implied position.

* `for`: clear endorsement or positive recommendation
* `against`: clear criticism, complaint, or recommendation against
* `neutral`: explicit statement of neutrality, weighing both sides
* `mixed`: contains genuinely both positive and negative claims of comparable strength
* `null`: stance is not the right lens for this post

### Step 6: Emotional tone

0 to 10. Calibrate against these anchors:

* 0 to 2: calm, analytical, or matter of fact
* 3 to 5: clear feeling without intensification
* 6 to 7: strong feeling with intensifiers, caps, or repeated punctuation
* 8 to 10: rage, despair, or rapture; profanity, threats, or hyperbolic praise

### Step 7: Representative quote

Pick one verbatim sentence from the post or top comment that best captures the signal. Hard rules:

* Under 15 words
* Verbatim, no editing for grammar
* Stripped of any usernames or links
* If nothing under 15 words is good, use a short fragment marked with ellipsis

### Step 8: Credibility signals

Tag any of these that apply:

* `claims_owner`: poster says they bought or own the thing
* `claims_user`: poster says they used or experienced the thing
* `posted_photo`: thread has user submitted images
* `linked_source`: poster cites or links external evidence
* `professional_in_field`: poster identifies as an expert (verify plausibility)
* `secondhand`: poster reports someone else's experience
* `speculation`: poster explicitly speculates
* `anecdotal`: single personal story without broader claim
* `controversial_thread`: heated disagreement in comments, low ratio

### Step 9: Apply emphasis

Look at `profile.analysis_emphasis`. For listed fields, expand the depth: include more items, more careful normalization, more nuanced labels. For unlisted fields, do the minimum honest job.

Example: if emphasis is `[key_claims, specific_evidence, entities_mentioned]`, spend most effort there. Stance can be `null` more readily; emotional_tone can be a quick estimate.

Example: if emphasis is `[stance, emotional_tone, key_claims]`, treat every post as a stance call, calibrate emotional_tone carefully, and skim entities.

## After All Posts

Aggregate into `aggregates.json`. Build only the aggregates needed by the chosen report modules. See the module table in SKILL.md Stage 5.

When clustering near duplicate `key_claims`:

* Merge claims that share both verb and object even if phrased differently (`lid leaks` and `cap drips` merge; `lid leaks` and `bottle smells` do not)
* Prefer the most concrete phrasing as the cluster label
* Track the original post_ids contributing to each cluster

When counting entities:

* Group obvious aliases
* Filter out the keyword itself
* Filter out generic terms (`Reddit`, `Amazon`, `the company`) unless they are actually the subject

## Common Pitfalls

* Reading only the post body and missing claims in top comments
* Inflating relevance because the post is interesting (interesting is not the same as on topic)
* Letting one viral post dominate when its claims are not echoed elsewhere
* Quoting more than 15 words from any single source
* Producing very generic key_claims that cluster everything into one bucket
