# Fine-tuned results — DistilBERT (distilbert-base-uncased)

Fine-tuned 3-class classifier vs the locked Groq zero-shot baseline. Test set = 43 posts
(15% stratified hold-out of `data/wsb_labeled.csv`). Per-class computed from the confusion
matrix (`confusion_matrix.png`); raw accuracy in `evaluation_results.json`.

## Baseline vs fine-tuned
| Metric | Baseline (Groq 70B, zero-shot) | Fine-tuned (DistilBERT) | Δ |
|--------|------:|------:|------:|
| Accuracy | 0.767 | 0.721 | −0.047 |
| **Macro-F1** | **0.54** | **0.51** | **−0.03** |
| Weighted-F1 | 0.72 | 0.68 | −0.04 |
| Analysis F1 | 0.78 | 0.74 | −0.04 |
| Hype F1 | 0.85 | 0.79 | −0.06 |
| Discussion F1 | 0.00 | 0.00 | 0 |

## Fine-tuned per-class
| Label | Precision | Recall | F1 | Support |
|-------|----------:|-------:|---:|--------:|
| Analysis | 0.62 | 0.94 | 0.74 | 17 |
| Hype | 0.88 | 0.71 | 0.79 | 21 |
| Discussion | 0.00 | 0.00 | 0.00 | 5 |

## Confusion matrix (rows=true, cols=pred)
| true ↓ / pred → | Analysis | Hype | Discussion |
|---|---:|---:|---:|
| Analysis | 16 | 1 | 0 |
| Hype | 6 | 15 | 0 |
| Discussion | 4 | 1 | 0 |

## Verdict (planning.md §6)
Fine-tuning **did not beat the baseline** — it is slightly worse on accuracy and macro-F1 and
never predicts Discussion. Per §6 this is reported honestly as a core result: a 70B model with
strong priors beats DistilBERT fine-tuned on ~200 imbalanced examples.

## Why (investigation — see error_analysis.md)
- **Not label leakage:** 0 duplicate/near-duplicate texts across the dataset (checked).
- **Class imbalance is the root cause:** Discussion = 32 total → ~22 train / 5 test; the model
  emits 0 Discussion predictions (minority collapse).
- **Not an obvious training bug:** the model learns Analysis/Hype; it only abandons the rare class.
- Both models share the failure mode (Analysis over-prediction sink; Discussion collapse), so it
  is a data/task property, not a quirk of one model.

## Caveat
Discussion rests on 5 test posts — its per-class metrics are extremely noisy (§6.1); treat as
directional. Any threshold judgment for Discussion should note this.

## Next lever (not yet applied)
Class-weighted loss / minority oversampling + `metric_for_best_model="f1_macro"` targets the
Discussion=0 collapse directly and is the most promising way to lift macro-F1 above baseline.
