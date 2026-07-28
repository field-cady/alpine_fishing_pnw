"""Merge every data/state_lakes_<code>.jsonl into data/all_states.json.

Since each state scraper now emits the common, already-normalized schema (see
``scrapers/base.py``), merging is just concatenation + a timestamp. The result
is what the frontend (``all_scripts.js``) loads.
"""

import glob
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def merge_datasets():
    all_lakes = []
    paths = sorted(glob.glob(os.path.join(DATA_DIR, "state_lakes_*.jsonl")))
    if not paths:
        print("No state_lakes_*.jsonl files found. Run scrape_all.py first.")

    for path in paths:
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                all_lakes.append(json.loads(line))
                count += 1
        print(f"Loaded {count} lakes from {os.path.basename(path)}")

    output = {
        "lakes": all_lakes,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    out_path = os.path.join(DATA_DIR, "all_states.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f)

    print(f"Merged {len(all_lakes)} total lakes -> {out_path}")


if __name__ == "__main__":
    merge_datasets()
