#!/usr/bin/env python3
"""Score model outputs against a held-out developmental evaluation set.

The runner accepts either structured predictions or plain-text answers.

Expected model-output JSONL shape:

```json
{"case_id": "heldout.physical.ceramic_slip_fall", "answer": "..."}
```

Optional structured fields improve scoring:

```json
{
  "case_id": "...",
  "answer": "...",
  "predicted_relation_families": ["schema.object_fall_impact"],
  "predicted_graph_anchors": [
    {"source": "schema.material_impact_outcome", "type": "built_from", "target": "schema.object_fall_impact"}
  ],
  "predicted_gap_indicators": ["schema.tension_pull_connection"]
}
```
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


Relation = tuple[str, str, str]
WORD_RE = re.compile(r"[a-z0-9]+")


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def resolve_path(base_file: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return cwd_path
    return base_file.parent / path


def load_source_graph(evaluation_path: Path, evaluation: dict[str, Any], override: Path | None) -> dict[str, Any] | None:
    if override:
        return load_json(override)
    source_seed = evaluation.get("source_seed")
    if not isinstance(source_seed, str) or not source_seed:
        return None
    source_path = resolve_path(evaluation_path, source_seed)
    if not source_path.exists():
        return None
    return load_json(source_path)


def normalize_text(value: str) -> str:
    return " ".join(WORD_RE.findall(value.lower()))


def id_tail_text(identifier: str) -> str:
    return identifier.split(".")[-1].replace("_", " ")


def node_aliases(graph: dict[str, Any] | None) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}
    if graph:
        for node in graph.get("nodes", []):
            if not isinstance(node, dict) or not isinstance(node.get("id"), str):
                continue
            node_id = node["id"]
            values = {node_id, id_tail_text(node_id)}
            if isinstance(node.get("label"), str):
                values.add(node["label"])
            aliases[node_id] = {normalize_text(value) for value in values if value}
    return aliases


def fallback_aliases(identifier: str) -> set[str]:
    return {normalize_text(identifier), normalize_text(id_tail_text(identifier))}


def aliases_for(identifier: str, aliases: dict[str, set[str]]) -> set[str]:
    return aliases.get(identifier, fallback_aliases(identifier))


def answer_mentions(identifier: str, answer_text: str, aliases: dict[str, set[str]]) -> bool:
    normalized = normalize_text(answer_text)
    return any(alias and alias in normalized for alias in aliases_for(identifier, aliases))


def relation_from_dict(value: Any) -> Relation | None:
    if not isinstance(value, dict):
        return None
    source = value.get("source")
    rel_type = value.get("type")
    target = value.get("target")
    if not all(isinstance(item, str) and item for item in (source, rel_type, target)):
        return None
    return source, rel_type, target


def relation_list(value: Any) -> set[Relation]:
    if not isinstance(value, list):
        return set()
    relations = {relation_from_dict(item) for item in value}
    return {relation for relation in relations if relation is not None}


def string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str) and item}


def load_model_outputs(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with path.open() as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"line {line_no} must be a JSON object")
            case_id = record.get("case_id") or record.get("id")
            if not isinstance(case_id, str) or not case_id:
                raise ValueError(f"line {line_no} missing case_id")
            if case_id in records:
                raise ValueError(f"duplicate model output for case_id: {case_id}")
            records[case_id] = record
    return records


def oracle_outputs(evaluation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for case in evaluation.get("cases", []):
        records[case["id"]] = {
            "case_id": case["id"],
            "answer": case.get("expected_answer", ""),
            "predicted_relation_families": case.get("expected_relation_families", []),
            "predicted_graph_anchors": case.get("graph_anchors", []),
            "predicted_gap_indicators": case.get("gap_indicators", []),
        }
    return records


def first_present(record: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in record:
            return record[name]
    return None


def score_relation_families(
    expected: list[str],
    record: dict[str, Any],
    aliases: dict[str, set[str]],
) -> tuple[int, list[str]]:
    predicted = string_set(
        first_present(record, ("predicted_relation_families", "relation_families", "relations", "relation_family_ids"))
    )
    answer = str(record.get("answer") or record.get("text") or "")
    matched = []
    for family_id in expected:
        if family_id in predicted or answer_mentions(family_id, answer, aliases):
            matched.append(family_id)
    return len(matched), matched


def score_gap_indicators(
    expected: list[str],
    record: dict[str, Any],
    aliases: dict[str, set[str]],
) -> tuple[int, list[str]]:
    predicted = string_set(first_present(record, ("predicted_gap_indicators", "gap_indicators", "gaps")))
    answer = str(record.get("answer") or record.get("text") or "")
    matched = []
    for gap_id in expected:
        if gap_id in predicted or answer_mentions(gap_id, answer, aliases):
            matched.append(gap_id)
    return len(matched), matched


def anchor_text_match(anchor: Relation, answer: str, aliases: dict[str, set[str]]) -> bool:
    source, _rel_type, target = anchor
    return answer_mentions(source, answer, aliases) and answer_mentions(target, answer, aliases)


def score_graph_anchors(
    expected: list[dict[str, Any]],
    record: dict[str, Any],
    aliases: dict[str, set[str]],
) -> tuple[int, list[dict[str, str]]]:
    expected_relations = [relation_from_dict(anchor) for anchor in expected]
    expected_relations = [anchor for anchor in expected_relations if anchor is not None]
    predicted = relation_list(first_present(record, ("predicted_graph_anchors", "graph_anchors", "anchors")))
    answer = str(record.get("answer") or record.get("text") or "")
    matched: list[Relation] = []
    for anchor in expected_relations:
        if anchor in predicted or anchor_text_match(anchor, answer, aliases):
            matched.append(anchor)
    return len(matched), [{"source": source, "type": rel_type, "target": target} for source, rel_type, target in matched]


def ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def passed_case(
    case_type: str,
    relation_recall: float | None,
    anchor_recall: float | None,
    gap_recall: float | None,
    min_relation_recall: float,
    min_anchor_recall: float,
    min_gap_recall: float,
) -> bool:
    if relation_recall is not None and relation_recall < min_relation_recall:
        return False
    if anchor_recall is not None and anchor_recall < min_anchor_recall:
        return False
    if case_type == "gap_probe" and gap_recall is not None and gap_recall < min_gap_recall:
        return False
    return True


def evaluate(
    evaluation: dict[str, Any],
    outputs: dict[str, dict[str, Any]],
    graph: dict[str, Any] | None,
    min_relation_recall: float,
    min_anchor_recall: float,
    min_gap_recall: float,
) -> dict[str, Any]:
    aliases = node_aliases(graph)
    cases = evaluation.get("cases", [])

    per_case: list[dict[str, Any]] = []
    totals = Counter()
    case_type_counts = Counter()
    pass_counts = Counter()

    for case in cases:
        case_id = case["id"]
        case_type = case.get("case_type", "unknown")
        record = outputs.get(case_id, {"case_id": case_id, "answer": ""})

        expected_families = case.get("expected_relation_families", [])
        expected_anchors = case.get("graph_anchors", [])
        expected_gaps = case.get("gap_indicators", [])

        family_hits, matched_families = score_relation_families(expected_families, record, aliases)
        anchor_hits, matched_anchors = score_graph_anchors(expected_anchors, record, aliases)
        gap_hits, matched_gaps = score_gap_indicators(expected_gaps, record, aliases)

        relation_recall = ratio(family_hits, len(expected_families))
        anchor_recall = ratio(anchor_hits, len(expected_anchors))
        gap_recall = ratio(gap_hits, len(expected_gaps))
        case_passed = passed_case(
            case_type,
            relation_recall,
            anchor_recall,
            gap_recall,
            min_relation_recall,
            min_anchor_recall,
            min_gap_recall,
        )

        case_type_counts[case_type] += 1
        pass_counts[case_type] += int(case_passed)
        totals["cases"] += 1
        totals["case_passes"] += int(case_passed)
        totals["expected_relation_families"] += len(expected_families)
        totals["matched_relation_families"] += family_hits
        totals["expected_graph_anchors"] += len(expected_anchors)
        totals["matched_graph_anchors"] += anchor_hits
        totals["expected_gap_indicators"] += len(expected_gaps)
        totals["matched_gap_indicators"] += gap_hits
        if case_id not in outputs:
            totals["missing_outputs"] += 1

        per_case.append(
            {
                "case_id": case_id,
                "case_type": case_type,
                "passed": case_passed,
                "relation_family_recall": relation_recall,
                "anchor_recall": anchor_recall,
                "gap_indicator_recall": gap_recall,
                "matched_relation_families": matched_families,
                "matched_graph_anchors": matched_anchors,
                "matched_gap_indicators": matched_gaps,
                "has_model_output": case_id in outputs,
            }
        )

    summary = {
        "evaluation_id": evaluation.get("evaluation_id"),
        "cases": totals["cases"],
        "missing_outputs": totals["missing_outputs"],
        "unmatched_outputs": len(set(outputs) - {case["id"] for case in cases}),
        "case_pass_rate": ratio(totals["case_passes"], totals["cases"]),
        "relation_family_recall": ratio(totals["matched_relation_families"], totals["expected_relation_families"]),
        "anchor_recall": ratio(totals["matched_graph_anchors"], totals["expected_graph_anchors"]),
        "gap_indicator_recall": ratio(totals["matched_gap_indicators"], totals["expected_gap_indicators"]),
        "case_type_counts": dict(sorted(case_type_counts.items())),
        "case_type_pass_counts": dict(sorted(pass_counts.items())),
        "thresholds": {
            "min_relation_recall": min_relation_recall,
            "min_anchor_recall": min_anchor_recall,
            "min_gap_recall": min_gap_recall,
        },
    }

    return {
        "schema_version": "0.1.0",
        "summary": summary,
        "cases": per_case,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evaluation_json", type=Path, help="Held-out evaluation JSON")
    parser.add_argument("model_outputs_jsonl", nargs="?", type=Path, help="Model output JSONL with case_id and answer")
    parser.add_argument("--source-graph", type=Path, help="Override source graph JSON path")
    parser.add_argument("--output", type=Path, help="Write full result JSON to this path")
    parser.add_argument("--oracle", action="store_true", help="Use expected structured labels as predictions for a smoke test")
    parser.add_argument("--min-relation-recall", type=float, default=0.5)
    parser.add_argument("--min-anchor-recall", type=float, default=0.5)
    parser.add_argument("--min-gap-recall", type=float, default=0.5)
    args = parser.parse_args()

    evaluation = load_json(args.evaluation_json)
    graph = load_source_graph(args.evaluation_json, evaluation, args.source_graph)
    if graph is None:
        print("WARNING: source graph not loaded; text matching will use ID-derived aliases only", file=sys.stderr)

    if args.oracle:
        outputs = oracle_outputs(evaluation)
    elif args.model_outputs_jsonl:
        outputs = load_model_outputs(args.model_outputs_jsonl)
    else:
        parser.error("provide model_outputs_jsonl or --oracle")

    result = evaluate(
        evaluation,
        outputs,
        graph,
        args.min_relation_recall,
        args.min_anchor_recall,
        args.min_gap_recall,
    )

    if args.output:
        write_json(args.output, result)

    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
