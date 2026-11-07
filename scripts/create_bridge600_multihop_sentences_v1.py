#!/usr/bin/env python3
"""Create a harder bridge-600 curriculum with scene and multi-hop questions.

The earlier bridge600_standalone_meaning_v1 dataset checks whether a small
model can learn direct word meanings. This variant checks whether the model can
use those meanings in short real-world scenes.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_root_bridge_600_v1 import sha256_file, write_json, write_jsonl  # noqa: E402
from output_state import retire_output_dir  # noqa: E402


EXPERIMENT_ID = "bridge600_multihop_sentences_v1"
VARIANT = "bridge600_multihop_qa"
WORD_RE = re.compile(r"[a-z]+")


@dataclass(frozen=True)
class Case:
    family: str
    scene: str
    question: str
    answer: str
    reason: str
    concepts: tuple[str, ...]
    hops: tuple[str, ...]


TRAIN_PROMPTS = (
    "{scene}\nQuestion: {question}\nAnswer:",
    "Read this event. {scene}\nNow answer: {question}\nAnswer:",
    "A child sees this happen: {scene}\nAnswer the question: {question}\nAnswer:",
    "Use the situation, not a dictionary. {scene}\nQuestion: {question}\nAnswer:",
    "Scene: {scene}\nQuestion: {question}\nGive the answer and reason:",
    "Here is a small world event. {scene}\n{question}\nSo the answer is:",
    "Think about the relation in this event. {scene}\nQuestion: {question}\nAnswer:",
    "This is the whole situation: {scene}\nWhat should be inferred? {question}\nAnswer:",
)

DEV_PROMPTS = (
    "New scene: {scene}\nWhat should we infer? {question}\nAnswer:",
    "Think through the event. {scene}\nQuestion: {question}\nAnswer:",
)

TEST_PROMPTS = (
    "In the room, {scene}\nNow answer this: {question}\nReply:",
    "The child notices: {scene}\nWhat is likely true? {question}\nAnswer:",
    "Short story: {scene}\nQuestion: {question}\nSo the answer is:",
)


OBJECTS = ("toy", "block", "cup", "spoon", "book", "blanket", "towel", "shirt", "shoe", "hat", "ball", "pillow")
SOFT_OBJECTS = ("pillow", "blanket", "towel", "soft toy", "soft ball", "shirt")
HARD_OBJECTS = ("block", "cup", "spoon", "book", "hard toy", "small box")
CONTAINERS = ("box", "basket", "drawer", "cupboard", "bag", "bucket")
PEOPLE = ("caregiver", "mom", "dad")


def sentence(text: str) -> str:
    text = " ".join(text.strip().split())
    return text if text.endswith(".") else f"{text}."


def target_text(answer: str, reason: str) -> str:
    return f"answer: {sentence(answer.lower())}\nreason: {sentence(reason.lower())}"


def add_case(
    cases: list[Case],
    *,
    family: str,
    scene: str,
    question: str,
    answer: str,
    reason: str,
    concepts: tuple[str, ...],
    hops: tuple[str, ...],
) -> None:
    cases.append(
        Case(
            family=family,
            scene=sentence(scene),
            question=question.strip().rstrip("?") + "?",
            answer=answer,
            reason=reason,
            concepts=concepts,
            hops=hops,
        )
    )


def build_cases() -> list[Case]:
    cases: list[Case] = []

    for action in ("pushes", "kicks", "presses", "rolls", "throws"):
        for place in ("floor", "mat", "rug"):
            add_case(
                cases,
                family="ball_action_roll",
                scene=f"The child {action} the ball on the {place}.",
                question="what may happen to the ball",
                answer="the ball may roll",
                reason="a ball can roll and the action can make it move",
                concepts=("ball", "roll", "move", place),
                hops=("ball can roll", f"{action} can make move", "moving can change place"),
            )
        add_case(
            cases,
            family="ball_action_bounce",
            scene=f"The child {action} the ball toward the wall.",
            question="what may happen after the ball hits the wall",
            answer="the ball may bounce",
            reason="a ball can bounce after a hit",
            concepts=("ball", "bounce", "hit"),
            hops=("ball can bounce", "hit can happen before bounce"),
        )

    for cover in ("blanket", "towel", "cloth", "shirt"):
        for thing in ("toy", "block", "cup", "spoon", "book", "ball"):
            add_case(
                cases,
                family="cover_hide_seen",
                scene=f"The {cover} is put over the {thing}. The child looks for the {thing}.",
                question=f"can the child see the {thing} now",
                answer=f"no, the {thing} is hidden",
                reason=f"a cover can hide a thing and hidden means not seen",
                concepts=("cover", "hide", "hidden", "see"),
                hops=("cover can hide", "hidden means not seen", "eye sees visible things"),
            )

    for container in CONTAINERS:
        for thing in ("toy", "block", "spoon", "cup", "ball"):
            add_case(
                cases,
                family="open_container_reach",
                scene=f"The {thing} is inside the open {container}. The hand reaches in.",
                question=f"can the hand touch the {thing}",
                answer=f"yes, the hand can touch the {thing}",
                reason=f"open lets the hand reach inside",
                concepts=("inside", "open", "touch", "hand"),
                hops=("inside is in container", "open lets touch happen", "hand can reach"),
            )
            add_case(
                cases,
                family="closed_container_block",
                scene=f"The {thing} is inside the closed {container}. The hand reaches in.",
                question=f"can the hand touch the {thing}",
                answer=f"no, the closed {container} blocks touch",
                reason=f"closed stops the hand from reaching inside",
                concepts=("inside", "closed", "touch", "hand"),
                hops=("inside is in container", "closed stops touch", "hand cannot reach through closed container"),
            )

    for thing in OBJECTS:
        add_case(
            cases,
            family="near_far_touch",
            scene=f"The {thing} is near the hand. The baby reaches.",
            question=f"does the hand touch the {thing}",
            answer=f"yes, the hand can touch the {thing}",
            reason=f"near lets reaching end in touch",
            concepts=("near", "hand", "touch", "reach"),
            hops=("near supports touch", "hand can reach", "touch happens at contact"),
        )
        add_case(
            cases,
            family="near_far_touch",
            scene=f"The {thing} is far from the hand. The baby reaches.",
            question=f"does the hand touch the {thing}",
            answer=f"no, the hand does not touch the {thing}",
            reason=f"far stops touch",
            concepts=("far", "hand", "touch", "reach"),
            hops=("far stops touch", "hand can reach only near things"),
        )

    for thing in HARD_OBJECTS:
        add_case(
            cases,
            family="hard_hit_pain",
            scene=f"The {thing} is hard. It falls onto the hand.",
            question="what feeling may happen",
            answer="pain may happen",
            reason="hardness can make hit hurt",
            concepts=("hardness", "hard", "fall", "hit", "pain"),
            hops=("fall can cause hit", "hardness can hurt", "hurt is near pain"),
        )
    for thing in SOFT_OBJECTS:
        add_case(
            cases,
            family="soft_hit_less_pain",
            scene=f"The {thing} is soft. It falls onto the hand.",
            question="what feeling may happen",
            answer="less pain may happen",
            reason="softness can reduce hurt",
            concepts=("softness", "soft", "fall", "hurt", "pain"),
            hops=("fall can cause hit", "softness reduces hurt", "less hurt means less pain"),
        )

    for scene, cause in (
        ("The towel feels rough on the baby's skin.", "rough touch"),
        ("The spoon feels cold on the baby's hand.", "cold touch"),
        ("A loud noise happens near the baby.", "loud sound"),
        ("The shirt is dirty and touches the baby's skin.", "dirty touch"),
        ("The baby has hunger and no milk yet.", "hunger"),
    ):
        add_case(
            cases,
            family="bad_feeling_causes_discomfort",
            scene=scene,
            question="what feeling may follow",
            answer="discomfort may follow",
            reason=f"{cause} can cause discomfort",
            concepts=("rough", "cold", "loud", "dirty", "hunger", "discomfort"),
            hops=(f"{cause} can cause discomfort", "discomfort is bad feeling"),
        )

    for action in ("gentle touch", "warm touch", "hugging", "soothing voice", "soft singing", "slow rocking"):
        add_case(
            cases,
            family="comfort_calm",
            scene=f"The caregiver gives the baby {action}.",
            question="what feeling may follow",
            answer="comfort may follow",
            reason=f"{action} can bring comfort",
            concepts=("caregiver", "gentle", "warm", "hugging", "soothe", "comfort", "calm"),
            hops=(f"{action} can bring comfort", "comfort can make calm"),
        )

    for need, fix, result in (
        ("hunger", "milk", "hunger is less"),
        ("thirst", "water", "thirst is less"),
        ("tired feeling", "rest", "tired feeling is less"),
    ):
        add_case(
            cases,
            family="need_reduction",
            scene=f"The baby has {need}. The caregiver gives {fix}.",
            question="what changes",
            answer=result,
            reason=f"{fix} can reduce the need",
            concepts=("hunger", "thirst", "tired", "milk", "water", "rest"),
            hops=(f"{need} is a need state", f"{fix} reduces the need", "less need reduces discomfort"),
        )

    for body_part in ("hand", "arm", "head", "foot", "leg"):
        add_case(
            cases,
            family="self_control",
            scene=f"The baby tries to move the {body_part}. The {body_part} moves after the try.",
            question=f"is the {body_part} part of self",
            answer=f"yes, the {body_part} is part of self",
            reason=f"control follows try and self is controlled body",
            concepts=("self", "control", "try", "body"),
            hops=("control follows try", "self is controlled body", f"{body_part} is body part"),
        )
    for person in PEOPLE:
        add_case(
            cases,
            family="other_not_controlled",
            scene=f"The baby tries to move the {person}. The {person} does not move after the try.",
            question=f"is the {person} self or other",
            answer=f"the {person} is other",
            reason=f"other is not controlled by the baby",
            concepts=("other", "control", "self"),
            hops=("other is not controlled", "self is controlled body"),
        )

    for thing in ("song", "face", "toy", "game", "voice", "sound"):
        sense_action = "hears" if thing in {"song", "voice", "sound"} else "sees"
        add_case(
            cases,
            family="repeat_memory_familiar",
            scene=f"The child {sense_action} the same {thing} again and again.",
            question=f"what can the {thing} become",
            answer=f"the {thing} can become familiar",
            reason=f"familiar comes from again and again",
            concepts=("repeat", "again", "memory", "familiar", "known"),
            hops=("repeat means again", "familiar comes from again", "memory keeps link"),
        )

    for thing in ("new sound", "new toy", "new game", "new face", "new song", "new shape"):
        add_case(
            cases,
            family="new_learning_interest",
            scene=f"The child notices a {thing} and looks longer.",
            question="what may be happening",
            answer="learning may be happening",
            reason="interesting things can make new links and learning makes new links",
            concepts=("interesting", "curious", "learning", "new", "link"),
            hops=("interesting can make new link", "curious wants new link", "learning makes new links"),
        )

    for thing in ("cup", "box", "basket", "drawer", "bag"):
        add_case(
            cases,
            family="empty_filled_inside",
            scene=f"The child looks inside the {thing}. There is no toy inside.",
            question=f"is the {thing} empty or filled",
            answer=f"the {thing} is empty",
            reason=f"empty means no thing inside",
            concepts=("inside", "empty", "filled"),
            hops=("inside is in container", "empty has no inside thing"),
        )
        add_case(
            cases,
            family="empty_filled_inside",
            scene=f"The child looks inside the {thing}. A toy is inside.",
            question=f"is the {thing} empty or filled",
            answer=f"the {thing} is filled",
            reason=f"filled means something is inside",
            concepts=("inside", "empty", "filled"),
            hops=("inside is in container", "filled has inside thing"),
        )

    for group in ("blocks", "cups", "toys", "books", "balls"):
        add_case(
            cases,
            family="part_group_whole",
            scene=f"The child sees many {group} together. One {group[:-1]} is taken away.",
            question="what changed",
            answer="one part left the group",
            reason="a group has many things and a part belongs to a whole",
            concepts=("group", "many", "one", "part", "whole"),
            hops=("group has many", "one means single", "part belongs to thing", "whole means all parts"),
        )

    for want, signal in (("milk", "crying"), ("toy", "reaching"), ("hug", "request"), ("water", "sound"), ("book", "pointing")):
        add_case(
            cases,
            family="request_response_want",
            scene=f"The child wants {want}. The child shows a {signal}. The caregiver answers.",
            question="what happened after the signal",
            answer="a response happened",
            reason="a response happens after a signal and a request shows want",
            concepts=("want", "request", "response", "signal", "caregiver"),
            hops=("want moves toward thing", "request shows want", "response is after signal"),
        )

    for unsafe in ("sharp edge", "hot cup", "hard block", "rough floor", "falling spoon"):
        add_case(
            cases,
            family="careful_avoid_pain",
            scene=f"The child moves near the {unsafe}. The caregiver moves the hand away.",
            question="why is this careful",
            answer="careful action can reduce pain",
            reason="avoid means move away from pain and careful reduces pain",
            concepts=("careful", "avoid", "away", "pain"),
            hops=("avoid moves away from pain", "careful reduces pain"),
        )

    return cases


def row_for_case(split: str, case: Case, prompt: str, prompt_index: int, case_index: int) -> dict[str, Any]:
    input_text = prompt.format(scene=case.scene, question=case.question)
    target = target_text(case.answer, case.reason)
    row_id = f"dataset.{EXPERIMENT_ID}.{VARIANT}.{split}.{case_index:04d}.{prompt_index:02d}.{case.family}"
    return {
        "id": row_id,
        "source_example_id": f"bridge600.multihop.{case_index:04d}.{case.family}",
        "experiment_id": EXPERIMENT_ID,
        "variant": VARIANT,
        "split": split,
        "evaluation_bucket": split,
        "surface_type": f"multihop_template_{prompt_index:02d}",
        "prompt_type": f"multihop_template_{prompt_index:02d}",
        "task_type": case.family,
        "input": input_text,
        "target": target,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target},
        ],
        "metadata": {
            "domain_id": EXPERIMENT_ID,
            "representation": VARIANT,
            "relations_visible_to_model": False,
            "case_family": case.family,
            "concepts": list(case.concepts),
            "hidden_relation_chain": list(case.hops),
            "scene": case.scene,
            "question": case.question,
            "answer": sentence(case.answer.lower()),
            "reason": sentence(case.reason.lower()),
            "multihop": len(case.hops) >= 2,
        },
    }


def split_cases_by_family(cases: list[Case], seed: int) -> dict[str, list[Case]]:
    by_family: dict[str, list[Case]] = defaultdict(list)
    for case in cases:
        by_family[case.family].append(case)

    splits: dict[str, list[Case]] = {"train": [], "dev": [], "test": []}
    rng = random.Random(seed)
    for family, family_cases in sorted(by_family.items()):
        shuffled = list(family_cases)
        rng.shuffle(shuffled)
        count = len(shuffled)
        if count >= 5:
            dev_count = max(1, round(count * 0.15))
            test_count = max(1, round(count * 0.15))
        elif count >= 3:
            dev_count = 1
            test_count = 1
        elif count == 2:
            dev_count = 0
            test_count = 1
        else:
            dev_count = 0
            test_count = 0
        train_count = max(1, count - dev_count - test_count)
        splits["train"].extend(shuffled[:train_count])
        splits["dev"].extend(shuffled[train_count : train_count + dev_count])
        splits["test"].extend(shuffled[train_count + dev_count :])

    for split in splits:
        rng.shuffle(splits[split])
    return splits


def build_rows(cases: list[Case], split: str, prompts: tuple[str, ...], seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_index, case in enumerate(cases, 1):
        for prompt_index, prompt in enumerate(prompts, 1):
            rows.append(row_for_case(split, case, prompt, prompt_index, case_index))
    random.Random(seed + {"train": 1, "dev": 2, "test": 3}[split]).shuffle(rows)
    return rows


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite")
    if path.exists() and overwrite:
        retire_output_dir(path)
    path.mkdir(parents=True, exist_ok=True)


def words_in_rows(rows: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(WORD_RE.findall(f"{row['input']}\n{row['target']}".lower()))
    return counter


def prompt_conflict_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets_by_input: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        targets_by_input[row["input"]].add(row["target"])
    return {
        "unique_inputs": len(targets_by_input),
        "ambiguous_inputs": sum(1 for targets in targets_by_input.values() if len(targets) > 1),
    }


def split_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    words = words_in_rows(rows)
    return {
        "rows": len(rows),
        "unique_alpha_words": len(words),
        "total_alpha_words": sum(words.values()),
        "task_type_counts": dict(Counter(row["task_type"] for row in rows)),
        "prompt_conflicts": prompt_conflict_stats(rows),
        "families": sorted({row["metadata"]["case_family"] for row in rows}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/bridge600_multihop_sentences_v1"),
    )
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ensure_output_dir(args.output_dir, args.overwrite)
    cases = build_cases()
    case_splits = split_cases_by_family(cases, args.seed)
    records = {
        "train": build_rows(case_splits["train"], "train", TRAIN_PROMPTS, args.seed),
        "dev": build_rows(case_splits["dev"], "dev", DEV_PROMPTS, args.seed),
        "test": build_rows(case_splits["test"], "test", TEST_PROMPTS, args.seed),
    }

    dataset_dir = args.output_dir / "datasets" / VARIANT
    output_paths: dict[str, Path] = {}
    for split, rows in records.items():
        path = dataset_dir / f"{split}.jsonl"
        write_jsonl(path, rows)
        output_paths[split] = path
        write_jsonl(args.output_dir / f"{split}.jsonl", rows)

    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": EXPERIMENT_ID,
        "variant": VARIANT,
        "source": "hand-authored multi-hop schemas over bridge/root concepts",
        "case_count": len(cases),
        "case_splits": {split: len(split_cases) for split, split_cases in case_splits.items()},
        "splits": {split: split_stats(rows) for split, rows in records.items()},
        "outputs": {
            split: {"path": str(path), "sha256": sha256_file(path)}
            for split, path in sorted(output_paths.items())
        },
        "notes": [
            "This variant tests relation use in short real-world scenes, not direct dictionary recall.",
            "The model sees only scene/question text; relation chains are hidden in metadata.",
            "Train, dev, and test use separate held-out scene cases and separate prompt wrappers.",
            "Targets keep answer/reason format so existing nanochat evaluators can run.",
        ],
    }
    write_json(args.output_dir / "datasets" / "manifest.json", manifest)
    write_json(
        args.output_dir / "training_config.json",
        {
            "schema_version": "0.1.0",
            "experiment_id": EXPERIMENT_ID,
            "dataset_manifest": str(args.output_dir / "datasets" / "manifest.json"),
            "format": {"prompt_template": "{input}\n", "target_template": "{target}"},
            "training": {"max_seq_length": 256, "seed": args.seed, "recommended_depth": 4},
        },
    )
    write_json(
        args.output_dir / "manifest.json",
        {
            "schema_version": "0.1.0",
            "experiment_id": EXPERIMENT_ID,
            "variant": VARIANT,
            "dataset_manifest": str(args.output_dir / "datasets" / "manifest.json"),
            "training_config": str(args.output_dir / "training_config.json"),
            "record_splits": {split: len(rows) for split, rows in records.items()},
            "case_count": len(cases),
            "unique_train_alpha_words": manifest["splits"]["train"]["unique_alpha_words"],
        },
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
