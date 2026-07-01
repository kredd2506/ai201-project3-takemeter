# Baseline results — Groq zero-shot (llama-3.3-70b-versatile)

Zero-shot baseline for the 3-class WSB substance classifier. Locked before fine-tuning;
the fine-tuned DistilBERT must be compared against these (planning.md §6: beat macro-F1 by ≥0.03).

## Setup
- **Model:** `llama-3.3-70b-versatile` (Groq), zero-shot
- **Decoding:** temperature = 0, max_tokens = 20 (deterministic, per §5 protocol)
- **Prompt:** label definitions + decision rules from planning.md; output = label name only
- **Test set:** 43 posts = 15% stratified hold-out of `data/wsb_labeled.csv` (283)
- **Parse rate:** 43 / 43 (0 unparseable)

## Headline
| Metric | Value |
|--------|------:|
| Accuracy | **0.767** |
| Macro-F1 | **0.54** |
| Weighted-F1 | 0.72 |

## Per-class
| Label | Precision | Recall | F1 | Support |
|-------|----------:|-------:|---:|--------:|
| Analysis | 0.67 | 0.94 | 0.78 | 17 |
| Hype | 0.89 | 0.81 | 0.85 | 21 |
| Discussion | 0.00 | 0.00 | 0.00 | 5 |

(The notebook printed placeholder class names `analysis/hot_take/reaction`; by `LABEL_MAP`
those are Analysis/Hype/Discussion respectively. Numbers are scored by integer ID and are correct.)

## Reflection (pre-fine-tuning)
- **Discussion collapses entirely (0.00 on 5)** — the model never predicts it correctly.
- **Analysis is over-predicted** — recall 0.94 but precision 0.67 (~8 false-Analysis calls).
- **Hype is the strongest class** (0.89 / 0.81) — clearest surface signal (bets, positions, emojis).
- Accuracy (0.77) looks fine only because the two common classes dominate — exactly why macro-F1
  is the headline metric (§5).

## Hypothesis to test after fine-tuning
The baseline leans on **surface cues** (tickers, finance jargon, argument-shaped prose) rather than
**dominant function**, so it defaults substantive-sounding posts to Analysis and can't recognize
Discussion (a question/opinion with no worked thesis). **Prediction:** the confusion matrix's
off-diagonal mass concentrates at **Discussion→Analysis** (all 5) plus some **Hype→Analysis**
(the directional-conviction edge). Fine-tuning should raise Analysis precision and give Discussion
nonzero recall, but Discussion stays weakest (only ~5 test / 32 train examples → very noisy).

## Confusion matrix
_TODO: paste the baseline confusion matrix here to confirm/correct the Discussion→Analysis claim._
