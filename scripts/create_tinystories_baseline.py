#!/usr/bin/env python3
"""Create a TinyStories normal-simple-text baseline slice.

This streams only enough TinyStories text to match a requested word budget. The
goal is a normal simple-language baseline for relation-curriculum experiments,
not a full local mirror of the multi-GB TinyStories corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import requests


VARIANT = "tinystories_plain_text"
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")
END_MARKER = "<|endoftext|>"
TRAIN_URL = "https://huggingface.co/datasets/roneneldan/TinyStories/resolve/main/TinyStories-train.txt"
VALID_URL = "https://huggingface.co/datasets/roneneldan/TinyStories/resolve/main/TinyStories-valid.txt"


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite")
    if path.exists() and overwrite:
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def story_stream(url: str) -> Iterable[str]:
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    buffer = ""
    try:
        for chunk in response.iter_content(chunk_size=1024 * 128, decode_unicode=True):
            if not chunk:
                continue
            buffer += chunk
            while END_MARKER in buffer:
                story, buffer = buffer.split(END_MARKER, 1)
                story = clean_story(story)
                if story:
                    yield story
        trailing = clean_story(buffer)
        if trailing:
            yield trailing
    finally:
        response.close()


def clean_story(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [" ".join(line.strip().split()) for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def word_count(text: str) -> int:
    return len(text.split())


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, int]:
    words: Counter[str] = Counter()
    raw: Counter[str] = Counter()
    for row in rows:
        text = str(row["target"]).lower()
        words.update(WORD_RE.findall(text))
        raw.update(RAW_RE.findall(text))
    return {
        "unique_words_alpha": len(words),
        "total_words_alpha": sum(words.values()),
        "unique_raw_whitespace_tokens": len(raw),
        "total_raw_whitespace_tokens": sum(raw.values()),
    }


def collect_stories(url: str, start_index: int, target_words: int, split: str, skip: int = 0) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    total_words = 0
    consumed = 0
    for stream_index, story in enumerate(story_stream(url)):
        if stream_index < skip:
            continue
        source_index = start_index + consumed
        consumed += 1
        story_words = word_count(story)
        if story_words == 0:
            continue
        rows.append(
            {
                "id": f"dataset.tinystories_v0.{VARIANT}.{split}.{source_index:08d}",
                "source_example_id": f"tinystories.{split}.{source_index:08d}",
                "experiment_id": "tinystories_v0",
                "variant": VARIANT,
                "split": split,
                "task_type": "normal_simple_story",
                "input": "",
                "target": story,
                "messages": [
                    {"role": "assistant", "content": story},
                ],
                "metadata": {
                    "domain_id": "tinystories",
                    "source_dataset": "roneneldan/TinyStories",
                    "source_url": url,
                    "representation": VARIANT,
                    "word_count": story_words,
                },
            }
        )
        total_words += story_words
        if total_words >= target_words:
            return rows, skip + consumed
    raise RuntimeError(f"{url} ended before collecting {target_words} words")


def file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        name: {"path": str(path), "sha256": sha256_file(path)}
        for name, path in sorted(paths.items())
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/developmental_graph/experiments/tinystories_v0"))
    parser.add_argument("--train-words", type=int, default=270_309)
    parser.add_argument("--dev-words", type=int, default=32_772)
    parser.add_argument("--test-words", type=int, default=36_626)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_output_dir(args.output_dir, args.overwrite)

    train_rows, _ = collect_stories(TRAIN_URL, 0, args.train_words, "train")
    dev_rows, next_valid_index = collect_stories(VALID_URL, 0, args.dev_words, "dev")
    test_rows, _ = collect_stories(
        VALID_URL,
        next_valid_index,
        args.test_words,
        "curriculum_test",
        skip=next_valid_index,
    )

    split_rows = {
        "train": train_rows,
        "dev": dev_rows,
        "curriculum_test": test_rows,
    }

    output_paths: dict[str, Path] = {}
    for split, rows in split_rows.items():
        top_path = args.output_dir / f"{split}.jsonl"
        dataset_path = args.output_dir / "datasets" / VARIANT / f"{split}.jsonl"
        write_jsonl(top_path, rows)
        write_jsonl(dataset_path, rows)
        output_paths[f"source.{split}"] = top_path
        output_paths[f"{VARIANT}.{split}"] = dataset_path

    dataset_manifest_path = args.output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": "tinystories_v0",
        "output_dir": str(args.output_dir / "datasets"),
        "source_dataset": "roneneldan/TinyStories",
        "source_urls": {
            "train": TRAIN_URL,
            "validation": VALID_URL,
        },
        "budget_policy": {
            "matched_to": "procedural_foundation_v3 relation variants",
            "train_words_requested": args.train_words,
            "dev_words_requested": args.dev_words,
            "test_words_requested": args.test_words,
            "unit": "whitespace word approximation; complete stories are kept, so actual totals may exceed requested budgets",
        },
        "variants": {
            VARIANT: {
                split: {
                    "total": len(rows),
                    "task_type_counts": {"normal_simple_story": len(rows)},
                    "vocabulary": vocab_stats(rows),
                    "whitespace_words": sum(word_count(row["target"]) for row in rows),
                }
                for split, rows in split_rows.items()
            }
        },
        "outputs": file_manifest({name: path for name, path in output_paths.items()}),
    }
    write_json(dataset_manifest_path, dataset_manifest)
    output_paths["dataset_manifest"] = dataset_manifest_path

    training_config_path = args.output_dir / "training_config.json"
    training_config = {
        "schema_version": "0.1.0",
        "experiment_id": "tinystories_v0",
        "baseline_model": {
            "name": "nanochat",
            "role": "normal simple text baseline for procedural_foundation_v3",
        },
        "dataset_manifest": str(dataset_manifest_path),
        "output_root": "runs/tinystories_v0/nanochat",
        "format": {
            "prompt_template": "",
            "target_template": "{target}",
        },
        "training": {
            "max_seq_length": 512,
            "seed": 1729,
        },
        "frozen_commands": {
            VARIANT: f"python3 scripts/train_tiny_causal_lm.py --config {args.output_dir / 'training_config.json'} --variant {VARIANT} --dry-run"
        },
    }
    write_json(training_config_path, training_config)
    output_paths["training_config"] = training_config_path

    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": "tinystories_v0",
        "variant": VARIANT,
        "source_dataset": "roneneldan/TinyStories",
        "splits": {split: len(rows) for split, rows in split_rows.items()},
        "whitespace_words": {split: sum(word_count(row["target"]) for row in rows) for split, rows in split_rows.items()},
        "dataset_manifest": str(dataset_manifest_path),
        "training_config": str(training_config_path),
        "outputs": file_manifest(output_paths),
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
