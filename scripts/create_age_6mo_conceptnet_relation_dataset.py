#!/usr/bin/env python3
"""Extract 6mo-word ConceptNet relations and render relation QA datasets.

This is intentionally pure programmatic generation. It keeps only ConceptNet
edges where both endpoints are present in the age_6mo seed vocabulary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_SEED = Path("data/developmental_graph/seeds/age_6mo_root_world_500.json")
DEFAULT_CONCEPTNET = Path("data/external/conceptnet/conceptnet-assertions-5.7.0-en-en.tsv")
DEFAULT_OUTPUT = Path("data/developmental_graph/experiments/age_6mo_conceptnet_relations_v5_alias_strict")

RELATION_MAP = {
    "/r/IsA": "is_a",
    "/r/HasProperty": "has_property",
    "/r/CapableOf": "can_do",
    "/r/UsedFor": "used_for",
    "/r/AtLocation": "at_location",
    "/r/PartOf": "part_of",
    "/r/HasA": "has_a",
    "/r/Causes": "causes",
    "/r/ReceivesAction": "receives_action",
}

BAD_WORDS = {
    "thing",
    "relation",
    "state",
    "event",
    "input",
    "effect",
    "cause",
}

ABSTRACT_ENDS = {
    "access",
    "back",
    "call",
    "inside",
    "left",
    "pressure",
    "right",
}

GENERAL_ISA_ENDS = {
    "body",
    "container",
    "object",
    "person",
    "place",
    "sound",
    "support",
    "surface",
    "toy",
    "water",
}

ACTION_CATEGORIES = {
    "body_action_control",
    "routine_event",
    "sound_language_precursor",
}

OBJECTISH_CATEGORIES = {
    "common_object",
    "body_part",
    "object_property",
    "sensory_input",
    "space_motion_physics",
}

LOCATION_ENDS = {
    "bed",
    "body",
    "bottle",
    "box",
    "chair",
    "container",
    "floor",
    "hand",
    "mouth",
    "table",
}

CONTAINER_STARTS = {"basket", "bottle", "bowl", "box", "cup"}
TOY_STARTS = {"ball", "doll", "rattle", "soft toy", "toy", "toy car"}
SURFACE_STARTS = {"bed", "floor", "mat", "table", "mirror"}
PERSON_STARTS = {"caregiver", "mother", "father", "grandmother", "grandfather", "sibling", "person"}
SOUND_STARTS = {"cry", "coo", "laugh", "song", "voice", "rhyme", "sound", "pat"}
LIVING_STARTS = {"bird", "dog"}

BLOCKED_EDGES = {
    ("arm", "at_location", "chair"),
    ("bed", "has_property", "black"),
    ("bed", "used_for", "hold"),
    ("chest", "at_location", "body"),
    ("dog", "at_location", "table"),
    ("dog", "has_a", "toy"),
    ("dog", "receives_action", "kick"),
    ("ear", "at_location", "floor"),
    ("eye", "can_do", "cry"),
    ("fast", "causes", "hunger"),
    ("floor", "at_location", "bed"),
    ("floor", "at_location", "table"),
    ("foot", "at_location", "table"),
    ("gum", "at_location", "floor"),
    ("gum", "at_location", "table"),
    ("head", "at_location", "body"),
    ("leg", "at_location", "body"),
    ("leg", "at_location", "chair"),
    ("leg", "at_location", "table"),
    ("lip", "at_location", "body"),
    ("neck", "at_location", "body"),
    ("neck", "at_location", "bottle"),
    ("rice", "has_property", "black"),
    ("skin", "at_location", "body"),
    ("water", "has_property", "blue"),
}

MANUAL_ALIASES = {
    "baby bottle": "bottle",
    "child bottle": "bottle",
    "childs toybox": "box",
    "toy box": "box",
    "toybox": "box",
    "crib": "bed",
    "couch": "bed",
    "blankie": "blanket",
    "teddy bear": "soft toy",
    "stuffed animal": "soft toy",
    "dolly": "doll",
    "blocks": "block",
    "wooden block": "block",
    "rubber ball": "ball",
    "beach ball": "ball",
    "soccer ball": "ball",
    "bouncy ball": "ball",
    "plaything": "toy",
    "toys": "toy",
    "puppy": "dog",
    "doggie": "dog",
    "birdie": "bird",
    "mom": "mother",
    "mommy": "mother",
    "mama": "mother",
    "dad": "father",
    "daddy": "father",
    "papa": "father",
    "grandma": "grandmother",
    "grandpa": "grandfather",
    "blanket warmth": "warm comfort",
    "warmth": "warm",
    "keeping warm": "warm",
    "keep warm": "warm",
    "keeps warm": "warm",
    "sleeping": "sleep onset",
    "sleep": "sleep onset",
    "napping": "nap",
    "eating": "feeding starts",
    "feeding": "feeding starts",
    "drinking": "drinkable",
    "holding": "hold",
    "grasping": "grasp",
    "touching": "touch",
    "rolling": "roll",
    "bouncing": "bounce",
    "moving": "move",
    "hearing": "hear",
    "seeing": "see",
    "looking": "look",
    "crying": "cry",
    "laughing": "laugh",
    "smiling": "smile",
    "sucking": "suck",
    "taste": "taste",
    "tasting": "taste",
    "playing": "play pleasure",
    "play": "play pleasure",
    "softness": "soft",
    "hardness": "hard",
    "roundness": "round",
    "flatness": "flat",
    "stickiness": "sticky",
    "slipperiness": "slippery",
    "wetness": "wet",
    "dryness": "dry",
    "dark": "darkness",
    "darkness": "darkness",
    "light": "light source",
    "milk bottle": "bottle",
    "baby food": "puree",
    "food": "puree",
    "drinking water": "water",
    "diapers": "diaper",
    "clothing": "shirt",
    "clothes": "shirt",
    "fabric": "cloth",
    "towel": "towel",
    "towels": "towel",
    "flooring": "floor",
    "ground": "floor",
    "skin contact": "skin contact",
    "body part": "body",
}


def load_seed_words(path: Path) -> tuple[set[str], dict[str, dict[str, Any]]]:
    seed = json.loads(path.read_text(encoding="utf-8"))
    concepts = {item["word"]: item for item in seed["concepts"]}
    return set(concepts), concepts


def singularize(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return f"{word[:-3]}y"
    if word.endswith("es") and len(word) > 3:
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def simple_lemma(word: str) -> str:
    if word.endswith("ing") and len(word) > 5:
        stem = word[:-3]
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        if f"{stem}e" in {"move", "taste"}:
            return f"{stem}e"
        return stem
    if word.endswith("ed") and len(word) > 4:
        return word[:-2]
    return singularize(word)


def load_source_aliases(path: Path | None, words: set[str]) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    aliases: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            approved = str(row.get("approved", "")).strip().lower()
            if approved not in {"1", "true", "yes", "y"}:
                continue
            alias = normalize_candidate(row.get("candidate_phrase", ""))
            target = normalize_candidate(row.get("approved_target", ""))
            if alias and target in words:
                aliases[alias] = target
    return aliases


def build_aliases(
    words: set[str],
    concepts: dict[str, dict[str, Any]] | None = None,
    source_aliases: dict[str, str] | None = None,
) -> dict[str, str]:
    aliases: dict[str, str] = {word: word for word in words}
    for word in words:
        aliases[word.replace(" ", "_")] = word
        aliases[singularize(word)] = word
        aliases[simple_lemma(word)] = word
    if concepts:
        for word, concept in concepts.items():
            for alias in concept.get("aliases", []):
                normalized = normalize_candidate(alias)
                if normalized:
                    aliases[normalized] = word
                    aliases[normalized.replace(" ", "_")] = word
    for alias, target in MANUAL_ALIASES.items():
        if target in words:
            aliases[alias] = target
            aliases[alias.replace(" ", "_")] = target
    for alias, target in (source_aliases or {}).items():
        if target in words:
            aliases[alias] = target
            aliases[alias.replace(" ", "_")] = target
    return aliases


def concept_uri_to_word(uri: str) -> str | None:
    match = re.match(r"^/c/en/([^/]+)(?:/.*)?$", uri)
    if not match:
        return None
    word = match.group(1).replace("_", " ").strip().lower()
    if not word or any(char.isdigit() for char in word):
        return None
    return word


def normalize_candidate(word: str) -> str:
    word = word.lower().strip()
    word = word.replace("_", " ")
    word = re.sub(r"\b(a|an|the|your|my|someone's|someones|child's|childs|baby's|babys)\b", " ", word)
    word = re.sub(r"[^a-z' ]+", " ", word)
    word = re.sub(r"\s+", " ", word).strip()
    return word


def map_word(word: str | None, aliases: dict[str, str]) -> str | None:
    if word is None:
        return None
    candidates = []
    normalized = normalize_candidate(word)
    candidates.extend([word, normalized, singularize(normalized), simple_lemma(normalized)])
    for candidate in candidates:
        if candidate in aliases:
            return aliases[candidate]
    return None


def metadata_weight(raw: str) -> float:
    try:
        return float(json.loads(raw).get("weight", 1.0))
    except Exception:
        return 1.0


def article(word: str) -> str:
    if word.startswith(("a ", "an ", "the ")):
        return word
    if " " in word:
        return word
    if word[0] in "aeiou":
        return f"an {word}"
    return f"a {word}"


def clean_action(text: str) -> str:
    return text.removeprefix("to ").strip()


def gerund(text: str) -> str:
    text = clean_action(text)
    if " " in text:
        return text
    irregular = {"hold": "holding", "move": "moving", "roll": "rolling", "bounce": "bouncing"}
    if text in irregular:
        return irregular[text]
    if text.endswith("e") and len(text) > 2:
        return f"{text[:-1]}ing"
    return f"{text}ing"


def passive_action(text: str) -> str:
    text = clean_action(text)
    irregular = {"kick": "kicked", "touch": "touched", "hold": "held", "move": "moved"}
    if text in irregular:
        return irregular[text]
    if text.endswith("e"):
        return f"{text}d"
    return f"{text}ed"


def render(edge: dict[str, Any]) -> tuple[str, str, str]:
    start = edge["start"]
    end = edge["end"]
    rel = edge["relation"]
    if rel == "is_a":
        return f"{start} is {article(end)}.", f"Is {start} {article(end)}?", "yes"
    if rel == "has_property":
        return f"{start} is {end}.", f"Is {start} {end}?", "yes"
    if rel == "can_do":
        action = clean_action(end)
        return f"{start} can {action}.", f"Can {start} {action}?", "yes"
    if rel == "used_for":
        action = clean_action(end)
        action_name = gerund(action)
        return f"{start} is used for {action_name}.", f"Is {start} used for {action_name}?", "yes"
    if rel == "at_location":
        return f"{start} can be at {article(end)}.", f"Can {start} be at {article(end)}?", "yes"
    if rel == "part_of":
        return f"{start} is part of {article(end)}.", f"Is {start} part of {article(end)}?", "yes"
    if rel == "has_a":
        return f"{start} has {article(end)}.", f"Does {start} have {article(end)}?", "yes"
    if rel == "causes":
        return f"{start} can cause {end}.", f"Can {start} cause {end}?", "yes"
    if rel == "receives_action":
        action = passive_action(end)
        return f"{start} can be {action}.", f"Can {start} be {action}?", "yes"
    raise ValueError(f"Unsupported relation: {rel}")


def split_for(edge: dict[str, Any]) -> str:
    key = f"{edge['start']}\t{edge['relation']}\t{edge['end']}"
    bucket = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "dev"
    return "test"


def compatible(edge: dict[str, Any], concepts: dict[str, dict[str, Any]]) -> bool:
    start = edge["start"]
    end = edge["end"]
    rel = edge["relation"]
    start_cat = concepts[start]["category"]
    end_cat = concepts[end]["category"]
    if (start, rel, end) in BLOCKED_EDGES:
        return False
    if end in ABSTRACT_ENDS:
        return False
    if rel == "is_a":
        if end == "yellow":
            return False
        if end == "person":
            return start in PERSON_STARTS
        if end == "container":
            return start in CONTAINER_STARTS
        if end == "toy":
            return start in TOY_STARTS
        if end == "sound":
            return start in SOUND_STARTS
        if end == "object":
            return start_cat == "common_object"
        if end in {"place", "surface", "support"}:
            return start in SURFACE_STARTS
        if end == "water":
            return start == "bath water"
        if end_cat == "body_state_valence":
            return start_cat == "body_state_valence"
        if end_cat == "caregiver_social":
            return start_cat == "caregiver_social"
        return False
    if rel == "has_property":
        return end_cat == "object_property" and start_cat in {"common_object", "body_part", "space_motion_physics"}
    if rel == "can_do":
        return end_cat in ACTION_CATEGORIES and end not in {"toy", "sound"}
    if rel == "used_for":
        return start_cat == "common_object" and end_cat in ACTION_CATEGORIES and end not in {"contact"}
    if rel == "at_location":
        if end not in LOCATION_ENDS:
            return False
        if start_cat == "body_part":
            return False
        if start in LIVING_STARTS:
            return end in {"bed", "floor"}
        return start_cat == "common_object"
    if rel == "part_of":
        return start_cat == "body_part" and end in {"body", "face", "hand", "head", "mouth", "arm", "leg", "person"}
    if rel == "has_a":
        return end_cat in {"body_part", "common_object"}
    if rel == "causes":
        return end_cat in {"body_state_valence", "body_action_control", "routine_event"}
    if rel == "receives_action":
        if start in LIVING_STARTS:
            return False
        return end_cat in ACTION_CATEGORIES
    return False


def make_rows(edge: dict[str, Any], split: str, index: int) -> list[dict[str, Any]]:
    statement, question, answer = render(edge)
    base = {
        "edge_id": edge["id"],
        "start": edge["start"],
        "relation": edge["relation"],
        "end": edge["end"],
        "conceptnet_relation": edge["conceptnet_relation"],
        "weight": edge["weight"],
    }
    rows: list[dict[str, Any]] = []
    if split == "train":
        rows.append({
            "id": f"age6mo_cn_v0.train.statement.{index:05d}",
            "task_type": "relation_statement",
            "input": "",
            "target": statement,
            "metadata": base,
        })
        rows.append({
            "id": f"age6mo_cn_v0.train.qa.{index:05d}",
            "task_type": "relation_yesno_qa",
            "input": f"Question: {question}\nAnswer:",
            "target": answer,
            "metadata": base,
        })
    else:
        rows.append({
            "id": f"age6mo_cn_v0.{split}.qa.{index:05d}",
            "task_type": "heldout_relation_yesno_qa",
            "input": f"Question: {question}\nAnswer:",
            "target": answer,
            "metadata": base,
        })
    return rows


def extract_edges(
    conceptnet_path: Path,
    words: set[str],
    concepts: dict[str, dict[str, Any]],
    min_weight: float,
    use_aliases: bool,
    source_aliases: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    aliases = build_aliases(words, concepts, source_aliases) if use_aliases else {word: word for word in words}
    edges_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    with conceptnet_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 5:
                continue
            assertion, cn_rel, start_uri, end_uri, raw_meta = parts
            if cn_rel not in RELATION_MAP:
                continue
            raw_start = concept_uri_to_word(start_uri)
            raw_end = concept_uri_to_word(end_uri)
            start = map_word(raw_start, aliases)
            end = map_word(raw_end, aliases)
            if start not in words or end not in words:
                continue
            if start == end or start in BAD_WORDS or end in BAD_WORDS:
                continue
            weight = metadata_weight(raw_meta)
            if weight < min_weight:
                continue
            relation = RELATION_MAP[cn_rel]
            key = (start, relation, end)
            edge = {
                "id": hashlib.sha1(assertion.encode("utf-8")).hexdigest()[:16],
                "start": start,
                "relation": relation,
                "end": end,
                "raw_start": raw_start,
                "raw_end": raw_end,
                "mapped": start != raw_start or end != raw_end,
                "conceptnet_relation": cn_rel,
                "weight": weight,
            }
            if not compatible(edge, concepts):
                continue
            previous = edges_by_key.get(key)
            if previous is None or edge["weight"] > previous["weight"]:
                edges_by_key[key] = edge
    return sorted(edges_by_key.values(), key=lambda item: (item["start"], item["relation"], item["end"]))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--conceptnet-path", type=Path, default=DEFAULT_CONCEPTNET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-weight", type=float, default=1.0)
    parser.add_argument("--no-aliases", action="store_true")
    parser.add_argument("--source-aliases", type=Path)
    args = parser.parse_args()

    words, concepts = load_seed_words(args.seed_path)
    source_aliases = load_source_aliases(args.source_aliases, words)
    edges = extract_edges(args.conceptnet_path, words, concepts, args.min_weight, not args.no_aliases, source_aliases)

    split_edges = {"train": [], "dev": [], "test": []}
    dataset_rows = {"train": [], "dev": [], "test": []}
    for index, edge in enumerate(edges, start=1):
        split = split_for(edge)
        split_edges[split].append(edge)
        dataset_rows[split].extend(make_rows(edge, split, index))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "edges.all.jsonl", edges)
    for split in ["train", "dev", "test"]:
        write_jsonl(args.output_dir / f"edges.{split}.jsonl", split_edges[split])
        write_jsonl(args.output_dir / f"{split}.jsonl", dataset_rows[split])

    relation_counts = Counter(edge["relation"] for edge in edges)
    start_counts = Counter(edge["start"] for edge in edges)
    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.output_dir.name,
        "seed_path": str(args.seed_path),
        "conceptnet_path": str(args.conceptnet_path),
        "min_weight": args.min_weight,
        "aliases_enabled": not args.no_aliases,
        "source_aliases_path": str(args.source_aliases) if args.source_aliases else None,
        "source_aliases_loaded": len(source_aliases),
        "seed_concepts": len(concepts),
        "covered_seed_concepts": len({edge["start"] for edge in edges} | {edge["end"] for edge in edges}),
        "edges": len(edges),
        "mapped_edges": sum(1 for edge in edges if edge.get("mapped")),
        "edges_by_relation": dict(sorted(relation_counts.items())),
        "top_start_words": start_counts.most_common(30),
        "splits": {
            split: {
                "edges": len(split_edges[split]),
                "rows": len(dataset_rows[split]),
            }
            for split in ["train", "dev", "test"]
        },
        "notes": [
            "Only edges where both ConceptNet endpoints are in the age_6mo seed vocabulary are kept.",
            "Train includes relation statements plus relation yes/no QA.",
            "Dev/test include held-out relation yes/no QA only; those edges are not in train.",
            "All rows are programmatic; no AI generation is used.",
        ],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
