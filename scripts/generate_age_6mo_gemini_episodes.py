#!/usr/bin/env python3
"""Generate natural training episodes from the age_6mo root graph with Gemini.

The graph remains the source of truth. Gemini is only used as a language
renderer that turns selected concept/relation bundles into ordinary child-world
episodes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parent))
from output_state import atomic_write_text, directory_lock  # noqa: E402


TRANSIENT_CODES = {408, 429, 500, 502, 503, 504}
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"
DEFAULT_SEED = Path("data/developmental_graph/seeds/age_6mo_root_world_500.json")
DEFAULT_OUTPUT_DIR = Path("data/developmental_graph/experiments/age_6mo_gemini_episodes_v0")

# Gemini API public list prices can change. Override these if the console shows
# a different rate for the exact preview model.
DEFAULT_INPUT_USD_PER_MILLION = 0.25
DEFAULT_OUTPUT_USD_PER_MILLION = 1.50

DISALLOWED_TEXT = [
    "relation type",
    "linked_to",
    "has_property",
    "comes_through",
    "caused_by",
    "contrasts_with",
    "root graph",
    "ontology",
    "concept id",
    "concept_id",
    "developmental",
    "appropriate",
    "milestone",
    "abstract",
    "jargon",
    "environment",
    "dataset",
    "training",
    "source truth",
    "metadata",
    "node",
    "sensory input",
    "you ",
    "your ",
    " you",
    " your",
    "has wanted",
    "are not wanted",
    "is not wanted",
    "cause fuss",
    "causes fuss",
]

DISALLOWED_CONCEPTS_USED = {
    "child",
    "infant",
    "body action control",
    "sensory input",
    "developmental",
}


def load_seed(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def selected_concepts(seed: dict[str, Any], limit: int, concepts_arg: str | None = None) -> list[dict[str, Any]]:
    by_word = {item["word"]: item for item in seed["concepts"]}
    if concepts_arg:
        requested = [word.strip() for word in concepts_arg.split(",") if word.strip()]
        missing = [word for word in requested if word not in by_word]
        if missing:
            raise SystemExit(f"Unknown concepts: {', '.join(missing)}")
        return [by_word[word] for word in requested[:limit]]
    priority_words = [
        "near", "far", "reach success", "reach fail", "wanted", "not wanted",
        "enough", "too much", "comfort", "pain", "safe touch", "alone",
        "with caregiver", "not held", "body limit", "gone", "back again",
        "can control", "cannot control", "new link", "broken link",
    ]
    picked = [by_word[word] for word in priority_words if word in by_word]
    if len(picked) >= limit:
        return picked[:limit]
    picked_words = {item["word"] for item in picked}
    for item in seed["concepts"]:
        if item["status"] in {"active", "emerging"} and item["word"] not in picked_words:
            picked.append(item)
            picked_words.add(item["word"])
        if len(picked) >= limit:
            break
    return picked


def relation_summary(item: dict[str, Any], max_relations: int = 5) -> list[dict[str, Any]]:
    relations = item.get("relations", [])[:max_relations]
    return [
        {
            "type": rel["type"],
            "target": rel["target"],
            "text": rel["text"],
            "strength": rel.get("strength", 0.75),
            "valence": rel.get("valence", "neutral"),
        }
        for rel in relations
    ]


def build_prompt(item: dict[str, Any]) -> str:
    payload = {
        "concept": item["word"],
        "status": item["status"],
        "category": item["category"],
        "summary": item["summary"],
        "prerequisites": item["prerequisites"],
        "relations": relation_summary(item),
    }
    return (
        "Create one natural training example for a 6-month-old baby's US "
        "household world.\n\n"
        "Use the graph payload only as hidden meaning. The visible scene, "
        "question, and answer must sound like ordinary child-world text, not an "
        "explanation of a dataset.\n\n"
        "Requirements:\n"
        "- Use plain concrete language a parent could say.\n"
        "- Use third person only: say the baby, the hand, the parent. Do not use you or your.\n"
        "- Scene: 1-2 sentences, 18-45 words.\n"
        "- Question: one direct question, 6-18 words.\n"
        "- Answer: one short sentence, 5-16 words.\n"
        "- concepts_used: only graph concept words from the payload; do not add baby, parent, toy, or category names.\n"
        "- Do not mention India-specific items.\n"
        "- Do not use adult/meta words: developmental, milestone, abstract, ontology, graph, relation type, node, edge, metadata, dataset, training, jargon.\n"
        "- Do not say sensory input in visible text. Say the concrete sound/touch/sight instead.\n"
        "- Avoid verbose answers. No phrase like which makes it simple, developmentally appropriate, or interact with their environment.\n"
        "- For wanted, say wants, not has wanted.\n"
        "- For not wanted, say the baby does not want it, not it is not wanted.\n"
        "- Do not use graph-like causal phrases such as cause fuss in the visible answer.\n"
        "- The hidden_relation field must copy one source relation text exactly.\n"
        "- Return strict JSON only.\n\n"
        "Good style examples:\n"
        "- Scene: The rattle is beside the baby's hand. The baby reaches and touches it.\n"
        "  Question: Why can the baby touch the rattle?\n"
        "  Answer: The rattle is near the hand.\n"
        "- Scene: The spoon comes close to the baby's mouth. The baby turns away and fusses.\n"
        "  Question: Why does the baby turn away?\n"
        "  Answer: The baby does not want the spoon.\n\n"
        "JSON shape:\n"
        "{\n"
        '  "concept": string,\n'
        '  "scene": string,\n'
        '  "question": string,\n'
        '  "answer": string,\n'
        '  "hidden_relation": string,\n'
        '  "concepts_used": [string]\n'
        "}\n\n"
        f"Graph payload:\n{json.dumps(payload, indent=2, sort_keys=True)}"
    )


def parse_json_text(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def validate_episode(row: dict[str, Any], item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ["concept", "scene", "question", "answer", "hidden_relation", "concepts_used"]
    for field in required:
        if field not in row:
            errors.append(f"missing field: {field}")
    if errors:
        return errors
    if row["concept"] != item["word"]:
        errors.append("concept mismatch")
    source_relations = {rel["text"] for rel in item.get("relations", [])}
    if row["hidden_relation"] not in source_relations:
        errors.append("hidden_relation does not match source relation text")
    visible = " ".join(str(row.get(field, "")) for field in ["scene", "question", "answer"]).lower()
    for phrase in DISALLOWED_TEXT:
        if phrase in visible:
            errors.append(f"disallowed visible phrase: {phrase}")
    scene_words = len(row["scene"].split())
    question_words = len(row["question"].split())
    answer_words = len(row["answer"].split())
    if not 14 <= scene_words <= 50:
        errors.append(f"scene length outside 14-50 words: {scene_words}")
    if not 4 <= question_words <= 20:
        errors.append(f"question length outside 4-20 words: {question_words}")
    if not 3 <= answer_words <= 18:
        errors.append(f"answer length outside 3-18 words: {answer_words}")
    if not isinstance(row["concepts_used"], list):
        errors.append("concepts_used is not a list")
    else:
        source_words = {item["word"], *(rel["target"] for rel in item.get("relations", []))}
        source_words.update(item.get("prerequisites", []))
        for concept in row["concepts_used"]:
            if str(concept).lower() in DISALLOWED_CONCEPTS_USED:
                errors.append(f"disallowed concepts_used item: {concept}")
            # Extra concepts_used values are metadata quality issues, not
            # training-text failures. Hidden_relation remains the source check.
    return errors


def usage_dict(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return {}
    return {
        "prompt_token_count": int(getattr(usage, "prompt_token_count", 0) or 0),
        "candidates_token_count": int(getattr(usage, "candidates_token_count", 0) or 0),
        "thoughts_token_count": int(getattr(usage, "thoughts_token_count", 0) or 0),
        "total_token_count": int(getattr(usage, "total_token_count", 0) or 0),
    }


def estimate_cost(usage: dict[str, int], input_price: float, output_price: float) -> float:
    input_tokens = usage.get("prompt_token_count", 0)
    output_tokens = usage.get("candidates_token_count", 0) + usage.get("thoughts_token_count", 0)
    return (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()


def partial_path(path: Path) -> Path:
    return path.with_name(path.name + ".partial")


def write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    atomic_write_text(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def read_partial(path: Path) -> list[dict[str, Any]]:
    """Rows from an unfinished run. A crash can tear only the last line; drop it."""
    rows = []
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    for number, line in enumerate(lines, start=1):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            if number != len(lines):
                raise SystemExit(f"{path} line {number} is damaged") from None
    write_jsonl_atomic(path, rows)
    return rows


def is_transient(exc: Exception) -> bool:
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True
    if getattr(exc, "code", None) in TRANSIENT_CODES:
        return True
    return "Timeout" in type(exc).__name__ or "Connect" in type(exc).__name__


def call_with_retries(call: Callable[[], Any], max_retries: int, base_seconds: float, label: str) -> Any:
    for attempt in range(max_retries + 1):
        try:
            return call()
        except Exception as exc:  # noqa: BLE001 - sorted by is_transient.
            if attempt == max_retries or not is_transient(exc):
                print(f"{label}: giving up: {exc}. Finished rows are kept; rerun with --resume.", flush=True)
                raise
            delay = base_seconds * 2 ** attempt
            print(f"{label}: {exc}; retry {attempt + 1}/{max_retries} in {delay:g}s", flush=True)
            time.sleep(delay)
    raise AssertionError("unreachable")


def training_rows(accepted: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in accepted:
        episode = row["episode"]
        rows.append({
            "id": row["id"],
            "task_type": "natural_episode_qa",
            "input": f"Scene: {episode['scene']}\nQuestion: {episode['question']}\nAnswer:",
            "target": episode["answer"],
            "metadata": {
                "source_concept_id": row["source_concept_id"],
                "source_concept": row["source_concept"],
                "source_status": row["source_status"],
                "source_category": row["source_category"],
                "hidden_relation": episode["hidden_relation"],
                "model": row["model"],
            },
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--concepts", default=None, help="Comma-separated concept words to generate.")
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--temperature", type=float, default=0.45)
    parser.add_argument("--max-output-tokens", type=int, default=700)
    parser.add_argument("--input-usd-per-million", type=float, default=DEFAULT_INPUT_USD_PER_MILLION)
    parser.add_argument("--output-usd-per-million", type=float, default=DEFAULT_OUTPUT_USD_PER_MILLION)
    parser.add_argument("--max-retries", type=int, default=4, help="Retries per call on transient API errors.")
    parser.add_argument("--retry-base-seconds", type=float, default=2.0)
    parser.add_argument("--resume", action="store_true", help="Continue an unfinished run; finished concepts aren't paid for again.")
    parser.add_argument("--discard-partial", action="store_true", help="Throw away an unfinished run and start again.")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("Set GEMINI_API_KEY or GOOGLE_API_KEY before running this script.")

    seed = load_seed(args.seed_path)
    concepts = selected_concepts(seed, args.limit, args.concepts)
    client = genai.Client(api_key=api_key)

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    usage_total = {
        "prompt_token_count": 0,
        "candidates_token_count": 0,
        "thoughts_token_count": 0,
        "total_token_count": 0,
    }

    config = types.GenerateContentConfig(
        temperature=args.temperature,
        max_output_tokens=args.max_output_tokens,
        response_mime_type="application/json",
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )

    accepted_path = args.output_dir / "episodes.accepted.jsonl"
    rejected_path = args.output_dir / "episodes.rejected.jsonl"
    training_path = args.output_dir / "training.accepted.jsonl"
    manifest_path = args.output_dir / "manifest.json"
    # Rows collect here. The published files above change only when a run finishes,
    # so they always describe one complete run.
    accepted_partial = partial_path(accepted_path)
    rejected_partial = partial_path(rejected_path)
    state_path = args.output_dir / "run_state.json"
    fingerprint = {
        "model": args.model,
        "seed_path": str(args.seed_path),
        "concept_ids": [item["id"] for item in concepts],
        "temperature": args.temperature,
        "max_output_tokens": args.max_output_tokens,
    }

    with directory_lock(args.output_dir):
        if state_path.exists() and args.discard_partial:
            for path in (state_path, accepted_partial, rejected_partial):
                path.unlink(missing_ok=True)
        if state_path.exists():
            if not args.resume:
                raise SystemExit(f"{args.output_dir} holds an unfinished paid run; pass --resume or --discard-partial")
            if json.loads(state_path.read_text(encoding="utf-8")) != fingerprint:
                raise SystemExit("--resume needs the same model, concepts and settings as the unfinished run")
            accepted = read_partial(accepted_partial)
            rejected = read_partial(rejected_partial)
        else:
            atomic_write_text(state_path, json.dumps(fingerprint, indent=2, sort_keys=True))
            accepted_partial.write_text("", encoding="utf-8")
            rejected_partial.write_text("", encoding="utf-8")
        finished = {row["source_concept_id"] for row in accepted + rejected}
        for row in accepted + rejected:
            for key in usage_total:
                usage_total[key] += row["usage"].get(key, 0)

        for index, item in enumerate(concepts, start=1):
            if item["id"] in finished:
                continue
            prompt = build_prompt(item)
            started = time.time()
            response = call_with_retries(
                lambda: client.models.generate_content(model=args.model, contents=prompt, config=config),
                args.max_retries,
                args.retry_base_seconds,
                f"[{index}/{len(concepts)}] {item['word']}",
            )
            elapsed = time.time() - started
            usage = usage_dict(response)
            for key in usage_total:
                usage_total[key] += usage.get(key, 0)
            raw_text = ""
            try:
                raw_text = getattr(response, "text", "") or ""  # raises on a blocked response
                episode = parse_json_text(raw_text)
                errors = validate_episode(episode, item)
            except Exception as exc:  # noqa: BLE001 - record generation failures.
                episode = {"raw_text": raw_text}
                errors = [f"parse error: {exc}"]

            row = {
                "id": f"age_6mo_gemini_episode_v0.{index:03d}.{item['word'].replace(' ', '_')}",
                "model": args.model,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_concept_id": item["id"],
                "source_concept": item["word"],
                "source_status": item["status"],
                "source_category": item["category"],
                "episode": episode,
                "validation_errors": errors,
                "usage": usage,
                "elapsed_seconds": round(elapsed, 3),
            }
            if errors:
                rejected.append(row)
                append_jsonl(rejected_partial, row)
                print(f"[{index}/{len(concepts)}] rejected {item['word']}: {errors}", flush=True)
            else:
                accepted.append(row)
                append_jsonl(accepted_partial, row)
                print(f"[{index}/{len(concepts)}] accepted {item['word']}", flush=True)
            time.sleep(args.sleep_seconds)

        order = {item["id"]: i for i, item in enumerate(concepts)}
        accepted.sort(key=lambda row: order[row["source_concept_id"]])
        rejected.sort(key=lambda row: order[row["source_concept_id"]])
        manifest_path.unlink(missing_ok=True)  # no manifest while the published files change
        write_jsonl_atomic(accepted_path, accepted)
        write_jsonl_atomic(rejected_path, rejected)
        write_jsonl_atomic(training_path, training_rows(accepted))
        token_priced_cost = estimate_cost(usage_total, args.input_usd_per_million, args.output_usd_per_million)
        manifest = {
            "schema_version": "0.1.0",
            "experiment_id": "age_6mo_gemini_episodes_v0",
            "model": args.model,
            "seed_path": str(args.seed_path),
            "accepted_path": str(accepted_path),
            "rejected_path": str(rejected_path),
            "training_path": str(training_path),
            "requested": len(concepts),
            "accepted": len(accepted),
            "rejected": len(rejected),
            "usage_total": usage_total,
            "price_assumption_usd_per_million": {
                "input": args.input_usd_per_million,
                "output": args.output_usd_per_million,
            },
            "token_priced_cost_usd": round(token_priced_cost, 6),
            "cost_note": (
                "Computed from exact API token usage and configured list-price assumptions. "
                "The exact billed invoice amount must be checked in Google Cloud Billing or AI Studio billing."
            ),
        }
        atomic_write_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        for path in (accepted_partial, rejected_partial, state_path):
            path.unlink(missing_ok=True)
        print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
