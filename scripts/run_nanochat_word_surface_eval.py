#!/usr/bin/env python3
"""Evaluate V4 word-surface nanochat checkpoints.

The evaluator uses the word_plain_text curriculum_test prompts for all models
by default. This keeps the prompt surface fair and checks whether the
relation-scaffolded training helped without giving relation lines at test time.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_RUN_DIR = Path("runs/nanochat_v4_word_surface_20260429")
DEFAULT_DATASET = Path(
    "data/developmental_graph/experiments/procedural_foundation_v4_word_surface/"
    "datasets/word_plain_text/curriculum_test.jsonl"
)
DEFAULT_OUTPUT_DIR = DEFAULT_RUN_DIR / "evaluation" / "word_plain_prompts_d4_i500"

MODEL_TAGS = {
    "word_plain_text": "v4_word_plain_text_d4_i500",
    "word_relation_scaffolded": "v4_word_relation_scaffolded_d4_i500",
    "word_plain_qa": "v5_word_plain_qa_d4_i1000",
    "word_relation_scaffolded_qa": "v5_word_relation_scaffolded_qa_d4_i1000",
}

STOP_MARKERS = re.compile(
    r"(?m)^(?:"
    r"scene:|question:|the scene is\b|the question is\b|answer this question:"
    r"|give the answer\b|known relation:|blocked relation:"
    r")(?:\s|$)",
    flags=re.IGNORECASE,
)


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            rows.append(record)
            if limit is not None and len(rows) >= limit:
                break
    if not rows:
        raise SystemExit(f"{path}: no records found")
    return rows


def normalize_value(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"^[\"'`]+|[\"'`]+$", "", value)
    value = value.rstrip(".")
    return value.strip()


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.split("<|", 1)[0]
    match = STOP_MARKERS.search(text)
    if match:
        text = text[: match.start()]
    return text.strip()


def strip_answer_intro(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^(?:the\s+)?answer\s+(?:is|:)\s+", "", text, flags=re.IGNORECASE)
    return text.strip()


def strip_reason_intro(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^(?:the\s+)?reason\s+(?:is|:)\s+", "", text, flags=re.IGNORECASE)
    return text.strip()


def split_because(text: str) -> tuple[str, str]:
    text = strip_answer_intro(text.strip())
    match = re.search(r"\s*,?\s+(?:because|since)\s+", text, flags=re.IGNORECASE)
    if not match:
        return text, ""
    return text[: match.start()].strip(" .,:;"), text[match.end() :].strip(" .,:;")


def parse_answer_reason(text: str, surface_type: str | None = None) -> tuple[str, str]:
    text = clean_text(text)
    if not text:
        return "", ""

    answer = ""
    reason = ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        lower = line.lower()
        if lower.startswith("answer:") and not answer:
            answer, inline_reason = split_because(line.split(":", 1)[1])
            reason = reason or inline_reason
        elif lower.startswith("reason:") and not reason:
            reason = strip_reason_intro(line.split(":", 1)[1])
        elif lower.startswith("the reason is:") and not reason:
            reason = strip_reason_intro(line.split(":", 1)[1])

    if not answer and lines:
        answer, inline_reason = split_because(lines[0])
        reason = reason or inline_reason

    if not reason and len(lines) >= 2:
        second = lines[1]
        if second.lower().startswith(("reason:", "the reason is:")):
            reason = strip_reason_intro(second.split(":", 1)[1])
        elif not second.lower().startswith(("known relation:", "blocked relation:")):
            reason = strip_reason_intro(second)

    if not reason and surface_type == "event_continuation":
        reason = answer

    return answer.strip(), reason.strip()


def import_nanochat(nanochat_dir: Path):
    sys.path.insert(0, str(nanochat_dir))
    try:
        import torch
        from nanochat.checkpoint_manager import load_model
        from nanochat.common import compute_init
        from nanochat.engine import Engine
    except ImportError as exc:
        raise SystemExit(f"Could not import nanochat from {nanochat_dir}") from exc
    return torch, compute_init, load_model, Engine


def evaluate_model(
    *,
    model_name: str,
    model_tag: str,
    run_dir: Path,
    rows: list[dict[str, Any]],
    torch: Any,
    load_model: Any,
    Engine: Any,
    device: Any,
    max_tokens: int,
    temperature: float,
    seed: int,
    progress_every: int,
    prompt_suffix: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base_dir = run_dir / model_name
    if not base_dir.exists():
        raise SystemExit(f"Missing model base dir: {base_dir}")

    os.environ["NANOCHAT_BASE_DIR"] = str(base_dir)
    model, tokenizer, meta = load_model("base", device, phase="eval", model_tag=model_tag, step=None)
    engine = Engine(model, tokenizer)
    bos = tokenizer.get_bos_token_id()

    predictions: list[dict[str, Any]] = []
    started = time.time()
    for index, row in enumerate(rows, start=1):
        prompt = str(row.get("input") or "")
        generation_prompt = f"{prompt}{prompt_suffix}"
        target = str(row.get("target") or "")
        surface_type = str(
            row.get("surface_type")
            or row.get("prompt_type")
            or row.get("metadata", {}).get("surface_type")
            or row.get("metadata", {}).get("prompt_type")
            or ""
        )
        prompt_tokens = tokenizer.encode(generation_prompt, prepend=bos)
        outputs, _masks = engine.generate_batch(
            prompt_tokens,
            num_samples=1,
            max_tokens=max_tokens,
            temperature=temperature,
            seed=seed,
        )
        generated_tokens = outputs[0][len(prompt_tokens) :]
        raw_generated = tokenizer.decode(generated_tokens)

        expected_answer, expected_reason = parse_answer_reason(target, surface_type)
        generated_answer, generated_reason = parse_answer_reason(raw_generated, surface_type)
        answer_exact = normalize_value(generated_answer) == normalize_value(expected_answer)
        reason_exact = bool(normalize_value(expected_reason)) and (
            normalize_value(generated_reason) == normalize_value(expected_reason)
        )
        prediction = {
            "model": model_name,
            "source_example_id": row.get("source_example_id") or row.get("id"),
            "task_type": row.get("task_type"),
            "surface_type": surface_type,
            "prompt": prompt,
            "generation_prompt": generation_prompt,
            "target": target,
            "raw_generated": raw_generated,
            "expected_answer": expected_answer,
            "generated_answer": generated_answer,
            "answer_exact": answer_exact,
            "expected_reason": expected_reason,
            "generated_reason": generated_reason,
            "reason_exact": reason_exact,
        }
        predictions.append(prediction)
        if progress_every and index % progress_every == 0:
            elapsed = time.time() - started
            print(f"{model_name}: {index}/{len(rows)} examples ({elapsed:.1f}s elapsed)", flush=True)

    del engine, model, tokenizer
    gc.collect()
    if hasattr(torch, "mps") and device.type == "mps":
        torch.mps.empty_cache()
    if hasattr(torch, "cuda") and device.type == "cuda":
        torch.cuda.empty_cache()

    return predictions, summarize_predictions(model_name, model_tag, meta, predictions)


def summarize_predictions(
    model_name: str,
    model_tag: str,
    meta: dict[str, Any],
    predictions: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(predictions)
    answer_correct = sum(1 for row in predictions if row["answer_exact"])
    reason_correct = sum(1 for row in predictions if row["reason_exact"])

    by_surface: dict[str, dict[str, Any]] = {}
    grouped_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        grouped_surface[str(row.get("surface_type") or "unknown")].append(row)
    for surface_type, rows in sorted(grouped_surface.items()):
        by_surface[surface_type] = score_group(rows)

    by_task: dict[str, dict[str, Any]] = {}
    grouped_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        grouped_task[str(row.get("task_type") or "unknown")].append(row)
    for task_type, rows in sorted(grouped_task.items()):
        by_task[task_type] = score_group(rows)

    answer_counts = Counter(normalize_value(row["generated_answer"]) or "<empty>" for row in predictions)
    return {
        "model": model_name,
        "model_tag": model_tag,
        "checkpoint_meta": {
            "step": meta.get("step"),
            "model_config": meta.get("model_config"),
        },
        "count": total,
        "answer_exact": answer_correct,
        "answer_accuracy": answer_correct / total,
        "reason_exact": reason_correct,
        "reason_accuracy": reason_correct / total,
        "by_surface_type": by_surface,
        "by_task_type": by_task,
        "top_generated_answers": answer_counts.most_common(20),
    }


def score_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    answer_correct = sum(1 for row in rows if row["answer_exact"])
    reason_correct = sum(1 for row in rows if row["reason_exact"])
    return {
        "count": total,
        "answer_exact": answer_correct,
        "answer_accuracy": answer_correct / total,
        "reason_exact": reason_correct,
        "reason_accuracy": reason_correct / total,
    }


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# nanochat word-surface held-out evaluation",
        "",
        f"- Dataset: `{summary['dataset']}`",
        f"- Examples: {summary['count']}",
        f"- Max generated tokens: {summary['max_tokens']}",
        f"- Temperature: {summary['temperature']}",
        "",
        "## Overall",
        "",
        "| Model | Answer exact | Reason exact |",
        "| --- | ---: | ---: |",
    ]
    for model_name, model_summary in summary["models"].items():
        lines.append(
            "| {model} | {ans:.1%} ({ans_n}/{n}) | {reason:.1%} ({reason_n}/{n}) |".format(
                model=model_name,
                ans=model_summary["answer_accuracy"],
                ans_n=model_summary["answer_exact"],
                reason=model_summary["reason_accuracy"],
                reason_n=model_summary["reason_exact"],
                n=model_summary["count"],
            )
        )

    lines.extend(["", "## By Surface Type", ""])
    for model_name, model_summary in summary["models"].items():
        lines.extend([f"### {model_name}", "", "| Surface | Count | Answer exact | Reason exact |", "| --- | ---: | ---: | ---: |"])
        for surface_type, surface_summary in model_summary["by_surface_type"].items():
            lines.append(
                "| {surface} | {count} | {ans:.1%} | {reason:.1%} |".format(
                    surface=surface_type,
                    count=surface_summary["count"],
                    ans=surface_summary["answer_accuracy"],
                    reason=surface_summary["reason_accuracy"],
                )
            )
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--nanochat-dir", type=Path, default=Path("/tmp/nanochat-read"))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default="mps")
    parser.add_argument("--models", nargs="+", default=list(MODEL_TAGS))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--surface-type", default=None, help="Optional surface type filter.")
    parser.add_argument("--max-tokens", type=int, default=48)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--progress-every", type=int, default=500)
    parser.add_argument(
        "--model-tag",
        action="append",
        default=[],
        metavar="MODEL=TAG",
        help="Override a model checkpoint tag. Can be repeated.",
    )
    parser.add_argument(
        "--prompt-suffix",
        default="\n\n",
        help="Suffix appended to each input before generation. Default matches input_target training shards.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_tags = dict(MODEL_TAGS)
    for override in args.model_tag:
        if "=" not in override:
            raise SystemExit(f"--model-tag must be MODEL=TAG, got: {override}")
        model_name, model_tag = override.split("=", 1)
        model_tags[model_name] = model_tag

    unknown_models = [model for model in args.models if model not in model_tags]
    if unknown_models:
        raise SystemExit(f"Unknown models: {', '.join(unknown_models)}")

    rows = read_jsonl(args.dataset, limit=args.limit)
    if args.surface_type:
        rows = [row for row in rows if row.get("surface_type") == args.surface_type]
        if args.limit is not None:
            rows = rows[: args.limit]
        if not rows:
            raise SystemExit(f"No rows left after --surface-type {args.surface_type}")

    predictions_dir = args.output_dir / "predictions"
    predictions_dir.mkdir(parents=True, exist_ok=True)

    torch, compute_init, load_model, Engine = import_nanochat(args.nanochat_dir)
    _ddp, _rank, _local_rank, _world_size, device = compute_init(args.device)

    all_summaries: dict[str, Any] = {}
    started = time.time()
    for model_name in args.models:
        model_tag = model_tags[model_name]
        print(f"Evaluating {model_name} ({model_tag}) on {len(rows)} examples", flush=True)
        predictions, model_summary = evaluate_model(
            model_name=model_name,
            model_tag=model_tag,
            run_dir=args.run_dir,
            rows=rows,
            torch=torch,
            load_model=load_model,
            Engine=Engine,
            device=device,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            seed=args.seed,
            progress_every=args.progress_every,
            prompt_suffix=args.prompt_suffix,
        )
        write_jsonl(predictions, predictions_dir / f"{model_name}.jsonl")
        all_summaries[model_name] = model_summary

    summary = {
        "dataset": str(args.dataset),
        "surface_type_filter": args.surface_type,
        "count": len(rows),
        "limit": args.limit,
        "run_dir": str(args.run_dir),
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "seed": args.seed,
        "prompt_suffix": args.prompt_suffix,
        "models": all_summaries,
        "elapsed_seconds": time.time() - started,
    }
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(summary, args.output_dir / "summary.md")
    print(f"Wrote {summary_path}")
    print(f"Wrote {args.output_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
