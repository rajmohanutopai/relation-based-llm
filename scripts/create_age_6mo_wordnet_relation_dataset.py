#!/usr/bin/env python3
"""Extract WordNet relations for the age_6mo seed vocabulary.

This complements ConceptNet. WordNet is used for cleaner lexical relations:
hypernym `is_a`, holonym `part_of`, and meronym `has_a`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from nltk.corpus import wordnet as wn

from create_age_6mo_conceptnet_relation_dataset import (
    CONTAINER_STARTS,
    SOUND_STARTS,
    SURFACE_STARTS,
    TOY_STARTS,
    DEFAULT_SEED,
    build_aliases,
    load_source_aliases,
    load_seed_words,
    map_word,
    render,
    split_for,
    write_jsonl,
)


DEFAULT_OUTPUT = Path("data/developmental_graph/experiments/age_6mo_wordnet_relations_v2")

GENERAL_OBJECT_STARTS = {
    "ball",
    "basket",
    "blanket",
    "block",
    "book",
    "bottle",
    "bowl",
    "box",
    "chair",
    "cloth",
    "cup",
    "diaper",
    "doll",
    "mat",
    "mirror",
    "rattle",
    "shirt",
    "soft toy",
    "spoon",
    "table",
    "toy",
    "toy car",
    "towel",
}

ALLOWED_LEXNAMES = {
    "body_part": {"noun.body"},
    "common_object": {"noun.artifact", "noun.food", "noun.animal", "noun.object", "noun.plant"},
    "object_property": {"noun.attribute", "adj.all", "adj.pert"},
    "body_state_valence": {"noun.state", "noun.feeling", "noun.cognition"},
    "caregiver_social": {"noun.person"},
    "sound_language_precursor": {"noun.communication", "noun.event", "noun.attribute"},
    "body_action_control": {"verb.body", "verb.contact", "verb.motion", "verb.perception", "verb.communication"},
    "space_motion_physics": {"noun.location", "noun.object", "noun.shape", "noun.attribute", "verb.motion"},
    "routine_event": {"noun.event", "verb.change", "verb.motion", "verb.contact"},
    "sensory_input": {"noun.cognition", "noun.attribute", "noun.communication", "noun.event"},
}


def wordnet_key(word: str) -> str:
    return word.replace(" ", "_")


def concept_synsets(word: str, category: str, max_senses: int) -> list[Any]:
    allowed = ALLOWED_LEXNAMES.get(category)
    synsets = wn.synsets(wordnet_key(word))
    if allowed:
        filtered = [synset for synset in synsets if synset.lexname() in allowed]
        synsets = filtered
    return synsets[:max_senses]


def mapped_lemma_names(synset: Any, aliases: dict[str, str]) -> set[str]:
    mapped: set[str] = set()
    for lemma in synset.lemma_names():
        word = map_word(lemma.replace("_", " "), aliases)
        if word:
            mapped.add(word)
    return mapped


def add_edge(
    edges: dict[tuple[str, str, str], dict[str, Any]],
    start: str,
    relation: str,
    end: str,
    synset: Any,
    source: str,
) -> None:
    if start == end:
        return
    key = (start, relation, end)
    edge = {
        "id": hashlib.sha1(f"{start}|{relation}|{end}|{synset.name()}|{source}".encode("utf-8")).hexdigest()[:16],
        "start": start,
        "relation": relation,
        "end": end,
        "wordnet_synset": synset.name(),
        "wordnet_source": source,
        "definition": synset.definition(),
        "weight": 1.0,
    }
    edges.setdefault(key, edge)


def compatible(edge: dict[str, Any], concepts: dict[str, dict[str, Any]]) -> bool:
    start = edge["start"]
    end = edge["end"]
    relation = edge["relation"]
    start_cat = concepts[start]["category"]
    end_cat = concepts[end]["category"]
    if relation == "is_a":
        if start_cat == "body_part":
            return False
        if end == "container":
            return start in CONTAINER_STARTS
        if end == "object":
            return start in GENERAL_OBJECT_STARTS
        if end == "person":
            return start_cat == "caregiver_social" or start == "self"
        if end == "sound":
            return start in SOUND_STARTS
        if end == "surface":
            return start in SURFACE_STARTS
        if end == "toy":
            return start in TOY_STARTS
        if end == "water":
            return True
        if (start, end) in {("bath water", "water"), ("picture book", "book")}:
            return True
        if end_cat in {"body_state_valence", "caregiver_social"}:
            return start_cat == end_cat
        return False
    if relation == "part_of":
        if start_cat == "body_part":
            return end_cat in {"body_part", "core_relation"}
        return False
    if relation == "has_a":
        if start == "body":
            return end_cat == "body_part"
        if start_cat == "body_part":
            return end_cat == "body_part"
        if start_cat == "common_object":
            return end_cat in {"body_part", "common_object"}
        return False
    return False


def extract_edges(seed_path: Path, max_senses: int, source_aliases_path: Path | None = None) -> tuple[list[dict[str, Any]], int, int]:
    words, concepts = load_seed_words(seed_path)
    source_aliases = load_source_aliases(source_aliases_path, words)
    aliases = build_aliases(words, concepts, source_aliases)
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    source_synset_count = 0

    for word, concept in concepts.items():
        synsets = concept_synsets(word, concept["category"], max_senses)
        source_synset_count += len(synsets)
        for synset in synsets:
            for hypernym in synset.hypernyms():
                for end in mapped_lemma_names(hypernym, aliases):
                    add_edge(edges, word, "is_a", end, synset, "hypernym")
            holonyms = synset.part_holonyms() + synset.member_holonyms() + synset.substance_holonyms()
            for holonym in holonyms:
                for end in mapped_lemma_names(holonym, aliases):
                    add_edge(edges, word, "part_of", end, synset, "holonym")
            meronyms = synset.part_meronyms() + synset.member_meronyms() + synset.substance_meronyms()
            for meronym in meronyms:
                for end in mapped_lemma_names(meronym, aliases):
                    add_edge(edges, word, "has_a", end, synset, "meronym")

    filtered = [edge for edge in edges.values() if compatible(edge, concepts)]
    return sorted(filtered, key=lambda item: (item["start"], item["relation"], item["end"])), source_synset_count, len(source_aliases)


def make_rows(edge: dict[str, Any], split: str, index: int) -> list[dict[str, Any]]:
    statement, question, answer = render(edge)
    base = {
        "edge_id": edge["id"],
        "start": edge["start"],
        "relation": edge["relation"],
        "end": edge["end"],
        "wordnet_synset": edge["wordnet_synset"],
        "wordnet_source": edge["wordnet_source"],
        "definition": edge["definition"],
        "weight": edge["weight"],
    }
    if split == "train":
        return [
            {
                "id": f"age6mo_wn_v0.train.statement.{index:05d}",
                "task_type": "relation_statement",
                "input": "",
                "target": statement,
                "metadata": base,
            },
            {
                "id": f"age6mo_wn_v0.train.qa.{index:05d}",
                "task_type": "relation_yesno_qa",
                "input": f"Question: {question}\nAnswer:",
                "target": answer,
                "metadata": base,
            },
        ]
    return [
        {
            "id": f"age6mo_wn_v0.{split}.qa.{index:05d}",
            "task_type": "heldout_relation_yesno_qa",
            "input": f"Question: {question}\nAnswer:",
            "target": answer,
            "metadata": base,
        }
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-senses", type=int, default=2)
    parser.add_argument("--source-aliases", type=Path)
    args = parser.parse_args()

    words, _ = load_seed_words(args.seed_path)
    edges, source_synset_count, source_alias_count = extract_edges(args.seed_path, args.max_senses, args.source_aliases)
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
        "max_senses": args.max_senses,
        "seed_concepts": len(words),
        "source_synsets_examined": source_synset_count,
        "source_aliases_path": str(args.source_aliases) if args.source_aliases else None,
        "source_aliases_loaded": source_alias_count,
        "covered_seed_concepts": len({edge["start"] for edge in edges} | {edge["end"] for edge in edges}),
        "edges": len(edges),
        "edges_by_relation": dict(sorted(Counter(edge["relation"] for edge in edges).items())),
        "edges_by_source": dict(sorted(Counter(edge["wordnet_source"] for edge in edges).items())),
        "splits": {
            split: {
                "edges": len(split_edges[split]),
                "rows": len(rows[split]),
            }
            for split in ["train", "dev", "test"]
        },
        "notes": [
            "WordNet is used for lexical hierarchy and part-whole relations.",
            "Train includes statements plus yes/no QA; dev/test hold out edges and include QA only.",
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
