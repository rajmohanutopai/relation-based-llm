#!/usr/bin/env python3
"""Create a binary candidate-scoring experiment.

physical_v0_2 used multi-select generation and the model often over-selected.
This v0.3-style generator turns each candidate into its own YES/NO judgment:

    prompt + one candidate relation family -> YES/NO
    prompt + one candidate graph anchor -> YES/NO

The held-out prompt file also has one row per candidate so evaluation can
reconstruct exact predicted sets from independent binary decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from create_candidate_selection_experiment import (
    SPLITS,
    anchor_options,
    choice_seed,
    compact_relation,
    counts_by_task,
    ensure_output_dir,
    format_anchor_options,
    format_gap_options,
    format_relation_family_options,
    gap_options,
    graph_relations,
    load_json,
    load_jsonl,
    node_label,
    node_map,
    ordered_unique,
    output_file_manifest,
    relation_candidates,
    relation_family_candidates,
    relation_family_options,
    relation_key,
    relation_text,
    relation_unique,
    stable_sample,
    strip_answer_marker,
    target_anchors,
    target_relation_family_ids,
    write_json,
    write_jsonl,
)


VARIANT = "binary_candidate_scoring"


def yes_no(value: bool) -> str:
    return "YES" if value else "NO"


def binary_target(value: bool) -> str:
    return f"ANSWER: {yes_no(value)}"


def balanced_binary_options(
    options: list[dict[str, Any]],
    is_positive: Any,
    negative_multiplier: int,
    rng: Any,
) -> list[dict[str, Any]]:
    positives = [option for option in options if is_positive(option)]
    negatives = [option for option in options if not is_positive(option)]
    if not positives:
        return options

    negative_limit = min(len(negatives), max(2, len(positives) * negative_multiplier))
    negative_by_option = {option["option"]: option for option in negatives}
    selected_negative_ids = stable_sample(list(negative_by_option), negative_limit, rng)
    selected_options = positives + [negative_by_option[option_id] for option_id in selected_negative_ids]
    return sorted(selected_options, key=lambda option: option["option"])


def make_record(
    experiment_id: str,
    split_name: str,
    source_example: dict[str, Any],
    selector_type: str,
    candidate_option: str,
    input_text: str,
    expected: bool,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    source_id = source_example["id"]
    record_id = f"dataset.{experiment_id}.{VARIANT}.{source_id}.{selector_type}.{candidate_option}"
    target_text = binary_target(expected)
    return {
        "id": record_id,
        "source_example_id": source_id,
        "source_task_type": source_example.get("task_type"),
        "experiment_id": experiment_id,
        "variant": VARIANT,
        "split": split_name,
        "task_type": selector_type,
        "input": input_text,
        "target": target_text,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target_text},
        ],
        "metadata": {
            "graph_id": source_example.get("graph_id"),
            "representation": VARIANT,
            "candidate_option": candidate_option,
            "expected": expected,
            **metadata,
        },
    }


def family_prompt(source_task: str, source_prompt: str, option: dict[str, str]) -> str:
    return (
        "Binary relation judgment. Answer exactly YES or NO.\n"
        f"SOURCE_TASK: {source_task}\n"
        f"PROMPT:\n{source_prompt}\n\n"
        "CANDIDATE_RELATION_FAMILY:\n"
        f"OPTION: {option['option']}\n"
        f"ID: {option['relation_family_id']}\n"
        f"LABEL: {option['label']}\n\n"
        "Is this candidate relation family needed to answer the prompt?\n"
        "OUTPUT:"
    )


def anchor_prompt(source_task: str, source_prompt: str, option: dict[str, Any]) -> str:
    return (
        "Binary graph-anchor judgment. Answer exactly YES or NO.\n"
        f"SOURCE_TASK: {source_task}\n"
        f"PROMPT:\n{source_prompt}\n\n"
        "CANDIDATE_GRAPH_ANCHOR:\n"
        f"OPTION: {option['option']}\n"
        f"ANCHOR: {option['text']}\n\n"
        "Is this exact graph anchor needed to answer the prompt?\n"
        "OUTPUT:"
    )


def gap_prompt(question: str, option: dict[str, str]) -> str:
    return (
        "Binary missing-relation judgment. Answer exactly YES or NO.\n"
        f"QUESTION: {question}\n\n"
        "CANDIDATE_GAP_RELATION:\n"
        f"OPTION: {option['option']}\n"
        f"ID: {option['gap_id']}\n\n"
        "Is this candidate relation needed but missing from the current seed graph?\n"
        "OUTPUT:"
    )


def build_binary_records(
    experiment_id: str,
    split_name: str,
    examples: list[dict[str, Any]],
    graph: dict[str, Any],
    candidate_count: int,
    negative_multiplier: int,
    seed: int,
) -> list[dict[str, Any]]:
    nodes = node_map(graph)
    all_family_ids = sorted(node_id for node_id in nodes if not node_id.startswith("object."))
    all_relations = graph_relations(graph)

    records: list[dict[str, Any]] = []
    for example in examples:
        source_prompt = strip_answer_marker(example.get("input", ""))
        source_task = str(example.get("task_type") or "unknown")
        anchors = target_anchors(example)
        family_ids = target_relation_family_ids(example, anchors)
        base_metadata = {
            "source_input": example.get("input"),
            "source_text_target": example.get("text_target"),
        }

        if family_ids:
            rng = choice_seed(seed, example["id"], "binary_families")
            candidates = relation_family_candidates(family_ids, all_family_ids, nodes, candidate_count, rng)
            options = relation_family_options(candidates, nodes)
            expected = set(family_ids)
            selected_options = balanced_binary_options(
                options,
                lambda option: option["relation_family_id"] in expected,
                negative_multiplier,
                rng,
            )
            for option in selected_options:
                relation_id = option["relation_family_id"]
                is_expected = relation_id in expected
                input_text = family_prompt(source_task, source_prompt, option)
                records.append(
                    make_record(
                        experiment_id,
                        split_name,
                        example,
                        "relation_family_binary_judgment",
                        option["option"],
                        input_text,
                        is_expected,
                        {
                            **base_metadata,
                            "candidate_type": "relation_family",
                            "candidate_relation_family_id": relation_id,
                            "candidate_relation_family_label": option["label"],
                            "candidate_relation_family_options": options,
                            "expected_relation_family_ids": family_ids,
                        },
                    )
                )

        if anchors:
            rng = choice_seed(seed, example["id"], "binary_anchors")
            candidates = relation_candidates(anchors, all_relations, nodes, candidate_count, rng)
            options = anchor_options(candidates)
            expected = {relation_key(anchor) for anchor in anchors}
            selected_options = balanced_binary_options(
                options,
                lambda option: relation_key(option["graph_anchor"]) in expected,
                negative_multiplier,
                rng,
            )
            for option in selected_options:
                anchor = option["graph_anchor"]
                is_expected = relation_key(anchor) in expected
                input_text = anchor_prompt(source_task, source_prompt, option)
                records.append(
                    make_record(
                        experiment_id,
                        split_name,
                        example,
                        "graph_anchor_binary_judgment",
                        option["option"],
                        input_text,
                        is_expected,
                        {
                            **base_metadata,
                            "candidate_type": "graph_anchor",
                            "candidate_graph_anchor": anchor,
                            "candidate_graph_anchor_text": option["text"],
                            "candidate_graph_anchor_options": options,
                            "expected_graph_anchors": anchors,
                        },
                    )
                )

    return records


def heldout_binary_rows(
    heldout: dict[str, Any],
    graph: dict[str, Any],
    candidate_count: int,
    seed: int,
) -> list[dict[str, Any]]:
    nodes = node_map(graph)
    all_family_ids = sorted(node_id for node_id in nodes if not node_id.startswith("object."))
    all_relations = graph_relations(graph)
    all_gap_ids = sorted(
        {
            item
            for case in heldout.get("cases", [])
            for item in case.get("gap_indicators", [])
            if isinstance(item, str)
        }
    )

    rows: list[dict[str, Any]] = []
    for case in heldout.get("cases", []):
        case_id = case["id"]
        question = case.get("prompt", "")
        family_source_prompt = (
            "Which relation family IDs are needed for this physical situation?\n"
            f"QUESTION: {question}"
        )
        anchor_source_prompt = (
            "Identify the graph anchors needed to answer this physical question.\n"
            f"QUESTION: {question}"
        )
        family_ids = ordered_unique(case.get("expected_relation_families", []))
        anchors = relation_unique([relation for raw in case.get("graph_anchors", []) if (relation := compact_relation(raw))])
        gap_ids = ordered_unique(case.get("gap_indicators", []))

        family_candidates = relation_family_candidates(
            family_ids,
            all_family_ids,
            nodes,
            max(candidate_count, len(family_ids) + 4),
            choice_seed(seed, case_id, "heldout_binary_families"),
        )
        family_option_rows = relation_family_options(family_candidates, nodes)
        expected_families = set(family_ids)
        for option in family_option_rows:
            prompt_id = f"{case_id}.family.{option['option']}"
            input_text = family_prompt("relation_family_from_prompt", family_source_prompt, option)
            rows.append(
                {
                    "case_id": prompt_id,
                    "source_case_id": case_id,
                    "case_type": case.get("case_type"),
                    "candidate_type": "relation_family",
                    "candidate_option": option["option"],
                    "candidate_relation_family_id": option["relation_family_id"],
                    "candidate_relation_family_label": option["label"],
                    "expected": option["relation_family_id"] in expected_families,
                    "input": input_text,
                    "prompt": input_text,
                }
            )

        anchor_candidates = relation_candidates(
            anchors,
            all_relations,
            nodes,
            max(candidate_count, len(anchors) + 4),
            choice_seed(seed, case_id, "heldout_binary_anchors"),
        )
        anchor_option_rows = anchor_options(anchor_candidates)
        expected_anchors = {relation_key(anchor) for anchor in anchors}
        for option in anchor_option_rows:
            prompt_id = f"{case_id}.anchor.{option['option']}"
            anchor = option["graph_anchor"]
            input_text = anchor_prompt("graph_anchor_from_prompt", anchor_source_prompt, option)
            rows.append(
                {
                    "case_id": prompt_id,
                    "source_case_id": case_id,
                    "case_type": case.get("case_type"),
                    "candidate_type": "graph_anchor",
                    "candidate_option": option["option"],
                    "candidate_graph_anchor": anchor,
                    "candidate_graph_anchor_text": option["text"],
                    "expected": relation_key(anchor) in expected_anchors,
                    "input": input_text,
                    "prompt": input_text,
                }
            )

        if gap_ids:
            rng = choice_seed(seed, case_id, "heldout_binary_gaps")
            negatives = [gap_id for gap_id in all_gap_ids if gap_id not in gap_ids]
            gap_candidates = sorted(
                ordered_unique(gap_ids + stable_sample(negatives, max(2, min(4, len(negatives))), rng))
            )
            gap_option_rows = gap_options(gap_candidates)
            expected_gaps = set(gap_ids)
            for option in gap_option_rows:
                prompt_id = f"{case_id}.gap.{option['option']}"
                input_text = gap_prompt(question, option)
                rows.append(
                    {
                        "case_id": prompt_id,
                        "source_case_id": case_id,
                        "case_type": case.get("case_type"),
                        "candidate_type": "gap",
                        "candidate_option": option["option"],
                        "candidate_gap_id": option["gap_id"],
                        "expected": option["gap_id"] in expected_gaps,
                        "input": input_text,
                        "prompt": input_text,
                    }
                )

    return rows


def write_training_config(experiment_id: str, output_dir: Path) -> Path:
    path = output_dir / "training_config.json"
    config = {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "baseline_model": {
            "name": "HuggingFaceTB/SmolLM2-135M",
            "role": "tiny causal-transformer binary candidate-scoring baseline",
            "reason": "Keep the same baseline model while changing only the candidate-selection task shape.",
        },
        "dataset_manifest": str(output_dir / "datasets" / "manifest.json"),
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
            "train": f"python3 scripts/train_tiny_causal_lm.py --config {output_dir / 'training_config.json'} --variant {VARIANT}",
            "generate_heldout": (
                "python3 scripts/generate_heldout_outputs.py "
                f"--config {output_dir / 'training_config.json'} "
                f"--model-dir runs/{experiment_id}/smollm2_135m/{VARIANT}/final "
                f"--prompts {output_dir / 'heldout_prompts.jsonl'} "
                f"--output runs/{experiment_id}/smollm2_135m/{VARIANT}/heldout_outputs_binary_candidate_scoring.jsonl "
                f"--variant {VARIANT} --prompt-style raw --max-new-tokens 8"
            ),
            "score_logits": (
                "python3 scripts/score_binary_candidate_logits.py "
                f"--config {output_dir / 'training_config.json'} "
                f"--model-dir runs/{experiment_id}/smollm2_135m/{VARIANT}/final "
                f"--prompts {output_dir / 'heldout_prompts.jsonl'} "
                f"--output runs/{experiment_id}/smollm2_135m/{VARIANT}/heldout_logits_binary_candidate_scoring.jsonl "
                f"--variant {VARIANT}"
            ),
            "score_binary_candidate_scoring": (
                "python3 scripts/run_binary_candidate_evaluation.py "
                f"{output_dir / 'heldout.json'} "
                f"{output_dir / 'heldout_prompts.jsonl'} "
                f"runs/{experiment_id}/smollm2_135m/{VARIANT}/heldout_outputs_binary_candidate_scoring.jsonl "
                f"--output runs/{experiment_id}/smollm2_135m/{VARIANT}/heldout_binary_candidate_scores.json"
            ),
            "score_binary_candidate_scoring_topk": (
                "python3 scripts/run_binary_candidate_evaluation.py "
                f"{output_dir / 'heldout.json'} "
                f"{output_dir / 'heldout_prompts.jsonl'} "
                f"runs/{experiment_id}/smollm2_135m/{VARIANT}/heldout_logits_binary_candidate_scoring.jsonl "
                f"--selection-mode top_expected_count "
                f"--output runs/{experiment_id}/smollm2_135m/{VARIANT}/heldout_binary_candidate_scores_logits_topk.json"
            ),
        },
        "notes": [
            "This experiment changes multi-select generation into independent binary candidate judgments.",
            "The goal is to reduce v0.2 over-selection while keeping closed-vocabulary relation supervision.",
            "Held-out prompts remain outside training.",
        ],
    }
    write_json(path, config)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-experiment", type=Path, default=Path("data/developmental_graph/experiments/physical_v0_1"))
    parser.add_argument("--source-graph", type=Path, default=Path("data/developmental_graph/seeds/everyday_physical_world.json"))
    parser.add_argument("--heldout", type=Path, default=Path("data/developmental_graph/evaluations/everyday_physical_world_heldout.json"))
    parser.add_argument("--experiment-id", default="physical_v0_3")
    parser.add_argument("--output-dir", type=Path, help="Defaults to data/developmental_graph/experiments/<experiment-id>")
    parser.add_argument("--candidate-count", type=int, default=10)
    parser.add_argument("--negative-multiplier", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.candidate_count < 4:
        raise ValueError("--candidate-count must be at least 4")
    if args.negative_multiplier < 1:
        raise ValueError("--negative-multiplier must be at least 1")

    output_dir = args.output_dir or Path("data/developmental_graph/experiments") / args.experiment_id
    ensure_output_dir(output_dir, args.overwrite)

    graph = load_json(args.source_graph)
    heldout = load_json(args.heldout)
    source_manifest = load_json(args.source_experiment / "manifest.json")

    split_records: dict[str, list[dict[str, Any]]] = {}
    output_paths: dict[str, Path] = {}
    dataset_output_dir = output_dir / "datasets"
    variant_dir = dataset_output_dir / VARIANT

    for split_name in SPLITS:
        source_examples = load_jsonl(args.source_experiment / f"{split_name}.jsonl")
        records = build_binary_records(
            args.experiment_id,
            split_name,
            source_examples,
            graph,
            args.candidate_count,
            args.negative_multiplier,
            args.seed,
        )
        split_records[split_name] = records
        top_level_path = output_dir / f"{split_name}.jsonl"
        dataset_path = variant_dir / f"{split_name}.jsonl"
        write_jsonl(top_level_path, records)
        write_jsonl(dataset_path, records)
        output_paths[split_name] = top_level_path
        output_paths[f"datasets.{VARIANT}.{split_name}"] = dataset_path

    heldout_copy = output_dir / "heldout.json"
    shutil.copyfile(args.heldout, heldout_copy)
    output_paths["heldout"] = heldout_copy

    heldout_prompts = heldout_binary_rows(heldout, graph, args.candidate_count, args.seed)
    heldout_prompts_path = output_dir / "heldout_prompts.jsonl"
    write_jsonl(heldout_prompts_path, heldout_prompts)
    output_paths["heldout_prompts"] = heldout_prompts_path

    training_config_path = write_training_config(args.experiment_id, output_dir)
    output_paths["training_config"] = training_config_path

    dataset_manifest_path = dataset_output_dir / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "source_experiment_dir": str(args.source_experiment),
        "source_graph": str(args.source_graph),
        "output_dir": str(dataset_output_dir),
        "variants": {
            VARIANT: {
                split_name: {
                    "total": len(rows),
                    "task_type_counts": counts_by_task(rows),
                    "positive_count": sum(1 for row in rows if row["metadata"]["expected"]),
                    "negative_count": sum(1 for row in rows if not row["metadata"]["expected"]),
                }
                for split_name, rows in split_records.items()
            }
        },
        "outputs": output_file_manifest(
            {
                f"{VARIANT}.{split_name}": variant_dir / f"{split_name}.jsonl"
                for split_name in SPLITS
            }
        ),
        "notes": [
            "This dataset is model-ready; each input/target pair is a single binary YES/NO candidate judgment.",
            "Candidates use the same hard-negative strategy as physical_v0_2.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)
    output_paths["dataset_manifest"] = dataset_manifest_path

    manifest_path = output_dir / "manifest.json"
    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "source_experiment_dir": str(args.source_experiment),
        "source_experiment_id": source_manifest.get("experiment_id"),
        "source_graph": str(args.source_graph),
        "source_heldout": str(args.heldout),
        "seed": args.seed,
        "candidate_count": args.candidate_count,
        "negative_multiplier": args.negative_multiplier,
        "variant": VARIANT,
        "split_strategy": "derived_from_physical_v0_1_splits",
        "splits": {
            split_name: {
                "total": len(rows),
                "task_type_counts": counts_by_task(rows),
                "positive_count": sum(1 for row in rows if row["metadata"]["expected"]),
                "negative_count": sum(1 for row in rows if not row["metadata"]["expected"]),
            }
            for split_name, rows in split_records.items()
        },
        "heldout_prompt_count": len(heldout_prompts),
        "heldout_prompt_type_counts": dict(sorted(Counter(row["candidate_type"] for row in heldout_prompts).items())),
        "outputs": output_file_manifest(output_paths),
        "notes": [
            "physical_v0_3 changes multi-select candidate generation into binary YES/NO candidate scoring.",
            "Hard negatives come from same or nearby graph layers, node kinds, relation types, or related family IDs.",
            "No broad domain expansion is included.",
        ],
    }
    write_json(manifest_path, manifest)

    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
