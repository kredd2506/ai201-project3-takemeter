# Demo — TakeMeter fine-tuned classifier

Narration script for the demo video. Shows 5 real r/wallstreetbets posts classified by the
fine-tuned DistilBERT model, with **predicted label + confidence** visible, one correct and one
incorrect prediction narrated, and a walkthrough of the evaluation report. Confidence = max softmax
probability from the fine-tuned model on the held-out test set.

## The 5 posts (all public, linked)

| # | Post (link) | Predicted | Confidence | True | Result |
|---|-------------|-----------|-----------:|------|:------:|
| 1 | [The next Financial Crisis is here…](https://www.reddit.com/r/wallstreetbets/comments/1ucpnbj/the_next_financial_crisis_is_here_and_its_not/) | Analysis | 0.459 | Analysis | ✅ |
| 2 | [Went full retard with my kid's college savings. WEN lambo?](https://www.reddit.com/r/wallstreetbets/comments/1uiy6hq/went_full_retard_with_my_kids_college_savings_wen/) | Hype | 0.429 | Hype | ✅ |
| 3 | [60k in BYND](https://www.reddit.com/r/wallstreetbets/comments/1od94t2/60k_in_bynd/) | Hype | 0.423 | Hype | ✅ |
| 4 | [Betting on BTC to crash by end of week](https://www.reddit.com/r/wallstreetbets/comments/1r8jyc5/betting_on_btc_to_crash_by_end_of_week/) | Analysis | 0.408 | **Hype** | ❌ |
| 5 | [Closed frontiers vs. Open source…](https://www.reddit.com/r/wallstreetbets/comments/1ugp32n/closed_frontiers_vs_open_source_how_can_the_ipos/) | Analysis | 0.428 | **Discussion** | ❌ |

## Narration

**Correct prediction — Post #1 → Analysis (conf 0.459).**
"This post argues that a financial crisis is underway and lays out a reasoned, multi-factor case —
it's not just a bet or a reaction, it's an evidence-backed argument that stands on its own. That's
exactly my definition of **Analysis**, and the model gets it right. Notice the confidence is only
0.46 though — even when correct, the model is barely above the one-in-three random floor, which is a
theme I'll come back to."

**Incorrect prediction — Post #4 → predicted Analysis, actually Hype (conf 0.408).**
"This one the model gets wrong, and it's the most revealing error. The post literally opens with
*'No analysis, this thought came to me in a dream'* and describes buying puts on $COIN and $PLTR
*'purely on vibes.'* By function it's pure **Hype** — an emotional bet with no argument. But it's
packed with tickers and finance words like 'proxy' and 'macro,' and the model latched onto that
surface vocabulary and called it **Analysis**. This is the core failure: the model learned to
classify by *vocabulary and register*, not by *function*. A post can look like DD without being an
argument, and the model can't tell the difference."

(Optional third callout — Post #5 → Analysis, actually Discussion: "This is a genuine open question
to the community about AI IPO valuations — a **Discussion** post. The model never predicts
Discussion at all; because it's the rare class with no distinct vocabulary of its own, argument-
shaped questions like this get absorbed into Analysis.")

## Evaluation-report walkthrough (say over the README §5 tables)

"On a 43-post held-out test set I compared two models on the **same** data:
- A **zero-shot Groq llama-3.3-70B baseline** and a **fine-tuned DistilBERT**.
- Headline metric is **macro-F1**, not accuracy, because the classes are imbalanced and the valuable
  class is the minority — accuracy would hide per-class failure.
- **Results:** the baseline gets macro-F1 **0.54**, the fine-tuned model **0.51** — so fine-tuning
  on ~200 examples actually did slightly *worse* than the big model's zero-shot priors. Accuracy is
  0.77 vs 0.72.
- **Per class:** both models do well on Hype (F1 ~0.79–0.85) and Analysis (~0.74–0.78), but **both
  score 0.00 on Discussion** — neither ever correctly labels it.
- **The confusion matrix** shows why: almost every error flows *into* Analysis — 6 Hype→Analysis and
  4 Discussion→Analysis — and the Discussion column is completely empty. The model has no working
  boundary for the rare class.
- **Root cause** (verified: no label leakage, consistent labels): class imbalance — Discussion is
  only ~11% of the data and collapses — plus the model keying on surface vocabulary instead of
  function. The fix is more Discussion data and/or class-weighted loss, not more epochs."

Full report: [README.md](README.md) §5–§7.
