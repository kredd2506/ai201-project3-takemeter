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
**real posts from the collected pool** (`data/raw_posts.csv`), cited by Reddit id so each is
auditable.

### Analysis (DD)
*A post whose main purpose is to argue a reasoned, evidence-backed case about a stock or trade
— one that would stand on its own even if you stripped out the poster's position.*
- `le235t` "GME Institutions Hold 177% of Float — Why the Squeeze is not Squoze" — walks float
  mechanics with Bloomberg data and a worked example.
- `mbx510` "SLV is a complete scam… the silver market is rigged" — structured argument on media
  incentives and ETF mechanics, with no personal bet at its center.

### Hype / Reaction (YOLO)
*A reactive, low-substance post centered on a personal bet, an outcome, or pure conviction,
with little or no supporting reasoning.*
- `1r35env` "If AMZN goes up 8% tomorrow this will be worth $1 million. If not, I'm cooked" — a
  bet and a hope, no analysis.
- `l71fl1` "Like this post if you are holding 💎 the real squeeze is yet to happen 🚀" — a pure
  morale/rally post.

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

### 3.2 Difficult cases logged during annotation (Milestone 2)
Real posts from `data/wsb_labeled.csv` / `data/edge_cases.csv` that gave genuine pause — the
candidate labels and the call made. (The full list of 70 changed/low-confidence rows is in
`data/edge_cases.csv`.)

1. **`lak773` "Why we're still winning… [REASSURANCE DD]"** — *Analysis vs Hype.* Flaired DD and
   cites short-sale mechanics, but the reasoning exists only to pump morale for holding.
   **Decided Hype:** strip the position and no standalone argument remains (codebook rule 1 / 4a).
2. **`1m9ajhj` "I made a $1.5M bet on Energy Fuels (UUUU)"** — *Hype vs Analysis.* Framed as a
   personal YOLO, but the body is a real rare-earth thesis (only domestic heavy-RE producer,
   DoD funding, named laggard competitors). **Decided Analysis:** the argument stands beyond the
   bet. (Exact mirror of case 1.)
3. **`la1o04` "There is no silver short squeeze. NONE. NEVER."** — *Discussion vs Analysis.*
   Flaired Discussion and reads like an opinion/PSA, but backs the claim with the 1980 Hunt-
   brothers corner and a Burry source. **Decided Analysis:** the evidence does the work.
4. **`1tyyxbo` "RDDT — help me see the light"** — *Discussion vs Analysis.* Question framing
   ("help me see the light"), but presents a worked thesis (market cap, API revenue, expiring
   data deals, training-data moat). **Decided Analysis:** worked thesis overrides the tacked-on
   question (codebook rule 2).
5. **`laccqy` "WHY YOU DEFINITELY SHOULD NOT … FALL FOR …"** — *Analysis vs Discussion.* DD-flaired
   and argumentative in tone, but it is a meta rant linking to *other* people's DDs with no
   worked thesis of its own. **Decided Discussion:** opens a topic, presents no argument itself.
6. **`1u748av` (Discussion-flaired short-bet post)** — *Discussion vs Hype.* **Decided Hype:**
   centered on the poster's own short position and conspiracy speculation, not evidence.

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

**Final labeled distribution (Milestone 2)** — `data/wsb_labeled.csv`, 283 posts after dropping
90 out-of-frame (meme/news/AMA/meta/megathread) from a 373-post pool:

| Label | Count | Share |
|-------|------:|------:|
| Hype | 141 | 49.8% |
| Analysis | 110 | 38.9% |
| Discussion | 32 | 11.3% |

≥200 total and no class >70% (max 49.8%), so the imbalance rule passes. **Discussion is the
genuinely rare class** here: even a targeted Discussion-flair oversample yielded mostly
megathreads, shitposts, and mis-flaired Analysis/Hype (only ~6 of 23 were real Discussion).
Per the fallback above we keep all real data, report the exact distribution, and lean on
macro-F1 (which weights classes equally) so the minority class is not hidden. The split is
stratified, so the test set preserves these proportions.

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

**Measurement protocol (so every number is reproducible and the pass/fail is defensible):**
- **Macro-F1** = the unweighted mean of the three per-class F1 scores.
- **Fixed split.** The 70/15/15 stratified split uses a **fixed random seed** (recorded in the
  notebook), so the test set is deterministic across runs.
- **Deterministic baseline.** The Groq `llama-3.3-70b-versatile` zero-shot baseline runs at
  **temperature = 0** with a **frozen prompt** (the exact string is committed). Outputs that
  cannot be parsed to one of the three labels (or are refusals) are **counted as wrong** and
  mapped to a fixed fallback class for the confusion matrix — never silently dropped.
