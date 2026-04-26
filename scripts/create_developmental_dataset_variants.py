#!/usr/bin/env python3
"""Create matched dataset variants from experiment curriculum splits.

The variants keep the same source example IDs and split membership:

- plain_text: ordinary natural-language inputs and targets, no relation IDs
- flat_triples: ConceptNet-style source/type/target triples
- relation_scaffolded: the original scaffolded prompt with structured JSON target

Held-out transfer prompts are not converted here. They remain shared evaluation
prompts so model variants are compared against the same transfer set.
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


Example = dict[str, Any]
VariantRecord = dict[str, Any]

SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = ("plain_text", "flat_triples", "relation_scaffolded")
NODE_REF_RE = re.compile(r"([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)")
LABELED_NODE_REF_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9 /,_'-]*?)\s+\(([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)\)")


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
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite to replace dataset variants")
    if path.exists() and overwrite:
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def graph_nodes(graph: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not graph:
        return {}
    return {node["id"]: node for node in graph.get("nodes", []) if isinstance(node, dict) and "id" in node}


def id_tail(identifier: str) -> str:
    return identifier.split(".")[-1].replace("_", " ")


def node_label(nodes: dict[str, dict[str, Any]], identifier: str | None, include_id: bool = False) -> str:
    if not isinstance(identifier, str) or not identifier:
        return ""
    label = nodes.get(identifier, {}).get("label") or id_tail(identifier)
    if include_id:
        return f"{label} ({identifier})"
    return label


def rel_text(rel_type: str | None) -> str:
    if not isinstance(rel_type, str):
        return ""
    return rel_type.replace("_", " ")


def plain_relation(nodes: dict[str, dict[str, Any]], relation: dict[str, Any]) -> str:
    source = node_label(nodes, relation.get("source"))
    target = node_label(nodes, relation.get("target"))
    relation_type = rel_text(relation.get("type"))
    if relation_type == "built from":
        return f"{source} is built from {target}"
    if relation_type == "has property":
        return f"{source} has property {target}"
    if relation_type == "can cause":
        return f"{source} can cause {target}"
    if relation_type == "contrasts with":
        return f"{source} contrasts with {target}"
    return f"{source} {relation_type} {target}".strip()


def flat_relation(relation: dict[str, Any]) -> str:
    source = relation.get("source", "")
    target = relation.get("target", "")
    relation_type = relation.get("type", "")
    return f"{source} --{relation_type}--> {target}"


def replace_ids_with_labels(text: str, nodes: dict[str, dict[str, Any]]) -> str:
    def replace_labeled(match: re.Match[str]) -> str:
        identifier = match.group(2)
        if identifier in nodes:
            return node_label(nodes, identifier)
        return match.group(1).strip()

    def replace(match: re.Match[str]) -> str:
        identifier = match.group(1)
        if identifier in nodes:
            return node_label(nodes, identifier)
        return id_tail(identifier)

    text = LABELED_NODE_REF_RE.sub(replace_labeled, text)
    text = NODE_REF_RE.sub(replace, text)
    text = re.sub(r"\s+\)", ")", text)
    return text


def compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def relation_completion_plain(example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    target = example["target"]
    source = node_label(nodes, target.get("source"))
    target_label = node_label(nodes, target.get("target"))
    relation_type = rel_text(target.get("type"))
    input_text = f"What does {source} connect to through the relation '{relation_type}'?"
    output_text = target_label
    return input_text, output_text


def relation_completion_flat(example: Example, _nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    target = example["target"]
    input_text = (
        "Complete the triple.\n"
        f"source: {target.get('source')}\n"
        f"relation: {target.get('type')}\n"
        "target:"
    )
    output_text = str(target.get("target", ""))
    return input_text, output_text


def state_action_plain(example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    input_text = replace_ids_with_labels(example["input"], nodes)
    input_text = input_text.replace("RELATIONS_OBSERVED:", "What relation changes are observed?")
    observed = example["target"].get("relations_observed", [])
    output_text = "\n".join(f"- {plain_relation(nodes, relation)}." for relation in observed)
    return input_text, output_text


def state_action_flat(example: Example, _nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    input_text = example["input"]
    observed = example["target"].get("relations_observed", [])
    output_text = "\n".join(flat_relation(relation) for relation in observed)
    return input_text, output_text


def counterfactual_plain(example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    input_text = replace_ids_with_labels(example["input"], nodes)
    target = example["target"]
    if {"object_a", "object_b", "property_a", "property_b"} <= set(target):
        object_a = node_label(nodes, target["object_a"])
        object_b = node_label(nodes, target["object_b"])
        property_a = node_label(nodes, target["property_a"])
        property_b = node_label(nodes, target["property_b"])
        output_text = f"Replacing {object_a} with {object_b} changes the active property from {property_a} to {property_b}."
    else:
        relation = target.get("contrast_relation", {})
        source = node_label(nodes, relation.get("source"))
        target_label = node_label(nodes, relation.get("target"))
        source_summary = target.get("source_summary", "")
        target_summary = target.get("target_summary", "")
        output_text = f"{source} contrasts with {target_label}. {source_summary} {target_summary}".strip()
    return input_text, output_text


def counterfactual_flat(example: Example, _nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    target = example["target"]
    relation = target.get("contrast_relation", {})
    if {"object_a", "object_b", "property_a", "property_b"} <= set(target):
        input_text = (
            "Object contrast.\n"
            f"object_a: {target['object_a']}\n"
            f"property_a: {target['property_a']}\n"
            f"object_b: {target['object_b']}\n"
            f"property_b:"
        )
        output_text = target["property_b"]
    else:
        input_text = (
            "Complete the contrast triple.\n"
            f"source: {relation.get('source')}\n"
            f"relation: {relation.get('type')}\n"
            "target:"
        )
        output_text = str(relation.get("target", ""))
    return input_text, output_text


def explanation_plain(example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    target = example["target"]
    question = ""
    for line in example["input"].splitlines():
        if line.startswith("QUESTION:"):
            question = line.removeprefix("QUESTION:").strip()
            break
    input_text = question or replace_ids_with_labels(example["input"], nodes)
    output_text = target.get("expected_answer", example.get("text_target", ""))
    return input_text, output_text


def explanation_flat(example: Example, _nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    target = example["target"]
    question = ""
    for line in example["input"].splitlines():
        if line.startswith("QUESTION:"):
            question = line.removeprefix("QUESTION:").strip()
            break
    relations = target.get("expected_relations", [])
    input_text = f"Question: {question}\nExpected triples:"
    output_text = "\n".join(flat_relation(relation) for relation in relations)
    if target.get("expected_answer"):
        output_text = f"{output_text}\nanswer: {target['expected_answer']}".strip()
    return input_text, output_text


def relation_family_labels(nodes: dict[str, dict[str, Any]], family_ids: list[str]) -> str:
    return ", ".join(node_label(nodes, family_id) for family_id in family_ids)


def relation_family_id_lines(family_ids: list[str]) -> str:
    return "\n".join(family_ids)


def node_bridge_plain(example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    input_text = replace_ids_with_labels(example["input"], nodes).replace("NODE_ID:", "CONCEPT:")
    target = example["target"]
    output_text = node_label(nodes, target.get("node_id"))
    return input_text, output_text


def node_bridge_flat(example: Example, _nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    input_text = example["input"]
    output_text = str(example["target"].get("node_id", ""))
    return input_text, output_text


def relation_family_bridge_plain(example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    input_text = (
        replace_ids_with_labels(example["input"], nodes)
        .replace("relation family IDs", "relation families")
        .replace("RELATION_FAMILY_IDS:", "RELATION_FAMILIES:")
    )
    output_text = relation_family_labels(nodes, example["target"].get("relation_family_ids", []))
    return input_text, output_text


def relation_family_bridge_flat(example: Example, _nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    input_text = example["input"]
    output_text = relation_family_id_lines(example["target"].get("relation_family_ids", []))
    return input_text, output_text


def graph_anchor_bridge_plain(example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    input_text = (
        replace_ids_with_labels(example["input"], nodes)
        .replace("graph anchor IDs", "physical relations")
        .replace("GRAPH_ANCHORS:", "RELATIONS:")
    )
    anchors = example["target"].get("graph_anchors", [])
    output_text = "\n".join(f"- {plain_relation(nodes, relation)}." for relation in anchors)
    return input_text, output_text


def graph_anchor_bridge_flat(example: Example, _nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    input_text = example["input"]
    anchors = example["target"].get("graph_anchors", [])
    output_text = "\n".join(flat_relation(relation) for relation in anchors)
    return input_text, output_text


def explanation_with_relations_plain(example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    input_text = (
        replace_ids_with_labels(example["input"], nodes)
        .replace("relation families used", "relation families used")
        .replace("ANSWER_WITH_RELATIONS:", "ANSWER:")
    )
    target = example["target"]
    families = relation_family_labels(nodes, target.get("relation_family_ids", []))
    output_text = f"{target.get('answer', '')} Relation families: {families}.".strip()
    return input_text, output_text


def explanation_with_relations_flat(example: Example, _nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    target = example["target"]
    family_lines = relation_family_id_lines(target.get("relation_family_ids", []))
    anchor_lines = "\n".join(flat_relation(relation) for relation in target.get("graph_anchors", []))
    input_text = example["input"]
    output_text = (
        f"relation_family_ids:\n{family_lines}\n"
        f"graph_anchors:\n{anchor_lines}\n"
        f"answer: {target.get('answer', '')}"
    ).strip()
    return input_text, output_text


def relation_scaffolded(example: Example, _nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    return example["input"], compact_json(example["target"])


def variant_pair(variant: str, example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    task_type = example["task_type"]
    if variant == "relation_scaffolded":
        return relation_scaffolded(example, nodes)
    if variant == "plain_text":
        if task_type == "relation_completion":
            return relation_completion_plain(example, nodes)
        if task_type == "state_action_effect":
            return state_action_plain(example, nodes)
        if task_type == "counterfactual_contrast":
            return counterfactual_plain(example, nodes)
        if task_type == "explanation_path":
            return explanation_plain(example, nodes)
        if task_type == "node_id_from_paraphrase":
            return node_bridge_plain(example, nodes)
        if task_type == "relation_family_from_prompt":
            return relation_family_bridge_plain(example, nodes)
        if task_type == "graph_anchor_from_prompt":
            return graph_anchor_bridge_plain(example, nodes)
        if task_type == "explanation_with_relations":
            return explanation_with_relations_plain(example, nodes)
    if variant == "flat_triples":
        if task_type == "relation_completion":
            return relation_completion_flat(example, nodes)
        if task_type == "state_action_effect":
            return state_action_flat(example, nodes)
        if task_type == "counterfactual_contrast":
            return counterfactual_flat(example, nodes)
        if task_type == "explanation_path":
            return explanation_flat(example, nodes)
        if task_type == "node_id_from_paraphrase":
            return node_bridge_flat(example, nodes)
        if task_type == "relation_family_from_prompt":
            return relation_family_bridge_flat(example, nodes)
        if task_type == "graph_anchor_from_prompt":
            return graph_anchor_bridge_flat(example, nodes)
        if task_type == "explanation_with_relations":
            return explanation_with_relations_flat(example, nodes)
    raise ValueError(f"unsupported variant/task pair: {variant}/{task_type}")


def make_record(
    experiment_id: str,
    variant: str,
    split_name: str,
    example: Example,
    nodes: dict[str, dict[str, Any]],
) -> VariantRecord:
    input_text, target_text = variant_pair(variant, example, nodes)
    if not input_text.strip() or not target_text.strip():
        raise ValueError(f"empty input or target for {variant}/{example['id']}")

    record_id = f"dataset.{experiment_id}.{variant}.{example['id']}"
    return {
        "id": record_id,
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
            "graph_id": example.get("graph_id"),
            "representation": variant,
        },
    }


def counts_by_task(rows: list[VariantRecord]) -> dict[str, int]:
    return dict(sorted(Counter(row["task_type"] for row in rows).items()))


def load_experiment_manifest(experiment_dir: Path) -> dict[str, Any]:
    manifest_path = experiment_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing experiment manifest: {manifest_path}")
    return load_json(manifest_path)


def infer_source_graph(experiment_manifest: dict[str, Any]) -> Path | None:
    source_graph = experiment_manifest.get("source_graph")
    if isinstance(source_graph, str):
        return Path(source_graph)
    # The physical v0 split manifest points to the curriculum manifest, which
    # contains the source graph path.
    curriculum_manifest = experiment_manifest.get("sources", {}).get("curriculum_manifest")
    if isinstance(curriculum_manifest, str) and Path(curriculum_manifest).exists():
        data = load_json(Path(curriculum_manifest))
        if isinstance(data.get("source_graph"), str):
            return Path(data["source_graph"])
    return None


def validate_matched_variants(records: dict[str, dict[str, list[VariantRecord]]]) -> None:
    for split_name in SPLITS:
        source_sets = {
            variant: {row["source_example_id"] for row in records[variant][split_name]}
            for variant in VARIANTS
        }
        expected = source_sets["relation_scaffolded"]
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


def build_manifest(
    experiment_id: str,
    experiment_dir: Path,
    output_dir: Path,
    graph_path: Path | None,
    records: dict[str, dict[str, list[VariantRecord]]],
    output_paths: dict[str, Path],
) -> dict[str, Any]:
    variants: dict[str, Any] = {}
    for variant in VARIANTS:
        variants[variant] = {
            split_name: {
                "total": len(records[variant][split_name]),
                "task_type_counts": counts_by_task(records[variant][split_name]),
            }
            for split_name in SPLITS
        }
    return {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "source_experiment_dir": str(experiment_dir),
        "source_graph": str(graph_path) if graph_path else None,
        "output_dir": str(output_dir),
        "variants": variants,
        "outputs": output_file_manifest(output_paths),
        "notes": [
            "All variants preserve source_example_id, split, and task_type.",
            "Only input and target representation differ by variant.",
            "Held-out transfer prompts remain shared and are not included in these training variants.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path, help="Experiment split directory, e.g. physical_v0")
    parser.add_argument("--source-graph", type=Path, help="Source graph JSON for natural-language labels")
    parser.add_argument("--output-dir", type=Path, help="Output directory. Defaults to <experiment_dir>/datasets")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing the output directory")
    args = parser.parse_args()

    experiment_manifest = load_experiment_manifest(args.experiment_dir)
    experiment_id = experiment_manifest.get("experiment_id", args.experiment_dir.name)
    graph_path = args.source_graph or infer_source_graph(experiment_manifest)
    graph = load_json(graph_path) if graph_path and graph_path.exists() else None
    nodes = graph_nodes(graph)

    output_dir = args.output_dir or args.experiment_dir / "datasets"
    ensure_output_dir(output_dir, args.overwrite)

    records: dict[str, dict[str, list[VariantRecord]]] = {
        variant: {split_name: [] for split_name in SPLITS}
        for variant in VARIANTS
    }
    output_paths: dict[str, Path] = {}

    for split_name in SPLITS:
        examples = load_jsonl(args.experiment_dir / f"{split_name}.jsonl")
        for variant in VARIANTS:
            rows = [make_record(experiment_id, variant, split_name, example, nodes) for example in examples]
            records[variant][split_name] = rows
            path = output_dir / variant / f"{split_name}.jsonl"
            write_jsonl(path, rows)
            output_paths[f"{variant}.{split_name}"] = path

    validate_matched_variants(records)

    manifest_path = output_dir / "manifest.json"
    manifest = build_manifest(experiment_id, args.experiment_dir, output_dir, graph_path, records, output_paths)
    write_json(manifest_path, manifest)

    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
