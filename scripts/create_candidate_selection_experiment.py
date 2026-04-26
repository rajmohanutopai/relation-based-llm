#!/usr/bin/env python3
"""Create a closed-vocabulary candidate-selection experiment.

physical_v0_1 failed because the model could fit structured local examples
while inventing plausible graph IDs during held-out generation. This script
creates physical_v0_2-style records where the valid graph vocabulary is shown in
the prompt and the model must select the correct node IDs, relation families, or
graph anchors from candidates.
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


Example = dict[str, Any]
Record = dict[str, Any]
Relation = dict[str, str]

SPLITS = ("train", "dev", "curriculum_test")
VARIANT = "candidate_selection"
ID_RE = re.compile(r"([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)")


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
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def compact_relation(value: dict[str, Any]) -> Relation | None:
    source = value.get("source")
    rel_type = value.get("type")
    target = value.get("target")
    if not all(isinstance(item, str) and item for item in (source, rel_type, target)):
        return None
    return {"source": source, "type": rel_type, "target": target}


def relation_key(relation: Relation) -> tuple[str, str, str]:
    return relation["source"], relation["type"], relation["target"]


def relation_text(relation: Relation) -> str:
    return f"{relation['source']} --{relation['type']}--> {relation['target']}"


def node_map(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {node["id"]: node for node in graph.get("nodes", []) if isinstance(node, dict) and "id" in node}


def graph_relations(graph: dict[str, Any]) -> list[Relation]:
    relations: list[Relation] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in graph.get("relations", []):
        relation = compact_relation(raw)
        if relation is None:
            continue
        key = relation_key(relation)
        if key in seen:
            continue
        seen.add(key)
        relations.append(relation)
    return sorted(relations, key=relation_key)


def id_prefix(identifier: str) -> str:
    return identifier.split(".", 1)[0]


def node_label(nodes: dict[str, dict[str, Any]], identifier: str) -> str:
    return nodes.get(identifier, {}).get("label") or identifier.split(".")[-1].replace("_", " ")


def node_layer(nodes: dict[str, dict[str, Any]], identifier: str) -> str:
    value = nodes.get(identifier, {}).get("layer")
    return value if isinstance(value, str) else ""


def node_kind(nodes: dict[str, dict[str, Any]], identifier: str) -> str:
    value = nodes.get(identifier, {}).get("kind")
    return value if isinstance(value, str) else ""


def non_object_relation_family_ids(relations: list[Relation]) -> list[str]:
    family_ids: list[str] = []
    for relation in relations:
        for node_id in (relation["source"], relation["target"]):
            if node_id.startswith("object."):
                continue
            if node_id not in family_ids:
                family_ids.append(node_id)
    return family_ids


def stable_sample(items: list[str], count: int, rng: random.Random) -> list[str]:
    if count <= 0:
        return []
    items = list(dict.fromkeys(items))
    rng.shuffle(items)
    return sorted(items[:count])


def ordered_unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if isinstance(item, str) and item))


def relation_unique(relations: list[Relation]) -> list[Relation]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[Relation] = []
    for relation in relations:
        key = relation_key(relation)
        if key in seen:
            continue
        seen.add(key)
        unique.append(relation)
    return unique


def choice_seed(seed: int, *parts: str) -> random.Random:
    digest = hashlib.sha256("|".join((str(seed), *parts)).encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def node_candidates(
    correct_ids: list[str],
    all_node_ids: list[str],
    nodes: dict[str, dict[str, Any]],
    count: int,
    rng: random.Random,
) -> list[str]:
    correct = ordered_unique(correct_ids)
    if not correct:
        return []

    layers = {node_layer(nodes, node_id) for node_id in correct}
    kinds = {node_kind(nodes, node_id) for node_id in correct}
    prefixes = {id_prefix(node_id) for node_id in correct}
    negatives = [node_id for node_id in all_node_ids if node_id not in correct]

    def score(node_id: str) -> tuple[int, str]:
        value = 0
        if node_layer(nodes, node_id) in layers:
            value -= 4
        if node_kind(nodes, node_id) in kinds:
            value -= 3
        if id_prefix(node_id) in prefixes:
            value -= 2
        return value, node_id

    hard_negatives = sorted(negatives, key=score)
    needed = max(count, len(correct) + 2) - len(correct)
    candidates = correct + stable_sample(hard_negatives[: max(needed * 4, needed)], needed, rng)
    return sorted(ordered_unique(candidates))


def relation_family_candidates(
    correct_ids: list[str],
    all_family_ids: list[str],
    nodes: dict[str, dict[str, Any]],
    count: int,
    rng: random.Random,
) -> list[str]:
    correct = ordered_unique(correct_ids)
    if not correct:
        return []

    layers = {node_layer(nodes, node_id) for node_id in correct}
    kinds = {node_kind(nodes, node_id) for node_id in correct}
    prefixes = {id_prefix(node_id) for node_id in correct}
    negatives = [node_id for node_id in all_family_ids if node_id not in correct]

    def score(node_id: str) -> tuple[int, str]:
        value = 0
        if node_layer(nodes, node_id) in layers:
            value -= 4
        if node_kind(nodes, node_id) in kinds:
            value -= 3
        if id_prefix(node_id) in prefixes:
            value -= 2
        return value, node_id

    hard_negatives = sorted(negatives, key=score)
    needed = max(count, len(correct) + 2) - len(correct)
    candidates = correct + stable_sample(hard_negatives[: max(needed * 5, needed)], needed, rng)
    return sorted(ordered_unique(candidates))


def relation_candidates(
    correct_relations: list[Relation],
    all_relations: list[Relation],
    nodes: dict[str, dict[str, Any]],
    count: int,
    rng: random.Random,
) -> list[Relation]:
    correct = relation_unique(correct_relations)
    if not correct:
        return []

    correct_keys = {relation_key(relation) for relation in correct}
    types = {relation["type"] for relation in correct}
    source_layers = {node_layer(nodes, relation["source"]) for relation in correct}
    target_layers = {node_layer(nodes, relation["target"]) for relation in correct}
    family_ids = set(non_object_relation_family_ids(correct))
    negatives = [relation for relation in all_relations if relation_key(relation) not in correct_keys]

    def score(relation: Relation) -> tuple[int, str, str, str]:
        value = 0
        if relation["type"] in types:
            value -= 4
        if node_layer(nodes, relation["source"]) in source_layers:
            value -= 2
        if node_layer(nodes, relation["target"]) in target_layers:
            value -= 2
        if relation["source"] in family_ids or relation["target"] in family_ids:
            value -= 3
        return value, relation["source"], relation["type"], relation["target"]

    hard_negatives = sorted(negatives, key=score)
    needed = max(count, len(correct) + 2) - len(correct)
    sampled = stable_sample([relation_text(relation) for relation in hard_negatives[: max(needed * 5, needed)]], needed, rng)
    by_text = {relation_text(relation): relation for relation in hard_negatives}
    candidates = correct + [by_text[text] for text in sampled]
    return sorted(relation_unique(candidates), key=relation_key)


def format_node_candidates(candidate_ids: list[str], nodes: dict[str, dict[str, Any]]) -> str:
    return "\n".join(f"- {node_id} | {node_label(nodes, node_id)}" for node_id in candidate_ids)


def format_relation_family_candidates(candidate_ids: list[str], nodes: dict[str, dict[str, Any]]) -> str:
    return "\n".join(f"- {node_id} | {node_label(nodes, node_id)}" for node_id in candidate_ids)


def format_anchor_candidates(candidates: list[Relation]) -> str:
    return "\n".join(f"- {relation_text(relation)}" for relation in candidates)


def node_options(candidate_ids: list[str], nodes: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"option": f"N{idx:02d}", "node_id": node_id, "label": node_label(nodes, node_id)}
        for idx, node_id in enumerate(candidate_ids, start=1)
    ]


def relation_family_options(candidate_ids: list[str], nodes: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"option": f"F{idx:02d}", "relation_family_id": node_id, "label": node_label(nodes, node_id)}
        for idx, node_id in enumerate(candidate_ids, start=1)
    ]


def anchor_options(candidates: list[Relation]) -> list[dict[str, Any]]:
    return [
        {"option": f"A{idx:02d}", "graph_anchor": relation, "text": relation_text(relation)}
        for idx, relation in enumerate(candidates, start=1)
    ]


def gap_options(candidate_ids: list[str]) -> list[dict[str, str]]:
    return [
        {"option": f"G{idx:02d}", "gap_id": gap_id}
        for idx, gap_id in enumerate(candidate_ids, start=1)
    ]


def format_node_options(options: list[dict[str, str]]) -> str:
    return "\n".join(f"- {option['option']}: {option['node_id']} | {option['label']}" for option in options)


def format_relation_family_options(options: list[dict[str, str]]) -> str:
    return "\n".join(
        f"- {option['option']}: {option['relation_family_id']} | {option['label']}"
        for option in options
    )


def format_anchor_options(options: list[dict[str, Any]]) -> str:
    return "\n".join(f"- {option['option']}: {option['text']}" for option in options)


def format_gap_options(options: list[dict[str, str]]) -> str:
    return "\n".join(f"- {option['option']}: {option['gap_id']}" for option in options)


def selected_node_options(options: list[dict[str, str]], node_ids: list[str]) -> list[str]:
    expected = set(node_ids)
    return [option["option"] for option in options if option["node_id"] in expected]


def selected_family_options(options: list[dict[str, str]], family_ids: list[str]) -> list[str]:
    expected = set(family_ids)
    return [option["option"] for option in options if option["relation_family_id"] in expected]


def selected_anchor_options(options: list[dict[str, Any]], anchors: list[Relation]) -> list[str]:
    expected = {relation_key(anchor) for anchor in anchors}
    return [option["option"] for option in options if relation_key(option["graph_anchor"]) in expected]


def selected_gap_options(options: list[dict[str, str]], gap_ids: list[str]) -> list[str]:
    expected = set(gap_ids)
    return [option["option"] for option in options if option["gap_id"] in expected]


def selection_target(
    node_ids: list[str] | None = None,
    family_ids: list[str] | None = None,
    anchors: list[Relation] | None = None,
    gap_ids: list[str] | None = None,
) -> str:
    sections: list[str] = []
    if node_ids is not None:
        sections.append("SELECTED_NODE_IDS:")
        sections.extend(ordered_unique(node_ids) or ["NONE"])
    if family_ids is not None:
        sections.append("SELECTED_RELATION_FAMILY_IDS:")
        sections.extend(ordered_unique(family_ids) or ["NONE"])
    if anchors is not None:
        sections.append("SELECTED_GRAPH_ANCHORS:")
        unique_anchors = relation_unique(anchors)
        sections.extend([relation_text(relation) for relation in unique_anchors] or ["NONE"])
    if gap_ids is not None:
        sections.append("SELECTED_GAP_IDS:")
        sections.extend(ordered_unique(gap_ids) or ["NONE"])
    return "\n".join(sections)


def option_selection_target(
    node_option_ids: list[str] | None = None,
    family_option_ids: list[str] | None = None,
    anchor_option_ids: list[str] | None = None,
    gap_option_ids: list[str] | None = None,
) -> str:
    sections: list[str] = []
    if node_option_ids is not None:
        sections.append("SELECTED_NODE_OPTIONS:")
        sections.extend(node_option_ids or ["NONE"])
    if family_option_ids is not None:
        sections.append("SELECTED_RELATION_OPTIONS:")
        sections.extend(family_option_ids or ["NONE"])
    if anchor_option_ids is not None:
        sections.append("SELECTED_ANCHOR_OPTIONS:")
        sections.extend(anchor_option_ids or ["NONE"])
    if gap_option_ids is not None:
        sections.append("SELECTED_GAP_OPTIONS:")
        sections.extend(gap_option_ids or ["NONE"])
    return "\n".join(sections)


def strip_answer_marker(text: str) -> str:
    replacements = (
        "NODE_ID:",
        "RELATION_FAMILY_IDS:",
        "GRAPH_ANCHORS:",
        "ANSWER_WITH_RELATIONS:",
        "RELATIONS_OBSERVED:",
        "TARGET:",
    )
    result = text
    for marker in replacements:
        result = result.replace(marker, "")
    return result.strip()


def make_record(
    experiment_id: str,
    split_name: str,
    source_example: Example,
    selector_type: str,
    input_text: str,
    target_text: str,
    metadata: dict[str, Any],
) -> Record:
    source_id = source_example["id"]
    record_id = f"dataset.{experiment_id}.{VARIANT}.{source_id}.{selector_type}"
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
            **metadata,
        },
    }


def target_node_ids(example: Example) -> list[str]:
    target = example.get("target", {})
    if not isinstance(target, dict):
        return []
    node_ids: list[str] = []
    if isinstance(target.get("node_id"), str):
        node_ids.append(target["node_id"])
    if example.get("task_type") == "relation_completion" and isinstance(target.get("target"), str):
        node_ids.append(target["target"])
    return ordered_unique(node_ids)


def target_anchors(example: Example) -> list[Relation]:
    target = example.get("target", {})
    if not isinstance(target, dict):
        return []

    anchors: list[Relation] = []
    for key in ("graph_anchors", "expected_relations", "relations_observed"):
        raw_relations = target.get(key)
        if isinstance(raw_relations, list):
            for raw in raw_relations:
                if isinstance(raw, dict):
                    relation = compact_relation(raw)
                    if relation is not None:
                        anchors.append(relation)

    relation = compact_relation(target)
    if relation is not None:
        anchors.append(relation)

    contrast = target.get("contrast_relation")
    if isinstance(contrast, dict):
        relation = compact_relation(contrast)
        if relation is not None:
            anchors.append(relation)

    if {"object_a", "property_a"} <= set(target):
        anchors.append({"source": target["object_a"], "type": "has_property", "target": target["property_a"]})
    if {"object_b", "property_b"} <= set(target):
        anchors.append({"source": target["object_b"], "type": "has_property", "target": target["property_b"]})

    return relation_unique(anchors)


def target_relation_family_ids(example: Example, anchors: list[Relation]) -> list[str]:
    target = example.get("target", {})
    if isinstance(target, dict) and isinstance(target.get("relation_family_ids"), list):
        return ordered_unique([item for item in target["relation_family_ids"] if isinstance(item, str)])
    return non_object_relation_family_ids(anchors)


def build_selection_records(
    experiment_id: str,
    split_name: str,
    examples: list[Example],
    graph: dict[str, Any],
    candidate_count: int,
    seed: int,
) -> list[Record]:
    nodes = node_map(graph)
    all_node_ids = sorted(nodes)
    all_family_ids = sorted(node_id for node_id in nodes if not node_id.startswith("object."))
    all_relations = graph_relations(graph)

    records: list[Record] = []
    for example in examples:
        source_prompt = strip_answer_marker(example.get("input", ""))
        anchors = target_anchors(example)
        family_ids = target_relation_family_ids(example, anchors)
        node_ids = target_node_ids(example)
        base_metadata = {
            "source_input": example.get("input"),
            "source_text_target": example.get("text_target"),
        }

        if node_ids:
            rng = choice_seed(seed, example["id"], "node")
            candidates = node_candidates(node_ids, all_node_ids, nodes, candidate_count, rng)
            options = node_options(candidates, nodes)
            input_text = (
                "Closed-vocabulary selection. Select only option keys from CANDIDATE_NODE_IDS.\n"
                f"SOURCE_TASK: {example.get('task_type')}\n"
                f"PROMPT:\n{source_prompt}\n\n"
                "CANDIDATE_NODE_IDS:\n"
                f"{format_node_options(options)}\n\n"
                "Return selected option keys under SELECTED_NODE_OPTIONS.\n"
                "OUTPUT:"
            )
            selected_options = selected_node_options(options, node_ids)
            records.append(
                make_record(
                    experiment_id,
                    split_name,
                    example,
                    "node_candidate_selection",
                    input_text,
                    option_selection_target(node_option_ids=selected_options),
                    {
                        **base_metadata,
                        "candidate_node_ids": candidates,
                        "candidate_node_options": options,
                        "expected_node_ids": node_ids,
                        "expected_node_options": selected_options,
                    },
                )
            )

        if family_ids:
            rng = choice_seed(seed, example["id"], "families")
            candidates = relation_family_candidates(family_ids, all_family_ids, nodes, candidate_count, rng)
            options = relation_family_options(candidates, nodes)
            input_text = (
                "Closed-vocabulary selection. Select only option keys from CANDIDATE_RELATION_FAMILY_IDS.\n"
                f"SOURCE_TASK: {example.get('task_type')}\n"
                f"PROMPT:\n{source_prompt}\n\n"
                "CANDIDATE_RELATION_FAMILY_IDS:\n"
                f"{format_relation_family_options(options)}\n\n"
                "Return selected option keys under SELECTED_RELATION_OPTIONS.\n"
                "OUTPUT:"
            )
            selected_options = selected_family_options(options, family_ids)
            records.append(
                make_record(
                    experiment_id,
                    split_name,
                    example,
                    "relation_family_candidate_selection",
                    input_text,
                    option_selection_target(family_option_ids=selected_options),
                    {
                        **base_metadata,
                        "candidate_relation_family_ids": candidates,
                        "candidate_relation_family_options": options,
                        "expected_relation_family_ids": family_ids,
                        "expected_relation_options": selected_options,
                    },
                )
            )

        if anchors:
            rng = choice_seed(seed, example["id"], "anchors")
            candidates = relation_candidates(anchors, all_relations, nodes, candidate_count, rng)
            options = anchor_options(candidates)
            input_text = (
                "Closed-vocabulary selection. Select only option keys from CANDIDATE_GRAPH_ANCHORS.\n"
                f"SOURCE_TASK: {example.get('task_type')}\n"
                f"PROMPT:\n{source_prompt}\n\n"
                "CANDIDATE_GRAPH_ANCHORS:\n"
                f"{format_anchor_options(options)}\n\n"
                "Return selected option keys under SELECTED_ANCHOR_OPTIONS.\n"
                "OUTPUT:"
            )
            selected_options = selected_anchor_options(options, anchors)
            records.append(
                make_record(
                    experiment_id,
                    split_name,
                    example,
                    "graph_anchor_candidate_selection",
                    input_text,
                    option_selection_target(anchor_option_ids=selected_options),
                    {
                        **base_metadata,
                        "candidate_graph_anchors": candidates,
                        "candidate_graph_anchor_options": options,
                        "expected_graph_anchors": anchors,
                        "expected_anchor_options": selected_options,
                    },
                )
            )

        if family_ids and anchors:
            rng_families = choice_seed(seed, example["id"], "combined_families")
            rng_anchors = choice_seed(seed, example["id"], "combined_anchors")
            family_candidates = relation_family_candidates(family_ids, all_family_ids, nodes, candidate_count, rng_families)
            anchor_candidates = relation_candidates(anchors, all_relations, nodes, candidate_count, rng_anchors)
            family_options = relation_family_options(family_candidates, nodes)
            graph_anchor_options = anchor_options(anchor_candidates)
            input_text = (
                "Closed-vocabulary selection. Select only option keys from the candidate lists.\n"
                f"SOURCE_TASK: {example.get('task_type')}\n"
                f"PROMPT:\n{source_prompt}\n\n"
                "CANDIDATE_RELATION_FAMILY_IDS:\n"
                f"{format_relation_family_options(family_options)}\n\n"
                "CANDIDATE_GRAPH_ANCHORS:\n"
                f"{format_anchor_options(graph_anchor_options)}\n\n"
                "Return selected option keys under SELECTED_RELATION_OPTIONS and SELECTED_ANCHOR_OPTIONS.\n"
                "OUTPUT:"
            )
            selected_family_option_ids = selected_family_options(family_options, family_ids)
            selected_anchor_option_ids = selected_anchor_options(graph_anchor_options, anchors)
            records.append(
                make_record(
                    experiment_id,
                    split_name,
                    example,
                    "relation_and_anchor_candidate_selection",
                    input_text,
                    option_selection_target(
                        family_option_ids=selected_family_option_ids,
                        anchor_option_ids=selected_anchor_option_ids,
                    ),
                    {
                        **base_metadata,
                        "candidate_relation_family_ids": family_candidates,
                        "candidate_relation_family_options": family_options,
                        "candidate_graph_anchors": anchor_candidates,
                        "candidate_graph_anchor_options": graph_anchor_options,
                        "expected_relation_family_ids": family_ids,
                        "expected_graph_anchors": anchors,
                        "expected_relation_options": selected_family_option_ids,
                        "expected_anchor_options": selected_anchor_option_ids,
                    },
                )
            )

    return records


def heldout_candidate_rows(
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
        family_ids = ordered_unique(case.get("expected_relation_families", []))
        anchors = relation_unique([relation for raw in case.get("graph_anchors", []) if (relation := compact_relation(raw))])
        gap_ids = ordered_unique(case.get("gap_indicators", []))

        family_candidates = relation_family_candidates(
            family_ids,
            all_family_ids,
            nodes,
            max(candidate_count, len(family_ids) + 4),
            choice_seed(seed, case_id, "heldout_families"),
        )
        anchor_candidates = relation_candidates(
            anchors,
            all_relations,
            nodes,
            max(candidate_count, len(anchors) + 4),
            choice_seed(seed, case_id, "heldout_anchors"),
        )
        gap_candidates = []
        if gap_ids:
            rng = choice_seed(seed, case_id, "heldout_gaps")
            negatives = [gap_id for gap_id in all_gap_ids if gap_id not in gap_ids]
            gap_candidates = sorted(ordered_unique(gap_ids + stable_sample(negatives, max(2, min(4, len(negatives))), rng)))

        family_options = relation_family_options(family_candidates, nodes)
        graph_anchor_options = anchor_options(anchor_candidates)
        gap_option_rows = gap_options(gap_candidates)
        selected_family_option_ids = selected_family_options(family_options, family_ids)
        selected_anchor_option_ids = selected_anchor_options(graph_anchor_options, anchors)
        selected_gap_option_ids = selected_gap_options(gap_option_rows, gap_ids)

        gap_block = ""
        if gap_option_rows:
            gap_block = f"CANDIDATE_GAP_IDS:\n{format_gap_options(gap_option_rows)}\n\n"

        input_text = (
            "Closed-vocabulary selection. Select only option keys from the candidate lists.\n"
            f"QUESTION: {case.get('prompt', '')}\n\n"
            "CANDIDATE_RELATION_FAMILY_IDS:\n"
            f"{format_relation_family_options(family_options)}\n\n"
            "CANDIDATE_GRAPH_ANCHORS:\n"
            f"{format_anchor_options(graph_anchor_options)}\n\n"
            f"{gap_block}"
            "Return selected option keys under SELECTED_RELATION_OPTIONS, SELECTED_ANCHOR_OPTIONS, and SELECTED_GAP_OPTIONS when gap options are present.\n"
            "OUTPUT:"
        ).strip()

        rows.append(
            {
                "case_id": case_id,
                "case_type": case.get("case_type"),
                "input": input_text,
                "prompt": input_text,
                "candidate_relation_family_ids": family_candidates,
                "candidate_relation_family_options": family_options,
                "candidate_graph_anchors": anchor_candidates,
                "candidate_graph_anchor_options": graph_anchor_options,
                "candidate_gap_indicators": gap_candidates,
                "candidate_gap_options": gap_option_rows,
                "expected_relation_family_ids": family_ids,
                "expected_graph_anchors": anchors,
                "expected_gap_indicators": gap_ids,
                "expected_relation_options": selected_family_option_ids,
                "expected_anchor_options": selected_anchor_option_ids,
                "expected_gap_options": selected_gap_option_ids,
            }
        )
    return rows


def counts_by_task(rows: list[Record]) -> dict[str, int]:
    return dict(sorted(Counter(row["task_type"] for row in rows).items()))


def output_file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {name: {"path": str(path), "sha256": sha256_file(path)} for name, path in sorted(paths.items())}


def write_training_config(experiment_id: str, output_dir: Path) -> Path:
    path = output_dir / "training_config.json"
    config = {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "baseline_model": {
            "name": "HuggingFaceTB/SmolLM2-135M",
            "role": "tiny causal-transformer closed-vocabulary candidate-selection baseline",
            "reason": "Keep the same model as physical_v0 and physical_v0_1 so the comparison isolates candidate selection.",
        },
        "dataset_manifest": str(output_dir / "datasets" / "manifest.json"),
        "output_root": f"runs/{experiment_id}/smollm2_135m",
        "format": {
            "prompt_template": "### Input:\n{input}\n\n### Response:\n",
            "target_template": "{target}",
        },
        "training": {
            "max_seq_length": 512,
            "num_train_epochs": 10,
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
                f"--output runs/{experiment_id}/smollm2_135m/{VARIANT}/heldout_outputs_candidate_selection.jsonl "
                f"--variant {VARIANT} --prompt-style raw"
            ),
            "score_candidate_selection": (
                "python3 scripts/run_candidate_selection_evaluation.py "
                f"{output_dir / 'heldout.json'} "
                f"{output_dir / 'heldout_prompts.jsonl'} "
                f"runs/{experiment_id}/smollm2_135m/{VARIANT}/heldout_outputs_candidate_selection.jsonl "
                f"--output runs/{experiment_id}/smollm2_135m/{VARIANT}/heldout_candidate_scores.json"
            ),
        },
        "notes": [
            "This experiment tests recognition among candidate graph IDs, not open-ended graph ID generation.",
            "Candidate lists include the correct labels plus deterministic hard negatives from nearby graph layers or relation types.",
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
    parser.add_argument("--experiment-id", default="physical_v0_2")
    parser.add_argument("--output-dir", type=Path, help="Defaults to data/developmental_graph/experiments/<experiment-id>")
    parser.add_argument("--candidate-count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.candidate_count < 4:
        raise ValueError("--candidate-count must be at least 4")

    output_dir = args.output_dir or Path("data/developmental_graph/experiments") / args.experiment_id
    ensure_output_dir(output_dir, args.overwrite)

    graph = load_json(args.source_graph)
    heldout = load_json(args.heldout)
    source_manifest = load_json(args.source_experiment / "manifest.json")

    split_records: dict[str, list[Record]] = {}
    output_paths: dict[str, Path] = {}
    dataset_output_dir = output_dir / "datasets"
    variant_dir = dataset_output_dir / VARIANT

    for split_name in SPLITS:
        source_examples = load_jsonl(args.source_experiment / f"{split_name}.jsonl")
        records = build_selection_records(
            args.experiment_id,
            split_name,
            source_examples,
            graph,
            args.candidate_count,
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

    heldout_prompts = heldout_candidate_rows(heldout, graph, args.candidate_count, args.seed)
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
            "This dataset is already model-ready; input/target strings are closed-vocabulary selection prompts.",
            "The valid graph vocabulary is supplied inside each prompt as candidate IDs or graph anchors.",
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
        "variant": VARIANT,
        "split_strategy": "derived_from_physical_v0_1_splits",
        "splits": {
            split_name: {
                "total": len(rows),
                "task_type_counts": counts_by_task(rows),
            }
            for split_name, rows in split_records.items()
        },
        "heldout_prompt_count": len(heldout_prompts),
        "outputs": output_file_manifest(output_paths),
        "notes": [
            "physical_v0_2 changes the task from free-form graph ID generation to closed-vocabulary candidate selection.",
            "Hard negatives come from same or nearby graph layers, node kinds, relation types, or related family IDs.",
            "No broad domain expansion is included.",
        ],
    }
    write_json(manifest_path, manifest)

    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
