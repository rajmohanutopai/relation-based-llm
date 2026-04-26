#!/usr/bin/env python3
"""Generate curriculum examples from a developmental relation graph.

The generator is intentionally simple and deterministic. It converts a validated
graph into JSONL examples for the first experiment types:

- relation_completion
- state_action_effect
- counterfactual_contrast
- explanation_path

It does not call an LLM and does not invent facts outside the graph. Later
generators can add paraphrases, difficulty levels, and teacher-model expansion.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


Example = dict[str, Any]


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, examples: list[Example]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for example in examples:
            f.write(json.dumps(example, sort_keys=True))
            f.write("\n")


def node_map(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {node["id"]: node for node in graph.get("nodes", [])}


def node_label(nodes: dict[str, dict[str, Any]], node_id: str) -> str:
    node = nodes.get(node_id)
    if not node:
        return node_id
    return f"{node.get('label', node_id)} ({node_id})"


def node_summary(nodes: dict[str, dict[str, Any]], node_id: str) -> str:
    node = nodes.get(node_id)
    if not node:
        return ""
    return node.get("summary", "")


def relation_text(nodes: dict[str, dict[str, Any]], relation: dict[str, Any]) -> str:
    source = node_label(nodes, relation["source"])
    target = node_label(nodes, relation["target"])
    return f"{source} --{relation['type']}--> {target}"


def observed_relation_text(nodes: dict[str, dict[str, Any]], relation: dict[str, Any]) -> str:
    source = node_label(nodes, relation["source"])
    target = node_label(nodes, relation["target"])
    return f"{source} --{relation['type']}--> {target}"


def make_example_id(graph_id: str, task_type: str, index: int) -> str:
    safe_graph_id = graph_id.replace(".", "_")
    return f"curriculum.{safe_graph_id}.{task_type}.{index:04d}"


def relation_completion_examples(graph: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> list[Example]:
    examples: list[Example] = []
    graph_id = graph["graph_id"]

    for idx, relation in enumerate(graph.get("relations", []), start=1):
        source = node_label(nodes, relation["source"])
        target = node_label(nodes, relation["target"])
        prompt = (
            "Complete the relation.\n"
            f"SOURCE: {source}\n"
            f"RELATION_TYPE: {relation['type']}\n"
            "TARGET:"
        )
        examples.append(
            {
                "id": make_example_id(graph_id, "relation_completion", idx),
                "graph_id": graph_id,
                "task_type": "relation_completion",
                "input": prompt,
                "target": {
                    "source": relation["source"],
                    "type": relation["type"],
                    "target": relation["target"],
                    "target_label": target,
                    "strength": relation.get("strength"),
                    "valence": relation.get("valence", "unknown"),
                    "conditions": relation.get("conditions", []),
                    "built_from": relation.get("built_from", []),
                },
                "text_target": target,
                "metadata": {
                    "source_summary": node_summary(nodes, relation["source"]),
                    "target_summary": node_summary(nodes, relation["target"]),
                },
            }
        )

    return examples


def state_action_effect_examples(graph: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> list[Example]:
    examples: list[Example] = []
    graph_id = graph["graph_id"]

    for idx, experience in enumerate(graph.get("micro_experiences", []), start=1):
        event_lines = "\n".join(f"- {event}" for event in experience.get("events", []))
        prompt = (
            "Given this physical or developmental trace, identify the relation changes.\n"
            f"TITLE: {experience.get('title', experience['id'])}\n"
            "EVENTS:\n"
            f"{event_lines}\n"
            "RELATIONS_OBSERVED:"
        )
        observed = experience.get("relations_observed", [])
        examples.append(
            {
                "id": make_example_id(graph_id, "state_action_effect", idx),
                "graph_id": graph_id,
                "task_type": "state_action_effect",
                "input": prompt,
                "target": {
                    "experience_id": experience["id"],
                    "relations_observed": observed,
                    "language_overlay": experience.get("language_overlay", []),
                },
                "text_target": "\n".join(observed_relation_text(nodes, relation) for relation in observed),
                "metadata": {
                    "age_status": experience.get("age_status"),
                    "participants": experience.get("participants", []),
                },
            }
        )

    return examples


def counterfactual_contrast_examples(graph: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> list[Example]:
    examples: list[Example] = []
    graph_id = graph["graph_id"]
    relations = graph.get("relations", [])
    contrast_relations = [relation for relation in relations if relation.get("type") == "contrasts_with"]

    for idx, relation in enumerate(contrast_relations, start=1):
        source = node_label(nodes, relation["source"])
        target = node_label(nodes, relation["target"])
        prompt = (
            "Counterfactual contrast.\n"
            f"CASE_A_PROPERTY: {source}\n"
            f"CASE_B_PROPERTY: {target}\n"
            "If the situation changes from CASE_A_PROPERTY to CASE_B_PROPERTY, what relation changes?"
        )
        examples.append(
            {
                "id": make_example_id(graph_id, "counterfactual_contrast", idx),
                "graph_id": graph_id,
                "task_type": "counterfactual_contrast",
                "input": prompt,
                "target": {
                    "contrast_relation": {
                        "source": relation["source"],
                        "type": relation["type"],
                        "target": relation["target"],
                    },
                    "source_summary": node_summary(nodes, relation["source"]),
                    "target_summary": node_summary(nodes, relation["target"]),
                },
                "text_target": (
                    f"{source} contrasts with {target}. "
                    f"{node_summary(nodes, relation['source'])} "
                    f"{node_summary(nodes, relation['target'])}"
                ).strip(),
                "metadata": {
                    "strength": relation.get("strength"),
                    "valence": relation.get("valence", "unknown"),
                },
            }
        )

    property_to_objects: dict[str, list[str]] = {}
    for relation in relations:
        if relation.get("type") == "has_property":
            property_to_objects.setdefault(relation["target"], []).append(relation["source"])

    object_example_index = len(examples)
    for relation in contrast_relations:
        source_property = relation["source"]
        target_property = relation["target"]
        source_objects = sorted(property_to_objects.get(source_property, []))
        target_objects = sorted(property_to_objects.get(target_property, []))

        for source_object in source_objects:
            for target_object in target_objects:
                object_example_index += 1
                source_object_label = node_label(nodes, source_object)
                target_object_label = node_label(nodes, target_object)
                source_property_label = node_label(nodes, source_property)
                target_property_label = node_label(nodes, target_property)
                prompt = (
                    "Object-level counterfactual contrast.\n"
                    f"CASE_A_OBJECT: {source_object_label}\n"
                    f"CASE_A_PROPERTY: {source_property_label}\n"
                    f"CASE_B_OBJECT: {target_object_label}\n"
                    f"CASE_B_PROPERTY: {target_property_label}\n"
                    "If CASE_A_OBJECT is replaced by CASE_B_OBJECT in the same event frame, "
                    "what property relation changes?"
                )
                examples.append(
                    {
                        "id": make_example_id(graph_id, "counterfactual_contrast", object_example_index),
                        "graph_id": graph_id,
                        "task_type": "counterfactual_contrast",
                        "input": prompt,
                        "target": {
                            "object_a": source_object,
                            "object_b": target_object,
                            "property_a": source_property,
                            "property_b": target_property,
                            "contrast_relation": {
                                "source": source_property,
                                "type": relation["type"],
                                "target": target_property,
                            },
                        },
                        "text_target": (
                            f"Replacing {source_object_label} with {target_object_label} changes the "
                            f"active property from {source_property_label} to {target_property_label}. "
                            f"{node_summary(nodes, source_property)} "
                            f"{node_summary(nodes, target_property)}"
                        ).strip(),
                        "metadata": {
                            "source_object_summary": node_summary(nodes, source_object),
                            "target_object_summary": node_summary(nodes, target_object),
                            "contrast_strength": relation.get("strength"),
                        },
                    }
                )

    return examples


def explanation_path_examples(graph: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> list[Example]:
    examples: list[Example] = []
    graph_id = graph["graph_id"]

    for idx, question in enumerate(graph.get("evaluation_questions", []), start=1):
        expected_relations = question.get("expected_relations", [])
        relation_lines = "\n".join(
            f"- {relation_text(nodes, relation)}" for relation in expected_relations
        )
        prompt = (
            "Answer the question using the expected relation path.\n"
            f"QUESTION: {question['question']}\n"
            "EXPECTED_RELATION_PATH:\n"
            f"{relation_lines}\n"
            "ANSWER:"
        )
        examples.append(
            {
                "id": make_example_id(graph_id, "explanation_path", idx),
                "graph_id": graph_id,
                "task_type": "explanation_path",
                "input": prompt,
                "target": {
                    "question_id": question["id"],
                    "expected_answer": question.get("expected_answer", ""),
                    "expected_relations": expected_relations,
                },
                "text_target": question.get("expected_answer", ""),
                "metadata": {
                    "relation_path_length": len(expected_relations),
                },
            }
        )

    return examples


GENERATORS = {
    "relation_completion": relation_completion_examples,
    "state_action_effect": state_action_effect_examples,
    "counterfactual_contrast": counterfactual_contrast_examples,
    "explanation_path": explanation_path_examples,
}


def generate_examples(graph: dict[str, Any], task_types: list[str]) -> list[Example]:
    nodes = node_map(graph)
    examples: list[Example] = []

    for task_type in task_types:
        examples.extend(GENERATORS[task_type](graph, nodes))

    return examples


def validate_examples(examples: list[Example]) -> None:
    ids = [example["id"] for example in examples]
    duplicates = sorted(example_id for example_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate curriculum example ids: {duplicates[:10]}")

    for example in examples:
        for key in ("id", "graph_id", "task_type", "input", "target", "text_target", "metadata"):
            if key not in example:
                raise ValueError(f"example {example.get('id', '<missing>')} missing key: {key}")
        if not isinstance(example["input"], str) or not example["input"].strip():
            raise ValueError(f"example {example['id']} has empty input")


def default_output_path(graph_path: Path, graph: dict[str, Any], output_dir: Path) -> Path:
    graph_name = graph.get("graph_id", graph_path.stem).replace(".", "_")
    return output_dir / f"{graph_name}_curriculum.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph_json", type=Path, help="Path to seed graph JSON")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSONL path. Defaults to data/developmental_graph/curricula/<graph_id>_curriculum.jsonl",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Output manifest JSON path. Defaults to the JSONL path with .manifest.json suffix.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/curricula"),
        help="Default output directory when --output is omitted.",
    )
    parser.add_argument(
        "--task-type",
        action="append",
        choices=sorted(GENERATORS),
        help="Task type to include. May be repeated. Defaults to all task types.",
    )
    args = parser.parse_args()

    graph = load_json(args.graph_json)
    task_types = args.task_type or list(GENERATORS)
    examples = generate_examples(graph, task_types)
    validate_examples(examples)

    output_path = args.output or default_output_path(args.graph_json, graph, args.output_dir)
    manifest_path = args.manifest or output_path.with_suffix(".manifest.json")

    write_jsonl(output_path, examples)

    counts = Counter(example["task_type"] for example in examples)
    manifest = {
        "schema_version": "0.1.0",
        "source_graph": str(args.graph_json),
        "graph_id": graph["graph_id"],
        "output": str(output_path),
        "task_types": task_types,
        "counts": dict(sorted(counts.items())),
        "total_examples": len(examples),
    }
    write_json(manifest_path, manifest)

    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
