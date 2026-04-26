#!/usr/bin/env python3
"""Generate bridge curriculum examples for prompt-to-graph transfer.

The first physical_v0 run showed that a model could fit structured examples
without recovering graph relation families from natural prompts. This generator
adds deterministic bridge tasks that bind natural descriptions to graph IDs and
anchors, while keeping held-out evaluation prompts out of training.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


Example = dict[str, Any]
Relation = dict[str, Any]


BRIDGE_TASK_TYPES = (
    "node_id_from_paraphrase",
    "relation_family_from_prompt",
    "graph_anchor_from_prompt",
    "explanation_with_relations",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[Example]:
    examples: list[Example] = []
    with path.open() as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}: line {line_no} must be a JSON object")
            examples.append(row)
    return examples


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[Example]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")


def node_map(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {node["id"]: node for node in graph.get("nodes", []) if isinstance(node, dict) and "id" in node}


def node_label(nodes: dict[str, dict[str, Any]], node_id: str, include_id: bool = False) -> str:
    node = nodes.get(node_id, {})
    label = node.get("label") or node_id.split(".")[-1].replace("_", " ")
    if include_id:
        return f"{label} ({node_id})"
    return label


def relation_text(nodes: dict[str, dict[str, Any]], relation: Relation, include_ids: bool = False) -> str:
    source = node_label(nodes, relation["source"], include_id=include_ids)
    rel_type = relation["type"].replace("_", " ")
    target = node_label(nodes, relation["target"], include_id=include_ids)
    return f"{source} --{rel_type}--> {target}"


def relation_family_ids(relations: list[Relation]) -> list[str]:
    families: list[str] = []
    for relation in relations:
        for node_id in (relation.get("source"), relation.get("target")):
            if not isinstance(node_id, str) or node_id.startswith("object."):
                continue
            if node_id not in families:
                families.append(node_id)
    return families


def compact_relation(relation: Relation) -> Relation:
    return {
        "source": relation["source"],
        "type": relation["type"],
        "target": relation["target"],
    }


def make_example_id(graph_id: str, task_type: str, index: int) -> str:
    safe_graph_id = graph_id.replace(".", "_")
    return f"curriculum.{safe_graph_id}.bridge.{task_type}.{index:04d}"


def node_id_from_paraphrase_examples(graph: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> list[Example]:
    graph_id = graph["graph_id"]
    examples: list[Example] = []
    idx = 0

    for node in sorted(graph.get("nodes", []), key=lambda item: item["id"]):
        node_id = node["id"]
        label = node.get("label", node_id)
        summary = node.get("summary", "")
        target = {
            "node_id": node_id,
            "node_label": label,
            "layer": node.get("layer"),
            "kind": node.get("kind"),
        }

        idx += 1
        examples.append(
            {
                "id": make_example_id(graph_id, "node_id_from_paraphrase", idx),
                "graph_id": graph_id,
                "task_type": "node_id_from_paraphrase",
                "input": f"Which graph node matches this physical concept?\nPHRASE: {label}\nNODE_ID:",
                "target": target,
                "text_target": node_id,
                "metadata": {"source": "node_label", "node_id": node_id},
            }
        )

        if summary:
            idx += 1
            examples.append(
                {
                    "id": make_example_id(graph_id, "node_id_from_paraphrase", idx),
                    "graph_id": graph_id,
                    "task_type": "node_id_from_paraphrase",
                    "input": (
                        "Which graph node matches this physical description?\n"
                        f"DESCRIPTION: {summary}\n"
                        "NODE_ID:"
                    ),
                    "target": target,
                    "text_target": node_id,
                    "metadata": {"source": "node_summary", "node_id": node_id},
                }
            )

    return examples


def graph_anchor_from_prompt_examples(graph: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> list[Example]:
    graph_id = graph["graph_id"]
    examples: list[Example] = []
    idx = 0

    for relation in sorted(graph.get("relations", []), key=lambda item: (item["source"], item["type"], item["target"])):
        anchor = compact_relation(relation)
        families = relation_family_ids([anchor])
        idx += 1
        examples.append(
            {
                "id": make_example_id(graph_id, "graph_anchor_from_prompt", idx),
                "graph_id": graph_id,
                "task_type": "graph_anchor_from_prompt",
                "input": (
                    "Convert this natural relation description into graph anchor IDs.\n"
                    f"DESCRIPTION: {relation_text(nodes, anchor)}\n"
                    "GRAPH_ANCHORS:"
                ),
                "target": {
                    "graph_anchors": [anchor],
                    "relation_family_ids": families,
                },
                "text_target": relation_text(nodes, anchor, include_ids=True),
                "metadata": {"source": "graph_relation", "relation_count": 1},
            }
        )

    for question in graph.get("evaluation_questions", []):
        anchors = [compact_relation(relation) for relation in question.get("expected_relations", [])]
        if not anchors:
            continue
        families = relation_family_ids(anchors)
        idx += 1
        examples.append(
            {
                "id": make_example_id(graph_id, "graph_anchor_from_prompt", idx),
                "graph_id": graph_id,
                "task_type": "graph_anchor_from_prompt",
                "input": (
                    "Identify the graph anchors needed to answer this physical question.\n"
                    f"QUESTION: {question['question']}\n"
                    "GRAPH_ANCHORS:"
                ),
                "target": {
                    "prompt_id": question["id"],
                    "graph_anchors": anchors,
                    "relation_family_ids": families,
                },
                "text_target": "\n".join(relation_text(nodes, relation, include_ids=True) for relation in anchors),
                "metadata": {"source": "evaluation_question", "question_id": question["id"], "relation_count": len(anchors)},
            }
        )

    return examples


def relation_family_from_prompt_examples(graph: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> list[Example]:
    graph_id = graph["graph_id"]
    examples: list[Example] = []
    idx = 0

    for question in graph.get("evaluation_questions", []):
        anchors = [compact_relation(relation) for relation in question.get("expected_relations", [])]
        families = relation_family_ids(anchors)
        if not families:
            continue
        idx += 1
        examples.append(
            {
                "id": make_example_id(graph_id, "relation_family_from_prompt", idx),
                "graph_id": graph_id,
                "task_type": "relation_family_from_prompt",
                "input": (
                    "Which relation family IDs are needed for this physical situation?\n"
                    f"QUESTION: {question['question']}\n"
                    "RELATION_FAMILY_IDS:"
                ),
                "target": {
                    "prompt_id": question["id"],
                    "relation_family_ids": families,
                    "graph_anchor_count": len(anchors),
                },
                "text_target": ", ".join(node_label(nodes, node_id, include_id=True) for node_id in families),
                "metadata": {"source": "evaluation_question", "question_id": question["id"]},
            }
        )

    for experience in graph.get("micro_experiences", []):
        observed = [compact_relation(relation) for relation in experience.get("relations_observed", [])]
        families = relation_family_ids(observed)
        if not families:
            continue
        event_lines = "\n".join(f"- {event}" for event in experience.get("events", []))
        idx += 1
        examples.append(
            {
                "id": make_example_id(graph_id, "relation_family_from_prompt", idx),
                "graph_id": graph_id,
                "task_type": "relation_family_from_prompt",
                "input": (
                    "Which relation family IDs are active in this observed physical trace?\n"
                    f"TITLE: {experience.get('title', experience['id'])}\n"
                    "EVENTS:\n"
                    f"{event_lines}\n"
                    "RELATION_FAMILY_IDS:"
                ),
                "target": {
                    "prompt_id": experience["id"],
                    "relation_family_ids": families,
                    "graph_anchor_count": len(observed),
                },
                "text_target": ", ".join(node_label(nodes, node_id, include_id=True) for node_id in families),
                "metadata": {"source": "micro_experience", "experience_id": experience["id"]},
            }
        )

    return examples


def explanation_with_relations_examples(graph: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> list[Example]:
    graph_id = graph["graph_id"]
    examples: list[Example] = []

    for idx, question in enumerate(graph.get("evaluation_questions", []), start=1):
        anchors = [compact_relation(relation) for relation in question.get("expected_relations", [])]
        families = relation_family_ids(anchors)
        family_text = ", ".join(node_label(nodes, node_id, include_id=True) for node_id in families)
        examples.append(
            {
                "id": make_example_id(graph_id, "explanation_with_relations", idx),
                "graph_id": graph_id,
                "task_type": "explanation_with_relations",
                "input": (
                    "Answer this physical question and name the relation families used.\n"
                    f"QUESTION: {question['question']}\n"
                    "ANSWER_WITH_RELATIONS:"
                ),
                "target": {
                    "prompt_id": question["id"],
                    "answer": question.get("expected_answer", ""),
                    "relation_family_ids": families,
                    "graph_anchors": anchors,
                },
                "text_target": f"{question.get('expected_answer', '')} Relation families: {family_text}".strip(),
                "metadata": {"source": "evaluation_question", "question_id": question["id"], "relation_count": len(anchors)},
            }
        )

    return examples


def generate_bridge_examples(graph: dict[str, Any]) -> list[Example]:
    nodes = node_map(graph)
    examples: list[Example] = []
    examples.extend(node_id_from_paraphrase_examples(graph, nodes))
    examples.extend(relation_family_from_prompt_examples(graph, nodes))
    examples.extend(graph_anchor_from_prompt_examples(graph, nodes))
    examples.extend(explanation_with_relations_examples(graph, nodes))
    return examples


def validate_unique_ids(examples: list[Example]) -> None:
    ids = [example["id"] for example in examples]
    duplicates = sorted(example_id for example_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate curriculum example IDs: {duplicates[:10]}")


def default_output_path(graph_path: Path, graph: dict[str, Any], output_dir: Path, combined: bool) -> Path:
    graph_name = graph.get("graph_id", graph_path.stem).replace(".", "_")
    suffix = "physical_v0_1_curriculum" if combined else "bridge_curriculum"
    return output_dir / f"{graph_name}_{suffix}.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph_json", type=Path, help="Path to seed graph JSON")
    parser.add_argument("--base-curriculum", type=Path, help="Optional existing curriculum JSONL to prepend")
    parser.add_argument("--output", type=Path, help="Output curriculum JSONL")
    parser.add_argument("--manifest", type=Path, help="Output manifest JSON")
    parser.add_argument("--output-dir", type=Path, default=Path("data/developmental_graph/curricula"))
    args = parser.parse_args()

    graph = load_json(args.graph_json)
    base_examples = load_jsonl(args.base_curriculum) if args.base_curriculum else []
    bridge_examples = generate_bridge_examples(graph)
    examples = base_examples + bridge_examples
    validate_unique_ids(examples)

    output_path = args.output or default_output_path(args.graph_json, graph, args.output_dir, bool(args.base_curriculum))
    manifest_path = args.manifest or output_path.with_suffix(".manifest.json")
    write_jsonl(output_path, examples)

    counts = Counter(example["task_type"] for example in examples)
    bridge_counts = Counter(example["task_type"] for example in bridge_examples)
    task_types = list(dict.fromkeys([example["task_type"] for example in examples]))
    manifest = {
        "schema_version": "0.1.0",
        "source_graph": str(args.graph_json),
        "graph_id": graph["graph_id"],
        "base_curriculum": str(args.base_curriculum) if args.base_curriculum else None,
        "output": str(output_path),
        "task_types": task_types,
        "counts": dict(sorted(counts.items())),
        "bridge_counts": dict(sorted(bridge_counts.items())),
        "base_example_count": len(base_examples),
        "bridge_example_count": len(bridge_examples),
        "total_examples": len(examples),
        "notes": [
            "Bridge examples bind natural-language prompts to graph node IDs, relation families, and anchors.",
            "Held-out evaluation prompts are not used as bridge training examples.",
        ],
    }
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
