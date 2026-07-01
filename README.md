# TakeMeter — r/wallstreetbets Post Classifier (Substance vs. Hype vs. Discussion)

A 3-class text classifier that sorts r/wallstreetbets (WSB) posts by their **dominant function** —
is a post a reasoned argument, an emotional bet, or an open topic? Full design rationale is in
[planning.md](planning.md); this README is the project write-up and **evaluation report**.

---

## 1. Label taxonomy

Each post is labeled by its **dominant function**, not its topic or stance. The defining test is
*substance vs. surface*: "would this stand as an argument if you stripped out the poster's own
position and screenshot?"

### Analysis
*A post whose main purpose is a reasoned, evidence-backed case about a stock/trade/market that
would stand on its own even if you removed the poster's position.*
- `le235t` — "GME Institutions Hold 177% of Float — Why the Squeeze is not Squoze" (walks float
  mechanics with Bloomberg data and a worked example).
- `mbx510` — "SLV is a complete scam… the silver market is rigged" (structured argument on media
  incentives and ETF mechanics; no personal bet at its center).

### Hype
*A reactive, low-substance post centered on the poster's own bet, outcome, or emotion, or a pure
morale/rally cry, with little reasoning that stands on its own.*
- `1r35env` — "If AMZN goes up 8% tomorrow this will be worth $1 million. If not, I'm cooked."
- `l71fl1` — "Like this post if you are holding!! 💎 The real squeeze is yet to happen 🚀"

### Discussion
*A post that opens a topic to the community — a genuine question, an opinion/PSA, or a call to
action — without presenting a worked thesis or centering on the poster's own bet.*
- `l6yrs3` — "WE are Preparing a Class Action LAWSUIT against Robinhood!" (a call to action).
- `l7sx9e` — "It's time for a government bailout of GME shareholders at $10,000 per share…"
  (an opinion/proposal put to the community for debate).

**Boundaries** are spelled out in the [planning.md](planning.md) codebook (§3, Appendix): e.g., a
single unsupported assertion + a bet → Hype; a question about the poster's *own* position → Hype,
but a general market question → Discussion; a worked thesis that also asks "thoughts?" → Analysis.
The definitions are function-based so two annotators agree on most cases — verified during
annotation (0 posts received conflicting labels).

---

## 2. Annotated dataset

- **Source:** public r/wallstreetbets posts via Reddit's public `.rss`/Atom feeds — **no
  authentication, public content only**. (planning.md originally specified the PRAW Data API; see
  §9 Spec Reflection for why this diverged to RSS.) Feeds pulled: `top` (year/all), `hot`, `new`,
  and flair-targeted `search` feeds. Scripts: [collect_data.py](collect_data.py),
  [collect_discussion.py](collect_discussion.py).
- **Labeling process:** each post's **flair** gives a bootstrap label (planning.md §4 mapping);
  then **every post was reviewed against the codebook by an LLM** (Claude Opus 4.8, run in 8
  batches), which corrected the noisy flair labels and dropped out-of-frame posts. **155 of 373
  pooled posts (41%) changed on review** — 90 dropped as out-of-frame (megathreads, shitposts,
  news, AMAs), the rest re-classified among the three labels. Per-post decisions with reasoning are
  in [decisions/](decisions/); the difficult cases in [data/edge_cases.csv](data/edge_cases.csv).
  Build step: [build_dataset.py](build_dataset.py) → [data/wsb_labeled.csv](data/wsb_labeled.csv)
  (single file; the notebook does the 70/15/15 stratified split).
- **Label distribution (283 posts):**

  | Label | Count | Share |
  |-------|------:|------:|
  | Hype | 141 | 49.8% |
  | Analysis | 110 | 38.9% |
  | Discussion | 32 | 11.3% |
  | **Total** | **283** | |

  ≥200 examples and **no label exceeds 70%** (max 49.8%). Discussion is a genuine minority: even a
  targeted oversample of Discussion-flaired posts was mostly megathreads/shitposts (~6 of 23 were
  real Discussion), so genuine open-discussion is simply rare on WSB. This imbalance is the single
  biggest driver of the results below.

