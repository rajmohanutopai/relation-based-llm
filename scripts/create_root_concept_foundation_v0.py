#!/usr/bin/env python3
"""Create the root concept foundation curriculum.

This is the first stage of the TinyStories relation-first path:

1. teach root concepts and inheritance patterns
2. later attach TinyStories words to those roots
3. then train on raw TinyStories text

The important design point is compression. A later word such as "puppy" should
not be defined by repeating every animal fact. It should attach to anchors such
as animal, young, pet, body, pain, sound, and happy. This generator builds the
root anchors and the inheritance/consequence training examples needed for that
attachment step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ID = "root_concept_foundation_v0"
SCHEMA_VERSION = "0.1.0"
SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = ("root_prose", "root_qa", "root_mixed")
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")


LAYERS = [
    ("root", 0, "Root", "Most general anchors: thing, relation, event, state."),
    ("sensory", 1, "Sensory Channels", "Touch, sight, sound, taste, smell, body feeling."),
    ("body_self", 2, "Body And Self", "Body parts, control, direct feeling, proto-self."),
    ("space", 3, "Space", "Near, far, up, down, inside, outside, on, under."),
    ("physical", 4, "Physical Process", "Move, touch, fall, block, push, pull, open, closed."),
    ("property", 5, "Object Properties", "Hard, soft, hot, cold, wet, dry, big, small."),
    ("living", 6, "Living Things", "Living thing, person, animal, plant, young, adult."),
    ("need_valence", 7, "Need And Valence", "Pain, comfort, food, water, sleep, good, bad."),
    ("emotion", 8, "Emotion", "Happy, sad, afraid, angry, want."),
    ("social", 9, "Social", "Caregiver, help, hurt, give, take, share, pet."),
    ("language", 10, "Language", "Word, name, say, hear, story, question, answer."),
    ("time_change", 11, "Time And Change", "Before, after, cause, effect, again, stop, start."),
]


NODES = [
    ("concept.thing", "thing", "root", "concept", "anything that can be related to another thing"),
    ("concept.relation", "relation", "root", "concept", "a link between things; the project meaning primitive"),
    ("concept.event", "event", "root", "concept", "something that happens"),
    ("concept.state", "state", "root", "concept", "how something is now"),
    ("concept.object", "object", "root", "concept", "a thing that can be touched or moved"),
    ("concept.place", "place", "root", "concept", "where things can be"),
    ("sense.touch", "touch", "sensory", "channel", "contact felt through body"),
    ("sense.sight", "see", "sensory", "channel", "light and shape input"),
    ("sense.sound", "hear", "sensory", "channel", "sound input"),
    ("sense.taste", "taste", "sensory", "channel", "mouth chemical input"),
    ("sense.smell", "smell", "sensory", "channel", "nose chemical input"),
    ("sense.body_feel", "body feel", "sensory", "channel", "inside body and control feeling"),
    ("self.proto_self", "self", "body_self", "concept", "things directly controlled and directly felt"),
    ("body.body", "body", "body_self", "object", "the controlled living body"),
    ("body.hand", "hand", "body_self", "object", "body part used to reach, touch, push, pull"),
    ("body.mouth", "mouth", "body_self", "object", "body part used to eat, taste, cry, speak"),
    ("body.eye", "eye", "body_self", "object", "body part used to see"),
    ("body.ear", "ear", "body_self", "object", "body part used to hear"),
    ("body.nose", "nose", "body_self", "object", "body part used to smell"),
    ("body.skin", "skin", "body_self", "object", "body surface that feels touch and pain"),
    ("body.leg", "leg", "body_self", "object", "body part used to move from place to place"),
    ("space.near", "near", "space", "relation_anchor", "small distance"),
    ("space.far", "far", "space", "relation_anchor", "large distance"),
    ("space.up", "up", "space", "relation_anchor", "higher place"),
    ("space.down", "down", "space", "relation_anchor", "lower place"),
    ("space.inside", "inside", "space", "relation_anchor", "in a container or boundary"),
    ("space.outside", "outside", "space", "relation_anchor", "not inside a boundary"),
    ("space.on", "on", "space", "relation_anchor", "supported by surface"),
    ("space.under", "under", "space", "relation_anchor", "below something"),
    ("physical.move", "move", "physical", "process", "change place"),
    ("physical.touch", "touch", "physical", "process", "make contact"),
    ("physical.fall", "fall", "physical", "process", "move down without support"),
    ("physical.hit", "hit", "physical", "process", "strong contact"),
    ("physical.block", "block", "physical", "process", "stop movement or access"),
    ("physical.push", "push", "physical", "process", "move away by force"),
    ("physical.pull", "pull", "physical", "process", "move toward by force"),
    ("physical.open", "open", "physical", "state", "allows entry or movement"),
    ("physical.closed", "closed", "physical", "state", "blocks entry or movement"),
    ("physical.hold", "hold", "physical", "process", "keep in hand or arms"),
    ("property.hard", "hard", "property", "property", "does not change shape easily"),
    ("property.soft", "soft", "property", "property", "changes shape easily"),
    ("property.hot", "hot", "property", "property", "high temperature"),
    ("property.cold", "cold", "property", "property", "low temperature"),
    ("property.wet", "wet", "property", "property", "has water on it"),
    ("property.dry", "dry", "property", "property", "does not have water on it"),
    ("property.big", "big", "property", "property", "large size"),
    ("property.small", "small", "property", "property", "little size"),
    ("property.heavy", "heavy", "property", "property", "hard to lift or move"),
    ("property.light", "light", "property", "property", "easy to lift or move"),
    ("property.sharp", "sharp", "property", "property", "can cut or hurt"),
    ("property.round", "round", "property", "property", "curved shape that can roll"),
    ("living.living_thing", "living thing", "living", "category", "thing that can grow or need"),
    ("living.person", "person", "living", "category", "living thing with social agency"),
    ("living.animal", "animal", "living", "category", "living thing that can move and feel"),
    ("living.plant", "plant", "living", "category", "living thing that grows but usually does not move like animal"),
    ("living.child", "child", "living", "category", "young person"),
    ("living.adult", "adult", "living", "category", "grown person"),
    ("living.young_animal", "young animal", "living", "category", "young animal, often small and dependent"),
    ("need.food", "food", "need_valence", "need", "what living things eat"),
    ("need.water", "water", "need_valence", "need", "what living things drink"),
    ("need.sleep", "sleep", "need_valence", "need", "rest needed by living things"),
    ("need.air", "air", "need_valence", "need", "what living things breathe"),
    ("valence.pain", "pain", "need_valence", "valence", "bad body feeling from hurt"),
    ("valence.comfort", "comfort", "need_valence", "valence", "body and situation feel okay"),
    ("valence.good", "good", "need_valence", "valence", "toward happiness or okay state"),
    ("valence.bad", "bad", "need_valence", "valence", "toward pain, danger, or loss"),
    ("emotion.happy", "happy", "emotion", "emotion", "positive feeling"),
    ("emotion.sad", "sad", "emotion", "emotion", "negative feeling from loss, pain, or broken relation"),
    ("emotion.afraid", "afraid", "emotion", "emotion", "negative feeling from possible danger"),
    ("emotion.angry", "angry", "emotion", "emotion", "negative feeling when wanted state is blocked"),
    ("emotion.want", "want", "emotion", "emotion", "pull toward a state or object"),
    ("social.caregiver", "caregiver", "social", "role", "person who protects, feeds, comforts"),
    ("social.mom", "mom", "social", "role", "familiar caregiver"),
    ("social.dad", "dad", "social", "role", "familiar caregiver"),
    ("social.help", "help", "social", "action", "action that reduces problem or pain"),
    ("social.hurt", "hurt", "social", "action", "action that causes pain or damage"),
    ("social.give", "give", "social", "action", "move object from one person to another"),
    ("social.take", "take", "social", "action", "get object from another place or person"),
    ("social.share", "share", "social", "action", "let another person use or have too"),
    ("social.role", "role", "social", "role", "a social position that changes expected relations"),
    ("social.pet", "pet", "social", "role", "animal living near people and cared for by people"),
    ("language.word", "word", "language", "symbol", "sound or text that can name a concept"),
    ("language.name", "name", "language", "symbol", "word used for a thing or person"),
    ("language.say", "say", "language", "action", "make words by mouth"),
    ("language.hear_word", "hear word", "language", "event", "sound word reaches listener"),
    ("language.story", "story", "language", "structure", "words describing events and relations"),
    ("language.question", "question", "language", "structure", "words asking for a relation or state"),
    ("language.answer", "answer", "language", "structure", "words giving a relation or state"),
    ("time.before", "before", "time_change", "time", "earlier state"),
    ("time.after", "after", "time_change", "time", "later state"),
    ("time.cause", "cause", "time_change", "relation", "earlier relation makes later relation"),
    ("time.effect", "effect", "time_change", "relation", "later relation caused by earlier relation"),
    ("time.again", "again", "time_change", "time", "same event repeats"),
    ("time.start", "start", "time_change", "time", "begin event"),
    ("time.stop", "stop", "time_change", "time", "end event or movement"),
]


RELATIONS = [
    ("concept.object", "is_a", "concept.thing", 0.95, "neutral"),
    ("concept.place", "is_a", "concept.thing", 0.90, "neutral"),
    ("concept.event", "has_part", "concept.relation", 0.90, "neutral"),
    ("concept.state", "has_part", "concept.relation", 0.90, "neutral"),
    ("body.body", "is_a", "concept.object", 0.95, "neutral"),
    ("body.hand", "part_of", "body.body", 0.95, "neutral"),
    ("body.mouth", "part_of", "body.body", 0.95, "neutral"),
    ("body.eye", "part_of", "body.body", 0.95, "neutral"),
    ("body.ear", "part_of", "body.body", 0.95, "neutral"),
    ("body.nose", "part_of", "body.body", 0.95, "neutral"),
    ("body.skin", "part_of", "body.body", 0.95, "neutral"),
    ("body.leg", "part_of", "body.body", 0.95, "neutral"),
    ("body.hand", "directly_controlled_by", "self.proto_self", 0.95, "positive"),
    ("body.mouth", "directly_controlled_by", "self.proto_self", 0.80, "positive"),
    ("body.leg", "directly_controlled_by", "self.proto_self", 0.75, "positive"),
    ("body.skin", "directly_feels", "sense.touch", 0.95, "neutral"),
    ("body.skin", "directly_feels", "valence.pain", 0.95, "negative"),
    ("body.eye", "uses_channel", "sense.sight", 0.95, "neutral"),
    ("body.ear", "uses_channel", "sense.sound", 0.95, "neutral"),
    ("body.nose", "uses_channel", "sense.smell", 0.90, "neutral"),
    ("body.mouth", "uses_channel", "sense.taste", 0.90, "neutral"),
    ("body.body", "uses_channel", "sense.body_feel", 0.85, "neutral"),
    ("body.mouth", "can_cause", "language.say", 0.70, "neutral"),
    ("body.hand", "can_cause", "physical.touch", 0.95, "neutral"),
    ("body.hand", "can_cause", "physical.push", 0.85, "neutral"),
    ("body.hand", "can_cause", "physical.pull", 0.85, "neutral"),
    ("space.near", "enables", "physical.touch", 0.95, "neutral"),
    ("space.far", "blocks", "physical.touch", 0.90, "negative"),
    ("space.up", "contrasts_with", "space.down", 0.95, "neutral"),
    ("space.near", "contrasts_with", "space.far", 0.95, "neutral"),
    ("space.inside", "contrasts_with", "space.outside", 0.95, "neutral"),
    ("space.on", "supports", "concept.object", 0.80, "neutral"),
    ("space.under", "contrasts_with", "space.on", 0.65, "neutral"),
    ("physical.open", "enables", "physical.touch", 0.85, "positive"),
    ("physical.closed", "blocks", "physical.touch", 0.90, "negative"),
    ("physical.closed", "can_cause", "physical.block", 0.90, "negative"),
    ("physical.hold", "blocks", "physical.fall", 0.85, "positive"),
    ("physical.fall", "can_cause", "physical.hit", 0.80, "negative"),
    ("physical.hit", "can_cause", "valence.pain", 0.85, "negative"),
    ("physical.push", "can_cause", "physical.move", 0.80, "neutral"),
    ("physical.pull", "can_cause", "physical.move", 0.80, "neutral"),
    ("physical.block", "blocks", "physical.move", 0.90, "negative"),
    ("property.hot", "can_cause", "valence.pain", 0.90, "negative"),
    ("property.sharp", "can_cause", "valence.pain", 0.90, "negative"),
    ("property.hard", "can_cause", "physical.hit", 0.55, "negative"),
    ("property.soft", "reduces", "physical.hit", 0.65, "positive"),
    ("property.heavy", "blocks", "physical.move", 0.70, "negative"),
    ("property.light", "enables", "physical.move", 0.75, "positive"),
    ("property.round", "enables", "physical.move", 0.55, "neutral"),
    ("property.wet", "contrasts_with", "property.dry", 0.95, "neutral"),
    ("property.hot", "contrasts_with", "property.cold", 0.95, "neutral"),
    ("property.hard", "contrasts_with", "property.soft", 0.95, "neutral"),
    ("property.big", "contrasts_with", "property.small", 0.95, "neutral"),
    ("property.heavy", "contrasts_with", "property.light", 0.95, "neutral"),
    ("living.living_thing", "is_a", "concept.thing", 0.95, "neutral"),
    ("living.person", "is_a", "living.living_thing", 0.95, "neutral"),
    ("living.animal", "is_a", "living.living_thing", 0.95, "neutral"),
    ("living.plant", "is_a", "living.living_thing", 0.90, "neutral"),
    ("living.child", "is_a", "living.person", 0.95, "neutral"),
    ("living.adult", "is_a", "living.person", 0.95, "neutral"),
    ("living.young_animal", "is_a", "living.animal", 0.95, "neutral"),
    ("living.living_thing", "needs", "need.food", 0.80, "neutral"),
    ("living.living_thing", "needs", "need.water", 0.85, "neutral"),
    ("living.living_thing", "needs", "need.sleep", 0.75, "neutral"),
    ("living.living_thing", "needs", "need.air", 0.75, "neutral"),
    ("living.animal", "can_cause", "physical.move", 0.85, "neutral"),
    ("living.animal", "can_cause", "sense.sound", 0.75, "neutral"),
    ("living.animal", "can_feel", "valence.pain", 0.90, "negative"),
    ("living.person", "can_cause", "language.say", 0.90, "neutral"),
    ("living.person", "can_feel", "emotion.happy", 0.90, "positive"),
    ("living.person", "can_feel", "emotion.sad", 0.90, "negative"),
    ("living.young_animal", "has_property", "property.small", 0.70, "neutral"),
    ("living.young_animal", "needs", "social.help", 0.70, "positive"),
    ("living.plant", "needs", "need.water", 0.85, "neutral"),
    ("valence.pain", "contrasts_with", "valence.comfort", 0.90, "neutral"),
    ("valence.pain", "can_cause", "emotion.sad", 0.80, "negative"),
    ("valence.pain", "can_cause", "emotion.afraid", 0.60, "negative"),
    ("valence.comfort", "can_cause", "emotion.happy", 0.80, "positive"),
    ("valence.good", "can_cause", "emotion.happy", 0.70, "positive"),
    ("valence.bad", "can_cause", "emotion.sad", 0.70, "negative"),
    ("valence.good", "contrasts_with", "valence.bad", 0.90, "neutral"),
    ("social.help", "reduces", "valence.pain", 0.80, "positive"),
    ("social.help", "can_cause", "emotion.happy", 0.80, "positive"),
    ("social.hurt", "can_cause", "valence.pain", 0.90, "negative"),
    ("social.hurt", "can_cause", "emotion.sad", 0.80, "negative"),
    ("emotion.want", "can_cause", "physical.move", 0.65, "neutral"),
    ("emotion.want", "can_cause", "social.take", 0.55, "neutral"),
    ("emotion.angry", "can_cause", "social.hurt", 0.45, "negative"),
    ("emotion.angry", "contrasts_with", "emotion.happy", 0.55, "neutral"),
    ("social.caregiver", "is_a", "living.person", 0.95, "positive"),
    ("social.mom", "is_a", "social.caregiver", 0.95, "positive"),
    ("social.dad", "is_a", "social.caregiver", 0.95, "positive"),
    ("social.caregiver", "can_cause", "social.help", 0.90, "positive"),
    ("social.caregiver", "can_cause", "valence.comfort", 0.85, "positive"),
    ("social.give", "can_cause", "social.take", 0.60, "neutral"),
    ("social.share", "is_a", "social.give", 0.65, "positive"),
    ("social.pet", "is_a", "social.role", 0.60, "positive"),
    ("social.pet", "near", "living.person", 0.70, "positive"),
    ("language.word", "is_a", "concept.thing", 0.90, "neutral"),
    ("language.name", "is_a", "language.word", 0.95, "neutral"),
    ("language.word", "can_name", "concept.thing", 0.95, "neutral"),
    ("language.hear_word", "uses_channel", "sense.sound", 0.95, "neutral"),
    ("language.hear_word", "can_activate", "concept.relation", 0.75, "neutral"),
    ("language.story", "has_part", "concept.event", 0.80, "neutral"),
    ("language.story", "has_part", "concept.relation", 0.80, "neutral"),
    ("language.question", "asks_for", "concept.relation", 0.90, "neutral"),
    ("language.answer", "gives", "concept.relation", 0.90, "neutral"),
    ("time.before", "contrasts_with", "time.after", 0.95, "neutral"),
    ("time.cause", "links", "time.before", 0.75, "neutral"),
    ("time.cause", "links", "time.effect", 0.75, "neutral"),
    ("time.start", "contrasts_with", "time.stop", 0.85, "neutral"),
    ("time.again", "repeats", "concept.event", 0.85, "neutral"),
]


EVENT_TEMPLATES = [
    {
        "id": "near_touch",
        "scene": "The hand is near the object. The hand moves to the object.",
        "answer": "The hand touches the object.",
        "relations": [
            ("space.near", "enables", "physical.touch"),
            ("body.hand", "can_cause", "physical.touch"),
        ],
    },
    {
        "id": "far_no_touch",
        "scene": "The object is far from the hand. The hand moves.",
        "answer": "The hand does not touch the object.",
        "relations": [
            ("space.far", "blocks", "physical.touch"),
        ],
    },
    {
        "id": "closed_blocks",
        "scene": "The object is inside a closed box. The hand reaches the box.",
        "answer": "The closed box blocks the hand.",
        "relations": [
            ("physical.closed", "can_cause", "physical.block"),
            ("physical.block", "blocks", "physical.move"),
        ],
    },
    {
        "id": "open_enables",
        "scene": "The object is inside an open box. The hand reaches inside.",
        "answer": "The hand can touch the object.",
        "relations": [
            ("physical.open", "enables", "physical.touch"),
        ],
    },
    {
        "id": "hot_pain",
        "scene": "The object is hot. The hand touches the hot object.",
        "answer": "Hot touch can cause pain.",
        "relations": [
            ("property.hot", "can_cause", "valence.pain"),
        ],
    },
    {
        "id": "sharp_pain",
        "scene": "The object is sharp. The skin touches the sharp object.",
        "answer": "Sharp touch can cause pain.",
        "relations": [
            ("property.sharp", "can_cause", "valence.pain"),
        ],
    },
    {
        "id": "caregiver_comfort",
        "scene": "The baby feels pain. The caregiver helps the baby.",
        "answer": "Help can reduce pain and bring comfort.",
        "relations": [
            ("social.help", "reduces", "valence.pain"),
            ("social.caregiver", "can_cause", "valence.comfort"),
        ],
    },
    {
        "id": "comfort_happy",
        "scene": "The baby is comfortable. The baby feels okay.",
        "answer": "Comfort can cause happy feeling.",
        "relations": [
            ("valence.comfort", "can_cause", "emotion.happy"),
        ],
    },
    {
        "id": "pain_sad",
        "scene": "The baby feels pain. The pain continues.",
        "answer": "Pain can cause sadness.",
        "relations": [
            ("valence.pain", "can_cause", "emotion.sad"),
        ],
    },
    {
        "id": "word_activates_relation",
        "scene": "Mom says a word. The baby hears the word.",
        "answer": "A heard word can activate a relation.",
        "relations": [
            ("language.hear_word", "can_activate", "concept.relation"),
            ("language.hear_word", "uses_channel", "sense.sound"),
        ],
    },
]


INHERITANCE_PROBES = [
    ("living.child", "is_a", "living.person", "is_a", "living.living_thing", "A child is a person. A person is a living thing."),
    ("social.mom", "is_a", "social.caregiver", "is_a", "living.person", "Mom is a caregiver. A caregiver is a person."),
    ("social.dad", "is_a", "social.caregiver", "is_a", "living.person", "Dad is a caregiver. A caregiver is a person."),
    ("living.young_animal", "is_a", "living.animal", "is_a", "living.living_thing", "A young animal is an animal. An animal is a living thing."),
    ("living.animal", "is_a", "living.living_thing", "needs", "need.food", "An animal is a living thing. A living thing needs food."),
    ("living.animal", "is_a", "living.living_thing", "needs", "need.water", "An animal is a living thing. A living thing needs water."),
    ("living.person", "is_a", "living.living_thing", "needs", "need.sleep", "A person is a living thing. A living thing needs sleep."),
    ("body.hand", "part_of", "body.body", "is_a", "concept.object", "A hand is part of body. Body is an object."),
    ("language.name", "is_a", "language.word", "is_a", "concept.thing", "A name is a word. A word is a thing."),
    ("language.story", "has_part", "concept.event", "has_part", "concept.relation", "A story has events. Events have relations."),
]


RELATION_RENDER = {
    "is_a": "{source} is {target}",
    "part_of": "{source} is part of {target}",
    "has_part": "{source} has {target}",
    "directly_controlled_by": "{source} is directly controlled by {target}",
    "directly_feels": "{source} directly feels {target}",
    "uses_channel": "{source} uses {target}",
    "can_cause": "{source} can cause {target}",
    "enables": "{source} enables {target}",
    "blocks": "{source} blocks {target}",
    "supports": "{source} supports {target}",
    "contrasts_with": "{source} contrasts with {target}",
    "reduces": "{source} reduces {target}",
    "needs": "{source} needs {target}",
    "can_feel": "{source} can feel {target}",
    "has_property": "{source} has property {target}",
    "near": "{source} is near {target}",
    "can_name": "{source} can name {target}",
    "can_activate": "{source} can activate {target}",
    "asks_for": "{source} asks for {target}",
    "gives": "{source} gives {target}",
    "links": "{source} links to {target}",
    "repeats": "{source} repeats {target}",
}


def clean_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    if text[-1] not in ".?!":
        text += "."
    return text


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite")
    if path.exists() and overwrite:
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def node_id_to_label() -> dict[str, str]:
    return {node_id: label for node_id, label, *_ in NODES}


def relation_to_graph(source: str, rel_type: str, target: str, strength: float, valence: str) -> dict[str, Any]:
    return {
        "source": source,
        "type": rel_type,
        "target": target,
        "strength": strength,
        "valence": valence,
        "age_status": "emerging",
    }


def build_graph() -> dict[str, Any]:
    layers = [
        {"id": layer_id, "order": order, "label": label, "description": description}
        for layer_id, order, label, description in LAYERS
    ]
    nodes = [
        {
            "id": node_id,
            "label": label,
            "layer": layer,
            "kind": kind,
            "age_status": "emerging",
            "summary": summary,
        }
        for node_id, label, layer, kind, summary in NODES
    ]
    relations = [relation_to_graph(*relation) for relation in RELATIONS]
    micro_experiences = []
    for item in EVENT_TEMPLATES:
        micro_experiences.append(
            {
                "id": f"root_event.{item['id']}",
                "title": item["id"].replace("_", " ").title(),
                "age_status": "emerging",
                "events": [item["scene"], item["answer"]],
                "relations_observed": [
                    {
                        "source": source,
                        "type": rel_type,
                        "target": target,
                        "strength_delta": 0.05,
                    }
                    for source, rel_type, target in item["relations"]
                ],
            }
        )
    evaluation_questions = []
    for index, (source, source_rel, middle, middle_rel, target, _scene) in enumerate(INHERITANCE_PROBES, start=1):
        evaluation_questions.append(
            {
                "id": f"root_eval.inherit_{index:03d}",
                "question": f"Using inheritance, how does {label(source)} connect to {label(target)}?",
                "expected_answer": f"{label(source)} connects to {label(target)} through {label(middle)}.",
                "expected_relations": [
                    {"source": source, "type": source_rel, "target": middle},
                    {"source": middle, "type": middle_rel, "target": target},
                ],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "graph_id": EXPERIMENT_ID,
        "metadata": {
            "title": "Root Concept Foundation V0",
            "description": "Root relation anchors for a relation-first TinyStories curriculum.",
            "notes": [
                "This graph is the base concept stage, not the TinyStories word attachment stage.",
                "Later words should attach to these anchors by inheritance rather than repeat flat facts.",
            ],
        },
        "layers": layers,
        "nodes": nodes,
        "relations": relations,
        "micro_experiences": micro_experiences,
        "evaluation_questions": evaluation_questions,
    }


def label(node_id: str) -> str:
    return node_id_to_label().get(node_id, node_id)


def relation_text(source: str, rel_type: str, target: str) -> str:
    template = RELATION_RENDER.get(rel_type, "{source} " + rel_type.replace("_", " ") + " {target}")
    return template.format(source=label(source), target=label(target))


def split_for(unit_id: str) -> str:
    value = int(hashlib.sha256(unit_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if value < 82:
        return "train"
    if value < 91:
        return "dev"
    return "curriculum_test"


def make_unit(unit_id: str, unit_type: str, input_text: str, target_text: str, relations: list[tuple[str, str, str]]) -> dict[str, Any]:
    return {
        "unit_id": unit_id,
        "unit_type": unit_type,
        "split": split_for(unit_id),
        "input": input_text,
        "target": target_text,
        "relations": [
            {"source": source, "type": rel_type, "target": target}
            for source, rel_type, target in relations
        ],
    }


def build_units() -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for index, (source, rel_type, target, _strength, _valence) in enumerate(RELATIONS, start=1):
        fact = clean_sentence(relation_text(source, rel_type, target))
        units.append(
            make_unit(
                f"fact.{index:03d}.{source}.{rel_type}.{target}",
                "root_fact_prose",
                "",
                fact,
                [(source, rel_type, target)],
            )
        )
        units.append(
            make_unit(
                f"qa.{index:03d}.{source}.{rel_type}.{target}",
                "root_fact_qa",
                f"Question: What relation connects {label(source)} and {label(target)}?\nAnswer:",
                f"answer: {fact.lower()}\nreason: this is a root relation.",
                [(source, rel_type, target)],
            )
        )

    for index, (source, source_rel, middle, middle_rel, target, scene) in enumerate(INHERITANCE_PROBES, start=1):
        if middle_rel == "needs":
            answer = f"{label(source)} needs {label(target)} because {label(source)} is {label(middle)}."
            rels = [(source, source_rel, middle), (middle, middle_rel, target)]
        elif source_rel == "part_of":
            answer = f"{label(source)} connects to {label(target)} because {label(source)} is part of {label(middle)}."
            rels = [(source, source_rel, middle), (middle, middle_rel, target)]
        elif source_rel == "has_part":
            answer = f"{label(source)} connects to {label(target)} because {label(source)} has {label(middle)}."
            rels = [(source, source_rel, middle), (middle, middle_rel, target)]
        else:
            answer = f"{label(source)} is {label(target)} through {label(middle)}."
            rels = [(source, source_rel, middle), (middle, middle_rel, target)]
        units.append(
            make_unit(
                f"inherit.prose.{index:03d}",
                "inheritance_prose",
                "",
                clean_sentence(f"{scene} So {answer.lower()}"),
                rels,
            )
        )
        units.append(
            make_unit(
                f"inherit.qa.{index:03d}",
                "inheritance_qa",
                f"Scene: {scene}\nQuestion: What follows by inheritance?\nAnswer:",
                f"answer: {answer.lower()}\nreason: relation passes through the middle concept.",
                rels,
            )
        )

    for item in EVENT_TEMPLATES:
        rels = item["relations"]
        units.append(
            make_unit(
                f"event.prose.{item['id']}",
                "event_prose",
                "",
                clean_sentence(f"{item['scene']} {item['answer']}"),
                rels,
            )
        )
        units.append(
            make_unit(
                f"event.qa.{item['id']}",
                "event_qa",
                f"Scene: {item['scene']}\nQuestion: What happens?\nAnswer:",
                f"answer: {item['answer'].lower()}\nreason: {'; '.join(relation_text(*relation).lower() for relation in rels)}.",
                rels,
            )
        )

    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, Any]] = []
    for unit in units:
        key = (unit["unit_type"], unit["input"], unit["target"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(unit)
    return unique


def variant_accepts(variant: str, unit: dict[str, Any]) -> bool:
    is_qa = unit["unit_type"].endswith("_qa")
    if variant == "root_prose":
        return not is_qa
    if variant == "root_qa":
        return is_qa
    if variant == "root_mixed":
        return True
    raise ValueError(f"unknown variant: {variant}")


def make_record(variant: str, unit: dict[str, Any]) -> dict[str, Any]:
    is_qa = bool(unit["input"])
    record_id = f"dataset.{EXPERIMENT_ID}.{variant}.{unit['split']}.{unit['unit_id']}"
    messages = (
        [{"role": "user", "content": unit["input"]}, {"role": "assistant", "content": unit["target"]}]
        if is_qa
        else [{"role": "assistant", "content": unit["target"]}]
    )
    return {
        "id": record_id,
        "source_example_id": unit["unit_id"],
        "experiment_id": EXPERIMENT_ID,
        "variant": variant,
        "split": unit["split"],
        "task_type": unit["unit_type"],
        "input": unit["input"],
        "target": unit["target"],
        "messages": messages,
        "metadata": {
            "domain_id": EXPERIMENT_ID,
            "representation": variant,
            "relations_visible_to_model": False,
            "root_relations": unit["relations"],
            "stage": "stage_1_root_concept_foundation",
        },
    }


def build_records(units: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    records: dict[str, dict[str, list[dict[str, Any]]]] = {
        variant: {split: [] for split in SPLITS} for variant in VARIANTS
    }
    for variant in VARIANTS:
        for unit in units:
            if not variant_accepts(variant, unit):
                continue
            records[variant][unit["split"]].append(make_record(variant, unit))
        for split in SPLITS:
            records[variant][split].sort(key=lambda row: row["id"])
    return records


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    alpha: Counter[str] = Counter()
    raw: Counter[str] = Counter()
    for row in rows:
        text = f"{row['input']}\n{row['target']}".lower()
        alpha.update(WORD_RE.findall(text))
        raw.update(RAW_RE.findall(text))
    return {
        "unique_words_alpha": len(alpha),
        "total_words_alpha": sum(alpha.values()),
        "unique_raw_whitespace_tokens": len(raw),
        "total_raw_whitespace_tokens": sum(raw.values()),
        "top_words": dict(alpha.most_common(40)),
    }


def file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {name: {"path": str(path), "sha256": sha256_file(path)} for name, path in sorted(paths.items())}


def write_outputs(args: argparse.Namespace, graph: dict[str, Any], records: dict[str, dict[str, list[dict[str, Any]]]]) -> None:
    ensure_output_dir(args.output_dir, args.overwrite)

    output_paths: dict[str, Path] = {}
    write_json(args.seed_output, graph)
    output_paths["seed_graph"] = args.seed_output

    for variant, split_rows in records.items():
        for split, rows in split_rows.items():
            path = args.output_dir / "datasets" / variant / f"{split}.jsonl"
            write_jsonl(path, rows)
            output_paths[f"{variant}.{split}"] = path

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "seed_graph": str(args.seed_output),
        "output_dir": str(args.output_dir / "datasets"),
        "variants": {
            variant: {
                split: {
                    "total": len(rows),
                    "task_type_counts": dict(sorted(Counter(row["task_type"] for row in rows).items())),
                    "vocabulary": vocab_stats(rows),
                }
                for split, rows in split_rows.items()
            }
            for variant, split_rows in records.items()
        },
        "outputs": file_manifest(output_paths),
    }
    manifest_path = args.output_dir / "datasets" / "manifest.json"
    write_json(manifest_path, manifest)
    output_paths["dataset_manifest"] = manifest_path

    training_config = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "dataset_manifest": str(manifest_path),
        "output_root": f"runs/{EXPERIMENT_ID}/nanochat",
        "format": {
            "prompt_template": "{input}",
            "target_template": "{target}",
            "notes": "Records with empty input are normal next-token prose. QA records use input-target pairs.",
        },
        "training": {
            "recommended_order": [
                "root_mixed",
                "tinystories_word_attachment_v0",
                "tinystories_plain_text",
            ],
            "max_seq_length": 256,
            "seed": 1729,
        },
    }
    training_config_path = args.output_dir / "training_config.json"
    write_json(training_config_path, training_config)
    output_paths["training_config"] = training_config_path

    top_manifest = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "seed_graph": str(args.seed_output),
        "dataset_manifest": str(manifest_path),
        "training_config": str(training_config_path),
        "graph_counts": {
            "layers": len(graph["layers"]),
            "nodes": len(graph["nodes"]),
            "relations": len(graph["relations"]),
            "micro_experiences": len(graph["micro_experiences"]),
            "evaluation_questions": len(graph["evaluation_questions"]),
        },
        "splits": {
            variant: {split: len(rows) for split, rows in split_rows.items()}
            for variant, split_rows in records.items()
        },
        "outputs": file_manifest(output_paths),
    }
    top_manifest_path = args.output_dir / "manifest.json"
    write_json(top_manifest_path, top_manifest)

    print(json.dumps(top_manifest, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(f"data/developmental_graph/experiments/{EXPERIMENT_ID}"))
    parser.add_argument("--seed-output", type=Path, default=Path(f"data/developmental_graph/seeds/{EXPERIMENT_ID}.json"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--seed", type=int, default=1729)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    random.seed(args.seed)
    graph = build_graph()
    units = build_units()
    records = build_records(units)
    write_outputs(args, graph, records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
