#!/usr/bin/env python3
"""Hybrid natural episode generator for the age_6mo root graph.

Most low-risk physical concepts are rendered with deterministic templates.
Harder concepts are routed to Gemini only when needed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from generate_age_6mo_gemini_episodes import (
    DEFAULT_MODEL,
    DEFAULT_SEED,
    training_rows,
    validate_episode,
    write_jsonl,
)


DEFAULT_OUTPUT_DIR = Path("data/developmental_graph/experiments/age_6mo_hybrid_episodes_v0")

TEMPLATE_OBJECTS = ["rattle", "ball", "blanket", "block", "soft toy"]
TEMPLATE_PLACES = ["rug", "play mat", "high chair tray", "crib"]
TEMPLATE_FILLERS = ["near the parent", "after a nap", "in the living room", "beside the couch"]

GEMINI_ONLY = [
    "comfort", "pain", "safe touch", "alone", "with caregiver", "not held",
    "body limit", "gone", "back again", "can control", "cannot control",
    "new link", "broken link", "expectation", "surprise mismatch",
    "object permanence precursor", "too much", "enough", "wanted", "not wanted",
]


def load_seed(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def concept_map(seed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["word"]: item for item in seed["concepts"]}


def relation_text(item: dict[str, Any], target: str | None = None, rel_type: str | None = None) -> str:
    for rel in item["relations"]:
        if target is not None and rel["target"] != target:
            continue
        if rel_type is not None and rel["type"] != rel_type:
            continue
        return rel["text"]
    return item["relations"][0]["text"]


def template_episode(item: dict[str, Any], variant: int) -> dict[str, Any] | None:
    word = item["word"]
    obj = TEMPLATE_OBJECTS[variant % len(TEMPLATE_OBJECTS)]
    place = TEMPLATE_PLACES[variant % len(TEMPLATE_PLACES)]
    filler = TEMPLATE_FILLERS[variant % len(TEMPLATE_FILLERS)]
    if word == "near":
        return {
            "concept": word,
            "scene": f"The {obj} sits beside the baby's hand on the {place} {filler}. The hand moves forward and touches it.",
            "question": f"Why can the baby touch the {obj}?",
            "answer": f"The {obj} is near the hand.",
            "hidden_relation": relation_text(item, "touch", "enables"),
            "concepts_used": ["near", "touch"],
        }
    if word == "far":
        return {
            "concept": word,
            "scene": f"The {obj} sits across the room on the {place}. The baby reaches toward it, but the hand cannot touch it.",
            "question": f"Why can the baby not touch the {obj}?",
            "answer": f"The {obj} is too far away.",
            "hidden_relation": relation_text(item, "touch", "prevents"),
            "concepts_used": ["far", "touch"],
        }
    if word == "reach success":
        return {
            "concept": word,
            "scene": f"The {obj} rests right beside the baby's open hand on the {place}. The hand moves forward and grabs it.",
            "question": f"Why does the baby grab the {obj}?",
            "answer": f"The {obj} is near enough to reach.",
            "hidden_relation": relation_text(item, "near", "caused_by"),
            "concepts_used": ["reach", "near"],
        }
    if word == "reach fail":
        return {
            "concept": word,
            "scene": f"The {obj} rests just beyond the baby's fingers on the {place}. The hand stretches forward but does not touch it.",
            "question": f"Why does the baby fail to touch the {obj}?",
            "answer": f"The {obj} is too far to reach.",
            "hidden_relation": relation_text(item, "far", "caused_by"),
            "concepts_used": ["reach", "far"],
        }
    if word == "wet":
        return {
            "concept": word,
            "scene": "Water spills on the baby's bib during a bottle feed. The cloth feels damp against the baby's chest.",
            "question": "Why does the bib feel damp?",
            "answer": "The bib has water on it.",
            "hidden_relation": item["relations"][0]["text"],
            "concepts_used": ["wet"],
        }
    if word == "dry":
        return {
            "concept": word,
            "scene": "A clean towel comes from the laundry basket. The towel touches the baby's skin and has no water on it.",
            "question": "Why does the towel not feel wet?",
            "answer": "The towel has no water on it.",
            "hidden_relation": item["relations"][0]["text"],
            "concepts_used": ["dry"],
        }
    if word == "hot":
        return {
            "concept": word,
            "scene": "The parent checks a warm bottle before feeding. The bottle feels too hot, so it stays away from the baby's mouth.",
            "question": "Why does the bottle stay away?",
            "answer": "The bottle is too hot.",
            "hidden_relation": item["relations"][0]["text"],
            "concepts_used": ["hot"],
        }
    if word == "cold":
        return {
            "concept": word,
            "scene": "A cool wipe touches the baby's leg during a diaper change. The baby kicks and pulls the leg back.",
            "question": "Why does the baby pull the leg back?",
            "answer": "The wipe feels cold on the leg.",
            "hidden_relation": item["relations"][0]["text"],
            "concepts_used": ["cold"],
        }
    return None


def make_row(item: dict[str, Any], episode: dict[str, Any], route: str, index: int, errors: list[str]) -> dict[str, Any]:
    return {
        "id": f"age_6mo_hybrid_episode_v0.{index:04d}.{item['word'].replace(' ', '_')}",
        "route": route,
        "model": "template" if route == "template" else DEFAULT_MODEL,
        "source_concept_id": item["id"],
        "source_concept": item["word"],
        "source_status": item["status"],
        "source_category": item["category"],
        "episode": episode,
        "validation_errors": errors,
        "usage": {},
    }


def write_manifest(path: Path, rows: list[dict[str, Any]], rejected: list[dict[str, Any]], gemini_manifest: dict[str, Any] | None) -> None:
    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": "age_6mo_hybrid_episodes_v0",
        "accepted": len(rows),
        "rejected": len(rejected),
        "template_rows": sum(1 for row in rows if row["route"] == "template"),
        "gemini_rows": sum(1 for row in rows if row["route"] == "gemini"),
        "gemini_manifest": gemini_manifest,
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--template-limit", type=int, default=12)
    parser.add_argument("--template-variants", type=int, default=2)
    parser.add_argument("--gemini-limit", type=int, default=6)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    seed = load_seed(args.seed_path)
    by_word = concept_map(seed)
    template_candidates = [
        "near", "far", "reach success", "reach fail", "wet", "dry", "hot", "cold",
    ][: args.template_limit]

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    index = 1
    for word in template_candidates:
        item = by_word[word]
        for variant in range(args.template_variants):
            episode = template_episode(item, variant)
            if episode is None:
                continue
            errors = validate_episode(episode, item)
            row = make_row(item, episode, "template", index, errors)
            if errors:
                rejected.append(row)
            else:
                accepted.append(row)
            index += 1

    gemini_manifest = None
    if args.gemini_limit:
        gemini_words = [word for word in GEMINI_ONLY if word in by_word][: args.gemini_limit]
        gemini_dir = args.output_dir / "gemini_routed"
        command = [
            "python",
            "scripts/generate_age_6mo_gemini_episodes.py",
            "--limit",
            str(len(gemini_words)),
            "--concepts",
            ",".join(gemini_words),
            "--model",
            args.model,
            "--output-dir",
            str(gemini_dir),
        ]
        subprocess.run(command, check=True)
        gemini_manifest = json.loads((gemini_dir / "manifest.json").read_text(encoding="utf-8"))
        for line in (gemini_dir / "episodes.accepted.jsonl").open("r", encoding="utf-8"):
            row = json.loads(line)
            row["route"] = "gemini"
            accepted.append(row)
        for line in (gemini_dir / "episodes.rejected.jsonl").open("r", encoding="utf-8"):
            row = json.loads(line)
            row["route"] = "gemini"
            rejected.append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "episodes.accepted.jsonl", accepted)
    write_jsonl(args.output_dir / "episodes.rejected.jsonl", rejected)
    write_jsonl(args.output_dir / "training.accepted.jsonl", training_rows(accepted))
    write_manifest(args.output_dir / "manifest.json", accepted, rejected, gemini_manifest)
    print(json.dumps(json.loads((args.output_dir / "manifest.json").read_text(encoding="utf-8")), indent=2))


if __name__ == "__main__":
    main()