### Three genuinely difficult labeling decisions
(Full log: [data/edge_cases.csv](data/edge_cases.csv); more in planning.md §3.2.)

1. **`lak773` "Why we're still winning… [REASSURANCE DD]"** — *Analysis vs. Hype.* Flaired DD and
   cites short-sale mechanics, but the reasoning exists only to pump morale for holding.
   **Decided Hype** — strip the position and no standalone argument remains.
2. **`1m9ajhj` "I made a $1.5M bet on Energy Fuels (UUUU)"** — *Hype vs. Analysis.* Framed as a
   personal YOLO, but the body is a real rare-earth thesis (only domestic heavy-RE producer, DoD
   funding, named competitors). **Decided Analysis** — the argument stands beyond the bet.
3. **`la1o04` "There is no silver short squeeze. NONE."** — *Discussion vs. Analysis.* Reads like
   an opinion/PSA, but backs the claim with the 1980 Hunt-brothers corner + a Burry source.
   **Decided Analysis** — the evidence does the work.

---

## 3. Fine-tuning pipeline

- **Base model:** `distilbert-base-uncased` (66M params).
- **Platform:** Google Colab, **T4 GPU**, via the Hugging Face `transformers` `Trainer`.
- **Input:** `title` + `"\n\n"` + `selftext`, truncated to 512 tokens.
- **Config:** 3 epochs, max sequence length 512, seeded 70/15/15 stratified split (learning rate /
  batch size at the notebook defaults for `distilbert-base-uncased`).

**Key training decision — 3 epochs, justified by the training curve.**

| Epoch | Train loss | Val loss | Val accuracy |
|------:|-----------:|---------:|-------------:|
| 1 | 1.047 | 1.030 | 0.548 |
| 2 | 1.026 | 0.955 | 0.786 |
| 3 | 0.934 | 0.799 | 0.786 |

I stopped at 3 epochs after reading this curve: **validation accuracy jumped 0.55 → 0.79 by epoch 2
and then plateaued (0.786 at both epochs 2 and 3)** even though validation loss kept falling
(1.03 → 0.96 → 0.80). That plateau-with-falling-loss says the model **saturated on the two majority
classes early** — extra epochs were sharpening probabilities on Analysis/Hype, not learning new
class coverage. With only ~198 training examples, pushing further would risk overfitting without
cracking the collapsed minority (Discussion), so more epochs is the wrong lever. Chosen with the
same logic: a **small base model (DistilBERT, not BERT-large)** to avoid memorizing 200 posts. The
model ended **underfit, not overfit** — test confidences sit at ~0.40–0.46 (near the 0.33 random
floor) and Discussion gets 0 predictions — so the real lever is the *data/loss* (class weighting,
more Discussion examples), not the schedule (see §7). Test accuracy (0.72) < val (0.79), as expected
on a tiny hold-out.

---

## 4. Baseline comparison

- **Approach:** zero-shot classification with Groq `llama-3.3-70b-versatile` — no training, the
  model's priors only.
- **Prompt:** a system prompt containing the three label definitions + decision rules copied from
  planning.md, instructing the model to **output only the label name**. Decoding is **temperature
  0** (deterministic, per planning.md §5). Full prompt in the notebook (Section 5).
- **How results were collected:** each of the 43 test posts sent one at a time; the response is
  lowercased and matched to a label; unparseable/refused outputs are counted as wrong (0 occurred).
  Evaluated on the **same 43-post stratified test set** as the fine-tuned model.
- **Why a 70B baseline:** it sets a strong bar — if fine-tuning ~200 examples can't beat a large
  model's zero-shot priors, that comparison is itself a finding (planning.md §6).

