#!/usr/bin/env python3
"""Extract age_6mo-compatible visual relations from Visual Genome.

Visual Genome is used only as raw scene evidence. This mapper keeps relations
that can be represented in the current 6mo relation grammar:

- object has_property attribute
- object at_location place_or_surface
- object has_a part_or_object
- object receives_action hold/touch
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from create_age_6mo_conceptnet_relation_dataset import (
    ACTION_CATEGORIES,
    DEFAULT_SEED,
    LOCATION_ENDS,
    build_aliases,
    load_seed_words,
    load_source_aliases,
    map_word,
    render,
    split_for,
    write_jsonl,
)


DEFAULT_VG_DIR = Path("data/external/visual_genome")
DEFAULT_OUTPUT = Path("data/developmental_graph/experiments/age_6mo_visual_genome_relations_v3")

EXTRA_ALIASES = {
    "baby": "person",
    "boy": "person",
    "child": "person",
    "girl": "person",
    "kid": "person",
    "man": "person",
    "woman": "person",
    "flooring": "floor",
    "ground": "floor",
    "tile floor": "floor",
    "wood floor": "floor",
    "baby bed": "bed",
    "crib": "bed",
    "couch": "bed",
    "sofa": "bed",
    "blankie": "blanket",
    "teddy bear": "soft toy",
    "stuffed animal": "soft toy",
    "toybox": "box",
    "toy box": "box",
    "blocks": "block",
    "book shelf": "book",
    "books": "book",
    "cupboard": "container",
    "dish": "bowl",
    "plate": "bowl",
    "bottle cap": "bottle",
    "baby bottle": "bottle",
    "shirt sleeve": "shirt",
    "clothes": "shirt",
    "clothing": "shirt",
    "skinny": "thin",
    "large": "big",
    "little": "small",
    "shiny": "smooth",
    "wooden": "hard",
}

PREDICATE_ALIASES = {
    "above": "above",
    "at": "at_location",
    "beside": "near",
    "by": "near",
    "has": "has_a",
    "have": "has_a",
    "having": "has_a",
    "held by": "hold",
    "holding": "hold",
    "holds": "hold",
    "in": "at_location",
    "inside": "at_location",
    "inside of": "at_location",
    "near": "near",
    "next to": "near",
    "on": "at_location",
    "on top of": "at_location",
    "sitting on": "at_location",
    "standing on": "at_location",
    "touching": "touch",
    "under": "below",
    "wearing": "wear",
    "wears": "wear",
    "with": "has_a",
}

BLOCKED_ATTRIBUTES = {
    "old",
    "young",
    "new",
    "plastic",
    "wooden",
    "metal",
    "cloth",
    "open",
    "closed",
}

BLOCKED_EDGES = {
    ("person", "has_a", "shirt"),
    ("person", "has_a", "toy"),
    ("person", "has_a", "book"),
    ("person", "has_property", "black"),
    ("person", "has_property", "white"),
}

COLOR_PROPERTIES = {"black", "blue", "green", "red", "white", "yellow"}
SIZE_PROPERTIES = {"big", "long", "short", "small"}
ALLOWED_SPACE_PROPERTY_STARTS = {"door", "floor", "window"}
ALLOWED_VISUAL_HAS_A = {
    ("bird", "eye"),
    ("bird", "head"),
    ("bird", "leg"),
    ("bird", "tail"),
    ("bottle", "mouth"),
    ("chair", "back"),
    ("chair", "leg"),
    ("dog", "ear"),
    ("dog", "eye"),
    ("dog", "face"),
    ("dog", "foot"),
    ("dog", "head"),
    ("dog", "leg"),
    ("dog", "nose"),
    ("soft toy", "ear"),
    ("soft toy", "eye"),
    ("soft toy", "face"),
    ("soft toy", "foot"),
    ("soft toy", "hand"),
    ("soft toy", "head"),
    ("soft toy", "leg"),
    ("table", "leg"),
}


def read_zip_json(path: Path) -> Any:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if len(names) != 1:
            raise ValueError(f"Expected one file in {path}, found {names}")
        with zf.open(names[0]) as handle:
            return json.load(handle)


def normalize_text(text: str | None) -> str | None:
    if text is None:
        return None
    text = text.lower().strip()
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z' ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def build_vg_aliases(
    seed_words: set[str],
    concepts: dict[str, dict[str, Any]],
    source_aliases: dict[str, str] | None = None,
) -> dict[str, str]:
    aliases = build_aliases(seed_words, concepts, source_aliases)
    for alias, target in EXTRA_ALIASES.items():
        if target in seed_words:
            aliases[alias] = target
    return aliases


def map_any(words: list[str] | str | None, aliases: dict[str, str]) -> str | None:
    if words is None:
        return None
    if isinstance(words, str):
        candidates = [words]
    else:
        candidates = words
    for candidate in candidates:
        mapped = map_word(normalize_text(candidate), aliases)
        if mapped:
            return mapped
    return None


def normalize_predicate(predicate: str | None) -> str | None:
    text = normalize_text(predicate)
    if not text:
        return None
    return PREDICATE_ALIASES.get(text, text)


def compatible(edge: dict[str, Any], concepts: dict[str, dict[str, Any]]) -> bool:
    start = edge["start"]
    relation = edge["relation"]
    end = edge["end"]
    if (start, relation, end) in BLOCKED_EDGES:
        return False
    start_cat = concepts[start]["category"]
    end_cat = concepts[end]["category"]
    if relation == "has_property":
        if end_cat != "object_property":
            return False
        if start_cat == "body_part" and end in COLOR_PROPERTIES | SIZE_PROPERTIES:
            return False
        if start == "water" and end in COLOR_PROPERTIES | SIZE_PROPERTIES:
            return False
        return start_cat in {"common_object", "sensory_input"} or start in ALLOWED_SPACE_PROPERTY_STARTS
    if relation == "at_location":
        if end not in LOCATION_ENDS:
            return False
        return start_cat == "common_object"
    if relation == "has_a":
        return (start, end) in ALLOWED_VISUAL_HAS_A
    if relation == "receives_action":
        return end in {"hold", "touch"} and end_cat in ACTION_CATEGORIES
    return False


def add_edge(
    counter: Counter[tuple[str, str, str]],
    examples: dict[tuple[str, str, str], dict[str, Any]],
    start: str,
    relation: str,
    end: str,
    image_id: int,
    source_kind: str,
) -> None:
    if start == end:
        return
    key = (start, relation, end)
    counter[key] += 1
    examples.setdefault(
        key,
        {
            "start": start,
            "relation": relation,
            "end": end,
            "example_image_id": image_id,
            "visual_genome_source": source_kind,
        },
    )


def extract_edges(
    vg_dir: Path,
    seed_path: Path,
    min_count: int,
    max_edges: int,
    source_aliases_path: Path | None = None,
) -> tuple[list[dict[str, Any]], int]:
    words, concepts = load_seed_words(seed_path)
    source_aliases = load_source_aliases(source_aliases_path, words)
    aliases = build_vg_aliases(words, concepts, source_aliases)
    counts: Counter[tuple[str, str, str]] = Counter()
    examples: dict[tuple[str, str, str], dict[str, Any]] = {}

    attributes_path = vg_dir / "attributes.json.zip"
    if attributes_path.exists():
        for image in read_zip_json(attributes_path):
            image_id = int(image["image_id"])
            for obj in image.get("attributes", []):
                start = map_any(obj.get("names") or obj.get("name"), aliases)
                if not start:
                    continue
                for attr in obj.get("attributes", []):
                    raw_attr = normalize_text(attr)
                    if raw_attr in BLOCKED_ATTRIBUTES:
                        continue
                    end = map_any(raw_attr, aliases)
                    if end:
                        add_edge(counts, examples, start, "has_property", end, image_id, "attribute")

    relationships_path = vg_dir / "relationships.json.zip"
    if relationships_path.exists():
        for image in read_zip_json(relationships_path):
            image_id = int(image.get("image_id", -1))
            for rel in image.get("relationships", []):
                subject = rel.get("subject", {})
                obj = rel.get("object", {})
                start = map_any(subject.get("names") or subject.get("name"), aliases)
                end = map_any(obj.get("names") or obj.get("name"), aliases)
                predicate = normalize_predicate(rel.get("predicate"))
                if not start or not end or not predicate:
                    continue
                if predicate == "has_a":
                    add_edge(counts, examples, start, "has_a", end, image_id, "relationship")
                elif predicate == "at_location":
                    add_edge(counts, examples, start, "at_location", end, image_id, "relationship")
                elif predicate in {"hold", "touch"}:
                    add_edge(counts, examples, end, "receives_action", predicate, image_id, "relationship")

    edges: list[dict[str, Any]] = []
    for (start, relation, end), count in counts.most_common():
        edge = dict(examples[(start, relation, end)])
        edge["count"] = count
        edge["weight"] = float(count)
        edge["id"] = hashlib.sha1(f"{start}|{relation}|{end}|visual_genome".encode("utf-8")).hexdigest()[:16]
        if count >= min_count and compatible(edge, concepts):
            edges.append(edge)
        if len(edges) >= max_edges:
            break
    return sorted(edges, key=lambda item: (item["start"], item["relation"], item["end"])), len(source_aliases)


def make_rows(edge: dict[str, Any], split: str, index: int) -> list[dict[str, Any]]:
    statement, question, answer = render_visual_edge(edge)
    base = {
        "edge_id": edge["id"],
        "start": edge["start"],
        "relation": edge["relation"],
        "end": edge["end"],
        "count": edge["count"],
        "weight": edge["weight"],
        "example_image_id": edge["example_image_id"],
        "visual_genome_source": edge["visual_genome_source"],
    }
    if split == "train":
        return [
            {
                "id": f"age6mo_vg_v0.train.statement.{index:05d}",
                "task_type": "relation_statement",
                "input": "",
                "target": statement,
                "metadata": base,
            },
            {
                "id": f"age6mo_vg_v0.train.qa.{index:05d}",
                "task_type": "relation_yesno_qa",
                "input": f"Question: {question}\nAnswer:",
                "target": answer,
                "metadata": base,
            },
        ]
    return [
        {
            "id": f"age6mo_vg_v0.{split}.qa.{index:05d}",
            "task_type": "heldout_relation_yesno_qa",
            "input": f"Question: {question}\nAnswer:",
            "target": answer,
            "metadata": base,
        }
    ]


def render_visual_edge(edge: dict[str, Any]) -> tuple[str, str, str]:
    if edge["relation"] == "has_property":
        start = edge["start"]
        end = edge["end"]
        return f"{start} can be {end}.", f"Can {start} be {end}?", "yes"
    if edge["relation"] == "has_a":
        start = edge["start"]
        end = edge["end"]
        article = "an" if end[:1] in "aeiou" else "a"
        return f"{start} can have {article} {end}.", f"Can {start} have {article} {end}?", "yes"
    return render(edge)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vg-dir", type=Path, default=DEFAULT_VG_DIR)
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-count", type=int, default=20)
    parser.add_argument("--max-edges", type=int, default=2000)
    parser.add_argument("--source-aliases", type=Path)
    args = parser.parse_args()

    words, _ = load_seed_words(args.seed_path)
    edges, source_alias_count = extract_edges(args.vg_dir, args.seed_path, args.min_count, args.max_edges, args.source_aliases)
    split_edges = {"train": [], "dev": [], "test": []}
    rows = {"train": [], "dev": [], "test": []}
    for index, edge in enumerate(edges, start=1):
        split = split_for(edge)
        split_edges[split].append(edge)
        rows[split].extend(make_rows(edge, split, index))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "edges.all.jsonl", edges)
    for split in ["train", "dev", "test"]:
        write_jsonl(args.output_dir / f"edges.{split}.jsonl", split_edges[split])
        write_jsonl(args.output_dir / f"{split}.jsonl", rows[split])

    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.output_dir.name,
        "seed_path": str(args.seed_path),
        "visual_genome_dir": str(args.vg_dir),
        "seed_concepts": len(words),
        "min_count": args.min_count,
        "max_edges": args.max_edges,
        "source_aliases_path": str(args.source_aliases) if args.source_aliases else None,
        "source_aliases_loaded": source_alias_count,
        "covered_seed_concepts": len({edge["start"] for edge in edges} | {edge["end"] for edge in edges}),
        "edges": len(edges),
        "edges_by_relation": dict(sorted(Counter(edge["relation"] for edge in edges).items())),
        "splits": {
            split: {
                "edges": len(split_edges[split]),
                "rows": len(rows[split]),
            }
            for split in ["train", "dev", "test"]
        },
        "notes": [
            "Visual Genome is used as visual-scene evidence, not as final ontology.",
            "Only relations compatible with the current 6mo grammar are kept.",
            "Counts are evidence frequency across Visual Genome annotations.",
            "Train includes statements plus yes/no QA; dev/test hold out edges and include QA only.",
        ],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
