#!/usr/bin/env python3
"""Inspect authored age_6mo relation rows by global row number."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT_DIR = Path(
    "data/developmental_graph/relation_authoring/age_6mo_handwritten_relations_v0"
)


def iter_rows(input_dir: Path) -> Iterable[dict]:
    global_index = 0
    for path in sorted(input_dir.glob("batch_*.jsonl")):
        with path.open() as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                global_index += 1
                row = json.loads(line)
                row["_global_index"] = global_index
                row["_file"] = path.name
                row["_line"] = line_number
                yield row


def render_relation(row: dict) -> str:
    return f"{row['subject']} {row['relation']} {row['object']}."


def render_training_text(row: dict) -> str:
    plain = row.get("plain_text")
    if plain:
        return plain
    return render_relation(row)


def print_row(row: dict, output_format: str) -> None:
    prefix = f"{row['_global_index']:06d} {row['_file']}:{row['_line']}"
    if output_format == "plain":
        print(f"{prefix} | {render_training_text(row)}")
    elif output_format == "relation":
        print(f"{prefix} | {render_relation(row)}")
    elif output_format == "json":
        clean = {k: v for k, v in row.items() if not k.startswith("_")}
        print(json.dumps(clean, ensure_ascii=True, sort_keys=True))
    else:
        print(f"{prefix}")
        print(f"  relation: {render_relation(row)}")
        print(f"  text:     {render_training_text(row)}")
        if row.get("supporting_relations"):
            print(f"  support:  {'; '.join(row['supporting_relations'])}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--start", type=int, default=1, help="1-based global row start")
    parser.add_argument("--end", type=int, default=None, help="1-based global row end")
    parser.add_argument("--count", type=int, default=100, help="rows to print when --end is omitted")
    parser.add_argument(
        "--format",
        choices=["all", "plain", "relation", "json"],
        default="all",
        help="output shape",
    )
    args = parser.parse_args()

    end = args.end if args.end is not None else args.start + args.count - 1
    if args.start < 1:
        raise SystemExit("--start must be >= 1")
    if end < args.start:
        raise SystemExit("--end must be >= --start")

    printed = 0
    for row in iter_rows(args.input_dir):
        if row["_global_index"] < args.start:
            continue
        if row["_global_index"] > end:
            break
        print_row(row, args.format)
        printed += 1

    if printed == 0:
        raise SystemExit("No rows matched the requested range.")


if __name__ == "__main__":
    main()