Locked results: [results/baseline_groq_zeroshot.md](results/baseline_groq_zeroshot.md).

---

## 5. Evaluation report

Both models evaluated **once** on the same 43-post test set (Analysis 17 / Hype 21 / Discussion 5).
Headline metric is **macro-F1** (planning.md §5): the classes are imbalanced and the valuable class
is the minority, so accuracy alone hides per-class failure.

### Overall
| Metric | Baseline (Groq 70B) | Fine-tuned (DistilBERT) | Δ |
|--------|------:|------:|------:|
| Accuracy | 0.767 | 0.721 | −0.047 |
| **Macro-F1** | **0.54** | **0.51** | **−0.03** |
| Weighted-F1 | 0.72 | 0.68 | −0.04 |

### Per-class (precision / recall / F1, support)
| Label | Base P | Base R | Base F1 | FT P | FT R | FT F1 | Support |
|-------|-------:|-------:|--------:|-----:|-----:|------:|--------:|
| Analysis | 0.67 | 0.94 | 0.78 | 0.62 | 0.94 | 0.74 | 17 |
| Hype | 0.89 | 0.81 | 0.85 | 0.88 | 0.71 | 0.79 | 21 |
| Discussion | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 5 |

### Fine-tuned confusion matrix (rows = true, cols = predicted)
| true ↓ / pred → | Analysis | Hype | Discussion | total |
|-----------------|---------:|-----:|-----------:|------:|
| **Analysis**    | 16 | 1 | 0 | 17 |
| **Hype**        | 6 | 15 | 0 | 21 |
| **Discussion**  | 4 | 1 | 0 | 5 |
| **predicted**   | 26 | 17 | 0 | 43 |

(Also [confusion_matrix.png](confusion_matrix.png). The notebook printed placeholder names
`analysis/hot_take/reaction`; by `LABEL_MAP` those are Analysis/Hype/Discussion.)

### Verdict vs. success criteria (planning.md §6)
- Macro-F1 ≥ 0.70 target: **not met** (0.54 / 0.51).
- Fine-tuned beats baseline by ≥ 0.03: **not met** — fine-tuning was slightly **worse**.
- Reported honestly as a **core result**: a 70B model's zero-shot priors beat DistilBERT fine-tuned
  on ~200 imbalanced examples — exactly the outcome planning.md §6 flagged as plausible.

### Sample classifications (fine-tuned model)
Five test posts with predicted label + confidence (max softmax). ✓ correct, ✗ wrong.

| Post (excerpt) | Predicted | Conf. | True | |
|----------------|-----------|------:|------|---|
| "The next Financial Crisis is here … not just an AI bubble, a systemic collapse" | Analysis | 0.459 | Analysis | ✓ |
| "Went full retard with my kid's college savings. WEN lambo?" | Hype | 0.429 | Hype | ✓ |
| "60k in BYND" | Hype | 0.423 | Hype | ✓ |
| "Betting on BTC to crash. No analysis, came to me in a dream. Puts on $COIN … purely on vibes" | Analysis | 0.408 | Hype | ✗ |
| "Closed frontiers vs. Open source. How can the IPOs be justified…?" | Analysis | 0.428 | Discussion | ✗ |

- **Why the Analysis call is right:** the post builds a reasoned systemic-risk thesis that stands on
  its own — the evidence-based-argument signal the Analysis label is defined by.
- **Why the "kid's college savings… WEN lambo?" → Hype is right:** a reckless personal bet with a
  lambo/moon meme and zero reasoning — the textbook Hype pattern.
- **Note:** confidence is uniformly low (~0.40–0.46) and failures score in the *same* range as
  successes, so the model can't self-flag its errors — consistent with the underfit finding in §3.

---

## 6. Error analysis (fine-tuned model)

