#!/usr/bin/env python3
"""Create an event-based bridge-600 curriculum.

The earlier bridge600_standalone_meaning_v1 dataset mostly asks direct
dictionary questions such as "What does noise mean?". This variant keeps the
same bridge concepts, but teaches them through short scenes, consequences,
yes/no checks, and why questions so that bridge training is closer to the
root-300 procedural QA surface.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_root_procedural_irregular_qa as root_irregular  # noqa: E402
from create_root_bridge_600_v1 import BRIDGE_CONCEPT_ROWS, sha256_file, write_json, write_jsonl  # noqa: E402
from output_state import retire_output_dir  # noqa: E402


EXPERIMENT_ID = "bridge600_event_meaning_v1"
VARIANT = "bridge600_event_qa"
WORD_RE = re.compile(r"[a-z]+")
SPLITS = ("train", "dev", "test")


def sentence(text: str) -> str:
    return root_irregular.sentence(text)


def lower_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip()).lower()
    if text and text[-1] not in ".?!":
        text += "."
    return text


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite")
    if path.exists() and overwrite:
        retire_output_dir(path)
    path.mkdir(parents=True, exist_ok=True)


def stable_int(*parts: object) -> int:
    return root_irregular.stable_int(*parts)


def unique_bridge_concepts() -> list[tuple[str, str, str, str, str]]:
    seen: set[str] = set()
    rows: list[tuple[str, str, str, str, str]] = []
    for concept, anchor, relation, scene, fact in BRIDGE_CONCEPT_ROWS:
        if concept in seen:
            continue
        seen.add(concept)
        rows.append((concept, anchor, relation, scene, fact))
    return rows


def surface_binding(concept: str, anchor: str) -> dict[str, str]:
    return {
        "surface": concept,
        "root_anchor": anchor,
        "text": f"{concept} attaches near {anchor}",
    }


def relation_text(concept: str, relation: str, anchor: str) -> str:
    return f"{concept} {relation.replace('_', ' ')} {anchor}"


def scene_for(concept: str, anchor: str, relation: str, scene: str, unit_kind: str) -> str:
    base = sentence(scene)
    relation_lc = relation.lower()

    if relation_lc in {"can_be_heard", "makes_sound", "can_be_seen"} or "hear" in scene.lower():
        return sentence(f"The child notices {concept} with a sense. {base} The child pays attention.")
    if relation_lc in {"can_be_touched", "is_feeling"} or "touch" in scene.lower():
        return sentence(f"The hand has a {concept} case. {base} The child notices the touch.")
    if relation_lc == "property":
        return sentence(f"The child notices something with {concept}. {base} The child asks what this property changes.")
    if relation_lc.startswith("part") or relation_lc in {"has_parts", "part", "place"}:
        return sentence(f"The child looks at the {anchor}. {base} The child asks where {concept} belongs.")
    if relation_lc in {"causes_discomfort", "can_cause_discomfort", "caused_by", "can_make", "can_make_comfort", "reduces_hunger", "reduces_tired"}:
        return sentence(f"The baby has a {concept} event. {base} A feeling changes.")
    if relation_lc in {"prevents", "state", "contrasts"}:
        return sentence(f"The child compares {concept} with {anchor}. {base} The situation changes what can happen.")
    if relation_lc in {"action", "event", "process"}:
        return sentence(f"The child sees {concept} happen. {base} The event has an effect.")
    if relation_lc in {"comparison", "quantity"}:
        return sentence(f"Two things are compared. {base} The child must tell what changed.")
    if relation_lc in {"relation", "name", "means"}:
        return sentence(f"The child hears the word {concept}. {base} The word points to a link.")
    if unit_kind == "check":
        return sentence(f"The child sees {concept} in a small event. {base}")
    return sentence(f"The child meets {concept} during play. {base}")


def primary_question(concept: str, anchor: str, relation: str) -> str:
    relation_lc = relation.lower()
    if relation_lc in {"can_be_heard", "makes_sound"}:
        return f"what can the child know about {concept}"
    if relation_lc in {"can_be_seen"}:
        return f"what can the eye do with {concept}"
    if relation_lc in {"can_be_touched", "is_feeling"}:
        return f"what can the hand know about {concept}"
    if relation_lc.startswith("part") or relation_lc == "has_parts":
        return f"where does {concept} belong"
    if relation_lc in {"causes_discomfort", "can_cause_discomfort", "caused_by"}:
        return f"what feeling can {concept} cause"
    if relation_lc in {"can_make", "can_make_comfort", "reduces_hunger", "reduces_tired"}:
        return f"what can {concept} change"
    if relation_lc in {"prevents", "state", "contrasts"}:
        return f"what does {concept} tell us now"
    if relation_lc in {"action", "event", "process"}:
        return f"what happens with {concept}"
    if relation_lc in {"comparison", "quantity"}:
        return f"what does {concept} tell about amount or change"
    return f"what should the child know about {concept}"


def check_question_answer(concept: str, anchor: str, relation: str, fact: str) -> tuple[str, str, str]:
    relation_lc = relation.lower()
    if relation_lc in {"contrasts", "prevents"}:
        return (
            f"is {concept} the same as {anchor}",
            "no",
            fact,
        )
    if relation_lc in {"can_be_heard", "makes_sound"}:
        return (
            f"can {concept} be connected to sound",
            "yes",
            fact,
        )
    if relation_lc in {"can_be_seen", "example"}:
        return (
            f"can the eye learn something from {concept}",
            "yes",
            fact,
        )
    if relation_lc == "can_be_wet":
        return (
            f"can {concept} be wet",
            "yes",
            fact,
        )
    if relation_lc in {"can_be_touched", "is_feeling"}:
        return (
            f"can touch help know {concept}",
            "yes",
            fact,
        )
    if relation_lc == "property":
        return (
            f"does {concept} describe a thing or event",
            "yes",
            fact,
        )
    if relation_lc.startswith("part") or relation_lc in {"has_parts", "part"}:
        return (
            f"is {concept} connected to {anchor}",
            "yes",
            fact,
        )
    if relation_lc in {"causes_discomfort", "can_cause_discomfort", "caused_by"}:
        return (
            f"can {concept} change feeling",
            "yes",
            fact,
        )
    return (
        f"does {concept} connect with {anchor}",
        "yes",
        fact,
    )


def relation_answer_for(concept: str, anchor: str, relation: str, fact: str) -> str:
    relation_lc = relation.lower()
    if relation_lc.startswith("part") or relation_lc in {"has_parts", "part", "place"}:
        return anchor
    if relation_lc in {"can_be_heard", "makes_sound", "kind", "pattern"}:
        return "sound"
    if relation_lc in {"can_be_seen", "example"}:
        return "eye"
    if relation_lc in {"can_be_touched", "is_feeling"}:
        return "touch"
    if relation_lc in {"causes_discomfort", "can_cause_discomfort", "caused_by", "near"}:
        return "bad feeling"
    if relation_lc in {"reduces_hunger", "reduces_tired", "can_make_comfort"}:
        return "comfort"
    if relation_lc in {"comparison", "quantity"}:
        return "amount or change"
    if relation_lc in {"action", "event", "process"}:
        return "event"
    return anchor or fact


def negative_check_question_answer(concept: str, anchor: str, relation: str, fact: str) -> tuple[str, str, str]:
    relation_lc = relation.lower()
    if relation_lc in {"can_be_heard", "makes_sound"}:
        return f"does {concept} tell the child about taste", "no", fact
    if relation_lc in {"can_be_seen", "example"}:
        return f"does {concept} tell the child about sound", "no", fact
    if relation_lc in {"can_be_touched", "is_feeling"}:
        return f"does {concept} tell the child about color", "no", fact
    if relation_lc.startswith("part") or relation_lc in {"has_parts", "part"}:
        return f"is {concept} separate from {anchor}", "no", fact
    if relation_lc in {"causes_discomfort", "can_cause_discomfort", "caused_by", "near"}:
        return f"does {concept} always mean comfort", "no", fact
    if relation_lc in {"reduces_hunger", "reduces_tired", "can_make_comfort"}:
        return f"does {concept} increase bad feeling", "no", fact
    if relation_lc in {"comparison", "quantity"}:
        return f"does {concept} mean no comparison is possible", "no", fact
    if relation_lc in {"contrasts", "prevents"}:
        return f"is {concept} the same as {anchor}", "no", fact
    return f"does {concept} mean no link to {anchor}", "no", fact


def causal_scene_question_answer(
    concept: str,
    anchor: str,
    relation: str,
    fact: str,
) -> tuple[str, str, str, str]:
    """Make bridge concepts act inside root-like causal mini-scenes."""
    relation_lc = relation.lower()
    place_phrase = {
        "under": "under the box",
        "behind": "behind the box",
        "front": "in front of the box",
        "left": "left of the box",
        "right": "right of the box",
        "middle": "in the middle of the mat",
        "top": "on top of the box",
        "bottom": "at the bottom of the box",
        "inside": "inside the box",
        "outside": "outside the box",
        "nearby": "near the child",
    }

    if concept in {"round", "roll"}:
        return (
            "The ball is round. The ball is near the hand. The hand pushes the ball.",
            "does the ball move by rolling",
            "yes",
            fact,
        )

    if concept in {"flat", "edge", "corner", "side"}:
        return (
            f"The block has a {concept}. The block is on the mat. The hand tries to roll the block.",
            "does the block roll easily",
            "no",
            fact,
        )

    if concept in {"squishy", "softness"}:
        return (
            f"The toy is {concept}. The hand presses the toy. The toy shape changes.",
            "what does the hand learn",
            fact,
            fact,
        )

    if concept in {"hardness"}:
        return (
            "The toy is hard. The hand presses the toy. The toy does not change shape.",
            "what does the hand learn",
            fact,
            fact,
        )

    if concept in {"smooth", "rough", "sticky", "slippery"}:
        touch_result = {
            "smooth": "touch feels even",
            "rough": "touch can feel bad",
            "sticky": "the thing stays on the hand",
            "slippery": "the thing can slide from the hand",
        }[concept]
        return (
            f"The hand touches the {concept} thing. The hand moves on the surface. The child notices the skin feeling.",
            "what happens at touch",
            touch_result,
            fact,
        )

    if relation_lc == "quantity":
        return (
            f"There are blocks on the mat. The amount is {concept}. The child checks the amount.",
            "what amount relation is shown",
            fact,
            fact,
        )

    if concept in {"big", "small", "tiny", "long", "short", "size", "weight", "nearer", "farther", "higher", "lower", "brighter", "quieter", "louder", "better", "worse", "stronger", "weaker", "fast", "slow", "weak"}:
        return (
            f"There are two toys. One toy is {concept}. The child compares the two toys.",
            "what does the child compare",
            fact,
            fact,
        )

    if concept in {"simple", "complex"}:
        return (
            f"The child tries a {concept} action. The action has parts. The child checks how many links are needed.",
            "what does the child learn about the action",
            fact,
            fact,
        )

    if concept in {"color", "red", "blue", "green", "yellow", "white", "black", "bright", "visible"}:
        return (
            f"The light is on. The {concept} toy is in front of the child. The child looks.",
            f"can the child see the {concept} toy",
            "yes",
            fact,
        )

    if concept in {"quiet", "audible", "voice", "noise", "music", "rhythm"}:
        return (
            f"The room is quiet. The {concept} happens near the child. The child's ear is working.",
            f"can the child hear the {concept}",
            "yes",
            fact,
        )

    if concept in {"edible"}:
        return (
            "The food is edible. The caregiver gives it to the baby. The baby puts it in the mouth.",
            "can the food be eaten",
            "yes",
            fact,
        )

    if concept in {"touchable", "surface", "back", "wet"}:
        return (
            f"The {concept} thing is near the hand. The hand reaches and touches it. The skin changes feeling.",
            "what sense gives information",
            "touch",
            fact,
        )

    if concept == "diaper":
        return (
            "The diaper is on the body. Water gets on the diaper. The hand checks the diaper.",
            "can the diaper be wet",
            "yes",
            fact,
        )

    if concept in {"under", "behind", "front", "left", "right", "middle", "top", "bottom", "inside", "outside", "nearby"}:
        return (
            f"The toy is {place_phrase[concept]}. The child looks for the toy. The place relation helps the search.",
            "where is the toy",
            fact,
            fact,
        )

    if concept in {"away", "towards"}:
        return (
            f"The toy moves {concept} the child. The child reaches after the move. The distance changes.",
            "what relation changed",
            fact,
            fact,
        )

    if concept in {"openable", "loose"}:
        return (
            f"The box is {concept}. The child opens the box. The toy is inside. The hand reaches in.",
            "can the hand touch the toy",
            "yes",
            f"{fact} and open lets the hand reach inside",
        )

    if concept in {"closable", "locked", "tight"}:
        return (
            f"The box is {concept}. The child tries to open the box. The toy is inside. The hand reaches in.",
            "can the hand touch the toy",
            "no",
            f"{fact} and closed blocks reach",
        )

    if concept in {"hidden", "hide", "cover", "dark", "absent", "missing", "gone"} or relation_lc in {"prevents"}:
        return (
            f"The {concept} thing is near the child. The child looks for the toy. The toy is not visible now.",
            "can the child see the toy",
            "no",
            f"{fact} and not seen means the eye cannot see it",
        )

    if concept in {"empty", "filled"}:
        answer = "no thing is inside" if concept == "empty" else "a thing is inside"
        return (
            f"The child looks inside the cup. The cup is {concept}. The child checks what is inside.",
            "what is inside",
            answer,
            fact,
        )

    if concept in {"moving", "still"}:
        answer = "the toy changes place" if concept == "moving" else "the toy does not change place"
        return (
            f"The child watches the toy. The toy is {concept}. The child checks if the place changes.",
            "does the place change",
            answer,
            fact,
        )

    if concept in {"present", "found", "known", "unknown", "familiar", "unfamiliar", "remember", "forget", "memory", "learning", "interesting", "boring", "curious", "surprise"}:
        return (
            f"The child sees a toy. The toy is {concept} in this moment. The child looks longer or changes attention.",
            "what happens to links in the mind",
            fact,
            fact,
        )

    if concept in {"awake", "dry"}:
        return (
            f"The child compares two body states. One state is {concept}. The other state is different.",
            "are the two states the same",
            "no",
            fact,
        )

    if relation_lc in {"can_be_heard", "makes_sound", "kind", "pattern"}:
        return (
            f"The room is quiet. The {concept} happens near the child. The child's ear is working.",
            f"can the child hear the {concept}",
            "yes",
            fact,
        )

    if relation_lc in {"can_be_seen", "example"}:
        return (
            f"The light is on. The {concept} thing is in front of the child. The child looks.",
            f"can the child see the {concept}",
            "yes",
            fact,
        )

    if relation_lc in {"can_be_touched", "is_feeling"}:
        return (
            f"The hand touches the {concept} thing. The child pays attention to the skin feeling.",
            "what sense gives information",
            "touch",
            fact,
        )

    if relation_lc.startswith("part") or relation_lc in {"has_parts", "part"}:
        return (
            f"The child looks at the {anchor}. The {concept} is seen with it. The child asks about the whole thing.",
            f"is {concept} part of {anchor}",
            "yes",
            fact,
        )

    if concept in {"hunger", "hungry"}:
        return (
            "The baby is hungry. The caregiver gives food. The baby waits.",
            "what changes",
            "hunger is less",
            f"{fact} and food can reduce hunger",
        )

    if concept in {"thirst", "thirsty"}:
        return (
            "The baby is thirsty. The caregiver gives water. The baby waits.",
            "what changes",
            "thirst is less",
            f"{fact} and water can reduce thirst",
        )

    if concept in {"tired"}:
        return (
            "The baby is tired. The caregiver helps the baby rest. The baby waits.",
            "what changes",
            "tired is less",
            f"{fact} and rest can reduce tired feeling",
        )

    if relation_lc == "feels_hunger":
        return (
            "The baby is hungry. The tummy has a hunger feeling. The caregiver gives food.",
            "what feeling changes",
            "hunger is less",
            f"{fact} and food can reduce hunger",
        )

    if relation_lc in {"is_need", "is_need_state"}:
        return (
            f"The baby has a need. The caregiver gives {anchor}. The baby waits.",
            "what changes",
            "need is less",
            f"{fact} and meeting a need can reduce the bad feeling",
        )

    if concept in {"rest", "full", "clean", "comfort", "calm", "soothe", "hugging", "gentle", "warm"} or relation_lc in {"reduces_hunger", "reduces_tired", "can_make_comfort"}:
        return (
            f"The baby has a bad feeling. The caregiver gives {concept}. The baby settles.",
            "what happens to bad feeling",
            "bad feeling is less",
            fact,
        )

    if concept in {"cold", "rough", "hardness", "loud", "dirty", "worse", "bad", "distress", "discomfort"} or relation_lc in {"causes_discomfort", "can_cause_discomfort", "caused_by", "near"}:
        return (
            f"The baby meets {concept}. The body reacts. The caregiver notices the baby is not okay.",
            "what feeling can happen",
            "bad feeling can happen",
            fact,
        )

    if concept in {"quickly", "slowly", "roughly"}:
        return (
            f"The child watches a hand move {concept}. The action changes a thing. The child notices the manner.",
            "how does the action happen",
            fact,
            fact,
        )

    if concept in {"peek", "attention", "expectation"}:
        return (
            f"The child looks at a toy. The child uses {concept}. The eye and mind choose what to follow.",
            "what guides the child",
            fact,
            fact,
        )

    if concept in {"nose", "tongue", "mouth", "arm", "head"}:
        sense_or_body = {
            "nose": "smell",
            "tongue": "taste",
            "mouth": "sound",
            "arm": "move",
            "head": "turn",
        }[concept]
        return (
            f"The child notices the {concept}. The {concept} changes what the child can do. The body gives information.",
            f"what does the {concept} help with",
            sense_or_body,
            fact,
        )

    if concept in {"success", "fail"}:
        return (
            f"The child tries an action. The result is {concept}. The child checks whether the action worked.",
            "did the action work",
            "yes" if concept == "success" else "no",
            fact,
        )

    if concept == "okay":
        return (
            "The baby checks the feeling. The feeling is okay. The caregiver does not need to stop the event.",
            "is the feeling bad",
            "no",
            fact,
        )

    if concept in {"start", "stop"}:
        return (
            f"The child watches an action. The action has a {concept}. The child notices the time relation.",
            "what time relation is shown",
            fact,
            fact,
        )

    if concept == "careful":
        return (
            "The child reaches near a hard thing. The hand moves slowly. The action avoids pain.",
            "what kind of response is this",
            "careful",
            fact,
        )

    if concept == "tone":
        return (
            "The caregiver makes a sound with the voice. The tone is gentle. The baby's feeling changes.",
            "what can tone change",
            "feeling",
            fact,
        )

    if concept in {"request", "response", "share", "take", "offer", "refuse", "accept", "turntaking", "together", "alone"}:
        return (
            f"The child is with another person. The event is {concept}. One person acts and the other reacts.",
            "what social relation is shown",
            fact,
            fact,
        )

    if relation_lc in {"action", "event", "process"} or concept in {"roll", "bounce", "drop", "lift", "press", "carry", "crawl", "sit", "stand", "falling", "feeding", "bath", "nap", "crying", "smiling", "looking", "listening"}:
        return (
            f"The child sees {concept}. A thing changes after the event. The child watches the result.",
            "what happened",
            fact,
            fact,
        )

    if concept in {"approach", "leave", "return", "comes", "leaves", "arrival"}:
        return (
            f"The child watches a person move. The person moves {concept}. The place relation changes.",
            "what happened to place",
            fact,
            fact,
        )

    if concept in {"self", "other", "own", "mine", "yours", "control", "boundary"}:
        return (
            f"The baby tries to move. The {concept} relation is noticed. Some things move with the baby and some do not.",
            "what does the child learn",
            fact,
            fact,
        )

    if concept in {"pattern", "change", "choice", "try", "goal", "want", "response", "together", "alone", "without", "favorite", "group", "part", "whole", "relation", "meaning"}:
        return (
            f"The child watches an event. The event has {concept}. The child checks how one thing links to another.",
            "what relation is active",
            fact,
            fact,
        )

    return (
        f"The child sees a small event with {concept}. The event changes the relation to {anchor}. The child watches what follows.",
        "what relation is active",
        fact,
        fact,
    )


def make_unit(
    *,
    index: int,
    concept: str,
    anchor: str,
    relation: str,
    scene: str,
    fact: str,
    unit_kind: str,
) -> dict[str, Any]:
    fact = fact.strip().lower()
    if unit_kind == "check":
        question, answer, main_fact = check_question_answer(concept, anchor, relation, fact)
        question_type = "relation_check"
        scene_text = scene_for(concept, anchor, relation, scene, unit_kind)
    elif unit_kind == "negative_check":
        question, answer, main_fact = negative_check_question_answer(concept, anchor, relation, fact)
        question_type = "negative_relation_check"
        scene_text = scene_for(concept, anchor, relation, scene, unit_kind)
    elif unit_kind == "causal":
        scene_text, question, answer, main_fact = causal_scene_question_answer(concept, anchor, relation, fact)
        question_type = "causal_event"
    elif unit_kind == "why":
        scene_text, _question, _answer, main_fact = causal_scene_question_answer(concept, anchor, relation, fact)
        question = f"why is {concept} important here"
        answer = main_fact
        question_type = "causal_why"
    elif unit_kind == "effect":
        scene_text, _question, _answer, main_fact = causal_scene_question_answer(concept, anchor, relation, fact)
        question = f"what changes because of {concept}"
        answer = main_fact
        question_type = "causal_effect"
    elif unit_kind == "relation_anchor":
        scene_text, _question, _answer, main_fact = causal_scene_question_answer(concept, anchor, relation, fact)
        question = f"what does {concept} connect with"
        answer = relation_answer_for(concept, anchor, relation, fact)
        question_type = "relation_anchor"
    elif unit_kind == "observation":
        scene_text, _question, _answer, main_fact = causal_scene_question_answer(concept, anchor, relation, fact)
        question = "what does the child observe"
        answer = main_fact
        question_type = "event_observation"
    elif unit_kind == "word_grounding":
        scene_text = scene_for(concept, anchor, relation, scene, unit_kind)
        question = f"what does the word {concept} point to"
        answer = fact
        main_fact = fact
        question_type = "word_grounding"
    else:
        question = primary_question(concept, anchor, relation)
        answer = fact
        main_fact = fact
        question_type = "event_inference"
        scene_text = scene_for(concept, anchor, relation, scene, unit_kind)

    unit_id = f"bridgeevent.v1.{unit_kind}.{index:04d}.{root_irregular.clean_spaces(concept)}"
    return {
        "id": unit_id,
        "rule_family": f"bridge_event_{relation}",
        "question_type": question_type,
        "scene": scene_text,
        "question": root_irregular.question(question),
        "answer": answer.strip().lower(),
        "main_fact": lower_sentence(main_fact),
        "relations": [relation_text(concept, relation, anchor).lower()],
        "negative_relations": [],
        "root_relations": [],
        "negative_root_relations": [],
        "surface_bindings": [surface_binding(concept, anchor)],
        "metadata": {
            "concept": concept,
            "thing": concept,
            "anchor": anchor,
            "relation": relation,
            "question_type": question_type,
            "source_fact": fact,
            "unit_kind": unit_kind,
            "root_seed_id": "root_concept_foundation_v1",
            "bridge_source": "controlled_600_word_bridge",
            "positive": True,
            "outcome": question_type,
        },
    }


def build_units() -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    unit_kinds = (
        "infer",
        "check",
        "negative_check",
        "causal",
        "why",
        "effect",
        "relation_anchor",
        "observation",
        "word_grounding",
    )
    for index, (concept, anchor, relation, scene, fact) in enumerate(unique_bridge_concepts(), 1):
        for unit_kind in unit_kinds:
            units.append(
                make_unit(
                    index=index,
                    concept=concept,
                    anchor=anchor,
                    relation=relation,
                    scene=scene,
                    fact=fact,
                    unit_kind=unit_kind,
                )
            )
    return units


def make_record(split: str, unit: dict[str, Any], surface: dict[str, str], surface_index: int) -> dict[str, Any]:
    target = root_irregular.target_text(unit)
    metadata = {
        **unit["metadata"],
        "domain_id": EXPERIMENT_ID,
        "rule_family": unit["rule_family"],
        "representation": VARIANT,
        "prompt_type": surface["prompt_type"],
        "source_world": EXPERIMENT_ID,
        "evaluation_bucket": split,
        "surface_bindings": unit["surface_bindings"],
        "hidden_root_relations": unit["root_relations"],
        "hidden_negative_root_relations": unit["negative_root_relations"],
        "relations_visible_to_model": False,
        "template_irregular": True,
        "bridge_vocab_locked": True,
    }
    return {
        "id": f"dataset.{EXPERIMENT_ID}.{VARIANT}.{split}.{surface_index:02d}.{surface['prompt_type']}.{unit['id']}",
        "source_example_id": unit["id"],
        "experiment_id": EXPERIMENT_ID,
        "variant": VARIANT,
        "split": split,
        "evaluation_bucket": split,
        "surface_type": surface["prompt_type"],
        "prompt_type": surface["prompt_type"],
        "task_type": unit["rule_family"],
        "input": surface["input"],
        "target": target,
        "messages": [
            {"role": "user", "content": surface["input"]},
            {"role": "assistant", "content": target},
        ],
        "metadata": metadata,
    }


def build_records(split: str, units: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    prompt_indices = {
        "train": {1, 2, 3, 4, 5, 6, 7},
        "dev": {1, 4},
        "test": {2, 5, 7},
    }[split]
    rows: list[dict[str, Any]] = []
    for unit in units:
        scene = root_irregular.irregular_scene(unit)
        surfaces = root_irregular.prompt_surfaces(unit, scene)
        for surface_index, surface in enumerate(surfaces, 1):
            if surface_index not in prompt_indices:
                continue
            rows.append(make_record(split, unit, surface, surface_index))
    random.Random(seed + stable_int(EXPERIMENT_ID, split)).shuffle(rows)
    return rows


def words_in_rows(rows: list[dict[str, Any]]) -> Counter[str]:
    words: Counter[str] = Counter()
    for row in rows:
        words.update(WORD_RE.findall(f"{row['input']}\n{row['target']}".lower()))
    return words


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
        "concept_count": len({row["metadata"]["concept"] for row in rows}),
        "unit_count": len({row["source_example_id"] for row in rows}),
        "task_type_counts": dict(Counter(row["task_type"] for row in rows)),
        "question_type_counts": dict(Counter(row["metadata"]["question_type"] for row in rows)),
        "prompt_conflicts": prompt_conflict_stats(rows),
    }


def readme_text(manifest: dict[str, Any]) -> str:
    train = manifest["splits"]["train"]
    dev = manifest["splits"]["dev"]
    test = manifest["splits"]["test"]
    return f"""# Bridge-600 Event Meaning v1

