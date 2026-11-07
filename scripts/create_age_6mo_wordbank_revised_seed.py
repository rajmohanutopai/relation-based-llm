#!/usr/bin/env python3
"""Create a Wordbank-informed revision of the age_6mo seed vocabulary."""

from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("data/developmental_graph/seeds/age_6mo_root_world_500.json")
DEFAULT_OUTPUT = Path("data/developmental_graph/seeds/age_6mo_root_world_wordbank_v1.json")

ALIASES = {
    "belly": ["tummy"],
    "bath water": ["bath", "bathtub"],
    "caregiver": ["grownup", "adult"],
    "father": ["daddy", "dad", "papa"],
    "feeding starts": ["eat", "eating"],
    "gone": ["all gone"],
    "grandfather": ["grandpa"],
    "grandmother": ["grandma"],
    "mother": ["mommy", "mama", "mom"],
    "sleep onset": ["night night", "bedtime"],
    "soft toy": ["teddybear", "teddy bear", "stuffed animal"],
    "toy": ["toy object", "plaything"],
    "water": ["water beverage", "drink beverage"],
}

NEW_CONCEPTS = [
    {
        "word": "bye",
        "category": "sound_language_precursor",
        "kind": "language_precursor",
        "summary": "social leaving sound or word",
        "domains": ["social", "language", "sound_language_precursor"],
        "prerequisites": ["voice", "person"],
        "relations": [
            {"type": "social_signal", "target": "person", "text": "bye is a social sound to a person", "strength": 0.72, "valence": "neutral"},
            {"type": "linked_to", "target": "away", "text": "bye often links to going away", "strength": 0.68, "valence": "neutral"},
        ],
    },
    {
        "word": "hi",
        "aliases": ["hello"],
        "category": "sound_language_precursor",
        "kind": "language_precursor",
        "summary": "social greeting sound or word",
        "domains": ["social", "language", "sound_language_precursor"],
        "prerequisites": ["voice", "person"],
        "relations": [
            {"type": "social_signal", "target": "person", "text": "hi is a social sound to a person", "strength": 0.72, "valence": "positive"},
            {"type": "linked_to", "target": "near", "text": "hi often happens when a person is near", "strength": 0.64, "valence": "neutral"},
        ],
    },
    {
        "word": "no",
        "aliases": ["don't"],
        "category": "sound_language_precursor",
        "kind": "language_precursor",
        "summary": "stop or blocked-action social word",
        "domains": ["social", "language", "sound_language_precursor"],
        "prerequisites": ["voice", "blocked access"],
        "relations": [
            {"type": "blocks", "target": "event", "text": "no can block an event", "strength": 0.76, "valence": "neutral"},
            {"type": "linked_to", "target": "bad", "text": "no can mark a bad or unsafe action", "strength": 0.6, "valence": "negative"},
        ],
    },
    {
        "word": "yes",
        "category": "sound_language_precursor",
        "kind": "language_precursor",
        "summary": "allow or confirm social word",
        "domains": ["social", "language", "sound_language_precursor"],
        "prerequisites": ["voice", "good"],
        "relations": [
            {"type": "allows", "target": "event", "text": "yes can allow an event", "strength": 0.7, "valence": "positive"},
            {"type": "linked_to", "target": "good", "text": "yes can mark okay or good", "strength": 0.62, "valence": "positive"},
        ],
    },
    {
        "word": "uh oh",
        "category": "sound_language_precursor",
        "kind": "language_precursor",
        "summary": "sound linked to a small problem or surprise",
        "domains": ["sound", "language", "sound_language_precursor"],
        "prerequisites": ["sound", "attention"],
        "relations": [
            {"type": "linked_to", "target": "attention", "text": "uh oh can change attention", "strength": 0.72, "valence": "neutral"},
            {"type": "linked_to", "target": "bad", "text": "uh oh can mark a small bad change", "strength": 0.58, "valence": "negative"},
        ],
    },
    {
        "word": "kiss",
        "category": "body_action_control",
        "kind": "action",
        "summary": "mouth touch used as a social comfort action",
        "domains": ["body", "social", "body_action_control"],
        "prerequisites": ["mouth", "touch"],
        "relations": [
            {"type": "uses", "target": "mouth", "text": "kiss uses mouth", "strength": 0.74, "valence": "neutral"},
            {"type": "linked_to", "target": "comfort", "text": "kiss can link to comfort", "strength": 0.68, "valence": "positive"},
        ],
    },
    {
        "word": "baby",
        "aliases": ["child"],
        "category": "caregiver_social",
        "kind": "social_relation",
        "summary": "small young person, often the self in the 6mo setup",
        "domains": ["social", "self", "caregiver_social"],
        "prerequisites": ["person", "body"],
        "relations": [
            {"type": "is_a", "target": "person", "text": "baby is a person", "strength": 0.75, "valence": "neutral"},
            {"type": "linked_to", "target": "self", "text": "baby can be linked to self", "strength": 0.7, "valence": "neutral"},
        ],
    },
    {
        "word": "shoe",
        "category": "common_object",
        "kind": "object",
        "summary": "object worn on foot",
        "domains": ["object", "body", "common_object"],
        "prerequisites": ["object", "foot"],
        "relations": [
            {"type": "at_location", "target": "foot", "text": "shoe can be at foot", "strength": 0.74, "valence": "neutral"},
            {"type": "is_a", "target": "object", "text": "shoe is an object", "strength": 0.7, "valence": "neutral"},
        ],
    },
    {
        "word": "sock",
        "category": "common_object",
        "kind": "object",
        "summary": "soft object worn on foot",
        "domains": ["object", "body", "common_object"],
        "prerequisites": ["object", "foot"],
        "relations": [
            {"type": "at_location", "target": "foot", "text": "sock can be at foot", "strength": 0.72, "valence": "neutral"},
            {"type": "has_property", "target": "soft", "text": "sock can be soft", "strength": 0.64, "valence": "neutral"},
        ],
    },
    {
        "word": "hat",
        "category": "common_object",
        "kind": "object",
        "summary": "object worn on head",
        "domains": ["object", "body", "common_object"],
        "prerequisites": ["object", "head"],
        "relations": [
            {"type": "at_location", "target": "head", "text": "hat can be at head", "strength": 0.72, "valence": "neutral"},
            {"type": "is_a", "target": "object", "text": "hat is an object", "strength": 0.7, "valence": "neutral"},
        ],
    },
    {
        "word": "juice",
        "category": "common_object",
        "kind": "object",
        "summary": "drinkable sweet liquid",
        "domains": ["object", "taste", "common_object"],
        "prerequisites": ["drinkable", "taste"],
        "relations": [
            {"type": "has_property", "target": "drinkable", "text": "juice is drinkable", "strength": 0.72, "valence": "neutral"},
            {"type": "linked_to", "target": "sweet", "text": "juice can be sweet", "strength": 0.58, "valence": "positive"},
        ],
    },
    {
        "word": "cracker",
        "aliases": ["cookie", "cheerios", "cereal", "bread", "cheese"],
        "category": "common_object",
        "kind": "object",
        "summary": "small edible food object",
        "domains": ["object", "taste", "common_object"],
        "prerequisites": ["edible", "taste"],
        "relations": [
            {"type": "has_property", "target": "edible", "text": "cracker is edible", "strength": 0.72, "valence": "neutral"},
            {"type": "used_for", "target": "feeding starts", "text": "cracker can be used for feeding", "strength": 0.68, "valence": "neutral"},
        ],
    },
    {
        "word": "cat",
        "aliases": ["kitty", "meow"],
        "category": "common_object",
        "kind": "object",
        "summary": "small animal often seen or heard near people",
        "domains": ["object", "living", "common_object"],
        "prerequisites": ["object", "sound"],
        "relations": [
            {"type": "is_a", "target": "object", "text": "cat is an object in the seen world", "strength": 0.62, "valence": "neutral"},
            {"type": "can_do", "target": "sound", "text": "cat can make sound", "strength": 0.66, "valence": "neutral"},
        ],
    },
    {
        "word": "duck",
        "aliases": ["quack quack"],
        "category": "common_object",
        "kind": "object",
        "summary": "animal or toy animal linked to quack sound",
        "domains": ["object", "sound", "common_object"],
        "prerequisites": ["object", "sound"],
        "relations": [
            {"type": "is_a", "target": "object", "text": "duck is an object in the seen world", "strength": 0.62, "valence": "neutral"},
            {"type": "can_do", "target": "sound", "text": "duck can link to quack sound", "strength": 0.66, "valence": "neutral"},
        ],
    },
    {
        "word": "balloon",
        "category": "common_object",
        "kind": "object",
        "summary": "light round object that can move",
        "domains": ["object", "space", "common_object"],
        "prerequisites": ["object", "round"],
        "relations": [
            {"type": "has_property", "target": "round", "text": "balloon can be round", "strength": 0.7, "valence": "neutral"},
            {"type": "has_property", "target": "light", "text": "balloon can be light", "strength": 0.62, "valence": "neutral"},
        ],
    },
    {
        "word": "car",
        "aliases": ["vroom"],
        "category": "common_object",
        "kind": "object",
        "summary": "moving object linked to ride and vroom sound",
        "domains": ["object", "motion", "common_object"],
        "prerequisites": ["object", "moving"],
        "relations": [
            {"type": "can_do", "target": "move", "text": "car can move", "strength": 0.7, "valence": "neutral"},
            {"type": "linked_to", "target": "sound", "text": "car can link to sound", "strength": 0.58, "valence": "neutral"},
        ],
    },
    {
        "word": "key",
        "aliases": ["keys"],
        "category": "common_object",
        "kind": "object",
        "summary": "small hard household object",
        "domains": ["object", "common_object"],
        "prerequisites": ["object", "hard"],
        "relations": [
            {"type": "has_property", "target": "hard", "text": "key can be hard", "strength": 0.66, "valence": "neutral"},
            {"type": "is_a", "target": "object", "text": "key is an object", "strength": 0.7, "valence": "neutral"},
        ],
    },
    {
        "word": "telephone",
        "aliases": ["phone"],
        "category": "common_object",
        "kind": "object",
        "summary": "household object linked to voice or sound",
        "domains": ["object", "sound", "common_object"],
        "prerequisites": ["object", "sound"],
        "relations": [
            {"type": "linked_to", "target": "voice", "text": "telephone can link to voice", "strength": 0.6, "valence": "neutral"},
            {"type": "is_a", "target": "object", "text": "telephone is an object", "strength": 0.7, "valence": "neutral"},
        ],
    },
    {
        "word": "toothbrush",
        "category": "common_object",
        "kind": "object",
        "summary": "small object used near mouth",
        "domains": ["object", "body", "common_object"],
        "prerequisites": ["object", "mouth"],
        "relations": [
            {"type": "at_location", "target": "mouth", "text": "toothbrush can be near mouth", "strength": 0.62, "valence": "neutral"},
            {"type": "is_a", "target": "object", "text": "toothbrush is an object", "strength": 0.7, "valence": "neutral"},
        ],
    },
    {
        "word": "own name",
        "aliases": ["child's own name", "name"],
        "category": "sound_language_precursor",
        "kind": "language_precursor",
        "summary": "sound pattern linked to self attention",
        "domains": ["self", "language", "sound_language_precursor"],
        "prerequisites": ["self", "voice", "attention"],
        "relations": [
            {"type": "linked_to", "target": "self", "text": "own name is linked to self", "strength": 0.74, "valence": "neutral"},
            {"type": "changes", "target": "attention", "text": "own name can change attention", "strength": 0.72, "valence": "neutral"},
        ],
    },
]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def add_aliases(concepts: dict[str, dict[str, Any]]) -> None:
    for word, aliases in ALIASES.items():
        if word not in concepts:
            continue
        existing = list(concepts[word].get("aliases", []))
        for alias in aliases:
            if alias not in existing:
                existing.append(alias)
        concepts[word]["aliases"] = existing


