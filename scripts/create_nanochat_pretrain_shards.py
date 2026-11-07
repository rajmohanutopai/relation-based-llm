#!/usr/bin/env python3
"""Create nanochat-compatible pretraining Parquet shards from project JSONL.

nanochat's base pretraining loader expects Parquet files with a `text` column
under `$NANOCHAT_BASE_DIR/base_data_climbmix`. The last sorted shard is used as
validation, and the earlier shards are used as train.
"""

from __future__ import annotations

import argparse
import json
import sys
import os
import random
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from output_state import atomic_write_text  # noqa: E402


TRAIN_SHARD = "shard_00000.parquet"
VAL_SHARD = "shard_06542.parquet"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise SystemExit(f"{path}:{line_number}: expected a JSON object")
            records.append(record)
    if not records:
        raise SystemExit(f"{path}: no records found")
    return records


def render_record(record: dict[str, Any], mode: str) -> str:
    record_id = str(record.get("id") or record.get("source_example_id") or "unknown")
    task_type = str(record.get("task_type") or "unknown")
    variant = str(record.get("variant") or record.get("metadata", {}).get("representation") or "unknown")
    input_text = str(record.get("input") or "")
    target_text = str(record.get("target") or "")

    if not input_text and isinstance(record.get("messages"), list):
        user_parts = [
            str(message.get("content", ""))
            for message in record["messages"]
            if isinstance(message, dict) and message.get("role") == "user"
        ]
        input_text = "\n".join(part for part in user_parts if part)

    if not target_text and isinstance(record.get("messages"), list):
        assistant_parts = [
            str(message.get("content", ""))
            for message in record["messages"]
            if isinstance(message, dict) and message.get("role") == "assistant"
        ]
        target_text = "\n".join(part for part in assistant_parts if part)

    if mode == "target_only":
        body = target_text
    elif mode == "input_target":
        body = f"{input_text}\n\n{target_text}"
    elif mode == "conversation":
        body = (
            f"EXAMPLE_ID: {record_id}\n"
            f"TASK_TYPE: {task_type}\n"
            f"VARIANT: {variant}\n\n"
            f"QUESTION:\n{input_text}\n\n"
            f"ANSWER:\n{target_text}"
        )
    else:
        raise ValueError(f"unknown mode: {mode}")

    return body.strip()


def repeat_and_limit(texts: list[str], repeat: int, max_docs: int | None) -> list[str]:
    if repeat < 1:
        raise SystemExit("--train-repeat and --val-repeat must be >= 1")
    repeated = texts * repeat
    if max_docs is not None:
        repeated = repeated[:max_docs]
    return repeated


def write_parquet(texts: list[str], path: Path) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise SystemExit(
            "pyarrow is required to write Parquet. Install nanochat dependencies "
            "or run `python -m pip install pyarrow` in the active environment."
        ) from exc

    table = pa.table({"text": texts})
    pq.write_table(table, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create nanochat base_data_climbmix shards from JSONL examples."
    )
    parser.add_argument("--train-jsonl", required=True, type=Path)
    parser.add_argument("--val-jsonl", required=True, type=Path)
    parser.add_argument(
        "--base-dir",
        required=True,
        type=Path,
        help="NANOCHAT_BASE_DIR to create. Writes base_data_climbmix inside it.",
    )
    parser.add_argument(
        "--mode",
        choices=["conversation", "input_target", "target_only"],
        default="conversation",
    )
    parser.add_argument("--train-repeat", type=int, default=1)
    parser.add_argument("--val-repeat", type=int, default=1)
    parser.add_argument("--max-train-docs", type=int, default=None)
    parser.add_argument("--max-val-docs", type=int, default=None)
    parser.add_argument("--shuffle-train", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing shard files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_records = read_jsonl(args.train_jsonl)
    val_records = read_jsonl(args.val_jsonl)

    train_texts = [render_record(record, args.mode) for record in train_records]
    val_texts = [render_record(record, args.mode) for record in val_records]
    train_texts = repeat_and_limit(train_texts, args.train_repeat, args.max_train_docs)
    val_texts = repeat_and_limit(val_texts, args.val_repeat, args.max_val_docs)

    if args.shuffle_train:
        rng = random.Random(args.seed)
        rng.shuffle(train_texts)

    data_dir = args.base_dir / "base_data_climbmix"
    data_dir.mkdir(parents=True, exist_ok=True)
    train_path = data_dir / TRAIN_SHARD
    val_path = data_dir / VAL_SHARD
    manifest_path = data_dir / "manifest.json"

    for output_path in [train_path, val_path, manifest_path]:
        if output_path.exists() and not args.overwrite:
            raise SystemExit(f"{output_path} already exists; pass --overwrite to replace it")

    # Write aside and move last, so a crash can't pair a new train shard with an
    # old val shard. The suffix keeps nanochat from reading these as shards.
    staged_train = train_path.with_name(f"{train_path.name}.tmp-{os.getpid()}")
    staged_val = val_path.with_name(f"{val_path.name}.tmp-{os.getpid()}")
    try:
        write_parquet(train_texts, staged_train)
        write_parquet(val_texts, staged_val)
        manifest_path.unlink(missing_ok=True)
        os.replace(staged_train, train_path)
        os.replace(staged_val, val_path)
    finally:
        staged_train.unlink(missing_ok=True)
        staged_val.unlink(missing_ok=True)

    manifest = {
        "format": "nanochat_base_data_climbmix",
        "train_jsonl": str(args.train_jsonl),
        "val_jsonl": str(args.val_jsonl),
        "mode": args.mode,
        "train_repeat": args.train_repeat,
        "val_repeat": args.val_repeat,
        "max_train_docs": args.max_train_docs,
        "max_val_docs": args.max_val_docs,
        "shuffle_train": args.shuffle_train,
        "seed": args.seed,
        "train_docs": len(train_texts),
        "val_docs": len(val_texts),
        "train_shard": str(train_path),
        "val_shard": str(val_path),
    }
    atomic_write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")

    print(f"Wrote {train_path} ({len(train_texts)} docs)")
    print(f"Wrote {val_path} ({len(val_texts)} docs)")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
