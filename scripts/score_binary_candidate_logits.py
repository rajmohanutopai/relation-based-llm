#!/usr/bin/env python3
"""Score binary held-out candidates by YES/NO target log probabilities."""

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


def import_deps() -> tuple[Any, Any, Any]:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Scoring dependencies are missing. Install them with:\n"
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


def format_prompt(config: dict[str, Any], prompt_input: str) -> str:
    template = config.get("format", {}).get("prompt_template", "### Input:\n{input}\n\n### Response:\n")
    return template.format(input=prompt_input, target="")


def target_logprob(torch: Any, model: Any, tokenizer: Any, device: str, prompt: str, target: str) -> float:
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    target_ids = tokenizer(target, add_special_tokens=False)["input_ids"]
    input_ids = prompt_ids + target_ids
    if len(input_ids) < 2:
        return float("-inf")

    tensor = torch.tensor([input_ids], dtype=torch.long, device=device)
    with torch.no_grad():
        logits = model(tensor[:, :-1]).logits[0]
        log_probs = torch.nn.functional.log_softmax(logits, dim=-1)

    total = 0.0
    first_target_pos = len(prompt_ids)
    for token_pos in range(first_target_pos, len(input_ids)):
        previous_pos = token_pos - 1
        token_id = input_ids[token_pos]
        total += float(log_probs[previous_pos, token_id].detach().cpu())
    return total


def score(
    config: dict[str, Any],
    model_dir: Path,
    prompts_path: Path,
    output_path: Path,
    variant: str,
    limit: int | None,
    device_override: str | None,
) -> None:
    torch, AutoModelForCausalLM, AutoTokenizer = import_deps()
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
    for index, row in enumerate(prompts, start=1):
        prompt_id = row.get("case_id")
        prompt_input = row.get("input") or row.get("prompt")
        if not isinstance(prompt_id, str) or not prompt_id:
            raise ValueError(f"prompt row missing case_id: {row!r}")
        if not isinstance(prompt_input, str) or not prompt_input:
            raise ValueError(f"prompt row missing input/prompt: {row!r}")

        prompt = format_prompt(config, prompt_input)
        yes_logprob = target_logprob(torch, model, tokenizer, device, prompt, "ANSWER: YES")
        no_logprob = target_logprob(torch, model, tokenizer, device, prompt, "ANSWER: NO")
        predicted_yes = yes_logprob > no_logprob
        rows.append(
            {
                "case_id": prompt_id,
                "source_case_id": row.get("source_case_id"),
                "case_type": row.get("case_type"),
                "candidate_type": row.get("candidate_type"),
                "candidate_option": row.get("candidate_option"),
                "variant": variant,
                "model_dir": str(model_dir),
                "answer": f"ANSWER: {'YES' if predicted_yes else 'NO'}",
                "predicted": predicted_yes,
                "yes_logprob": yes_logprob,
                "no_logprob": no_logprob,
                "yes_margin": yes_logprob - no_logprob,
            }
        )
        if index % 100 == 0:
            print(json.dumps({"scored": index, "total": len(prompts)}, sort_keys=True))

    write_jsonl(output_path, rows)
    print(json.dumps({"output": str(output_path), "rows": len(rows), "device": device}, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--device")
    args = parser.parse_args()

    score(
        config=load_json(args.config),
        model_dir=args.model_dir,
        prompts_path=args.prompts,
        output_path=args.output,
        variant=args.variant,
        limit=args.limit,
        device_override=args.device,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