def make_concept(raw: dict[str, Any], index: int) -> dict[str, Any]:
    concept = {
        "age_level": "age_6mo",
        "aliases": raw.get("aliases", []),
        "category": raw["category"],
        "domains": raw["domains"],
        "id": f"6mo.{raw['category']}.{slug(raw['word'])}",
        "index": index,
        "kind": raw["kind"],
        "prerequisites": raw["prerequisites"],
        "relations": raw["relations"],
        "status": "active",
        "summary": raw["summary"],
        "word": raw["word"],
    }
    return concept


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    seed = json.loads(args.input.read_text(encoding="utf-8"))
    revised = copy.deepcopy(seed)
    concepts_by_word = {item["word"]: item for item in revised["concepts"]}
    add_aliases(concepts_by_word)

    next_index = len(revised["concepts"])
    added = []
    for raw in NEW_CONCEPTS:
        if raw["word"] in concepts_by_word:
            continue
        concept = make_concept(raw, next_index)
        revised["concepts"].append(concept)
        concepts_by_word[concept["word"]] = concept
        added.append(concept["word"])
        next_index += 1

    for index, concept in enumerate(revised["concepts"]):
        concept["index"] = index

    counts = Counter(item["category"] for item in revised["concepts"])
    revised["graph_id"] = "age_6mo_root_world_wordbank_v1"
    revised["title"] = "Age 6mo Root World Seed, Wordbank Revision V1"
    revised["description"] = (
        revised["description"]
        + " Wordbank v1 adds conservative US-English CDI aliases and early concepts."
    )
    revised["target_count"] = len(revised["concepts"])
    revised["counts"] = dict(sorted(counts.items()))
    revised["validation"] = {
        **revised.get("validation", {}),
        "wordbank_revision": {
            "source": "wordbank_age_staging_v0",
            "aliases_added_for": sorted(ALIASES),
            "concepts_added": added,
            "notes": [
                "Original 500-concept seed is unchanged.",
                "This file is a candidate revision for coverage comparison.",
                "Added concepts are conservative early American-English CDI items.",
            ],
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(revised, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "original_count": len(seed["concepts"]),
        "revised_count": len(revised["concepts"]),
        "added_count": len(added),
        "added": added,
        "counts": revised["counts"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
