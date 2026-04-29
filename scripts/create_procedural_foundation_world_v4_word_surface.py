#!/usr/bin/env python3
"""Generate word-surface procedural foundation datasets.

V4 keeps the V3 underlying world and held-out split logic, but changes the
training surface. The main goal is to remove shorthand protocol tokens such as
``s:``, ``q:``, ``a:``, ``f:``, ``r:``, and ``n:`` from the first training
surface. Instead, the same generated situations are rendered through ordinary
words:

- scene / question / answer / reason labels
- simple unlabeled question-answer text
- because explanations
- short event continuation text
- optional full-word relation scaffolds
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import create_procedural_foundation_world_v3 as v3


SPLITS = v3.SPLITS
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")
SHORTHAND_RE = re.compile(r"(?m)^(?:s|q|a|f|r|n):\s")

VARIANTS = (
    "word_plain_text",
    "word_relation_scaffolded",
    "word_relation_first_then_text",
)

SURFACE_TYPES = (
    "labeled_words",
    "simple_lines",
    "because_answer",
    "answer_reason_bridge",
    "event_continuation",
)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite")
    if path.exists() and overwrite:
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    text = re.sub(
        r"(^|[.!?]\s+)([a-z])",
        lambda match: match.group(1) + match.group(2).upper(),
        text,
    )
    if text[-1] not in ".?!":
        text += "."
    return text


def lower_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    if text[-1] not in ".?!":
        text += "."
    return text


def question(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    text = text.rstrip(".")
    if text[-1] != "?":
        text += "?"
    return text


def answer_text(answer: str) -> str:
    answer = re.sub(r"\s+", " ", answer.strip())
    return answer


def because_target(answer: str, fact: str) -> str:
    answer = answer_text(answer)
    fact = lower_sentence(fact).rstrip(".")
    if answer.rstrip(".") == fact:
        return lower_sentence(fact)
    return f"{answer}, because {fact}."


def labeled_relation_lines(row: dict[str, Any]) -> list[str]:
    lines = []
    for relation in row["relations"]:
        lines.append(f"known relation: {lower_sentence(relation)}")
    for relation in row["negative_relations"]:
        lines.append(f"blocked relation: {lower_sentence(relation)}")
    return lines


def plain_surfaces(row: dict[str, Any]) -> list[dict[str, str]]:
    scene = sentence(row["scene"])
    question_text = question(row["question"])
    answer = answer_text(row["answer"])
    fact = lower_sentence(row["main_fact"])

    return [
        {
            "surface_type": "labeled_words",
            "input": f"scene: {scene}\nquestion: {question_text}\nanswer:",
            "target": f"answer: {answer}.\nreason: {fact}",
        },
        {
            "surface_type": "simple_lines",
            "input": f"{scene}\n{question_text}",
            "target": f"{answer}.\n{fact}",
        },
        {
            "surface_type": "because_answer",
            "input": f"{scene}\n{question_text}",
            "target": because_target(row["answer"], row["main_fact"]),
        },
        {
            "surface_type": "answer_reason_bridge",
            "input": f"the scene is: {scene}\nthe question is: {question_text}\nthe answer is:",
            "target": f"{answer}.\nthe reason is: {fact}",
        },
        {
            "surface_type": "event_continuation",
            "input": scene,
            "target": fact,
        },
    ]


def render_pair(variant: str, row: dict[str, Any], surface: dict[str, str]) -> tuple[str, str]:
    input_text = surface["input"]
    target_text = surface["target"]
    relation_lines = labeled_relation_lines(row)

    if variant == "word_plain_text":
        return input_text, target_text
    if variant == "word_relation_scaffolded":
        if relation_lines:
            target_text = f"{target_text}\n" + "\n".join(relation_lines)
        return input_text, target_text
    if variant == "word_relation_first_then_text":
        if relation_lines:
            input_text = "\n".join(relation_lines) + "\n" + input_text
        return input_text, target_text
    raise ValueError(f"unknown variant: {variant}")


def make_record(
    experiment_id: str,
    variant: str,
    split: str,
    row: dict[str, Any],
    surface: dict[str, str],
    surface_index: int,
) -> dict[str, Any]:
    input_text, target_text = render_pair(variant, row, surface)
    text = f"{input_text}\n{target_text}"
    if SHORTHAND_RE.search(text):
        raise ValueError(f"shorthand protocol token leaked into {row['id']} {surface['surface_type']}")

    return {
        "id": (
            f"dataset.{experiment_id}.{variant}.{surface_index:02d}."
            f"{surface['surface_type']}.{row['id']}"
        ),
        "source_example_id": row["id"],
        "experiment_id": experiment_id,
        "variant": variant,
        "surface_type": surface["surface_type"],
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
            "surface_type": surface["surface_type"],
            "source_world": "procedural_foundation_v3",
        },
    }


def build_records(experiment_id: str, variant: str, split: str, units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for unit in units:
        for index, surface in enumerate(plain_surfaces(unit), start=1):
            rows.append(make_record(experiment_id, variant, split, unit, surface, index))
    return rows


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, int]:
    words: Counter[str] = Counter()
    raw: Counter[str] = Counter()
    shorthand_hits = 0
    for row in rows:
        text = f"{row['input']}\n{row['target']}".lower()
        words.update(WORD_RE.findall(text))
        raw.update(RAW_RE.findall(text))
        if SHORTHAND_RE.search(text):
            shorthand_hits += 1
    return {
        "unique_words_alpha": len(words),
        "total_words_alpha": sum(words.values()),
        "unique_raw_whitespace_tokens": len(raw),
        "total_raw_whitespace_tokens": sum(raw.values()),
        "shorthand_protocol_hits": shorthand_hits,
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


def build_base_world() -> dict[str, Any]:
    base_world = v3.build_base_world()
    base_world["world_id"] = "procedural_foundation_v4_word_surface_world"
    base_world["purpose"] = (
        "V3 baby + physical + simple social base world rendered with word-surface "
        "training text instead of shorthand protocol tokens."
    )
    base_world["surface_policy"] = {
        "avoid_initial_shorthand": ["s:", "q:", "a:", "f:", "r:", "n:"],
        "use_word_labels": ["scene", "question", "answer", "reason", "known relation", "blocked relation"],
        "surface_types": list(SURFACE_TYPES),
    }
    return base_world


def build_training_config(experiment_id: str, output_dir: Path, dataset_manifest: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "baseline_model": {
            "name": "nanochat",
            "role": "from-scratch local comparison after V3",
            "reason": "V4 tests word-surface relation learning without shorthand prompt tokens.",
        },
        "dataset_manifest": str(dataset_manifest),
        "output_root": f"runs/{experiment_id}/nanochat",
        "format": {
            "prompt_template": "{input}\n",
            "target_template": "{target}",
        },
        "training": {
            "max_seq_length": 512,
            "seed": 1729,
            "note": "Use scripts/create_nanochat_pretrain_shards.py before nanochat training.",
        },
        "frozen_commands": {
            variant: (
                "python3 scripts/create_nanochat_pretrain_shards.py "
                f"--train-jsonl {output_dir / 'datasets' / variant / 'train.jsonl'} "
                f"--val-jsonl {output_dir / 'datasets' / variant / 'dev.jsonl'} "
                f"--base-dir runs/{experiment_id}/nanochat/{variant} "
                "--mode input_target"
            )
            for variant in VARIANTS
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/procedural_foundation_v4_word_surface"),
    )
    parser.add_argument("--experiment-id", default="procedural_foundation_v4_word_surface")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--shuffle-surfaces", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_output_dir(args.output_dir, args.overwrite)

    base_world_path = args.output_dir / "base_world.json"
    write_json(base_world_path, build_base_world())

    units = v3.generate_units()
    splits = v3.split_units(units, args.seed)
    for split, rows in splits.items():
        write_jsonl(args.output_dir / f"{split}.jsonl", rows)

    records: dict[str, dict[str, list[dict[str, Any]]]] = {
        variant: {split: [] for split in SPLITS}
        for variant in VARIANTS
    }
    output_paths: dict[str, Path] = {}
    rng = random.Random(args.seed)
    for variant in VARIANTS:
        for split in SPLITS:
            rows = build_records(args.experiment_id, variant, split, splits[split])
            if args.shuffle_surfaces and split == "train":
                rng.shuffle(rows)
            records[variant][split] = rows
            path = args.output_dir / "datasets" / variant / f"{split}.jsonl"
            write_jsonl(path, rows)
            output_paths[f"{variant}.{split}"] = path

    dataset_manifest_path = args.output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "output_dir": str(args.output_dir / "datasets"),
        "base_world": str(base_world_path),
        "source": {
            "source_experiment": "procedural_foundation_v3",
            "rule_families": sorted({row["rule_family"] for row in units}),
            "question_types": sorted({row["question_type"] for row in units}),
            "surface_types": list(SURFACE_TYPES),
        },
        "variants": {
            variant: {
                split: {
                    "total": len(records[variant][split]),
                    "base_units": len(splits[split]),
                    "surfaces_per_unit": len(SURFACE_TYPES),
                    "task_type_counts": count_by(records[variant][split], "task_type"),
                    "surface_type_counts": count_by(records[variant][split], "surface_type"),
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
            "V4 reuses V3 base units and split policy.",
            "Each base unit is rendered into five word-surface records.",
            "No initial shorthand protocol tokens s:/q:/a:/f:/r:/n: are allowed.",
            "Relation scaffolds use full-word labels: known relation and blocked relation.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)

    training_config_path = args.output_dir / "training_config.json"
    write_json(training_config_path, build_training_config(args.experiment_id, args.output_dir, dataset_manifest_path))

    output_paths_with_meta = {
        **output_paths,
        "base_world": base_world_path,
        "dataset_manifest": dataset_manifest_path,
        "training_config": training_config_path,
    }
    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "base_world": str(base_world_path),
        "base_world_counts": build_base_world()["counts"],
        "source_total_units": len(units),
        "splits": {split: len(rows) for split, rows in splits.items()},
        "records_per_variant": {
            variant: {split: len(records[variant][split]) for split in SPLITS}
            for variant in VARIANTS
        },
        "surfaces_per_unit": len(SURFACE_TYPES),
        "surface_types": list(SURFACE_TYPES),
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
