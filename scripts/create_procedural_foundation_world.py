#!/usr/bin/env python3
"""Generate a procedural foundation-world curriculum.

This creates relation-derived scenarios rather than paraphrases. A small set of
objects is reused across many states and actions so the model is pushed to learn
relations such as height, reach, touch, movement, support, and negative cases.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from output_state import retire_output_dir  # noqa: E402


SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = (
    "procedural_plain_text",
    "procedural_relation_scaffolded",
    "procedural_relation_first_then_text",
)


@dataclass(frozen=True)
class Thing:
    name: str
    size: str
    weight: str
    feel: str
    safe: bool
    mobile: bool


THINGS = (
    Thing("book", "medium", "heavy", "hard", True, True),
    Thing("pen", "small", "light", "hard", True, True),
    Thing("cup", "small", "light", "hard", True, True),
    Thing("spoon", "small", "light", "hard", True, True),
    Thing("ball", "small", "light", "soft", True, True),
    Thing("cloth", "medium", "light", "soft", True, True),
    Thing("toy", "small", "light", "soft", True, True),
    Thing("block", "small", "light", "hard", True, True),
    Thing("bottle", "small", "light", "hard", True, True),
    Thing("bowl", "medium", "light", "hard", True, True),
    Thing("blanket", "big", "light", "soft", True, True),
    Thing("pillow", "big", "light", "soft", True, True),
    Thing("paper", "small", "light", "soft", True, True),
    Thing("rattle", "small", "light", "hard", True, True),
    Thing("box", "medium", "light", "hard", True, True),
    Thing("banana", "small", "light", "soft", True, True),
    Thing("plate", "medium", "light", "hard", True, True),
    Thing("shoe", "medium", "heavy", "hard", True, True),
    Thing("phone", "small", "light", "hard", False, True),
    Thing("key", "small", "light", "hard", False, True),
    Thing("lamp", "big", "heavy", "hard", False, False),
    Thing("fan", "big", "heavy", "hard", False, False),
    Thing("table", "big", "heavy", "hard", True, False),
    Thing("chair", "big", "heavy", "hard", True, False),
    Thing("door", "big", "heavy", "hard", True, False),
    Thing("wall", "big", "heavy", "hard", True, False),
    Thing("bed", "big", "heavy", "soft", True, False),
    Thing("floor", "big", "heavy", "hard", True, False),
)

HEIGHTS = ("low", "middle", "high", "very high")
DISTANCES = ("near", "far")
SURFACES = ("floor", "bed", "table")
ACTIONS = ("lift hand", "lower hand", "push hand", "reach hand", "open hand", "close hand")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite")
    if path.exists() and overwrite:
        retire_output_dir(path)
    path.mkdir(parents=True, exist_ok=True)


def can_reach(height: str, distance: str, action: str) -> bool:
    if distance == "far":
        return False
    if height in {"low", "middle"}:
        return action in {"lift hand", "lower hand", "push hand", "reach hand", "open hand", "close hand"}
    if height == "high":
        return action in {"lift hand", "reach hand"}
    return False


def hand_motion(action: str) -> str:
    if action == "lift hand":
        return "hand go up"
    if action == "lower hand":
        return "hand go down"
    if action == "push hand":
        return "hand go to thing"
    if action == "reach hand":
        return "hand go to thing"
    if action == "open hand":
        return "hand open"
    if action == "close hand":
        return "hand close"
    return "hand move"


def outcome_for(thing: Thing, height: str, distance: str, action: str, on_surface: str) -> dict[str, Any]:
    reached = can_reach(height, distance, action)
    relations = [f"baby can move hand", hand_motion(action)]
    negatives: list[str] = []
    valence = "ok"

    if distance == "near":
        relations.append(f"{thing.name} near hand")
    else:
        relations.append(f"{thing.name} far hand")
    relations.append(f"{thing.name} {height}")
    relations.append(f"{thing.name} on {on_surface}")
    relations.append(f"{thing.name} is {thing.feel}")

    if reached:
        relations.append(f"hand touch {thing.name}")
        relations.append(f"baby feel {thing.name}")
        if thing.mobile and action in {"push hand", "reach hand", "lift hand"}:
            relations.append(f"hand can make {thing.name} move")
            if thing.name == "ball":
                relations.append("ball can roll")
            if thing.name == "rattle":
                relations.append("rattle can make sound")
        else:
            relations.append(f"hand cannot make {thing.name} move")
        if not thing.safe:
            relations.append(f"{thing.name} not ok")
            valence = "not ok"
    else:
        negatives.append(f"hand not touch {thing.name}")
        negatives.append(f"baby cannot feel {thing.name}")
        negatives.append(f"hand cannot make {thing.name} move")

    if height == "very high":
        negatives.append(f"baby cannot reach {thing.name}")
    if distance == "far":
        negatives.append(f"{thing.name} too far")
    if thing.weight == "heavy":
        negatives.append(f"{thing.name} heavy")
    if thing.size == "big":
        negatives.append(f"{thing.name} big")

    answer = relations[-1] if reached else negatives[0]
    if reached and action in {"lift hand", "reach hand"}:
        answer = f"hand touch {thing.name}"
    if not reached:
        answer = f"hand not touch {thing.name}"

    return {
        "answer": answer,
        "relations": relations,
        "negative_relations": negatives,
        "reached": reached,
        "valence": valence,
    }


def scenario_id(thing: Thing, height: str, distance: str, action: str, surface: str) -> str:
    parts = [thing.name, height.replace(" ", "_"), distance, action.replace(" ", "_"), surface]
    return ".".join(parts)


def make_unit(thing: Thing, height: str, distance: str, action: str, surface: str) -> dict[str, Any]:
    outcome = outcome_for(thing, height, distance, action, surface)
    scene = f"baby {action}. {thing.name} {height}. {thing.name} {distance}. {thing.name} on {surface}."
    question = f"does hand touch {thing.name}?"
    answer = "yes" if outcome["reached"] else "no"
    return {
        "id": f"procedural.foundation.{scenario_id(thing, height, distance, action, surface)}",
        "scene": scene,
        "question": question,
        "answer": answer,
        "main_fact": outcome["answer"],
        "relations": outcome["relations"],
        "negative_relations": outcome["negative_relations"],
        "metadata": {
            "thing": thing.name,
            "height": height,
            "distance": distance,
            "action": action,
            "surface": surface,
            "size": thing.size,
            "weight": thing.weight,
            "feel": thing.feel,
            "safe": thing.safe,
            "mobile": thing.mobile,
            "reached": outcome["reached"],
            "valence": outcome["valence"],
        },
    }


def generate_units() -> list[dict[str, Any]]:
    units = [
        make_unit(thing, height, distance, action, surface)
        for thing in THINGS
        for height in HEIGHTS
        for distance in DISTANCES
        for action in ACTIONS
        for surface in SURFACES
        if not (thing.name == surface)
    ]
    return sorted(units, key=lambda row: row["id"])


def split_units(units: list[dict[str, Any]], seed: int) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        key = f"{unit['metadata']['thing']}|{unit['metadata']['reached']}|{unit['metadata']['height']}"
        grouped[key].append(unit)

    rng = random.Random(seed)
    splits = {split: [] for split in SPLITS}
    for key in sorted(grouped):
        rows = grouped[key][:]
        rng.shuffle(rows)
        total = len(rows)
        train_count = int(total * 0.8)
        dev_count = int(total * 0.1)
        if total >= 3 and dev_count == 0:
            dev_count = 1
            train_count -= 1
        for row in rows[:train_count]:
            splits["train"].append(row)
        for row in rows[train_count : train_count + dev_count]:
            splits["dev"].append(row)
        for row in rows[train_count + dev_count :]:
            splits["curriculum_test"].append(row)

    for split in SPLITS:
        splits[split] = sorted(splits[split], key=lambda row: row["id"])
    return splits


def render_pair(variant: str, unit: dict[str, Any]) -> tuple[str, str]:
    input_lines = [
        f"s: {unit['scene']}",
        f"q: {unit['question']}",
        "a:",
    ]
    target_lines = [
        f"a: {unit['answer']}",
        f"f: {unit['main_fact']}",
    ]
    relation_lines = [f"r: {rel}" for rel in unit["relations"]]
    negative_lines = [f"n: {rel}" for rel in unit["negative_relations"]]

    if variant == "procedural_plain_text":
        return "\n".join(input_lines), "\n".join(target_lines)
    if variant == "procedural_relation_scaffolded":
        return "\n".join(input_lines), "\n".join(target_lines + relation_lines + negative_lines)
    if variant == "procedural_relation_first_then_text":
        return "\n".join(relation_lines + negative_lines + input_lines), "\n".join(target_lines)
    raise ValueError(f"unknown variant: {variant}")


def make_record(experiment_id: str, variant: str, split: str, unit: dict[str, Any]) -> dict[str, Any]:
    input_text, target_text = render_pair(variant, unit)
    return {
        "id": f"dataset.{experiment_id}.{variant}.{unit['id']}",
        "source_example_id": unit["id"],
        "experiment_id": experiment_id,
        "variant": variant,
        "split": split,
        "task_type": "procedural_touch_height_reach",
        "input": input_text,
        "target": target_text,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target_text},
        ],
        "metadata": {
            **unit["metadata"],
            "domain_id": "procedural_foundation_world",
            "representation": variant,
        },
    }


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, int]:
    words: Counter[str] = Counter()
    raw: Counter[str] = Counter()
    for row in rows:
        text = f"{row['input']}\n{row['target']}".lower()
        words.update(token for token in text.replace(".", " ").replace("?", " ").replace(":", " ").split() if token.isalpha())
        raw.update(text.split())
    return {
        "unique_words_alpha": len(words),
        "total_words_alpha": sum(words.values()),
        "unique_raw_whitespace_tokens": len(raw),
        "total_raw_whitespace_tokens": sum(raw.values()),
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(key, "unknown") for row in rows).items()))


def nested_count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get("metadata", {}).get(key, "unknown") for row in rows).items()))


def file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        name: {"path": str(path), "sha256": sha256_file(path)}
        for name, path in sorted(paths.items())
    }


def build_training_config(experiment_id: str, output_dir: Path, dataset_manifest: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "baseline_model": {
            "name": "HuggingFaceTB/SmolLM2-135M",
            "role": "format validation only before nanochat from-scratch training",
            "reason": "Use dry-run compatibility checks; actual procedural test should use nanochat.",
        },
        "dataset_manifest": str(dataset_manifest),
        "output_root": f"runs/{experiment_id}/smollm2_135m",
        "format": {
            "prompt_template": "{input}\n",
            "target_template": "{target}",
        },
        "training": {
            "max_seq_length": 512,
            "num_train_epochs": 3,
            "learning_rate": 5e-5,
            "per_device_train_batch_size": 1,
            "per_device_eval_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "warmup_ratio": 0.03,
            "weight_decay": 0.0,
            "logging_steps": 10,
            "save_total_limit": 2,
            "seed": 1729,
        },
        "frozen_commands": {
            variant: f"python3 scripts/train_tiny_causal_lm.py --config {output_dir / 'training_config.json'} --variant {variant} --dry-run"
            for variant in VARIANTS
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/procedural_foundation_v0"),
    )
    parser.add_argument("--experiment-id", default="procedural_foundation_v0")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ensure_output_dir(args.output_dir, args.overwrite)
    units = generate_units()
    splits = split_units(units, args.seed)
    for split, rows in splits.items():
        write_jsonl(args.output_dir / f"{split}.jsonl", rows)

    records: dict[str, dict[str, list[dict[str, Any]]]] = {
        variant: {split: [] for split in SPLITS}
        for variant in VARIANTS
    }
    output_paths: dict[str, Path] = {}
    for variant in VARIANTS:
        for split in SPLITS:
            rows = [make_record(args.experiment_id, variant, split, unit) for unit in splits[split]]
            records[variant][split] = rows
            path = args.output_dir / "datasets" / variant / f"{split}.jsonl"
            write_jsonl(path, rows)
            output_paths[f"{variant}.{split}"] = path

    dataset_manifest_path = args.output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "output_dir": str(args.output_dir / "datasets"),
        "source": {
            "things": [thing.name for thing in THINGS],
            "heights": list(HEIGHTS),
            "distances": list(DISTANCES),
            "actions": list(ACTIONS),
            "surfaces": list(SURFACES),
        },
        "variants": {
            variant: {
                split: {
                    "total": len(records[variant][split]),
                    "task_type_counts": count_by(records[variant][split], "task_type"),
                    "thing_counts": nested_count(records[variant][split], "thing"),
                    "height_counts": nested_count(records[variant][split], "height"),
                    "distance_counts": nested_count(records[variant][split], "distance"),
                    "reached_counts": nested_count(records[variant][split], "reached"),
                    "vocabulary": vocab_stats(records[variant][split]),
                }
                for split in SPLITS
            }
            for variant in VARIANTS
        },
        "outputs": file_manifest(output_paths),
        "notes": [
            "Procedural relation composition, not paraphrase repetition.",
            "Positive and negative touch/reach/move outcomes are generated from world state.",
            "A small noun world is reused across many relation combinations.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)

    training_config_path = args.output_dir / "training_config.json"
    write_json(training_config_path, build_training_config(args.experiment_id, args.output_dir, dataset_manifest_path))

    manifest_paths = {
        **output_paths,
        "dataset_manifest": dataset_manifest_path,
        "training_config": training_config_path,
    }
    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "total_units": len(units),
        "splits": {split: len(rows) for split, rows in splits.items()},
        "variants": list(VARIANTS),
        "procedural_rules": [
            "near plus reachable height plus action causes hand touch object",
            "far or very high blocks touch",
            "touch gives baby feel object",
            "touch plus movable object can make object move",
            "unsafe objects create not ok relation",
            "heavy or big objects resist hand movement",
        ],
        "dataset_manifest": str(dataset_manifest_path),
        "training_config": str(training_config_path),
        "outputs": file_manifest(manifest_paths),
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
