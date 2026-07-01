# r/wallstreetbets Post Classifier — Substance vs. Hype vs. Discussion

A 3-class text classifier that sorts r/wallstreetbets posts by their **dominant function**:

- **Analysis** — an evidence-based argument about a stock/trade that would stand on its own even
  if you stripped out the poster's position.
- **Hype** — a reactive, low-substance post centered on the poster's own bet, outcome, or emotion,
  or a pure rally cry.
- **Discussion** — a post that opens a topic to the community (question, opinion/PSA, call to
  action) without a worked thesis or a personal bet at its center.

Label design, edge cases, and methodology are in [planning.md](planning.md). This README is the
**evaluation report**.

## Dataset

283 hand-reviewed posts collected from public Reddit `.rss` feeds (no auth), flair-bootstrapped
then LLM-reviewed against the codebook (see [planning.md §7.2](planning.md)). One file,
[data/wsb_labeled.csv](data/wsb_labeled.csv); the notebook does the 70/15/15 stratified split.

| Label | Count | Share |
|-------|------:|------:|
| Hype | 141 | 49.8% |
| Analysis | 110 | 38.9% |
| Discussion | 32 | 11.3% |
| **Total** | **283** | |

No class exceeds 70%, but **Discussion is a genuine minority** — even a targeted oversample of
Discussion-flaired posts yielded mostly megathreads/shitposts (only ~6 of 23 were real
Discussion). This imbalance drives the results below.

## Models compared

- **Baseline:** Groq `llama-3.3-70b-versatile`, zero-shot, temperature 0, prompt = the label
  definitions from planning.md (output = label name only).
- **Fine-tuned:** `distilbert-base-uncased`, fine-tuned on the training split.

Both evaluated **once** on the same 43-post stratified test set (Analysis 17 / Hype 21 /
Discussion 5). Headline metric is **macro-F1** (planning.md §5) because the valuable class is the
minority one and accuracy hides per-class failure.

## Results

### Overall
| Metric | Baseline (Groq 70B) | Fine-tuned (DistilBERT) | Δ |
|--------|------:|------:|------:|
| Accuracy | 0.767 | 0.721 | −0.047 |
| **Macro-F1** | **0.54** | **0.51** | **−0.03** |
| Weighted-F1 | 0.72 | 0.68 | −0.04 |

### Per-class (precision / recall / F1, support)
| Label | Baseline P | Baseline R | Baseline F1 | Fine-tuned P | Fine-tuned R | Fine-tuned F1 | Support |
|-------|-----------:|-----------:|------------:|-------------:|-------------:|--------------:|--------:|
| Analysis | 0.67 | 0.94 | 0.78 | 0.62 | 0.94 | 0.74 | 17 |
| Hype | 0.89 | 0.81 | 0.85 | 0.88 | 0.71 | 0.79 | 21 |
| Discussion | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 5 |

### Fine-tuned confusion matrix (test set)
Rows = true label, columns = predicted label.

| true ↓ / pred → | Analysis | Hype | Discussion | total |
|-----------------|---------:|-----:|-----------:|------:|
| **Analysis**    | 16 | 1 | 0 | 17 |
| **Hype**        | 6 | 15 | 0 | 21 |
| **Discussion**  | 4 | 1 | 0 | 5 |
| **predicted**   | 26 | 17 | 0 | 43 |

(Also rendered in [confusion_matrix.png](confusion_matrix.png). The notebook printed placeholder
class names `analysis/hot_take/reaction`; by `LABEL_MAP` those are Analysis/Hype/Discussion.)

### Verdict against success criteria (planning.md §6)
- Macro-F1 ≥ 0.70 target: **not met** (baseline 0.54, fine-tuned 0.51).
- Fine-tuned beats baseline by ≥ 0.03: **not met** — fine-tuning was slightly **worse**.
- This is reported honestly as a **core result**, which planning.md §6 anticipated: *a 70B model
  with strong priors plausibly wins over DistilBERT fine-tuned on only ~200 imbalanced examples.*

### Sample classifications (fine-tuned model)

Five test posts run through the fine-tuned model, with predicted label and confidence
(max softmax probability). ✓ = correct, ✗ = wrong.

| Post (excerpt) | Predicted | Confidence | True | |
|----------------|-----------|-----------:|------|---|
| "The next Financial Crisis is here … it's not just an AI bubble, it's a systemic collapse" | Analysis | 0.459 | Analysis | ✓ |
| "Went full retard with my kid's college savings. WEN lambo?" | Hype | 0.429 | Hype | ✓ |
| "60k in BYND" | Hype | 0.423 | Hype | ✓ |
| "Betting on BTC to crash by end of week. No analysis, this thought came to me in a dream. Puts on $COIN … purely on vibes" | Analysis | 0.408 | Hype | ✗ |
| "Closed frontiers vs. Open source. How can the IPOs be justified by investors pouring in billions?" | Analysis | 0.428 | Discussion | ✗ |

**Why the correct ones are reasonable:**
- The **Analysis** prediction is right because the post builds a reasoned systemic-risk argument
  (a thesis with supporting reasoning that stands on its own) — exactly the evidence-based-argument
  signal the Analysis label is defined by.
