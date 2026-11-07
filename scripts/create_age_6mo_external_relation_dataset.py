#!/usr/bin/env python3
"""Merge curated external 6mo relation sources into one training dataset."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from create_age_6mo_conceptnet_relation_dataset import render, split_for, write_jsonl


DEFAULT_CONCEPTNET_EDGES = Path(
    "data/developmental_graph/experiments/age_6mo_conceptnet_relations_v5_alias_strict/edges.all.jsonl"
)
DEFAULT_WORDNET_EDGES = Path(
    "data/developmental_graph/experiments/age_6mo_wordnet_relations_v2/edges.all.jsonl"
)
DEFAULT_VISUAL_GENOME_EDGES = Path(
    "data/developmental_graph/experiments/age_6mo_visual_genome_relations_v3/edges.all.jsonl"
)
DEFAULT_OUTPUT = Path("data/developmental_graph/experiments/age_6mo_external_relations_v3")

SOURCE_PRIORITY = {
    "wordnet": 0,
    "conceptnet": 1,
    "visual_genome": 2,
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def normalize_edge(edge: dict[str, Any], source: str) -> dict[str, Any]:
    result = dict(edge)
    result["source"] = source
    result["source_id"] = edge["id"]
    result["id"] = f"{source}_{edge['id']}"
    return result


def merge_edges(sources: list[tuple[str, Path]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for source, path in sources:
        for edge in read_jsonl(path):
            normalized = normalize_edge(edge, source)
            key = (normalized["start"], normalized["relation"], normalized["end"])
            previous = by_key.get(key)
            if previous is None:
                by_key[key] = normalized
                continue
            previous_rank = SOURCE_PRIORITY.get(previous["source"], 99)
            current_rank = SOURCE_PRIORITY.get(source, 99)
            if current_rank < previous_rank:
                by_key[key] = normalized
    return sorted(by_key.values(), key=lambda item: (item["start"], item["relation"], item["end"], item["source"]))


def make_rows(edge: dict[str, Any], split: str, index: int) -> list[dict[str, Any]]:
    statement, question, answer = render_edge(edge)
    base = {
        "edge_id": edge["id"],
        "source": edge["source"],
        "source_id": edge["source_id"],
        "start": edge["start"],
        "relation": edge["relation"],
        "end": edge["end"],
        "weight": edge.get("weight", 1.0),
    }
    if split == "train":
        return [
            {
                "id": f"age6mo_ext_v3.train.statement.{index:05d}",
                "task_type": "relation_statement",
                "input": "",
                "target": statement,
                "metadata": base,
            },
            {
                "id": f"age6mo_ext_v3.train.qa.{index:05d}",
                "task_type": "relation_yesno_qa",
                "input": f"Question: {question}\nAnswer:",
                "target": answer,
                "metadata": base,
            },
        ]
    return [
        {
            "id": f"age6mo_ext_v3.{split}.qa.{index:05d}",
            "task_type": "heldout_relation_yesno_qa",
            "input": f"Question: {question}\nAnswer:",
            "target": answer,
            "metadata": base,
        }
    ]


def render_edge(edge: dict[str, Any]) -> tuple[str, str, str]:
    if edge.get("source") == "visual_genome":
        start = edge["start"]
        end = edge["end"]
        if edge["relation"] == "has_property":
            return f"{start} can be {end}.", f"Can {start} be {end}?", "yes"
        if edge["relation"] == "has_a":
            article = "an" if end[:1] in "aeiou" else "a"
            return f"{start} can have {article} {end}.", f"Can {start} have {article} {end}?", "yes"
    return render(edge)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conceptnet-edges", type=Path, default=DEFAULT_CONCEPTNET_EDGES)
    parser.add_argument("--wordnet-edges", type=Path, default=DEFAULT_WORDNET_EDGES)
    parser.add_argument("--visual-genome-edges", type=Path, default=DEFAULT_VISUAL_GENOME_EDGES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    sources = [
        ("conceptnet", args.conceptnet_edges),
        ("wordnet", args.wordnet_edges),
    ]
    if args.visual_genome_edges.exists():
        sources.append(("visual_genome", args.visual_genome_edges))
    edges = merge_edges(sources)
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
        "sources": {source: str(path) for source, path in sources},
        "edges": len(edges),
        "covered_seed_concepts": len({edge["start"] for edge in edges} | {edge["end"] for edge in edges}),
        "edges_by_relation": dict(sorted(Counter(edge["relation"] for edge in edges).items())),
        "edges_by_source": dict(sorted(Counter(edge["source"] for edge in edges).items())),
        "splits": {
            split: {
                "edges": len(split_edges[split]),
                "rows": len(rows[split]),
            }
            for split in ["train", "dev", "test"]
        },
        "notes": [
            "Merged external relation source for the 6mo seed vocabulary.",
            "ConceptNet contributes commonsense object/action/place relations.",
            "WordNet contributes cleaner lexical hierarchy and part-whole relations.",
            "Visual Genome contributes high-frequency visual evidence relations.",
            "Duplicate triples keep the higher-priority source, currently WordNet before ConceptNet.",
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
