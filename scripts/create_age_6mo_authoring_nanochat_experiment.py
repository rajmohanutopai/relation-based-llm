#!/usr/bin/env python3
"""Create nanochat-ready splits from the handwritten age_6mo relation rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT_DIR = Path(
    "data/developmental_graph/relation_authoring/age_6mo_handwritten_relations_v0"
)
DEFAULT_OUTPUT_DIR = Path(
    "data/developmental_graph/experiments/age_6mo_handwritten_relations_v0"
)
EXPERIMENT_ID = "age_6mo_handwritten_relations_v0"
VARIANTS = (
    "plain_text",
    "relation_scaffolded",
    "relation_qa",
    "relation_qa_resolved",
    "mixed",
)


def stable_bucket(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def split_for(row_id: str) -> str:
    bucket = stable_bucket(row_id)
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "dev"
    return "curriculum_test"


def read_rows(input_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(input_dir.glob("batch_*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                row["_source_file"] = path.name
                row["_source_line"] = line_number
                rows.append(row)
    if not rows:
        raise SystemExit(f"{input_dir}: no batch rows found")
    return rows


def relation_sentence(row: dict[str, Any]) -> str:
    return f"{row['subject']} {row['relation']} {row['object']}."


def base_metadata(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_file": row["_source_file"],
        "source_line": row["_source_line"],
        "subject": row["subject"],
        "relation": row["relation"],
        "object": row["object"],
        "domain": row["domain"],
        "polarity": row["polarity"],
        "confidence": row["confidence"],
        "plain_text": row.get("plain_text") or relation_sentence(row),
        "relation_sentence": relation_sentence(row),
    }


def make_record(
    row: dict[str, Any],
    *,
    split: str,
    variant: str,
    surface: str,
    input_text: str,
    target: str,
    task_type: str,
) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "id": f"{EXPERIMENT_ID}.{variant}.{split}.{surface}.{row['id']}",
        "source_example_id": row["id"],
        "split": split,
        "variant": variant,
        "surface": surface,
        "task_type": task_type,
        "input": input_text,
        "target": target,
        "metadata": base_metadata(row),
    }


def make_plain_text(row: dict[str, Any], split: str) -> dict[str, Any]:
    text = row.get("plain_text") or relation_sentence(row)
    return make_record(
        row,
        split=split,
        variant="plain_text",
        surface="statement",
        input_text="",
        target=text,
        task_type="relation_statement",
    )


def make_relation_scaffolded(row: dict[str, Any], split: str) -> dict[str, Any]:
    text = row.get("plain_text") or relation_sentence(row)
    target = f"Relation: {relation_sentence(row)}\nText: {text}"
    return make_record(
        row,
        split=split,
        variant="relation_scaffolded",
        surface="relation_plus_text",
        input_text="",
        target=target,
        task_type="relation_scaffolded_statement",
    )


def is_no_answer(row: dict[str, Any]) -> bool:
    relation = str(row.get("relation", ""))
    return relation.startswith("cannot_")


def yes_no_answer(row: dict[str, Any]) -> str:
    text = row.get("plain_text") or relation_sentence(row)
    answer = "No." if is_no_answer(row) else "Yes."
    return f"{answer} {text}"


def qa_prompt_and_target(row: dict[str, Any]) -> tuple[str, str]:
    subject = row["subject"]
    relation = row["relation"]
    obj = row["object"]
    text = row.get("plain_text") or relation_sentence(row)
    if relation in {"can_be_seen", "cannot_be_seen"}:
        return f"Question: Can the baby see {subject}?\nAnswer:", yes_no_answer(row)
    if relation in {"can_be_touched", "cannot_be_touched"}:
        return f"Question: Can the baby touch {subject}?\nAnswer:", yes_no_answer(row)
    if relation in {"can_control", "cannot_control"}:
        return f"Question: Can the baby control {obj}?\nAnswer:", yes_no_answer(row)
    if relation in {"causes_distress", "causes_discomfort", "causes_pain"}:
        return f"Question: Does {subject} feel bad for the baby?\nAnswer:", yes_no_answer(row)
    if relation in {"causes_comfort", "causes_happiness", "reduces_distress", "reduces_hunger"}:
        return f"Question: Does {subject} help the baby feel better?\nAnswer:", yes_no_answer(row)
    if relation == "is_a":
        return f"Question: What is {subject}?\nAnswer:", text
    if relation == "has_state":
        return f"Question: What state can {subject} have?\nAnswer:", text
    if relation == "has_part":
        return f"Question: What part does {subject} have?\nAnswer:", text
    if relation == "part_of":
        return f"Question: What is {subject} part of?\nAnswer:", text
    if relation in {"allows", "blocks", "prevents"}:
        return f"Question: What does {subject} {relation}?\nAnswer:", text
    if relation in {"creates_new_relation", "strengthens_relation", "weakens_relation", "breaks_relation"}:
        return f"Question: What relation effect does {subject} have?\nAnswer:", text
    return f"Question: What is true about {subject}?\nAnswer:", text


def make_relation_qa(row: dict[str, Any], split: str) -> dict[str, Any]:
    input_text, target = qa_prompt_and_target(row)
    return make_record(
        row,
        split=split,
        variant="relation_qa",
        surface="direct_qa",
        input_text=input_text,
        target=target,
        task_type="relation_direct_qa",
    )


def resolved_qa_prompt_and_target(row: dict[str, Any]) -> tuple[str, str]:
    subject = row["subject"]
    relation = row["relation"]
    obj = row["object"]
    text = row.get("plain_text") or relation_sentence(row)
    if relation == "is_a":
        return f"Question: Is {subject} a {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "has_state":
        return f"Question: Can {subject} have the state {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "has_part":
        return f"Question: Does {subject} have {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "part_of":
        return f"Question: Is {subject} part of {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "can_be_seen":
        return f"Question: Can the baby see {subject}?\nAnswer:", yes_no_answer(row)
    if relation == "cannot_be_seen":
        return f"Question: Can the baby see {subject}?\nAnswer:", yes_no_answer(row)
    if relation == "can_be_touched":
        return f"Question: Can the baby touch {subject}?\nAnswer:", yes_no_answer(row)
    if relation == "cannot_be_touched":
        return f"Question: Can the baby touch {subject}?\nAnswer:", yes_no_answer(row)
    if relation == "can_control":
        return f"Question: Can the baby control {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "cannot_control":
        return f"Question: Can the baby control {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "allows":
        return f"Question: Does {subject} allow {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "blocks":
        return f"Question: Does {subject} block {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "prevents":
        return f"Question: Does {subject} prevent {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "causes_happiness":
        return f"Question: Does {subject} make {obj} happy?\nAnswer:", yes_no_answer(row)
    if relation == "causes_distress":
        return f"Question: Does {subject} cause distress for {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "causes_discomfort":
        return f"Question: Does {subject} cause discomfort for {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "causes_pain":
        return f"Question: Does {subject} cause pain for {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "creates_new_relation":
        return f"Question: Does {subject} create {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "strengthens_relation":
        return f"Question: Does {subject} strengthen {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "weakens_relation":
        return f"Question: Does {subject} weaken {obj}?\nAnswer:", yes_no_answer(row)
    if relation == "breaks_relation":
        return f"Question: Does {subject} break {obj}?\nAnswer:", yes_no_answer(row)
    return f"Question: Is it true that {text}\nAnswer:", yes_no_answer(row)


def make_relation_qa_resolved(row: dict[str, Any], split: str) -> dict[str, Any]:
    input_text, target = resolved_qa_prompt_and_target(row)
    return make_record(
        row,
        split=split,
        variant="relation_qa_resolved",
        surface="resolved_qa",
        input_text=input_text,
        target=target,
        task_type="relation_resolved_qa",
    )


def make_scenario_qa(row: dict[str, Any], split: str) -> dict[str, Any]:
    text = row.get("plain_text") or relation_sentence(row)
    input_text = f"Scene: {text}\nQuestion: What does this mean?\nAnswer:"
    return make_record(
        row,
        split=split,
        variant="mixed",
        surface="scenario_qa",
        input_text=input_text,
        target=yes_no_answer(row),
        task_type="relation_scenario_qa",
    )


def make_mixed_rows(row: dict[str, Any], split: str) -> list[dict[str, Any]]:
    qa_input, qa_target = qa_prompt_and_target(row)
    statement = make_record(
        row,
        split=split,
        variant="mixed",
        surface="statement",
        input_text="",
        target=row.get("plain_text") or relation_sentence(row),
        task_type="relation_statement",
    )
    scaffold = make_record(
        row,
        split=split,
        variant="mixed",
        surface="relation_plus_text",
        input_text="",
        target=f"Relation: {relation_sentence(row)}\nText: {row.get('plain_text') or relation_sentence(row)}",
        task_type="relation_scaffolded_statement",
    )
    direct_qa = make_record(
        row,
        split=split,
        variant="mixed",
        surface="direct_qa",
        input_text=qa_input,
        target=qa_target,
        task_type="relation_direct_qa",
    )
    return [statement, scaffold, direct_qa, make_scenario_qa(row, split)]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"{args.output_dir} exists and is not empty; pass --overwrite")

    source_rows = read_rows(args.input_dir)
    by_variant: dict[str, dict[str, list[dict[str, Any]]]] = {
        variant: {"train": [], "dev": [], "curriculum_test": []} for variant in VARIANTS
    }
    for row in source_rows:
        split = split_for(row["id"])
        by_variant["plain_text"][split].append(make_plain_text(row, split))
        by_variant["relation_scaffolded"][split].append(make_relation_scaffolded(row, split))
        by_variant["relation_qa"][split].append(make_relation_qa(row, split))
        by_variant["relation_qa_resolved"][split].append(make_relation_qa_resolved(row, split))
        by_variant["mixed"][split].extend(make_mixed_rows(row, split))

    dataset_dir = args.output_dir / "datasets"
    for variant in VARIANTS:
        for split, rows in by_variant[variant].items():
            write_jsonl(dataset_dir / variant / f"{split}.jsonl", rows)

    dataset_manifest = {
        "experiment_id": EXPERIMENT_ID,
        "input_dir": str(args.input_dir),
        "output_dir": str(dataset_dir),
        "schema_version": "0.1.0",
        "variants": {
            variant: {
                "splits": {
                    split: {
                        "path": str(dataset_dir / variant / f"{split}.jsonl"),
                        "count": len(rows),
                    }
                    for split, rows in by_variant[variant].items()
                }
            }
            for variant in VARIANTS
        },
    }
    write_json(dataset_dir / "manifest.json", dataset_manifest)

    training_config = {
        "experiment_id": EXPERIMENT_ID,
        "schema_version": "0.1.0",
        "dataset_manifest": str(dataset_dir / "manifest.json"),
        "baseline_model": {"name": "nanochat"},
        "output_root": f"runs/{EXPERIMENT_ID}/nanochat",
        "format": {
            "prompt_template": "{input}",
            "target_template": "{target}",
            "note": "Use create_nanochat_pretrain_shards.py with --mode input_target.",
        },
        "training": {
            "seed": 1729,
            "max_seq_length": 256,
            "recommended_local_smoke": {
                "depth": 2,
                "num_iterations": 100,
                "total_batch_size": 2048,
            },
        },
    }
    write_json(args.output_dir / "training_config.json", training_config)

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "source_rows": len(source_rows),
        "dataset_manifest": str(dataset_dir / "manifest.json"),
        "training_config": str(args.output_dir / "training_config.json"),
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(dataset_manifest["variants"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
