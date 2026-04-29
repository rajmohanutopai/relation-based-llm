#!/usr/bin/env python3
"""Generate coherent procedural foundation-world scenarios.

V0 proved that programmatic relation generation works, but independent
combinations such as "pen very high, pen on bed" produced awkward scenes. This
v1 generator uses scenario grammars: each rule family owns coherent layouts,
actions, outcomes, positive cases, and negative cases.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = (
    "procedural_plain_text",
    "procedural_relation_scaffolded",
    "procedural_relation_first_then_text",
)
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")


@dataclass(frozen=True)
class Thing:
    name: str
    size: str
    weight: str
    feel: str
    safe: bool
    mobile: bool
    sound: str
    container: bool = False


THINGS = (
    Thing("book", "medium", "heavy", "hard", True, True, "quiet"),
    Thing("pen", "small", "light", "hard", True, True, "quiet"),
    Thing("cup", "small", "light", "hard", True, True, "quiet", container=True),
    Thing("spoon", "small", "light", "hard", True, True, "clink"),
    Thing("ball", "small", "light", "soft", True, True, "quiet"),
    Thing("cloth", "medium", "light", "soft", True, True, "quiet"),
    Thing("toy", "small", "light", "soft", True, True, "quiet"),
    Thing("block", "small", "light", "hard", True, True, "clack"),
    Thing("bottle", "small", "light", "hard", True, True, "quiet"),
    Thing("bowl", "medium", "light", "hard", True, True, "clink", container=True),
    Thing("blanket", "big", "light", "soft", True, True, "quiet"),
    Thing("pillow", "big", "light", "soft", True, True, "quiet"),
    Thing("paper", "small", "light", "soft", True, True, "rustle"),
    Thing("rattle", "small", "light", "hard", True, True, "rattle"),
    Thing("box", "medium", "light", "hard", True, True, "quiet", container=True),
    Thing("banana", "small", "light", "soft", True, True, "quiet"),
    Thing("plate", "medium", "light", "hard", True, True, "clink"),
    Thing("shoe", "medium", "heavy", "hard", True, True, "quiet"),
    Thing("phone", "small", "light", "hard", False, True, "sound"),
    Thing("key", "small", "light", "hard", False, True, "jingle"),
    Thing("lamp", "big", "heavy", "hard", False, False, "quiet"),
    Thing("fan", "big", "heavy", "hard", False, False, "sound"),
    Thing("table", "big", "heavy", "hard", True, False, "quiet"),
    Thing("chair", "big", "heavy", "hard", True, False, "quiet"),
    Thing("door", "big", "heavy", "hard", True, False, "quiet"),
    Thing("wall", "big", "heavy", "hard", True, False, "quiet"),
    Thing("bed", "big", "heavy", "soft", True, False, "quiet"),
    Thing("floor", "big", "heavy", "hard", True, False, "quiet"),
)

MOVABLE_THINGS = tuple(thing for thing in THINGS if thing.mobile and thing.name not in {"floor", "wall"})
SMALL_MOVABLE_THINGS = tuple(thing for thing in MOVABLE_THINGS if thing.size in {"small", "medium"})
SOUND_THINGS = tuple(thing for thing in THINGS if thing.sound not in {"quiet"})
QUIET_THINGS = tuple(thing for thing in THINGS if thing.sound == "quiet" and thing.mobile)
COVER_THINGS = tuple(thing for thing in THINGS if thing.name in {"cloth", "blanket", "pillow"})
CONTAINERS = tuple(thing for thing in THINGS if thing.container)
HOT_COLD_THINGS = tuple(thing for thing in THINGS if thing.name in {"cup", "bottle", "spoon", "plate", "bowl", "cloth"})


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


def unit(
    rule_family: str,
    scenario: str,
    scene: str,
    question: str,
    answer: str,
    main_fact: str,
    relations: list[str],
    negatives: list[str] | None,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": f"procedural.v1.{rule_family}.{slug(scenario)}",
        "rule_family": rule_family,
        "scene": scene,
        "question": question,
        "answer": answer,
        "main_fact": main_fact,
        "relations": relations,
        "negative_relations": negatives or [],
        "metadata": metadata,
    }


def relation_base(thing: Thing) -> list[str]:
    return [
        f"{thing.name} is {thing.feel}",
        f"{thing.name} is {thing.size}",
        f"{thing.name} is {thing.weight}",
    ]


def reach_touch_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    layouts = [
        ("on floor near baby", "floor", "low", "near", True, "baby reaches hand"),
        ("on bed near baby", "bed", "middle", "near", True, "baby reaches hand"),
        ("beside hand on bed", "bed", "middle", "near", True, "baby closes hand"),
        ("above hand on toy bar", "toy bar", "high", "near", True, "baby lifts hand up"),
        ("on floor far from baby", "floor", "low", "far", False, "baby reaches hand"),
        ("on table far from baby", "table", "high", "far", False, "baby reaches hand"),
        ("on high shelf", "shelf", "very high", "far", False, "baby reaches hand up"),
        ("near fan on ceiling", "ceiling", "very high", "near", False, "baby lifts hand up"),
    ]
    for thing in THINGS:
        if thing.name in {"floor", "wall"}:
            continue
        for label, surface, height, distance, reached, action in layouts:
            if thing.name in {surface, "ceiling", "shelf", "toy bar"}:
                continue
            scene = f"{thing.name} is {label}. {action}."
            question = f"does hand touch {thing.name}?"
            if reached:
                relations = [
                    "baby can move hand",
                    f"{thing.name} is {distance}",
                    f"{thing.name} is {height}",
                    f"{thing.name} is on {surface}",
                    f"hand touches {thing.name}",
                    f"baby feels {thing.name}",
                    *relation_base(thing),
                ]
                if thing.mobile:
                    relations.append(f"hand can make {thing.name} move")
                rows.append(
                    unit(
                        "reach_touch",
                        f"{thing.name}.{surface}.{height}.{distance}.{action}.yes",
                        scene,
                        question,
                        "yes",
                        f"hand touches {thing.name}",
                        relations,
                        [],
                        {
                            "thing": thing.name,
                            "layout": label,
                            "surface": surface,
                            "height": height,
                            "distance": distance,
                            "action": action,
                            "outcome": "touch",
                            "positive": True,
                        },
                    )
                )
            else:
                negatives = [
                    f"hand does not touch {thing.name}",
                    f"baby does not feel {thing.name}",
                    f"hand cannot make {thing.name} move",
                ]
                if distance == "far":
                    negatives.append(f"{thing.name} is too far")
                if height == "very high":
                    negatives.append(f"{thing.name} is too high")
                relations = [
                    "baby can move hand",
                    f"{thing.name} is {distance}",
                    f"{thing.name} is {height}",
                    f"{thing.name} is on {surface}",
                    *relation_base(thing),
                ]
                rows.append(
                    unit(
                        "reach_touch",
                        f"{thing.name}.{surface}.{height}.{distance}.{action}.no",
                        scene,
                        question,
                        "no",
                        f"hand does not touch {thing.name}",
                        relations,
                        negatives,
                        {
                            "thing": thing.name,
                            "layout": label,
                            "surface": surface,
                            "height": height,
                            "distance": distance,
                            "action": action,
                            "outcome": "no_touch",
                            "positive": False,
                        },
                    )
                )
    return rows


def push_move_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    layouts = [
        ("on floor near baby", "floor", True),
        ("on bed near baby", "bed", True),
        ("on floor far from baby", "floor", False),
        ("on high shelf", "shelf", False),
    ]
    for thing in THINGS:
        if thing.name in {"floor", "wall"}:
            continue
        for label, surface, reachable in layouts:
            scene = f"{thing.name} is {label}. baby pushes hand."
            question = f"does {thing.name} move?"
            can_move = reachable and thing.mobile and thing.weight == "light" and thing.size != "big"
            relations = [
                "baby can move hand",
                f"{thing.name} is on {surface}",
                f"{thing.name} is {thing.weight}",
                f"{thing.name} is {thing.size}",
            ]
            negatives: list[str] = []
            if reachable:
                relations.append(f"hand touches {thing.name}")
            else:
                negatives.append(f"hand does not touch {thing.name}")
            if can_move:
                relations.append(f"hand makes {thing.name} move")
                if thing.name == "ball":
                    relations.append("ball rolls")
                answer = "yes"
                main_fact = f"{thing.name} moves"
                positive = True
            else:
                if not thing.mobile:
                    negatives.append(f"{thing.name} is fixed")
                if thing.weight == "heavy":
                    negatives.append(f"{thing.name} is heavy")
                if thing.size == "big":
                    negatives.append(f"{thing.name} is big")
                if not reachable:
                    negatives.append(f"{thing.name} is not near hand")
                answer = "no"
                main_fact = f"{thing.name} does not move"
                positive = False
            rows.append(
                unit(
                    "push_move",
                    f"{thing.name}.{surface}.{reachable}.{answer}",
                    scene,
                    question,
                    answer,
                    main_fact,
                    relations,
                    negatives,
                    {
                        "thing": thing.name,
                        "layout": label,
                        "surface": surface,
                        "action": "baby pushes hand",
                        "outcome": "move" if can_move else "no_move",
                        "positive": positive,
                    },
                )
            )
    return rows


def drop_fall_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for thing in SMALL_MOVABLE_THINGS:
        scenes = [
            (f"{thing.name} is in hand. baby opens hand.", True),
            (f"{thing.name} is on bed. baby opens hand.", False),
            (f"{thing.name} is on floor. baby opens hand.", False),
        ]
        for scene, falls in scenes:
            question = f"does {thing.name} fall?"
            relations = ["baby can open hand", *relation_base(thing)]
            negatives: list[str] = []
            if falls:
                relations.extend([f"{thing.name} is in hand", f"{thing.name} falls down", f"{thing.name} hits floor"])
                if thing.sound in {"clink", "clack", "jingle", "rattle"}:
                    relations.append(f"{thing.name} makes sound")
                answer = "yes"
                main_fact = f"{thing.name} falls down"
                positive = True
            else:
                relations.append(f"{thing.name} is not in hand")
                negatives.append(f"{thing.name} does not fall")
                answer = "no"
                main_fact = f"{thing.name} does not fall"
                positive = False
            rows.append(
                unit(
                    "drop_fall",
                    f"{thing.name}.{slug(scene)}",
                    scene,
                    question,
                    answer,
                    main_fact,
                    relations,
                    negatives,
                    {
                        "thing": thing.name,
                        "action": "baby opens hand",
                        "outcome": "fall" if falls else "no_fall",
                        "positive": positive,
                    },
                )
            )
    return rows


def shake_sound_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for thing in SOUND_THINGS + QUIET_THINGS:
        if not thing.mobile:
            continue
        scene = f"{thing.name} is in hand. baby shakes hand."
        question = "does baby hear sound?"
        relations = ["baby can move hand", f"{thing.name} is in hand", f"baby shakes {thing.name}", *relation_base(thing)]
        negatives: list[str] = []
        if thing.sound == "quiet":
            negatives.append(f"{thing.name} does not make sound")
            answer = "no"
            main_fact = "baby does not hear sound"
            positive = False
        else:
            relations.append(f"{thing.name} makes sound")
            relations.append("baby hears sound")
            answer = "yes"
            main_fact = "baby hears sound"
            positive = True
        rows.append(
            unit(
                "shake_sound",
                f"{thing.name}.{thing.sound}",
                scene,
                question,
                answer,
                main_fact,
                relations,
                negatives,
                {
                    "thing": thing.name,
                    "action": "baby shakes hand",
                    "sound": thing.sound,
                    "outcome": "sound" if positive else "no_sound",
                    "positive": positive,
                },
            )
        )
    return rows


def hide_see_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    visible_things = [thing for thing in SMALL_MOVABLE_THINGS if thing.name not in {"cloth", "blanket", "pillow"}]
    for thing in visible_things:
        for cover in COVER_THINGS:
            scenes = [
                (f"{thing.name} is on bed. baby looks.", True, [f"{thing.name} is not covered"]),
                (f"{thing.name} is under {cover.name}. baby looks.", False, [f"{cover.name} covers {thing.name}"]),
                (f"{thing.name} is under {cover.name}. mom lifts {cover.name}. baby looks.", True, [f"{cover.name} moves off {thing.name}"]),
            ]
            for scene, seen, extra in scenes:
                question = f"does baby see {thing.name}?"
                relations = ["baby can see", *extra]
                negatives: list[str] = []
                if seen:
                    relations.append(f"baby sees {thing.name}")
                    answer = "yes"
                    main_fact = f"baby sees {thing.name}"
                    positive = True
                else:
                    negatives.append(f"baby does not see {thing.name}")
                    answer = "no"
                    main_fact = f"baby does not see {thing.name}"
                    positive = False
                rows.append(
                    unit(
                        "hide_see",
                        f"{thing.name}.{cover.name}.{slug(scene)}",
                        scene,
                        question,
                        answer,
                        main_fact,
                        relations,
                        negatives,
                        {
                            "thing": thing.name,
                            "cover": cover.name,
                            "outcome": "see" if seen else "not_see",
                            "positive": positive,
                        },
                    )
                )
    return rows


def container_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    contents = [thing for thing in SMALL_MOVABLE_THINGS if not thing.container]
    for container in CONTAINERS:
        for thing in contents:
            if thing.name == container.name:
                continue
            scenes = [
                (f"{thing.name} is in open {container.name}. baby puts hand in {container.name}.", True),
                (f"{thing.name} is in closed {container.name}. baby puts hand on {container.name}.", False),
                (f"{thing.name} is beside {container.name}. baby puts hand in {container.name}.", False),
            ]
            for scene, touches in scenes:
                question = f"does hand touch {thing.name}?"
                relations = [f"{container.name} can hold {thing.name}", f"{thing.name} is near baby"]
                negatives: list[str] = []
                if touches:
                    relations.extend([f"{container.name} is open", f"{thing.name} is in {container.name}", f"hand touches {thing.name}"])
                    answer = "yes"
                    main_fact = f"hand touches {thing.name}"
                    positive = True
                else:
                    if "closed" in scene:
                        relations.append(f"{container.name} is closed")
                        negatives.append(f"closed {container.name} blocks hand")
                    else:
                        relations.append(f"{thing.name} is not in {container.name}")
                    negatives.append(f"hand does not touch {thing.name}")
                    answer = "no"
                    main_fact = f"hand does not touch {thing.name}"
                    positive = False
                rows.append(
                    unit(
                        "container_open_closed",
                        f"{container.name}.{thing.name}.{slug(scene)}",
                        scene,
                        question,
                        answer,
                        main_fact,
                        relations,
                        negatives,
                        {
                            "thing": thing.name,
                            "container": container.name,
                            "outcome": "touch_inside" if touches else "no_touch_inside",
                            "positive": positive,
                        },
                    )
                )
    return rows


def hot_cold_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for thing in HOT_COLD_THINGS:
        states = [
            ("hot", "hurt", "not ok", False),
            ("cold", "cold", "ok", True),
            ("warm", "warm", "ok", True),
        ]
        for temp, feel, valence, positive in states:
            scene = f"{thing.name} is {temp}. {thing.name} is near hand. baby touches {thing.name}."
            question = f"is touch ok?"
            relations = [
                f"hand touches {thing.name}",
                f"baby feels {temp}",
                f"{thing.name} is {temp}",
            ]
            negatives = []
            if valence == "not ok":
                relations.append("baby feels hurt")
                negatives.append("touch is not ok")
                answer = "no"
                main_fact = "touch is not ok"
            else:
                relations.append("touch is ok")
                answer = "yes"
                main_fact = f"baby feels {feel}"
            rows.append(
                unit(
                    "hot_cold_touch",
                    f"{thing.name}.{temp}",
                    scene,
                    question,
                    answer,
                    main_fact,
                    relations,
                    negatives,
                    {
                        "thing": thing.name,
                        "temperature": temp,
                        "outcome": valence,
                        "positive": positive,
                    },
                )
            )
    return rows


def generate_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for generator in (
        reach_touch_units,
        push_move_units,
        drop_fall_units,
        shake_sound_units,
        hide_see_units,
        container_units,
        hot_cold_units,
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
        key = f"{row['rule_family']}|{meta.get('positive', '')}"
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


def token_words(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, int]:
    words: Counter[str] = Counter()
    raw: Counter[str] = Counter()
    for row in rows:
        text = f"{row['input']}\n{row['target']}".lower()
        words.update(token_words(text))
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
        default=Path("data/developmental_graph/experiments/procedural_foundation_v1"),
    )
    parser.add_argument("--experiment-id", default="procedural_foundation_v1")
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
            "things": [thing.name for thing in THINGS],
            "rule_families": sorted({row["rule_family"] for row in units}),
        },
        "variants": {
            variant: {
                split: {
                    "total": len(records[variant][split]),
                    "task_type_counts": count_by(records[variant][split], "task_type"),
                    "thing_counts": nested_count(records[variant][split], "thing"),
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
            "Procedural relation composition, not paraphrase repetition.",
            "Scenario grammars keep layouts coherent.",
            "Positive and negative cases are generated for each rule family.",
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
        "procedural_rules": [
            "coherent layout controls reach and touch",
            "touch causes feel",
            "push plus touch plus movable/light thing causes movement",
            "object in hand plus open hand causes fall",
            "shake plus sound object causes heard sound",
            "cover blocks seeing until removed",
            "open container allows touch, closed container blocks touch",
            "hot touch is not ok, warm/cold touch gives feel without hurt",
        ],
        "dataset_manifest": str(dataset_manifest_path),
        "training_config": str(training_config_path),
        "outputs": file_manifest(output_paths_with_meta),
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