- **Uncertainty.** Because the test set is small (~52 posts; see the caveat in §6.1), every
  headline metric is reported with a **bootstrap 95% confidence interval** (1000 resamples of
  the test set), and the macro-F1 headline is **cross-checked with stratified 5-fold CV** on the
  combined train+val data. Thresholds are judged against these, not a single fragile point.
- **Rounding.** Metrics are reported to **2 decimals**; a threshold is met only if the rounded
  value is `≥` the bar (e.g., 0.695 → 0.70 → meets 0.70; 0.694 → 0.69 → does not).

---

## 6. Definition of Success

The intended real-world use is a community tool that **suggests a flair / surfaces substantive
DD** as posts are submitted. Success is defined against that use, with thresholds set in advance
and measured once on the held-out test set.

**Genuinely useful (the bar this project targets):**
- Macro-F1 ≥ **0.70** on the test set.
- DD (the valuable minority class) F1 ≥ **0.65**.
- The fine-tuned model's macro-F1 **beats the zero-shot baseline by a margin of ≥ 0.03**
  (a smaller gap is treated as a tie, since it is within test-set noise) — or, if it does not,
  that result is reported honestly as a finding (a 70B model with strong priors plausibly wins
  on only ~200 training examples; that comparison is itself a core result).

**Good enough to deploy in a real community tool (a higher bar):**
- DD **precision ≥ 0.80** — a flair-suggestion tool that frequently mislabels hype as DD is
  worse than useless, so suggestions must be trustworthy.
- DD **recall ≥ 0.70** — it should catch most genuine DD, not just the obvious cases.
- Overall **macro-F1 ≥ 0.78**.

### 6.1 Review: are these criteria objective?
**Mechanically, yes:** each criterion is a numeric threshold on a named metric, computed on a
held-out test set, fixed before results are seen, so each resolves to a clean pass/fail (e.g.,
"macro-F1 = 0.73 ≥ 0.70 → met"). But *objectively computable* is not the same as *objectively
conclusive*, and two caveats are recorded honestly rather than hidden:

1. **Small test set.** At ~350 labeled posts, a 15% stratified test set is ~52 posts, ~17 of
   them DD — so the per-class DD thresholds (precision ≥ 0.80, recall ≥ 0.70, F1 ≥ 0.65) can
   swing several points on a single example. This is why §5 reports **bootstrap 95% CIs** and a
   **5-fold CV** cross-check and judges thresholds against those intervals; a point estimate that
   only marginally clears a bar (CI straddling it) is reported as "borderline," not a clean pass.
2. **Distribution scope.** The corpus is heavily skewed to the Jan-2021 GME saga (§3.1), so the
   metrics are objective *for this distribution*. They validate "useful/deployable **on
   r/wallstreetbets posts like these**," not unconditional real-world deployment; out-of-period /
   non-GME generalization is logged as a known limitation, not claimed.

With the measurement protocol (fixed seed, temperature 0, frozen prompt, defined handling of
unparseable outputs, the ≥ 0.03 baseline margin, and the rounding rule) the remaining judgment
is confined to the borderline-CI cases above, which are flagged as such.

---

## 7. AI Tool Plan

This is an annotation/evaluation project, not an implementation project, so AI tools help in
three specific places rather than by generating code.

### 7.1 Label stress-testing
**Method.** Give an LLM (Claude Opus 4.8) the three label definitions and the edge-case
description from §3 and ask it to generate posts that deliberately sit on the Analysis/Hype,
Discussion/Analysis, and Hype/Discussion boundaries. Any post I cannot classify cleanly with
the current rules exposes a gap, and I tighten the definitions *now*, before annotation.

