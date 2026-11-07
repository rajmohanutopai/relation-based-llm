#!/usr/bin/env python3
"""Create deterministic train/dev/test splits for a developmental experiment.

This script turns generated curriculum JSONL into model-ready split files while
keeping held-out transfer evaluation separate. It does not create baseline
variants; those come in the next roadmap step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import os
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from output_state import atomic_write_text  # noqa: E402


Example = dict[str, Any]


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[Example]:
    examples: list[Example] = []
    with path.open() as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            example = json.loads(line)
            if not isinstance(example, dict):
                raise ValueError(f"{path}: line {line_no} must be a JSON object")
            examples.append(example)
    return examples


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_sizes(total: int, train_ratio: float, dev_ratio: float, test_ratio: float) -> tuple[int, int, int]:
    if total <= 0:
        return 0, 0, 0

    train_count = int(total * train_ratio)
    dev_count = int(total * dev_ratio)
    test_count = total - train_count - dev_count

    if total >= 3:
        if dev_ratio > 0 and dev_count == 0:
            dev_count = 1
            train_count -= 1
        if test_ratio > 0 and test_count == 0:
            test_count = 1
            train_count -= 1

    while train_count < 0:
        if test_count > 0:
            test_count -= 1
        elif dev_count > 0:
            dev_count -= 1
        train_count += 1

    return train_count, dev_count, test_count


def validate_ratios(train_ratio: float, dev_ratio: float, test_ratio: float) -> None:
    ratio_sum = train_ratio + dev_ratio + test_ratio
    if min(train_ratio, dev_ratio, test_ratio) < 0:
        raise ValueError("split ratios must be non-negative")
    if abs(ratio_sum - 1.0) > 1e-9:
        raise ValueError(f"split ratios must sum to 1.0, got {ratio_sum}")


def stratified_split(
    examples: list[Example],
    train_ratio: float,
    dev_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, list[Example]]:
    grouped: dict[str, list[Example]] = defaultdict(list)
    for example in examples:
        grouped[example.get("task_type", "unknown")].append(example)

    rng = random.Random(seed)
    splits = {"train": [], "dev": [], "curriculum_test": []}

    for task_type in sorted(grouped):
        task_examples = sorted(grouped[task_type], key=lambda example: example["id"])
        rng.shuffle(task_examples)

        train_count, dev_count, test_count = split_sizes(
            len(task_examples),
            train_ratio,
            dev_ratio,
            test_ratio,
        )
        train_items = task_examples[:train_count]
        dev_items = task_examples[train_count : train_count + dev_count]
        test_items = task_examples[train_count + dev_count : train_count + dev_count + test_count]

        splits["train"].extend(with_split(train_items, "train"))
        splits["dev"].extend(with_split(dev_items, "dev"))
        splits["curriculum_test"].extend(with_split(test_items, "curriculum_test"))

    for split_name in splits:
        splits[split_name] = sorted(splits[split_name], key=lambda example: example["id"])

    return splits


def with_split(examples: list[Example], split_name: str) -> list[Example]:
    split_examples = []
    for example in examples:
        split_example = dict(example)
        split_example["split"] = split_name
        split_examples.append(split_example)
    return split_examples


def counts_by_task(examples: list[Example]) -> dict[str, int]:
    return dict(sorted(Counter(example.get("task_type", "unknown") for example in examples).items()))


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite to replace split files")
    path.mkdir(parents=True, exist_ok=True)


def copy_or_write_heldout(heldout_path: Path, output_dir: Path) -> tuple[Path, Path, int]:
    heldout_data = load_json(heldout_path)
    heldout_copy = output_dir / "heldout.json"
    shutil.copyfile(heldout_path, heldout_copy)

    prompt_path = output_dir / "heldout_prompts.jsonl"
    prompt_records = [
        {
            "case_id": case["id"],
            "case_type": case.get("case_type"),
            "input": case.get("prompt", ""),
            "prompt": case.get("prompt", ""),
        }
        for case in heldout_data.get("cases", [])
    ]
    write_jsonl(prompt_path, prompt_records)
    return heldout_copy, prompt_path, len(prompt_records)


def source_manifest(curriculum_path: Path, heldout_path: Path | None) -> dict[str, Any]:
    sources: dict[str, Any] = {
        "curriculum_jsonl": str(curriculum_path),
        "curriculum_sha256": sha256_file(curriculum_path),
    }
    manifest_path = curriculum_path.with_suffix(".manifest.json")
    if manifest_path.exists():
        sources["curriculum_manifest"] = str(manifest_path)
        sources["curriculum_manifest_sha256"] = sha256_file(manifest_path)
    if heldout_path:
        sources["heldout_json"] = str(heldout_path)
        sources["heldout_sha256"] = sha256_file(heldout_path)
    return sources


def output_file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        name: {
            "path": str(path),
            "sha256": sha256_file(path),
        }
        for name, path in sorted(paths.items())
    }


def build_manifest(
    experiment_id: str,
    curriculum_path: Path,
    heldout_path: Path | None,
    seed: int,
    ratios: dict[str, float],
    splits: dict[str, list[Example]],
    output_paths: dict[str, Path],
    heldout_prompt_count: int,
) -> dict[str, Any]:
    split_counts = {
        split_name: {
            "total": len(examples),
            "task_type_counts": counts_by_task(examples),
        }
        for split_name, examples in sorted(splits.items())
    }
    return {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "split_strategy": "deterministic_stratified_by_task_type",
        "seed": seed,
        "ratios": ratios,
        "sources": source_manifest(curriculum_path, heldout_path),
        "splits": split_counts,
        "heldout_prompt_count": heldout_prompt_count,
        "outputs": output_file_manifest(output_paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("curriculum_jsonl", type=Path, help="Generated curriculum JSONL path")
    parser.add_argument("--heldout", type=Path, help="Held-out evaluation JSON to copy and convert to prompts")
    parser.add_argument("--experiment-id", default="physical_v0", help="Experiment ID")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory. Defaults to data/developmental_graph/experiments/<experiment-id>",
    )
    parser.add_argument("--seed", type=int, default=1729, help="Deterministic split seed")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--dev-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing files in the output directory")
    args = parser.parse_args()

    validate_ratios(args.train_ratio, args.dev_ratio, args.test_ratio)

    output_dir = args.output_dir or Path("data/developmental_graph/experiments") / args.experiment_id
    ensure_output_dir(output_dir, args.overwrite)

    examples = load_jsonl(args.curriculum_jsonl)
    splits = stratified_split(examples, args.train_ratio, args.dev_ratio, args.test_ratio, args.seed)

    # Stage everything first, so a failure leaves the previous split untouched.
    # The manifest goes last: no manifest means an incomplete experiment, and
    # create_developmental_dataset_variants.py refuses to read one.
    names = {"train": "train.jsonl", "dev": "dev.jsonl", "curriculum_test": "curriculum_test.jsonl"}
    manifest_path = output_dir / "manifest.json"
    staged = output_dir / f".staging-{os.getpid()}"
    try:
        for split_name, name in names.items():
            write_jsonl(staged / name, splits[split_name])
        heldout_prompt_count = 0
        if args.heldout:
            _, _, heldout_prompt_count = copy_or_write_heldout(args.heldout, staged)
            names |= {"heldout": "heldout.json", "heldout_prompts": "heldout_prompts.jsonl"}
        manifest_path.unlink(missing_ok=True)
        # Files the new split doesn't list, and datasets built from the old split, are now wrong.
        for stale in ("heldout.json", "heldout_prompts.jsonl"):
            (output_dir / stale).unlink(missing_ok=True)
        if (output_dir / "datasets").exists():
            shutil.rmtree(output_dir / "datasets")
            print(f"Removed {output_dir / 'datasets'}: built from the old split; rerun create_developmental_dataset_variants.py",
                  file=sys.stderr)
        for name in names.values():
            os.replace(staged / name, output_dir / name)
    finally:
        shutil.rmtree(staged, ignore_errors=True)
    output_paths = {key: output_dir / name for key, name in names.items()}

    ratios = {
        "train": args.train_ratio,
        "dev": args.dev_ratio,
        "curriculum_test": args.test_ratio,
    }
    manifest = build_manifest(
        args.experiment_id,
        args.curriculum_jsonl,
        args.heldout,
        args.seed,
        ratios,
        splits,
        output_paths,
        heldout_prompt_count,
    )
    atomic_write_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    output_paths["manifest"] = manifest_path

    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
