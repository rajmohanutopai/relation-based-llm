#!/usr/bin/env python3
"""Create core5 model-ready curriculum variants.

This combines the five seed domains into one deterministic experiment:

- 6mo child root world
- everyday physical world
- social world
- math/abstraction roots
- language binding

The script intentionally runs without LLM calls. It reuses the existing base and
bridge curriculum generators, creates deterministic train/dev/curriculum_test
splits, merges available held-out evaluations, and renders matched variants.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import create_developmental_dataset_variants as variant_render
import generate_developmental_bridge_curriculum as bridge_gen
import generate_developmental_curriculum as base_gen
from output_state import retire_output_dir  # noqa: E402


Example = dict[str, Any]
VariantRecord = dict[str, Any]

SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = ("plain_text", "relation_scaffolded", "relation_first_then_text")

DOMAIN_SPECS = (
    {
        "domain_id": "agent_6mo_indian_child",
        "label": "6mo root world",
        "seed": "data/developmental_graph/seeds/agent_6mo_indian_child.json",
        "heldout": None,
    },
    {
        "domain_id": "everyday_physical_world",
        "label": "everyday physical world",
        "seed": "data/developmental_graph/seeds/everyday_physical_world.json",
        "heldout": "data/developmental_graph/evaluations/everyday_physical_world_heldout.json",
    },
    {
        "domain_id": "social_world",
        "label": "simple social world",
        "seed": "data/developmental_graph/seeds/social_world.json",
        "heldout": "data/developmental_graph/evaluations/social_world_heldout.json",
    },
    {
        "domain_id": "math_abstraction",
        "label": "math and abstraction roots",
        "seed": "data/developmental_graph/seeds/math_abstraction.json",
        "heldout": "data/developmental_graph/evaluations/math_abstraction_heldout.json",
    },
    {
        "domain_id": "language_binding",
        "label": "language binding",
        "seed": "data/developmental_graph/seeds/language_binding.json",
        "heldout": "data/developmental_graph/evaluations/language_binding_heldout.json",
    },
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


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


def split_sizes(total: int, train_ratio: float, dev_ratio: float, test_ratio: float) -> tuple[int, int, int]:
    if total <= 0:
        return 0, 0, 0
    train_count = int(total * train_ratio)
    dev_count = int(total * dev_ratio)
    test_count = total - train_count - dev_count
    if total >= 3:
        if dev_ratio > 0 and dev_count == 0:
            dev_count = 1
            train_count -= 1
        if test_ratio > 0 and test_count == 0:
            test_count = 1
            train_count -= 1
    while train_count < 0:
        if test_count > 0:
            test_count -= 1
        elif dev_count > 0:
            dev_count -= 1
        train_count += 1
    return train_count, dev_count, test_count


def validate_ratios(train_ratio: float, dev_ratio: float, test_ratio: float) -> None:
    ratio_sum = train_ratio + dev_ratio + test_ratio
    if min(train_ratio, dev_ratio, test_ratio) < 0:
        raise ValueError("split ratios must be non-negative")
    if abs(ratio_sum - 1.0) > 1e-9:
        raise ValueError(f"split ratios must sum to 1.0, got {ratio_sum}")


def stratified_split(
    examples: list[Example],
    train_ratio: float,
    dev_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, list[Example]]:
    grouped: dict[tuple[str, str], list[Example]] = defaultdict(list)
    for example in examples:
        domain_id = example.get("metadata", {}).get("domain_id", "unknown")
        grouped[(domain_id, example.get("task_type", "unknown"))].append(example)

    rng = random.Random(seed)
    splits = {split_name: [] for split_name in SPLITS}
    for group_key in sorted(grouped):
        group_examples = sorted(grouped[group_key], key=lambda example: example["id"])
        rng.shuffle(group_examples)
        train_count, dev_count, test_count = split_sizes(
            len(group_examples),
            train_ratio,
            dev_ratio,
            test_ratio,
        )
        ranges = {
            "train": group_examples[:train_count],
            "dev": group_examples[train_count : train_count + dev_count],
            "curriculum_test": group_examples[train_count + dev_count : train_count + dev_count + test_count],
        }
        for split_name, rows in ranges.items():
            for row in rows:
                split_row = copy.deepcopy(row)
                split_row["split"] = split_name
                splits[split_name].append(split_row)

    for split_name in SPLITS:
        splits[split_name] = sorted(splits[split_name], key=lambda example: example["id"])
    return splits


def clean_bridge_example(example: Example) -> Example | None:
    """Keep bridge examples valid when a graph anchor has only object endpoints."""
    row = copy.deepcopy(example)
    target = row.get("target")
    if isinstance(target, dict) and target.get("relation_family_ids") == []:
        if row.get("task_type") in {"relation_family_from_prompt", "explanation_with_relations"}:
            return None
        target.pop("relation_family_ids", None)
    return row


def tagged_example(example: Example, domain: dict[str, str]) -> Example:
    row = copy.deepcopy(example)
    if row.get("task_type") in {
        "node_id_from_paraphrase",
        "relation_family_from_prompt",
        "graph_anchor_from_prompt",
        "explanation_with_relations",
    }:
        row["input"] = normalize_bridge_language(str(row.get("input", "")), domain["label"])
    metadata = dict(row.get("metadata", {}))
    metadata["domain_id"] = domain["domain_id"]
    metadata["domain_label"] = domain["label"]
    metadata["source_seed"] = domain["seed"]
    row["metadata"] = metadata
    return row


def normalize_bridge_language(text: str, domain_label: str) -> str:
    replacements = {
        "physical concept": "graph concept",
        "physical description": "relation description",
        "physical situation": f"{domain_label} situation",
        "physical trace": f"{domain_label} trace",
        "physical question": f"{domain_label} question",
        "physical relations": "graph relations",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def generate_domain_examples(domain: dict[str, str | None]) -> tuple[dict[str, Any], list[Example], dict[str, int]]:
    graph = load_json(Path(str(domain["seed"])))
    base_examples = base_gen.generate_examples(graph, list(base_gen.GENERATORS))
    bridge_examples = []
    for example in bridge_gen.generate_bridge_examples(graph):
        cleaned = clean_bridge_example(example)
        if cleaned is not None:
            bridge_examples.append(cleaned)

    examples = [tagged_example(example, domain) for example in base_examples + bridge_examples]
    counts = {
        "base_examples": len(base_examples),
        "bridge_examples": len(bridge_examples),
        "total_examples": len(examples),
    }
    return graph, examples, counts


def compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def relation_first_then_text(example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    plain_input, plain_target = variant_render.variant_pair("plain_text", example, nodes)
    relation_packet = {
        "domain_id": example.get("metadata", {}).get("domain_id"),
        "graph_id": example.get("graph_id"),
        "task_type": example.get("task_type"),
        "target_relation_structure": example.get("target"),
    }
    input_text = (
        "RELATION_PACKET:\n"
        f"{compact_json(relation_packet)}\n\n"
        "TEXT_PROMPT:\n"
        f"{plain_input}"
    )
    target_text = (
        "RELATION_TARGET:\n"
        f"{compact_json(example.get('target'))}\n\n"
        "TEXT_ANSWER:\n"
        f"{plain_target}"
    )
    return input_text, target_text


def render_pair(variant: str, example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    if variant == "relation_first_then_text":
        return relation_first_then_text(example, nodes)
    return variant_render.variant_pair(variant, example, nodes)


def make_record(
    experiment_id: str,
    variant: str,
    split_name: str,
    example: Example,
    nodes_by_graph: dict[str, dict[str, dict[str, Any]]],
) -> VariantRecord:
    graph_id = example.get("graph_id")
    nodes = nodes_by_graph.get(graph_id, {})
    input_text, target_text = render_pair(variant, example, nodes)
    domain_label = str(example.get("metadata", {}).get("domain_label", "relation"))
    input_text = normalize_bridge_language(input_text, domain_label)
    target_text = normalize_bridge_language(target_text, domain_label)
    if not input_text.strip() or not target_text.strip():
        raise ValueError(f"empty input or target for {variant}/{example['id']}")

    return {
        "id": f"dataset.{experiment_id}.{variant}.{example['id']}",
        "source_example_id": example["id"],
        "experiment_id": experiment_id,
        "variant": variant,
        "split": split_name,
        "task_type": example["task_type"],
        "input": input_text,
        "target": target_text,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target_text},
        ],
        "metadata": {
            "domain_id": example.get("metadata", {}).get("domain_id"),
            "domain_label": example.get("metadata", {}).get("domain_label"),
            "graph_id": graph_id,
            "representation": variant,
        },
    }


def counts_by_task(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row.get("task_type", "unknown") for row in rows).items()))


def counts_by_domain(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row.get("metadata", {}).get("domain_id", "unknown") for row in rows).items()))


def validate_matched_variants(records: dict[str, dict[str, list[VariantRecord]]], variants: list[str]) -> None:
    for split_name in SPLITS:
        source_sets = {
            variant: {row["source_example_id"] for row in records[variant][split_name]}
            for variant in variants
        }
        expected = source_sets[variants[0]]
        for variant, source_ids in source_sets.items():
            if source_ids != expected:
                missing = sorted(expected - source_ids)[:5]
                extra = sorted(source_ids - expected)[:5]
                raise ValueError(f"{split_name}/{variant} source IDs differ; missing={missing}, extra={extra}")


def output_file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        name: {"path": str(path), "sha256": sha256_file(path)}
        for name, path in sorted(paths.items())
    }


def merge_heldout(output_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    source_evaluations: list[str] = []

    for domain in DOMAIN_SPECS:
        heldout = domain.get("heldout")
        if not heldout:
            continue
        data = load_json(Path(str(heldout)))
        source_evaluations.append(str(heldout))
        for case in data.get("cases", []):
            row = copy.deepcopy(case)
            row["domain_id"] = domain["domain_id"]
            row["domain_label"] = domain["label"]
            row["source_evaluation_id"] = data.get("evaluation_id")
            cases.append(row)

    heldout_data = {
        "schema_version": "0.1.0",
        "evaluation_id": "heldout.core5_relation_curriculum_v0",
        "title": "Held-Out Evaluation: Core5 Relation Curriculum V0",
        "status": "heldout",
        "source_seed": "multiple",
        "source_inventory": "multiple",
        "source_audit": "multiple",
        "purpose": "Merged held-out evaluation prompts for the core5 relation curriculum. The 6mo root domain is included in training but has no held-out evaluation yet.",
        "scoring_notes": [
            "Evaluate cases by domain as well as overall.",
            "These held-out prompts are not included in the training curriculum variants.",
            "Graph anchor existence is validated in each source domain before merge; this merged file intentionally has source_seed=multiple.",
        ],
        "source_evaluations": source_evaluations,
        "cases": sorted(cases, key=lambda case: case["id"]),
    }
    heldout_path = output_dir / "heldout.json"
    write_json(heldout_path, heldout_data)

    prompt_rows = [
        {
            "case_id": case["id"],
            "case_type": case.get("case_type"),
            "domain_id": case.get("domain_id"),
            "input": case.get("prompt", ""),
            "prompt": case.get("prompt", ""),
        }
        for case in heldout_data["cases"]
    ]
    prompt_path = output_dir / "heldout_prompts.jsonl"
    write_jsonl(prompt_path, prompt_rows)

    stats = {
        "cases": len(cases),
        "case_type_counts": dict(sorted(Counter(case.get("case_type") for case in cases).items())),
        "domain_counts": dict(sorted(Counter(case.get("domain_id") for case in cases).items())),
        "source_evaluations": source_evaluations,
    }
    return heldout_path, prompt_path, stats


def build_training_config(experiment_id: str, dataset_manifest: Path, output_dir: Path, variants: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "baseline_model": {
            "name": "HuggingFaceTB/SmolLM2-135M",
            "role": "core5 local sanity baseline",
            "reason": "Use the existing tiny local baseline before spending GPU money.",
        },
        "dataset_manifest": str(dataset_manifest),
        "output_root": f"runs/{experiment_id}/smollm2_135m",
        "format": {
            "prompt_template": "### Input:\n{input}\n\n### Response:\n",
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
            variant: f"python3 scripts/train_tiny_causal_lm.py --config {output_dir / 'training_config.json'} --variant {variant}"
            for variant in variants
        },
        "notes": [
            "This is a JSONL model-ready curriculum, not a shared-tokenizer nanochat run yet.",
            "Run dry-runs before training.",
            "Held-out transfer prompts remain outside training.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-id", default="core5_v0")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/core5_v0"),
    )
    parser.add_argument("--variant", action="append", choices=VARIANTS, help="Variant to render. May be repeated.")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--dev-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_ratios(args.train_ratio, args.dev_ratio, args.test_ratio)
    variants = args.variant or list(VARIANTS)
    ensure_output_dir(args.output_dir, args.overwrite)

    all_examples: list[Example] = []
    domain_stats: dict[str, Any] = {}
    nodes_by_graph: dict[str, dict[str, dict[str, Any]]] = {}
    source_graphs: dict[str, str] = {}

    for domain in DOMAIN_SPECS:
        graph, examples, counts = generate_domain_examples(domain)
        graph_id = graph["graph_id"]
        nodes_by_graph[graph_id] = variant_render.graph_nodes(graph)
        source_graphs[domain["domain_id"]] = str(domain["seed"])
        domain_stats[domain["domain_id"]] = {
            "label": domain["label"],
            "graph_id": graph_id,
            **counts,
            "task_type_counts": counts_by_task(examples),
        }
        all_examples.extend(examples)

    all_examples = sorted(all_examples, key=lambda example: example["id"])
    curriculum_path = args.output_dir / "curriculum.jsonl"
    write_jsonl(curriculum_path, all_examples)

    splits = stratified_split(all_examples, args.train_ratio, args.dev_ratio, args.test_ratio, args.seed)
    split_paths: dict[str, Path] = {}
    for split_name in SPLITS:
        path = args.output_dir / f"{split_name}.jsonl"
        write_jsonl(path, splits[split_name])
        split_paths[split_name] = path

    heldout_path, heldout_prompt_path, heldout_stats = merge_heldout(args.output_dir)

    dataset_dir = args.output_dir / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict[str, list[VariantRecord]]] = {
        variant: {split_name: [] for split_name in SPLITS}
        for variant in variants
    }
    dataset_paths: dict[str, Path] = {}

    for split_name in SPLITS:
        for variant in variants:
            rows = [
                make_record(args.experiment_id, variant, split_name, example, nodes_by_graph)
                for example in splits[split_name]
            ]
            records[variant][split_name] = rows
            path = dataset_dir / variant / f"{split_name}.jsonl"
            write_jsonl(path, rows)
            dataset_paths[f"{variant}.{split_name}"] = path

    validate_matched_variants(records, variants)

    dataset_manifest_path = dataset_dir / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "source_experiment_dir": str(args.output_dir),
        "source_graph": None,
        "source_graphs": source_graphs,
        "output_dir": str(dataset_dir),
        "variants": {
            variant: {
                split_name: {
                    "total": len(records[variant][split_name]),
                    "task_type_counts": counts_by_task(records[variant][split_name]),
                    "domain_counts": counts_by_domain(records[variant][split_name]),
                }
                for split_name in SPLITS
            }
            for variant in variants
        },
        "outputs": output_file_manifest(dataset_paths),
        "notes": [
            "All variants preserve source_example_id, split, task_type, and domain membership.",
            "Only input and target representation differ by variant.",
            "Held-out transfer prompts remain shared and are not included in these training variants.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)

    training_config_path = args.output_dir / "training_config.json"
    write_json(training_config_path, build_training_config(args.experiment_id, dataset_manifest_path, args.output_dir, variants))

    manifest_path = args.output_dir / "manifest.json"
    split_summary = {
        split_name: {
            "total": len(rows),
            "task_type_counts": counts_by_task(rows),
            "domain_counts": counts_by_domain(rows),
        }
        for split_name, rows in splits.items()
    }
    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "curriculum_jsonl": str(curriculum_path),
        "curriculum_sha256": sha256_file(curriculum_path),
        "seed": args.seed,
        "ratios": {
            "train": args.train_ratio,
            "dev": args.dev_ratio,
            "curriculum_test": args.test_ratio,
        },
        "domains": domain_stats,
        "total_examples": len(all_examples),
        "task_type_counts": counts_by_task(all_examples),
        "splits": split_summary,
        "heldout": {
            "path": str(heldout_path),
            "prompts_path": str(heldout_prompt_path),
            **heldout_stats,
        },
        "dataset_manifest": str(dataset_manifest_path),
        "training_config": str(training_config_path),
        "outputs": output_file_manifest({
            "curriculum": curriculum_path,
            "train": split_paths["train"],
            "dev": split_paths["dev"],
            "curriculum_test": split_paths["curriculum_test"],
            "heldout": heldout_path,
            "heldout_prompts": heldout_prompt_path,
            "dataset_manifest": dataset_manifest_path,
            "training_config": training_config_path,
        }),
    }
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
