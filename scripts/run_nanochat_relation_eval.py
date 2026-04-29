#!/usr/bin/env python3
"""Evaluate nanochat checkpoints on held-out procedural relation questions.

This is a generation-based evaluator. It prompts each model with the same
plain held-out question, asks for a short answer, and scores the generated
answer/fact lines against the expected target.
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


DEFAULT_RUN_DIR = Path("runs/nanochat_core4_20260429")
DEFAULT_DATASET = Path(
    "data/developmental_graph/experiments/procedural_foundation_v3/"
    "datasets/procedural_plain_text/curriculum_test.jsonl"
)

MODEL_TAGS = {
    "tinystories_plain_text": "core4_tinystories_plain_text_d4_i500",
    "procedural_plain_text": "core4_procedural_plain_text_d4_i500",
    "procedural_relation_scaffolded": "core4_procedural_relation_scaffolded_d4_i500",
    "procedural_relation_first_then_text": "core4_procedural_relation_first_then_text_d4_i500",
}

DEFAULT_OUTPUT_DIRS = {
    "structured": "procedural_v3_plain_prompt_d4_i500",
    "natural_a": "procedural_v3_natural_a_prompt_d4_i500",
    "natural_answer": "procedural_v3_natural_answer_prompt_d4_i500",
}

STOP_MARKERS = re.compile(
    r"(?m)^(?:s:|q:|r:|n:|scene:|question:|TASK_TYPE:|VARIANT:|QUESTION:|EXAMPLE_ID:)(?:\s|$)",
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
            if not isinstance(record, dict):
                raise SystemExit(f"{path}:{line_number}: expected JSON object")
            rows.append(record)
            if limit is not None and len(rows) >= limit:
                break
    if not rows:
        raise SystemExit(f"{path}: no records found")
    return rows


def expected_field(target: str, prefix: str) -> str:
    marker = f"{prefix}:"
    for line in target.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(marker):
            return stripped[len(marker) :].strip()
    return ""


def sentence_case(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    return text[0].upper() + text[1:]


def prompt_parts(input_text: str) -> tuple[str, str]:
    scenario = ""
    question = ""
    for line in input_text.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith("s:"):
            scenario = stripped[2:].strip()
        elif lower.startswith("q:"):
            question = stripped[2:].strip()
    return scenario, question


def render_prompt(row: dict[str, Any], prompt_style: str) -> str:
    input_text = str(row.get("input") or "")
    if prompt_style == "structured":
        return input_text

    scenario, question = prompt_parts(input_text)
    scenario = sentence_case(scenario)
    question = sentence_case(question)
    if prompt_style == "natural_a":
        return f"{scenario}\n{question}\na:"
    if prompt_style == "natural_answer":
        return f"Scene: {scenario}\nQuestion: {question}\nAnswer:"
    raise ValueError(f"unknown prompt style: {prompt_style}")


def normalize_value(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"^[\"'`]+|[\"'`]+$", "", value)
    value = value.rstrip(".")
    return value.strip()


def clean_generated_text(text: str) -> str:
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


def split_answer_and_reason(text: str) -> tuple[str, str]:
    text = strip_answer_intro(text)
    match = re.search(r"\s+(?:because|since)\s+", text, flags=re.IGNORECASE)
    if match:
        return text[: match.start()].strip(" .,:;"), text[match.end() :].strip(" .,:;")
    return text.strip(), ""


def extract_generated_fields(text: str) -> tuple[str, str]:
    """Extract generated answer and fact values from a decoded continuation.

    The prompt ends with ``a:``, so a good continuation can be either
    ``yes\nf: ...`` or ``a: yes\nf: ...``. This parser accepts both.
    """

    text = clean_generated_text(text)
    if not text:
        return "", ""

    answer = ""
    fact = ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    answer_prefixes = ("a:", "answer:")
    fact_prefixes = ("f:", "fact:", "reason:")

    lines_for_label_scan = lines
    if lines:
        first_lower = lines[0].lower()
        if not first_lower.startswith(answer_prefixes + fact_prefixes):
            # If the model starts by drifting into prose or a new question, do
            # not skip ahead to a later self-generated a: line.
            answer, inline_reason = split_answer_and_reason(lines[0])
            fact = fact or inline_reason
            lines_for_label_scan = lines[1:]

    for line in lines_for_label_scan:
        lower = line.lower()
        if lower.startswith(answer_prefixes) and not answer:
            answer = line.split(":", 1)[1].strip()
            if " f:" in answer.lower():
                before, after = re.split(r"\bf:\s*", answer, maxsplit=1, flags=re.IGNORECASE)
                answer = before.strip()
                fact = fact or after.strip()
            answer, inline_reason = split_answer_and_reason(answer)
            fact = fact or inline_reason
        elif lower.startswith(fact_prefixes) and not fact:
            fact = line.split(":", 1)[1].strip()

    if not answer and lines:
        first = lines[0]
        if " f:" in first.lower():
            before, after = re.split(r"\bf:\s*", first, maxsplit=1, flags=re.IGNORECASE)
            answer = before.strip()
            fact = fact or after.strip()
        else:
            answer, inline_reason = split_answer_and_reason(first)
            fact = fact or inline_reason

    if not fact:
        match = re.search(r"(?im)^f:\s*(.+)$", text)
        if match:
            fact = match.group(1).strip()

    # If the model continued with another field after a fact, keep only the fact.
    if fact:
        fact = re.split(r"\s+(?:a:|r:|n:|s:|q:)\s*", fact, maxsplit=1, flags=re.IGNORECASE)[0]

    return answer.strip(), fact.strip()


def import_nanochat(nanochat_dir: Path):
    sys.path.insert(0, str(nanochat_dir))
    try:
        import torch
        from nanochat.checkpoint_manager import load_model
        from nanochat.common import compute_init
        from nanochat.engine import Engine
    except ImportError as exc:
        raise SystemExit(
            f"Could not import nanochat from {nanochat_dir}. "
            "Run with the nanochat virtualenv Python or pass --nanochat-dir."
        ) from exc
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
    prompt_style: str,
    max_tokens: int,
    temperature: float,
    seed: int,
    progress_every: int,
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
        prompt = render_prompt(row, prompt_style)
        target = str(row.get("target") or "")
        prompt_tokens = tokenizer.encode(prompt, prepend=bos)
        outputs, _masks = engine.generate_batch(
            prompt_tokens,
            num_samples=1,
            max_tokens=max_tokens,
            temperature=temperature,
            seed=seed,
        )
        full_tokens = outputs[0]
        generated_tokens = full_tokens[len(prompt_tokens) :]
        raw_generated = tokenizer.decode(generated_tokens)

        expected_answer = expected_field(target, "a")
        expected_fact = expected_field(target, "f")
        generated_answer, generated_fact = extract_generated_fields(raw_generated)

        normalized_expected_answer = normalize_value(expected_answer)
        normalized_generated_answer = normalize_value(generated_answer)
        normalized_expected_fact = normalize_value(expected_fact)
        normalized_generated_fact = normalize_value(generated_fact)

        prediction = {
            "model": model_name,
            "source_example_id": row.get("source_example_id") or row.get("id"),
            "task_type": row.get("task_type") or row.get("metadata", {}).get("rule_family"),
            "prompt": prompt,
            "target": target,
            "raw_generated": raw_generated,
            "expected_answer": expected_answer,
            "generated_answer": generated_answer,
            "answer_exact": normalized_generated_answer == normalized_expected_answer,
            "expected_fact": expected_fact,
            "generated_fact": generated_fact,
            "fact_exact": bool(normalized_expected_fact)
            and normalized_generated_fact == normalized_expected_fact,
        }
        predictions.append(prediction)

        if progress_every and index % progress_every == 0:
            elapsed = time.time() - started
            print(
                f"{model_name}: {index}/{len(rows)} examples "
                f"({elapsed:.1f}s elapsed)",
                flush=True,
            )

    del engine, model, tokenizer
    gc.collect()
    if hasattr(torch, "mps") and device.type == "mps":
        torch.mps.empty_cache()
    if hasattr(torch, "cuda") and device.type == "cuda":
        torch.cuda.empty_cache()

    summary = summarize_predictions(model_name, model_tag, meta, predictions)
    return predictions, summary


def summarize_predictions(
    model_name: str,
    model_tag: str,
    meta: dict[str, Any],
    predictions: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(predictions)
    answer_correct = sum(1 for row in predictions if row["answer_exact"])
    fact_correct = sum(1 for row in predictions if row["fact_exact"])

    by_task: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        grouped[str(row.get("task_type") or "unknown")].append(row)
    for task_type, task_rows in sorted(grouped.items()):
        task_total = len(task_rows)
        by_task[task_type] = {
            "count": task_total,
            "answer_exact": sum(1 for row in task_rows if row["answer_exact"]),
            "answer_accuracy": sum(1 for row in task_rows if row["answer_exact"]) / task_total,
            "fact_exact": sum(1 for row in task_rows if row["fact_exact"]),
            "fact_accuracy": sum(1 for row in task_rows if row["fact_exact"]) / task_total,
        }

    generated_answer_counts = Counter(
        normalize_value(row["generated_answer"]) or "<empty>" for row in predictions
    )

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
        "fact_exact": fact_correct,
        "fact_accuracy": fact_correct / total,
        "by_task_type": by_task,
        "top_generated_answers": generated_answer_counts.most_common(20),
    }


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    models = summary["models"]
    lines = [
        f"# nanochat core4 held-out relation evaluation: {summary['prompt_mode']}",
        "",
        f"- Dataset: `{summary['dataset']}`",
        f"- Prompt mode: `{summary['prompt_mode']}`",
        f"- Examples: {summary['count']}",
        f"- Max generated tokens: {summary['max_tokens']}",
        f"- Temperature: {summary['temperature']}",
        "",
        "## Overall",
        "",
        "| Model | Answer exact | Fact exact |",
        "| --- | ---: | ---: |",
    ]
    for model_name, model_summary in models.items():
        lines.append(
            "| {model} | {ans:.1%} ({ans_n}/{n}) | {fact:.1%} ({fact_n}/{n}) |".format(
                model=model_name,
                ans=model_summary["answer_accuracy"],
                ans_n=model_summary["answer_exact"],
                fact=model_summary["fact_accuracy"],
                fact_n=model_summary["fact_exact"],
                n=model_summary["count"],
            )
        )

    lines.extend(["", "## By Task Type", ""])
    for model_name, model_summary in models.items():
        lines.extend([f"### {model_name}", "", "| Task | Count | Answer exact | Fact exact |", "| --- | ---: | ---: | ---: |"])
        for task_type, task_summary in model_summary["by_task_type"].items():
            lines.append(
                "| {task} | {count} | {ans:.1%} | {fact:.1%} |".format(
                    task=task_type,
                    count=task_summary["count"],
                    ans=task_summary["answer_accuracy"],
                    fact=task_summary["fact_accuracy"],
                )
            )
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run generation-based held-out relation evaluation for nanochat checkpoints."
    )
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--nanochat-dir", type=Path, default=Path("/tmp/nanochat-read"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Defaults to RUN_DIR/evaluation/procedural_v3_plain_prompt_d4_i500.",
    )
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default="mps")
    parser.add_argument("--models", nargs="+", default=list(MODEL_TAGS))
    parser.add_argument(
        "--prompt-style",
        choices=["structured", "natural_a", "natural_answer"],
        default="structured",
        help=(
            "structured uses the original s:/q:/a: prompt; natural_a rewrites "
            "s:/q: into prose but keeps a: as the answer cue; natural_answer "
            "uses Scene/Question/Answer labels."
        ),
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-tokens", type=int, default=32)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--progress-every", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    unknown_models = [model for model in args.models if model not in MODEL_TAGS]
    if unknown_models:
        raise SystemExit(f"Unknown models: {', '.join(unknown_models)}")

    rows = read_jsonl(args.dataset, limit=args.limit)
    output_dir = args.output_dir or (
        args.run_dir / "evaluation" / DEFAULT_OUTPUT_DIRS[args.prompt_style]
    )
    predictions_dir = output_dir / "predictions"
    predictions_dir.mkdir(parents=True, exist_ok=True)

    torch, compute_init, load_model, Engine = import_nanochat(args.nanochat_dir)
    _ddp, _rank, _local_rank, _world_size, device = compute_init(args.device)

    all_summaries: dict[str, Any] = {}
    started = time.time()
    for model_name in args.models:
        model_tag = MODEL_TAGS[model_name]
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
            prompt_style=args.prompt_style,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            seed=args.seed,
            progress_every=args.progress_every,
        )
        write_jsonl(predictions, predictions_dir / f"{model_name}.jsonl")
        all_summaries[model_name] = model_summary

    summary = {
        "dataset": str(args.dataset),
        "prompt_mode": args.prompt_style,
        "count": len(rows),
        "limit": args.limit,
        "run_dir": str(args.run_dir),
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "seed": args.seed,
        "models": all_summaries,
        "elapsed_seconds": time.time() - started,
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(summary, output_dir / "summary.md")

    print(f"Wrote {summary_path}")
    print(f"Wrote {output_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
