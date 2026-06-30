"""
build_dataset.py -- Merge LLM review decisions onto the collected pools and write
the single labeled CSV the notebook consumes.

Inputs (all in the repo):
  data/raw_posts.csv             -- 350-post pool (flair-bootstrapped)
  data/raw_discussion_extra.csv  -- targeted Discussion oversample
  decisions/dec_*.json           -- per-post LLM review (label, changed, confidence, note)

Process (planning.md s4, s7.2):
  - Each post's flair gives a bootstrap label; an LLM (Claude Opus 4.8) then reviewed
    every post against the codebook and produced the decision files.
  - Posts judged out-of-frame (meme/news/AMA/meta/megathread) are dropped (exclude).
  - The 3 in-frame labels (Analysis / Hype / Discussion) are written out.

Outputs:
  data/wsb_labeled.csv  -- columns: text, label, notes, + audit (id,url,flair,
                           original_label, llm_confidence, reviewed_by)
  data/edge_cases.csv   -- the running list of difficult cases (label changed from
                           flair bootstrap, or low LLM confidence) with reasoning

NOTE: reviewed_by is 'llm' -- these are LLM pre-labels + LLM review. Per the
assignment, a human must still review every label (especially edge_cases.csv)
before training; set reviewed_by to 'human' as you confirm rows.
"""

import csv
import glob
import json
import os

RAW = "data/raw_posts.csv"
EXTRA = "data/raw_discussion_extra.csv"
DEC_GLOB = "decisions/dec_*.json"
OUT = "data/wsb_labeled.csv"
EDGE = "data/edge_cases.csv"
KEEP = {"Analysis", "Hype", "Discussion"}


def load_pool():
    pool = {}
    for r in csv.DictReader(open(RAW, encoding="utf-8")):
        pool[r["id"]] = {
            "id": r["id"], "text": r["text"], "title": r["title"],
            "flair": r["flair"], "url": r["url"], "original_label": r["label"],
        }
    if os.path.exists(EXTRA):
        for r in csv.DictReader(open(EXTRA, encoding="utf-8")):
            pool.setdefault(r["id"], {
                "id": r["id"], "text": r["text"], "title": r["title"],
                "flair": r["flair"], "url": r.get("link", ""),
                "original_label": "Discussion",  # extra pool was a Discussion-flair pull
            })
    return pool


def load_decisions():
    dec = {}
    for f in sorted(glob.glob(DEC_GLOB)):
        for d in json.load(open(f, encoding="utf-8")):
            dec[d["id"]] = d
    return dec


def main():
    pool = load_pool()
    dec = load_decisions()

    rows, edges = [], []
    missing = [pid for pid in pool if pid not in dec]
    counts = {}
    for pid, p in pool.items():
        d = dec.get(pid)
        if not d:
            continue
        label = d["label"]
        counts[label] = counts.get(label, 0) + 1
        if label not in KEEP:
            continue
        row = {
            "text": p["text"],
            "label": label,
            "notes": d.get("note", ""),
            "id": pid,
            "url": p["url"],
            "flair": p["flair"],
            "original_label": p["original_label"],
            "llm_confidence": d.get("confidence", ""),
            "reviewed_by": "llm",
        }
        rows.append(row)
        if d.get("changed") or d.get("confidence") == "low":
            edges.append({
                "id": pid, "label": label, "original_label": p["original_label"],
                "llm_confidence": d.get("confidence", ""), "note": d.get("note", ""),
                "title": p["title"][:140], "url": p["url"],
            })

    fields = ["text", "label", "notes", "id", "url", "flair",
              "original_label", "llm_confidence", "reviewed_by"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    efields = ["id", "label", "original_label", "llm_confidence", "note", "title", "url"]
    with open(EDGE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=efields)
        w.writeheader()
        w.writerows(edges)

    kept = sum(1 for r in rows)
    print(f"pool={len(pool)}  decisions={len(dec)}  missing_decision={len(missing)} {missing}")
    print(f"all-label counts (incl exclude): {counts}")
    print(f"\nLABELED DATASET -> {OUT}  ({kept} rows, 3-class)")
    by = {}
    for r in rows:
        by[r["label"]] = by.get(r["label"], 0) + 1
    for k in sorted(by):
        print(f"   {k:11s} {by[k]:4d}  ({100*by[k]/kept:.1f}%)")
    mx = max(by.values()) / kept
    print(f"   max class share = {100*mx:.1f}%  ({'OK <=70%' if mx <= 0.70 else 'IMBALANCE >70%'})")
    print(f"\nEDGE CASES -> {EDGE}  ({len(edges)} rows: label changed from flair or low confidence)")


if __name__ == "__main__":
    main()
