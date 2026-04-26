#!/usr/bin/env python3
"""Validate a held-out developmental evaluation JSON file.

This validator checks the project-specific contract for held-out evaluation
sets. It intentionally avoids third-party dependencies.

It validates:

- required top-level fields
- unique and well-formed evaluation/case IDs
- required case fields
- expected relation family IDs
- graph anchor endpoints and anchor edge existence in the source graph
- optional gap indicators as valid future relation IDs
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
STATUSES = {"draft", "heldout", "active", "archived"}
CASE_TYPES = {"transfer_probe", "gap_probe"}
SPLITS = {"train", "dev", "test", "heldout", "maybe"}


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


def load_source_graph(evaluation_path: Path, data: dict[str, Any], override: Path | None) -> dict[str, Any] | None:
    if override:
        return load_json(override)
    source_seed = data.get("source_seed")
    if not isinstance(source_seed, str) or not source_seed:
        return None
    source_path = resolve_path(evaluation_path, source_seed)
    if not source_path.exists():
        return None
    return load_json(source_path)


def validate_string_list(value: Any, field_name: str, prefix: str, errors: list[str]) -> None:
    require(isinstance(value, list), f"{prefix} {field_name} must be a list", errors)
    if not isinstance(value, list):
        return
    for idx, item in enumerate(value):
        require(isinstance(item, str) and item, f"{prefix} {field_name}[{idx}] must be a non-empty string", errors)


def validate_relation_id_list(value: Any, field_name: str, prefix: str, errors: list[str]) -> None:
    validate_string_list(value, field_name, prefix, errors)
    if not isinstance(value, list):
        return
    for idx, item in enumerate(value):
        require(valid_id(item), f"{prefix} {field_name}[{idx}] invalid id: {item!r}", errors)


def validate_anchor(anchor: Any, prefix: str, errors: list[str]) -> tuple[str | None, str | None, str | None]:
    require(isinstance(anchor, dict), f"{prefix} must be an object", errors)
    if not isinstance(anchor, dict):
        return None, None, None

    source = anchor.get("source")
    rel_type = anchor.get("type")
    target = anchor.get("target")
    require(valid_id(source), f"{prefix} invalid source id: {source!r}", errors)
    require(isinstance(rel_type, str) and rel_type, f"{prefix} missing type", errors)
    require(valid_id(target), f"{prefix} invalid target id: {target!r}", errors)
    return source, rel_type, target


def validate_evaluation(
    data: dict[str, Any],
    source_graph: dict[str, Any] | None = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    required_top_level = (
        "schema_version",
        "evaluation_id",
        "title",
        "status",
        "source_seed",
        "source_inventory",
        "source_audit",
        "purpose",
        "scoring_notes",
        "cases",
    )
    for key in required_top_level:
        require(key in data, f"missing top-level key: {key}", errors)
    if errors:
        return errors, warnings, {}

    require(valid_id(data["evaluation_id"]), f"invalid evaluation_id: {data['evaluation_id']!r}", errors)
    require(data.get("status") in STATUSES, f"invalid status: {data.get('status')!r}", errors)
    for key in ("schema_version", "title", "source_seed", "source_inventory", "source_audit", "purpose"):
        require(isinstance(data.get(key), str) and data.get(key), f"{key} must be a non-empty string", errors)
    validate_string_list(data.get("scoring_notes"), "scoring_notes", "evaluation", errors)

    cases = data.get("cases")
    require(isinstance(cases, list) and cases, "cases must be a non-empty list", errors)
    if not isinstance(cases, list):
        return errors, warnings, {}

    graph_node_ids: set[str] = set()
    graph_edges: set[tuple[str, str, str]] = set()
    if source_graph:
        graph_node_ids = {node.get("id") for node in source_graph.get("nodes", []) if isinstance(node, dict)}
        graph_edges = {
            (relation.get("source"), relation.get("type"), relation.get("target"))
            for relation in source_graph.get("relations", [])
            if isinstance(relation, dict)
        }

    case_ids: list[str] = []
    case_type_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    anchor_count = 0
    gap_indicator_count = 0
    expected_family_count = 0

    for idx, case in enumerate(cases):
        prefix = f"case[{idx}]"
        require(isinstance(case, dict), f"{prefix} must be an object", errors)
        if not isinstance(case, dict):
            continue

        required_case_fields = (
            "id",
            "source_ids",
            "split",
            "case_type",
            "prompt",
            "expected_answer",
            "expected_relation_families",
            "graph_anchors",
            "transfer_focus",
        )
        for key in required_case_fields:
            require(key in case, f"{prefix} missing key: {key}", errors)

        case_id = case.get("id")
        case_ids.append(case_id)
        case_prefix = f"case {case_id or idx}"
        require(valid_id(case_id), f"{prefix} invalid id: {case_id!r}", errors)
        require(case.get("split") in SPLITS, f"{case_prefix} invalid split: {case.get('split')!r}", errors)
        require(case.get("case_type") in CASE_TYPES, f"{case_prefix} invalid case_type: {case.get('case_type')!r}", errors)

        validate_string_list(case.get("source_ids"), "source_ids", case_prefix, errors)
        for key in ("prompt", "expected_answer", "transfer_focus"):
            require(isinstance(case.get(key), str) and case.get(key), f"{case_prefix} {key} must be a non-empty string", errors)

        validate_relation_id_list(case.get("expected_relation_families"), "expected_relation_families", case_prefix, errors)
        expected_relation_families = case.get("expected_relation_families", [])
        if isinstance(expected_relation_families, list):
            expected_family_count += len(expected_relation_families)
            if source_graph:
                for relation_id in expected_relation_families:
                    if valid_id(relation_id) and relation_id not in graph_node_ids:
                        errors.append(f"{case_prefix} expected relation family missing from source graph: {relation_id}")

        graph_anchors = case.get("graph_anchors")
        require(isinstance(graph_anchors, list) and graph_anchors, f"{case_prefix} graph_anchors must be a non-empty list", errors)
        if isinstance(graph_anchors, list):
            anchor_count += len(graph_anchors)
            for anchor_idx, anchor in enumerate(graph_anchors):
                source, rel_type, target = validate_anchor(anchor, f"{case_prefix}.graph_anchors[{anchor_idx}]", errors)
                if source_graph and source and target and rel_type:
                    if source not in graph_node_ids:
                        errors.append(f"{case_prefix}.graph_anchors[{anchor_idx}] source missing from graph: {source}")
                    if target not in graph_node_ids:
                        errors.append(f"{case_prefix}.graph_anchors[{anchor_idx}] target missing from graph: {target}")
                    if source in graph_node_ids and target in graph_node_ids and (source, rel_type, target) not in graph_edges:
                        errors.append(
                            f"{case_prefix}.graph_anchors[{anchor_idx}] edge missing from graph: "
                            f"{source} --{rel_type}--> {target}"
                        )

        gap_indicators = case.get("gap_indicators", [])
        if "gap_indicators" in case:
            validate_relation_id_list(gap_indicators, "gap_indicators", case_prefix, errors)
        if isinstance(gap_indicators, list):
            gap_indicator_count += len(gap_indicators)
            if source_graph:
                present_gap_indicators = sorted(
                    gap_id for gap_id in gap_indicators if valid_id(gap_id) and gap_id in graph_node_ids
                )
                if present_gap_indicators:
                    warnings.append(
                        f"{case_prefix} gap indicators already exist in source graph: "
                        f"{', '.join(present_gap_indicators)}"
                    )

        if case.get("case_type") == "gap_probe" and not gap_indicators:
            warnings.append(f"{case_prefix} is gap_probe but has no gap_indicators")

        case_type_counts[case.get("case_type")] += 1
        split_counts[case.get("split")] += 1

    for case_id, count in Counter(case_ids).items():
        require(count == 1, f"duplicate case id: {case_id}", errors)

    stats = {
        "evaluation_id": data["evaluation_id"],
        "cases": len(cases),
        "case_type_counts": dict(sorted(case_type_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "graph_anchors": anchor_count,
        "expected_relation_families": expected_family_count,
        "gap_indicators": gap_indicator_count,
        "source_graph_loaded": bool(source_graph),
        "source_graph_id": source_graph.get("graph_id") if source_graph else None,
    }
    return errors, warnings, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evaluation_json", type=Path, help="Path to held-out evaluation JSON file")
    parser.add_argument("--source-graph", type=Path, help="Override source graph JSON path")
    parser.add_argument("--stats", action="store_true", help="Print validation statistics")
    args = parser.parse_args()

    data = load_json(args.evaluation_json)
    source_graph = load_source_graph(args.evaluation_json, data, args.source_graph)
    if source_graph is None:
        print("WARNING: source graph not loaded; graph anchor existence checks skipped", file=sys.stderr)

    errors, warnings, stats = validate_evaluation(data, source_graph)

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.evaluation_json}")
    if args.stats:
        print(json.dumps(stats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
