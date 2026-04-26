#!/usr/bin/env python3
"""Generate held-out answers from a trained causal LM checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")


def import_generation_deps() -> tuple[Any, Any, Any]:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Generation dependencies are missing. Install them with:\n"
            "  python3 -m pip install -r requirements-training.txt"
        ) from exc
    return torch, AutoModelForCausalLM, AutoTokenizer


def choose_device(torch: Any, requested: str | None) -> str:
    if requested:
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def prompt_input_for_style(row: dict[str, Any], prompt_style: str) -> str:
    prompt_input = row.get("input") or row.get("prompt")
    if not isinstance(prompt_input, str) or not prompt_input:
        raise ValueError(f"held-out row missing input/prompt: {row!r}")
    if prompt_style == "raw":
        return prompt_input
    if prompt_style == "answer":
        return (
            "Answer this physical question and name the relation families used.\n"
            f"QUESTION: {prompt_input}\n"
            "ANSWER:"
        )
    if prompt_style == "answer_with_relations":
        return (
            "Answer this physical question and name the relation families used.\n"
            f"QUESTION: {prompt_input}\n"
            "ANSWER_WITH_RELATIONS:"
        )
    if prompt_style == "relation_families":
        return (
            "Which relation family IDs are needed for this physical situation?\n"
            f"QUESTION: {prompt_input}\n"
            "RELATION_FAMILY_IDS:"
        )
    if prompt_style == "graph_anchors":
        return (
            "Identify the graph anchors needed to answer this physical question.\n"
            f"QUESTION: {prompt_input}\n"
            "GRAPH_ANCHORS:"
        )
    raise ValueError(f"unknown prompt style: {prompt_style}")


def format_prompt(config: dict[str, Any], prompt_input: str) -> str:
    template = config.get("format", {}).get("prompt_template", "### Input:\n{input}\n\n### Response:\n")
    return template.format(input=prompt_input, target="")


def clean_answer(text: str) -> str:
    text = text.strip()
    for marker in ("\n### Input:", "\n### Response:", "<|endoftext|>"):
        if marker in text:
            text = text.split(marker, 1)[0].strip()
    return text


def generate_outputs(
    config: dict[str, Any],
    model_dir: Path,
    prompts_path: Path,
    output_path: Path,
    variant: str,
    max_new_tokens: int,
    limit: int | None,
    device_override: str | None,
    prompt_style: str,
) -> None:
    torch, AutoModelForCausalLM, AutoTokenizer = import_generation_deps()
    device = choose_device(torch, device_override)
    prompts = load_jsonl(prompts_path)
    if limit is not None:
        if limit <= 0:
            raise ValueError("--limit must be positive")
        prompts = prompts[:limit]

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_dir)
    model.to(device)
    model.eval()

    rows: list[dict[str, Any]] = []
    for row in prompts:
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"held-out row missing case_id: {row!r}")

        prompt_input = prompt_input_for_style(row, prompt_style)
        prompt = format_prompt(config, prompt_input)
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        input_length = int(inputs["input_ids"].shape[1])

        with torch.no_grad():
            generated = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        answer_ids = generated[0][input_length:]
        answer = clean_answer(tokenizer.decode(answer_ids, skip_special_tokens=True))
        rows.append(
            {
                "case_id": case_id,
                "case_type": row.get("case_type"),
                "variant": variant,
                "model_dir": str(model_dir),
                "prompt": prompt_input,
                "prompt_style": prompt_style,
                "answer": answer,
            }
        )

    write_jsonl(output_path, rows)
    print(json.dumps({"output": str(output_path), "rows": len(rows), "device": device}, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Training config JSON")
    parser.add_argument("--model-dir", type=Path, required=True, help="Trained checkpoint directory")
    parser.add_argument("--prompts", type=Path, required=True, help="Held-out prompt JSONL")
    parser.add_argument("--output", type=Path, required=True, help="Generated output JSONL")
    parser.add_argument("--variant", required=True, help="Dataset variant label for metadata")
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--limit", type=int, help="Only generate the first N prompts")
    parser.add_argument("--device", help="Override device, e.g. cpu, mps, cuda")
    parser.add_argument(
        "--prompt-style",
        choices=("raw", "answer", "answer_with_relations", "relation_families", "graph_anchors"),
        default="raw",
        help="How to wrap each held-out prompt before applying the training prompt template",
    )
    args = parser.parse_args()

    config = load_json(args.config)
    generate_outputs(
        config=config,
        model_dir=args.model_dir,
        prompts_path=args.prompts,
        output_path=args.output,
        variant=args.variant,
        max_new_tokens=args.max_new_tokens,
        limit=args.limit,
        device_override=args.device,
        prompt_style=args.prompt_style,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
