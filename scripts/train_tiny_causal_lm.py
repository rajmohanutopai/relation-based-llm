#!/usr/bin/env python3
"""Train a tiny causal LM on one physical_v0 dataset variant.

The script is intentionally small and conventional. It uses Hugging Face
Transformers only at runtime, so `--dry-run` can validate config and data
formatting without training dependencies installed.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


SPLITS = ("train", "dev", "curriculum_test")


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


def dataset_paths(config: dict[str, Any], variant: str) -> dict[str, Path]:
    manifest_path = Path(config["dataset_manifest"])
    manifest = load_json(manifest_path)
    variants = manifest.get("variants", {})
    if variant not in variants:
        raise ValueError(f"unknown variant {variant!r}; expected one of {sorted(variants)}")

    output_dir = Path(manifest["output_dir"])
    return {split: output_dir / variant / f"{split}.jsonl" for split in SPLITS}


def load_variant_data(config: dict[str, Any], variant: str, overfit_limit: int | None) -> dict[str, list[dict[str, Any]]]:
    paths = dataset_paths(config, variant)
    data = {split: load_jsonl(path) for split, path in paths.items()}
    if overfit_limit is not None:
        if overfit_limit <= 0:
            raise ValueError("--overfit-limit must be positive")
        data["train"] = data["train"][:overfit_limit]
        data["dev"] = data["train"]
        data["curriculum_test"] = data["train"]
    return data


def format_prompt(config: dict[str, Any], row: dict[str, Any]) -> str:
    template = config.get("format", {}).get("prompt_template", "### Input:\n{input}\n\n### Response:\n")
    return template.format(input=row["input"], target=row["target"])


def format_target(config: dict[str, Any], row: dict[str, Any]) -> str:
    template = config.get("format", {}).get("target_template", "{target}")
    return template.format(input=row["input"], target=row["target"])


def dry_run(config: dict[str, Any], variant: str, overfit_limit: int | None) -> None:
    data = load_variant_data(config, variant, overfit_limit)
    summary = {
        "experiment_id": config["experiment_id"],
        "variant": variant,
        "baseline_model": config["baseline_model"]["name"],
        "counts": {split: len(rows) for split, rows in data.items()},
        "training": config["training"],
    }
    sample = data["train"][0]
    summary["sample"] = {
        "source_example_id": sample["source_example_id"],
        "task_type": sample["task_type"],
        "prompt": format_prompt(config, sample),
        "target": format_target(config, sample),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


def import_training_deps() -> tuple[Any, Any, Any, Any, Any]:
    try:
        import torch
        from torch.utils.data import Dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Training dependencies are missing. Install them with:\n"
            "  python3 -m pip install -r requirements-training.txt"
        ) from exc
    return torch, Dataset, AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments


def make_dataset_class(dataset_base: Any) -> type:
    class SFTDataset(dataset_base):  # type: ignore[misc, valid-type]
        def __init__(self, rows: list[dict[str, Any]], tokenizer: Any, config: dict[str, Any]):
            self.rows = rows
            self.tokenizer = tokenizer
            self.config = config
            self.max_seq_length = int(config["training"]["max_seq_length"])

        def __len__(self) -> int:
            return len(self.rows)

        def __getitem__(self, idx: int) -> dict[str, list[int]]:
            row = self.rows[idx]
            prompt = format_prompt(self.config, row)
            target = format_target(self.config, row)
            eos = self.tokenizer.eos_token or ""

            prompt_ids = self.tokenizer(prompt, add_special_tokens=False)["input_ids"]
            target_ids = self.tokenizer(target + eos, add_special_tokens=False)["input_ids"]

            if len(target_ids) >= self.max_seq_length:
                prompt_ids = []
                target_ids = target_ids[: self.max_seq_length]
            else:
                prompt_ids = prompt_ids[: self.max_seq_length - len(target_ids)]

            input_ids = prompt_ids + target_ids
            labels = [-100] * len(prompt_ids) + target_ids
            attention_mask = [1] * len(input_ids)
            return {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels,
            }

    return SFTDataset


def make_collator(tokenizer: Any) -> Any:
    pad_token_id = tokenizer.pad_token_id

    def collate(features: list[dict[str, list[int]]]) -> dict[str, Any]:
        import torch

        max_len = max(len(feature["input_ids"]) for feature in features)
        batch = {"input_ids": [], "attention_mask": [], "labels": []}
        for feature in features:
            pad_len = max_len - len(feature["input_ids"])
            batch["input_ids"].append(feature["input_ids"] + [pad_token_id] * pad_len)
            batch["attention_mask"].append(feature["attention_mask"] + [0] * pad_len)
            batch["labels"].append(feature["labels"] + [-100] * pad_len)
        return {key: torch.tensor(value, dtype=torch.long) for key, value in batch.items()}

    return collate


def train(config: dict[str, Any], variant: str, output_dir: Path | None, overfit_limit: int | None, max_steps: int | None) -> None:
    torch, Dataset, AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments = import_training_deps()

    seed = int(config["training"]["seed"])
    random.seed(seed)
    torch.manual_seed(seed)

    data = load_variant_data(config, variant, overfit_limit)
    model_name = config["baseline_model"]["name"]
    run_output_dir = output_dir or Path(config["output_root"]) / variant

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.config.use_cache = False

    dataset_class = make_dataset_class(Dataset)
    train_dataset = dataset_class(data["train"], tokenizer, config)
    eval_dataset = dataset_class(data["dev"], tokenizer, config)

    training_config = config["training"]
    kwargs = {
        "output_dir": str(run_output_dir),
        "num_train_epochs": float(training_config["num_train_epochs"]),
        "learning_rate": float(training_config["learning_rate"]),
        "per_device_train_batch_size": int(training_config["per_device_train_batch_size"]),
        "per_device_eval_batch_size": int(training_config["per_device_eval_batch_size"]),
        "gradient_accumulation_steps": int(training_config["gradient_accumulation_steps"]),
        "warmup_ratio": float(training_config["warmup_ratio"]),
        "weight_decay": float(training_config["weight_decay"]),
        "logging_steps": int(training_config["logging_steps"]),
        "save_total_limit": int(training_config["save_total_limit"]),
        "save_strategy": "epoch",
        "report_to": [],
        "seed": seed,
        "fp16": False,
        "bf16": False,
        "do_train": True,
        "do_eval": True,
        "remove_unused_columns": False,
    }
    if max_steps is not None:
        kwargs["max_steps"] = max_steps
    training_args = TrainingArguments(eval_strategy="epoch", **kwargs)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=make_collator(tokenizer),
    )
    trainer.train()
    trainer.save_model(str(run_output_dir / "final"))
    tokenizer.save_pretrained(str(run_output_dir / "final"))

    run_manifest = {
        "experiment_id": config["experiment_id"],
        "variant": variant,
        "baseline_model": model_name,
        "output_dir": str(run_output_dir),
        "counts": {split: len(rows) for split, rows in data.items()},
        "overfit_limit": overfit_limit,
        "max_steps": max_steps,
        "training": training_config,
    }
    write_json(run_output_dir / "run_manifest.json", run_manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Training config JSON")
    parser.add_argument("--variant", required=True, help="Dataset variant name from the dataset manifest")
    parser.add_argument("--output-dir", type=Path, help="Override run output directory")
    parser.add_argument("--overfit-limit", type=int, help="Train/dev/test on the first N training examples")
    parser.add_argument("--max-steps", type=int, help="Override max training steps")
    parser.add_argument("--dry-run", action="store_true", help="Validate config/data and print one formatted sample")
    args = parser.parse_args()

    config = load_json(args.config)
    if args.dry_run:
        dry_run(config, args.variant, args.overfit_limit)
    else:
        train(config, args.variant, args.output_dir, args.overfit_limit, args.max_steps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
