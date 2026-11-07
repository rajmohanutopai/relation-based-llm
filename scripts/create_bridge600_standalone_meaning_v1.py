#!/usr/bin/env python3
"""Create a standalone bridge-600 word-meaning curriculum.

This experiment intentionally drops the earlier root-300 rows. The goal is to
first prove that a small nanochat model can learn the bridge vocabulary itself
when the bridge facts are not drowned out by other task families.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_root_bridge_600_v1 import BRIDGE_CONCEPT_ROWS, sha256_file, write_json, write_jsonl  # noqa: E402
from output_state import retire_output_dir  # noqa: E402


EXPERIMENT_ID = "bridge600_standalone_meaning_v1"
VARIANT = "bridge600_meaning_qa"
WORD_RE = re.compile(r"[a-z]+")


def unique_bridge_concepts() -> list[tuple[str, str, str, str, str]]:
    seen: set[str] = set()
    rows: list[tuple[str, str, str, str, str]] = []
    for concept, anchor, relation, scene, fact in BRIDGE_CONCEPT_ROWS:
        if concept in seen:
            continue
        seen.add(concept)
        rows.append((concept, anchor, relation, scene, fact))
    return rows


TRAIN_TEMPLATES = (
    "{scene}\nQuestion: What does {concept} mean?\nAnswer:",
    "Fact: {scene}\nNow answer: What does {concept} mean?\nAnswer:",
    "Learn this: {scene}\nWhat does {concept} tell us?\nGive the answer:",
    "In this lesson, {scene_lc}\nQuestion: {concept} means what?\nAnswer:",
    "Use the fact: {scene}\nWhat is the meaning of {concept}?\nAnswer:",
    "Remember: {scene}\nNow say the meaning of {concept}.\nAnswer:",
    "Here is a meaning fact. {scene}\nWhat does {concept} mean?\nReply:",
    "The child hears: {scene}\nWhat should the child know about {concept}?\nAnswer:",
    "Meaning line: {scene}\nQuestion: tell the meaning of {concept}.\nAnswer:",
    "Given this sentence: {scene}\nWhat does the word {concept} mean?\nAnswer:",
)

DEV_TEMPLATES = (
    "New wording: {scene}\nWhat does {concept} mean?\nAnswer:",
    "Use this clue: {scene}\nTell me about {concept}.\nAnswer:",
)

TEST_TEMPLATES = (
    "In the room, {scene}\nNow answer this: What does {concept} mean?\nReply:",
    "The child notices this: {scene}\nNow answer this: What does {concept} mean?\nSo the answer is:",
    "Meaning check. {scene}\nWhat is true about {concept}?\nAnswer:",
)


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite")
    if path.exists() and overwrite:
        retire_output_dir(path)
    path.mkdir(parents=True, exist_ok=True)


def sentence(text: str) -> str:
    text = " ".join(text.strip().split())
    return text if text.endswith(".") else f"{text}."


def target_text(fact: str) -> str:
    fact = sentence(fact.lower())
    return f"answer: {fact}\nreason: {fact}"


def words_in_rows(rows: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(WORD_RE.findall(f"{row['input']}\n{row['target']}".lower()))
    return counter


def prompt_conflict_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets_by_input: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        targets_by_input[row["input"]].add(row["target"])
    return {
        "unique_inputs": len(targets_by_input),
        "ambiguous_inputs": sum(1 for targets in targets_by_input.values() if len(targets) > 1),
    }


def make_row(
    *,
    split: str,
    concept_index: int,
    concept: str,
    anchor: str,
    relation: str,
    scene: str,
    fact: str,
    template: str,
    template_index: int,
    repeat_index: int,
) -> dict[str, Any]:
    scene = sentence(scene)
    prompt = template.format(concept=concept, anchor=anchor, relation=relation, scene=scene, scene_lc=scene[:1].lower() + scene[1:])
    target = target_text(fact)
    row_id = (
        f"dataset.{EXPERIMENT_ID}.{VARIANT}.{split}."
        f"{concept_index:04d}.{template_index:02d}.{repeat_index:02d}.{concept}"
    )
    return {
        "id": row_id,
        "source_example_id": f"bridge600.meaning.{concept_index:04d}.{concept}",
        "experiment_id": EXPERIMENT_ID,
        "variant": VARIANT,
        "split": split,
        "evaluation_bucket": split,
        "surface_type": f"template_{template_index:02d}",
        "prompt_type": f"template_{template_index:02d}",
        "task_type": "bridge_word_meaning",
        "input": prompt,
        "target": target,
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": target},
        ],
        "metadata": {
            "concept": concept,
            "anchor": anchor,
            "relation": relation,
            "main_fact": fact.lower(),
            "scene": scene,
            "domain_id": EXPERIMENT_ID,
            "representation": VARIANT,
            "relations_visible_to_model": False,
            "bridge_standalone": True,
        },
    }


def build_rows(split: str, templates: tuple[str, ...], repeats: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for concept_index, (concept, anchor, relation, scene, fact) in enumerate(unique_bridge_concepts(), 1):
        for template_index, template in enumerate(templates, 1):
            for repeat_index in range(1, repeats + 1):
                rows.append(
                    make_row(
                        split=split,
                        concept_index=concept_index,
                        concept=concept,
                        anchor=anchor,
                        relation=relation,
                        scene=scene,
                        fact=fact,
                        template=template,
                        template_index=template_index,
                        repeat_index=repeat_index,
                    )
                )
    random.Random(seed + {"train": 1, "dev": 2, "test": 3}[split]).shuffle(rows)
    return rows


def split_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    words = words_in_rows(rows)
    return {
        "rows": len(rows),
        "unique_alpha_words": len(words),
        "total_alpha_words": sum(words.values()),
        "concept_count": len({row["metadata"]["concept"] for row in rows}),
        "task_type_counts": dict(Counter(row["task_type"] for row in rows)),
        "prompt_conflicts": prompt_conflict_stats(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/bridge600_standalone_meaning_v1"),
    )
    parser.add_argument("--train-repeats", type=int, default=5)
    parser.add_argument("--dev-repeats", type=int, default=1)
    parser.add_argument("--test-repeats", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ensure_output_dir(args.output_dir, args.overwrite)
    records = {
        "train": build_rows("train", TRAIN_TEMPLATES, args.train_repeats, args.seed),
        "dev": build_rows("dev", DEV_TEMPLATES, args.dev_repeats, args.seed),
        "test": build_rows("test", TEST_TEMPLATES, args.test_repeats, args.seed),
    }
    dataset_dir = args.output_dir / "datasets" / VARIANT
    output_paths: dict[str, Path] = {}
    for split, rows in records.items():
        path = dataset_dir / f"{split}.jsonl"
        write_jsonl(path, rows)
        output_paths[split] = path
    write_jsonl(args.output_dir / "train.jsonl", records["train"])
    write_jsonl(args.output_dir / "dev.jsonl", records["dev"])
    write_jsonl(args.output_dir / "test.jsonl", records["test"])

    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": EXPERIMENT_ID,
        "variant": VARIANT,
        "source": "BRIDGE_CONCEPT_ROWS from root_bridge_600_v1",
        "source_concept_rows": len(BRIDGE_CONCEPT_ROWS),
        "deduped_concept_count": len(unique_bridge_concepts()),
        "splits": {split: split_stats(rows) for split, rows in records.items()},
        "outputs": {
            split: {"path": str(path), "sha256": sha256_file(path)}
            for split, path in sorted(output_paths.items())
        },
        "notes": [
            "Standalone bridge-word meaning curriculum; no root-300 rows are included.",
            "All rows are bridge_word_meaning rows to avoid task imbalance.",
            "Train, dev, and test use different prompt templates.",
            "This is a learnability check, not a transfer check.",
        ],
    }
    write_json(args.output_dir / "datasets" / "manifest.json", manifest)
    write_json(
        args.output_dir / "training_config.json",
        {
            "schema_version": "0.1.0",
            "experiment_id": EXPERIMENT_ID,
            "dataset_manifest": str(args.output_dir / "datasets" / "manifest.json"),
            "format": {"prompt_template": "{input}\n", "target_template": "{target}"},
            "training": {"max_seq_length": 256, "seed": args.seed, "recommended_depth": 4},
        },
    )
    write_json(
        args.output_dir / "manifest.json",
        {
            "schema_version": "0.1.0",
            "experiment_id": EXPERIMENT_ID,
            "variant": VARIANT,
            "dataset_manifest": str(args.output_dir / "datasets" / "manifest.json"),
            "training_config": str(args.output_dir / "training_config.json"),
            "record_splits": {split: len(rows) for split, rows in records.items()},
            "unique_train_alpha_words": manifest["splits"]["train"]["unique_alpha_words"],
        },
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
