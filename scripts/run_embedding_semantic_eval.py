#!/usr/bin/env python3
"""Semantic embedding evaluation for nanochat prediction JSONL files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer


DEFAULT_MODEL = Path(
    "~/.cache/torch/sentence_transformers/sentence-transformers_all-MiniLM-L6-v2"
).expanduser()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
    if not rows:
        raise SystemExit(f"{path}: no rows found")
    return rows


def normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" .,:;\"'`")
    return value


def yes_no(value: str) -> str | None:
    value = normalize_text(value)
    if value.startswith("yes"):
        return "yes"
    if value.startswith("no"):
        return "no"
    return None


def polarity_matches(expected: str, generated: str) -> bool:
    expected_polarity = yes_no(expected)
    generated_polarity = yes_no(generated)
    if expected_polarity is None:
        return True
    return expected_polarity == generated_polarity


def mean_pool(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).to(last_hidden_state.dtype)
    summed = torch.sum(last_hidden_state * mask, dim=1)
    counts = torch.clamp(mask.sum(dim=1), min=1e-9)
    return summed / counts


class Embedder:
    def __init__(self, model_path: Path, device: str) -> None:
        if not model_path.exists():
            raise SystemExit(f"Embedding model path not found: {model_path}")
        self.device = torch.device(device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path).to(self.device)
        self.model.eval()

    @torch.no_grad()
    def encode(self, texts: list[str], batch_size: int) -> torch.Tensor:
        vectors: list[torch.Tensor] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            encoded = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt",
            )
            encoded = {key: value.to(self.device) for key, value in encoded.items()}
            output = self.model(**encoded)
            pooled = mean_pool(output.last_hidden_state, encoded["attention_mask"])
            pooled = F.normalize(pooled, p=2, dim=1)
            vectors.append(pooled.cpu())
        return torch.cat(vectors, dim=0)


def bucket(score: float) -> str:
    if score >= 0.90:
        return ">=0.90"
    if score >= 0.85:
        return "0.85-0.90"
    if score >= 0.80:
        return "0.80-0.85"
    if score >= 0.70:
        return "0.70-0.80"
    return "<0.70"


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_summary(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Embedding Semantic Evaluation",
        "",
        f"- Predictions: `{summary['predictions']}`",
        f"- Embedding model: `{summary['embedding_model']}`",
        f"- Rows: {summary['count']}",
        f"- Threshold: {summary['threshold']:.2f}",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Exact answer | {summary['exact_accuracy']:.1%} ({summary['exact_correct']}/{summary['count']}) |",
        f"| Semantic answer | {summary['semantic_accuracy']:.1%} ({summary['semantic_correct']}/{summary['count']}) |",
        f"| Mean cosine | {summary['mean_cosine']:.3f} |",
        f"| Median cosine | {summary['median_cosine']:.3f} |",
        f"| Polarity mismatches | {summary['polarity_mismatches']} |",
        "",
        "## Similarity Buckets",
        "",
        "| Bucket | Count |",
        "| --- | ---: |",
    ]
    for name, count in summary["similarity_buckets"].items():
        lines.append(f"| {name} | {count} |")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu")
    parser.add_argument("--threshold", type=float, default=0.85)
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_jsonl(args.predictions)
    expected = [str(row.get("expected_answer") or row.get("target") or "") for row in rows]
    generated = [str(row.get("generated_answer") or row.get("raw_generated") or "") for row in rows]

    embedder = Embedder(args.model.expanduser(), args.device)
    expected_vecs = embedder.encode(expected, args.batch_size)
    generated_vecs = embedder.encode(generated, args.batch_size)
    similarities = torch.sum(expected_vecs * generated_vecs, dim=1).tolist()

    scored: list[dict[str, Any]] = []
    exact_correct = 0
    semantic_correct = 0
    polarity_mismatches = 0
    bucket_counts = {">=0.90": 0, "0.85-0.90": 0, "0.80-0.85": 0, "0.70-0.80": 0, "<0.70": 0}
    for row, exp, gen, score in zip(rows, expected, generated, similarities, strict=True):
        exact = bool(row.get("answer_exact"))
        polarity_ok = polarity_matches(exp, gen)
        semantic = score >= args.threshold and polarity_ok
        exact_correct += int(exact)
        semantic_correct += int(semantic)
        polarity_mismatches += int(not polarity_ok)
        bucket_counts[bucket(score)] += 1
        enriched = dict(row)
        enriched["embedding_cosine"] = score
        enriched["polarity_match"] = polarity_ok
        enriched["semantic_answer"] = semantic
        scored.append(enriched)

    sorted_scores = sorted(similarities)
    count = len(scored)
    summary = {
        "predictions": str(args.predictions),
        "embedding_model": str(args.model.expanduser()),
        "count": count,
        "threshold": args.threshold,
        "exact_correct": exact_correct,
        "exact_accuracy": exact_correct / count,
        "semantic_correct": semantic_correct,
        "semantic_accuracy": semantic_correct / count,
        "mean_cosine": sum(similarities) / count,
        "median_cosine": sorted_scores[count // 2],
        "polarity_mismatches": polarity_mismatches,
        "similarity_buckets": bucket_counts,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_summary(summary, args.output_dir / "summary.md")
    write_jsonl(scored, args.output_dir / "predictions.semantic.jsonl")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