- The **"kid's college savings … WEN lambo?"** → **Hype** is right because it's a reckless personal
  bet with a lambo/moon meme and zero reasoning — the textbook Hype pattern (own bet + emotion, no
  argument).

**Two things these samples expose:**
1. **Confidence is uniformly low (~0.40–0.46), barely above the 0.33 three-class random floor.**
   The model is uncertain and poorly calibrated even when correct — unsurprising given only ~200
   training examples. Confidence is therefore not a reliable filter here.
2. **The failures are confident-looking in the same range as the successes** (the BTC "no analysis"
   post scores 0.408 for Analysis; the open-source question 0.428). The model can't separate right
   from wrong by confidence, reinforcing that it classifies on surface vocabulary, not function.

## Error analysis (fine-tuned model)

**Process:** exported all 12 misclassified test posts, used an LLM (Claude Opus 4.8) to surface
candidate patterns, then verified each by re-reading the posts — correcting/discarding the ones
that didn't hold. Full write-up: [results/error_analysis.md](results/error_analysis.md);
rows: [results/misclassified_finetuned.csv](results/misclassified_finetuned.csv).

### Which labels are confused? (directional pattern)
**10 of 12 errors flow *into* Analysis:** 6 Hype→Analysis and 4 Discussion→Analysis. Only 2 go the
other way (1 Analysis→Hype, 1 Discussion→Hype), and **Discussion is never predicted at all** (its
column is empty). So the model has learned Analysis and Hype but has **no working boundary for
Discussion**, and it defaults ambiguous posts to Analysis.

### Three specific failures, and *why* each failed

**1. Hype → Analysis — "Betting on BTC to crash by end of week"** (len 399)
> *"No analysis, this thought came to me in a dream. Puts on $COIN because it's a BTC proxy, puts
> on $PLTR because I don't like the stock™ … purely on vibes, one last YOLO."*
- **Why it failed:** the post *literally states it has no analysis*, but the tickers ($COIN, $PLTR),
  "proxy," and "macro events" are surface features the model associates with Analysis. It classifies
  on **vocabulary, not function**. This is the single clearest piece of evidence that the model
  keys on surface cues over meaning.
- **Labeling or data problem?** Data. The label is unambiguously Hype and consistent with similar
  YOLO posts. The model simply never learned that ticker/jargon presence ≠ argument.

**2. Discussion → Analysis — silver "META THREAD" rant** (len 4161)
> *"WHY YOU SHOULD NOT FALL FOR ALL THE SILVER SCAMS!!! … THIS IS A META THREAD IN WHICH I'M JUST
> DOING 2 THINGS: RANTING AND LINKING TO OTHER DD THREADS…"*
- **Why it failed:** it's long, finance-heavy, and argument-*shaped*, so it looks like DD — but its
  actual function is a rant/PSA that opens a topic and points at *other people's* analyses. The
  model can't tell "argues a thesis" from "rants about a topic," and Discussion is so rare in
  training (~22 examples) it has no representation to fall back on.
- **Labeling or data problem?** Data / class imbalance. Discussion is 11% of the set and collapses
  entirely; the boundary is under-trained, not mislabeled.

**3. Analysis → Hype — "Yen Tsunami Coming"** (len 309)
> *"Japan's finance minister said they'd shore up the yen … that most likely means they sell US
> treasuries (a $1.21T position). If they sell, what's your next move? I will be buying UVXY calls."*
- **Why it failed:** the opposite error, and instructive. It's **short**, states a real causal
  chain, but ends with a personal position ("buying UVXY calls") and a question. With little
  surrounding jargon and a visible bet, the model tips it to Hype. Short posts lose the "Analysis"
  surface signal, and a stated position looks like Hype.
- **Labeling or data problem?** Partly the **boundary itself** — this genuinely sits on the
  Analysis↔Hype edge (a real thesis *plus* a bet *plus* a question), the exact hard case in
  planning.md §3. Reasonable annotators could disagree; the model's call is defensible.

### Why is that boundary hard?
The distinguishing signal is **function, not surface**: a WSB post can carry tickers, TA, and
valuation words whether it's arguing (Analysis), betting (Hype), or asking (Discussion). Sarcasm
and self-aware shitposting make it worse — "the TA Gods spoke to me in my sleep" and "came to me
in a dream" are Hype tells the model reads literally. **Length is a weak secondary factor** (I
initially hypothesized long posts fail, but the →Analysis errors span 367–4301 chars — I corrected
this; jargon + argument-shape is the real driver). Short, low-information posts are where the model
flips *away* from Analysis toward Hype.

### Labeling problem or data/prompt problem?
**Data/boundary problem, not annotation inconsistency.** I checked the dataset: 0 duplicate or
near-duplicate texts, 0 IDs mapped to two labels, and similar posts are labeled consistently. So
the model's errors aren't caused by contradictory labels — they come from (a) Discussion being too
rare to learn (minority collapse: 0 predictions), and (b) the intrinsic function-vs-surface
boundary. On re-reading, ~2–3 of the 12 "errors" are genuinely debatable boundary cases (e.g. Yen
Tsunami; a $10k-bailout *opinion* that also argues), so the true error rate is marginally better
than 12/43.

