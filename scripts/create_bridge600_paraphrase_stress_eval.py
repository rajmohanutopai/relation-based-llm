#!/usr/bin/env python3
"""Create paraphrase-stress evaluation rows for bridge-600.

This keeps the same held-out examples, same target answers, and same core
concept words, but rewrites the prompt surface so evaluation is less tied to the
training templates.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "data/developmental_graph/experiments/bridge600_event_meaning_v1/"
    "datasets/bridge600_event_qa/test.jsonl"
)
DEFAULT_OUTPUT = Path(
    "data/developmental_graph/experiments/bridge600_event_meaning_v1/"
    "datasets/bridge600_event_qa/paraphrase_stress_test.jsonl"
)
DEFAULT_VOCAB_SOURCES = [
    Path("data/developmental_graph/experiments/bridge600_event_meaning_v1/datasets/bridge600_event_qa/train.jsonl"),
    Path("data/developmental_graph/experiments/root_procedural_irregular_v1/train.jsonl"),
]
WORD_RE = re.compile(r"[a-z]+")


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if limit is not None and len(rows) >= limit:
                break
    return rows


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def trained_words(paths: list[Path]) -> set[str]:
    words: set[str] = set()
    for path in paths:
        for row in read_jsonl(path):
            words.update(WORD_RE.findall(f"{row.get('input', '')}\n{row.get('target', '')}".lower()))
    return words


def compact_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"\s+([.?!])", r"\1", text)
    return text


def scene_from_original(prompt: str) -> str:
    prompt = prompt.strip()
    prompt = re.sub(r"\nAnswer(?: with the result and reason)?:\s*$", "", prompt, flags=re.IGNORECASE)
    prompt = re.sub(r"\nReply:\s*$", "", prompt, flags=re.IGNORECASE)
    prompt = re.sub(r"\nNow answer this:.*$", "", prompt, flags=re.IGNORECASE | re.DOTALL)
    prompt = re.sub(r"\nWhat should we conclude\?.*$", "", prompt, flags=re.IGNORECASE | re.DOTALL)
    prompt = re.sub(r"\nTask:.*$", "", prompt, flags=re.IGNORECASE | re.DOTALL)
    prompt = re.sub(r"\nQuestion to answer:.*$", "", prompt, flags=re.IGNORECASE | re.DOTALL)
    prompt = prompt.replace("Situation: ", "")
    prompt = prompt.replace("During play, ", "")
    prompt = prompt.replace("Now, ", "")
    prompt = prompt.replace("The child notices this: ", "")
    prompt = prompt.replace("Read this situation and answer. ", "")
    prompt = prompt.replace("Read this situation and answer.\n", "")
    prompt = prompt.replace("About this event: ", "")
    prompt = prompt.replace("Given: ", "")
    prompt = re.sub(r"\bFrom this,\s*[^.?!]*\?", "", prompt, flags=re.IGNORECASE)
    prompt = re.sub(r"\bTell me:\s*[^.?!]*\?", "", prompt, flags=re.IGNORECASE)
    prompt = re.sub(r"\bWhat should we conclude\?\s*", "", prompt, flags=re.IGNORECASE)
    prompt = "\n".join(line for line in prompt.splitlines() if "?" not in line)
    return compact_sentence(prompt)


def expected_answer(row: dict[str, Any]) -> str:
    match = re.search(r"(?im)^answer:\s*([^\n.]+)", str(row.get("target") or ""))
    if not match:
        return ""
    return match.group(1).strip().lower()


def question_for(row: dict[str, Any], variant: int) -> str:
    meta = row.get("metadata", {})
    concept = str(meta.get("concept") or meta.get("thing") or "this")
    anchor = str(meta.get("anchor") or "link")
    relation = str(meta.get("relation") or "relation").replace("_", " ")
    task_type = str(row.get("task_type") or "")
    answer = expected_answer(row)

    if answer == "yes":
        forms = [
            f"Is this right for {concept}: link to {anchor}?",
            f"Does {concept} go with {anchor}?",
            f"Say yes or no: {concept} means link to {anchor}.",
            f"Is the link to {anchor} right for {concept}?",
        ]
    elif answer == "no":
        forms = [
            f"Is this right for {concept}: no link to {anchor}?",
            f"Does {concept} mean no link to {anchor}?",
            f"Say yes or no: {concept} means no link to {anchor}.",
            f"Is the no link to {anchor} right for {concept}?",
        ]
    elif "quantity" in task_type:
        forms = [
            f"For {concept}, what amount link is right?",
            f"What does {concept} tell about amount?",
            f"Give the amount meaning for {concept}.",
            f"In this case, what does {concept} show?",
        ]
    elif "state" in task_type:
        forms = [
            f"For {concept}, what state link is right?",
            f"What does {concept} tell us in this case?",
            f"Give the state meaning for {concept}.",
            f"In this case, what does {concept} show?",
        ]
    elif "part" in task_type or "place" in task_type:
        forms = [
            f"Where does {concept} go?",
            f"What place link belongs to {concept}?",
            f"Give the place meaning for {concept}.",
            f"In this case, what is connected to {concept}?",
        ]
    elif "sound" in task_type or "heard" in task_type:
        forms = [
            f"What sense link goes with {concept}?",
            f"What can the child know from {concept}?",
            f"Give the sound meaning for {concept}.",
            f"In this case, what does {concept} show?",
        ]
    elif "touch" in task_type or "feeling" in task_type:
        forms = [
            f"What touch link goes with {concept}?",
            f"What can the hand know from {concept}?",
            f"Give the touch meaning for {concept}.",
            f"In this case, what does {concept} show?",
        ]
    else:
        forms = [
            f"What link is right for {concept}?",
            f"What should the child know about {concept}?",
            f"Give the meaning for {concept}.",
            f"In this case, what does {concept} show?",
        ]
    return forms[variant % len(forms)]


def paraphrase_input(row: dict[str, Any], variant: int) -> str:
    scene = scene_from_original(str(row.get("input") or ""))
    question = question_for(row, variant)
    if variant % 4 == 0:
        return f"Case: {scene}\n{question}\nGive answer and reason:"
    if variant % 4 == 1:
        return f"{question}\nWith this case: {scene}\nAnswer and reason:"
    if variant % 4 == 2:
        return f"{scene}\nFrom this, {question}\nReply with answer then reason:"
    return f"Read the case and answer.\nCase: {scene}\nQuestion: {question}\nAnswer:"


def unknown_words(rows: list[dict[str, Any]], vocab: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for word in WORD_RE.findall(str(row.get("input") or "").lower()):
            if word not in vocab:
                counts[word] = counts.get(word, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def build_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        new_row = dict(row)
        metadata = dict(row.get("metadata") or {})
        metadata["original_input"] = row.get("input")
        metadata["paraphrase_stress"] = True
        metadata["original_surface_type"] = row.get("surface_type")
        new_row["id"] = f"{row.get('id')}.paraphrase_stress"
        new_row["input"] = paraphrase_input(row, index)
        new_row["surface_type"] = "paraphrase_stress"
        new_row["prompt_type"] = "paraphrase_stress"
        new_row["metadata"] = metadata
        new_row["messages"] = [
            {"role": "user", "content": new_row["input"]},
            {"role": "assistant", "content": new_row["target"]},
        ]
        output.append(new_row)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--vocab-source", type=Path, action="append", default=DEFAULT_VOCAB_SOURCES)
    parser.add_argument("--allow-new-words", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(args.input, limit=args.limit)
    output = build_rows(rows)
    vocab = trained_words(args.vocab_source)
    unknown = unknown_words(output, vocab)
    if unknown and not args.allow_new_words:
        preview = ", ".join(f"{word}={count}" for word, count in list(unknown.items())[:50])
        raise SystemExit(f"Paraphrase prompts contain words outside training vocabulary: {preview}")
    write_jsonl(output, args.output)
    print(f"Wrote {len(output)} rows to {args.output}")


if __name__ == "__main__":
    main()
