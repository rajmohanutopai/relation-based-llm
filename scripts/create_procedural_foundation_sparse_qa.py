#!/usr/bin/env python3
"""Create a relation-sparse QA control from the V5 procedural QA data.

The control keeps the same question and answer/reason target as the proper
word QA data, but strips most scene relations. It is meant to answer one
specific question: how much of the held-out score comes from relation-dense
scene text rather than from the output protocol, answer priors, or object
identity priors?
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


SPLITS = ("train", "dev", "curriculum_test")
SOURCE_VARIANT = "word_plain_qa"
TARGET_VARIANT = "word_sparse_qa"
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise SystemExit(f"{path}:{line_number}: expected object")
            rows.append(row)
    if not rows:
        raise SystemExit(f"{path}: no rows")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    if text[-1] not in ".?!":
        text += "."
    return text


def phrase_list(names: list[str]) -> str:
    clean = [name.strip() for name in names if name and name.strip()]
    if not clean:
        return "something"
    if len(clean) == 1:
        return clean[0]
    return ", ".join(clean[:-1]) + f" and {clean[-1]}"


def split_pair(value: str) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split("_") if part.strip()]


def sparse_scene(row: dict[str, Any]) -> str:
    """Return a scene with object/agent handles but minimal relation cues."""

    task = str(row.get("task_type") or "")
    meta = row.get("metadata", {})
    thing = str(meta.get("thing") or "thing")

    if task == "reach_touch":
        return sentence(f"baby is here. {thing} is here. baby moves hand")

    if task == "push_pull_move":
        action = str(meta.get("action") or "moves")
        verb = "pushes" if action == "push" else "pulls" if action == "pull" else "moves"
        return sentence(f"{thing} is here. baby {verb} {thing}")

    if task == "body_control":
        return sentence(f"baby tries to move {thing}")

    if task == "drop_fall":
        return sentence(f"{thing} is here. baby opens hand")

    if task == "support_edge_fall":
        surface = str(meta.get("surface") or "surface")
        return sentence(f"{thing} is on {surface}. baby bumps {surface}")

    if task == "container_open_closed":
        container = str(meta.get("container") or "container")
        return sentence(f"{thing} is in {container}. baby puts hand on {container}")

    if task == "hide_see":
        return sentence(f"{thing} is here. baby looks")

    if task == "shake_sound":
        return sentence(f"baby holds {thing}. baby moves {thing}")

    if task == "temperature_touch":
        return sentence(f"{thing} is here. baby touches {thing}")

    if task == "wet_dry":
        return sentence(f"{thing} is here. baby touches {thing}")

    if task == "safe_unsafe_touch":
        return sentence(f"{thing} is here. baby reaches hand")

    if task == "same_different_match":
        names = split_pair(thing)
        return sentence(f"{phrase_list(names)} are here. baby looks")

    if task == "more_less_count":
        return sentence(f"left has {thing}. right has {thing}. baby looks")

    if task == "path_open_closed":
        path = str(meta.get("path") or "path")
        return sentence(f"{path} is here. baby pushes {thing} to {path}")

    if task == "caregiver_comfort":
        return sentence("baby is here. caregiver is here")

    if task == "familiar_agent":
        return sentence(f"{thing} comes near baby. baby looks")

    if task == "social_signal_response":
        return sentence("a person is near baby. baby sees and hears")

    if task == "give_take":
        agent = str(meta.get("agent") or "person")
        return sentence(f"{agent} and {thing} are near baby. baby looks")

    if task == "word_name_binding":
        word = str(meta.get("word") or "word")
        return sentence(f"mom says {word}. baby looks")

    return sentence("baby is here. something happens")


def replace_scene(input_text: str, new_scene: str) -> str:
    scene_patterns = [
        (r"(?s)^scene:\s*(.*?)\nquestion:", "scene: {scene}\nquestion:"),
        (r"(?s)^The scene is\s*(.*?)\nThe question is", "The scene is {scene}\nThe question is"),
        (r"(?s)^Scene:\s*(.*?)\nAnswer this question:", "Scene: {scene}\nAnswer this question:"),
        (r"(?s)^Scene:\s*(.*?)\nQuestion:", "Scene: {scene}\nQuestion:"),
        (r"(?s)^Question:\s*(.*?)\nScene:\s*(.*?)\nAnswer:", None),
    ]

    for pattern, replacement in scene_patterns:
        match = re.search(pattern, input_text)
        if not match:
            continue
        if replacement is None:
            return f"Question: {match.group(1).strip()}\nScene: {new_scene}\nAnswer:"
        return re.sub(pattern, replacement.format(scene=new_scene), input_text, count=1)
    raise ValueError(f"could not locate scene in input: {input_text!r}")


def transform_row(row: dict[str, Any], experiment_id: str) -> dict[str, Any]:
    new_scene = sparse_scene(row)
    input_text = replace_scene(str(row["input"]), new_scene)
    target_text = str(row["target"])
    metadata = {
        **row.get("metadata", {}),
        "representation": TARGET_VARIANT,
        "sparse_control": True,
        "sparse_scene_policy": "objects_and_agents_without_discriminating_scene_relations",
    }
    transformed = {
        **row,
        "id": str(row["id"]).replace(row.get("experiment_id", "unknown"), experiment_id).replace(SOURCE_VARIANT, TARGET_VARIANT),
        "experiment_id": experiment_id,
        "variant": TARGET_VARIANT,
        "input": input_text,
        "target": target_text,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target_text},
        ],
        "metadata": metadata,
    }
    return transformed


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, int]:
    words: Counter[str] = Counter()
    raw: Counter[str] = Counter()
    for row in rows:
        text = f"{row['input']}\n{row['target']}".lower()
        words.update(WORD_RE.findall(text))
        raw.update(RAW_RE.findall(text))
    return {
        "unique_words_alpha": len(words),
        "total_words_alpha": sum(words.values()),
        "unique_raw_whitespace_tokens": len(raw),
        "total_raw_whitespace_tokens": sum(raw.values()),
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "unknown") for row in rows).items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/procedural_foundation_v5_consistent_qa_5k"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/procedural_foundation_v5_sparse_qa_5k"),
    )
    parser.add_argument("--experiment-id", default="procedural_foundation_v5_sparse_qa_5k")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        if not args.overwrite:
            raise SystemExit(f"{args.output_dir} exists; pass --overwrite")
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    split_rows: dict[str, list[dict[str, Any]]] = {}
    for split in SPLITS:
        source_path = args.source_dir / "datasets" / SOURCE_VARIANT / f"{split}.jsonl"
        rows = read_jsonl(source_path)
        split_rows[split] = [transform_row(row, args.experiment_id) for row in rows]

    dataset_dir = args.output_dir / "datasets" / TARGET_VARIANT
    output_paths = {}
    for split, rows in split_rows.items():
        path = dataset_dir / f"{split}.jsonl"
        write_jsonl(path, rows)
        output_paths[split] = path

    # Keep top-level split aliases for scripts that expect the experiment root.
    for split, rows in split_rows.items():
        write_jsonl(args.output_dir / f"{split}.jsonl", rows)

    manifest = {
        "experiment_id": args.experiment_id,
        "source_dir": str(args.source_dir),
        "source_variant": SOURCE_VARIANT,
        "variant": TARGET_VARIANT,
        "purpose": "Relation-sparse natural QA control using the same source examples and targets as V5 5K plain QA.",
        "counts": {split: len(rows) for split, rows in split_rows.items()},
        "vocab": {split: vocab_stats(rows) for split, rows in split_rows.items()},
        "task_type_counts": {split: count_by(rows, "task_type") for split, rows in split_rows.items()},
        "paths": {split: str(path) for split, path in output_paths.items()},
    }
    write_json(args.output_dir / "manifest.json", manifest)
    write_json(args.output_dir / "datasets" / "manifest.json", manifest)

    print(json.dumps(manifest["counts"], indent=2, sort_keys=True))
    print(f"Wrote {dataset_dir}")


if __name__ == "__main__":
    main()
