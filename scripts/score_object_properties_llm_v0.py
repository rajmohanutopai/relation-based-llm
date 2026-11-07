#!/usr/bin/env python3
"""Turn the blind LLM answers into cells and score them against the simulator.

Report: docs/object-properties-v0.md. Reads raw_answers.json; writes cells.json and
an answers sheet kept apart from the blank worksheet and the hand-written rows.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_world_sim_v1 as wv1  # noqa: E402
from create_object_properties_v0 import FIELDS, HELD_OUT, OBJECTS  # noqa: E402

OUT = Path("data/developmental_graph/experiments/object_properties_llm_v0")
SHEET = Path("data/developmental_graph/relation_authoring/age_6mo_object_properties_llm_answers_v0.csv")
SOURCE = "llm_blind_subagent_claude_opus_5_5"

raw = json.loads((OUT / "raw_answers.json").read_text())
assert set(raw) == set(OBJECTS) and all(set(a) == set(FIELDS) for a in raw.values())
cells, rows = [], []
by_field, wrong = {f: Counter() for f in FIELDS}, []
for o in OBJECTS:
    for f in FIELDS:
        a = raw[o][f]
        sim = wv1.table_value(o, f)
        sim = None if sim is None else bool(sim)
        rows.append({"object": o, "field": f, "answer": a, "source": SOURCE, "held_out": o in HELD_OUT})
        if a == "unsure":
            by_field[f]["unsure"] += 1
            continue
        v = a == "yes"
        cells.append({"object": o, "field": f, "value": v, "sources": [SOURCE], "held_out": o in HELD_OUT})
        by_field[f]["right" if v == sim else "wrong"] += 1
        if v != sim:
            wrong.append((o, f, a, sim))
(OUT / "cells.json").write_text(json.dumps({"source": SOURCE, "cells": cells}, indent=1))
with SHEET.open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
right = sum(c["right"] for c in by_field.values())
print(f"cells {len(cells)} of {len(rows)}; held-out {sum(c['held_out'] for c in cells)}; agree {right} of {len(cells)} = {right / len(cells):.1%}")
for f, c in by_field.items():
    print(f, dict(c))
base = sum(1 for o in OBJECTS for f in FIELDS if raw[o][f] != "unsure" and not wv1.table_value(o, f))
print(f"baseline: answering 'no' to everything would agree on {base} of {len(cells)} = {base / len(cells):.1%}")
for x in wrong:
    print("  ", *x)
(OUT / "noise_report.json").write_text(json.dumps({"cells": len(cells), "agree": right, "by_field": {k: dict(v) for k, v in by_field.items()}, "disagreements": wrong}, indent=1))