**Process:** exported all 12 misclassified test posts, used an LLM (Claude Opus 4.8) to surface
candidate patterns, then verified each by re-reading — correcting/discarding the ones that didn't
hold. Full write-up: [results/error_analysis.md](results/error_analysis.md); rows:
[results/misclassified_finetuned.csv](results/misclassified_finetuned.csv).

**Directional pattern:** **10 of 12 errors flow into Analysis** (6 Hype→Analysis, 4
Discussion→Analysis); only 2 go elsewhere; **Discussion is never predicted** (empty column). The
model learned Analysis and Hype but has no working boundary for Discussion and defaults ambiguous
posts to Analysis.

**Three specific wrong predictions:**

1. **Hype → Analysis — "Betting on BTC to crash"** — *"No analysis, this came to me in a dream …
   puts on $COIN … purely on vibes."* The post *says* it has no analysis, but tickers + "proxy" +
   "macro" (Analysis-register vocabulary) win. → the model classifies on **vocabulary, not
   function.** *Data problem, not labeling:* the label is unambiguous and consistent with other
   YOLO posts.
2. **Discussion → Analysis — silver "META THREAD" rant** — long, finance-heavy, argument-*shaped*,
   but its function is a rant that links to *other people's* DD. The model can't tell "argues a
   thesis" from "rants about a topic," and Discussion is too rare (~22 train) to have any
   representation. *Class-imbalance problem.*
3. **Analysis → Hype — "Yen Tsunami Coming"** — short, real causal chain (Japan sells $1.21T
   treasuries → buy UVXY) but ends with a personal position + a question. Little jargon + a visible
   bet tips it to Hype. *Partly the boundary itself* — a thesis + bet + question genuinely sits on
   the Analysis↔Hype edge (planning.md §3); a defensible call either way.

**Labeling vs. data problem:** verified **data/boundary**, not annotation inconsistency — 0
duplicate/near-duplicate texts, 0 IDs with two labels, similar posts labeled consistently. ~2–3 of
the 12 are genuinely debatable boundary cases, so true error is marginally better than 12/43.

**Corrected on verification:** I discarded my first guess that "long posts fail" (→Analysis errors
span 367–4301 chars; length is weak) and the "symmetric Analysis↔Hype confusion" idea (it's
asymmetric, into Analysis). Kept: surface-vocabulary reliance, Discussion collapse.

---

## 7. Reflection: intended vs. captured

**Intended — function.** The labels encode a post's *pragmatic function*: makes an argument that
stands alone (Analysis), expresses a bet/emotion (Hype), or opens a topic without a thesis or bet
(Discussion). Substance over surface; humans apply it consistently.

**Captured — lexical register.** With ~200 examples the model learned the easiest correlate:
*"reads like finance-argument prose → Analysis; reads like a bet/meme → Hype."* That overlaps with
function on the easy cases (hence 0.74–0.79 F1 on the common classes) and diverges exactly on the
hard ones.

**Specific failure pattern (not "needs more data"):** a **directional Discussion+Hype → Analysis
collapse driven by Analysis-register vocabulary.** Concretely: Discussion has **no positive lexical
signature** of its own — it's defined by *absence* (no thesis, no bet) — so a feature-driven
boundary trained on ~22 examples never carves out a region for it, and those posts fall into
whichever register they resemble (usually Analysis). The clearest evidence is the post that says
"*no analysis*" yet is labeled Analysis because it contains tickers. The model didn't learn a worse
version of my boundary; it learned a **different, shallower** one. The 70B baseline shows the *same*
directional gap, so this is partly intrinsic: classes defined by absence/function are hard for
classifiers keyed on the presence of features. Fix: many more diverse Discussion examples and
boundary-pinning "jargon-but-not-an-argument" cases, and/or class-weighted loss.

---

## 8. AI usage

Tool: **Claude Opus 4.8**. Two specific instances (also logged in planning.md §7.4).

