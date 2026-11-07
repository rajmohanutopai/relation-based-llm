#!/usr/bin/env python3
"""Create a conservative first approved source-alias mapping file."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


DEFAULT_INPUT = Path("data/developmental_graph/experiments/seed_embedding_source_audit_all_v0/source_mapping_review.csv")
DEFAULT_OUTPUT = Path("data/developmental_graph/source_aliases/age_6mo_source_aliases_v0.csv")

MANUAL_SAFE = {
    ("attached", "attachedness"),
    ("avoidance", "avoidance"),
    ("avoidance", "avoidances"),
    ("breakable", "breakableness"),
    ("breakable", "breakable"),
    ("calm", "calmness"),
    ("cause", "cause effect"),
    ("contact", "physical contact"),
    ("hidden", "hiddenness"),
    ("hidden", "the state of being hidden"),
    ("moving", "the act of moving from one place to another"),
    ("moving", "the act of moving something from one location to another"),
    ("safe", "safeness"),
    ("separate", "separateness"),
    ("unfamiliar", "unfamiliarity"),
    ("visible", "visibleness"),
    ("vibration", "of or relating to or characterized by vibration"),
}

BLOCKED_WORDS = {
    "opposite",
    "unrelated",
    "wrong",
}

GENERIC_SEEDS = {
    "thing",
    "state",
    "same",
    "different",
    "more",
    "less",
    "one",
    "many",
    "up",
    "down",
    "left",
    "right",
    "there",
    "here",
}


def norm(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z' ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_simple_morph(seed: str, candidate: str) -> bool:
    seed = norm(seed)
    candidate = norm(candidate)
    forms = {
        seed,
        f"{seed}s",
        f"{seed}es",
        f"{seed}ness",
        f"{seed}ing",
        f"{seed}ed",
    }
    if seed.endswith("e"):
        forms.add(f"{seed[:-1]}ing")
    return candidate in forms


def is_blocked(seed: str, candidate: str) -> bool:
    candidate_norm = norm(candidate)
    if (" or " in candidate_norm or " and " in candidate_norm) and candidate_norm != seed:
        return True
    if any(word in candidate_norm.split() for word in BLOCKED_WORDS):
        return True
    if seed == "right" and "left" in candidate_norm:
        return True
    if seed == "left" and "right" in candidate_norm:
        return True
    if seed != "no support" and seed != "no contact" and candidate_norm.startswith("no "):
        return True
    return False


def approval_reason(row: pd.Series) -> str | None:
    seed = norm(row["seed_word"])
    candidate = norm(row["candidate_phrase"])
    score = float(row["embedding_score"])
    if is_blocked(seed, candidate):
        return None
    if (seed, candidate) in MANUAL_SAFE:
        return "manual_safe"
    if is_simple_morph(seed, candidate):
        return "simple_morph"
    if seed not in GENERIC_SEEDS and score >= 0.72 and seed in candidate:
        return "high_score_contains_seed"
    if seed not in GENERIC_SEEDS and score >= 0.74 and candidate in seed:
        return "high_score_candidate_in_seed"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-per-seed", type=int, default=4)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    approved_rows = []
    counts: Counter[str] = Counter()
    candidate_targets: dict[str, str] = {}
    for _, row in df.sort_values("embedding_score", ascending=False).iterrows():
        seed = row["seed_word"]
        candidate = norm(row["candidate_phrase"])
        if candidate in candidate_targets and candidate_targets[candidate] != seed:
            continue
        if counts[seed] >= args.max_per_seed:
            continue
        reason = approval_reason(row)
        if not reason:
            continue
        output = row.to_dict()
        output["approved"] = "yes"
        output["approved_target"] = seed
        output["review_notes"] = reason
        approved_rows.append(output)
        counts[seed] += 1
        candidate_targets[candidate] = seed

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "seed_word",
        "seed_category",
        "candidate_phrase",
        "sources",
        "embedding_score",
        "approved",
        "approved_target",
        "review_notes",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in approved_rows:
            writer.writerow({field: row.get(field, "") for field in fields})

    print({
        "input": str(args.input),
        "output": str(args.output),
        "approved_rows": len(approved_rows),
        "approved_seed_concepts": len(counts),
        "top_reasons": Counter(row["review_notes"] for row in approved_rows).most_common(),
    })


if __name__ == "__main__":
    main()
