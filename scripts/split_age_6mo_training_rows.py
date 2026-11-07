#!/usr/bin/env python3
"""Create deterministic train/dev/test splits for age_6mo training rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def split_name(row: dict[str, Any], train_pct: int, dev_pct: int) -> str:
    digest = hashlib.sha256(row["id"].encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 100
    if bucket < train_pct:
        return "train"
    if bucket < train_pct + dev_pct:
        return "dev"
    return "test"


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    category = Counter(row.get("metadata", {}).get("source_category", "unknown") for row in rows)
    status = Counter(row.get("metadata", {}).get("source_status", "unknown") for row in rows)
    model = Counter(row.get("metadata", {}).get("model", "unknown") for row in rows)
    concepts = {row.get("metadata", {}).get("source_concept") for row in rows}
    concepts.discard(None)
    return {
        "rows": len(rows),
        "unique_concepts": len(concepts),
        "by_category": dict(sorted(category.items())),
        "by_status": dict(sorted(status.items())),
        "by_model": dict(sorted(model.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--train-pct", type=int, default=80)
    parser.add_argument("--dev-pct", type=int, default=10)
    parser.add_argument("--experiment-id", default="age_6mo_full_natural_v0")
    args = parser.parse_args()

    if args.train_pct + args.dev_pct >= 100:
        raise SystemExit("train-pct + dev-pct must be less than 100")

    rows = read_jsonl(args.input)
    splits = {"train": [], "dev": [], "test": []}
    for row in rows:
        splits[split_name(row, args.train_pct, args.dev_pct)].append(row)

    for name, split_rows in splits.items():
        write_jsonl(args.output_dir / f"{name}.jsonl", split_rows)

    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "source_path": str(args.input),
        "split_method": "sha256(row.id) bucket; deterministic row-level split",
        "split_percentages": {
            "train": args.train_pct,
            "dev": args.dev_pct,
            "test": 100 - args.train_pct - args.dev_pct,
        },
        "total": summarize(rows),
        "splits": {name: summarize(split_rows) for name, split_rows in splits.items()},
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
