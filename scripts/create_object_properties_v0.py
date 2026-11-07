#!/usr/bin/env python3
"""Object property facts from audited external sources (no LLM, no simulator).

Design and results: docs/object-properties-v0.md

Reads raw ConceptNet and Visual Genome, keeps every piece of evidence, and
decides a value for each (object, field) cell. Each source votes alone. Where
the sources disagree the cell stays a gap. Simulator values are read only by
--score, after the facts are written, so they can't shape the facts.

  (no flag)    map sources, write evidence and cells, run the validator
  --score      noise report against the simulator table, plus a review sheet
"""

from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

CONCEPTNET = Path("data/external/conceptnet/conceptnet-assertions-5.7.0-en-en.tsv")
VISUAL_GENOME = Path("data/external/visual_genome/attributes.json.zip")
OUT = Path("data/developmental_graph/experiments/object_properties_v0")
WORKSHEET = Path("data/developmental_graph/relation_authoring/age_6mo_object_properties_worksheet_v0.csv")
MIN_VG_MENTIONS = 5

# The 55 world objects, listed here so the mapper needn't import the simulator.
OBJECTS = ["ball", "rattle", "block", "doll", "toy car", "ring toy", "balloon", "spoon", "cup", "bowl", "bottle",
           "banana", "cracker", "apple", "sock", "shoe", "hat", "towel", "blanket", "soap", "comb", "toothbrush",
           "key", "book", "phone", "pillow", "pot", "chair", "plate", "glass", "box", "basket", "bag", "jar",
           "bucket", "mug", "tin", "teddy bear", "drum", "orange", "slipper", "mitten", "sponge", "brush", "cushion",
           "fork", "bell", "stool", "watermelon", "beach ball", "rolling pin", "toy truck", "soup can", "tambourine",
           "melon"]
HELD_OUT = {"mug", "tin", "teddy bear", "drum", "orange", "slipper", "mitten", "sponge", "brush", "cushion", "fork",
            "tambourine", "melon"}
FIELDS = ["round_like", "hard", "bouncy", "breakable", "heavy_like", "noisy", "closable"]

# (relation, words, field, value). A word matches a whole token of the end term.
CONCEPTNET_RULES = [
    ("HasProperty", {"round", "spherical", "circular", "cylindrical"}, "round_like", True),
    ("HasProperty", {"square", "rectangular", "flat", "angular"}, "round_like", False),
    ("CapableOf", {"roll"}, "round_like", True),
    ("NotCapableOf", {"roll"}, "round_like", False),
    ("ReceivesAction", {"rolled"}, "round_like", True),
    ("HasProperty", {"hard", "rigid", "solid"}, "hard", True),
    ("HasProperty", {"soft", "fluffy", "squishy", "plush"}, "hard", False),
    ("HasProperty", {"bouncy", "elastic"}, "bouncy", True),
    ("CapableOf", {"bounce"}, "bouncy", True),
    ("NotCapableOf", {"bounce"}, "bouncy", False),
    ("ReceivesAction", {"bounced"}, "bouncy", True),
    ("HasProperty", {"breakable", "fragile", "brittle"}, "breakable", True),
    ("HasProperty", {"unbreakable"}, "breakable", False),
    ("CapableOf", {"break", "shatter"}, "breakable", True),
    ("ReceivesAction", {"broken", "shattered", "smashed"}, "breakable", True),
    ("HasProperty", {"heavy"}, "heavy_like", True),
    ("HasProperty", {"light", "lightweight"}, "heavy_like", False),
    ("HasProperty", {"noisy", "loud"}, "noisy", True),
    ("HasProperty", {"quiet", "silent"}, "noisy", False),
    ("CapableOf", {"rattle", "jingle", "ring", "beep", "clang"}, "noisy", True),
    ("ReceivesAction", {"closed", "opened", "sealed"}, "closable", True),
    ("HasA", {"lid", "cap", "zipper"}, "closable", True),
]

