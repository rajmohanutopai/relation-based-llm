#!/usr/bin/env python3
"""Validate generated developmental curriculum JSONL.

This validator checks the generated training examples, not the source graph.
It verifies JSONL structure, manifest counts, task contracts, and graph
references where a source graph is available.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$")
TASK_TYPES = {
    "relation_completion",
    "state_action_effect",
    "counterfactual_contrast",
    "explanation_path",
    "node_id_from_paraphrase",
    "relation_family_from_prompt",
    "graph_anchor_from_prompt",
    "explanation_with_relations",
}
REQUIRED_EXAMPLE_KEYS = {"id", "graph_id", "task_type", "input", "target", "text_target", "metadata"}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(ID_RE.match(value))


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def resolve_path(base_file: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return cwd_path
    return base_file.parent / path


def default_manifest_path(curriculum_path: Path) -> Path:
    return curriculum_path.with_suffix(".manifest.json")


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    examples: list[dict[str, Any]] = []
    errors: list[str] = []

    with path.open() as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                example = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no} invalid JSON: {exc}")
                continue
            if not isinstance(example, dict):
                errors.append(f"line {line_no} must be a JSON object")
                continue
            examples.append(example)

    return examples, errors


def graph_context(graph: dict[str, Any] | None) -> tuple[set[str], set[tuple[str, str, str]], set[str]]:
    if not graph:
        return set(), set(), set()
    node_ids = {node.get("id") for node in graph.get("nodes", []) if isinstance(node, dict)}
    layer_ids = {layer.get("id") for layer in graph.get("layers", []) if isinstance(layer, dict)}
    edges = {
        (relation.get("source"), relation.get("type"), relation.get("target"))
        for relation in graph.get("relations", [])
        if isinstance(relation, dict)
    }
    return node_ids, edges, node_ids | layer_ids


def validate_node_ref(value: Any, field_name: str, prefix: str, node_ids: set[str], errors: list[str]) -> None:
    require(valid_id(value), f"{prefix} invalid {field_name}: {value!r}", errors)
    if node_ids and valid_id(value):
        require(value in node_ids, f"{prefix} {field_name} missing from graph: {value}", errors)


def validate_id_ref(value: Any, field_name: str, prefix: str, valid_ids: set[str], errors: list[str]) -> None:
    require(valid_id(value), f"{prefix} invalid {field_name}: {value!r}", errors)
    if valid_ids and valid_id(value):
        require(value in valid_ids, f"{prefix} {field_name} missing from graph or layers: {value}", errors)


def validate_relation_object(
    relation: Any,
    prefix: str,
    node_ids: set[str],
    edges: set[tuple[str, str, str]],
    errors: list[str],
    require_edge: bool,
) -> None:
    require(isinstance(relation, dict), f"{prefix} must be an object", errors)
    if not isinstance(relation, dict):
        return
    source = relation.get("source")
    rel_type = relation.get("type")
    target = relation.get("target")
    validate_node_ref(source, "source", prefix, node_ids, errors)
    require(isinstance(rel_type, str) and rel_type, f"{prefix} missing type", errors)
    validate_node_ref(target, "target", prefix, node_ids, errors)
    if require_edge and edges and valid_id(source) and isinstance(rel_type, str) and valid_id(target):
        require((source, rel_type, target) in edges, f"{prefix} edge missing from graph: {source} --{rel_type}--> {target}", errors)


def validate_relation_completion(
    example: dict[str, Any],
    prefix: str,
    node_ids: set[str],
    edges: set[tuple[str, str, str]],
    valid_ids: set[str],
    errors: list[str],
) -> None:
    target = example.get("target")
    validate_relation_object(target, f"{prefix}.target", node_ids, edges, errors, require_edge=True)
    if not isinstance(target, dict):
        return
    require("target_label" in target, f"{prefix}.target missing target_label", errors)
    built_from = target.get("built_from", [])
    require(isinstance(built_from, list), f"{prefix}.target built_from must be a list", errors)
    if isinstance(built_from, list):
        for idx, item in enumerate(built_from):
            validate_id_ref(item, f"built_from[{idx}]", f"{prefix}.target", valid_ids, errors)


def validate_state_action_effect(
    example: dict[str, Any],
    prefix: str,
    node_ids: set[str],
    errors: list[str],
) -> None:
    target = example.get("target")
    require(isinstance(target, dict), f"{prefix}.target must be an object", errors)
    if not isinstance(target, dict):
        return
    require(valid_id(target.get("experience_id")), f"{prefix}.target invalid experience_id", errors)
    observed = target.get("relations_observed")
    require(isinstance(observed, list), f"{prefix}.target relations_observed must be a list", errors)
    if isinstance(observed, list):
        for idx, relation in enumerate(observed):
            validate_relation_object(
                relation,
                f"{prefix}.target.relations_observed[{idx}]",
                node_ids,
                set(),
                errors,
                require_edge=False,
            )


def validate_counterfactual_contrast(
    example: dict[str, Any],
    prefix: str,
    node_ids: set[str],
    edges: set[tuple[str, str, str]],
    errors: list[str],
) -> None:
    target = example.get("target")
    require(isinstance(target, dict), f"{prefix}.target must be an object", errors)
    if not isinstance(target, dict):
        return
    if "contrast_relation" in target:
        validate_relation_object(
            target["contrast_relation"],
            f"{prefix}.target.contrast_relation",
            node_ids,
            edges,
            errors,
            require_edge=True,
        )
    for field_name in ("object_a", "object_b", "property_a", "property_b"):
        if field_name in target:
            validate_node_ref(target[field_name], field_name, f"{prefix}.target", node_ids, errors)


def validate_explanation_path(
    example: dict[str, Any],
    prefix: str,
    node_ids: set[str],
    edges: set[tuple[str, str, str]],
    errors: list[str],
) -> None:
    target = example.get("target")
    require(isinstance(target, dict), f"{prefix}.target must be an object", errors)
    if not isinstance(target, dict):
        return
    require(valid_id(target.get("question_id")), f"{prefix}.target invalid question_id", errors)
    expected_relations = target.get("expected_relations")
    require(isinstance(expected_relations, list), f"{prefix}.target expected_relations must be a list", errors)
    if isinstance(expected_relations, list):
        for idx, relation in enumerate(expected_relations):
            validate_relation_object(
                relation,
                f"{prefix}.target.expected_relations[{idx}]",
                node_ids,
                edges,
                errors,
                require_edge=True,
            )


def validate_node_id_from_paraphrase(
    example: dict[str, Any],
    prefix: str,
    node_ids: set[str],
    errors: list[str],
) -> None:
    target = example.get("target")
    require(isinstance(target, dict), f"{prefix}.target must be an object", errors)
    if not isinstance(target, dict):
        return
    validate_node_ref(target.get("node_id"), "node_id", f"{prefix}.target", node_ids, errors)
    require(isinstance(target.get("node_label"), str) and target.get("node_label"), f"{prefix}.target missing node_label", errors)
    require(valid_id(target.get("layer")), f"{prefix}.target invalid layer", errors)
    require(isinstance(target.get("kind"), str) and target.get("kind"), f"{prefix}.target missing kind", errors)


def validate_relation_family_from_prompt(
    example: dict[str, Any],
    prefix: str,
    node_ids: set[str],
    errors: list[str],
) -> None:
    target = example.get("target")
    require(isinstance(target, dict), f"{prefix}.target must be an object", errors)
    if not isinstance(target, dict):
        return
    family_ids = target.get("relation_family_ids")
    require(isinstance(family_ids, list) and bool(family_ids), f"{prefix}.target relation_family_ids must be a non-empty list", errors)
    if isinstance(family_ids, list):
        for idx, node_id in enumerate(family_ids):
            validate_node_ref(node_id, f"relation_family_ids[{idx}]", f"{prefix}.target", node_ids, errors)
    if "graph_anchor_count" in target:
        require(isinstance(target["graph_anchor_count"], int) and target["graph_anchor_count"] >= 0, f"{prefix}.target graph_anchor_count must be a non-negative integer", errors)


def validate_graph_anchor_from_prompt(
    example: dict[str, Any],
    prefix: str,
    node_ids: set[str],
    edges: set[tuple[str, str, str]],
    errors: list[str],
) -> None:
    target = example.get("target")
    require(isinstance(target, dict), f"{prefix}.target must be an object", errors)
    if not isinstance(target, dict):
        return
    anchors = target.get("graph_anchors")
    require(isinstance(anchors, list) and bool(anchors), f"{prefix}.target graph_anchors must be a non-empty list", errors)
    if isinstance(anchors, list):
        for idx, relation in enumerate(anchors):
            validate_relation_object(
                relation,
                f"{prefix}.target.graph_anchors[{idx}]",
                node_ids,
                edges,
                errors,
                require_edge=True,
            )
    if "relation_family_ids" in target:
        validate_relation_family_from_prompt(example, prefix, node_ids, errors)


def validate_explanation_with_relations(
    example: dict[str, Any],
    prefix: str,
    node_ids: set[str],
    edges: set[tuple[str, str, str]],
    errors: list[str],
) -> None:
    target = example.get("target")
    require(isinstance(target, dict), f"{prefix}.target must be an object", errors)
    if not isinstance(target, dict):
        return
    require(isinstance(target.get("answer"), str) and target.get("answer").strip(), f"{prefix}.target answer must be non-empty", errors)
    validate_relation_family_from_prompt(example, prefix, node_ids, errors)
    anchors = target.get("graph_anchors")
    require(isinstance(anchors, list) and bool(anchors), f"{prefix}.target graph_anchors must be a non-empty list", errors)
    if isinstance(anchors, list):
        for idx, relation in enumerate(anchors):
            validate_relation_object(
                relation,
                f"{prefix}.target.graph_anchors[{idx}]",
                node_ids,
                edges,
                errors,
                require_edge=True,
            )


def validate_examples(
    examples: list[dict[str, Any]],
    manifest: dict[str, Any] | None,
    source_graph: dict[str, Any] | None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    node_ids, edges, valid_ids = graph_context(source_graph)

    expected_graph_id = None
    if manifest:
        expected_graph_id = manifest.get("graph_id")
    if source_graph:
        expected_graph_id = source_graph.get("graph_id")

    ids: list[str] = []
    counts: Counter[str] = Counter()
    for idx, example in enumerate(examples, start=1):
        prefix = f"example[{idx}]"
        missing = REQUIRED_EXAMPLE_KEYS - set(example)
        require(not missing, f"{prefix} missing keys: {sorted(missing)}", errors)

        example_id = example.get("id")
        ids.append(example_id)
        require(valid_id(example_id), f"{prefix} invalid id: {example_id!r}", errors)

        graph_id = example.get("graph_id")
        require(valid_id(graph_id), f"{prefix} invalid graph_id: {graph_id!r}", errors)
        if expected_graph_id:
            require(graph_id == expected_graph_id, f"{prefix} graph_id {graph_id!r} != expected {expected_graph_id!r}", errors)

        task_type = example.get("task_type")
        require(task_type in TASK_TYPES, f"{prefix} invalid task_type: {task_type!r}", errors)
        counts[task_type] += 1

        require(isinstance(example.get("input"), str) and example.get("input").strip(), f"{prefix} input must be non-empty", errors)
        require(
            isinstance(example.get("text_target"), str) and example.get("text_target").strip(),
            f"{prefix} text_target must be non-empty",
            errors,
        )
        require(isinstance(example.get("metadata"), dict), f"{prefix} metadata must be an object", errors)

        if task_type == "relation_completion":
            validate_relation_completion(example, prefix, node_ids, edges, valid_ids, errors)
        elif task_type == "state_action_effect":
            validate_state_action_effect(example, prefix, node_ids, errors)
        elif task_type == "counterfactual_contrast":
            validate_counterfactual_contrast(example, prefix, node_ids, edges, errors)
        elif task_type == "explanation_path":
            validate_explanation_path(example, prefix, node_ids, edges, errors)
        elif task_type == "node_id_from_paraphrase":
            validate_node_id_from_paraphrase(example, prefix, node_ids, errors)
        elif task_type == "relation_family_from_prompt":
            validate_relation_family_from_prompt(example, prefix, node_ids, errors)
        elif task_type == "graph_anchor_from_prompt":
            validate_graph_anchor_from_prompt(example, prefix, node_ids, edges, errors)
        elif task_type == "explanation_with_relations":
            validate_explanation_with_relations(example, prefix, node_ids, edges, errors)

    for example_id, count in Counter(ids).items():
        require(count == 1, f"duplicate example id: {example_id}", errors)

    count_dict = dict(sorted(counts.items()))
    if manifest:
        require(manifest.get("total_examples") == len(examples), "manifest total_examples does not match JSONL count", errors)
        require(manifest.get("counts") == count_dict, "manifest counts do not match JSONL task counts", errors)
        manifest_task_types = manifest.get("task_types")
        require(isinstance(manifest_task_types, list) and manifest_task_types, "manifest task_types must be a non-empty list", errors)
        if isinstance(manifest_task_types, list):
            unknown = sorted(task for task in manifest_task_types if task not in TASK_TYPES)
            require(not unknown, f"manifest has unknown task_types: {unknown}", errors)

    if not source_graph:
        warnings.append("source graph not loaded; graph reference checks were limited")

    stats = {
        "examples": len(examples),
        "task_type_counts": count_dict,
        "manifest_loaded": bool(manifest),
        "source_graph_loaded": bool(source_graph),
        "source_graph_id": source_graph.get("graph_id") if source_graph else None,
    }
    return errors, warnings, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("curriculum_jsonl", type=Path, help="Path to generated curriculum JSONL")
    parser.add_argument("--manifest", type=Path, help="Manifest JSON path. Defaults to JSONL path with .manifest.json suffix.")
    parser.add_argument("--allow-missing-manifest", action="store_true", help="Do not warn when no manifest exists")
    parser.add_argument("--source-graph", type=Path, help="Override source graph JSON path")
    parser.add_argument("--stats", action="store_true", help="Print validation statistics")
    args = parser.parse_args()

    examples, jsonl_errors = load_jsonl(args.curriculum_jsonl)

    manifest_path = args.manifest or default_manifest_path(args.curriculum_jsonl)
    manifest = load_json(manifest_path) if manifest_path.exists() else None
    if manifest is None and not args.allow_missing_manifest:
        print(f"WARNING: manifest not loaded from {manifest_path}", file=sys.stderr)

    source_graph = None
    if args.source_graph:
        source_graph = load_json(args.source_graph)
    elif manifest and isinstance(manifest.get("source_graph"), str):
        source_path = resolve_path(manifest_path, manifest["source_graph"])
        if source_path.exists():
            source_graph = load_json(source_path)
        else:
            print(f"WARNING: source graph not found at {source_path}", file=sys.stderr)

    errors, warnings, stats = validate_examples(examples, manifest, source_graph)
    errors = jsonl_errors + errors

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.curriculum_jsonl}")
    if args.stats:
        print(json.dumps(stats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