This dataset turns the controlled bridge-600 concept list into root-style
scene/question/answer training data.

It is meant to fix the earlier bridge weakness: the bridge rows were too close
to dictionary definition training, while root-300 was procedural and causal.
This version keeps the same bridge concepts, but gives each concept nine
units:

- `event_inference`: infer the relation from a short scene.
- `relation_check`: answer a yes/no relation check.
- `causal_event`: apply the concept inside a concrete mini-event.
- `negative_relation_check`: reject an incorrect relation.
- `causal_why`: explain why the concept matters in the event.
- `causal_effect`: state what changes because of the concept.
- `relation_anchor`: name the anchor relation.
- `event_observation`: describe what the child observes.
- `word_grounding`: attach the visible word to the relation bundle.

The relation labels are kept in metadata and are not shown to the model.

## Counts

- Concepts: {manifest["deduped_concept_count"]}
- Units: {manifest["unit_count"]}
- Train rows: {train["rows"]}
- Dev rows: {dev["rows"]}
- Test rows: {test["rows"]}
- Train unique alpha words: {train["unique_alpha_words"]}
- Prompt conflicts: train={train["prompt_conflicts"]["ambiguous_inputs"]}, dev={dev["prompt_conflicts"]["ambiguous_inputs"]}, test={test["prompt_conflicts"]["ambiguous_inputs"]}