# "light" and "solid" are left out here: on Visual Genome they mostly mean colour.
VISUAL_GENOME_RULES = {
    "round": ("round_like", True), "circular": ("round_like", True), "spherical": ("round_like", True),
    "cylindrical": ("round_like", True), "square": ("round_like", False), "rectangular": ("round_like", False),
    "flat": ("round_like", False), "hard": ("hard", True), "soft": ("hard", False), "fluffy": ("hard", False),
    "plush": ("hard", False), "bouncy": ("bouncy", True), "broken": ("breakable", True),
    "cracked": ("breakable", True), "shattered": ("breakable", True), "fragile": ("breakable", True),
    "heavy": ("heavy_like", True), "lightweight": ("heavy_like", False), "noisy": ("noisy", True),
    "loud": ("noisy", True), "closed": ("closable", True), "sealed": ("closable", True),
}


def conceptnet_evidence() -> list[dict]:
    uris = {f"/c/en/{o.replace(' ', '_')}": o for o in OBJECTS}
    rules = defaultdict(list)
    for rel, words, field, value in CONCEPTNET_RULES:
        rules[rel].append((words, field, value))
    found = []
    with CONCEPTNET.open(encoding="utf-8") as f:
        for line in f:
            _, rel, start, end, meta = line.rstrip("\n").split("\t")
            rel = rel.removeprefix("/r/")
            if rel not in rules:
                continue
            parts = start.split("/")
            obj = uris.get("/".join(parts[:4]))
            # A sense tag other than noun means another word that looks the same.
            if obj is None or (len(parts) > 4 and parts[4] != "n"):
                continue
            tokens = set(end.split("/")[3].split("_"))
            if tokens & {"not", "never", "cannot"}:
                continue
            for words, field, value in rules[rel]:
                if tokens & words:
                    found.append({"source": "conceptnet", "object": obj, "field": field, "value": value,
                                  "weight": json.loads(meta).get("weight", 1.0),
                                  "evidence": f"{rel} {end.split('/')[3]}"})
    return found


def visual_genome_evidence() -> list[dict]:
    wanted = set(OBJECTS)
    counts = Counter()
    with zipfile.ZipFile(VISUAL_GENOME) as z:
        images = json.loads(z.read("attributes.json"))
    for image in images:
        for box in image.get("attributes", []):
            attrs = {a.strip().lower() for a in box.get("attributes", [])} & VISUAL_GENOME_RULES.keys()
            if not attrs:
                continue
            for name in {n.strip().lower() for n in box.get("names", [])} & wanted:
                for a in attrs:
                    counts[(name, a)] += 1
    return [{"source": "visual_genome", "object": o, "field": VISUAL_GENOME_RULES[a][0],
             "value": VISUAL_GENOME_RULES[a][1], "weight": float(n), "evidence": f"attribute {a}"}
            for (o, a), n in sorted(counts.items()) if n >= MIN_VG_MENTIONS]


def votes(evidence: list[dict]) -> dict[tuple[str, str], bool]:
    total = defaultdict(float)
    for e in evidence:
        total[(e["object"], e["field"], e["value"])] += e["weight"]
    out = {}
    for o in OBJECTS:
        for f in FIELDS:
            yes, no = total[(o, f, True)], total[(o, f, False)]
            if yes != no:
                out[(o, f)] = yes > no
    return out


def validate(cells: list[dict]) -> None:
    seen = set()
    for c in cells:
        key = (c["object"], c["field"])
        assert c["object"] in OBJECTS and c["field"] in FIELDS and isinstance(c["value"], bool), c
        assert key not in seen, c
        assert c["sources"], c
        seen.add(key)
    print(f"validator: {len(cells)} cells ok")


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    per_source = {"conceptnet": conceptnet_evidence(), "visual_genome": visual_genome_evidence()}
    for name, ev in per_source.items():
        with (OUT / f"raw_{name}_evidence.jsonl").open("w") as f:
            f.writelines(json.dumps(e) + "\n" for e in ev)
        print(f"{name}: {len(ev)} pieces of evidence")
    decided = {n: votes(ev) for n, ev in per_source.items()}
    cells, conflicts = [], []
    for o in OBJECTS:
        for f in FIELDS:
            said = {n: d[(o, f)] for n, d in decided.items() if (o, f) in d}
            if not said:
                continue
            if len(set(said.values())) > 1:
                conflicts.append({"object": o, "field": f, "said": said})
                continue
            cells.append({"object": o, "field": f, "value": next(iter(said.values())), "sources": sorted(said),
                          "held_out": o in HELD_OUT})
    validate(cells)
    (OUT / "cells.json").write_text(json.dumps({"cells": cells, "conflicts": conflicts}, indent=1))
    total = len(OBJECTS) * len(FIELDS)
    print(f"cells {len(cells)} of {total} ({len(cells) / total:.0%}), held-out {sum(c['held_out'] for c in cells)}, "
          f"conflicts left as gaps {len(conflicts)}")