### What would need to change to fix it?
1. **More Discussion examples** — the highest-leverage fix. At ~22 training examples the class
   collapses; it needs enough real (non-megathread) Discussion posts to be learnable. Genuine
   Discussion is scarce on WSB, so this likely means broadening sources or accepting the limit.
2. **Class-weighted loss / minority oversampling** + `metric_for_best_model="f1_macro"` — directly
   attacks the Discussion=0 collapse without new data; the most promising immediate lever.
3. **Harder, more diverse boundary examples in training** — explicitly include "jargon-heavy but
   not an argument" (Hype) and "argument-shaped rant/opinion" (Discussion) so the model learns
   function over vocabulary.
4. **More training data overall** — ~200 examples is very small to beat a 70B model's priors.

## Reflection: what I intended to capture vs. what the model captured

**What the labels were designed to capture — function, not vocabulary.** The taxonomy is defined
by a post's *dominant pragmatic function*: does it *make an argument that stands on its own*
(Analysis), *express a bet/emotion* (Hype), or *open a topic without a thesis or bet* (Discussion)?
The codebook deliberately separates **substance from surface** — "would this stand as an argument
if you stripped out the poster's position and screenshot?" A post loaded with tickers and TA can
still be Hype; a plain-language question can be Discussion. That distinction is what makes the task
interesting, and humans can apply it consistently (the annotation had no label conflicts).

**What the model's decision boundary actually captures — lexical register.** With ~200 examples,
the model learned the easiest available correlate of the labels: **topical/structural vocabulary**.
Its effective rule is closer to *"does this read like finance-argument prose (tickers, valuation
words, TA, structured reasoning)? → Analysis; does it read like a bet/meme (YOLO, lambo, positions,
emojis, '$X into Y')? → Hype."* That correlates with function often enough to score ~0.79–0.85 F1
on the two common classes, because Analysis and Hype happen to have distinct registers.

**What it overfit to.** The surface correlation between *finance-argument register* and the
Analysis label — to the point of ignoring explicit content. It labeled "*No analysis, this came to
me in a dream … puts on $COIN*" as Analysis, and a conspiracy "theory" and a rant that merely
*links to* other people's DD as Analysis. Vocabulary and prose-shape became the signal; the actual
function became invisible. It also picked up register-adjacent cues (length, "DD/thesis/play"
words) rather than reasoning.

**What it missed.**
- **The substance-vs-stance distinction itself** — the core thing the project set out to learn. It
  cannot tell a real argument from argument-*shaped* hype, which is exactly the hard edge (§3) the
  labels were built around.
- **Discussion, entirely (0 predictions).** This is the deepest lesson: Discussion is defined
  largely by *absence* — no worked thesis, no personal bet — and by pragmatic intent (opening a
  topic). It has **no positive lexical signature** distinct from Analysis, so a feature-driven
  boundary trained on ~22 examples never carves out a region for it; those posts fall into whichever
  register they most resemble (usually Analysis).
- **Irony and self-aware framing** ("the TA Gods spoke to me in my sleep"), the very cues a human
  uses to catch hype dressed as DD.

**The gap, stated plainly.** My labels are *semantically clean and human-learnable* but *not
surface-separable at this data scale*. The model didn't learn a worse version of my boundary — it
learned a **different, shallower boundary** (register) that happens to overlap with mine on the easy
cases and diverges exactly on the hard ones. Notably the 70B zero-shot baseline shows the *same*
directional gap (everything → Analysis, Discussion collapses), which says this is partly intrinsic
to the task: classes defined by *absence* and *function* are structurally hard for text classifiers
that key on the *presence* of features. Closing the gap needs either many more (and more diverse)
examples that pin the function-vs-surface boundary explicitly — especially for Discussion — or a
reframing of the taxonomy so each class has a positive, learnable signal.

## Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python collect_data.py          # collect raw pool via public RSS (no auth)
.venv/bin/python collect_discussion.py    # targeted Discussion oversample
.venv/bin/python build_dataset.py         # merge LLM review -> data/wsb_labeled.csv
# then run the Colab notebook (Sections 1-2 split/tokenize, 3-4 fine-tune, 5 Groq baseline)
```

## Repo map
- [planning.md](planning.md) — community, labels, edge cases, metrics, success criteria, AI plan
- [data/wsb_labeled.csv](data/wsb_labeled.csv) — the single labeled dataset (283 rows)
- [data/edge_cases.csv](data/edge_cases.csv) — difficult cases logged during annotation
- [results/](results/) — baseline, fine-tuned, and error-analysis write-ups
- [decisions/](decisions/) — per-post LLM review labels (audit trail)

## AI usage
Disclosed in [planning.md §7.4](planning.md): AI (Claude Opus 4.8) helped refine the label
taxonomy, stress-test labels, pre-label + review annotations (155/373 labels changed on review),
and cluster misclassification patterns (verified by hand). The Groq `llama-3.3-70b-versatile`
model is the *evaluated* zero-shot baseline, not an authoring aid.
