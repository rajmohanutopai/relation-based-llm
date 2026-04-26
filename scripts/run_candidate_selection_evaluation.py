#!/usr/bin/env python3
"""Score closed-vocabulary candidate-selection held-out outputs."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


Relation = tuple[str, str, str]
ID_RE = re.compile(r"\b(?:channel|invariant|schema|property|event|object)\.[a-z0-9_]+\b")
TRIPLE_RE = re.compile(
    r"\b((?:channel|invariant|schema|property|event|object)\.[a-z0-9_]+)\s*--([a-z0-9_]+)-->\s*"
    r"((?:channel|invariant|schema|property|event|object)\.[a-z0-9_]+)\b"
)
SECTION_RE = re.compile(r"^\s*(SELECTED_[A-Z_]+):\s*$", re.MULTILINE)
OPTION_RE = re.compile(r"\b([FNAG]\d{2})\b")


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


def relation_from_dict(value: Any) -> Relation | None:
    if not isinstance(value, dict):
        return None
    source = value.get("source")
    rel_type = value.get("type")
    target = value.get("target")
    if not all(isinstance(item, str) and item for item in (source, rel_type, target)):
        return None
    return source, rel_type, target


def relation_text(relation: Relation) -> str:
    source, rel_type, target = relation
    return f"{source} --{rel_type}--> {target}"


def relation_set(values: Any) -> set[Relation]:
    if not isinstance(values, list):
        return set()
    relations = {relation_from_dict(value) for value in values}
    return {relation for relation in relations if relation is not None}


def string_set(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {value for value in values if isinstance(value, str) and value}


def family_option_map(prompt: dict[str, Any]) -> dict[str, str]:
    options: dict[str, str] = {}
    for row in prompt.get("candidate_relation_family_options", []):
        if not isinstance(row, dict):
            continue
        option = row.get("option")
        family_id = row.get("relation_family_id")
        if isinstance(option, str) and isinstance(family_id, str):
            options[option] = family_id
    return options


def anchor_option_map(prompt: dict[str, Any]) -> dict[str, Relation]:
    options: dict[str, Relation] = {}
    for row in prompt.get("candidate_graph_anchor_options", []):
        if not isinstance(row, dict):
            continue
        option = row.get("option")
        relation = relation_from_dict(row.get("graph_anchor"))
        if isinstance(option, str) and relation is not None:
            options[option] = relation
    return options


def gap_option_map(prompt: dict[str, Any]) -> dict[str, str]:
    options: dict[str, str] = {}
    for row in prompt.get("candidate_gap_options", []):
        if not isinstance(row, dict):
            continue
        option = row.get("option")
        gap_id = row.get("gap_id")
        if isinstance(option, str) and isinstance(gap_id, str):
            options[option] = gap_id
    return options


def rows_by_case_id(rows: list[dict[str, Any]], path: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = row.get("case_id") or row.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"{path}: row missing case_id")
        if case_id in result:
            raise ValueError(f"{path}: duplicate case_id {case_id}")
        result[case_id] = row
    return result


def case_expectations(heldout: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {case["id"]: case for case in heldout.get("cases", [])}


def answer_text(output: dict[str, Any] | None) -> str:
    if output is None:
        return ""
    for key in ("answer", "text", "output", "prediction"):
        value = output.get(key)
        if isinstance(value, str):
            return value
    return ""


def answer_sections(answer: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(answer))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(answer)
        sections[name] = answer[start:end].strip()
    return sections


def extract_candidate_ids(answer: str, candidates: set[str]) -> set[str]:
    mentioned = set(ID_RE.findall(answer))
    return mentioned & candidates


def extract_option_values(answer: str, options: dict[str, Any]) -> set[Any]:
    return {options[option] for option in OPTION_RE.findall(answer) if option in options}


def extract_candidate_relations(answer: str, candidates: set[Relation]) -> set[Relation]:
    matched = {
        (source, rel_type, target)
        for source, rel_type, target in TRIPLE_RE.findall(answer)
        if (source, rel_type, target) in candidates
    }
    for relation in candidates:
        if relation_text(relation) in answer:
            matched.add(relation)
    return matched


def non_candidate_ids(answer: str, allowed_ids: set[str]) -> set[str]:
    return set(ID_RE.findall(answer)) - allowed_ids


def precision_recall_f1(predicted: set[Any], expected: set[Any]) -> tuple[float | None, float | None, float | None, int]:
    hits = len(predicted & expected)
    precision = hits / len(predicted) if predicted else (1.0 if not expected else 0.0)
    recall = hits / len(expected) if expected else None
    if recall is None:
        f1 = None
    elif precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1, hits


def ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def evaluate(
    heldout: dict[str, Any],
    prompts: dict[str, dict[str, Any]],
    outputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    cases = case_expectations(heldout)
    per_case: list[dict[str, Any]] = []
    totals = Counter()
    case_type_counts = Counter()
    case_type_pass_counts = Counter()

    for case_id, case in cases.items():
        prompt = prompts.get(case_id, {})
        output = outputs.get(case_id)
        answer = answer_text(output)
        case_type = case.get("case_type", "unknown")

        expected_families = string_set(case.get("expected_relation_families"))
        expected_anchors = relation_set(case.get("graph_anchors"))
        expected_gaps = string_set(case.get("gap_indicators"))

        candidate_families = string_set(prompt.get("candidate_relation_family_ids"))
        candidate_anchors = relation_set(prompt.get("candidate_graph_anchors"))
        candidate_gaps = string_set(prompt.get("candidate_gap_indicators"))
        allowed_ids = candidate_families | candidate_gaps
        for source, _rel_type, target in candidate_anchors:
            allowed_ids.add(source)
            allowed_ids.add(target)

        sections = answer_sections(answer)
        family_text = sections.get("SELECTED_RELATION_OPTIONS") or sections.get("SELECTED_RELATION_FAMILY_IDS", answer)
        anchor_text = sections.get("SELECTED_ANCHOR_OPTIONS") or sections.get("SELECTED_GRAPH_ANCHORS", answer)
        gap_text = sections.get("SELECTED_GAP_OPTIONS") or sections.get("SELECTED_GAP_IDS", answer)

        predicted_families = {
            *extract_option_values(family_text, family_option_map(prompt)),
            *extract_candidate_ids(family_text, candidate_families),
        }
        predicted_anchors = {
            *extract_option_values(anchor_text, anchor_option_map(prompt)),
            *extract_candidate_relations(anchor_text, candidate_anchors),
        }
        predicted_gaps = {
            *extract_option_values(gap_text, gap_option_map(prompt)),
            *extract_candidate_ids(gap_text, candidate_gaps),
        }
        non_candidate_id_mentions = non_candidate_ids(answer, allowed_ids)

        family_precision, family_recall, family_f1, family_hits = precision_recall_f1(predicted_families, expected_families)
        anchor_precision, anchor_recall, anchor_f1, anchor_hits = precision_recall_f1(predicted_anchors, expected_anchors)
        gap_precision, gap_recall, gap_f1, gap_hits = precision_recall_f1(predicted_gaps, expected_gaps)

        exact_family_set = predicted_families == expected_families
        exact_anchor_set = predicted_anchors == expected_anchors
        exact_gap_set = predicted_gaps == expected_gaps
        passed = exact_family_set and exact_anchor_set and (exact_gap_set if expected_gaps else True)

        case_type_counts[case_type] += 1
        case_type_pass_counts[case_type] += int(passed)
        totals["cases"] += 1
        totals["case_passes"] += int(passed)
        totals["missing_outputs"] += int(output is None)
        totals["expected_families"] += len(expected_families)
        totals["predicted_families"] += len(predicted_families)
        totals["family_hits"] += family_hits
        totals["expected_anchors"] += len(expected_anchors)
        totals["predicted_anchors"] += len(predicted_anchors)
        totals["anchor_hits"] += anchor_hits
        totals["expected_gaps"] += len(expected_gaps)
        totals["predicted_gaps"] += len(predicted_gaps)
        totals["gap_hits"] += gap_hits
        totals["non_candidate_id_mentions"] += len(non_candidate_id_mentions)

        per_case.append(
            {
                "case_id": case_id,
                "case_type": case_type,
                "passed": passed,
                "has_model_output": output is not None,
                "exact_family_set": exact_family_set,
                "exact_anchor_set": exact_anchor_set,
                "exact_gap_set": exact_gap_set,
                "family_precision": family_precision,
                "family_recall": family_recall,
                "family_f1": family_f1,
                "anchor_precision": anchor_precision,
                "anchor_recall": anchor_recall,
                "anchor_f1": anchor_f1,
                "gap_precision": gap_precision,
                "gap_recall": gap_recall,
                "gap_f1": gap_f1,
                "expected_relation_families": sorted(expected_families),
                "predicted_relation_families": sorted(predicted_families),
                "expected_graph_anchors": [relation_text(relation) for relation in sorted(expected_anchors)],
                "predicted_graph_anchors": [relation_text(relation) for relation in sorted(predicted_anchors)],
                "expected_gap_indicators": sorted(expected_gaps),
                "predicted_gap_indicators": sorted(predicted_gaps),
                "non_candidate_id_mentions": sorted(non_candidate_id_mentions),
                "answer": answer,
            }
        )

    family_precision = ratio(totals["family_hits"], totals["predicted_families"])
    family_recall = ratio(totals["family_hits"], totals["expected_families"])
    anchor_precision = ratio(totals["anchor_hits"], totals["predicted_anchors"])
    anchor_recall = ratio(totals["anchor_hits"], totals["expected_anchors"])
    gap_precision = ratio(totals["gap_hits"], totals["predicted_gaps"])
    gap_recall = ratio(totals["gap_hits"], totals["expected_gaps"])

    summary = {
        "evaluation_id": heldout.get("evaluation_id"),
        "cases": totals["cases"],
        "missing_outputs": totals["missing_outputs"],
        "case_pass_rate": ratio(totals["case_passes"], totals["cases"]),
        "relation_family_precision": family_precision,
        "relation_family_recall": family_recall,
        "anchor_precision": anchor_precision,
        "anchor_recall": anchor_recall,
        "gap_precision": gap_precision,
        "gap_recall": gap_recall,
        "non_candidate_id_mentions": totals["non_candidate_id_mentions"],
        "case_type_counts": dict(sorted(case_type_counts.items())),
        "case_type_pass_counts": dict(sorted(case_type_pass_counts.items())),
        "scoring_rule": "case passes only if selected family set and anchor set exactly match expected; gap set must also match when expected gaps exist",
    }

    return {
        "schema_version": "0.1.0",
        "summary": summary,
        "cases": per_case,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("heldout_json", type=Path)
    parser.add_argument("heldout_prompts_jsonl", type=Path)
    parser.add_argument("model_outputs_jsonl", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    heldout = load_json(args.heldout_json)
    prompts = rows_by_case_id(load_jsonl(args.heldout_prompts_jsonl), args.heldout_prompts_jsonl)
    outputs = rows_by_case_id(load_jsonl(args.model_outputs_jsonl), args.model_outputs_jsonl)
    result = evaluate(heldout, prompts, outputs)

    if args.output:
        write_json(args.output, result)

    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
