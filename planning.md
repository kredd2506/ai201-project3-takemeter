# planning.md — r/wallstreetbets Post Classifier

A text classifier that sorts r/wallstreetbets posts by the *substance* of the post:
serious analysis vs. hype vs. open discussion.

---

## 1. Community

**Choice:** [r/wallstreetbets](https://reddit.com/r/wallstreetbets) (WSB), a ~19.9M-member
subreddit where retail traders discuss stock and options bets.

**Why this community.** WSB is active, large, and easy to sample from: every submission
carries a user/mod-assigned "flair," so I can collect 200+ public posts and bootstrap an
initial label for each one for free.

**Why it's a good fit for a classification task.** The defining feature of WSB is that post
quality *varies enormously* — and that variance is not random noise, it's a distinction the
community itself recognizes and polices. The same feed contains rigorously argued investment
theses ("here's my DD"), pure emotional gambling posts ("yolo'd my life savings"), and genuine
crowd-sourced questions ("which of these two looks better?"). Members demand substance from
each other ("where's the DD?"), and the platform encodes the distinction in its flair system,
which research has split into *proactive* posts that reason about price (DD, YOLO, Discussion)
and *reactive* posts that just respond to events (Gain, Loss, Meme, News). That built-in,
community-meaningful spread of quality is exactly what makes "substance vs. hype" a real,
learnable distinction rather than an arbitrary one I imposed.

---

## 2. Labels

Three labels, assigned by a post's **dominant function**, not its topic. Examples below are
paraphrased from real posts read during the pre-annotation review (anonymized; replace with
your own collected, anonymized examples).

### Analysis (DD)
*A post whose main purpose is to argue a reasoned, evidence-backed case about a stock or trade.*
- A KVYO write-up citing high revenue growth, profitability, and a sub-3x price-to-sales
  multiple as the reason it's mispriced.
- A Texas Pacific Land post built around quiet insider buying as the core thesis.

### Hype / Reaction (YOLO)
*A reactive, low-substance post centered on a personal bet, an outcome, or pure conviction,
with little or no supporting reasoning.*
- "Yolo'd my life savings into three stocks last week."
- "With $300k, hitting $1M is basically inevitable."

### Discussion / Opinion
*A post whose dominant function is to open a topic to the community — a genuine
question, an opinion/PSA, or a call to action — without presenting a worked thesis
or centering on the poster's own bet.*
- "WE are Preparing a Class Action LAWSUIT against Robinhood!" (a call to action put
  to the crowd).
- "MU or SNDK — which looks better going forward?" (a genuine open question).

*Refined after the pre-annotation read (see §3.1): on WSB the "Discussion" flair is
dominated by rants, opinions, and rallying cries, not clean questions, so the label
is broadened from "open question" to "opens a topic — question / opinion / PSA /
call-to-action."*

**Out of frame (excluded, not labeled):** Meme/Shitpost posts, pure external-headline News
posts, and stickied Daily/Weekend megathreads. These are dropped at collection time so we
don't need a catch-all "other" bucket; the three labels are exhaustive over the remaining
text-bearing posts.

---

## 3. Hard Edge Cases

**Primary edge case — the directional-conviction post (Analysis vs. Hype).** Posts like
"The top has yet to come for MU and DRAM" or "Gold is done (for now)." These assert a market
direction the way real DD does, but they may contain zero actual reasoning the way hype does —
and you often cannot tell which from the title alone. A post titled "Hot Take: gold may
underperform but…" can still contain a real argument, which is why the label tracks *substance,
not stance* and not the words a poster uses.

**Handling rule:** read the body and ask — *would this stand as an argument if you stripped out
the poster's own position and screenshot?* If yes → **Analysis (DD)**. If it's mostly assertion,
or the reasoning exists only to justify a bet the poster has already placed → **Hype**. A post
that genuinely cannot be resolved after reading the body is logged as an adjudicated edge case
(see codebook) rather than force-fit, and those logged cases feed the error-analysis writeup.

**Secondary edges, with their rules:**
- *Thesis-shaped question (Discussion vs. Analysis):* if it ends in a genuine open question and
  presents no worked thesis, it's **Discussion** (e.g., "MU or SNDK?").
- *News-prompted question (Discussion vs. excluded News):* we exclude bare headlines, but a
  question *prompted by* an event ("Domino's value now that Pizza Hut is being sold?") is a real
  question to the crowd → **Discussion**.
- *Opinion / PSA post:* an opinion piece with no thesis, bet, or question ("Reminder: you
  shouldn't invest if you can't handle X") opens a topic → **Discussion**.
- *Rally / call-to-action (Hype vs Discussion):* WSB flair scatters rallying content
  across both YOLO and Discussion. Rule: if it centers on the poster's own bet, holding,
  or emotion ("Like this post if you're holding 💎🚀") → **Hype**; if it is directed at the
  crowd to *do* or *think* something ("Preparing a class action — comment if you held GME")
  → **Discussion**.

### 3.1 Findings from the pre-annotation read (Milestone 1)
Read 36 real posts (12 per flair group, bodies included) from the 350-post pool before
committing to labels. What the actual text changed:
1. **Flair is genuinely noisy — confirmed with examples.** DD-flaired posts include real
   DD *and* pure morale ("REASSURANCE DD", `lak773`) *and* jokes ("Markets crash every
   time Oreo releases a greater-stuffed cookie", `mzkumu`); a YOLO-flaired post (`1m9ajhj`)
   is a genuine rare-earth thesis; a Discussion-flaired post (`la1o04`) is evidence-based
   analysis. → validates the mandatory human-review step (§4, §7.2).
2. **"Discussion" flair ≠ questions** — it is mostly rants/opinions/calls-to-action, hence
   the broadened Discussion definition above.
3. **~29% of posts are title-only / image posts** (gain-porn screenshots, photos) → confirms
   `title + selftext` input and that some labels must rest on the title alone.
4. **Heavy Jan-2021 GME topical skew** in `top`-of-year/all listings. Topical, not a label
   problem, but a generalization risk to note; mitigated somewhat by `new`/`hot` and the
   varied flair searches.
5. **Excludes must override flair**: megathreads ("Pajama Party Megathread", `l7iorh`), meta
   ("Subreddit of the Day", `l7sx8h`), AMAs ("Mark Cuban AMA", `lawubt`), and shitposts are
   dropped even when DD/Discussion-flaired.

**Mutual-exclusivity decision procedure (apply in order):** (1) evidence-based argument
that stands without the poster's position? → **Analysis**; (2) else, centered on the
poster's own bet/outcome/emotion or a pure rally? → **Hype**; (3) else, opens a topic
(question/opinion/PSA/call-to-action)? → **Discussion**. ~85% of the read sample
single-labeled cleanly; the rest are logged edge cases.

---

## 4. Data Collection Plan

**Source.** Reddit's public `.rss`/Atom feeds, pulling from r/wallstreetbets `top` (year and
all), `new`, `hot`, and flair-targeted `search` feeds. See `collect_data.py`.

*Note (Milestone 1):* planning originally specified the Reddit Data API via PRAW, but as of
mid-2026 Reddit has gated new Data API app registration behind a moderation-use-case review,
so self-serve script credentials were not available. Reddit's public `.rss` feeds require no
authentication and satisfy the "public posts only, no auth" rule directly, so the collector
uses those (with rate-limit backoff). The flair-bootstrap mechanism is unchanged: flair-search
feeds (`q=flair:"DD"`) return only posts of that flair, so each result inherits a known flair.

**Bootstrapping labels from flair.** Each post's flair gives an initial label:

| Flair | Bootstrap label |
|-------|-----------------|
| DD, Technical Analysis | Analysis (DD) |
| YOLO, Gain, Loss | Hype / Reaction |
| Discussion, Question | Discussion |
| Meme, Shitpost, News, Daily/Weekend Discussion | excluded |

**Manual review.** Flair is sometimes wrong, missing, or sarcastic, so every row is reviewed by
hand against the codebook and corrected. This review is the documented labeling process; the
corrections are tracked (see §7.2).

**Target counts.** Aim for ~70+ examples per label (≥210 total) so no class is trivially small.
Final per-label counts are reported in the README.

**If a label is underrepresented after 200 examples** (DD is the realistic risk — genuine DD is
a small share of all posts):
1. Targeted oversampling first: pull additional DD/Technical-Analysis-flaired posts from longer
   time windows (`top` of year and all-time) and additional listing pages until the count is met.
2. If still short, downsample the majority classes (Discussion/Hype) to restore rough balance,
   keeping the test set stratified.
3. As a last resort, accept mild imbalance, report the exact class distribution, and lean on
   macro-F1 (which weights classes equally) so the rare class isn't hidden.

**Splits.** Stratified by label: 70% train / 15% validation / 15% test (~140/30/30 at 200).
The test set is touched only once, for final evaluation.

**Model input.** `title` + "\n\n" + `selftext`, because many posts are title-only and, as the
pre-annotation read showed, the title alone is often insufficient to classify a post.

---

## 5. Evaluation Metrics

Evaluated on the held-out test set, for **both** the fine-tuned DistilBERT and the zero-shot
Groq `llama-3.3-70b-versatile` baseline.

- **Overall accuracy** — reported, but *not* sufficient on its own. The classes are imbalanced
  (DD is scarce), so a model that simply predicts the majority class can post a high accuracy
  while being useless at the thing we actually care about. Accuracy hides per-class failure.
- **Macro-averaged F1 (primary headline metric)** — averages F1 across the three classes with
  equal weight, so weak performance on the rare DD class cannot be masked by strong performance
  on common Discussion/Hype posts. This is the metric the project is optimized against.
- **Per-class precision, recall, and F1** — because the cost of errors differs by class. For the
  intended use (surfacing substantive analysis), **DD recall** matters (don't miss good DD) and
  **DD precision** matters (don't flood users with hype mislabeled as DD). Per-class numbers make
  that tradeoff visible.
- **Confusion matrix** — to see *which* pairs are confused. We expect the model to struggle most
  on Analysis↔Hype (the directional-conviction edge) and Discussion↔Analysis.

Why these and not just accuracy: the task is an imbalanced, multi-class problem where the
valuable class is the minority one, so we need metrics that are per-class and balance-aware,
plus a confusion matrix to diagnose *how* it fails for the error analysis.

---

## 6. Definition of Success

The intended real-world use is a community tool that **suggests a flair / surfaces substantive
DD** as posts are submitted. Success is defined against that use, with thresholds set in advance
and measured once on the held-out test set.

**Genuinely useful (the bar this project targets):**
- Macro-F1 ≥ **0.70** on the test set.
- DD (the valuable minority class) F1 ≥ **0.65**.
- The fine-tuned model's macro-F1 **beats the zero-shot baseline** — or, if it does not, that
  result is reported honestly as a finding (a 70B model with strong priors plausibly wins on
  only ~200 training examples; that comparison is itself a core result).

**Good enough to deploy in a real community tool (a higher bar):**
- DD **precision ≥ 0.80** — a flair-suggestion tool that frequently mislabels hype as DD is
  worse than useless, so suggestions must be trustworthy.
- DD **recall ≥ 0.70** — it should catch most genuine DD, not just the obvious cases.
- Overall **macro-F1 ≥ 0.78**.

### 6.1 Review: are these criteria objective?
Yes. Each criterion is a numeric threshold on a named metric, computed once on a held-out test
set, and fixed before results are seen. At the end of the project each line resolves to a clean
pass/fail (e.g., "macro-F1 = 0.73 ≥ 0.70 → met"), so whether the classifier hit its goals is an
objective check, not a judgment call.

---

## 7. AI Tool Plan

This is an annotation/evaluation project, not an implementation project, so AI tools help in
three specific places rather than by generating code.

### 7.1 Label stress-testing
Before annotating 200 examples, I give an LLM the three label definitions and the edge-case
description from §3 and ask it to generate 5–10 posts that deliberately sit on the
Analysis/Hype and Discussion/Analysis boundaries. If it produces any post I cannot classify
cleanly with the current rules, that exposes a gap and I tighten the definitions *now*, before
annotation. (A first pass of this happened by reading real posts, which surfaced the News
category and the directional-conviction edge; the synthetic stress test is a second, harder
pass.) Outcome and any definition changes are recorded here.

### 7.2 Annotation assistance
**Yes — pre-labeling is used, and disclosed.** The primary pre-label is the post's **flair**,
which is itself a form of automatic labeling and is disclosed as such. For posts with missing or
sarcastic flair, an LLM may be used as a second-opinion pre-label. Tracking columns in the
dataset:

| Column | Meaning |
|--------|---------|
| `label_source` | `flair`, `llm`, or `human` — origin of the pre-label |
| `original_label` | the pre-label before review |
| `final_label` | the label after human review (used for training) |
| `reviewed` | boolean; every row must be `true` before use |

Every row is human-reviewed against the codebook before it enters train/val/test. The AI usage
section reports how many rows were pre-labeled by flair vs. by LLM, and how many were changed on
review.

### 7.3 Failure analysis
After evaluation, I export the list of misclassified test posts (text, true label, predicted
label) and ask an LLM to cluster them into error patterns. What I look for:
- Which confusion pairs dominate (expecting Analysis↔Hype and Discussion↔Analysis).
- Reliance on surface lexical cues rather than meaning (e.g., predicting DD because the text
  contains "$TICKER," "calls/puts," or the literal word "DD").
- Length effects (does it fail on short, title-only posts?).
- Sarcasm/irony and self-labeled "hot takes."

**Verification:** I do not accept any pattern the LLM asserts on its word. For each claimed
pattern I read the actual posts behind it and confirm it against the confusion matrix and a
minimum number of supporting examples; unsupported patterns are dropped from the writeup.

### 7.4 AI usage disclosure (to be completed)
A running log of where AI tools were used: (a) help designing/refining the label taxonomy and
codebook; (b) label stress-testing (§7.1); (c) optional LLM pre-labeling counts (§7.2); (d)
failure-pattern clustering (§7.3). The Groq `llama-3.3-70b-versatile` model is also used as the
*evaluated* zero-shot baseline, which is part of the methodology rather than an authoring aid.

---

## 8. Maintenance

This document is updated **before** starting any stretch features, and whenever annotation or
evaluation surfaces a change to the labels, codebook, or success criteria.

---

## Appendix: Annotation Codebook (tie-break rules)

Apply in order:
1. **Research vs. flex.** If a post argues a thesis with evidence, it's **Analysis (DD)** even if
   the poster mentions their own position. If it's mainly a position/outcome with a one-liner of
   justification, it's **Hype**. Test: would it stand as an argument without the screenshot?
2. **Genuine question.** If the post ends in a real open question and presents no worked thesis,
   it's **Discussion**, even if it contains some reasoning.
3. **Validation-seeking.** A question-shaped post that is really showing off an active bet and
   fishing for agreement is **Hype**, not Discussion.
4. **Substance, not quality.** "Analysis (DD)" means the post *makes an evidence-based argument* —
   it does not mean the argument is correct or good. A weak-but-real thesis is still DD.
5. **Rally vs. call-to-action.** A post centered on the poster's own bet/holding/emotion is
   **Hype** ("Like this if you're holding 💎🚀"); a post directing the crowd to do or think
   something is **Discussion** ("Preparing a class action — comment if you held GME").
6. **Out of frame (flair does not override this).** Memes/shitposts, bare external-headline
   News posts, AMAs, meta/announcement posts, and stickied daily/weekend megathreads are
   excluded even when carrying a DD/Discussion flair — they are dropped, not force-labeled.
