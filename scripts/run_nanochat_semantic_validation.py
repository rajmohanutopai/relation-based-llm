#!/usr/bin/env python3
"""Run nanochat generation eval and semantic embedding validation in one command."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--nanochat-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-tag", required=True)
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default="mps")
    parser.add_argument("--embedding-device", choices=["cpu", "mps", "cuda"], default="cpu")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--max-tokens", type=int, default=48)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--progress-every", type=int, default=50)
    parser.add_argument("--semantic-threshold", type=float, default=0.90)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prediction_output = args.output_dir
    semantic_output = args.output_dir / f"semantic_eval_minilm_t{int(args.semantic_threshold * 100):03d}"

    run(
        [
            sys.executable,
            "scripts/run_nanochat_word_surface_eval.py",
            "--run-dir",
            str(args.run_dir),
            "--dataset",
            str(args.dataset),
            "--nanochat-dir",
            str(args.nanochat_dir),
            "--output-dir",
            str(prediction_output),
            "--device",
            args.device,
            "--models",
            args.model,
            "--model-tag",
            f"{args.model}={args.model_tag}",
            "--limit",
            str(args.limit),
            "--max-tokens",
            str(args.max_tokens),
            "--temperature",
            str(args.temperature),
            "--progress-every",
            str(args.progress_every),
        ]
    )

    prediction_path = prediction_output / "predictions" / f"{args.model}.jsonl"
    run(
        [
            sys.executable,
            "scripts/run_embedding_semantic_eval.py",
            "--predictions",
            str(prediction_path),
            "--output-dir",
            str(semantic_output),
            "--device",
            args.embedding_device,
            "--threshold",
            str(args.semantic_threshold),
        ]
    )


if __name__ == "__main__":
    main()
