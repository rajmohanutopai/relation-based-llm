#!/usr/bin/env python3
"""Create a template-irregular root procedural QA dataset.

This is a stricter follow-up to root_procedural_expansion_v1. It keeps the same
source relation units, split policy, answers, and reasons, but varies the
model-visible language so success is less likely to come from memorizing a few
prompt/scene templates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_root_procedural_expansion_v1 as root_v1  # noqa: E402
from output_state import retire_output_dir  # noqa: E402


EXPERIMENT_ID = "root_procedural_irregular_v1"
VARIANT = "root_irregular_qa"
SPLITS = root_v1.SPLITS
TEST_SPLITS = root_v1.TEST_SPLITS
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")


SCENE_PREFIXES = (
    "",
    "In this moment, ",
    "Now, ",
    "The child notices this: ",
    "During play, ",
    "In the room, ",
)
SCENE_JOINERS = (" ", " Then ", " After that, ", " At the same time, ")
QUESTION_LEADS = (
    "{question}",
    "Tell me: {question}",
    "From this, {question_lc}",
    "Using the situation, {question_lc}",
    "What should we conclude? {question}",
)
ANSWER_LEADS = (
    "Answer:",
    "Reply:",
    "Give the answer:",
    "So the answer is:",
    "Answer with the result and reason:",
)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite")
    if path.exists() and overwrite:
        retire_output_dir(path)
    path.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_int(*parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def pick(options: tuple[str, ...], *parts: object) -> str:
    return options[stable_int(*parts) % len(options)]


def clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sentence(text: str) -> str:
    text = clean_spaces(text)
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    if text[-1] not in ".?!":
        text += "."
    return text


def question(text: str) -> str:
    text = clean_spaces(text).rstrip(".")
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    if not text.endswith("?"):
        text += "?"
    return text


def article_for(word: str) -> str:
    word = word.strip().lower()
    return "an" if word[:1] in {"a", "e", "i", "o", "u"} else "a"


def property_word(value: str) -> str:
    value = value.strip().lower()
    return {"danger": "dangerous"}.get(value, value)


def hand_state_phrase(value: str, thing: str) -> str:
    value = value.strip().lower()
    if value == "held":
        return f"holds the {thing}"
    if value == "released":
        return f"lets the {thing} go"
    return f"has the {thing}"


def split_sentences(scene: str) -> list[str]:
    parts = [clean_spaces(part) for part in re.split(r"\.\s*", scene) if clean_spaces(part)]
    return [part.rstrip(".") for part in parts]


def irregular_scene(row: dict[str, Any]) -> str:
    """Render the same facts with varied but conservative wording."""
    meta = row.get("metadata", {})
    family = str(row["rule_family"])
    thing = str(meta.get("thing") or "thing")
    parts = split_sentences(str(row["scene"]))

    if family == "container_access":
        container = str(meta.get("container") or "container")
        state = str(meta.get("state") or "")
        article = article_for(state)
        templates = (
            f"{thing} sits inside a {container} that is {state}. the hand tries to reach inside",
            f"the hand goes toward the {container}. inside it is the {thing}, and the {container} is {state}",
            f"there is {article} {state} {container} with the {thing} in it. the hand reaches for the {thing}",
            f"the {thing} is not outside; it is in the {state} {container}. the hand reaches in",
        )
        return sentence(pick(templates, row["id"]))

    if family == "touch_distance":
        distance = str(meta.get("distance") or "")
        if len(parts) >= 2:
            templates = (
                f"{parts[1]}. {parts[0]}",
                f"the hand tries first. {parts[0]}",
                f"{parts[0]}, while the hand reaches",
                f"the child reaches toward the {thing}; {parts[0].lower()}",
            )
            return sentence(pick(templates, row["id"]))

    if family == "move_weight":
        action = str(meta.get("action") or "moves")
        templates = (
            f"the hand {action}s the {thing}. {thing} is {meta.get('distance')} from the hand",
            f"{thing} is {meta.get('distance')} and light. the hand tries to {action} it",
            f"the hand tries a {action} on the {thing}; the {thing} is {meta.get('distance')}",
            str(row["scene"]),
        )
        return sentence(pick(templates, row["id"]))

    if family == "support_fall":
        surface = str(meta.get("surface") or "surface")
        state = str(meta.get("state") or "")
        hand_phrase = hand_state_phrase(state, thing)
        templates = (
            f"the {thing} is above the {surface}. the hand {hand_phrase}",
            f"above the {surface}, the hand has the {thing}; then the state is {state}",
            f"the hand is with the {thing} over the {surface}. the important state is {state}",
            str(row["scene"]),
        )
        return sentence(pick(templates, row["id"]))

    if family == "property_touch":
        prop = property_word(str(meta.get("property") or ""))
        templates = (
            f"the hand touches the {thing}. the {thing} is {prop}",
            f"{thing} has a {prop} touch-property. the hand touches it",
            f"touch happens between the hand and the {thing}; the {thing} is {prop}",
            str(row["scene"]),
        )
        return sentence(pick(templates, row["id"]))

    if family == "language_name":
        word = str(meta.get("word") or "word")
        templates = (
            f"mom says {word}. the child hears it and looks at the {thing}",
            f"the spoken word is {word}. the child looks toward the {thing}",
            f"a sound-word, {word}, is heard. the child's eyes go to the {thing}",
            str(row["scene"]),
        )
        return sentence(pick(templates, row["id"]))

    if family == "living_need":
        need = str(meta.get("need") or "something")
        templates = (
            f"{thing} is living. living things need {need}",
            f"because the {thing} is alive, {need} matters",
            f"the {thing} belongs to living things, and living things need {need}",
            str(row["scene"]),
        )
        return sentence(pick(templates, row["id"]))

    if family in {"happiness_mechanism", "object_change", "social_effect", "social_signal"}:
        if len(parts) > 1 and stable_int("reverse", row["id"]) % 3 == 0:
            parts = list(reversed(parts))
        prefix = pick(SCENE_PREFIXES, row["id"], "prefix")
        joiner = pick(SCENE_JOINERS, row["id"], "join")
        return sentence(prefix + joiner.join(part.lower() if idx else part for idx, part in enumerate(parts)))

    if family in {"place_context", "time_change"}:
        prefix = pick(SCENE_PREFIXES, row["id"], "prefix")
        return sentence(prefix + str(row["scene"]).strip())

    prefix = pick(SCENE_PREFIXES, row["id"], "prefix")
    if len(parts) > 1 and stable_int("swap", row["id"]) % 4 == 0:
        parts = parts[1:] + parts[:1]
    return sentence(prefix + pick(SCENE_JOINERS, row["id"], "join").join(parts))


def target_text(row: dict[str, Any]) -> str:
    return root_v1.target_text(row)


def prompt_surfaces(row: dict[str, Any], scene: str) -> list[dict[str, str]]:
    q = question(str(row["question"]))
    q_lc = q[0].lower() + q[1:] if q else q
    lead = pick(QUESTION_LEADS, row["id"], "lead")
    answer_lead = pick(ANSWER_LEADS, row["id"], "answer")
    variants = [
        f"{scene}\n{lead.format(question=q, question_lc=q_lc)}\n{answer_lead}",
        f"Situation: {scene}\n{lead.format(question=q, question_lc=q_lc)}\n{answer_lead}",
        f"Read this situation and answer.\n{scene}\n{q}\n{answer_lead}",
        f"{lead.format(question=q, question_lc=q_lc)}\nSituation: {scene}\n{answer_lead}",
        f"Given: {scene}\nTask: {q}\n{answer_lead}",
        f"About this event: {scene}\nQuestion to answer: {q}\n{answer_lead}",
        f"{scene}\nNow answer this: {q}\n{answer_lead}",
    ]
    rows: list[dict[str, str]] = []
    for index, text in enumerate(variants, start=1):
        rows.append({"prompt_type": f"irregular_{index:02d}", "input": text})
    return rows


def make_record(
    experiment_id: str,
    split: str,
    row: dict[str, Any],
    surface: dict[str, str],
    surface_index: int,
) -> dict[str, Any]:
    target = target_text(row)
    metadata = {
        **row["metadata"],
        "domain_id": experiment_id,
        "rule_family": row["rule_family"],
        "representation": VARIANT,
        "prompt_type": surface["prompt_type"],
        "source_world": root_v1.EXPERIMENT_ID,
        "evaluation_bucket": split,
        "surface_bindings": row["surface_bindings"],
        "hidden_root_relations": row["root_relations"],
        "hidden_negative_root_relations": row["negative_root_relations"],
        "relations_visible_to_model": False,
        "template_irregular": True,
    }
    return {
        "id": f"dataset.{experiment_id}.{VARIANT}.{split}.{surface_index:02d}.{surface['prompt_type']}.{row['id']}",
        "source_example_id": row["id"],
        "experiment_id": experiment_id,
        "variant": VARIANT,
        "split": split,
        "evaluation_bucket": split,
        "surface_type": surface["prompt_type"],
        "prompt_type": surface["prompt_type"],
        "task_type": row["rule_family"],
        "input": surface["input"],
        "target": target,
        "messages": [
            {"role": "user", "content": surface["input"]},
            {"role": "assistant", "content": target},
        ],
        "metadata": metadata,
    }


def build_records(experiment_id: str, split: str, units: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for unit in units:
        scene = irregular_scene(unit)
        surfaces = prompt_surfaces(unit, scene)
        for index, surface in enumerate(surfaces, start=1):
            rows.append(make_record(experiment_id, split, unit, surface, index))
    random.Random(seed + stable_int(split)).shuffle(rows)
    return rows


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "unknown")) for row in rows).items()))


def nested_count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("metadata", {}).get(key, "unknown")).lower() for row in rows).items()))


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


def prompt_conflict_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets_by_input: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        targets_by_input[row["input"]].add(row["target"])
    conflicts = sum(1 for values in targets_by_input.values() if len(values) > 1)
    return {
        "unique_inputs": len(targets_by_input),
        "ambiguous_inputs": conflicts,
        "ambiguous_input_percent": round((conflicts / len(targets_by_input)) * 100, 4)
        if targets_by_input
        else 0.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/root_procedural_irregular_v1"),
    )
    parser.add_argument("--experiment-id", default=EXPERIMENT_ID)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_output_dir(args.output_dir, args.overwrite)

    units = root_v1.build_units()
    unit_splits, split_policy = root_v1.split_units(units, args.seed)

    for split, split_units in unit_splits.items():
        write_jsonl(args.output_dir / "units" / f"{split}.jsonl", split_units)
    test_units = [row for split in TEST_SPLITS for row in unit_splits[split]]
    write_jsonl(args.output_dir / "units" / "curriculum_test.jsonl", sorted(test_units, key=lambda row: row["id"]))

    records: dict[str, list[dict[str, Any]]] = {}
    output_paths: dict[str, Path] = {}
    for split in SPLITS:
        rows = build_records(args.experiment_id, split, unit_splits[split], args.seed)
        records[split] = rows
        path = args.output_dir / "datasets" / VARIANT / f"{split}.jsonl"
        write_jsonl(path, rows)
        output_paths[split] = path
    curriculum_rows = [row for split in TEST_SPLITS for row in records[split]]
    curriculum_rows.sort(key=lambda row: row["id"])
    records["curriculum_test"] = curriculum_rows
    curriculum_path = args.output_dir / "datasets" / VARIANT / "curriculum_test.jsonl"
    write_jsonl(curriculum_path, curriculum_rows)
    output_paths["curriculum_test"] = curriculum_path

    for split in ("train", "dev", "curriculum_test"):
        write_jsonl(args.output_dir / f"{split}.jsonl", records[split])

    base_world = root_v1.build_base_world(units)
    base_world["world_id"] = args.experiment_id
    base_world["purpose"] = "Template-irregular ordinary-text QA rendering of root_procedural_expansion_v1."
    base_world["surface_policy"] = {
        "source_world": root_v1.EXPERIMENT_ID,
        "variant": VARIANT,
        "prompt_surfaces_per_unit": 7,
        "relations_visible_to_model": False,
        "target_format": "answer line followed by reason line",
    }
    base_world_path = args.output_dir / "base_world.json"
    write_json(base_world_path, base_world)

    dataset_manifest_path = args.output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "variant": VARIANT,
        "source_experiment_id": root_v1.EXPERIMENT_ID,
        "base_world": str(base_world_path),
        "split_policy": split_policy,
        "splits": {
            split: {
                "total": len(records[split]),
                "base_units": len(unit_splits[split]) if split in unit_splits else len(test_units),
                "prompts_per_unit": 7,
                "task_type_counts": count_by(records[split], "task_type"),
                "prompt_type_counts": count_by(records[split], "prompt_type"),
                "question_type_counts": nested_count(records[split], "question_type"),
                "evaluation_bucket_counts": count_by(records[split], "evaluation_bucket"),
                "vocabulary": vocab_stats(records[split]),
                "prompt_conflicts": prompt_conflict_stats(records[split]),
            }
            for split in (*SPLITS, "curriculum_test")
        },
        "outputs": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in sorted(output_paths.items())
        },
        "notes": [
            "Same source units and split policy as root_procedural_expansion_v1.",
            "Scene and prompt templates are intentionally varied to reduce template memorization.",
            "Answers and reasons are unchanged so old dense QA and irregular QA remain comparable.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)

    training_config_path = args.output_dir / "training_config.json"
    write_json(
        training_config_path,
        {
            "schema_version": "0.1.0",
            "experiment_id": args.experiment_id,
            "dataset_manifest": str(dataset_manifest_path),
            "output_root": f"runs/{args.experiment_id}/nanochat",
            "format": {"prompt_template": "{input}\n", "target_template": "{target}"},
            "training": {"max_seq_length": 256, "seed": args.seed, "recommended_depth": 4},
        },
    )

    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "variant": VARIANT,
        "source_experiment_id": root_v1.EXPERIMENT_ID,
        "source_total_units": len(units),
        "record_splits": {split: len(records[split]) for split in (*SPLITS, "curriculum_test")},
        "prompts_per_unit": 7,
        "dataset_manifest": str(dataset_manifest_path),
        "training_config": str(training_config_path),
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