def score() -> None:
    import create_world_sim_v1 as wv1
    data = json.loads((OUT / "cells.json").read_text())
    evidence = defaultdict(list)
    for name in ("conceptnet", "visual_genome"):
        for line in (OUT / f"raw_{name}_evidence.jsonl").open():
            e = json.loads(line)
            evidence[(e["object"], e["field"])].append(f"{name}: {e['evidence']} ({e['weight']:g}) -> {e['value']}")
    tally = {k: Counter() for k in ("conceptnet", "visual_genome", "both")}
    fields = defaultdict(Counter)
    rows = []
    for c in data["cells"]:
        truth = wv1.table_value(c["object"], c["field"])
        truth = None if truth is None else bool(truth)
        right = truth == c["value"]
        group = "both" if len(c["sources"]) == 2 else c["sources"][0]
        tally[group]["right" if right else "wrong"] += 1
        fields[c["field"]]["right" if right else "wrong"] += 1
        fields[c["field"]][f"said_{c['value']}"] += 1
        rows.append({**c, "sources": "+".join(c["sources"]), "simulator": truth, "agrees": right,
                     "evidence": " | ".join(evidence[(c["object"], c["field"])][:6]), "your_verdict": ""})
    rows.sort(key=lambda r: (r["agrees"], r["object"], r["field"]))
    with (OUT / "review_sheet.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    report = {"by_source": {k: dict(v) for k, v in tally.items()}, "by_field": {k: dict(v) for k, v in fields.items()},
              "right": sum(r["agrees"] for r in rows), "cells": len(rows),
              "base_rate_true": {f: sum(bool(wv1.table_value(o, f)) for o in OBJECTS) / len(OBJECTS) for f in FIELDS}}
    (OUT / "noise_report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    for r in rows:
        if not r["agrees"]:
            print(f"  wrong? {r['object']:<12}{r['field']:<12}said {r['value']!s:<6}sim {r['simulator']!s:<6}{r['evidence'][:90]}")


def worksheet() -> None:
    """A blank sheet for a person to fill: source evidence shown, simulator values left out."""
    meaning = {"round_like": "rolls when pushed", "hard": "hard, not soft", "bouncy": "bounces when dropped",
               "breakable": "breaks when dropped on a hard floor", "heavy_like": "a 6-month-old can't easily push it",
               "noisy": "makes a sound when shaken", "closable": "has a lid or cover that closes it"}
    evidence = defaultdict(list)
    for name in ("conceptnet", "visual_genome"):
        for line in (OUT / f"raw_{name}_evidence.jsonl").open():
            e = json.loads(line)
            evidence[(e["object"], e["field"])].append(f"{name}: {e['evidence']} ({e['weight']:g})")
    WORKSHEET.parent.mkdir(parents=True, exist_ok=True)
    with WORKSHEET.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["object", "field", "question", "source_evidence", "answer_yes_no_unsure"])
        for o in OBJECTS:
            for field in FIELDS:
                w.writerow([o, field, f"{o}: {meaning[field]}?", " | ".join(evidence[(o, field)][:4]), ""])
    print(f"wrote {WORKSHEET}: {len(OBJECTS) * len(FIELDS)} blank answers")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--score", action="store_true")
    p.add_argument("--worksheet", action="store_true")
    cli = p.parse_args()
    if cli.score:
        score()
    elif cli.worksheet:
        worksheet()
    else:
        build()
