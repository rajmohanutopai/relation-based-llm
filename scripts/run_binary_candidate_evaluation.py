#!/usr/bin/env python3
"""Score binary candidate-scoring held-out outputs."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


Relation = tuple[str, str, str]
YES_NO_RE = re.compile(r"\b(YES|NO)\b", re.IGNORECASE)


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


def answer_text(output: dict[str, Any] | None) -> str:
    if output is None:
        return ""
    for key in ("answer", "text", "output", "prediction"):
        value = output.get(key)
        if isinstance(value, str):
            return value
    return ""


def parse_yes_no(answer: str) -> bool | None:
    match = YES_NO_RE.search(answer)
    if not match:
        return None
    return match.group(1).upper() == "YES"


def threshold_prediction(output: dict[str, Any] | None) -> bool | None:
    if output is None:
        return None
    predicted = output.get("predicted")
    if isinstance(predicted, bool):
        return predicted
    return parse_yes_no(answer_text(output))


def output_margin(output: dict[str, Any] | None) -> float | None:
    if output is None:
        return None
    value = output.get("yes_margin")
    if isinstance(value, int | float):
        return float(value)
    predicted = threshold_prediction(output)
    if predicted is None:
        return None
    return 1.0 if predicted else 0.0


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


def relation_set(values: Any) -> set[Relation]:
    if not isinstance(values, list):
        return set()
    relations = {relation_from_dict(value) for value in values}
    return {relation for relation in relations if relation is not None}


def string_set(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {value for value in values if isinstance(value, str) and value}


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


def build_predictions(
    prompts: list[dict[str, Any]],
    outputs: dict[str, dict[str, Any]],
    selection_mode: str,
) -> dict[str, bool | None]:
    if selection_mode == "threshold":
        return {
            str(prompt.get("case_id")): threshold_prediction(outputs.get(str(prompt.get("case_id"))))
            for prompt in prompts
            if isinstance(prompt.get("case_id"), str)
        }

    if selection_mode != "top_expected_count":
        raise ValueError(f"unknown selection mode: {selection_mode}")

    predictions: dict[str, bool | None] = {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for prompt in prompts:
        prompt_id = prompt.get("case_id")
        source_case_id = prompt.get("source_case_id")
        candidate_type = prompt.get("candidate_type")
        if not all(isinstance(item, str) and item for item in (prompt_id, source_case_id, candidate_type)):
            continue
        grouped[(source_case_id, candidate_type)].append(prompt)
        predictions[prompt_id] = False

    for group_prompts in grouped.values():
        expected_count = sum(1 for prompt in group_prompts if prompt.get("expected") is True)
        if expected_count <= 0:
            continue

        scored: list[tuple[float, str]] = []
        unscored: list[str] = []
        for prompt in group_prompts:
            prompt_id = str(prompt["case_id"])
            margin = output_margin(outputs.get(prompt_id))
            if margin is None:
                unscored.append(prompt_id)
            else:
                scored.append((margin, prompt_id))

        for _margin, prompt_id in sorted(scored, reverse=True)[:expected_count]:
            predictions[prompt_id] = True
        for prompt_id in unscored:
            predictions[prompt_id] = None

    return predictions


def evaluate(
    heldout: dict[str, Any],
    prompts: list[dict[str, Any]],
    outputs: dict[str, dict[str, Any]],
    selection_mode: str,
) -> dict[str, Any]:
    cases = case_expectations(heldout)
    predictions = build_predictions(prompts, outputs, selection_mode)
    prompts_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prompt in prompts:
        source_case_id = prompt.get("source_case_id")
        if not isinstance(source_case_id, str) or not source_case_id:
            raise ValueError(f"prompt row missing source_case_id: {prompt!r}")
        prompts_by_source[source_case_id].append(prompt)

    binary_totals = Counter()
    binary_by_type: dict[str, Counter] = defaultdict(Counter)
    per_candidate: list[dict[str, Any]] = []
    per_case: list[dict[str, Any]] = []
    case_type_counts = Counter()
    case_type_pass_counts = Counter()

    for prompt in prompts:
        prompt_id = prompt.get("case_id")
        if not isinstance(prompt_id, str):
            continue
        output = outputs.get(prompt_id)
        answer = answer_text(output)
        predicted = predictions.get(prompt_id)
        expected = bool(prompt.get("expected"))
        candidate_type = str(prompt.get("candidate_type") or "unknown")
        correct = predicted == expected

        binary_totals["rows"] += 1
        binary_totals["missing_outputs"] += int(output is None)
        binary_totals["unparseable"] += int(predicted is None)
        binary_totals["correct"] += int(correct)
        binary_totals["expected_yes"] += int(expected)
        binary_totals["predicted_yes"] += int(predicted is True)
        binary_totals["yes_hits"] += int(predicted is True and expected)

        type_totals = binary_by_type[candidate_type]
        type_totals["rows"] += 1
        type_totals["missing_outputs"] += int(output is None)
        type_totals["unparseable"] += int(predicted is None)
        type_totals["correct"] += int(correct)
        type_totals["expected_yes"] += int(expected)
        type_totals["predicted_yes"] += int(predicted is True)
        type_totals["yes_hits"] += int(predicted is True and expected)

        per_candidate.append(
            {
                "prompt_id": prompt_id,
                "source_case_id": prompt.get("source_case_id"),
                "candidate_type": candidate_type,
                "candidate_option": prompt.get("candidate_option"),
                "expected": expected,
                "predicted": predicted,
                "correct": correct,
                "answer": answer,
            }
        )

    family_hits_total = anchor_hits_total = gap_hits_total = 0
    predicted_families_total = expected_families_total = 0
    predicted_anchors_total = expected_anchors_total = 0
    predicted_gaps_total = expected_gaps_total = 0

    for case_id, case in cases.items():
        case_prompts = prompts_by_source.get(case_id, [])
        case_type = case.get("case_type", "unknown")
        expected_families = string_set(case.get("expected_relation_families"))
        expected_anchors = relation_set(case.get("graph_anchors"))
        expected_gaps = string_set(case.get("gap_indicators"))
        predicted_families: set[str] = set()
        predicted_anchors: set[Relation] = set()
        predicted_gaps: set[str] = set()

        for prompt in case_prompts:
            prompt_id = prompt.get("case_id")
            predicted = predictions.get(prompt_id) if isinstance(prompt_id, str) else None
            if predicted is not True:
                continue

            candidate_type = prompt.get("candidate_type")
            if candidate_type == "relation_family":
                value = prompt.get("candidate_relation_family_id")
                if isinstance(value, str):
                    predicted_families.add(value)
            elif candidate_type == "graph_anchor":
                relation = relation_from_dict(prompt.get("candidate_graph_anchor"))
                if relation is not None:
                    predicted_anchors.add(relation)
            elif candidate_type == "gap":
                value = prompt.get("candidate_gap_id")
                if isinstance(value, str):
                    predicted_gaps.add(value)

        family_precision, family_recall, family_f1, family_hits = precision_recall_f1(
            predicted_families, expected_families
        )
        anchor_precision, anchor_recall, anchor_f1, anchor_hits = precision_recall_f1(
            predicted_anchors, expected_anchors
        )
        gap_precision, gap_recall, gap_f1, gap_hits = precision_recall_f1(predicted_gaps, expected_gaps)

        exact_family_set = predicted_families == expected_families
        exact_anchor_set = predicted_anchors == expected_anchors
        exact_gap_set = predicted_gaps == expected_gaps
        passed = exact_family_set and exact_anchor_set and (exact_gap_set if expected_gaps else True)

        case_type_counts[case_type] += 1
        case_type_pass_counts[case_type] += int(passed)
        family_hits_total += family_hits
        anchor_hits_total += anchor_hits
        gap_hits_total += gap_hits
        predicted_families_total += len(predicted_families)
        expected_families_total += len(expected_families)
        predicted_anchors_total += len(predicted_anchors)
        expected_anchors_total += len(expected_anchors)
        predicted_gaps_total += len(predicted_gaps)
        expected_gaps_total += len(expected_gaps)

        per_case.append(
            {
                "case_id": case_id,
                "case_type": case_type,
                "passed": passed,
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
            }
        )

    def type_summary(counts: Counter) -> dict[str, float | int | None]:
        return {
            "rows": counts["rows"],
            "missing_outputs": counts["missing_outputs"],
            "unparseable": counts["unparseable"],
            "accuracy": ratio(counts["correct"], counts["rows"]),
            "yes_precision": ratio(counts["yes_hits"], counts["predicted_yes"]),
            "yes_recall": ratio(counts["yes_hits"], counts["expected_yes"]),
            "expected_yes": counts["expected_yes"],
            "predicted_yes": counts["predicted_yes"],
        }

    summary = {
        "evaluation_id": heldout.get("evaluation_id"),
        "cases": len(cases),
        "binary_rows": binary_totals["rows"],
        "binary_accuracy": ratio(binary_totals["correct"], binary_totals["rows"]),
        "binary_unparseable": binary_totals["unparseable"],
        "binary_missing_outputs": binary_totals["missing_outputs"],
        "binary_yes_precision": ratio(binary_totals["yes_hits"], binary_totals["predicted_yes"]),
        "binary_yes_recall": ratio(binary_totals["yes_hits"], binary_totals["expected_yes"]),
        "case_pass_rate": ratio(sum(1 for row in per_case if row["passed"]), len(per_case)),
        "relation_family_precision": ratio(family_hits_total, predicted_families_total),
        "relation_family_recall": ratio(family_hits_total, expected_families_total),
        "anchor_precision": ratio(anchor_hits_total, predicted_anchors_total),
        "anchor_recall": ratio(anchor_hits_total, expected_anchors_total),
        "gap_precision": ratio(gap_hits_total, predicted_gaps_total),
        "gap_recall": ratio(gap_hits_total, expected_gaps_total),
        "case_type_counts": dict(sorted(case_type_counts.items())),
        "case_type_pass_counts": dict(sorted(case_type_pass_counts.items())),
        "candidate_type_summary": {
            candidate_type: type_summary(counts)
            for candidate_type, counts in sorted(binary_by_type.items())
        },
        "selection_mode": selection_mode,
        "scoring_rule": "Each candidate is judged YES/NO; case pass requires exact positive family, anchor, and gap sets.",
    }

    return {
        "schema_version": "0.1.0",
        "summary": summary,
        "candidates": per_candidate,
        "cases": per_case,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("heldout_json", type=Path)
    parser.add_argument("heldout_prompts_jsonl", type=Path)
    parser.add_argument("model_outputs_jsonl", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--selection-mode", choices=("threshold", "top_expected_count"), default="threshold")
    args = parser.parse_args()

    heldout = load_json(args.heldout_json)
    prompts = load_jsonl(args.heldout_prompts_jsonl)
    outputs = rows_by_case_id(load_jsonl(args.model_outputs_jsonl), args.model_outputs_jsonl)
    result = evaluate(heldout, prompts, outputs, args.selection_mode)

    if args.output:
        write_json(args.output, result)

    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
