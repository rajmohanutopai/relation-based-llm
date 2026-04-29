#!/usr/bin/env python3
"""Generate expanded coherent procedural foundation-world scenarios.

V2 builds on procedural_foundation_v1:

- keep coherent scenario grammars
- add derived questions per scenario
- add new rule families for support, matching, quantity, path, caregiver, and
  word-name binding
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import create_procedural_foundation_world_v1 as v1


SPLITS = v1.SPLITS
VARIANTS = v1.VARIANTS
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")

COLORS = ("red", "blue", "yellow", "green")
SHAPES = {
    "ball": "round",
    "cup": "open",
    "book": "flat",
    "block": "square",
    "plate": "round",
    "box": "square",
}
COUNT_OBJECTS = ("ball", "block", "cup", "spoon", "toy")
WORD_OBJECTS = ("ball", "cup", "book", "spoon", "toy", "bottle", "shoe", "door")


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
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def make_unit(
    rule_family: str,
    scenario: str,
    question_type: str,
    scene: str,
    question: str,
    answer: str,
    main_fact: str,
    relations: list[str],
    negatives: list[str] | None,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": f"procedural.v2.{rule_family}.{slug(scenario)}.{slug(question_type)}",
        "rule_family": rule_family,
        "question_type": question_type,
        "scene": scene,
        "question": question,
        "answer": answer,
        "main_fact": main_fact,
        "relations": relations,
        "negative_relations": negatives or [],
        "metadata": {
            **metadata,
            "question_type": question_type,
        },
    }


def convert_v1_unit(row: dict[str, Any], question_type: str, question: str, answer: str, main_fact: str) -> dict[str, Any]:
    return make_unit(
        row["rule_family"],
        row["id"],
        question_type,
        row["scene"],
        question,
        answer,
        main_fact,
        row["relations"],
        row["negative_relations"],
        row["metadata"],
    )


def relation_has(row: dict[str, Any], text: str) -> bool:
    return text in row["relations"] or text in row["negative_relations"]


def thing(row: dict[str, Any]) -> str | None:
    value = row.get("metadata", {}).get("thing")
    return str(value) if value else None


def derived_from_v1(row: dict[str, Any]) -> list[dict[str, Any]]:
    units = [
        convert_v1_unit(row, "main", row["question"], row["answer"], row["main_fact"]),
        convert_v1_unit(row, "what_happened", "what happened?", row["main_fact"], row["main_fact"]),
    ]
    item = thing(row)
    family = row["rule_family"]

    if item:
        if relation_has(row, f"baby feels {item}"):
            units.append(convert_v1_unit(row, "feel", f"does baby feel {item}?", "yes", f"baby feels {item}"))
        elif relation_has(row, f"baby does not feel {item}"):
            units.append(convert_v1_unit(row, "feel", f"does baby feel {item}?", "no", f"baby does not feel {item}"))

        if relation_has(row, f"hand touches {item}"):
            units.append(convert_v1_unit(row, "touch", f"does hand touch {item}?", "yes", f"hand touches {item}"))
        elif relation_has(row, f"hand does not touch {item}"):
            units.append(convert_v1_unit(row, "touch", f"does hand touch {item}?", "no", f"hand does not touch {item}"))

        if relation_has(row, f"hand can make {item} move") or relation_has(row, f"hand makes {item} move"):
            units.append(convert_v1_unit(row, "move", f"can hand make {item} move?", "yes", f"hand can make {item} move"))
        elif relation_has(row, f"hand cannot make {item} move"):
            units.append(convert_v1_unit(row, "move", f"can hand make {item} move?", "no", f"hand cannot make {item} move"))

    if family == "reach_touch" and item:
        if row["answer"] == "no":
            reason = next((neg for neg in row["negative_relations"] if "too" in neg), row["main_fact"])
            units.append(convert_v1_unit(row, "why_no_touch", "why no touch?", reason, reason))
    if family == "container_open_closed":
        container = str(row.get("metadata", {}).get("container", "box"))
        if relation_has(row, f"{container} is closed"):
            units.append(convert_v1_unit(row, "open_closed", f"is {container} open?", "no", f"{container} is closed"))
            units.append(convert_v1_unit(row, "block", "what blocks hand?", f"closed {container}", f"closed {container} blocks hand"))
        elif relation_has(row, f"{container} is open"):
            units.append(convert_v1_unit(row, "open_closed", f"is {container} open?", "yes", f"{container} is open"))
    if family == "hide_see" and item:
        if row["answer"] == "no":
            cover = str(row.get("metadata", {}).get("cover", "cloth"))
            units.append(convert_v1_unit(row, "cover", f"what covers {item}?", cover, f"{cover} covers {item}"))
        else:
            units.append(convert_v1_unit(row, "see", f"does baby see {item}?", "yes", f"baby sees {item}"))
    if family == "drop_fall" and item:
        in_hand = relation_has(row, f"{item} is in hand")
        units.append(convert_v1_unit(row, "in_hand", f"is {item} in hand?", "yes" if in_hand else "no", f"{item} {'is' if in_hand else 'is not'} in hand"))
    if family == "shake_sound":
        heard = row["answer"] == "yes"
        units.append(convert_v1_unit(row, "hear_sound", "does baby hear sound?", "yes" if heard else "no", row["main_fact"]))
    if family == "hot_cold_touch":
        ok = row["answer"] == "yes"
        units.append(convert_v1_unit(row, "ok_touch", "is touch ok?", "yes" if ok else "no", row["main_fact"]))

    return units


def support_edge_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    objects = ("ball", "book", "cup", "block", "toy", "plate")
    layouts = [
        ("middle of table", False),
        ("edge of table", True),
        ("middle of bed", False),
        ("edge of bed", True),
    ]
    for obj in objects:
        for layout, falls in layouts:
            scene = f"{obj} is on {layout}. baby bumps {layout.split()[-1]}."
            relations = [f"{obj} is on {layout}", f"baby bumps {layout.split()[-1]}"]
            negatives: list[str] = []
            if falls:
                relations.extend([f"{obj} is at edge", f"{obj} falls down", f"{obj} hits floor"])
                answer = "yes"
                fact = f"{obj} falls down"
                positive = True
            else:
                relations.extend([f"{obj} is not at edge", f"{obj} stays on {layout.split()[-1]}"])
                negatives.append(f"{obj} does not fall")
                answer = "no"
                fact = f"{obj} does not fall"
                positive = False
            base_meta = {"thing": obj, "layout": layout, "outcome": "fall" if falls else "no_fall", "positive": positive}
            rows.append(make_unit("support_edge_fall", f"{obj}.{layout}.main", "fall", scene, f"does {obj} fall?", answer, fact, relations, negatives, base_meta))
            rows.append(make_unit("support_edge_fall", f"{obj}.{layout}.edge", "edge", scene, f"is {obj} at edge?", "yes" if falls else "no", f"{obj} {'is' if falls else 'is not'} at edge", relations, negatives, base_meta))
            rows.append(make_unit("support_edge_fall", f"{obj}.{layout}.why", "why", scene, "why?", f"{obj} {'is at edge' if falls else 'is not at edge'}", f"{obj} {'is at edge' if falls else 'is not at edge'}", relations, negatives, base_meta))
    return rows


def same_different_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    objects = ("ball", "cup", "book", "block", "plate", "box")
    for index, obj_a in enumerate(objects):
        obj_b = objects[(index + 1) % len(objects)]
        for color_a in COLORS:
            for color_b in COLORS:
                same_color = color_a == color_b
                scene = f"{color_a} {obj_a} is here. {color_b} {obj_b} is here. baby looks."
                relations = [f"{obj_a} is {color_a}", f"{obj_b} is {color_b}"]
                negatives = [] if same_color else [f"{color_a} is not {color_b}"]
                fact = "same color" if same_color else "different color"
                answer = "yes" if same_color else "no"
                meta = {"thing": f"{obj_a}_{obj_b}", "outcome": fact.replace(" ", "_"), "positive": same_color}
                rows.append(make_unit("same_different_match", f"{obj_a}.{obj_b}.{color_a}.{color_b}.color", "same_color", scene, "same color?", answer, fact, relations, negatives, meta))
        shape_a = SHAPES[obj_a]
        shape_b = SHAPES[obj_b]
        same_shape = shape_a == shape_b
        scene = f"{obj_a} is here. {obj_b} is here. baby looks."
        relations = [f"{obj_a} is {shape_a}", f"{obj_b} is {shape_b}"]
        negatives = [] if same_shape else [f"{shape_a} is not {shape_b}"]
        fact = "same shape" if same_shape else "different shape"
        rows.append(make_unit("same_different_match", f"{obj_a}.{obj_b}.shape", "same_shape", scene, "same shape?", "yes" if same_shape else "no", fact, relations, negatives, {"thing": f"{obj_a}_{obj_b}", "outcome": fact.replace(" ", "_"), "positive": same_shape}))
    return rows


def count_phrase(count: int, obj: str) -> str:
    if count == 0:
        return f"zero {obj}"
    if count == 1:
        return f"one {obj}"
    if count == 2:
        return f"two {obj}"
    return f"three {obj}"


def more_less_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    counts = (0, 1, 2, 3)
    for obj in COUNT_OBJECTS:
        for left in counts:
            for right in counts:
                if left == right:
                    continue
                scene = f"left has {count_phrase(left, obj)}. right has {count_phrase(right, obj)}. baby looks."
                if left > right:
                    answer = "left"
                    fact = "left has more"
                    positive = True
                else:
                    answer = "right"
                    fact = "right has more"
                    positive = True
                less_fact = f"{'right' if left > right else 'left'} has less"
                relations = [f"left has {left}", f"right has {right}", fact, less_fact]
                negatives: list[str] = []
                meta = {"thing": obj, "left_count": left, "right_count": right, "outcome": fact.replace(" ", "_"), "positive": positive}
                rows.append(make_unit("more_less_count", f"{obj}.{left}.{right}.more", "more", scene, "which has more?", answer, fact, relations, negatives, meta))
                rows.append(make_unit("more_less_count", f"{obj}.{left}.{right}.less", "less", scene, "which has less?", "right" if left > right else "left", f"{'right' if left > right else 'left'} has less", relations, negatives, meta))
    return rows


def path_open_closed_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = ("door", "box", "gate")
    moving = ("ball", "toy", "block")
    for path in paths:
        for obj in moving:
            for open_state in (True, False):
                scene = f"{path} is {'open' if open_state else 'closed'}. baby pushes {obj} to {path}."
                if open_state:
                    relations = [f"{path} is open", f"{obj} can go through {path}"]
                    negatives: list[str] = []
                    answer = "yes"
                    fact = f"{obj} can go through {path}"
                else:
                    relations = [f"{path} is closed"]
                    negatives = [f"closed {path} blocks {obj}", f"{obj} cannot go through {path}"]
                    answer = "no"
                    fact = f"{obj} cannot go through {path}"
                meta = {"thing": obj, "path": path, "outcome": "go_through" if open_state else "blocked", "positive": open_state}
                rows.append(make_unit("path_open_closed", f"{path}.{obj}.{open_state}.go", "go_through", scene, f"can {obj} go through?", answer, fact, relations, negatives, meta))
                rows.append(make_unit("path_open_closed", f"{path}.{obj}.{open_state}.open", "open", scene, f"is {path} open?", "yes" if open_state else "no", f"{path} is {'open' if open_state else 'closed'}", relations, negatives, meta))
    return rows


def caregiver_comfort_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    scenes = [
        ("baby cries. mom comes near. mom holds baby.", True, "mom near helps baby"),
        ("baby cries. mom is far. no one comes.", False, "mom far does not help baby"),
        ("baby is hungry. mom gives milk.", True, "milk helps baby"),
        ("baby is hungry. bottle is empty.", False, "empty bottle does not help baby"),
        ("baby hears loud sound. mom holds baby.", True, "mom hold helps baby"),
        ("baby hears loud sound. mom is not near.", False, "baby is not ok"),
    ]
    for index, (scene, ok, fact) in enumerate(scenes, start=1):
        relations = ["baby not ok"]
        negatives: list[str] = []
        if ok:
            relations.extend([fact, "baby ok"])
            answer = "yes"
        else:
            negatives.append(fact)
            answer = "no"
        meta = {"thing": "baby", "outcome": "comfort" if ok else "no_comfort", "positive": ok}
        rows.append(make_unit("caregiver_comfort", f"{index}.ok", "ok", scene, "is baby ok?", answer, "baby ok" if ok else "baby not ok", relations, negatives, meta))
        rows.append(make_unit("caregiver_comfort", f"{index}.help", "help", scene, "what helps?", fact if ok else "nothing", fact, relations, negatives, meta))
    return rows


def word_name_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for word in WORD_OBJECTS:
        for obj in WORD_OBJECTS:
            match = word == obj
            scene = f"mom says {word}. {obj} is here. baby looks."
            relations = [f"word {word} names {word}", f"{obj} is here"]
            negatives = [] if match else [f"word {word} does not name {obj}"]
            answer = "yes" if match else "no"
            fact = f"word {word} names {obj}" if match else f"word {word} does not name {obj}"
            meta = {"thing": obj, "word": word, "outcome": "name_match" if match else "name_mismatch", "positive": match}
            rows.append(make_unit("word_name_binding", f"{word}.{obj}.match", "word_match", scene, f"does word name {obj}?", answer, fact, relations, negatives, meta))
            if match:
                rows.append(make_unit("word_name_binding", f"{word}.{obj}.what", "what_name", scene, "what does word name?", obj, f"word {word} names {obj}", relations, negatives, meta))
    return rows


def generate_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in v1.generate_units():
        rows.extend(derived_from_v1(base))
    for generator in (
        support_edge_units,
        same_different_units,
        more_less_units,
        path_open_closed_units,
        caregiver_comfort_units,
        word_name_units,
    ):
        rows.extend(generator())
    seen: set[str] = set()
    unique_rows: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: item["id"]):
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        unique_rows.append(row)
    return unique_rows


def split_units(units: list[dict[str, Any]], seed: int) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in units:
        meta = row["metadata"]
        key = f"{row['rule_family']}|{row['question_type']}|{meta.get('positive', '')}"
        grouped[key].append(row)

    rng = random.Random(seed)
    splits = {split: [] for split in SPLITS}
    for key in sorted(grouped):
        rows = grouped[key][:]
        rng.shuffle(rows)
        total = len(rows)
        if total == 1:
            train_count = 1
            dev_count = 0
        elif total == 2:
            train_count = 1
            dev_count = 0
        elif total == 3:
            train_count = 2
            dev_count = 0
        else:
            train_count = int(total * 0.8)
            dev_count = int(total * 0.1)
        if total >= 4 and dev_count == 0:
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


def render_pair(variant: str, row: dict[str, Any]) -> tuple[str, str]:
    input_lines = [f"s: {row['scene']}", f"q: {row['question']}", "a:"]
    target_lines = [f"a: {row['answer']}", f"f: {row['main_fact']}"]
    relation_lines = [f"r: {rel}" for rel in row["relations"]]
    negative_lines = [f"n: {rel}" for rel in row["negative_relations"]]
    if variant == "procedural_plain_text":
        return "\n".join(input_lines), "\n".join(target_lines)
    if variant == "procedural_relation_scaffolded":
        return "\n".join(input_lines), "\n".join(target_lines + relation_lines + negative_lines)
    if variant == "procedural_relation_first_then_text":
        return "\n".join(relation_lines + negative_lines + input_lines), "\n".join(target_lines)
    raise ValueError(f"unknown variant: {variant}")


def make_record(experiment_id: str, variant: str, split: str, row: dict[str, Any]) -> dict[str, Any]:
    input_text, target_text = render_pair(variant, row)
    return {
        "id": f"dataset.{experiment_id}.{variant}.{row['id']}",
        "source_example_id": row["id"],
        "experiment_id": experiment_id,
        "variant": variant,
        "split": split,
        "task_type": row["rule_family"],
        "input": input_text,
        "target": target_text,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target_text},
        ],
        "metadata": {
            **row["metadata"],
            "domain_id": "procedural_foundation_world",
            "rule_family": row["rule_family"],
            "representation": variant,
        },
    }


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, int]:
    words: Counter[str] = Counter()
    raw: Counter[str] = Counter()
    for row in rows:
        text = f"{row['input']}\n{row['target']}".lower()
        words.update(WORD_RE.findall(text))
        raw.update(RAW_RE.findall(text))
    return {
        "unique_words_alpha": len(words),
        "total_words_alpha": sum(words.values()),
        "unique_raw_whitespace_tokens": len(raw),
        "total_raw_whitespace_tokens": sum(raw.values()),
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(key, "unknown") for row in rows).items()))


def nested_count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("metadata", {}).get(key, "unknown")).lower() for row in rows).items()))


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
        default=Path("data/developmental_graph/experiments/procedural_foundation_v2"),
    )
    parser.add_argument("--experiment-id", default="procedural_foundation_v2")
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
            rows = [make_record(args.experiment_id, variant, split, row) for row in splits[split]]
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
            "rule_families": sorted({row["rule_family"] for row in units}),
            "question_types": sorted({row["question_type"] for row in units}),
        },
        "variants": {
            variant: {
                split: {
                    "total": len(records[variant][split]),
                    "task_type_counts": count_by(records[variant][split], "task_type"),
                    "question_type_counts": nested_count(records[variant][split], "question_type"),
                    "outcome_counts": nested_count(records[variant][split], "outcome"),
                    "positive_counts": nested_count(records[variant][split], "positive"),
                    "vocabulary": vocab_stats(records[variant][split]),
                }
                for split in SPLITS
            }
            for variant in VARIANTS
        },
        "outputs": file_manifest(output_paths),
        "notes": [
            "V2 expands V1 with derived questions per scenario.",
            "V2 adds support, match, quantity, path, caregiver, and word-name rule families.",
            "Scenario grammars remain coherent; no arbitrary field combinations.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)

    training_config_path = args.output_dir / "training_config.json"
    write_json(training_config_path, build_training_config(args.experiment_id, args.output_dir, dataset_manifest_path))

    output_paths_with_meta = {
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
        "rule_family_counts": count_by(units, "rule_family"),
        "question_type_counts": count_by(units, "question_type"),
        "dataset_manifest": str(dataset_manifest_path),
        "training_config": str(training_config_path),
        "outputs": file_manifest(output_paths_with_meta),
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
