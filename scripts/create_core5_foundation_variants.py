#!/usr/bin/env python3
"""Create staged foundation variants for core5.

The foundation dataset is not a stricter word-ban version of child language.
It is a staged ladder:

- f0: simple facts only
- f1: introduce a handle after supporting facts
- f2: ask using the handle
- f3: attach later names to the learned handle

This keeps necessary handles such as "body" and "own body", but avoids using
them as primitives before their support relations are shown.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any
from output_state import retire_output_dir  # noqa: E402


SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = ("foundation_plain_text", "foundation_relation_scaffolded", "foundation_relation_first_then_text")
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")

Example = dict[str, Any]
Unit = dict[str, Any]
Record = dict[str, Any]


NODE_WORDS = {
    "agent.primary_caregiver": "mom dad",
    "agent.secondary_caregiver": "mom dad",
    "agent.caregiver": "mom dad",
    "agent.other_child": "child",
    "agent.person": "person",
    "agent.referent_person": "person",
    "concept.other_agent_proto": "person",
    "concept.self_proto": "body",
    "object.self_hand": "hand",
    "object.self_mouth": "mouth",
    "object.ball": "ball",
    "object.ceiling_fan": "fan",
    "object.rattle": "toy",
    "object.cloth": "cloth",
    "object.floor": "floor",
    "object.cup": "cup",
    "object.bowl": "bowl",
    "object.spoon": "spoon",
    "object.door": "door",
    "object.book": "book",
    "object.toy": "toy",
    "object.block": "block",
    "object.water": "water",
    "object.milk": "milk",
    "object.food": "food",
    "object.bottle": "bottle",
    "object.rubber_ball": "ball",
    "object.sponge_ball": "ball",
    "property.soft": "soft",
    "property.hard": "hard",
    "property.round": "round",
    "property.hot": "hot",
    "property.cold": "cold",
    "property.wet": "wet",
    "property.wet_body": "wet",
    "property.dry": "dry",
    "property.loud": "loud",
    "property.quiet": "quiet",
    "property.heavy": "heavy",
    "property.light": "light",
    "property.big": "big",
    "property.small": "small",
    "property.familiar": "known",
    "channel.visual": "see",
    "channel.sound": "hear",
    "channel.touch": "touch feel",
    "channel.chemical": "taste smell",
    "channel.valence": "good bad",
    "channel.proprioception_control": "move feel",
    "channel.motion": "move",
    "channel.temperature": "hot cold",
    "invariant.direct_control": "can move",
    "invariant.indirect_effect": "can make",
    "invariant.comfort_discomfort": "ok not ok",
    "invariant.pain_relief": "hurt help",
    "invariant.same_different": "same different",
    "invariant.before_after": "before after",
    "invariant.near_far": "near far",
    "invariant.touching": "touch",
    "invariant.moves_stops": "move stop",
    "invariant.inside_outside": "in out",
    "invariant.open_closed": "open close",
    "invariant.more_less": "more less",
    "invariant.more_less_equal": "more less same",
    "invariant.zero_one_many": "zero one many",
    "invariant.one_to_one": "one each",
    "invariant.group_member": "part group",
    "invariant.part_whole": "part whole",
    "invariant.expected_unexpected": "known new",
    "schema.self_motion": "baby move",
    "schema.shake_sound": "shake sound",
    "schema.feeding_relief": "milk help",
    "schema.held_by_caregiver": "mom dad hold",
    "schema.object_fall_impact": "thing fall hit",
    "schema.surface_friction_motion": "thing slide stop",
    "schema.containment_fit": "thing fit in",
    "schema.object_label_binding": "word name thing",
    "schema.word_handle": "word name",
    "schema.name_binding": "name thing",
    "schema.attribute_match": "same kind",
    "schema.object_count": "count thing",
    "symbol.number_word": "number word",
    "surface.spoken_word": "word",
    "surface.home_language_word": "word",
    "event.ball_roll": "ball roll",
    "event.roll_motion": "roll",
    "event.door_open_close": "door open close",
    "signal.no_word": "no",
    "signal.yes_word": "yes",
}

REL_WORDS = {
    "action_effect": "make",
    "binds_to": "name",
    "built_from": "from",
    "can_activate": "wake",
    "can_cause": "make",
    "can_contact": "touch",
    "co_occurs_with": "with",
    "contrasts_with": "not same",
    "counteracts": "stop",
    "directly_controlled_by": "can move",
    "directly_feels": "can feel",
    "enables": "let",
    "has_property": "is",
    "has_relation": "has",
    "instance_of": "is",
    "modifies": "change",
    "not_directly_controlled_by": "cannot move",
    "predicts": "tell",
    "selects": "pick",
    "strengthens": "make strong",
    "strengthens_can_cause": "make",
    "strengthens_direct_control": "can move",
    "strengthens_has_property": "is",
    "strengthens_predicts": "tell",
    "supports": "help",
    "updates": "change",
    "uses": "use",
}

ALLOWED_WORDS = {
    "a",
    "after",
    "again",
    "all",
    "and",
    "baby",
    "bad",
    "ball",
    "before",
    "big",
    "block",
    "body",
    "book",
    "bottle",
    "bounce",
    "bowl",
    "can",
    "cannot",
    "child",
    "close",
    "cloth",
    "cold",
    "count",
    "cup",
    "dad",
    "different",
    "door",
    "down",
    "dry",
    "each",
    "f",
    "fan",
    "fall",
    "far",
    "feel",
    "fit",
    "floor",
    "food",
    "from",
    "give",
    "go",
    "good",
    "group",
    "hand",
    "hard",
    "hear",
    "heavy",
    "help",
    "hit",
    "hold",
    "hot",
    "hurt",
    "in",
    "is",
    "kind",
    "known",
    "l",
    "later",
    "let",
    "light",
    "look",
    "loud",
    "make",
    "many",
    "me",
    "milk",
    "mom",
    "more",
    "mouth",
    "move",
    "name",
    "near",
    "new",
    "no",
    "not",
    "ok",
    "on",
    "one",
    "open",
    "out",
    "own",
    "part",
    "person",
    "pick",
    "push",
    "q",
    "quiet",
    "r",
    "roll",
    "round",
    "s",
    "same",
    "see",
    "shake",
    "slide",
    "small",
    "smell",
    "soft",
    "sound",
    "spoon",
    "stop",
    "strong",
    "take",
    "taste",
    "tell",
    "thing",
    "touch",
    "toy",
    "two",
    "up",
    "use",
    "wake",
    "warm",
    "water",
    "wet",
    "with",
    "word",
    "yes",
    "zero",
}


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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite")
    if path.exists() and overwrite:
        retire_output_dir(path)
    path.mkdir(parents=True, exist_ok=True)


def clean(value: Any) -> str:
    text = str(value or "").lower()
    text = text.replace("_", " ").replace(".", " ").replace("/", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def words(text: str) -> set[str]:
    return set(WORD_RE.findall(text.lower()))


def is_allowed(text: str) -> bool:
    return words(text) <= ALLOWED_WORDS


def id_tail(identifier: Any) -> str | None:
    tail = clean(str(identifier or "").split(".")[-1])
    return tail if tail and is_allowed(tail) else None


def node_text(identifier: Any) -> str | None:
    if not isinstance(identifier, str) or not identifier:
        return None
    if identifier in NODE_WORDS:
        return NODE_WORDS[identifier]
    return id_tail(identifier)


def rel_text(rel_type: Any) -> str | None:
    rel = str(rel_type or "")
    if rel in REL_WORDS:
        return REL_WORDS[rel]
    fallback = clean(rel)
    return fallback if fallback and is_allowed(fallback) else None


def target_relations(example: Example) -> list[dict[str, Any]]:
    target = example.get("target", {})
    task_type = example["task_type"]
    if task_type == "relation_completion":
        return [{"source": target.get("source"), "type": target.get("type"), "target": target.get("target")}]
    if task_type == "state_action_effect":
        return target.get("relations_observed", [])
    if task_type == "counterfactual_contrast":
        relation = target.get("contrast_relation")
        return [relation] if isinstance(relation, dict) else []
    if task_type == "explanation_path":
        return target.get("expected_relations", [])
    if task_type in {"graph_anchor_from_prompt", "explanation_with_relations"}:
        return target.get("graph_anchors", [])
    if task_type == "relation_family_from_prompt":
        return [{"source": family_id, "type": "instance_of", "target": "kind"} for family_id in target.get("relation_family_ids", [])]
    if task_type == "node_id_from_paraphrase":
        return [{"source": target.get("node_id"), "type": "instance_of", "target": "thing"}]
    return []


def simple_fact(relation: dict[str, Any]) -> str | None:
    source_id = relation.get("source")
    target_id = relation.get("target")
    rel_type = relation.get("type")
    source = node_text(source_id)
    target = node_text(target_id)
    link = rel_text(rel_type)
    if not source or not link:
        return None

    if rel_type == "directly_controlled_by" and target_id == "concept.self_proto":
        return f"baby can move {source}"
    if rel_type == "not_directly_controlled_by" and target_id == "concept.self_proto":
        return f"baby cannot move {source}"
    if rel_type == "directly_feels":
        return f"baby can feel {source}"
    if rel_type == "can_contact" and target:
        return f"{source} can touch {target}"
    if rel_type == "has_property" and target:
        return f"{source} is {target}"
    if rel_type in {"can_cause", "action_effect", "strengthens_can_cause"} and target:
        return f"{source} can make {target}"
    if rel_type in {"built_from", "future_built_from"} and target:
        return f"{source} from {target}"
    if rel_type in {"contrasts_with", "strengthens_contrast"} and target:
        return f"{source} not same {target}"
    if rel_type in {"binds_to", "strengthens_bind"} and target:
        return f"{source} name {target}"
    if rel_type in {"predicts", "strengthens_predicts"} and target:
        return f"{source} tell {target}"
    if rel_type in {"strengthens", "strengthens_direct_control", "strengthens_has_property"} and target:
        return f"{source} make {target} strong"
    if rel_type in {"supports", "strengthens_supports"} and target:
        return f"{source} help {target}"
    if rel_type in {"instance_of", "strengthens_instance_of"} and target:
        return f"{source} is {target}"
    if rel_type == "uses" and target:
        return f"{source} use {target}"
    if target:
        return f"{source} {link} {target}"
    return None


def facts_for(example: Example) -> list[str]:
    facts: list[str] = []
    for relation in target_relations(example):
        if not isinstance(relation, dict):
            continue
        fact = simple_fact(relation)
        if fact and is_allowed(fact) and fact not in facts:
            facts.append(fact)
    return facts


def scene_from_fact(fact: str) -> str:
    scene = fact
    for old in (" can ", " cannot ", " is ", " from ", " make ", " tell ", " name "):
        scene = scene.replace(old, " ")
    return re.sub(r"\s+", " ", scene).strip()


def unit(unit_id: str, source: Example, stage: str, scene: str, question: str, answer: str, relations: list[str]) -> Unit | None:
    lines = [f"l: {stage}", f"s: {scene}", f"q: {question}", "a:"]
    target = [f"a: {answer}"]
    relation_lines = [f"r: {relation}" for relation in relations if relation]
    text = "\n".join(lines + target + relation_lines)
    if not is_allowed(text):
        return None
    return {
        "id": f"{source['id']}.{stage}.{unit_id}",
        "source_example_id": source["id"],
        "source_task_type": source["task_type"],
        "stage": stage,
        "scene": scene,
        "question": question,
        "answer": answer,
        "relations": relations,
        "metadata": source.get("metadata", {}),
        "graph_id": source.get("graph_id"),
    }


def body_units(example: Example, fact: str, index: int) -> list[Unit]:
    units: list[Unit] = []
    match = re.fullmatch(r"baby can move ([a-z ]+)", fact)
    if match:
        thing = match.group(1)
        units.extend(
            candidate
            for candidate in [
                unit(f"{index}.body.name", example, "f1", fact, "name", "body", [f"{thing} is body"]),
                unit(f"{index}.body.ask", example, "f2", f"{thing} body", f"can baby move {thing}", "yes", [fact]),
                unit(f"{index}.body.later", example, "f3", f"{thing} body", "later name", "own body", ["own body name body"]),
            ]
            if candidate
        )
    match = re.fullmatch(r"baby cannot move ([a-z ]+)", fact)
    if match:
        thing = match.group(1)
        units.extend(
            candidate
            for candidate in [
                unit(f"{index}.notbody.name", example, "f1", fact, "name", "not body", [f"{thing} is not body"]),
                unit(f"{index}.notbody.ask", example, "f2", f"{thing} not body", f"can baby move {thing}", "no", [fact]),
                unit(f"{index}.notbody.later", example, "f3", f"{thing} not body", "later name", "not me", ["not me name not body"]),
            ]
            if candidate
        )
    return units


def person_units(example: Example, fact: str, index: int) -> list[Unit]:
    match = re.fullmatch(r"([a-z ]+) is person", fact)
    if not match:
        return []
    thing = match.group(1)
    return [
        candidate
        for candidate in [
            unit(f"{index}.person.name", example, "f1", fact, "name", "person", [f"{thing} is person"]),
            unit(f"{index}.person.ask", example, "f2", f"{thing} person", f"is {thing} person", "yes", [fact]),
            unit(f"{index}.person.later", example, "f3", f"{thing} person", "later name", "other person", ["other person name person"]),
        ]
        if candidate
    ]


def word_units(example: Example, fact: str, index: int) -> list[Unit]:
    if " name " not in fact:
        return []
    return [
        candidate
        for candidate in [
            unit(f"{index}.word.name", example, "f1", fact, "name", "word", [fact]),
            unit(f"{index}.word.ask", example, "f2", fact, "what kind", "word", [fact]),
        ]
        if candidate
    ]


def units_for(example: Example) -> list[Unit]:
    units: list[Unit] = []
    for index, fact in enumerate(facts_for(example), start=1):
        scene = scene_from_fact(fact)
        f0 = unit(f"{index}.fact", example, "f0", scene, "?", fact, [fact])
        if f0:
            units.append(f0)
        units.extend(body_units(example, fact, index))
        units.extend(person_units(example, fact, index))
        units.extend(word_units(example, fact, index))
    seen: set[tuple[str, str, str, str]] = set()
    unique_units: list[Unit] = []
    for item in units:
        key = (item["stage"], item["scene"], item["question"], item["answer"])
        if key in seen:
            continue
        seen.add(key)
        unique_units.append(item)
    return unique_units


def render_pair(variant: str, item: Unit) -> tuple[str, str]:
    input_lines = [f"l: {item['stage']}", f"s: {item['scene']}", f"q: {item['question']}", "a:"]
    target_lines = [f"a: {item['answer']}"]
    relation_lines = [f"r: {relation}" for relation in item["relations"]]
    if variant == "foundation_plain_text":
        return "\n".join(input_lines), "\n".join(target_lines)
    if variant == "foundation_relation_scaffolded":
        return "\n".join(input_lines), "\n".join(target_lines + relation_lines)
    if variant == "foundation_relation_first_then_text":
        return "\n".join(relation_lines + input_lines), "\n".join(target_lines)
    raise ValueError(f"unknown variant: {variant}")


def make_record(experiment_id: str, variant: str, split_name: str, item: Unit) -> Record:
    input_text, target_text = render_pair(variant, item)
    return {
        "id": f"dataset.{experiment_id}.{variant}.{item['id']}",
        "source_example_id": item["source_example_id"],
        "foundation_unit_id": item["id"],
        "experiment_id": experiment_id,
        "variant": variant,
        "split": split_name,
        "task_type": item["source_task_type"],
        "foundation_stage": item["stage"],
        "input": input_text,
        "target": target_text,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target_text},
        ],
        "metadata": {
            "domain_id": item.get("metadata", {}).get("domain_id"),
            "domain_label": item.get("metadata", {}).get("domain_label"),
            "graph_id": item.get("graph_id"),
            "representation": variant,
            "source_representation": "core5_v0",
            "vocabulary_policy": "staged_foundation_relation_ladder",
        },
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(key, "unknown") for row in rows).items()))


def domain_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row.get("metadata", {}).get("domain_id", "unknown") for row in rows).items()))


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    word_counts: Counter[str] = Counter()
    raw_counts: Counter[str] = Counter()
    for row in rows:
        text = f"{row.get('input', '')}\n{row.get('target', '')}".lower()
        word_counts.update(WORD_RE.findall(text))
        raw_counts.update(RAW_RE.findall(text))
    return {
        "unique_words_alpha": len(word_counts),
        "total_words_alpha": sum(word_counts.values()),
        "unique_raw_whitespace_tokens": len(raw_counts),
        "total_raw_whitespace_tokens": sum(raw_counts.values()),
        "top_words": dict(word_counts.most_common(40)),
    }


def validate_matched(records: dict[str, dict[str, list[Record]]]) -> None:
    for split_name in SPLITS:
        expected: set[str] | None = None
        for variant in VARIANTS:
            unit_ids = {row["foundation_unit_id"] for row in records[variant][split_name]}
            if expected is None:
                expected = unit_ids
            elif unit_ids != expected:
                raise ValueError(f"{split_name}/{variant} unit IDs do not match")


def file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        name: {"path": str(path), "sha256": sha256_file(path)}
        for name, path in sorted(paths.items())
    }


def build_training_config(experiment_id: str, output_dir: Path, dataset_manifest: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "baseline_model": {
            "name": "HuggingFaceTB/SmolLM2-135M",
            "role": "format validation only before nanochat from-scratch training",
            "reason": "Use dry-run compatibility checks; actual foundation test should use nanochat.",
        },
        "dataset_manifest": str(dataset_manifest),
        "output_root": f"runs/{experiment_id}/smollm2_135m",
        "format": {
            "prompt_template": "{input}\n",
            "target_template": "{target}",
        },
        "training": {
            "max_seq_length": 256,
            "num_train_epochs": 3,
            "learning_rate": 5e-5,
            "per_device_train_batch_size": 1,
            "per_device_eval_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "warmup_ratio": 0.03,
            "weight_decay": 0.0,
            "logging_steps": 10,
            "save_total_limit": 2,
            "seed": 1729,
        },
        "frozen_commands": {
            variant: f"python3 scripts/train_tiny_causal_lm.py --config {output_dir / 'training_config.json'} --variant {variant} --dry-run"
            for variant in VARIANTS
        },
        "notes": [
            "This config is for JSONL format checks only.",
            "The intended training path is nanochat from scratch with a shared tokenizer.",
        ],
    }


def copy_if_exists(source: Path, target: Path) -> Path | None:
    if not source.exists():
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("data/developmental_graph/experiments/core5_v0"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/developmental_graph/experiments/core5_v0_foundation"))
    parser.add_argument("--experiment-id", default="core5_v0_foundation")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ensure_output_dir(args.output_dir, args.overwrite)

    source_examples = {split: load_jsonl(args.source_dir / f"{split}.jsonl") for split in SPLITS}
    units_by_split = {
        split: [item for example in examples for item in units_for(example)]
        for split, examples in source_examples.items()
    }
    for split_name, rows in units_by_split.items():
        write_jsonl(args.output_dir / f"{split_name}.jsonl", rows)

    records: dict[str, dict[str, list[Record]]] = {
        variant: {split_name: [] for split_name in SPLITS}
        for variant in VARIANTS
    }
    dataset_paths: dict[str, Path] = {}
    for variant in VARIANTS:
        for split_name in SPLITS:
            rows = [make_record(args.experiment_id, variant, split_name, item) for item in units_by_split[split_name]]
            records[variant][split_name] = rows
            path = args.output_dir / "datasets" / variant / f"{split_name}.jsonl"
            write_jsonl(path, rows)
            dataset_paths[f"{variant}.{split_name}"] = path

    validate_matched(records)

    copied_paths: dict[str, Path] = {}
    for name in ("heldout.json", "heldout_prompts.jsonl"):
        copied = copy_if_exists(args.source_dir / name, args.output_dir / name)
        if copied:
            copied_paths[name.removesuffix(".json").removesuffix(".jsonl")] = copied

    dataset_manifest_path = args.output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "source_experiment_dir": str(args.source_dir),
        "output_dir": str(args.output_dir / "datasets"),
        "allowed_words": sorted(ALLOWED_WORDS),
        "variants": {
            variant: {
                split_name: {
                    "total": len(records[variant][split_name]),
                    "task_type_counts": count_by(records[variant][split_name], "task_type"),
                    "stage_counts": count_by(records[variant][split_name], "foundation_stage"),
                    "domain_counts": domain_counts(records[variant][split_name]),
                    "vocabulary": vocab_stats(records[variant][split_name]),
                }
                for split_name in SPLITS
            }
            for variant in VARIANTS
        },
        "outputs": file_manifest(dataset_paths),
        "notes": [
            "All variants preserve foundation_unit_id and split membership.",
            "f0 shows simple facts before handles.",
            "f1 introduces a handle after support facts.",
            "f2 asks using the handle.",
            "f3 attaches later names to learned handles.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)

    vocabulary_dir = args.output_dir / "vocabulary"
    vocabulary_dir.mkdir(parents=True, exist_ok=True)
    all_train_words: Counter[str] = Counter()
    for variant in VARIANTS:
        for row in records[variant]["train"]:
            all_train_words.update(WORD_RE.findall(f"{row['input']}\n{row['target']}".lower()))
    alpha_vocab_path = vocabulary_dir / "train_alpha_words.txt"
    alpha_vocab_path.write_text("\n".join(sorted(all_train_words)) + "\n")

    training_config_path = args.output_dir / "training_config.json"
    write_json(training_config_path, build_training_config(args.experiment_id, args.output_dir, dataset_manifest_path))

    output_paths = {
        **dataset_paths,
        "dataset_manifest": dataset_manifest_path,
        "training_config": training_config_path,
        "train_alpha_words": alpha_vocab_path,
    }
    output_paths.update(copied_paths)
    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "source_experiment_dir": str(args.source_dir),
        "source_counts": {split: len(rows) for split, rows in source_examples.items()},
        "foundation_policy": {
            "stages": {
                "f0": "simple facts only",
                "f1": "introduce handle from support facts",
                "f2": "ask using handle",
                "f3": "attach later name to learned handle",
            },
            "field_tokens": "l_s_q_a_r",
            "json_targets": "removed",
            "complex_words": "introduced only after support facts where supported",
        },
        "splits": {
            split_name: {
                "total": len(units_by_split[split_name]),
                "stage_counts": count_by(units_by_split[split_name], "stage"),
                "source_task_type_counts": count_by(units_by_split[split_name], "source_task_type"),
            }
            for split_name in SPLITS
        },
        "variants": list(VARIANTS),
        "vocabulary": {
            "allowed_words": len(ALLOWED_WORDS),
            "train_unique_words_all_variants": len(all_train_words),
            "train_alpha_words_path": str(alpha_vocab_path),
        },
        "dataset_manifest": str(dataset_manifest_path),
        "training_config": str(training_config_path),
        "outputs": file_manifest(output_paths),
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
