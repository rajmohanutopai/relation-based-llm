#!/usr/bin/env python3
"""Generate V6 transfer-first ordinary-text procedural QA datasets.

V6 keeps the V3 hidden procedural relation world, but changes the experimental
shape:

- the model sees ordinary QA text only, not relation tags
- hidden relation facts are preserved only in metadata
- held-out tests are split by purpose: observation, inference, transfer, and
  counterfactual
- sparse and corrupted-cue control arms are generated from the same source
  units and targets

The main arm is `ordinary_dense_qa`. The control arms are useful only as
comparisons; they intentionally remove or damage the relation cues that the
main arm should learn from.
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

import create_procedural_foundation_world_v3 as v3
from output_state import retire_output_dir  # noqa: E402


SPLITS = (
    "train",
    "dev",
    "test_observation",
    "test_inference",
    "test_transfer",
    "test_counterfactual",
)
TEST_SPLITS = tuple(split for split in SPLITS if split.startswith("test_"))
VARIANTS = (
    "ordinary_dense_qa",
    "ordinary_sparse_qa",
    "ordinary_corrupt_qa",
)
PROMPT_TYPES = (
    "scene_question_answer",
    "natural_scene_question",
    "direct_question",
    "answer_and_reason_request",
    "question_then_scene",
)
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")
SHORTHAND_RE = re.compile(r"(?m)^(?:s|q|a|f|r|n):\s")

INFERENCE_FAMILIES = {
    "reach_touch",
    "support_edge_fall",
    "container_open_closed",
    "path_open_closed",
    "temperature_touch",
    "safe_unsafe_touch",
    "hide_see",
    "caregiver_comfort",
    "social_signal_response",
}
COUNTERFACTUAL_FAMILIES = {
    "reach_touch",
    "push_pull_move",
    "drop_fall",
    "support_edge_fall",
    "container_open_closed",
    "hide_see",
    "temperature_touch",
    "wet_dry",
    "safe_unsafe_touch",
    "path_open_closed",
    "give_take",
}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
        retire_output_dir(path)
    path.mkdir(parents=True, exist_ok=True)


def stable_int(*parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def stable_percent(*parts: object) -> int:
    return stable_int(*parts) % 100


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
    text = re.sub(r"\s+", " ", text.strip()).lower()
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


def phrase_list(names: list[str]) -> str:
    clean = [name.strip() for name in names if name and name.strip()]
    if not clean:
        return "something"
    if len(clean) == 1:
        return clean[0]
    return ", ".join(clean[:-1]) + f" and {clean[-1]}"


def split_pair(value: str) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split("_") if part.strip()]


def target_text(row: dict[str, Any]) -> str:
    answer = re.sub(r"\s+", " ", str(row["answer"]).strip()).rstrip(".")
    fact = lower_sentence(str(row["main_fact"]))
    return f"answer: {answer}.\nreason: {fact}"


def natural_scene(row: dict[str, Any]) -> str:
    return sentence(str(row["scene"]))


def sparse_scene(row: dict[str, Any]) -> str:
    task = str(row.get("rule_family") or "")
    meta = row.get("metadata", {})
    thing = str(meta.get("thing") or "thing")

    if task == "reach_touch":
        return sentence(f"baby is here. {thing} is here. baby moves hand")
    if task == "push_pull_move":
        action = str(meta.get("action") or "moves")
        verb = "pushes" if action == "push" else "pulls" if action == "pull" else "moves"
        return sentence(f"{thing} is here. baby {verb} {thing}")
    if task == "body_control":
        return sentence(f"baby tries to move {thing}")
    if task == "drop_fall":
        return sentence(f"{thing} is here. baby opens hand")
    if task == "support_edge_fall":
        surface = str(meta.get("surface") or "surface")
        return sentence(f"{thing} is on {surface}. baby bumps {surface}")
    if task == "container_open_closed":
        container = str(meta.get("container") or "container")
        return sentence(f"{thing} is in {container}. baby puts hand on {container}")
    if task == "hide_see":
        return sentence(f"{thing} is here. baby looks")
    if task == "shake_sound":
        return sentence(f"baby holds {thing}. baby moves {thing}")
    if task == "temperature_touch":
        return sentence(f"{thing} is here. baby touches {thing}")
    if task == "wet_dry":
        return sentence(f"{thing} is here. baby touches {thing}")
    if task == "safe_unsafe_touch":
        return sentence(f"{thing} is here. baby reaches hand")
    if task == "same_different_match":
        return sentence(f"{phrase_list(split_pair(thing))} are here. baby looks")
    if task == "more_less_count":
        return sentence(f"left has {thing}. right has {thing}. baby looks")
    if task == "path_open_closed":
        path = str(meta.get("path") or "path")
        return sentence(f"{path} is here. baby pushes {thing} to {path}")
    if task == "caregiver_comfort":
        return sentence("baby is here. caregiver is here")
    if task == "familiar_agent":
        return sentence(f"{thing} comes near baby. baby looks")
    if task == "social_signal_response":
        return sentence("a person is near baby. baby sees and hears")
    if task == "give_take":
        agent = str(meta.get("agent") or "person")
        return sentence(f"{agent} and {thing} are near baby. baby looks")
    if task == "word_name_binding":
        word = str(meta.get("word") or "word")
        return sentence(f"mom says {word}. baby looks")
    return sentence("baby is here. something happens")


def swap_phrases(text: str, pairs: list[tuple[str, str]]) -> tuple[str, int]:
    replacements: dict[str, str] = {}
    changed = 0
    output = text
    for index, (left, right) in enumerate(pairs):
        left_token = f"__swap_{index}_left__"
        right_token = f"__swap_{index}_right__"
        left_pattern = re.compile(rf"\b{re.escape(left)}\b", flags=re.IGNORECASE)
        right_pattern = re.compile(rf"\b{re.escape(right)}\b", flags=re.IGNORECASE)
        output, left_count = left_pattern.subn(left_token, output)
        output, right_count = right_pattern.subn(right_token, output)
        changed += left_count + right_count
        replacements[left_token] = right
        replacements[right_token] = left
    for token, replacement in replacements.items():
        output = output.replace(token, replacement)
    return output, changed


def corrupt_scene(row: dict[str, Any]) -> str:
    scene = natural_scene(row)
    corrupted, changed = swap_phrases(
        scene,
        [
            ("far from", "near"),
            ("near", "far"),
            ("open", "closed"),
            ("wet", "dry"),
            ("hot", "cold"),
            ("edge", "middle"),
            ("in hand", "on floor"),
            ("under", "on"),
            ("gives", "takes"),
            ("smiles", "frowns"),
            ("gentle voice", "loud voice"),
        ],
    )
    if changed:
        return sentence(corrupted)
    return sparse_scene(row)


def render_scene(variant: str, row: dict[str, Any]) -> str:
    if variant == "ordinary_dense_qa":
        return natural_scene(row)
    if variant == "ordinary_sparse_qa":
        return sparse_scene(row)
    if variant == "ordinary_corrupt_qa":
        return corrupt_scene(row)
    raise ValueError(f"unknown variant: {variant}")


def prompt_surfaces(row: dict[str, Any], scene_text: str) -> list[dict[str, str]]:
    question_text = question(str(row["question"]))
    return [
        {
            "prompt_type": "scene_question_answer",
            "input": f"Scene: {scene_text}\nQuestion: {question_text}\nAnswer:",
        },
        {
            "prompt_type": "natural_scene_question",
            "input": f"Here is what happened. {scene_text}\nQuestion: {question_text}\nAnswer:",
        },
        {
            "prompt_type": "direct_question",
            "input": f"Scene: {scene_text}\nAnswer this question: {question_text}\nAnswer:",
        },
        {
            "prompt_type": "answer_and_reason_request",
            "input": f"Scene: {scene_text}\nQuestion: {question_text}\nGive the answer and the reason.\nAnswer:",
        },
        {
            "prompt_type": "question_then_scene",
            "input": f"Question: {question_text}\nScene: {scene_text}\nAnswer:",
        },
    ]


def make_record(
    *,
    experiment_id: str,
    variant: str,
    split: str,
    row: dict[str, Any],
    surface: dict[str, str],
    surface_index: int,
) -> dict[str, Any]:
    input_text = surface["input"]
    target = target_text(row)
    full_text = f"{input_text}\n{target}"
    if SHORTHAND_RE.search(full_text):
        raise ValueError(f"shorthand protocol leaked into {row['id']} {surface['prompt_type']}")

    metadata = {
        **row["metadata"],
        "domain_id": "procedural_foundation_world",
        "rule_family": row["rule_family"],
        "representation": variant,
        "prompt_type": surface["prompt_type"],
        "source_world": "procedural_foundation_v3",
        "evaluation_bucket": split,
        "counterfactual_group": counterfactual_group(row),
        "hidden_positive_relations": row["relations"],
        "hidden_negative_relations": row["negative_relations"],
        "relations_visible_to_model": False,
    }
    return {
        "id": (
            f"dataset.{experiment_id}.{variant}.{split}.{surface_index:02d}."
            f"{surface['prompt_type']}.{row['id']}"
        ),
        "source_example_id": row["id"],
        "experiment_id": experiment_id,
        "variant": variant,
        "split": split,
        "evaluation_bucket": split,
        "surface_type": surface["prompt_type"],
        "prompt_type": surface["prompt_type"],
        "task_type": row["rule_family"],
        "input": input_text,
        "target": target,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target},
        ],
        "metadata": metadata,
    }


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
    return dict(sorted(Counter(str(row.get(key, "unknown")) for row in rows).items()))


def nested_count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("metadata", {}).get(key, "unknown")).lower() for row in rows).items()))


def prompt_conflict_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets_by_input: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        targets_by_input[row["input"]].add(row["target"])
    conflict_count = sum(1 for targets in targets_by_input.values() if len(targets) > 1)
    return {
        "unique_inputs": len(targets_by_input),
        "ambiguous_inputs": conflict_count,
        "ambiguous_input_percent": round((conflict_count / len(targets_by_input)) * 100, 4)
        if targets_by_input
        else 0.0,
        "target_count_distribution": dict(sorted(Counter(len(v) for v in targets_by_input.values()).items())),
    }


def family_thing(row: dict[str, Any]) -> tuple[str, str]:
    return str(row["rule_family"]), str(row.get("metadata", {}).get("thing") or "")


def counterfactual_group(row: dict[str, Any]) -> str | None:
    family = str(row["rule_family"])
    meta = row.get("metadata", {})
    question_type = str(row.get("question_type") or meta.get("question_type") or "")
    thing = str(meta.get("thing") or "")
    if family not in COUNTERFACTUAL_FAMILIES or not thing:
        return None
    if family == "reach_touch":
        return f"{family}|{thing}|{question_type}"
    if family == "push_pull_move":
        return f"{family}|{thing}|{meta.get('action')}|{question_type}"
    if family == "drop_fall":
        return f"{family}|{thing}|{question_type}"
    if family == "support_edge_fall":
        return f"{family}|{thing}|{meta.get('surface')}|{question_type}"
    if family == "container_open_closed":
        return f"{family}|{meta.get('container')}|{thing}|{question_type}"
    if family == "hide_see":
        return f"{family}|{thing}|{meta.get('cover')}|{question_type}"
    if family == "temperature_touch":
        return f"{family}|{thing}|{question_type}"
    if family == "wet_dry":
        return f"{family}|{thing}|{question_type}"
    if family == "path_open_closed":
        return f"{family}|{meta.get('path')}|{thing}|{question_type}"
    if family == "give_take":
        return f"{family}|{meta.get('agent')}|{thing}|{question_type}"
    return None


def build_transfer_keys(units: list[dict[str, Any]]) -> set[tuple[str, str]]:
    families_by_thing: dict[str, set[str]] = defaultdict(set)
    things_by_family: dict[str, set[str]] = defaultdict(set)
    for row in units:
        family, thing = family_thing(row)
        if not thing:
            continue
        families_by_thing[thing].add(family)
        things_by_family[family].add(thing)

    transfer_keys: set[tuple[str, str]] = set()
    selected_by_thing: Counter[str] = Counter()
    for family, things in sorted(things_by_family.items()):
        candidates = [
            thing
            for thing in things
            if len(families_by_thing[thing]) >= 2 and selected_by_thing[thing] < 2
        ]
        if not candidates:
            continue
        target_count = max(1, int(round(len(candidates) * 0.12)))
        ranked = sorted(candidates, key=lambda thing: stable_int("transfer", family, thing))
        for thing in ranked[:target_count]:
            transfer_keys.add((family, thing))
            selected_by_thing[thing] += 1
    return transfer_keys


def build_counterfactual_groups(units: list[dict[str, Any]]) -> set[str]:
    rows_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in units:
        group = counterfactual_group(row)
        if group:
            rows_by_group[group].append(row)

    candidates: list[str] = []
    for group, rows in rows_by_group.items():
        polarities = {row.get("metadata", {}).get("positive") for row in rows}
        if True in polarities and False in polarities:
            candidates.append(group)

    if not candidates:
        return set()
    target_count = max(1, int(round(len(candidates) * 0.10)))
    ranked = sorted(candidates, key=lambda group: stable_int("counterfactual-group", group))
    return set(ranked[:target_count])


def is_inference_test(row: dict[str, Any]) -> bool:
    family = str(row["rule_family"])
    if family not in INFERENCE_FAMILIES:
        return False
    question_type = str(row.get("question_type") or row.get("metadata", {}).get("question_type") or "")
    if question_type in {"is_body", "in_hand", "open", "edge", "wet_or_dry", "same_color", "same_shape"}:
        return False
    return stable_percent("inference", row["id"]) < 16


def split_units(units: list[dict[str, Any]], seed: int) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    transfer_keys = build_transfer_keys(units)
    counterfactual_groups = build_counterfactual_groups(units)
    rng = random.Random(seed)
    shuffled = sorted(units, key=lambda row: (stable_int(seed, row["id"]), row["id"]))

    splits: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}
    for row in shuffled:
        key = family_thing(row)
        if (counterfactual_group(row) or "") in counterfactual_groups:
            split = "test_counterfactual"
        elif key in transfer_keys:
            split = "test_transfer"
        elif is_inference_test(row):
            split = "test_inference"
        else:
            percent = stable_percent("observation-dev", seed, row["id"])
            if percent < 10:
                split = "dev"
            elif percent < 22:
                split = "test_observation"
            else:
                split = "train"
        splits[split].append(row)

    for split in SPLITS:
        rng.shuffle(splits[split])
        splits[split] = sorted(splits[split], key=lambda row: row["id"])

    policy = {
        "transfer_keys": [f"{family}|{thing}" for family, thing in sorted(transfer_keys)],
        "transfer_key_count": len(transfer_keys),
        "inference_families": sorted(INFERENCE_FAMILIES),
        "counterfactual_families": sorted(COUNTERFACTUAL_FAMILIES),
        "split_unit_counts": {split: len(rows) for split, rows in splits.items()},
        "split_rule_family_counts": {split: count_by(rows, "rule_family") for split, rows in splits.items()},
        "counterfactual_group_count": len(counterfactual_groups),
        "counterfactual_groups": sorted(counterfactual_groups),
    }
    return splits, policy


def build_records(
    experiment_id: str,
    variant: str,
    split: str,
    units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for unit in units:
        scene_text = render_scene(variant, unit)
        for index, surface in enumerate(prompt_surfaces(unit, scene_text), start=1):
            rows.append(
                make_record(
                    experiment_id=experiment_id,
                    variant=variant,
                    split=split,
                    row=unit,
                    surface=surface,
                    surface_index=index,
                )
            )
    return rows


def file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        name: {"path": str(path), "sha256": sha256_file(path)}
        for name, path in sorted(paths.items())
    }


def build_base_world() -> dict[str, Any]:
    base_world = v3.build_base_world()
    base_world["world_id"] = "procedural_foundation_v6_transfer_qa_world"
    base_world["purpose"] = (
        "V3 hidden baby + physical + simple social relation world rendered as "
        "ordinary QA text with explicit transfer-first evaluation buckets."
    )
    base_world["surface_policy"] = {
        "relations_visible_to_model": False,
        "main_variant": "ordinary_dense_qa",
        "control_variants": ["ordinary_sparse_qa", "ordinary_corrupt_qa"],
        "prompt_types": list(PROMPT_TYPES),
        "target_format": "answer line followed by reason line",
    }
    return base_world


def build_training_config(experiment_id: str, output_dir: Path, dataset_manifest: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "baseline_model": {
            "name": "nanochat",
            "role": "from-scratch local transfer comparison",
            "reason": "V6 tests whether relation-dense ordinary text transfers beyond repeated generator patterns.",
        },
        "dataset_manifest": str(dataset_manifest),
        "output_root": f"runs/{experiment_id}/nanochat",
        "format": {
            "prompt_template": "{input}\\n",
            "target_template": "{target}",
        },
        "training": {
            "max_seq_length": 256,
            "seed": 1729,
            "note": "Use scripts/create_nanochat_pretrain_shards.py for train/dev conversion. Evaluate each test_* split separately.",
        },
        "frozen_commands": {
            variant: (
                "python3 scripts/create_nanochat_pretrain_shards.py "
                f"--train-jsonl {output_dir / 'datasets' / variant / 'train.jsonl'} "
                f"--val-jsonl {output_dir / 'datasets' / variant / 'dev.jsonl'} "
                f"--base-dir runs/{experiment_id}/nanochat/{variant} "
                "--mode input_target --shuffle-train --seed 1729"
            )
            for variant in VARIANTS
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa"),
    )
    parser.add_argument("--experiment-id", default="procedural_foundation_v6_transfer_qa")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--shuffle-train-prompts", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_output_dir(args.output_dir, args.overwrite)

    base_world_path = args.output_dir / "base_world.json"
    write_json(base_world_path, build_base_world())

    units = v3.generate_units()
    unit_splits, split_policy = split_units(units, args.seed)
    for split, rows in unit_splits.items():
        write_jsonl(args.output_dir / "units" / f"{split}.jsonl", rows)
    test_units = [row for split in TEST_SPLITS for row in unit_splits[split]]
    write_jsonl(args.output_dir / "units" / "curriculum_test.jsonl", sorted(test_units, key=lambda row: row["id"]))

    records: dict[str, dict[str, list[dict[str, Any]]]] = {
        variant: {split: [] for split in (*SPLITS, "curriculum_test")}
        for variant in VARIANTS
    }
    output_paths: dict[str, Path] = {}
    rng = random.Random(args.seed)
    for variant in VARIANTS:
        for split in SPLITS:
            rows = build_records(args.experiment_id, variant, split, unit_splits[split])
            if args.shuffle_train_prompts and split == "train":
                rng.shuffle(rows)
            records[variant][split] = rows
            path = args.output_dir / "datasets" / variant / f"{split}.jsonl"
            write_jsonl(path, rows)
            output_paths[f"{variant}.{split}"] = path
        curriculum_rows = [
            row
            for split in TEST_SPLITS
            for row in records[variant][split]
        ]
        curriculum_rows = sorted(curriculum_rows, key=lambda row: row["id"])
        records[variant]["curriculum_test"] = curriculum_rows
        path = args.output_dir / "datasets" / variant / "curriculum_test.jsonl"
        write_jsonl(path, curriculum_rows)
        output_paths[f"{variant}.curriculum_test"] = path

    # Top-level aliases keep quick scripts pointed at the main dense arm.
    for split in ("train", "dev", "curriculum_test"):
        write_jsonl(args.output_dir / f"{split}.jsonl", records["ordinary_dense_qa"][split])

    dataset_manifest_path = args.output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "output_dir": str(args.output_dir / "datasets"),
        "base_world": str(base_world_path),
        "source": {
            "source_world": "procedural_foundation_v3",
            "source_total_units": len(units),
            "rule_families": sorted({row["rule_family"] for row in units}),
            "question_types": sorted({row["question_type"] for row in units}),
            "prompt_types": list(PROMPT_TYPES),
        },
        "split_policy": split_policy,
        "variants": {
            variant: {
                split: {
                    "total": len(records[variant][split]),
                    "base_units": len(unit_splits[split]) if split in unit_splits else len(test_units),
                    "prompts_per_unit": len(PROMPT_TYPES),
                    "task_type_counts": count_by(records[variant][split], "task_type"),
                    "prompt_type_counts": count_by(records[variant][split], "prompt_type"),
                    "question_type_counts": nested_count(records[variant][split], "question_type"),
                    "outcome_counts": nested_count(records[variant][split], "outcome"),
                    "positive_counts": nested_count(records[variant][split], "positive"),
                    "evaluation_bucket_counts": count_by(records[variant][split], "evaluation_bucket"),
                    "vocabulary": vocab_stats(records[variant][split]),
                    "prompt_conflicts": prompt_conflict_stats(records[variant][split]),
                }
                for split in (*SPLITS, "curriculum_test")
            }
            for variant in VARIANTS
        },
        "outputs": file_manifest(output_paths),
        "notes": [
            "V6 uses hidden V3 relation units but does not render relation lines to the model.",
            "ordinary_dense_qa is the main arm.",
            "ordinary_sparse_qa removes discriminating relation cues while preserving targets.",
            "ordinary_corrupt_qa flips common relation cues while preserving targets; it is a negative control.",
            "test_transfer holds out family/object combinations while keeping object words present elsewhere where possible.",
            "curriculum_test is the union of observation, inference, transfer, and counterfactual tests.",
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
        "unit_splits": {split: len(rows) for split, rows in unit_splits.items()},
        "record_splits": {
            variant: {split: len(records[variant][split]) for split in (*SPLITS, "curriculum_test")}
            for variant in VARIANTS
        },
        "prompts_per_unit": len(PROMPT_TYPES),
        "prompt_types": list(PROMPT_TYPES),
        "variants": list(VARIANTS),
        "split_policy": split_policy,
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
