#!/usr/bin/env python3
"""Create controlled-vocabulary variants for the core5 curriculum.

The regular core5_v0 data is useful as a structural dataset, but it contains a
lot of incidental vocabulary from natural prompts and JSON schema text. This
script keeps the same source examples and split membership while rendering
short, lower-case, fixed-template examples for a tiny from-scratch model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any
from output_state import retire_output_dir  # noqa: E402


SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = (
    "controlled_plain_text",
    "controlled_relation_scaffolded",
    "controlled_relation_first_then_text",
)
WORD_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")
RAW_RE = re.compile(r"\S+")
FIELD_RE_TEMPLATE = r"^{field}:\s*(.*)$"


Example = dict[str, Any]
Record = dict[str, Any]


TASK_LABELS = {
    "counterfactual_contrast": "compare case",
    "explanation_path": "answer path",
    "explanation_with_relations": "answer with relation",
    "graph_anchor_from_prompt": "find relation",
    "node_id_from_paraphrase": "name concept",
    "relation_completion": "complete relation",
    "relation_family_from_prompt": "choose family",
    "state_action_effect": "read event",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}: line {line_no} must be a JSON object")
            rows.append(row)
    return rows


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


def clean_text(value: Any) -> str:
    text = str(value or "").lower()
    replacements = {
        "6mo": "six month",
        "proto-self": "proto self",
        "self/non-self": "self non self",
        "->": " ",
        "--": " ",
        "_": " ",
        ".": " ",
        "/": " ",
        "'": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def id_tail(identifier: Any) -> str:
    return clean_text(str(identifier or "").split(".")[-1].replace("_", " "))


def relation_phrase(rel_type: Any) -> str:
    return clean_text(str(rel_type or "").replace("_", " "))


def load_nodes(source_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    dataset_manifest = load_json(source_dir / "datasets" / "manifest.json")
    nodes_by_graph: dict[str, dict[str, dict[str, Any]]] = {}
    for graph_path in dataset_manifest.get("source_graphs", {}).values():
        graph = load_json(Path(graph_path))
        graph_id = graph["graph_id"]
        nodes_by_graph[graph_id] = {
            node["id"]: node for node in graph.get("nodes", []) if isinstance(node, dict) and "id" in node
        }
    return nodes_by_graph


def node_phrase(nodes: dict[str, dict[str, Any]], identifier: Any) -> str:
    if not isinstance(identifier, str) or not identifier:
        return ""
    # Use ID tails rather than full labels for the controlled-vocabulary pass.
    # The tails still carry concept words like "ball", "caregiver", "same",
    # and "pain", but avoid verbose descriptive labels.
    return id_tail(identifier)


def domain_phrase(example: Example) -> str:
    label = example.get("metadata", {}).get("domain_label")
    return clean_text(label) or clean_text(example.get("metadata", {}).get("domain_id", "core"))


def task_phrase(example: Example) -> str:
    return TASK_LABELS.get(example.get("task_type", ""), clean_text(example.get("task_type", "task")))


def field_value(text: str, field: str) -> str:
    pattern = re.compile(FIELD_RE_TEMPLATE.format(field=re.escape(field)), flags=re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    return clean_text(match.group(1)) if match else ""


def question_text(example: Example) -> str:
    return field_value(str(example.get("input", "")), "QUESTION") or clean_text(example.get("input", ""))


def description_text(example: Example) -> str:
    return field_value(str(example.get("input", "")), "DESCRIPTION") or clean_text(example.get("input", ""))


def phrase_text(example: Example) -> str:
    return field_value(str(example.get("input", "")), "PHRASE") or clean_text(example.get("input", ""))


def title_text(example: Example) -> str:
    return field_value(str(example.get("input", "")), "TITLE")


def event_text(example: Example) -> str:
    events: list[str] = []
    in_events = False
    for line in str(example.get("input", "")).splitlines():
        stripped = line.strip()
        if stripped.upper() == "EVENTS:":
            in_events = True
            continue
        if in_events and stripped.startswith("-"):
            events.append(clean_text(stripped.removeprefix("-")))
        elif in_events and stripped and not stripped.startswith("-"):
            break
    return " then ".join(event for event in events if event)


def relation_text(relation: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> str:
    source = node_phrase(nodes, relation.get("source"))
    rel = relation_phrase(relation.get("type"))
    target = node_phrase(nodes, relation.get("target"))
    pieces = []
    if source:
        pieces.append(f"source {source}")
    if rel:
        pieces.append(f"rel {rel}")
    if target:
        pieces.append(f"target {target}")
    return " ".join(pieces)


def relation_list_text(relations: list[dict[str, Any]], nodes: dict[str, dict[str, Any]]) -> str:
    rendered = [relation_text(relation, nodes) for relation in relations]
    rendered = [item for item in rendered if item]
    return " ; ".join(rendered) if rendered else "none"


def family_text(family_ids: list[Any], nodes: dict[str, dict[str, Any]]) -> str:
    families = [node_phrase(nodes, family_id) or id_tail(family_id) for family_id in family_ids]
    families = [family for family in families if family]
    return " ; ".join(families) if families else "none"


def answer_text(value: Any) -> str:
    return clean_text(value)


def plain_pair(example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    target = example.get("target", {})
    task_type = example["task_type"]
    domain = domain_phrase(example)
    task = task_phrase(example)

    if task_type == "relation_completion":
        source = node_phrase(nodes, target.get("source"))
        rel = relation_phrase(target.get("type"))
        target_label = node_phrase(nodes, target.get("target"))
        return (
            f"task {task}. domain {domain}. source {source}. relation {rel}. answer target.",
            f"target {target_label}.",
        )

    if task_type == "state_action_effect":
        title = title_text(example)
        events = event_text(example)
        relations = relation_list_text(target.get("relations_observed", []), nodes)
        return (
            f"task {task}. domain {domain}. event {title}. steps {events}. answer relations.",
            f"relations {relations}.",
        )

    if task_type == "counterfactual_contrast":
        relation = target.get("contrast_relation", {})
        source = node_phrase(nodes, relation.get("source")) or node_phrase(nodes, target.get("object_a"))
        contrast = node_phrase(nodes, relation.get("target")) or node_phrase(nodes, target.get("object_b"))
        return (
            f"task {task}. domain {domain}. case a {source}. case b {contrast}. answer change.",
            f"{source} contrasts with {contrast}.",
        )

    if task_type == "explanation_path":
        relations = relation_list_text(target.get("expected_relations", []), nodes)
        answer = answer_text(target.get("expected_answer", example.get("text_target", "")))
        return (
            f"task {task}. domain {domain}. question {question_text(example)}. answer.",
            f"{answer}. relations {relations}.",
        )

    if task_type == "node_id_from_paraphrase":
        concept = node_phrase(nodes, target.get("node_id"))
        return (
            f"task {task}. domain {domain}. phrase {concept}. answer concept.",
            f"concept {concept}.",
        )

    if task_type == "relation_family_from_prompt":
        families = family_text(target.get("relation_family_ids", []), nodes)
        return (
            f"task {task}. domain {domain}. question {question_text(example)}. answer family.",
            f"family {families}.",
        )

    if task_type == "graph_anchor_from_prompt":
        anchors = relation_list_text(target.get("graph_anchors", []), nodes)
        return (
            f"task {task}. domain {domain}. text {description_text(example)}. answer relation.",
            f"relations {anchors}.",
        )

    if task_type == "explanation_with_relations":
        answer = answer_text(target.get("answer", example.get("text_target", "")))
        families = family_text(target.get("relation_family_ids", []), nodes)
        anchors = relation_list_text(target.get("graph_anchors", []), nodes)
        return (
            f"task {task}. domain {domain}. question {question_text(example)}. answer.",
            f"{answer}. family {families}. relations {anchors}.",
        )

    raise ValueError(f"unsupported task type: {task_type}")


def relation_packet(example: Example, nodes: dict[str, dict[str, Any]]) -> str:
    target = example.get("target", {})
    task_type = example["task_type"]
    parts = [
        f"domain {domain_phrase(example)}",
        f"task {task_phrase(example)}",
    ]

    if task_type == "relation_completion":
        parts.append(
            relation_text(
                {
                    "source": target.get("source"),
                    "type": target.get("type"),
                    "target": target.get("target"),
                },
                nodes,
            )
        )
    if task_type == "state_action_effect":
        parts.append(f"relations {relation_list_text(target.get('relations_observed', []), nodes)}")
    if task_type == "counterfactual_contrast":
        relation = target.get("contrast_relation", {})
        parts.append(f"relations {relation_text(relation, nodes)}")
    if task_type == "explanation_path":
        parts.append(f"relations {relation_list_text(target.get('expected_relations', []), nodes)}")
        if target.get("expected_answer"):
            parts.append(f"answer {answer_text(target.get('expected_answer'))}")
    if task_type == "node_id_from_paraphrase":
        parts.append(f"concept {node_phrase(nodes, target.get('node_id'))}")
    if task_type == "relation_family_from_prompt":
        parts.append(f"family {family_text(target.get('relation_family_ids', []), nodes)}")
    if task_type == "graph_anchor_from_prompt":
        parts.append(f"relations {relation_list_text(target.get('graph_anchors', []), nodes)}")
        parts.append(f"family {family_text(target.get('relation_family_ids', []), nodes)}")
    if task_type == "explanation_with_relations":
        parts.append(f"answer {answer_text(target.get('answer'))}")
        parts.append(f"family {family_text(target.get('relation_family_ids', []), nodes)}")
        parts.append(f"relations {relation_list_text(target.get('graph_anchors', []), nodes)}")

    clean_parts = [clean_text(part) for part in parts if clean_text(part)]
    return ". ".join(clean_parts) + "."


def render_pair(variant: str, example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    plain_input, plain_target = plain_pair(example, nodes)
    packet = relation_packet(example, nodes)

    if variant == "controlled_plain_text":
        return plain_input, plain_target
    if variant == "controlled_relation_scaffolded":
        return f"{plain_input} give relation packet.", packet
    if variant == "controlled_relation_first_then_text":
        return f"relation packet {packet} text prompt {plain_input}", f"text answer {plain_target}"
    raise ValueError(f"unknown variant: {variant}")


def make_record(
    experiment_id: str,
    variant: str,
    split_name: str,
    example: Example,
    nodes_by_graph: dict[str, dict[str, dict[str, Any]]],
) -> Record:
    graph_id = example.get("graph_id")
    nodes = nodes_by_graph.get(graph_id, {})
    input_text, target_text = render_pair(variant, example, nodes)
    if not input_text.strip() or not target_text.strip():
        raise ValueError(f"empty controlled record for {variant}/{example['id']}")
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
            "source_representation": "core5_v0",
            "vocabulary_policy": "controlled_lowercase_fixed_templates",
        },
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(key, "unknown") for row in rows).items()))


def domain_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row.get("metadata", {}).get("domain_id", "unknown") for row in rows).items()))


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    words: Counter[str] = Counter()
    raw: Counter[str] = Counter()
    for row in rows:
        text = f"{row.get('input', '')}\n{row.get('target', '')}".lower()
        words.update(WORD_RE.findall(text))
        raw.update(RAW_RE.findall(text))
    return {
        "unique_words_alpha": len(words),
        "total_words_alpha": sum(words.values()),
        "unique_raw_whitespace_tokens": len(raw),
        "total_raw_whitespace_tokens": sum(raw.values()),
        "top_words": dict(words.most_common(40)),
    }


def validate_matched(records: dict[str, dict[str, list[Record]]]) -> None:
    for split_name in SPLITS:
        expected: set[str] | None = None
        for variant in VARIANTS:
            source_ids = {row["source_example_id"] for row in records[variant][split_name]}
            if expected is None:
                expected = source_ids
            elif source_ids != expected:
                missing = sorted(expected - source_ids)[:5]
                extra = sorted(source_ids - expected)[:5]
                raise ValueError(f"{split_name}/{variant} source mismatch missing={missing} extra={extra}")


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
            "reason": "Use dry-run compatibility checks; actual controlled-vocabulary test should use nanochat.",
        },
        "dataset_manifest": str(dataset_manifest),
        "output_root": f"runs/{experiment_id}/smollm2_135m",
        "format": {
            "prompt_template": "input {input}\noutput",
            "target_template": " {target}",
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
        "notes": [
            "This config is for JSONL format checks only.",
            "The intended training path is nanochat from scratch with a shared tokenizer.",
        ],
    }


def copy_if_exists(source: Path, target: Path) -> Path | None:
    if not source.exists():
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("data/developmental_graph/experiments/core5_v0"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/core5_v0_controlled"),
    )
    parser.add_argument("--experiment-id", default="core5_v0_controlled")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ensure_output_dir(args.output_dir, args.overwrite)
    nodes_by_graph = load_nodes(args.source_dir)

    split_examples = {split: load_jsonl(args.source_dir / f"{split}.jsonl") for split in SPLITS}
    for split_name, rows in split_examples.items():
        write_jsonl(args.output_dir / f"{split_name}.jsonl", rows)

    records: dict[str, dict[str, list[Record]]] = {
        variant: {split_name: [] for split_name in SPLITS}
        for variant in VARIANTS
    }
    dataset_paths: dict[str, Path] = {}

    for variant in VARIANTS:
        for split_name in SPLITS:
            rows = [
                make_record(args.experiment_id, variant, split_name, example, nodes_by_graph)
                for example in split_examples[split_name]
            ]
            records[variant][split_name] = rows
            output_path = args.output_dir / "datasets" / variant / f"{split_name}.jsonl"
            write_jsonl(output_path, rows)
            dataset_paths[f"{variant}.{split_name}"] = output_path

    validate_matched(records)

    copied_paths: dict[str, Path] = {}
    for name in ("heldout.json", "heldout_prompts.jsonl"):
        copied = copy_if_exists(args.source_dir / name, args.output_dir / name)
        if copied:
            copied_paths[name.removesuffix(".json").removesuffix(".jsonl")] = copied

    dataset_manifest_path = args.output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "source_experiment_dir": str(args.source_dir),
        "output_dir": str(args.output_dir / "datasets"),
        "variants": {
            variant: {
                split_name: {
                    "total": len(records[variant][split_name]),
                    "task_type_counts": count_by(records[variant][split_name], "task_type"),
                    "domain_counts": domain_counts(records[variant][split_name]),
                    "vocabulary": vocab_stats(records[variant][split_name]),
                }
                for split_name in SPLITS
            }
            for variant in VARIANTS
        },
        "outputs": file_manifest(dataset_paths),
        "notes": [
            "All variants preserve source_example_id and split membership from core5_v0.",
            "Natural language is lower-case and rendered through fixed templates.",
            "Relation variants use compact text packets instead of verbose JSON.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)

    vocabulary_dir = args.output_dir / "vocabulary"
    vocabulary_dir.mkdir(parents=True, exist_ok=True)
    all_train_words: Counter[str] = Counter()
    for variant in VARIANTS:
        for row in records[variant]["train"]:
            all_train_words.update(WORD_RE.findall(f"{row['input']}\n{row['target']}".lower()))
    alpha_vocab_path = vocabulary_dir / "train_alpha_words.txt"
    alpha_vocab_path.write_text("\n".join(sorted(all_train_words)) + "\n")

    training_config_path = args.output_dir / "training_config.json"
    write_json(training_config_path, build_training_config(args.experiment_id, args.output_dir, dataset_manifest_path))

    manifest_path = args.output_dir / "manifest.json"
    output_paths = {
        **dataset_paths,
        "dataset_manifest": dataset_manifest_path,
        "training_config": training_config_path,
        "train_alpha_words": alpha_vocab_path,
    }
    output_paths.update(copied_paths)
    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "source_experiment_dir": str(args.source_dir),
        "source_manifest": str(args.source_dir / "manifest.json"),
        "controlled_policy": {
            "case": "lowercase",
            "templates": "fixed",
            "json_targets": "removed",
            "concept_labels": "kept as word handles",
        },
        "splits": {
            split_name: {
                "total": len(split_examples[split_name]),
                "task_type_counts": count_by(split_examples[split_name], "task_type"),
            }
            for split_name in SPLITS
        },
        "variants": list(VARIANTS),
        "vocabulary": {
            "train_unique_words_all_variants": len(all_train_words),
            "train_alpha_words_path": str(alpha_vocab_path),
        },
        "dataset_manifest": str(dataset_manifest_path),
        "training_config": str(training_config_path),
        "outputs": file_manifest(output_paths),
    }
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
