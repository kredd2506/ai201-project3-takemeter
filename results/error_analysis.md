# Error analysis — fine-tuned DistilBERT (test set)

**Method (planning.md §7.3):** exported the 12 misclassified test posts (of 43), had an LLM
(Claude Opus 4.8) surface candidate patterns, then **verified each pattern by re-reading the
actual posts**. Patterns that did not hold on re-reading were corrected or discarded (below).
Misclassified rows: `results/misclassified_finetuned.csv`.

## Error breakdown (from the confusion matrix)
12 errors / 43: **6 Hype→Analysis, 4 Discussion→Analysis, 1 Discussion→Hype, 1 Analysis→Hype.**
10 of 12 errors flow *into* Analysis.

## Confirmed patterns
1. **"Analysis" is an over-prediction sink (10/12).** The model tags argument-shaped or
   jargon-heavy posts as Analysis regardless of true function. Smoking gun: the BTC-crash post
   literally says *"No analysis, this thought came to me in a dream … purely on vibes"* yet the
   tickers ($COIN/$PLTR) + "proxy"/"macro" got it labeled Analysis. Surface cues override meaning.
2. **Discussion has no functional representation (5/5 Discussion wrong).** Rants/PSAs/opinion
   proposals (sub-history rant, silver "META THREAD," $10k-bailout proposal) sound like arguments
   → routed to Analysis. This is the imbalance-driven class collapse (~22 train examples) at the
   example level.
3. **Sarcasm / ironic "hot-take" framing missed** (secondary): beard-bet TA, Blue-Origin
   conspiracy, dream/vibes YOLO. The model reads the argument-shaped surface literally. A symptom
   of pattern 1, not an independent driver.

## Corrected / discarded on verification
- **"Errors cluster by length" — CORRECTED.** The →Analysis errors span 367–4301 chars (includes
  short ones), so length is not the driver; **jargon + argument-shape** is. Length only shows up
  weakly at the bottom end: the two →Hype errors (77, 309 chars) are the shortest, where there is
  too little jargon to trigger the Analysis sink.
- **"Symmetric Analysis↔Hype confusion" — DISCARDED.** The confusion is asymmetric: almost
  everything flows into Analysis, not both directions.

## Self-critique — ~2–3 "errors" are debatable gold labels, not clean model failures
- **"Yen Tsunami"** (gold Analysis / pred Hype): real causal chain (Japan sells $1.21T treasuries
  → buy UVXY) but ends with a personal position + a question — Analysis vs Hype genuinely close.
- **"$10k bailout"** and **"open-source vs closed"** (gold Discussion / pred Analysis): both argue
  a point while opening a topic — the Discussion↔Analysis fuzziness documented in §3.
- Data-quality note: "open-source vs closed" is an image post with garbled OCR text ("Al", "iust").

So a few "errors" reflect inherent boundary ambiguity + label noise rather than pure model failure;
the honest true-error rate is slightly better than 12/43.

## Relation to the pre-registered hypothesis (§7.3.1)
Confirms it: the baseline's predicted **Discussion/Hype → Analysis via surface cues** is exactly
what the fine-tuned model does too. Both models share the failure mode — Analysis is the sink,
Discussion collapses — so it is a task/data property (rare, function-not-surface class), not a
quirk of one model.
