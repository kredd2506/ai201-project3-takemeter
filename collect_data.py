"""
collect_data.py -- Collect and pre-label r/wallstreetbets posts (public RSS).

Why RSS instead of PRAW
-----------------------
planning.md s4 originally specified the Reddit Data API via PRAW. As of mid-2026
Reddit has gated new Data API app registration behind a moderation-use-case review,
so self-serve script credentials are no longer available for this project. Reddit's
public `.rss` feeds, however, are still open and require NO authentication -- they
satisfy the "public posts only, no auth" rule directly. This script uses those.

What it does
------------
- Pulls posts from r/wallstreetbets via public Atom/RSS feeds (no credentials).
- BOOTSTRAP LABELS come from flair-SEARCH feeds: querying `flair:"DD"` returns only
  DD-flaired posts, so every result inherits a known flair -> label mapping
  (planning.md s4). This is the RSS-equivalent of reading each post's flair.
- Adds a few generic listings (hot/new) for natural variety; those have no flair,
  so they are written with an empty bootstrap label for full manual labeling.
- Cleans post bodies out of the feed HTML, dedups by id, writes data/raw_posts.csv.

Rate limits
-----------
Reddit throttles RSS (HTTP 429). We space requests and back off on 429.
A full run takes a few minutes. Be patient; do not hammer it.

After running
------------
Open data/raw_posts.csv and HAND-REVIEW every row against planning.md's codebook.
Flair is sometimes wrong or sarcastic. Fix the `label` column where needed and
log what you changed -- that manual pass is the documented labeling process.
"""

import csv
import html
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ATOM = {"a": "http://www.w3.org/2005/Atom"}
UA = "macos:wsb-classifier:0.1 (academic discourse-classification project)"
OUTPUT_PATH = "data/raw_posts.csv"

# flair (as queried) -> bootstrap label (planning.md s4)
FLAIR_TO_LABEL = {
    "DD": "Analysis",
    "Technical Analysis": "Analysis",
    "YOLO": "Hype",
    "Gain": "Hype",
    "Loss": "Hype",
    "Discussion": "Discussion",
    "Question": "Discussion",
}

# Pull each flair across several sorts/time-windows so we get DISTINCT posts
# (top-of-year overlaps top-of-all heavily; varying the sort diversifies results).
SORTS = ["top", "new", "comments"]
TIMES = ["all", "year"]

# Stop once each bootstrap class has at least this many (headroom for review drops).
TARGET_PER_CLASS = 110
MAX_SELFTEXT_CHARS = 4000


def fetch(url, tries=6):
    """GET a feed, backing off on 429. Returns text or None."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (i + 1)
                print(f"    429 rate-limited, backoff {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"    HTTP {e.code} for {url}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"    error {e} for {url}", file=sys.stderr)
            return None
    return None


def clean_body(content_html):
    """Extract the self-post body text from a feed entry's content HTML."""
    if not content_html:
        return ""
    # Self-post bodies sit between the SC_OFF / SC_ON markers; link/image posts
    # have no such block (just a [link]/[comments] stub + 'submitted by' footer).
    m = re.search(r"<!-- SC_OFF -->(.*?)<!-- SC_ON -->", content_html, re.S)
    body = m.group(1) if m else ""
    body = re.sub(r"<[^>]+>", " ", body)          # strip tags
    body = html.unescape(body)
    body = re.sub(r"\s+", " ", body).strip()
    return body[:MAX_SELFTEXT_CHARS]


def parse_feed(xmltext, flair):
    """Yield post dicts from one feed. `flair` is the queried flair, or None."""
    try:
        root = ET.fromstring(xmltext)
    except ET.ParseError:
        return
    label = FLAIR_TO_LABEL.get(flair, "") if flair else ""
    for e in root.findall("a:entry", ATOM):
        pid = (e.findtext("a:id", default="", namespaces=ATOM) or "").strip()
        title = (e.findtext("a:title", default="", namespaces=ATOM) or "").strip()
        if not pid or not title:
            continue
        link_el = e.find("a:link", ATOM)
        url = link_el.get("href") if link_el is not None else ""
        published = (e.findtext("a:published", default="", namespaces=ATOM) or "").strip()
        content_el = e.find("a:content", ATOM)
        selftext = clean_body(content_el.text if content_el is not None else "")
        text = (title + "\n\n" + selftext).strip()
        yield {
            "id": pid.replace("t3_", ""),
            "published": published,
            "flair": flair or "",
            "title": title,
            "selftext": selftext,
            "text": text,
            "label": label,
            "label_source": "flair" if flair else "",
            "url": url,
        }


def feeds():
    """(flair, url) pairs to fetch, in priority order."""
    base = "https://www.reddit.com/r/wallstreetbets"
    out = []
    # Flair-targeted search feeds (these carry bootstrap labels).
    for flair in FLAIR_TO_LABEL:
        q = urllib.parse.quote(f'flair:"{flair}"')
        for sort in SORTS:
            for t in TIMES:
                url = f"{base}/search.rss?q={q}&restrict_sr=1&sort={sort}&t={t}&limit=25"
                out.append((flair, url))
    # Generic listings for natural variety (no flair -> manual labeling).
    for listing in ["hot", "new", "rising"]:
        out.append((None, f"{base}/{listing}/.rss?limit=25"))
    return out


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    seen = {}
    counts = {"Analysis": 0, "Hype": 0, "Discussion": 0, "": 0}

    for flair, url in feeds():
        # Skip flair feeds whose class is already full (still pull generic feeds).
        if flair:
            cls = FLAIR_TO_LABEL[flair]
            if counts[cls] >= TARGET_PER_CLASS:
                continue
        tag = flair or "listing"
        body = fetch(url)
        added = 0
        if body:
            for row in parse_feed(body, flair):
                if row["id"] in seen:
                    continue
                seen[row["id"]] = row
                counts[row["label"]] += 1
                added += 1
        print(f"  [{tag:18s}] +{added:3d}  totals={ {k:v for k,v in counts.items() if k} }")
        time.sleep(6)  # be polite; avoids most 429s
        if all(counts[c] >= TARGET_PER_CLASS for c in ("Analysis", "Hype", "Discussion")):
            print("  reached target for all classes")
            break

    rows = list(seen.values())
    fields = ["id", "published", "flair", "title", "selftext", "text",
              "label", "label_source", "url"]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"\nWrote {len(rows)} posts to {OUTPUT_PATH}")
    print("Bootstrap label counts:",
          {k: v for k, v in counts.items()})
    print("\nNext: hand-review the `label` column against planning.md before training.")


if __name__ == "__main__":
    main()