## Generated Files

- `datasets/{VARIANT}/train.jsonl`
- `datasets/{VARIANT}/dev.jsonl`
- `datasets/{VARIANT}/test.jsonl`
- `datasets/manifest.json`
- `training_config.json`
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/bridge600_event_meaning_v1"),
    )
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ensure_output_dir(args.output_dir, args.overwrite)
    units = build_units()
    records = {split: build_records(split, units, args.seed) for split in SPLITS}

    dataset_dir = args.output_dir / "datasets" / VARIANT
    output_paths: dict[str, Path] = {}
    for split, rows in records.items():
        path = dataset_dir / f"{split}.jsonl"
        write_jsonl(path, rows)
        write_jsonl(args.output_dir / f"{split}.jsonl", rows)
        output_paths[split] = path

    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": EXPERIMENT_ID,
        "variant": VARIANT,
        "source": "BRIDGE_CONCEPT_ROWS from root_bridge_600_v1",
        "source_concept_rows": len(BRIDGE_CONCEPT_ROWS),
        "deduped_concept_count": len(unique_bridge_concepts()),
        "unit_count": len(units),
        "splits": {split: split_stats(rows) for split, rows in records.items()},
        "outputs": {
            split: {"path": str(path), "sha256": sha256_file(path)}
            for split, path in sorted(output_paths.items())
        },
        "notes": [
            "Event-based bridge-600 curriculum; no root-300 rows are included.",
            "Same bridge concepts as bridge600_standalone_meaning_v1.",
            "Rows use root-style scene/question/answer surfaces instead of direct dictionary prompts.",
            "Each concept has event_inference, relation_check, and causal_event units.",
            "The causal_event units avoid generic small-event fallback phrasing.",
            "Relations remain hidden in metadata.",
        ],
    }
    write_json(args.output_dir / "datasets" / "manifest.json", manifest)
    (args.output_dir / "README.md").write_text(readme_text(manifest), encoding="utf-8")
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
            "unique_train_alpha_words": manifest["splits"]["train"]["unique_alpha_words"],
        },
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
