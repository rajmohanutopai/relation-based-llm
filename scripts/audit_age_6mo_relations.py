#!/usr/bin/env python3
"""Machine audit of the 6mo hand-written relation rows. Reads only; changes no row or status.

Report: docs/age-6mo-relation-audit-v0.md

  (no flag)      print checks, write findings to the output folder
  --sample N     also write a fixed random sample for reading
"""

from __future__ import annotations

import argparse
import glob
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

ROWS = "data/developmental_graph/relation_authoring/age_6mo_handwritten_relations_v0/*.jsonl"
STATUS = Path("data/developmental_graph/relation_authoring/age_6mo_relation_authoring_status_v0.json")
OUT = Path("data/developmental_graph/experiments/age_6mo_relation_audit_v0")
REQUIRED = ["id", "age_level", "batch_id", "domain", "subject", "relation", "object", "polarity", "confidence",
            "source_type", "supporting_relations", "plain_text"]
OPPOSITES = {"can_do": "cannot_do", "can_be_seen": "cannot_be_seen", "causes_comfort": "causes_discomfort",
             "causes_happiness": "causes_sadness", "increases": "reduces", "allows": "prevents", "causes": "prevents"}
# Labels from the project's own theory or adult psychology, which a row of infant
# experience can't observe directly.
THEORY = re.compile(r"relation|object_permanence|prediction|memory|attention|happiness|sadness|recognition|learning")


def stem(word: str) -> str:
    w = word.lower()
    for tail in ("ing", "ed", "es", "s"):
        if w.endswith(tail) and len(w) - len(tail) >= 3:
            return w[: -len(tail)]
    return w


def words(text: str) -> set[str]:
    return {stem(w) for w in re.findall(r"[a-zA-Z]+", text)}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sample", type=int, default=0)
    args = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for f in sorted(glob.glob(ROWS)) for l in open(f)]
    status = json.loads(STATUS.read_text())["concepts"]
    known = {c["word"] for c in status} | {a for c in status for a in c.get("aliases", [])}
    ids = Counter(r.get("id") for r in rows)

    found = defaultdict(list)
    triples = defaultdict(list)
    for r in rows:
        if missing := [k for k in REQUIRED if k not in r]:
            found["missing_field"].append({"id": r.get("id"), "missing": missing})
        triples[(r["subject"], r["relation"], r["object"])].append(r)
        if ids[r["id"]] > 1:
            found["repeated_id"].append(r["id"])
        if not (words(r["subject"]) & words(r["plain_text"])):
            found["text_lacks_subject"].append(r)
        if not (words(r["object"]) & words(r["plain_text"])):
            found["text_lacks_object"].append(r)
        if r["subject"] not in known:
            found["subject_not_a_concept"].append(r)
        if THEORY.search(r["relation"]):
            found["theory_label_relation"].append(r)
        if r["subject"] == r["object"]:
            found["self_link"].append(r)
    for key, group in triples.items():
        if len(group) > 1:
            found["repeated_triple"].append(group)
            if len({g["polarity"] for g in group}) > 1:
                found["same_triple_both_polarities"].append(group)
    for (s, rel, o), group in triples.items():
        if rel in OPPOSITES and (s, OPPOSITES[rel], o) in triples:
            found["opposite_relation_same_pair"].append(group + triples[(s, OPPOSITES[rel], o)])
    wrote = Counter(c["word"] for c in status for _ in range(c["relation_rows_written"]))
    subject_counts = Counter(r["subject"] for r in rows)
    objects = Counter(r["object"] for r in rows)
    report = {
        "rows": len(rows), "batches": len({r["batch_id"] for r in rows}),
        "checks": {k: len(v) for k, v in sorted(found.items())},
        "concepts_marked_reviewed": sum(c["review_status"] != "not_reviewed" for c in status),
        "concepts": len(status), "concepts_with_rows_as_subject": sum(c["word"] in subject_counts for c in status),
        "status_row_count_total": sum(wrote.values()),
        "distinct_subjects": len(subject_counts), "distinct_objects": len(objects),
        "objects_used_once": sum(v == 1 for v in objects.values()),
        "top_subjects": subject_counts.most_common(12), "top_objects": objects.most_common(12),
    }
    # Do the rows join up? Nodes are exact phrases; "yes" is an answer, not a node.
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    real = [r for r in rows if r["object"] != "yes"]
    for r in real:
        parent[find(r["subject"])] = find(r["object"])
    sizes = Counter(find(x) for x in list(parent))
    degree = Counter()
    for r in real:
        degree[r["subject"]] += 1
        degree[r["object"]] += 1
    hub_free = {n: d for n, d in degree.items() if n not in ("baby", "caregiver")}
    report["joining"] = {
        "rows_yes_as_object": len(rows) - len(real),
        "rows_both_ends_are_concepts": sum(r["subject"] in known and r["object"] in known for r in real),
        "nodes": len(degree), "nodes_with_one_row": sum(d == 1 for d in degree.values()),
        "largest_group_share": max(sizes.values()) / len(parent), "groups": len(sizes),
        "median_rows_per_node_without_hubs": sorted(hub_free.values())[len(hub_free) // 2],
    }
    (OUT / "audit_report.json").write_text(json.dumps(report, indent=1))
    (OUT / "audit_findings.json").write_text(json.dumps(found, indent=1))
    print(json.dumps(report, indent=1))
    for name in ("same_triple_both_polarities", "opposite_relation_same_pair"):
        print(f"\n--- {name}")
        for group in found[name][:14]:
            print("  " + " || ".join(f"{g['id'][-6:]} {g['plain_text']}" for g in group[:3]))
    for name in ("text_lacks_subject", "text_lacks_object", "self_link", "subject_not_a_concept"):
        print(f"\n--- {name}")
        for r in random.Random(0).sample(found[name], min(8, len(found[name]))):
            print(f"  {r['id'][-6:]} [{r['subject']} | {r['relation']} | {r['object']}] {r['plain_text']}")
    if args.sample:
        chosen = sorted(random.Random(6).sample(rows, args.sample), key=lambda r: r["id"])
        (OUT / "sample.jsonl").write_text("".join(json.dumps(r) + "\n" for r in chosen))
        for r in chosen:
            print(f"{r['id'][-6:]}\t{r['domain']}\t{r['confidence'][0]}\t{r['polarity'][0]}\t{r['relation']}\t{r['plain_text']}")


if __name__ == "__main__":
    main()