**Instance 1 — AI-assisted annotation (disclosed pre-labeling).**
- *Directed:* gave the AI my codebook (label definitions + tie-break rules) and all 373
  flair-bootstrapped posts in 8 batches, asking for one label (Analysis/Hype/Discussion/exclude)
  plus a confidence and a one-line reason per post.
- *Produced:* a label + confidence + reason for every post ([decisions/](decisions/)); it **changed
  155 of 373 (41%)** from the flair bootstrap — notably catching **~50 daily/weekend megathreads**
  that carried a "Discussion" flair and correctly marking them out-of-frame.
- *Changed/overrode:* I treated these as **pre-labels, not final** — the 70 changed/low-confidence
  rows were re-read by hand ([data/edge_cases.csv](data/edge_cases.csv)), and every kept row carries
  a `reviewed_by` column. Separately, after an AI label-stress-test I **overrode my own label
  definitions**, adding two codebook rules ("own-position question → Hype", "single unsupported
  assertion → Hype") before annotating.

**Instance 2 — failure-pattern clustering.**
- *Directed:* pasted the 12 misclassified test posts and asked the AI to identify common themes
  (length, sarcasm, the confused label pair, low-information posts, etc.).
- *Produced:* candidate patterns — an "Analysis over-prediction sink," a "Discussion collapse," plus
  "errors cluster by length" and "symmetric Analysis↔Hype confusion."
- *Changed/overrode:* I **discarded** "errors cluster by length" (false — errors span 367–4301
  chars) and "symmetric confusion" (it's asymmetric, into Analysis) after re-reading each post, and
  kept only the patterns I could verify against the confusion matrix (§6).

*(Disclosure: the Groq `llama-3.3-70b-versatile` model is the **evaluated** zero-shot baseline —
part of the methodology being measured — not an authoring aid.)*

---

## 9. Spec reflection

**How the spec (planning.md) helped:** pre-registering the metric and thresholds was decisive. By
committing *in advance* to **macro-F1 as the headline** and to concrete bars (macro-F1 ≥ 0.70, DD
F1 ≥ 0.65) with an honest "report it if the baseline wins" clause, the disappointing result became
an *interpretable finding* rather than a scramble — accuracy (0.77) looked fine, but the
pre-committed macro-F1 lens correctly exposed the Discussion collapse. The codebook's edge-case
rules likewise kept annotation consistent (0 label conflicts).

**How implementation diverged, and why:** the plan specified collecting via the **Reddit Data API
(PRAW)**, but mid-project Reddit **gated new Data API app registration** behind a moderation-use
review, so self-serve credentials were unavailable. I diverged to Reddit's **public `.rss` feeds**,
which need no authentication and satisfy the "public posts only" rule directly (with rate-limit
backoff). A second divergence: the plan targeted **~70 examples per label**, but genuine Discussion
proved so scarce (mostly megathreads/shitposts) that it capped at **32**; rather than pad it with
low-quality posts, I kept all real data, documented the imbalance, and leaned on the pre-chosen
macro-F1 — the §4 fallback the plan already specified.

---

## 10. Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python collect_data.py          # raw pool via public RSS (no auth)
.venv/bin/python collect_discussion.py    # targeted Discussion oversample
.venv/bin/python build_dataset.py         # merge LLM review -> data/wsb_labeled.csv
# then run the Colab notebook: Sec 1-2 split/tokenize, 3-4 fine-tune (T4 GPU), 5 Groq baseline
```

## Repo map
- [planning.md](planning.md) — community, labels, edge cases, metrics, success criteria, AI plan
- [data/wsb_labeled.csv](data/wsb_labeled.csv) — the single labeled dataset (283 rows)
- [data/edge_cases.csv](data/edge_cases.csv) — difficult cases logged during annotation
- [results/](results/) — baseline, fine-tuned, and error-analysis write-ups
- [decisions/](decisions/) — per-post LLM review labels (audit trail)
- [confusion_matrix.png](confusion_matrix.png), [evaluation_results.json](evaluation_results.json)
