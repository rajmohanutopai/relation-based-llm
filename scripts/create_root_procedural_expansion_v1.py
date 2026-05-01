#!/usr/bin/env python3
"""Create a root-anchored procedural expansion dataset.

This dataset is the larger training/evaluation layer after
root_concept_foundation_v1.

The model-visible text is ordinary QA text. The root graph is kept in metadata:

- surface words such as dog, spoon, kitchen, and puppy attach to root anchors
- hidden root relations explain the expected answer
- dense/sparse/corrupt variants are generated from the same source units
- held-out buckets separate observation, inference, transfer, and counterfactual

The purpose is to test whether a tiny model learns reusable relation behavior
from relation-dense ordinary text, before moving into TinyStories word
attachment and raw TinyStories text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import create_procedural_foundation_world_v3 as v3
import create_root_concept_foundation_v1 as root_v1


EXPERIMENT_ID = "root_procedural_expansion_v1"
SCHEMA_VERSION = "0.1.0"
ROOT_SEED_ID = "root_concept_foundation_v1"
SPLITS = (
    "train",
    "dev",
    "test_observation",
    "test_inference",
    "test_transfer",
    "test_counterfactual",
)
TEST_SPLITS = tuple(split for split in SPLITS if split.startswith("test_"))
VARIANTS = (
    "root_dense_qa",
    "root_sparse_qa",
    "root_corrupt_qa",
)
PROMPT_TYPES = (
    "scene_question_answer",
    "natural_scene_question",
    "direct_question",
    "answer_and_reason_request",
    "question_then_scene",
)
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")
SHORTHAND_RE = re.compile(r"(?m)^(?:s|q|a|f|r|n):\s")


CORE_SURFACE_NAMES = (
    "hand",
    "finger",
    "mouth",
    "eye",
    "ear",
    "leg",
    "skin",
    "baby",
    "mom",
    "dad",
    "caregiver",
    "sibling",
    "brother",
    "sister",
    "child",
    "friend",
    "stranger",
    "doctor",
    "dog",
    "cat",
    "puppy",
    "bird",
    "cow",
    "goat",
    "fish",
    "plant",
    "floor",
    "bed",
    "mat",
    "table",
    "chair",
    "sofa",
    "shelf",
    "wall",
    "door",
    "window",
    "room",
    "kitchen",
    "bathroom",
    "garden",
    "park",
    "road",
    "lap",
    "arms",
    "ball",
    "rattle",
    "block",
    "cube",
    "ring",
    "toy",
    "doll",
    "teddy",
    "toy car",
    "cup",
    "spoon",
    "bottle",
    "bowl",
    "plate",
    "book",
    "cloth",
    "blanket",
    "pillow",
    "towel",
    "shirt",
    "sock",
    "shoe",
    "hat",
    "bag",
    "box",
    "basket",
    "drawer",
    "cupboard",
    "phone",
    "key",
    "paper",
    "pen",
    "brush",
    "comb",
    "pacifier",
    "teether",
    "soap",
    "bucket",
    "tray",
    "lid",
    "bell",
    "drum",
    "crayon",
    "pencil",
    "coin",
    "plug",
    "wire",
    "socket",
    "knife",
    "scissor",
    "candle",
    "match",
    "medicine bottle",
    "fan",
    "lamp",
    "milk",
    "water",
    "rice",
    "dal",
    "curd",
    "porridge",
    "banana",
    "apple",
    "mango",
    "biscuit",
    "bread",
    "chapati",
    "idli",
    "dosa",
    "carrot",
    "potato",
    "pea",
    "soup",
    "juice",
    "medicine",
    "stone",
    "leaf",
    "flower",
    "stick",
    "puddle",
    "rain",
    "sun",
    "wind",
    "dust",
    "fire",
    "ice",
    "smile",
    "cry",
    "laugh",
    "clap",
    "wave",
    "gentle voice",
    "loud voice",
    "song",
    "hug",
    "play",
)


ANIMAL_NAMES = {"dog", "cat", "bird", "cow", "goat", "fish"}
YOUNG_ANIMAL_NAMES = {"puppy"}
ROOT_RELATION_SET = {
    (source, rel_type, target)
    for source, rel_type, target, _strength, _valence in root_v1.RELATION_SPECS
}


@dataclass(frozen=True)
class SurfaceEntity:
    name: str
    category: str
    root_anchor: str
    size: str
    weight: str
    feel: str
    safe_touch: bool
    mobile: bool
    sound: str
    container: bool
    openable: bool
    support: bool
    cover: bool
    food: bool
    liquid: bool
    body_part: bool
    person: bool
    place: bool
    social_signal: bool
    can_be_hot: bool
    can_be_wet: bool
    fragile: bool


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


def stable_int(*parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def stable_percent(*parts: object) -> int:
    return stable_int(*parts) % 100


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def verb3(action: str) -> str:
    return {
        "push": "pushes",
        "pull": "pulls",
        "find": "finds",
        "lose": "loses",
        "fix": "fixes",
        "clean": "cleans",
        "move": "moves",
    }.get(action, f"{action}s")


def property_phrase(prop: str) -> str:
    return {
        "danger": "not safe",
        "safe": "safe",
        "hot": "hot",
        "sharp": "sharp",
        "soft": "soft",
    }.get(prop, prop)


def sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    text = re.sub(
        r"(^|[.!?]\s+)([a-z])",
        lambda match: match.group(1) + match.group(2).upper(),
        text,
    )
    if text[-1] not in ".?!":
        text += "."
    return text


def lower_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip()).lower()
    if not text:
        return ""
    if text[-1] not in ".?!":
        text += "."
    return text


def question(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip()).rstrip(".")
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    if not text.endswith("?"):
        text += "?"
    return text


def root_relation(source: str, rel_type: str, target: str) -> dict[str, str]:
    if (source, rel_type, target) not in ROOT_RELATION_SET:
        raise ValueError(f"unknown root relation: {source} --{rel_type}--> {target}")
    return {
        "source": source,
        "type": rel_type,
        "target": target,
        "text": root_v1.relation_text(source, rel_type, target),
    }


def rr(source: str, rel_type: str, target: str) -> dict[str, str]:
    return root_relation(source, rel_type, target)


def surface_binding(name: str, anchor: str) -> dict[str, str]:
    return {
        "surface": name,
        "root_anchor": anchor,
        "text": f"{name} attaches to {root_v1.label(anchor)}",
    }


def root_anchor_for(item: v3.Entity) -> str:
    if item.name == "hand":
        return "body.hand"
    if item.name == "mouth":
        return "body.mouth"
    if item.name == "eye":
        return "body.eye"
    if item.name == "ear":
        return "body.ear"
    if item.name == "skin":
        return "body.skin"
    if item.name == "leg":
        return "body.leg"
    if item.body_part:
        return "body.body"
    if item.name == "baby" or item.name == "child":
        return "living.child"
    if item.name == "mom":
        return "social.mom"
    if item.name == "dad":
        return "social.dad"
    if item.name == "caregiver":
        return "social.caregiver"
    if item.name in {"friend", "sibling", "brother", "sister"}:
        return "social.friend"
    if item.person:
        return "living.person"
    if item.name in YOUNG_ANIMAL_NAMES:
        return "living.young_animal"
    if item.name in ANIMAL_NAMES:
        return "living.animal"
    if item.name == "plant":
        return "living.plant"
    if item.name == "ball":
        return "object.ball"
    if item.name == "cup":
        return "object.cup"
    if item.name == "book":
        return "object.book"
    if item.name == "blanket":
        return "object.blanket"
    if item.name in {"needle", "knife", "scissor", "match"}:
        return "object.needle"
    if item.name == "box":
        return "object.box"
    if item.name == "bag":
        return "object.bag"
    if item.name == "door":
        return "object.door"
    if item.name == "table":
        return "object.table"
    if item.name == "floor":
        return "object.floor"
    if item.name in {"home", "room", "kitchen", "bathroom", "bed", "lap", "arms"}:
        return "place.home"
    if item.name in {"park", "garden"}:
        return "place.park"
    if item.food and item.liquid and item.name == "water":
        return "object.water"
    if item.food:
        return "object.food"
    if item.category == "toy":
        return "object.toy"
    if item.place:
        return "place.home"
    return "object.object"


def get_entity(name: str) -> SurfaceEntity:
    if name == "dog":
        base = v3.e("dog", "animal", size="medium", weight="medium", feel="soft", person=False)
    elif name == "cat":
        base = v3.e("cat", "animal", size="medium", weight="medium", feel="soft", person=False)
    elif name == "puppy":
        base = v3.e("puppy", "animal", size="small", weight="light", feel="soft", person=False)
    elif name == "bird":
        base = v3.e("bird", "animal", size="small", weight="light", feel="soft", person=False)
    elif name == "cow":
        base = v3.e("cow", "animal", size="big", weight="heavy", feel="soft", person=False)
    elif name == "goat":
        base = v3.e("goat", "animal", size="medium", weight="medium", feel="soft", person=False)
    elif name == "fish":
        base = v3.e("fish", "animal", size="small", weight="light", feel="wet", person=False)
    elif name == "plant":
        base = v3.e("plant", "plant", size="medium", weight="medium", feel="soft", mobile=False)
    else:
        base = v3.ENTITY_BY_NAME[name]
    return SurfaceEntity(
        name=base.name,
        category=base.category,
        root_anchor=root_anchor_for(base),
        size=base.size,
        weight=base.weight,
        feel=base.feel,
        safe_touch=base.safe_touch,
        mobile=base.mobile,
        sound=base.sound,
        container=base.container,
        openable=base.openable,
        support=base.support,
        cover=base.cover,
        food=base.food,
        liquid=base.liquid,
        body_part=base.body_part,
        person=base.person,
        place=base.place,
        social_signal=base.social_signal,
        can_be_hot=base.can_be_hot,
        can_be_wet=base.can_be_wet,
        fragile=base.fragile,
    )


ENTITIES = [get_entity(name) for name in CORE_SURFACE_NAMES]
ENTITY_BY_NAME = {item.name: item for item in ENTITIES}


def anchor_relations(item: SurfaceEntity) -> list[dict[str, str]]:
    anchor = item.root_anchor
    if anchor == "object.ball":
        return [rr("object.ball", "is_a", "object.toy"), rr("object.toy", "is_a", "object.object")]
    if anchor == "object.toy":
        return [rr("object.toy", "is_a", "object.object")]
    if anchor in {"object.cup", "object.book", "object.box", "object.bag", "object.door", "object.food", "object.water", "object.blanket", "object.needle", "object.floor", "object.table"}:
        return [rr(anchor, "is_a", "object.object")]
    if anchor == "living.child":
        return [rr("living.child", "is_a", "living.person"), rr("living.person", "is_a", "living.living_thing")]
    if anchor == "living.person":
        return [rr("living.person", "is_a", "living.living_thing")]
    if anchor == "living.animal":
        return [rr("living.animal", "is_a", "living.living_thing")]
    if anchor == "living.young_animal":
        return [rr("living.young_animal", "is_a", "living.animal"), rr("living.animal", "is_a", "living.living_thing")]
    if anchor == "living.plant":
        return [rr("living.plant", "is_a", "living.living_thing")]
    if anchor == "social.mom":
        return [rr("social.mom", "is_a", "social.caregiver"), rr("social.caregiver", "is_a", "living.person")]
    if anchor == "social.dad":
        return [rr("social.dad", "is_a", "social.caregiver"), rr("social.caregiver", "is_a", "living.person")]
    if anchor == "social.caregiver":
        return [rr("social.caregiver", "is_a", "living.person")]
    if anchor == "social.friend":
        return [rr("social.friend", "is_a", "living.person")]
    if anchor == "place.home":
        return [rr("place.home", "has_property", "property.safe")]
    if anchor == "place.park":
        return [rr("place.park", "enables", "social.play")]
    if anchor == "body.hand":
        return [rr("body.hand", "part_of", "body.body"), rr("body.hand", "controlled_by", "self.self")]
    if anchor == "body.mouth":
        return [rr("body.mouth", "part_of", "body.body"), rr("body.mouth", "controlled_by", "self.self")]
    if anchor == "body.leg":
        return [rr("body.leg", "part_of", "body.body"), rr("body.leg", "controlled_by", "self.self")]
    if anchor in {"body.eye", "body.ear", "body.skin"}:
        return [rr(anchor, "part_of", "body.body")]
    return []


def property_relations(item: SurfaceEntity) -> list[dict[str, str]]:
    relations: list[dict[str, str]] = []
    if item.root_anchor == "object.ball":
        relations.append(rr("object.ball", "has_property", "property.round"))
    if item.root_anchor == "object.blanket" or item.feel == "soft":
        relations.append(rr("property.soft", "reduces", "physical.hit"))
    if item.root_anchor == "object.needle" or not item.safe_touch:
        relations.append(rr("property.danger", "can_make", "valence.pain"))
    if item.can_be_hot or item.feel == "hot":
        relations.append(rr("property.hot", "causes", "valence.pain"))
    if item.weight == "heavy":
        relations.append(rr("property.heavy", "prevents", "physical.move"))
    if item.weight == "light":
        relations.append(rr("property.light", "enables", "physical.move"))
    if item.safe_touch:
        relations.append(rr("property.safe", "prevents", "valence.pain"))
    return dedupe_relations(relations)


def dedupe_relations(relations: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, str]] = []
    for relation in relations:
        key = (relation["source"], relation["type"], relation["target"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(relation)
    return unique


def bindings_for(*items: SurfaceEntity) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    bindings: list[dict[str, str]] = []
    for item in items:
        key = (item.name, item.root_anchor)
        if key in seen:
            continue
        seen.add(key)
        bindings.append(surface_binding(item.name, item.root_anchor))
    return bindings


def make_unit(
    rule_family: str,
    scenario: str,
    question_type: str,
    scene: str,
    question_text: str,
    answer: str,
    main_fact: str,
    root_relations: list[dict[str, str]],
    negative_root_relations: list[dict[str, str]] | None,
    surface_bindings: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": f"rootproc.v1.{rule_family}.{slug(scenario)}.{slug(question_type)}",
        "rule_family": rule_family,
        "question_type": question_type,
        "scene": sentence(scene),
        "question": question(question_text),
        "answer": answer.strip().lower(),
        "main_fact": lower_sentence(main_fact),
        "relations": [relation["text"].lower().rstrip(".") for relation in root_relations],
        "negative_relations": [
            relation["text"].lower().rstrip(".")
            for relation in (negative_root_relations or [])
        ],
        "root_relations": dedupe_relations(root_relations),
        "negative_root_relations": dedupe_relations(negative_root_relations or []),
        "surface_bindings": surface_bindings,
        "metadata": {
            **metadata,
            "question_type": question_type,
            "root_seed_id": ROOT_SEED_ID,
        },
    }


def add_unit(rows: list[dict[str, Any]], *args: Any, **kwargs: Any) -> None:
    rows.append(make_unit(*args, **kwargs))


def touch_objects() -> list[SurfaceEntity]:
    blocked = {"hand", "finger", "mouth", "eye", "ear", "leg", "skin", "baby", "smile", "cry", "laugh", "clap", "wave", "gentle voice", "loud voice", "song", "hug", "play"}
    return [
        item
        for item in ENTITIES
        if item.name not in blocked
        and not item.person
        and not item.place
        and not item.social_signal
        and item.category != "animal"
        and item.category != "plant"
        and item.name not in {"rain", "sun", "wind", "fire"}
    ]


def movable_objects() -> list[SurfaceEntity]:
    return [
        item
        for item in touch_objects()
        if item.mobile and item.weight != "heavy" and not item.place and not item.liquid
    ]


def fallable_objects() -> list[SurfaceEntity]:
    return [
        item
        for item in movable_objects()
        if item.name not in {"water", "milk", "juice", "dal", "curd", "soup", "rain", "wind"}
    ]


def containers() -> list[SurfaceEntity]:
    return [
        ENTITY_BY_NAME[name]
        for name in ("box", "bag", "basket", "drawer", "cupboard", "bucket", "bowl", "cup")
        if name in ENTITY_BY_NAME
    ]


def container_accepts(container: SurfaceEntity, target: SurfaceEntity) -> bool:
    if target.name == container.name:
        return False
    if target.liquid and container.name not in {"cup", "bowl", "bottle", "bucket"}:
        return False
    if container.name == "cup":
        return target.size == "tiny" or target.name in {"spoon", "ring", "key", "coin", "pea", "crayon", "pencil"}
    if container.name == "bowl":
        return target.size in {"tiny", "small"} or target.food or target.name in {"spoon", "ring", "block"}
    if container.name == "drawer":
        return not target.food and not target.liquid and target.size in {"tiny", "small", "medium"}
    if container.name == "cupboard":
        return not target.liquid
    if container.name in {"bag", "box", "basket", "bucket"}:
        return target.size != "big"
    return True


def people() -> list[SurfaceEntity]:
    return [item for item in ENTITIES if item.person or item.root_anchor in {"social.mom", "social.dad", "social.caregiver", "social.friend"}]


def living_entities() -> list[SurfaceEntity]:
    names = ("baby", "child", "mom", "dad", "friend", "dog", "cat", "puppy", "bird", "cow", "goat", "fish", "plant")
    return [ENTITY_BY_NAME[name] for name in names]


def build_touch_distance_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    layouts = [
        ("near the hand", "near", True, "The hand reaches."),
        ("beside the hand", "near", True, "The hand closes."),
        ("far from the hand", "far", False, "The hand reaches."),
        ("high on the table", "far", False, "The hand lifts up."),
    ]
    for item in touch_objects():
        for layout, distance, can_touch, action in layouts:
            scene = f"The {item.name} is {layout}. {action}"
            relations = anchor_relations(item) + property_relations(item)
            if can_touch:
                relations += [rr("space.near", "enables", "physical.touch"), rr("body.hand", "can_do", "physical.touch")]
                answer = "yes"
                fact = f"the {item.name} is near the hand"
                reason_fact = f"near lets the hand touch the {item.name}"
                negative: list[dict[str, str]] = []
            else:
                relations += [rr("space.far", "prevents", "physical.touch"), rr("body.hand", "can_do", "physical.reach")]
                answer = "no"
                fact = f"the {item.name} is far from the hand"
                reason_fact = f"far stops the hand from touching the {item.name}"
                negative = [rr("space.far", "prevents", "physical.touch")]
            meta = {
                "thing": item.name,
                "root_anchor": item.root_anchor,
                "distance": distance,
                "outcome": "touch" if can_touch else "no_touch",
                "positive": can_touch,
                "counterfactual_group": f"touch|{item.name}",
            }
            scenario = f"{item.name}.{distance}.{slug(layout)}"
            add_unit(rows, "touch_distance", scenario, "touch", scene, f"does the hand touch the {item.name}", answer, fact, relations, negative, bindings_for(item), meta)
            if can_touch:
                reason_question = f"why does the hand touch the {item.name}"
                reason_answer = fact
            else:
                reason_question = f"why does the hand not touch the {item.name}"
                reason_answer = fact
            add_unit(rows, "touch_distance", scenario, "reason", scene, reason_question, reason_answer, reason_fact, relations, negative, bindings_for(item), meta)
    return rows


def build_container_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    targets = [item for item in movable_objects()[:36] if not item.container]
    for target in targets:
        for container in containers():
            if not container_accepts(container, target):
                continue
            for is_open in (True, False):
                state = "open" if is_open else "closed"
                scene = f"The {target.name} is inside the {state} {container.name}. The hand reaches into the {container.name}."
                relations = anchor_relations(target) + anchor_relations(container)
                if is_open:
                    relations += [rr("physical.open", "enables", "physical.touch")]
                    if container.root_anchor in {"object.box", "object.bag", "object.door"}:
                        relations.append(rr(container.root_anchor, "can_have_state", "physical.open"))
                    answer = "yes"
                    fact = f"the {container.name} is open"
                    reason_fact = f"the open {container.name} lets the hand reach the {target.name}"
                    negative: list[dict[str, str]] = []
                else:
                    relations += [rr("physical.closed", "prevents", "physical.touch"), rr("physical.closed", "makes", "physical.block")]
                    if container.root_anchor in {"object.box", "object.bag", "object.door"}:
                        relations.append(rr(container.root_anchor, "can_have_state", "physical.closed"))
                    answer = "no"
                    fact = f"the {container.name} is closed"
                    reason_fact = f"the closed {container.name} blocks the hand from the {target.name}"
                    negative = [rr("physical.closed", "prevents", "physical.touch")]
                meta = {
                    "thing": target.name,
                    "container": container.name,
                    "root_anchor": target.root_anchor,
                    "container_anchor": container.root_anchor,
                    "state": state,
                    "outcome": "touch" if is_open else "blocked",
                    "positive": is_open,
                    "counterfactual_group": f"container|{container.name}|{target.name}",
                }
                scenario = f"{target.name}.{container.name}.{state}"
                add_unit(rows, "container_access", scenario, "touch", scene, f"can the hand touch the {target.name}", answer, fact, relations, negative, bindings_for(target, container), meta)
                if is_open:
                    reason_question = f"why can the hand touch the {target.name}"
                    reason_answer = fact
                else:
                    reason_question = f"why can the hand not touch the {target.name}"
                    reason_answer = fact
                add_unit(rows, "container_access", scenario, "why", scene, reason_question, reason_answer, reason_fact, relations, negative, bindings_for(target, container), meta)
    return rows


def build_property_touch_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates = touch_objects()
    for item in candidates:
        properties: list[tuple[str, bool, str, str, list[dict[str, str]]]] = []
        if item.safe_touch:
            properties.append(("safe", True, "no", f"the {item.name} does not hurt the hand", [rr("property.safe", "prevents", "valence.pain")]))
        else:
            properties.append(("danger", False, "yes", f"the {item.name} can hurt the hand", [rr("property.danger", "can_make", "valence.pain")]))
        if item.can_be_hot or item.name in {"cup", "spoon", "bottle", "bowl", "plate", "milk", "water", "dal", "soup", "candle", "lamp", "fire", "sun"}:
            properties.append(("hot", False, "yes", f"the hot {item.name} can hurt the hand", [rr("property.hot", "causes", "valence.pain")]))
        if item.root_anchor == "object.needle" or item.name in {"knife", "scissor", "needle"}:
            properties.append(("sharp", False, "yes", f"the sharp {item.name} can hurt the skin", [rr("property.sharp", "causes", "valence.pain")]))
        if item.feel == "soft":
            properties.append(("soft", True, "no", f"the soft {item.name} does not hurt the skin", [rr("property.soft", "reduces", "physical.hit")]))
        for prop, positive, answer, fact, prop_relations in properties:
            scene = f"The {item.name} is {property_phrase(prop)}. The hand touches the {item.name}."
            relations = anchor_relations(item) + prop_relations + [rr("body.skin", "feels", "sense.touch")]
            meta = {
                "thing": item.name,
                "root_anchor": item.root_anchor,
                "property": prop,
                "outcome": "pain" if answer == "yes" else "no_pain",
                "positive": positive,
                "counterfactual_group": f"property_touch|{item.name}|{prop}",
            }
            scenario = f"{item.name}.{prop}"
            add_unit(rows, "property_touch", scenario, "pain", scene, "does touch cause pain", answer, fact, relations, [] if positive else prop_relations, bindings_for(item), meta)
            add_unit(rows, "property_touch", scenario, "what_happens", scene, "what happens", fact, fact, relations, [] if positive else prop_relations, bindings_for(item), meta)
    return rows


def build_move_weight_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    objects = movable_objects()[:50] + [ENTITY_BY_NAME[name] for name in ("table", "chair", "fan", "lamp", "drawer", "cupboard") if name in ENTITY_BY_NAME]
    for item in objects:
        for action in ("push", "pull"):
            for near in (True, False):
                can_move = near and item.mobile and item.weight != "heavy"
                place = "near the hand" if near else "far from the hand"
                weight_word = "heavy" if item.weight == "heavy" else "light"
                scene = f"The {item.name} is {place}. The {item.name} is {weight_word}. The hand {verb3(action)} the {item.name}."
                relations = anchor_relations(item) + [rr("body.hand", "can_do", f"physical.{action}")]
                if can_move:
                    relations += [rr(f"physical.{action}", "can_make", "physical.move"), rr("property.light", "enables", "physical.move")]
                    answer = "yes"
                    fact = f"the {item.name} is near and light"
                    reason_fact = f"the hand can {action} the nearby light {item.name}"
                    negative: list[dict[str, str]] = []
                else:
                    answer = "no"
                    if not near:
                        fact = f"the {item.name} is far from the hand"
                        reason_fact = f"far stops the hand from reaching the {item.name}"
                        relations.append(rr("space.far", "prevents", "physical.touch"))
                        negative = [rr("space.far", "prevents", "physical.touch")]
                    else:
                        fact = f"the {item.name} is heavy"
                        reason_fact = f"heavy things are hard to move"
                        relations.append(rr("property.heavy", "prevents", "physical.move"))
                        negative = [rr("property.heavy", "prevents", "physical.move")]
                meta = {
                    "thing": item.name,
                    "root_anchor": item.root_anchor,
                    "action": action,
                    "distance": "near" if near else "far",
                    "outcome": "move" if can_move else "no_move",
                    "positive": can_move,
                    "counterfactual_group": f"move|{item.name}|{action}",
                }
                scenario = f"{item.name}.{action}.{near}"
                add_unit(rows, "move_weight", scenario, "move", scene, f"does the {item.name} move", answer, fact, relations, negative, bindings_for(item), meta)
                add_unit(rows, "move_weight", scenario, "why", scene, f"why does the {item.name} {'move' if can_move else 'not move'}", fact, reason_fact, relations, negative, bindings_for(item), meta)
    return rows


def build_support_fall_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    surfaces = [ENTITY_BY_NAME[name] for name in ("floor", "table", "bed", "lap", "mat") if name in ENTITY_BY_NAME]
    for item in fallable_objects()[:48]:
        for surface in surfaces:
            for held in (True, False):
                scene = f"The {item.name} is above the {surface.name}. " + ("The hand holds it." if held else "The hand lets it go.")
                relations = anchor_relations(item) + anchor_relations(surface)
                if held:
                    relations.append(rr("physical.hold", "prevents", "physical.fall"))
                    answer = "no"
                    fact = f"the hand holds the {item.name}"
                    positive = True
                    negative: list[dict[str, str]] = []
                else:
                    relations += [rr("physical.fall", "causes", "physical.hit"), rr("physical.hit", "causes", "valence.pain")]
                    answer = "yes"
                    fact = f"the hand lets the {item.name} go"
                    positive = False
                    negative = [rr("physical.fall", "causes", "physical.hit")]
                meta = {
                    "thing": item.name,
                    "surface": surface.name,
                    "root_anchor": item.root_anchor,
                    "state": "held" if held else "released",
                    "outcome": "no_fall" if held else "fall",
                    "positive": positive,
                    "counterfactual_group": f"fall|{item.name}|{surface.name}",
                }
                scenario = f"{item.name}.{surface.name}.{held}"
                add_unit(rows, "support_fall", scenario, "fall", scene, f"does the {item.name} fall", answer, fact, relations, negative, bindings_for(item, surface), meta)
    return rows


def build_living_need_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    needs = [
        ("food", "need.food"),
        ("water", "need.water"),
        ("sleep", "need.sleep"),
        ("air", "need.air"),
    ]
    for living in living_entities():
        for need_name, need_node in needs:
            if living.root_anchor == "living.plant" and need_name in {"food", "sleep"}:
                continue
            scene = f"The {living.name} is a living thing. Living things need {need_name}."
            relations = anchor_relations(living) + [rr("living.living_thing", "needs", need_node)]
            meta = {
                "thing": living.name,
                "root_anchor": living.root_anchor,
                "need": need_name,
                "outcome": "need",
                "positive": True,
            }
            scenario = f"{living.name}.{need_name}"
            add_unit(rows, "living_need", scenario, "need", scene, f"what does the {living.name} need", need_name, f"living things need {need_name}", relations, [], bindings_for(living), meta)
            add_unit(rows, "living_need", scenario, "why", scene, f"why does the {living.name} need {need_name}", f"the {living.name} is a living thing", f"living things need {need_name}", relations, [], bindings_for(living), meta)
    return rows


def build_social_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    toys = [ENTITY_BY_NAME[name] for name in ("ball", "toy", "book", "doll", "teddy", "rattle") if name in ENTITY_BY_NAME]
    helpers = [ENTITY_BY_NAME[name] for name in ("mom", "dad", "caregiver", "friend", "sibling") if name in ENTITY_BY_NAME]
    child = ENTITY_BY_NAME["child"]
    for helper in helpers:
        for toy in toys:
            scene = f"The child feels pain. The {helper.name} helps the child and gives the {toy.name}."
            relations = anchor_relations(helper) + anchor_relations(child) + anchor_relations(toy) + [
                rr("social.help", "reduces", "valence.pain"),
                rr("social.help", "can_make", "valence.comfort"),
                rr("social.give", "changes_owner_to", "living.person"),
            ]
            meta = {
                "thing": toy.name,
                "agent": helper.name,
                "root_anchor": toy.root_anchor,
                "outcome": "comfort",
                "positive": True,
            }
            scenario = f"{helper.name}.{toy.name}.help"
            add_unit(rows, "social_effect", scenario, "comfort", scene, "what happens to pain", "pain goes down", "help reduces pain", relations, [], bindings_for(helper, child, toy), meta)
            add_unit(rows, "social_effect", scenario, "feeling", scene, "how does the child feel", "comfort", "comfort can make happy feeling", relations + [rr("valence.comfort", "causes", "emotion.happy")], [], bindings_for(helper, child, toy), meta)
    for friend in [ENTITY_BY_NAME[name] for name in ("friend", "sibling", "brother", "sister") if name in ENTITY_BY_NAME]:
        for toy in toys:
            scene = f"The child wants the {toy.name}. The {friend.name} shares the {toy.name}. They play."
            relations = anchor_relations(friend) + anchor_relations(toy) + [
                rr("social.friend", "can_do", "social.share"),
                rr("social.friend", "can_do", "social.play"),
                rr("social.play", "can_make", "emotion.happy"),
            ]
            meta = {"thing": toy.name, "agent": friend.name, "outcome": "happy", "positive": True}
            scenario = f"{friend.name}.{toy.name}.share"
            add_unit(rows, "social_effect", scenario, "happy", scene, "how does the child feel", "happy", "play can make happy feeling", relations, [], bindings_for(friend, toy), meta)
    for agent_name in ("stranger", "doctor", "child"):
        agent = ENTITY_BY_NAME[agent_name]
        scene = f"The {agent.name} hits the child. The child is hurt."
        relations = anchor_relations(agent) + anchor_relations(child) + [
            rr("social.hurt", "causes", "valence.pain"),
            rr("valence.pain", "causes", "emotion.sad"),
        ]
        meta = {"agent": agent.name, "outcome": "pain", "positive": False}
        add_unit(rows, "social_effect", f"{agent.name}.hurt", "pain", scene, "what happens", "the child feels pain", "hurt causes pain", relations, relations, bindings_for(agent, child), meta)
    signal_cases = [
        ("smile", "happy", "social.smile", "signals", "emotion.happy"),
        ("cry", "sad", "social.cry", "signals", "emotion.sad"),
        ("cry", "pain", "social.cry", "signals", "valence.pain"),
    ]
    for signal, feeling, source, rel_type, target in signal_cases:
        scene = f"The child feels {feeling}. The child {signal}s."
        relations = [rr(source, rel_type, target)]
        meta = {"thing": signal, "outcome": feeling, "positive": feeling == "happy"}
        add_unit(rows, "social_signal", f"{signal}.{feeling}", "signal", scene, f"what does the {signal} show", feeling, f"{signal} shows {feeling}", relations, [], [], meta)
    return rows


def build_language_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    word_items = [item for item in touch_objects()[:42] if " " not in item.name]
    for index, word_item in enumerate(word_items):
        candidates = [
            word_item,
            word_items[(index + 7) % len(word_items)],
            word_items[(index + 17) % len(word_items)],
        ]
        for candidate in candidates:
            match = candidate.name == word_item.name
            scene = f"Mom says the word {word_item.name}. The child hears the word and looks at the {candidate.name}."
            relations = anchor_relations(word_item) + anchor_relations(candidate) + [
                rr("language.name", "names", "concept.thing"),
                rr("language.hear_word", "can_wake", "language.word"),
                rr("language.say", "makes", "sense.sound"),
            ]
            meta = {
                "word": word_item.name,
                "thing": candidate.name,
                "root_anchor": candidate.root_anchor,
                "outcome": "name_match" if match else "name_mismatch",
                "positive": match,
                "counterfactual_group": f"name|{word_item.name}",
            }
            scenario = f"{word_item.name}.{candidate.name}"
            add_unit(rows, "language_name", scenario, "match", scene, f"does the word name the {candidate.name}", "yes" if match else "no", f"the word {word_item.name} {'names' if match else 'does not name'} the {candidate.name}", relations, [] if match else [rr("language.name", "names", "concept.thing")], bindings_for(word_item, candidate), meta)
            if match:
                add_unit(rows, "language_name", scenario, "what_name", scene, "what does the word name", candidate.name, f"the word {word_item.name} names the {candidate.name}", relations, [], bindings_for(word_item, candidate), meta)
    return rows


def build_happiness_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    child = ENTITY_BY_NAME["child"]
    objects = [item for item in touch_objects()[:36] if " " not in item.name]
    helpers = [ENTITY_BY_NAME[name] for name in ("mom", "dad", "caregiver", "friend") if name in ENTITY_BY_NAME]
    for item in objects:
        scene = f"The child learns a new word for the {item.name}."
        relations = anchor_relations(child) + anchor_relations(item) + [
            rr("learning.new_link", "causes", "emotion.happy"),
            rr("learning.new_link", "can_make", "emotion.excited"),
        ]
        meta = {"thing": item.name, "outcome": "new_link_happy", "positive": True, "relation_strength": "new"}
        add_unit(rows, "happiness_mechanism", f"{item.name}.new_link", "feeling", scene, "how does the child feel", "happy and excited", "a new link can cause happy feeling", relations, [], bindings_for(child, item), meta)
        scene = f"The child already knows the word {item.name}. Mom says {item.name} again."
        relations = anchor_relations(child) + anchor_relations(item) + [rr("learning.strong_link", "reduces", "emotion.excited")]
        meta = {"thing": item.name, "outcome": "strong_link_less_excited", "positive": True, "relation_strength": "strong"}
        add_unit(rows, "happiness_mechanism", f"{item.name}.strong_link", "feeling", scene, "how does the child feel", "a little excited", "a strong old link gives less new excitement", relations, [], bindings_for(child, item), meta)
        scene = f"The child keeps the {item.name} near him. Then the {item.name} is gone."
        relations = anchor_relations(child) + anchor_relations(item) + [
            rr("learning.broken_link", "causes", "emotion.sad"),
            rr("physical.lose", "causes", "emotion.sad"),
        ]
        meta = {"thing": item.name, "outcome": "broken_link_sad", "positive": False, "relation_strength": "broken"}
        add_unit(rows, "happiness_mechanism", f"{item.name}.broken_link", "feeling", scene, "how does the child feel", "sad", "a broken link causes sadness", relations, relations, bindings_for(child, item), meta)
    for helper in helpers:
        for item in objects[:20]:
            scene = f"The child cannot reach the {item.name}. The {helper.name} gives the {item.name} to the child."
            relations = anchor_relations(helper) + anchor_relations(item) + [
                rr("social.help", "reduces", "valence.pain"),
                rr("social.give", "changes_owner_to", "living.person"),
                rr("valence.comfort", "causes", "emotion.happy"),
            ]
            meta = {"thing": item.name, "agent": helper.name, "outcome": "help_happy", "positive": True}
            add_unit(rows, "happiness_mechanism", f"{helper.name}.{item.name}.give", "feeling", scene, "how does the child feel", "happy", "help brings comfort and comfort can cause happy feeling", relations, [], bindings_for(helper, item), meta)
    return rows


def build_place_time_action_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    places = [ENTITY_BY_NAME[name] for name in ("room", "kitchen", "bathroom", "garden", "park", "road", "bed", "floor") if name in ENTITY_BY_NAME]
    child = ENTITY_BY_NAME["child"]
    for place in places:
        is_play_place = place.root_anchor in {"place.home", "place.park"} and place.name != "road"
        scene = f"The child is at the {place.name}. A friend is near the child."
        relations = anchor_relations(place) + anchor_relations(child) + [rr("social.friend", "can_do", "social.play")]
        if is_play_place:
            relations.append(rr("social.play", "can_make", "emotion.happy"))
            answer = "play"
            fact = f"the child can play at the {place.name}"
            positive = True
        else:
            relations.append(rr("property.danger", "causes", "emotion.afraid"))
            answer = "be careful"
            fact = f"the {place.name} can need care"
            positive = False
        meta = {"thing": place.name, "root_anchor": place.root_anchor, "outcome": "play" if positive else "care", "positive": positive}
        add_unit(rows, "place_context", place.name, "what_can_happen", scene, "what can happen", answer, fact, relations, [] if positive else [rr("property.danger", "causes", "emotion.afraid")], bindings_for(place, child), meta)
    actions = [
        ("ball", "fall", "The ball is up before. The ball falls after.", "what is the order", "up before fall", "before and after mark order", [rr("time.before", "contrasts_with", "time.after"), rr("physical.fall", "causes", "physical.hit")]),
        ("child", "run_stop", "The child starts running. Then the child stops.", "what changed", "running starts and then stops", "start and stop contrast", [rr("time.start", "contrasts_with", "time.stop"), rr("body.leg", "can_do", "physical.run")]),
        ("song", "again", "The child hears the song. Then the child hears the song again.", "what happened", "the event repeated", "again repeats an event", [rr("time.again", "repeats", "concept.event")]),
    ]
    for thing, action, scene, q, answer, fact, relations in actions:
        add_unit(rows, "time_change", f"{thing}.{action}", "order", scene, q, answer, fact, relations, [], [], {"thing": thing, "outcome": action, "positive": True})
    for item in movable_objects()[:36]:
        for action, answer, fact, relations, positive in [
            ("find", "happy", f"finding the {item.name} can make the child happy", [rr("physical.find", "causes", "emotion.happy")], True),
            ("lose", "sad", f"losing the {item.name} can make the child sad", [rr("physical.lose", "causes", "emotion.sad")], False),
            ("fix", "good", f"fixing the {item.name} makes things good again", [rr("physical.fix", "causes", "valence.good")], True),
            ("clean", "good", f"cleaning the {item.name} makes things good", [rr("physical.clean", "causes", "valence.good")], True),
        ]:
            scene = f"The child has the {item.name}. Then the child {verb3(action)} the {item.name}."
            add_unit(rows, "object_change", f"{item.name}.{action}", "feeling", scene, "what feeling follows", answer, fact, anchor_relations(item) + relations, [] if positive else relations, bindings_for(item), {"thing": item.name, "action": action, "outcome": answer, "positive": positive})
    return rows


def build_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for generator in (
        build_touch_distance_units,
        build_container_units,
        build_property_touch_units,
        build_move_weight_units,
        build_support_fall_units,
        build_living_need_units,
        build_social_units,
        build_language_units,
        build_happiness_units,
        build_place_time_action_units,
    ):
        rows.extend(generator())
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: item["id"]):
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        unique.append(row)
    return unique


def target_text(row: dict[str, Any]) -> str:
    answer = str(row["answer"]).strip().rstrip(".")
    fact = lower_sentence(str(row["main_fact"]))
    return f"answer: {answer}.\nreason: {fact}"


def sparse_scene(row: dict[str, Any]) -> str:
    family = str(row["rule_family"])
    meta = row["metadata"]
    thing = str(meta.get("thing") or "thing")
    if family == "touch_distance":
        return sentence(f"The {thing} is here. The hand moves.")
    if family == "container_access":
        return sentence(f"The {thing} is inside the {meta.get('container', 'container')}. The hand moves.")
    if family == "property_touch":
        return sentence(f"The hand touches the {thing}.")
    if family == "move_weight":
        return sentence(f"The hand {verb3(str(meta.get('action', 'move')))} the {thing}.")
    if family == "support_fall":
        return sentence(f"The {thing} is up. Something happens.")
    if family == "living_need":
        return sentence(f"The {thing} is here.")
    if family in {"social_effect", "social_signal"}:
        return sentence("The child and another person are here. Something happens.")
    if family == "language_name":
        return sentence(f"Mom says a word. The child looks at the {thing}.")
    if family == "happiness_mechanism":
        return sentence(f"The child and the {thing} are here. Something changes.")
    if family == "place_context":
        return sentence(f"The child is at the {thing}.")
    if family in {"time_change", "object_change"}:
        return sentence(f"The {thing} changes.")
    return sentence("Something happens.")


def swap_phrases(text: str, pairs: list[tuple[str, str]]) -> str:
    output = text
    replacements: dict[str, str] = {}
    for index, (left, right) in enumerate(pairs):
        left_token = f"__swap_{index}_left__"
        right_token = f"__swap_{index}_right__"
        output = re.sub(rf"\b{re.escape(left)}\b", left_token, output, flags=re.IGNORECASE)
        output = re.sub(rf"\b{re.escape(right)}\b", right_token, output, flags=re.IGNORECASE)
        replacements[left_token] = right
        replacements[right_token] = left
    for token, replacement in replacements.items():
        output = output.replace(token, replacement)
    return output


def corrupt_scene(row: dict[str, Any]) -> str:
    return sentence(
        swap_phrases(
            str(row["scene"]),
            [
                ("near", "far"),
                ("open", "closed"),
                ("hot", "cold"),
                ("soft", "sharp"),
                ("safe", "danger"),
                ("heavy", "light"),
                ("holds", "lets go"),
                ("helps", "hurts"),
                ("gives", "takes"),
                ("finds", "loses"),
                ("new", "old"),
                ("gone", "near"),
                ("happy", "sad"),
            ],
        )
    )


def render_scene(variant: str, row: dict[str, Any]) -> str:
    if variant == "root_dense_qa":
        return sentence(str(row["scene"]))
    if variant == "root_sparse_qa":
        return sparse_scene(row)
    if variant == "root_corrupt_qa":
        return corrupt_scene(row)
    raise ValueError(f"unknown variant: {variant}")


def prompt_surfaces(row: dict[str, Any], scene_text: str) -> list[dict[str, str]]:
    question_text = question(str(row["question"]))
    return [
        {"prompt_type": "scene_question_answer", "input": f"Scene: {scene_text}\nQuestion: {question_text}\nAnswer:"},
        {"prompt_type": "natural_scene_question", "input": f"Here is what happened. {scene_text}\nQuestion: {question_text}\nAnswer:"},
        {"prompt_type": "direct_question", "input": f"Scene: {scene_text}\nAnswer this question: {question_text}\nAnswer:"},
        {"prompt_type": "answer_and_reason_request", "input": f"Scene: {scene_text}\nQuestion: {question_text}\nGive the answer and the reason.\nAnswer:"},
        {"prompt_type": "question_then_scene", "input": f"Question: {question_text}\nScene: {scene_text}\nAnswer:"},
    ]


def make_record(
    experiment_id: str,
    variant: str,
    split: str,
    row: dict[str, Any],
    surface: dict[str, str],
    surface_index: int,
) -> dict[str, Any]:
    input_text = surface["input"]
    target = target_text(row)
    full_text = f"{input_text}\n{target}"
    if SHORTHAND_RE.search(full_text):
        raise ValueError(f"shorthand protocol leaked into {row['id']}")
    metadata = {
        **row["metadata"],
        "domain_id": EXPERIMENT_ID,
        "rule_family": row["rule_family"],
        "representation": variant,
        "prompt_type": surface["prompt_type"],
        "source_world": EXPERIMENT_ID,
        "evaluation_bucket": split,
        "surface_bindings": row["surface_bindings"],
        "hidden_root_relations": row["root_relations"],
        "hidden_negative_root_relations": row["negative_root_relations"],
        "relations_visible_to_model": False,
    }
    return {
        "id": f"dataset.{experiment_id}.{variant}.{split}.{surface_index:02d}.{surface['prompt_type']}.{row['id']}",
        "source_example_id": row["id"],
        "experiment_id": experiment_id,
        "variant": variant,
        "split": split,
        "evaluation_bucket": split,
        "surface_type": surface["prompt_type"],
        "prompt_type": surface["prompt_type"],
        "task_type": row["rule_family"],
        "input": input_text,
        "target": target,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target},
        ],
        "metadata": metadata,
    }


def family_thing(row: dict[str, Any]) -> tuple[str, str]:
    return str(row["rule_family"]), str(row.get("metadata", {}).get("thing") or "")


def counterfactual_group(row: dict[str, Any]) -> str | None:
    group = row.get("metadata", {}).get("counterfactual_group")
    return str(group) if group else None


def build_transfer_keys(units: list[dict[str, Any]]) -> set[tuple[str, str]]:
    families_by_thing: dict[str, set[str]] = defaultdict(set)
    things_by_family: dict[str, set[str]] = defaultdict(set)
    for row in units:
        family, thing = family_thing(row)
        if not thing:
            continue
        families_by_thing[thing].add(family)
        things_by_family[family].add(thing)
    transfer_keys: set[tuple[str, str]] = set()
    selected_by_thing: Counter[str] = Counter()
    for family, things in sorted(things_by_family.items()):
        candidates = [
            thing
            for thing in things
            if len(families_by_thing[thing]) >= 2 and selected_by_thing[thing] < 2
        ]
        target_count = max(1, int(round(len(candidates) * 0.12))) if candidates else 0
        ranked = sorted(candidates, key=lambda thing: stable_int("transfer", family, thing))
        for thing in ranked[:target_count]:
            transfer_keys.add((family, thing))
            selected_by_thing[thing] += 1
    return transfer_keys


def build_counterfactual_groups(units: list[dict[str, Any]]) -> set[str]:
    rows_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in units:
        group = counterfactual_group(row)
        if group:
            rows_by_group[group].append(row)
    candidates = []
    for group, rows in rows_by_group.items():
        polarities = {row.get("metadata", {}).get("positive") for row in rows}
        if True in polarities and False in polarities:
            candidates.append(group)
    target_count = max(1, int(round(len(candidates) * 0.12))) if candidates else 0
    ranked = sorted(candidates, key=lambda group: stable_int("counterfactual", group))
    return set(ranked[:target_count])


INFERENCE_FAMILIES = {
    "container_access",
    "property_touch",
    "move_weight",
    "support_fall",
    "living_need",
    "language_name",
    "happiness_mechanism",
    "object_change",
}


def is_inference_test(row: dict[str, Any]) -> bool:
    if row["rule_family"] not in INFERENCE_FAMILIES:
        return False
    if row["question_type"] in {"touch", "move", "fall", "match"}:
        return False
    return stable_percent("inference", row["id"]) < 16


def split_units(units: list[dict[str, Any]], seed: int) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    transfer_keys = build_transfer_keys(units)
    counterfactual_groups = build_counterfactual_groups(units)
    all_counterfactual_groups = sorted(
        {group for group in (counterfactual_group(row) for row in units) if group}
    )
    group_transfer_keys: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in units:
        group = counterfactual_group(row)
        key = family_thing(row)
        if group and key[1]:
            group_transfer_keys[group].add(key)

    residual_group_splits: dict[str, str] = {}
    for group in all_counterfactual_groups:
        if group in counterfactual_groups:
            residual_group_splits[group] = "test_counterfactual"
            continue
        if group_transfer_keys[group] & transfer_keys:
            residual_group_splits[group] = "test_transfer"
            continue
        percent = stable_percent("counterfactual-group-split", seed, group)
        if percent < 10:
            residual_group_splits[group] = "dev"
        elif percent < 22:
            residual_group_splits[group] = "test_observation"
        else:
            residual_group_splits[group] = "train"

    splits: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}
    for row in sorted(units, key=lambda unit: (stable_int(seed, unit["id"]), unit["id"])):
        group = counterfactual_group(row)
        key = family_thing(row)
        if group:
            split = residual_group_splits[group]
        elif key in transfer_keys:
            split = "test_transfer"
        elif is_inference_test(row):
            split = "test_inference"
        else:
            percent = stable_percent("observation-dev", seed, row["id"])
            if percent < 10:
                split = "dev"
            elif percent < 22:
                split = "test_observation"
            else:
                split = "train"
        splits[split].append(row)
    for split in SPLITS:
        splits[split].sort(key=lambda row: row["id"])
    policy = {
        "transfer_keys": [f"{family}|{thing}" for family, thing in sorted(transfer_keys)],
        "transfer_key_count": len(transfer_keys),
        "inference_families": sorted(INFERENCE_FAMILIES),
        "counterfactual_group_count": len(counterfactual_groups),
        "counterfactual_groups": sorted(counterfactual_groups),
        "all_counterfactual_group_count": len(all_counterfactual_groups),
        "counterfactual_group_split_counts": dict(sorted(Counter(residual_group_splits.values()).items())),
        "split_unit_counts": {split: len(rows) for split, rows in splits.items()},
        "split_rule_family_counts": {split: count_by(rows, "rule_family") for split, rows in splits.items()},
    }
    return splits, policy


def build_records(
    experiment_id: str,
    variant: str,
    split: str,
    units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for unit in units:
        scene_text = render_scene(variant, unit)
        for index, surface in enumerate(prompt_surfaces(unit, scene_text), start=1):
            rows.append(
                make_record(
                    experiment_id=experiment_id,
                    variant=variant,
                    split=split,
                    row=unit,
                    surface=surface,
                    surface_index=index,
                )
            )
    return rows


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, int]:
    words: Counter[str] = Counter()
    raw: Counter[str] = Counter()
    shorthand_hits = 0
    for row in rows:
        text = f"{row['input']}\n{row['target']}".lower()
        words.update(WORD_RE.findall(text))
        raw.update(RAW_RE.findall(text))
        if SHORTHAND_RE.search(text):
            shorthand_hits += 1
    return {
        "unique_words_alpha": len(words),
        "total_words_alpha": sum(words.values()),
        "unique_raw_whitespace_tokens": len(raw),
        "total_raw_whitespace_tokens": sum(raw.values()),
        "shorthand_protocol_hits": shorthand_hits,
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "unknown")) for row in rows).items()))


def nested_count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("metadata", {}).get(key, "unknown")).lower() for row in rows).items()))


def prompt_conflict_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets_by_input: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        targets_by_input[row["input"]].add(row["target"])
    conflict_count = sum(1 for targets in targets_by_input.values() if len(targets) > 1)
    return {
        "unique_inputs": len(targets_by_input),
        "ambiguous_inputs": conflict_count,
        "ambiguous_input_percent": round((conflict_count / len(targets_by_input)) * 100, 4) if targets_by_input else 0.0,
        "target_count_distribution": dict(sorted(Counter(len(value) for value in targets_by_input.values()).items())),
    }


def leakage_stats(
    splits: dict[str, list[dict[str, Any]]],
    selected_transfer_keys: set[tuple[str, str]],
) -> dict[str, Any]:
    by_split = {
        split: {
            "source_ids": {row["id"] for row in rows},
            "transfer_keys": {family_thing(row) for row in rows if family_thing(row)[1]},
            "counterfactual_groups": {counterfactual_group(row) for row in rows if counterfactual_group(row)},
        }
        for split, rows in splits.items()
    }
    train_source = by_split["train"]["source_ids"]
    test_source = set().union(*(by_split[split]["source_ids"] for split in TEST_SPLITS))
    transfer_overlap = sorted(
        "|".join(key)
        for key in selected_transfer_keys
        if key in by_split["train"]["transfer_keys"]
        and any(key in by_split[split]["transfer_keys"] for split in TEST_SPLITS)
    )
    counter_overlap = sorted(
        group
        for split in TEST_SPLITS
        for group in (by_split["train"]["counterfactual_groups"] & by_split[split]["counterfactual_groups"])
        if group
    )
    return {
        "train_test_source_id_overlap": sorted(train_source & test_source),
        "train_test_counterfactual_group_overlap": counter_overlap,
        "note": "Transfer keeps object words visible in other families by design; family/thing keys are held out only for selected transfer pairs.",
        "selected_transfer_key_train_overlap": transfer_overlap,
    }


def file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {name: {"path": str(path), "sha256": sha256_file(path)} for name, path in sorted(paths.items())}


def build_base_world(units: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter(item.category for item in ENTITIES)
    anchor_counts = Counter(item.root_anchor for item in ENTITIES)
    return {
        "schema_version": SCHEMA_VERSION,
        "world_id": EXPERIMENT_ID,
        "root_seed_id": ROOT_SEED_ID,
        "purpose": "Procedural ordinary-text expansion of root_concept_foundation_v1.",
        "scope": {
            "included": [
                "body/self",
                "space and touch",
                "container access",
                "properties and pain",
                "movement and support",
                "living needs",
                "simple social effects",
                "word-name binding",
                "happiness mechanism",
                "time/change",
            ],
            "excluded_for_now": [
                "formal math",
                "history",
                "geography",
                "medical expert knowledge",
                "adult institutions",
            ],
        },
        "counts": {
            "surface_entities": len(ENTITIES),
            "surface_categories": dict(sorted(category_counts.items())),
            "root_anchor_counts": dict(sorted(anchor_counts.items())),
            "source_units": len(units),
            "rule_families": dict(sorted(Counter(row["rule_family"] for row in units).items())),
        },
        "surface_entities": [asdict(item) for item in ENTITIES],
        "root_seed_summary": {
            "nodes": len(root_v1.NODE_SPECS),
            "relations": len(root_v1.RELATION_SPECS),
            "layers": len(root_v1.LAYERS),
        },
    }


def build_training_config(experiment_id: str, output_dir: Path, dataset_manifest: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": experiment_id,
        "baseline_model": {
            "name": "nanochat",
            "role": "from-scratch local relation-transfer comparison",
            "reason": "This dataset is sized for tiny local training before TinyStories transfer.",
        },
        "dataset_manifest": str(dataset_manifest),
        "output_root": f"runs/{experiment_id}/nanochat",
        "format": {
            "prompt_template": "{input}\n",
            "target_template": "{target}",
        },
        "training": {
            "max_seq_length": 256,
            "seed": 1729,
            "note": "Use scripts/create_nanochat_pretrain_shards.py for train/dev conversion. Evaluate test_* splits separately.",
        },
        "frozen_commands": {
            variant: (
                "python3 scripts/create_nanochat_pretrain_shards.py "
                f"--train-jsonl {output_dir / 'datasets' / variant / 'train.jsonl'} "
                f"--val-jsonl {output_dir / 'datasets' / variant / 'dev.jsonl'} "
                f"--base-dir runs/{experiment_id}/nanochat/{variant} "
                "--mode input_target --shuffle-train --seed 1729"
            )
            for variant in VARIANTS
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/root_procedural_expansion_v1"),
    )
    parser.add_argument("--experiment-id", default=EXPERIMENT_ID)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--shuffle-train-prompts", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_output_dir(args.output_dir, args.overwrite)

    units = build_units()
    unit_splits, split_policy = split_units(units, args.seed)

    base_world_path = args.output_dir / "base_world.json"
    write_json(base_world_path, build_base_world(units))

    for split, rows in unit_splits.items():
        write_jsonl(args.output_dir / "units" / f"{split}.jsonl", rows)
    test_units = [row for split in TEST_SPLITS for row in unit_splits[split]]
    write_jsonl(args.output_dir / "units" / "curriculum_test.jsonl", sorted(test_units, key=lambda row: row["id"]))

    records: dict[str, dict[str, list[dict[str, Any]]]] = {
        variant: {split: [] for split in (*SPLITS, "curriculum_test")}
        for variant in VARIANTS
    }
    output_paths: dict[str, Path] = {}
    rng = random.Random(args.seed)
    for variant in VARIANTS:
        for split in SPLITS:
            rows = build_records(args.experiment_id, variant, split, unit_splits[split])
            if args.shuffle_train_prompts and split == "train":
                rng.shuffle(rows)
            records[variant][split] = rows
            path = args.output_dir / "datasets" / variant / f"{split}.jsonl"
            write_jsonl(path, rows)
            output_paths[f"{variant}.{split}"] = path
        curriculum_rows = [row for split in TEST_SPLITS for row in records[variant][split]]
        curriculum_rows.sort(key=lambda row: row["id"])
        records[variant]["curriculum_test"] = curriculum_rows
        path = args.output_dir / "datasets" / variant / "curriculum_test.jsonl"
        write_jsonl(path, curriculum_rows)
        output_paths[f"{variant}.curriculum_test"] = path

    for split in ("train", "dev", "curriculum_test"):
        write_jsonl(args.output_dir / f"{split}.jsonl", records["root_dense_qa"][split])

    dataset_manifest_path = args.output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": args.experiment_id,
        "output_dir": str(args.output_dir / "datasets"),
        "base_world": str(base_world_path),
        "source": {
            "root_seed_id": ROOT_SEED_ID,
            "source_total_units": len(units),
            "rule_families": sorted({row["rule_family"] for row in units}),
            "question_types": sorted({row["question_type"] for row in units}),
            "prompt_types": list(PROMPT_TYPES),
        },
        "split_policy": split_policy,
        "leakage": leakage_stats(unit_splits, build_transfer_keys(units)),
        "variants": {
            variant: {
                split: {
                    "total": len(records[variant][split]),
                    "base_units": len(unit_splits[split]) if split in unit_splits else len(test_units),
                    "prompts_per_unit": len(PROMPT_TYPES),
                    "task_type_counts": count_by(records[variant][split], "task_type"),
                    "prompt_type_counts": count_by(records[variant][split], "prompt_type"),
                    "question_type_counts": nested_count(records[variant][split], "question_type"),
                    "outcome_counts": nested_count(records[variant][split], "outcome"),
                    "positive_counts": nested_count(records[variant][split], "positive"),
                    "evaluation_bucket_counts": count_by(records[variant][split], "evaluation_bucket"),
                    "vocabulary": vocab_stats(records[variant][split]),
                    "prompt_conflicts": prompt_conflict_stats(records[variant][split]),
                }
                for split in (*SPLITS, "curriculum_test")
            }
            for variant in VARIANTS
        },
        "outputs": file_manifest(output_paths),
        "notes": [
            "root_dense_qa is the main arm.",
            "root_sparse_qa removes discriminating cues while preserving targets.",
            "root_corrupt_qa flips common cues while preserving targets.",
            "Root relations and surface-to-root bindings are hidden in metadata, not rendered to the model.",
            "curriculum_test is the union of observation, inference, transfer, and counterfactual tests.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)

    training_config_path = args.output_dir / "training_config.json"
    write_json(training_config_path, build_training_config(args.experiment_id, args.output_dir, dataset_manifest_path))

    output_paths_with_meta = {
        **output_paths,
        "base_world": base_world_path,
        "dataset_manifest": dataset_manifest_path,
        "training_config": training_config_path,
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": args.experiment_id,
        "root_seed_id": ROOT_SEED_ID,
        "base_world": str(base_world_path),
        "source_total_units": len(units),
        "unit_splits": {split: len(rows) for split, rows in unit_splits.items()},
        "record_splits": {
            variant: {split: len(records[variant][split]) for split in (*SPLITS, "curriculum_test")}
            for variant in VARIANTS
        },
        "prompts_per_unit": len(PROMPT_TYPES),
        "prompt_types": list(PROMPT_TYPES),
        "variants": list(VARIANTS),
        "split_policy": split_policy,
        "leakage": dataset_manifest["leakage"],
        "rule_family_counts": count_by(units, "rule_family"),
        "question_type_counts": count_by(units, "question_type"),
        "dataset_manifest": str(dataset_manifest_path),
        "training_config": str(training_config_path),
        "outputs": file_manifest(output_paths_with_meta),
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
