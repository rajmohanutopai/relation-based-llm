#!/usr/bin/env python3
"""Validate a developmental relation graph JSON file.

This intentionally avoids third-party dependencies so the graph can be checked
in a bare Python environment. It validates the project-specific invariants that
matter most for code consumption:

- required top-level sections
- ID syntax
- duplicate layer/node IDs
- node -> layer references
- relation endpoints
- micro-experience participants and observed relation endpoints
- evaluation relation endpoints and whether the expected edge exists
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$")
AGE_STATUSES = {"active", "emerging", "latent", "future"}
VALENCES = {"negative", "neutral", "positive", "mixed", "unknown"}


class ValidationError(Exception):
    """Raised when validation fails."""


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(ID_RE.match(value))


def validate_strength(value: Any) -> bool:
    return isinstance(value, int | float) and 0.0 <= float(value) <= 1.0


def validate_graph(data: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    for key in ("schema_version", "graph_id", "metadata", "layers", "nodes", "relations"):
        require(key in data, f"missing top-level key: {key}", errors)
    if errors:
        return errors, warnings, {}

    require(valid_id(data["graph_id"]), f"invalid graph_id: {data['graph_id']!r}", errors)

    layers = data.get("layers", [])
    nodes = data.get("nodes", [])
    relations = data.get("relations", [])
    micro_experiences = data.get("micro_experiences", [])
    evaluation_questions = data.get("evaluation_questions", [])

    require(isinstance(layers, list) and layers, "layers must be a non-empty list", errors)
    require(isinstance(nodes, list), "nodes must be a list", errors)
    require(isinstance(relations, list), "relations must be a list", errors)

    layer_ids = [layer.get("id") for layer in layers if isinstance(layer, dict)]
    node_ids = [node.get("id") for node in nodes if isinstance(node, dict)]

    for layer_id in layer_ids:
        require(valid_id(layer_id), f"invalid layer id: {layer_id!r}", errors)
    for node_id in node_ids:
        require(valid_id(node_id), f"invalid node id: {node_id!r}", errors)

    for id_value, count in Counter(layer_ids).items():
        require(count == 1, f"duplicate layer id: {id_value}", errors)
    for id_value, count in Counter(node_ids).items():
        require(count == 1, f"duplicate node id: {id_value}", errors)

    layer_set = set(layer_ids)
    node_set = set(node_ids)
    all_id_set = layer_set | node_set

    for node in nodes:
        node_id = node.get("id", "<missing>")
        require(node.get("layer") in layer_set, f"node {node_id} references missing layer {node.get('layer')}", errors)
        require(node.get("age_status") in AGE_STATUSES, f"node {node_id} has invalid age_status {node.get('age_status')!r}", errors)
        require(isinstance(node.get("label"), str) and node.get("label"), f"node {node_id} missing label", errors)
        require(isinstance(node.get("kind"), str) and node.get("kind"), f"node {node_id} missing kind", errors)

    edge_keys: set[tuple[str, str, str]] = set()
    relation_type_counts: Counter[str] = Counter()
    incoming: defaultdict[str, int] = defaultdict(int)
    outgoing: defaultdict[str, int] = defaultdict(int)
    referenced: defaultdict[str, int] = defaultdict(int)

    for idx, relation in enumerate(relations):
        prefix = f"relation[{idx}]"
        source = relation.get("source")
        target = relation.get("target")
        rel_type = relation.get("type")

        require(source in node_set, f"{prefix} source missing node: {source}", errors)
        require(target in node_set, f"{prefix} target missing node: {target}", errors)
        require(isinstance(rel_type, str) and rel_type, f"{prefix} missing type", errors)
        require(validate_strength(relation.get("strength")), f"{prefix} invalid strength {relation.get('strength')!r}", errors)

        if "valence" in relation:
            require(relation["valence"] in VALENCES, f"{prefix} invalid valence {relation['valence']!r}", errors)
        if "age_status" in relation:
            require(relation["age_status"] in AGE_STATUSES, f"{prefix} invalid age_status {relation['age_status']!r}", errors)

        for built_from in relation.get("built_from", []):
            require(built_from in all_id_set, f"{prefix} built_from missing id: {built_from}", errors)
            if built_from in all_id_set:
                referenced[built_from] += 1

        if source and target and rel_type:
            edge_keys.add((source, rel_type, target))
            relation_type_counts[rel_type] += 1
            outgoing[source] += 1
            incoming[target] += 1
            referenced[source] += 1
            referenced[target] += 1

    for idx, experience in enumerate(micro_experiences):
        prefix = f"micro_experience[{idx}]"
        exp_id = experience.get("id")
        require(valid_id(exp_id), f"{prefix} invalid id: {exp_id!r}", errors)
        require(experience.get("age_status") in AGE_STATUSES, f"{prefix} invalid age_status {experience.get('age_status')!r}", errors)
        for participant in experience.get("participants", []):
            require(participant in node_set, f"{prefix} participant missing node: {participant}", errors)
        for observed_idx, observed in enumerate(experience.get("relations_observed", [])):
            obs_prefix = f"{prefix}.relations_observed[{observed_idx}]"
            require(observed.get("source") in node_set, f"{obs_prefix} source missing node: {observed.get('source')}", errors)
            require(observed.get("target") in node_set, f"{obs_prefix} target missing node: {observed.get('target')}", errors)

    for idx, question in enumerate(evaluation_questions):
        prefix = f"evaluation_question[{idx}]"
        q_id = question.get("id")
        require(valid_id(q_id), f"{prefix} invalid id: {q_id!r}", errors)
        for expected_idx, expected in enumerate(question.get("expected_relations", [])):
            exp_prefix = f"{prefix}.expected_relations[{expected_idx}]"
            source = expected.get("source")
            rel_type = expected.get("type")
            target = expected.get("target")
            require(source in node_set, f"{exp_prefix} source missing node: {source}", errors)
            require(target in node_set, f"{exp_prefix} target missing node: {target}", errors)
            if source in node_set and target in node_set and rel_type:
                if (source, rel_type, target) not in edge_keys:
                    warnings.append(f"{exp_prefix} expected edge is not present in graph: {source} --{rel_type}--> {target}")

    orphan_nodes = sorted(node_id for node_id in node_set if referenced[node_id] == 0)
    if orphan_nodes:
        warnings.append(f"{len(orphan_nodes)} nodes have no relations: {', '.join(orphan_nodes[:10])}")

    layer_counts = Counter(node["layer"] for node in nodes)
    stats = {
        "graph_id": data["graph_id"],
        "layers": len(layers),
        "nodes": len(nodes),
        "relations": len(relations),
        "micro_experiences": len(micro_experiences),
        "evaluation_questions": len(evaluation_questions),
        "layer_counts": dict(sorted(layer_counts.items())),
        "relation_type_counts": dict(sorted(relation_type_counts.items())),
    }
    return errors, warnings, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph_json", type=Path, help="Path to graph JSON file")
    parser.add_argument("--stats", action="store_true", help="Print validation statistics")
    args = parser.parse_args()

    with args.graph_json.open() as f:
        data = json.load(f)

    errors, warnings, stats = validate_graph(data)

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.graph_json}")
    if args.stats:
        print(json.dumps(stats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