**Executed (Milestone 1).** A first pass happened by reading 36 real posts (§3.1), which
surfaced the flair-noise and rally-vs-question issues. A second, harder synthetic pass
generated **8 boundary posts**; 6 resolved cleanly and **2 exposed gaps**, which were fixed
by adding three tie-break rules to the codebook:
- **Minimum substance (Appendix rule 4a):** a single unsupported causal assertion ("real
  yields are rising, short it") is *not* evidence-based → **Hype**, not Analysis.
- **Own-position questions (Appendix rule 2a):** "should I hold *my* calls?" is centered on a
  personal bet → **Hype**; a question about a security/market in general → **Discussion**.
- **Thesis + tacked-on question (Appendix rule 2):** a worked thesis ending in "what do you
  think?" stays **Analysis** (the question→Discussion rule applies only with *no* worked thesis).

These changes are reflected in §2, §3, and the Appendix codebook.

### 7.2 Annotation assistance
**Decision: yes — pre-labeling is used, and disclosed.** Two pre-label sources:
1. **Flair (primary).** Each post's flair, mapped to a label per §4, is itself a form of
   automatic labeling — every row in `data/raw_posts.csv` arrives with `label_source=flair`.
2. **LLM (secondary).** **Claude Opus 4.8** is used as a second-opinion pre-label where flair
   is missing, sarcastic, or contradicts the body, and to draft the per-row `notes` reasoning.
   Those rows are marked `label_source=llm`.

**Every row is then read and corrected by a human against the codebook** (`reviewed=true`)
before it enters train/val/test — skimming is not review. The §7.4 log reports how many rows
were pre-labeled by flair vs. LLM and how many changed on review. Tracking columns:

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

### 7.3.1 Baseline (zero-shot) error reflection — hypothesis to test after fine-tuning
Numbers saved in `results/baseline_groq_zeroshot.md`: accuracy 0.767, macro-F1 0.54;
Analysis P0.67/R0.94/F1 0.78, Hype P0.89/R0.81/F1 0.85, **Discussion 0.00 (0/5)**.

**Where it struggled:** Discussion collapses entirely; Analysis is over-predicted (high recall,
low precision). **Hypothesis:** the baseline keys on surface cues (tickers, finance jargon,
argument-shaped prose) rather than dominant function, defaulting substantive-sounding posts to
Analysis and failing to recognize Discussion (question/opinion with no worked thesis). Predicted
confusion: mostly **Discussion→Analysis** (all 5) plus some **Hype→Analysis** (directional-
conviction edge). Fine-tuning should lift Analysis precision and give Discussion nonzero recall,
but Discussion stays weakest (~5 test / 32 train → noisy). To be confirmed against the baseline
and fine-tuned confusion matrices.

### 7.4 AI usage disclosure (running log)
Where AI tools were used (tool: **Claude Opus 4.8**, unless noted):
- **(a) Label taxonomy & codebook** — refined the three labels and tie-break rules after a
  36-post pre-annotation read (§3.1). *[Milestone 1, done]*
- **(b) Label stress-testing** — generated 8 boundary posts; surfaced 2 gaps → 3 new codebook
  rules (§7.1). *[Milestone 1, done]*
- **(c) Collection tooling** — wrote `collect_data.py` (public-RSS collector). *[Milestone 1, done]*
- **(d) LLM pre-labeling + review** — *[Milestone 2, done]* all **373** pooled posts were
  bootstrap-labeled by flair, then every post was reviewed against the codebook by an LLM
  (Claude Opus 4.8, 8 batched labelers). **155 / 373 (41%) labels were changed** on review
  (90 reclassified to exclude — mostly megathreads/shitposts; the rest flipped between the 3
  classes); 10 were flagged low-confidence. The 70 changed/low-confidence rows are listed in
  `data/edge_cases.csv`. These are LLM labels (`reviewed_by=llm`); a **human pass is still
  required** before training — start with `edge_cases.csv`.
- **(e) Failure-pattern clustering** — over misclassified test posts, then human-verified (§7.3).
  *[after evaluation]*

Separately, the Groq `llama-3.3-70b-versatile` model is the *evaluated* zero-shot baseline —
part of the methodology being measured, not an authoring aid.

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
2. **Genuine question.** If the post ends in a real open question and presents **no worked
   thesis**, it's **Discussion**, even if it contains some reasoning. *(2a — own-position
   question: a question about whether to hold/sell the poster's **own** open position
   ("should I hold my NVDA calls?") is centered on a personal bet → **Hype**; a question about
   a security/market in general ("MU or SNDK?") → **Discussion**.)* A post that presents a
   worked thesis **and** tacks on "what do you think?" stays **Analysis** — this rule applies
   only when there is no worked thesis.
3. **Validation-seeking.** A question-shaped post that is really showing off an active bet and
   fishing for agreement is **Hype**, not Discussion.
4. **Substance, not quality.** "Analysis (DD)" means the post *makes an evidence-based argument* —
   it does not mean the argument is correct or good. A weak-but-real thesis is still DD.
   *(4a — minimum substance: a **single unsupported causal assertion** ("real yields are rising,
   short it") is not evidence-based. Analysis requires support — data, specific facts, a chain of
   reasoning, or sourced claims. A lone assertion paired with a bet → **Hype**.)*
5. **Rally vs. call-to-action.** A post centered on the poster's own bet/holding/emotion is
   **Hype** ("Like this if you're holding 💎🚀"); a post directing the crowd to do or think
   something is **Discussion** ("Preparing a class action — comment if you held GME").
6. **Out of frame (flair does not override this).** Memes/shitposts, bare external-headline
   News posts, AMAs, meta/announcement posts, and stickied daily/weekend megathreads are
   excluded even when carrying a DD/Discussion flair — they are dropped, not force-labeled.
