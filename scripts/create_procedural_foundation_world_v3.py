#!/usr/bin/env python3
"""Generate a larger baby + physical + social procedural foundation world.

V3 expands the base world before generating more rows. It keeps the same
comparison variants as V1/V2, but uses a much broader entity inventory:

- baby body and needs
- household objects, surfaces, containers, food, materials, and places
- simple social agents, signals, care actions, and word-name binding

Formal math is intentionally excluded, except for primitive comparison roots
such as same/different and more/less.
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


SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = (
    "procedural_plain_text",
    "procedural_relation_scaffolded",
    "procedural_relation_first_then_text",
)
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")


@dataclass(frozen=True)
class Entity:
    name: str
    category: str
    size: str = "small"
    weight: str = "light"
    feel: str = "hard"
    safe_touch: bool = True
    mobile: bool = True
    sound: str = "quiet"
    container: bool = False
    openable: bool = False
    support: bool = False
    cover: bool = False
    food: bool = False
    liquid: bool = False
    body_part: bool = False
    person: bool = False
    place: bool = False
    social_signal: bool = False
    can_be_hot: bool = False
    can_be_wet: bool = True
    fragile: bool = False


def e(name: str, category: str, **kwargs: Any) -> Entity:
    return Entity(name=name, category=category, **kwargs)


BODY_PARTS = (
    e("hand", "body", feel="soft", body_part=True),
    e("finger", "body", size="tiny", feel="soft", body_part=True),
    e("thumb", "body", size="tiny", feel="soft", body_part=True),
    e("arm", "body", feel="soft", body_part=True),
    e("elbow", "body", feel="hard", body_part=True),
    e("shoulder", "body", feel="soft", body_part=True),
    e("foot", "body", feel="soft", body_part=True),
    e("toe", "body", size="tiny", feel="soft", body_part=True),
    e("leg", "body", feel="soft", body_part=True),
    e("knee", "body", feel="hard", body_part=True),
    e("head", "body", size="medium", weight="medium", feel="hard", body_part=True),
    e("hair", "body", feel="soft", body_part=True),
    e("face", "body", feel="soft", body_part=True),
    e("eye", "body", size="tiny", feel="soft", body_part=True),
    e("ear", "body", size="tiny", feel="soft", body_part=True),
    e("mouth", "body", size="tiny", feel="soft", body_part=True),
    e("tongue", "body", size="tiny", feel="wet", body_part=True),
    e("gum", "body", size="tiny", feel="soft", body_part=True),
    e("nose", "body", size="tiny", feel="soft", body_part=True),
    e("cheek", "body", feel="soft", body_part=True),
    e("skin", "body", feel="soft", body_part=True),
    e("tummy", "body", feel="soft", body_part=True),
    e("back", "body", feel="soft", body_part=True),
    e("neck", "body", feel="soft", body_part=True),
    e("chest", "body", feel="soft", body_part=True),
)


PEOPLE = (
    e("baby", "person", size="medium", weight="medium", feel="soft", person=True),
    e("mom", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("dad", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("caregiver", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("grandmother", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("grandfather", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("sibling", "person", size="medium", weight="medium", feel="soft", mobile=True, person=True),
    e("brother", "person", size="medium", weight="medium", feel="soft", mobile=True, person=True),
    e("sister", "person", size="medium", weight="medium", feel="soft", mobile=True, person=True),
    e("aunt", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("uncle", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("visitor", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("stranger", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("doctor", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("nurse", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("neighbor", "person", size="big", weight="heavy", feel="soft", mobile=True, person=True),
    e("child", "person", size="medium", weight="medium", feel="soft", mobile=True, person=True),
    e("friend", "person", size="medium", weight="medium", feel="soft", mobile=True, person=True),
)


PLACES_AND_SURFACES = (
    e("floor", "surface", size="big", weight="heavy", feel="hard", mobile=False, support=True, place=True),
    e("bed", "surface", size="big", weight="heavy", feel="soft", mobile=False, support=True, place=True),
    e("crib", "surface", size="big", weight="heavy", feel="hard", mobile=False, container=True, support=True, place=True),
    e("mat", "surface", size="big", weight="medium", feel="soft", mobile=True, support=True, place=True),
    e("table", "surface", size="big", weight="heavy", feel="hard", mobile=False, support=True, place=True),
    e("chair", "surface", size="big", weight="heavy", feel="hard", mobile=False, support=True, place=True),
    e("sofa", "surface", size="big", weight="heavy", feel="soft", mobile=False, support=True, place=True),
    e("shelf", "surface", size="big", weight="heavy", feel="hard", mobile=False, support=True, place=True),
    e("wall", "surface", size="big", weight="heavy", feel="hard", mobile=False, place=True),
    e("door", "place", size="big", weight="heavy", feel="hard", mobile=False, openable=True, place=True),
    e("window", "place", size="big", weight="heavy", feel="hard", mobile=False, openable=True, place=True),
    e("room", "place", size="big", weight="heavy", feel="hard", mobile=False, place=True),
    e("kitchen", "place", size="big", weight="heavy", feel="hard", mobile=False, place=True),
    e("bathroom", "place", size="big", weight="heavy", feel="hard", mobile=False, place=True),
    e("balcony", "place", size="big", weight="heavy", feel="hard", mobile=False, place=True),
    e("doorway", "place", size="big", weight="heavy", feel="hard", mobile=False, openable=True, place=True),
    e("stairs", "place", size="big", weight="heavy", feel="hard", mobile=False, support=True, place=True),
    e("sink", "place", size="medium", weight="heavy", feel="hard", mobile=False, container=True, place=True, can_be_wet=True),
    e("bath", "place", size="big", weight="heavy", feel="hard", mobile=False, container=True, place=True, can_be_wet=True),
    e("garden", "place", size="big", weight="heavy", feel="soft", mobile=False, place=True),
    e("park", "place", size="big", weight="heavy", feel="soft", mobile=False, place=True),
    e("road", "place", size="big", weight="heavy", feel="hard", mobile=False, place=True),
    e("car", "place", size="big", weight="heavy", feel="hard", mobile=False, container=True, openable=True, place=True),
    e("clinic", "place", size="big", weight="heavy", feel="hard", mobile=False, place=True),
    e("lap", "surface", size="medium", weight="medium", feel="soft", mobile=True, support=True, place=True),
    e("arms", "surface", size="medium", weight="medium", feel="soft", mobile=True, support=True, place=True),
    e("highchair", "surface", size="big", weight="heavy", feel="hard", mobile=False, support=True, place=True),
    e("stroller", "surface", size="big", weight="heavy", feel="soft", mobile=True, support=True, container=True, place=True),
)


OBJECTS = (
    e("ball", "toy", feel="soft", sound="quiet"),
    e("rattle", "toy", feel="hard", sound="rattle"),
    e("block", "toy", feel="hard", sound="clack"),
    e("cube", "toy", feel="hard", sound="clack"),
    e("ring", "toy", feel="hard", sound="quiet"),
    e("toy", "toy", feel="soft", sound="quiet"),
    e("doll", "toy", feel="soft", sound="quiet"),
    e("teddy", "toy", size="medium", feel="soft", sound="quiet"),
    e("toy car", "toy", feel="hard", sound="roll"),
    e("cup", "container", feel="hard", sound="clink", container=True, openable=True, can_be_hot=True),
    e("spoon", "object", feel="hard", sound="clink", can_be_hot=True),
    e("bottle", "container", feel="hard", sound="quiet", container=True, openable=True, can_be_hot=True),
    e("bowl", "container", size="medium", feel="hard", sound="clink", container=True, openable=True, can_be_hot=True),
    e("plate", "object", size="medium", feel="hard", sound="clink", can_be_hot=True),
    e("book", "object", size="medium", weight="medium", feel="hard", sound="quiet"),
    e("cloth", "object", size="medium", feel="soft", cover=True),
    e("blanket", "object", size="big", feel="soft", cover=True),
    e("pillow", "object", size="big", feel="soft", cover=True),
    e("towel", "object", size="medium", feel="soft", cover=True),
    e("diaper", "object", size="medium", feel="soft"),
    e("shirt", "object", size="medium", feel="soft"),
    e("sock", "object", size="small", feel="soft"),
    e("shoe", "object", size="medium", weight="medium", feel="hard"),
    e("hat", "object", size="small", feel="soft"),
    e("bag", "container", size="medium", feel="soft", container=True, openable=True),
    e("box", "container", size="medium", feel="hard", container=True, openable=True),
    e("basket", "container", size="medium", feel="hard", container=True, openable=True),
    e("drawer", "container", size="medium", weight="heavy", feel="hard", mobile=False, container=True, openable=True),
    e("cupboard", "container", size="big", weight="heavy", feel="hard", mobile=False, container=True, openable=True),
    e("remote", "object", feel="hard", safe_touch=False),
    e("phone", "object", feel="hard", sound="sound", safe_touch=False),
    e("key", "object", feel="hard", sound="jingle", safe_touch=False),
    e("paper", "object", feel="soft", sound="rustle"),
    e("pen", "object", feel="hard", safe_touch=True),
    e("brush", "object", feel="rough"),
    e("comb", "object", feel="hard"),
    e("mirror", "object", size="medium", weight="medium", feel="hard", fragile=True, safe_touch=False),
    e("pacifier", "object", feel="soft"),
    e("teether", "object", feel="soft"),
    e("soap", "object", feel="smooth", safe_touch=False, can_be_wet=True),
    e("bucket", "container", size="medium", weight="medium", feel="hard", container=True, openable=True, can_be_wet=True),
    e("tray", "object", size="medium", feel="hard"),
    e("lid", "object", feel="hard", cover=True),
    e("cap", "object", feel="hard", cover=True),
    e("bell", "object", feel="hard", sound="ring"),
    e("drum", "object", size="medium", feel="hard", sound="drum"),
    e("whistle", "object", feel="hard", sound="whistle", safe_touch=False),
    e("crayon", "object", feel="hard"),
    e("pencil", "object", feel="hard"),
    e("coin", "object", size="tiny", feel="hard", sound="clink", safe_touch=False),
    e("plug", "object", feel="hard", safe_touch=False, mobile=False),
    e("wire", "object", size="medium", feel="soft", safe_touch=False, mobile=False),
    e("socket", "object", feel="hard", safe_touch=False, mobile=False),
    e("knife", "object", feel="hard", safe_touch=False),
    e("scissor", "object", feel="hard", safe_touch=False),
    e("candle", "object", feel="hard", safe_touch=False, can_be_hot=True),
    e("match", "object", size="tiny", feel="hard", safe_touch=False, can_be_hot=True),
    e("medicine bottle", "container", feel="hard", safe_touch=False, container=True, openable=True),
    e("thermometer", "object", feel="hard", fragile=True, safe_touch=False),
    e("fan", "object", size="big", weight="heavy", feel="hard", mobile=False, sound="sound", safe_touch=False),
    e("lamp", "object", size="big", weight="heavy", feel="hard", mobile=False, safe_touch=False, can_be_hot=True),
)


FOOD_AND_LIQUID = (
    e("milk", "food", size="small", weight="light", feel="wet", sound="quiet", food=True, liquid=True, can_be_hot=True),
    e("water", "food", size="small", weight="light", feel="wet", sound="quiet", food=True, liquid=True, can_be_hot=True),
    e("rice", "food", feel="soft", food=True),
    e("dal", "food", feel="wet", food=True, liquid=True, can_be_hot=True),
    e("curd", "food", feel="wet", food=True),
    e("porridge", "food", feel="wet", food=True, can_be_hot=True),
    e("banana", "food", feel="soft", food=True),
    e("apple", "food", feel="hard", food=True),
    e("mango", "food", feel="soft", food=True),
    e("biscuit", "food", feel="hard", food=True),
    e("bread", "food", feel="soft", food=True),
    e("chapati", "food", feel="soft", food=True),
    e("idli", "food", feel="soft", food=True),
    e("dosa", "food", feel="soft", food=True),
    e("carrot", "food", feel="hard", food=True),
    e("potato", "food", feel="soft", food=True),
    e("pea", "food", size="tiny", feel="soft", food=True),
    e("soup", "food", feel="wet", food=True, liquid=True, can_be_hot=True),
    e("cereal", "food", feel="hard", food=True),
    e("juice", "food", feel="wet", food=True, liquid=True),
    e("medicine", "food", size="tiny", feel="wet", safe_touch=False, food=False, liquid=True),
    e("sugar", "food", size="tiny", feel="hard", food=True),
    e("salt", "food", size="tiny", feel="hard", food=False, safe_touch=False),
    e("oil", "food", feel="wet", food=False, liquid=True, safe_touch=False),
    e("tea", "food", feel="wet", food=False, liquid=True, safe_touch=False, can_be_hot=True),
    e("egg", "food", feel="soft", food=True),
    e("fish", "food", feel="soft", food=True),
    e("spice", "food", size="tiny", feel="hard", food=False, safe_touch=False),
)


NATURE_AND_MATERIALS = (
    e("sand", "material", feel="rough", can_be_wet=True),
    e("mud", "material", feel="wet", safe_touch=False, can_be_wet=True),
    e("stone", "material", weight="medium", feel="hard"),
    e("leaf", "material", feel="soft"),
    e("flower", "material", feel="soft"),
    e("stick", "material", size="medium", feel="hard"),
    e("puddle", "material", size="medium", feel="wet", safe_touch=False, can_be_wet=True),
    e("rain", "material", size="big", feel="wet", mobile=False, can_be_wet=True),
    e("sun", "material", size="big", weight="heavy", feel="hot", mobile=False, safe_touch=False, can_be_hot=True),
    e("wind", "material", size="big", feel="soft", mobile=False),
    e("dust", "material", size="tiny", feel="rough", safe_touch=False),
    e("smoke", "material", size="big", feel="soft", safe_touch=False),
    e("fire", "material", size="medium", feel="hot", safe_touch=False, can_be_hot=True),
    e("shadow", "material", size="big", feel="soft", mobile=False),
    e("light", "material", size="big", feel="soft", mobile=False),
    e("plastic", "material", feel="hard"),
    e("metal", "material", weight="heavy", feel="hard", sound="clink", can_be_hot=True),
    e("wood", "material", weight="medium", feel="hard"),
    e("glass", "material", weight="medium", feel="hard", fragile=True, safe_touch=False),
    e("rubber", "material", feel="soft"),
    e("foam", "material", feel="soft"),
    e("cotton", "material", feel="soft"),
    e("ice", "material", feel="cold", can_be_wet=True),
    e("steam", "material", feel="hot", safe_touch=False, can_be_hot=True),
)


SOCIAL_SIGNALS = (
    e("smile", "social_signal", feel="soft", social_signal=True),
    e("frown", "social_signal", feel="hard", social_signal=True),
    e("cry", "social_signal", feel="wet", sound="cry", social_signal=True),
    e("laugh", "social_signal", feel="soft", sound="laugh", social_signal=True),
    e("clap", "social_signal", feel="hard", sound="clap", social_signal=True),
    e("wave", "social_signal", feel="soft", social_signal=True),
    e("point", "social_signal", feel="soft", social_signal=True),
    e("nod", "social_signal", feel="soft", social_signal=True),
    e("head shake", "social_signal", feel="soft", social_signal=True),
    e("gentle voice", "social_signal", feel="soft", sound="voice", social_signal=True),
    e("loud voice", "social_signal", feel="hard", sound="voice", social_signal=True),
    e("song", "social_signal", feel="soft", sound="song", social_signal=True),
    e("call", "social_signal", feel="hard", sound="voice", social_signal=True),
    e("praise", "social_signal", feel="soft", sound="voice", social_signal=True),
    e("no word", "social_signal", feel="hard", sound="voice", social_signal=True),
    e("yes word", "social_signal", feel="soft", sound="voice", social_signal=True),
    e("hug", "social_signal", feel="soft", social_signal=True),
    e("kiss", "social_signal", feel="soft", social_signal=True),
    e("scold", "social_signal", feel="hard", sound="voice", social_signal=True),
    e("comfort", "social_signal", feel="soft", social_signal=True),
    e("anger", "social_signal", feel="hard", social_signal=True),
    e("play", "social_signal", feel="soft", social_signal=True),
    e("goodbye", "social_signal", feel="soft", sound="voice", social_signal=True),
    e("hello", "social_signal", feel="soft", sound="voice", social_signal=True),
)


ENTITIES = (
    *BODY_PARTS,
    *PEOPLE,
    *PLACES_AND_SURFACES,
    *OBJECTS,
    *FOOD_AND_LIQUID,
    *NATURE_AND_MATERIALS,
    *SOCIAL_SIGNALS,
)

ENTITY_BY_NAME = {item.name: item for item in ENTITIES}
COLORS = ("red", "blue", "yellow", "green", "white", "black", "brown")
SHAPES = ("round", "square", "flat", "long", "thin", "curved")
COUNTS = (0, 1, 2, 3, 4)
FAMILIAR_PEOPLE = ("mom", "dad", "caregiver", "grandmother", "grandfather", "sibling")
UNFAMILIAR_PEOPLE = ("visitor", "stranger", "doctor", "nurse", "neighbor")
AMBIENT_NAMES = {"rain", "sun", "wind", "smoke", "fire", "shadow", "light", "steam"}
LOOSE_LIQUID_NAMES = {"milk", "water", "dal", "curd", "porridge", "soup", "juice", "medicine", "oil", "tea"}
LOOSE_SUBSTANCE_NAMES = {"rice", "cereal", "sugar", "salt", "spice", "sand", "mud", "puddle", "dust"}
PATH_NAMES = {"door", "window", "doorway", "box", "bag", "drawer", "cupboard"}
CONTAINER_TARGETS = {
    "bag": ("ball", "rattle", "block", "book", "toy", "doll", "teddy", "shoe", "hat", "diaper", "shirt", "sock", "cup", "spoon", "bottle", "banana", "apple"),
    "box": ("ball", "rattle", "block", "cube", "ring", "toy", "doll", "book", "cup", "spoon", "bottle", "shoe", "hat", "key", "paper", "pen"),
    "bowl": ("ball", "block", "ring", "spoon", "banana", "apple", "mango", "biscuit", "carrot", "potato", "pea"),
    "drawer": ("spoon", "book", "cloth", "diaper", "shirt", "sock", "hat", "key", "paper", "pen", "brush", "comb", "pacifier", "teether"),
    "cupboard": ("book", "cloth", "blanket", "pillow", "towel", "diaper", "shirt", "sock", "shoe", "bag", "box", "basket"),
    "bucket": ("ball", "block", "toy", "cup", "spoon", "bottle", "cloth", "towel", "ring"),
}


def visible(name: str) -> str:
    return name


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
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def relation_base(item: Entity, include_safety: bool = True) -> list[str]:
    if item.liquid:
        relations = [
            f"{item.name} is wet",
            f"{item.name} can flow",
        ]
        if include_safety:
            if item.safe_touch:
                relations.append(f"{item.name} is ok to touch")
            else:
                relations.append(f"{item.name} is not ok to touch")
        return relations

    relations = [
        f"{item.name} is {item.feel}",
        f"{item.name} is {item.size}",
        f"{item.name} is {item.weight}",
    ]
    if include_safety:
        if item.safe_touch:
            relations.append(f"{item.name} is ok to touch")
        else:
            relations.append(f"{item.name} is not ok to touch")
    if item.mobile:
        relations.append(f"{item.name} can move")
    else:
        relations.append(f"{item.name} does not move")
    return relations


def make_unit(
    rule_family: str,
    scenario: str,
    question_type: str,
    scene: str,
    question: str,
    answer: str,
    main_fact: str,
    relations: list[str],
    negatives: list[str] | None,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": f"procedural.v3.{rule_family}.{slug(scenario)}.{slug(question_type)}",
        "rule_family": rule_family,
        "question_type": question_type,
        "scene": scene,
        "question": question,
        "answer": answer,
        "main_fact": main_fact,
        "relations": relations,
        "negative_relations": negatives or [],
        "metadata": {
            **metadata,
            "question_type": question_type,
        },
    }


def add_question(
    rows: list[dict[str, Any]],
    rule_family: str,
    scenario: str,
    question_type: str,
    scene: str,
    question: str,
    answer: str,
    main_fact: str,
    relations: list[str],
    negatives: list[str] | None,
    metadata: dict[str, Any],
) -> None:
    rows.append(
        make_unit(
            rule_family,
            scenario,
            question_type,
            scene,
            question,
            answer,
            main_fact,
            relations,
            negatives,
            metadata,
        )
    )


def objects_for_touch() -> list[Entity]:
    return [
        item
        for item in ENTITIES
        if not item.person
        and not item.place
        and not item.social_signal
        and item.category != "body"
        and item.category != "material"
        and item.name not in AMBIENT_NAMES
        and item.name not in LOOSE_LIQUID_NAMES
        and item.name not in LOOSE_SUBSTANCE_NAMES
    ]


def manipulable_objects() -> list[Entity]:
    return [
        item
        for item in objects_for_touch()
        if item.category in {"toy", "object", "container"}
        and item.mobile
        and item.weight != "heavy"
    ]


def fallable_objects() -> list[Entity]:
    return [
        item
        for item in objects_for_touch()
        if item.mobile
        and item.weight != "heavy"
        and item.category in {"toy", "object", "container", "food"}
        and item.name not in LOOSE_SUBSTANCE_NAMES
    ]


def items_for_safety() -> list[Entity]:
    safe_items = [item for item in objects_for_touch() if item.safe_touch][:50]
    unsafe_items = [
        item
        for item in ENTITIES
        if not item.person
        and not item.place
        and not item.social_signal
        and item.category != "body"
        and not item.safe_touch
    ]
    return [*safe_items, *unsafe_items]


def count_phrase(count: int, obj: str) -> str:
    words = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four"}
    if count == 1:
        return f"one {obj}"
    plural = obj if obj.endswith("s") else f"{obj}s"
    return f"{words[count]} {plural}"


def reach_touch_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    layouts = [
        ("on floor near baby", "floor", "low", "near", True, "baby reaches hand"),
        ("on bed near baby", "bed", "middle", "near", True, "baby reaches hand"),
        ("beside hand on mat", "mat", "middle", "near", True, "baby closes hand"),
        ("on table far from baby", "table", "high", "far", False, "baby reaches hand"),
        ("on high shelf", "shelf", "very high", "far", False, "baby lifts hand up"),
        ("behind closed door", "door", "blocked", "near", False, "baby reaches hand"),
    ]
    for item in objects_for_touch():
        for label, surface, height, distance, reached, action in layouts:
            scene = f"{item.name} is {label}. {action}."
            place_relation = f"{item.name} is behind {surface}" if height == "blocked" else f"{item.name} is on {surface}"
            relations = [
                "baby can move hand",
                f"{item.name} is {distance}",
                f"{item.name} is {height}",
                place_relation,
                *relation_base(item),
            ]
            negatives: list[str] = []
            if reached:
                relations.extend([f"hand touches {item.name}", f"baby feels {item.name}"])
                if item.mobile and item.weight != "heavy":
                    relations.append(f"hand can make {item.name} move")
                answer = "yes"
                fact = f"hand touches {item.name}"
                positive = True
            else:
                negatives.extend([f"hand does not touch {item.name}", f"baby does not feel {item.name}"])
                if distance == "far":
                    negatives.append(f"{item.name} is too far")
                if height == "very high":
                    negatives.append(f"{item.name} is too high")
                if height == "blocked":
                    negatives.append(f"closed door blocks hand")
                answer = "no"
                fact = f"hand does not touch {item.name}"
                positive = False
            meta = {
                "thing": item.name,
                "category": item.category,
                "surface": surface,
                "height": height,
                "distance": distance,
                "action": action,
                "outcome": "touch" if reached else "no_touch",
                "positive": positive,
            }
            scenario = f"{item.name}.{surface}.{height}.{distance}.{action}"
            add_question(rows, "reach_touch", scenario, "touch", scene, f"does hand touch {item.name}?", answer, fact, relations, negatives, meta)
            add_question(rows, "reach_touch", scenario, "feel", scene, f"does baby feel {item.name}?", "yes" if reached else "no", f"baby {'feels' if reached else 'does not feel'} {item.name}", relations, negatives, meta)
            if reached:
                ok = item.safe_touch
                ok_fact = f"{item.name} is {'ok' if ok else 'not ok'} to touch"
                add_question(rows, "reach_touch", scenario, "ok_touch", scene, "is touch ok?", "yes" if ok else "no", ok_fact, relations, negatives if ok else [f"touching {item.name} can hurt baby"], {**meta, "positive": ok})
            else:
                reason = negatives[-1] if negatives else fact
                add_question(rows, "reach_touch", scenario, "why_no_touch", scene, "why no touch?", reason, reason, relations, negatives, meta)
    return rows


def push_pull_move_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    actions = (("pushes", "push"), ("pulls", "pull"))
    heavy_examples = [
        ENTITY_BY_NAME[name]
        for name in ("lamp", "fan", "table", "chair", "door")
        if name in ENTITY_BY_NAME
    ]
    for item in [*manipulable_objects(), *heavy_examples]:
        for verb, action in actions:
            for near in (True, False):
                scene = f"{item.name} is {'near baby' if near else 'far from baby'}. baby {verb} {item.name}."
                can_move = near and item.mobile and item.weight != "heavy"
                relations = [
                    f"{item.name} is {'near' if near else 'far'}",
                    f"baby {verb} {item.name}",
                    *relation_base(item),
                ]
                negatives: list[str] = []
                if can_move:
                    relations.append(f"hand makes {item.name} move")
                    answer = "yes"
                    fact = f"hand makes {item.name} move"
                else:
                    if not near:
                        negatives.append(f"{item.name} is too far")
                    if not item.mobile or item.weight == "heavy":
                        negatives.append(f"{item.name} resists movement")
                    negatives.append(f"hand cannot make {item.name} move")
                    answer = "no"
                    fact = f"hand cannot make {item.name} move"
                meta = {"thing": item.name, "action": action, "outcome": "move" if can_move else "no_move", "positive": can_move}
                scenario = f"{action}.{item.name}.{near}"
                add_question(rows, "push_pull_move", scenario, "move", scene, f"can hand make {item.name} move?", answer, fact, relations, negatives, meta)
                add_question(rows, "push_pull_move", scenario, "why", scene, "why?", fact if can_move else negatives[0], fact if can_move else negatives[0], relations, negatives, meta)
    return rows


def body_control_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    movable_body = {"hand", "finger", "thumb", "arm", "foot", "toe", "leg", "head", "mouth", "tongue"}
    for part in BODY_PARTS:
        can_move = part.name in movable_body
        scene = f"baby tries to move {part.name}."
        relations = [f"{part.name} is body", "baby has body"]
        negatives: list[str] = []
        if can_move:
            relations.extend([f"baby can move {part.name}", f"{part.name} moves with baby"])
            answer = "yes"
            fact = f"baby can move {part.name}"
        else:
            relations.append(f"{part.name} is body")
            negatives.append(f"baby cannot easily move {part.name}")
            answer = "no"
            fact = f"baby cannot easily move {part.name}"
        meta = {"thing": part.name, "outcome": "body_control" if can_move else "weak_body_control", "positive": can_move}
        add_question(rows, "body_control", part.name, "can_move", scene, f"can baby move {part.name}?", answer, fact, relations, negatives, meta)
        add_question(rows, "body_control", part.name, "is_body", scene, f"is {part.name} body?", "yes", f"{part.name} is body", relations, negatives, {**meta, "positive": True})

    for item_name in ("ball", "cup", "door", "lamp", "table", "mom", "stranger"):
        item = ENTITY_BY_NAME[item_name]
        scene = f"baby tries to move {item.name} like body."
        relations = [f"{item.name} is not body", "baby has body"]
        negatives = [f"baby does not directly control {item.name}"]
        meta = {"thing": item.name, "outcome": "not_body", "positive": False}
        add_question(rows, "body_control", item.name, "is_body", scene, f"is {item.name} body?", "no", f"{item.name} is not body", relations, negatives, meta)
        add_question(rows, "body_control", item.name, "direct_control", scene, f"does baby directly control {item.name}?", "no", f"baby does not directly control {item.name}", relations, negatives, meta)
    return rows


def drop_fall_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates = fallable_objects()
    for item in candidates:
        for in_hand in (True, False):
            scene = f"{item.name} is {'in hand' if in_hand else 'on floor'}. baby opens hand."
            relations = [*relation_base(item)]
            negatives: list[str] = []
            if in_hand:
                relations.extend([f"{item.name} is in hand", f"{item.name} falls down", f"{item.name} hits floor"])
                answer = "yes"
                fact = f"{item.name} falls down"
            else:
                relations.append(f"{item.name} is on floor")
                negatives.append(f"{item.name} does not fall")
                answer = "no"
                fact = f"{item.name} does not fall"
            meta = {"thing": item.name, "outcome": "fall" if in_hand else "no_fall", "positive": in_hand}
            scenario = f"{item.name}.{in_hand}"
            add_question(rows, "drop_fall", scenario, "fall", scene, f"does {item.name} fall?", answer, fact, relations, negatives, meta)
            add_question(rows, "drop_fall", scenario, "in_hand", scene, f"is {item.name} in hand?", "yes" if in_hand else "no", f"{item.name} {'is' if in_hand else 'is not'} in hand", relations, negatives, meta)
    return rows


def support_edge_fall_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    surfaces = ("table", "bed", "chair", "sofa")
    candidates = fallable_objects()[:80]
    for item in candidates:
        for surface in surfaces:
            for edge in (True, False):
                layout = f"{'edge' if edge else 'middle'} of {surface}"
                scene = f"{item.name} is on {layout}. baby bumps {surface}."
                relations = [f"{item.name} is on {layout}", f"baby bumps {surface}", *relation_base(item)]
                negatives: list[str] = []
                if edge:
                    relations.extend([f"{item.name} is at edge", f"{item.name} falls down"])
                    answer = "yes"
                    fact = f"{item.name} falls down"
                else:
                    relations.extend([f"{item.name} is not at edge", f"{item.name} stays on {surface}"])
                    negatives.append(f"{item.name} does not fall")
                    answer = "no"
                    fact = f"{item.name} does not fall"
                meta = {"thing": item.name, "surface": surface, "outcome": "fall" if edge else "no_fall", "positive": edge}
                scenario = f"{item.name}.{surface}.{edge}"
                add_question(rows, "support_edge_fall", scenario, "fall", scene, f"does {item.name} fall?", answer, fact, relations, negatives, meta)
                add_question(rows, "support_edge_fall", scenario, "edge", scene, f"is {item.name} at edge?", "yes" if edge else "no", f"{item.name} {'is' if edge else 'is not'} at edge", relations, negatives, meta)
    return rows


def container_access_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    containers = [ENTITY_BY_NAME[name] for name in CONTAINER_TARGETS if name in ENTITY_BY_NAME]
    for container in containers:
        targets = [ENTITY_BY_NAME[name] for name in CONTAINER_TARGETS[container.name] if name in ENTITY_BY_NAME]
        for target in targets:
            for open_state in (True, False):
                scene = f"{target.name} is in {'open' if open_state else 'closed'} {container.name}. baby puts hand on {container.name}."
                relations = [f"{container.name} can hold {target.name}", f"{target.name} is in {container.name}", *relation_base(target)]
                negatives: list[str] = []
                if open_state:
                    relations.extend([f"{container.name} is open", f"hand touches {target.name}"])
                    answer = "yes"
                    fact = f"hand touches {target.name}"
                else:
                    relations.append(f"{container.name} is closed")
                    negatives.extend([f"closed {container.name} blocks hand", f"hand does not touch {target.name}"])
                    answer = "no"
                    fact = f"hand does not touch {target.name}"
                meta = {"thing": target.name, "container": container.name, "outcome": "touch" if open_state else "blocked", "positive": open_state}
                scenario = f"{container.name}.{target.name}.{open_state}"
                add_question(rows, "container_open_closed", scenario, "touch", scene, f"does hand touch {target.name}?", answer, fact, relations, negatives, meta)
                add_question(rows, "container_open_closed", scenario, "open", scene, f"is {container.name} open?", "yes" if open_state else "no", f"{container.name} is {'open' if open_state else 'closed'}", relations, negatives, meta)
                if not open_state:
                    add_question(rows, "container_open_closed", scenario, "block", scene, "what blocks hand?", f"closed {container.name}", f"closed {container.name} blocks hand", relations, negatives, meta)
    return rows


def hide_see_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    covers = [item for item in ENTITIES if item.cover][:8]
    targets = [item for item in objects_for_touch() if item.size in {"tiny", "small", "medium"}][:60]
    for t_index, target in enumerate(targets):
        cover = covers[t_index % len(covers)]
        for covered in (True, False):
            scene = f"{target.name} is {'under ' + cover.name if covered else 'on floor'}. baby looks."
            relations = ["baby can see", *relation_base(target)]
            negatives: list[str] = []
            if covered:
                relations.append(f"{cover.name} covers {target.name}")
                negatives.append(f"baby does not see {target.name}")
                answer = "no"
                fact = f"baby does not see {target.name}"
            else:
                relations.append(f"baby sees {target.name}")
                answer = "yes"
                fact = f"baby sees {target.name}"
            meta = {"thing": target.name, "cover": cover.name, "outcome": "see" if not covered else "no_see", "positive": not covered}
            scenario = f"{target.name}.{cover.name}.{covered}"
            add_question(rows, "hide_see", scenario, "see", scene, f"does baby see {target.name}?", answer, fact, relations, negatives, meta)
            if covered:
                add_question(rows, "hide_see", scenario, "cover", scene, f"what covers {target.name}?", cover.name, f"{cover.name} covers {target.name}", relations, negatives, meta)
    return rows


def sound_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sound_items = [item for item in ENTITIES if item.sound != "quiet" and not item.social_signal]
    quiet_items = [item for item in objects_for_touch() if item.sound == "quiet"][:30]
    for item in [*sound_items, *quiet_items]:
        makes_sound = item.sound != "quiet"
        scene = f"baby shakes {item.name}."
        relations = [f"baby shakes {item.name}", *relation_base(item)]
        negatives: list[str] = []
        if makes_sound:
            relations.extend([f"{item.name} makes sound", f"baby hears {item.sound}"])
            answer = "yes"
            fact = f"{item.name} makes sound"
        else:
            negatives.append(f"{item.name} does not make sound")
            answer = "no"
            fact = f"{item.name} does not make sound"
        meta = {"thing": item.name, "sound": item.sound, "outcome": "sound" if makes_sound else "no_sound", "positive": makes_sound}
        add_question(rows, "shake_sound", item.name, "hear_sound", scene, "does baby hear sound?", answer, fact, relations, negatives, meta)
    return rows


def temperature_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates = [
        item
        for item in ENTITIES
        if item.can_be_hot and item.name not in {"sun", "fire", "smoke", "steam"}
    ][:35]
    for item in candidates:
        for temp in ("cold", "warm", "hot"):
            scene = f"{item.name} is {temp}. baby touches {item.name}."
            relations = [f"{item.name} is {temp}", f"hand touches {item.name}", *relation_base(item, include_safety=False)]
            negatives: list[str] = []
            ok = temp != "hot" and item.safe_touch
            if ok:
                relations.append(f"touching {item.name} is ok")
                answer = "yes"
                fact = f"touching {item.name} is ok"
            else:
                negatives.extend([f"touching {item.name} can hurt baby", "baby not ok"])
                answer = "no"
                fact = f"touching {item.name} is not ok"
            meta = {"thing": item.name, "temperature": temp, "outcome": "ok_touch" if ok else "not_ok_touch", "positive": ok}
            add_question(rows, "temperature_touch", f"{item.name}.{temp}", "ok_touch", scene, "is touch ok?", answer, fact, relations, negatives, meta)
    return rows


def wet_dry_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates = [
        item
        for item in ENTITIES
        if item.can_be_wet
        and not item.person
        and not item.social_signal
        and item.category != "body"
        and item.category != "place"
        and not item.liquid
        and item.name not in AMBIENT_NAMES
        and item.name not in LOOSE_SUBSTANCE_NAMES
        and item.name != "arms"
    ][:80]
    for item in candidates:
        for wet in (True, False):
            scene = f"{item.name} is {'wet' if wet else 'dry'}. baby touches {item.name}."
            relations = [f"{item.name} is {'wet' if wet else 'dry'}", f"hand touches {item.name}", *relation_base(item)]
            answer = "wet" if wet else "dry"
            fact = f"{item.name} is {'wet' if wet else 'dry'}"
            meta = {"thing": item.name, "outcome": "wet" if wet else "dry", "positive": not wet}
            add_question(rows, "wet_dry", f"{item.name}.{wet}", "wet_or_dry", scene, f"is {item.name} wet or dry?", answer, fact, relations, [], meta)
    return rows


def safe_unsafe_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items_for_safety():
        scene = f"{item.name} is near baby. baby reaches hand."
        relations = [f"{item.name} is near", *relation_base(item)]
        negatives: list[str] = []
        if item.safe_touch:
            relations.append(f"{item.name} is ok to touch")
            answer = "yes"
            fact = f"{item.name} is ok to touch"
        else:
            negatives.extend([f"{item.name} is not ok to touch", f"{item.name} can hurt baby"])
            answer = "no"
            fact = f"{item.name} is not ok to touch"
        meta = {"thing": item.name, "outcome": "safe" if item.safe_touch else "unsafe", "positive": item.safe_touch}
        add_question(rows, "safe_unsafe_touch", item.name, "ok_touch", scene, f"is {item.name} ok to touch?", answer, fact, relations, negatives, meta)
    return rows


def same_different_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    objects = [
        item
        for item in objects_for_touch()
        if item.size in {"tiny", "small", "medium"} and item.mobile
    ][:36]
    for index, left in enumerate(objects):
        right = objects[(index + 7) % len(objects)]
        for color_a in COLORS:
            color_options = (color_a, COLORS[(COLORS.index(color_a) + index + 1) % len(COLORS)])
            for color_b in dict.fromkeys(color_options):
                same = color_a == color_b
                scene = f"{color_a} {left.name} is here. {color_b} {right.name} is here. baby looks."
                relations = [f"{left.name} is {color_a}", f"{right.name} is {color_b}"]
                negatives = [] if same else [f"{color_a} is not {color_b}"]
                fact = "same color" if same else "different color"
                meta = {"thing": f"{left.name}_{right.name}", "outcome": fact.replace(" ", "_"), "positive": same}
                add_question(rows, "same_different_match", f"{left.name}.{right.name}.{color_a}.{color_b}", "same_color", scene, "same color?", "yes" if same else "no", fact, relations, negatives, meta)
        shape_a = SHAPES[index % len(SHAPES)]
        shape_b = SHAPES[(index + 2) % len(SHAPES)]
        same_shape = shape_a == shape_b
        scene = f"{left.name} is {shape_a}. {right.name} is {shape_b}. baby looks."
        relations = [f"{left.name} is {shape_a}", f"{right.name} is {shape_b}"]
        negatives = [] if same_shape else [f"{shape_a} is not {shape_b}"]
        fact = "same shape" if same_shape else "different shape"
        meta = {"thing": f"{left.name}_{right.name}", "outcome": fact.replace(" ", "_"), "positive": same_shape}
        add_question(rows, "same_different_match", f"{left.name}.{right.name}.{shape_a}.{shape_b}", "same_shape", scene, "same shape?", "yes" if same_shape else "no", fact, relations, negatives, meta)
    return rows


def more_less_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    objects = [
        item.name
        for item in objects_for_touch()
        if item.size in {"tiny", "small"} and item.mobile
    ][:18]
    for obj in objects:
        for left in COUNTS:
            for right in COUNTS:
                if left == right:
                    continue
                scene = f"left has {count_phrase(left, obj)}. right has {count_phrase(right, obj)}. baby looks."
                more_side = "left" if left > right else "right"
                less_side = "right" if left > right else "left"
                relations = [f"left has {left}", f"right has {right}", f"{more_side} has more", f"{less_side} has less"]
                meta = {"thing": obj, "left_count": left, "right_count": right, "outcome": f"{more_side}_has_more", "positive": True}
                scenario = f"{obj}.{left}.{right}"
                add_question(rows, "more_less_count", scenario, "more", scene, "which has more?", more_side, f"{more_side} has more", relations, [], meta)
                add_question(rows, "more_less_count", scenario, "less", scene, "which has less?", less_side, f"{less_side} has less", relations, [], meta)
    return rows


def path_open_closed_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = [item for item in ENTITIES if item.openable and item.name in PATH_NAMES][:18]
    moving = [item for item in objects_for_touch() if item.mobile and item.weight != "heavy"][:24]
    for p_index, path in enumerate(paths):
        for item in moving[p_index % 4 :: 4][:6]:
            for open_state in (True, False):
                scene = f"{path.name} is {'open' if open_state else 'closed'}. baby pushes {item.name} to {path.name}."
                relations = [f"{path.name} is {'open' if open_state else 'closed'}", *relation_base(item)]
                negatives: list[str] = []
                if open_state:
                    relations.append(f"{item.name} can go through {path.name}")
                    answer = "yes"
                    fact = f"{item.name} can go through {path.name}"
                else:
                    negatives.extend([f"closed {path.name} blocks {item.name}", f"{item.name} cannot go through {path.name}"])
                    answer = "no"
                    fact = f"{item.name} cannot go through {path.name}"
                meta = {"thing": item.name, "path": path.name, "outcome": "go_through" if open_state else "blocked", "positive": open_state}
                scenario = f"{path.name}.{item.name}.{open_state}"
                add_question(rows, "path_open_closed", scenario, "go_through", scene, f"can {item.name} go through?", answer, fact, relations, negatives, meta)
                add_question(rows, "path_open_closed", scenario, "open", scene, f"is {path.name} open?", "yes" if open_state else "no", f"{path.name} is {'open' if open_state else 'closed'}", relations, negatives, meta)
    return rows


def caregiver_comfort_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cases = [
        ("baby is hungry", "mom gives milk", "milk helps baby", True),
        ("baby is hungry", "bottle is empty", "empty bottle does not help baby", False),
        ("baby is wet", "dad changes diaper", "dry diaper helps baby", True),
        ("baby is wet", "no one comes", "wet diaper does not help baby", False),
        ("baby is sleepy", "caregiver rocks baby", "rocking helps baby", True),
        ("baby is sleepy", "loud voice continues", "loud voice does not help baby", False),
        ("baby hears loud sound", "mom holds baby", "mom hold helps baby", True),
        ("baby feels pain", "caregiver comes near", "caregiver near helps baby", True),
        ("baby feels pain", "caregiver is far", "caregiver far does not help baby", False),
        ("baby is bored", "sibling plays peekaboo", "play helps baby", True),
        ("baby is scared", "stranger comes near fast", "stranger near does not help baby", False),
        ("baby is calm", "mom smiles", "smile keeps baby ok", True),
    ]
    for index, (state, action, fact, ok) in enumerate(cases, start=1):
        scene = f"{state}. {action}."
        relations = ["baby not ok" if not state.endswith("calm") else "baby ok"]
        negatives: list[str] = []
        if ok:
            relations.extend([fact, "baby ok"])
            answer = "yes"
            main_fact = "baby ok"
        else:
            negatives.append(fact)
            answer = "no"
            main_fact = "baby not ok"
        meta = {"thing": "baby", "outcome": "comfort" if ok else "no_comfort", "positive": ok}
        add_question(rows, "caregiver_comfort", str(index), "ok", scene, "is baby ok?", answer, main_fact, relations, negatives, meta)
        add_question(rows, "caregiver_comfort", str(index), "help", scene, "what helps?", fact if ok else "nothing", fact, relations, negatives, meta)
    return rows


def familiar_agent_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for person in [*FAMILIAR_PEOPLE, *UNFAMILIAR_PEOPLE]:
        familiar = person in FAMILIAR_PEOPLE
        scene = f"{person} comes near baby. baby looks at {person}."
        relations = [f"{person} is person", f"{person} is {'familiar' if familiar else 'unfamiliar'}"]
        negatives = [] if familiar else [f"baby does not know {person} well"]
        meta = {"thing": person, "outcome": "familiar" if familiar else "unfamiliar", "positive": familiar}
        add_question(rows, "familiar_agent", person, "familiar", scene, f"is {person} familiar?", "yes" if familiar else "no", f"{person} is {'familiar' if familiar else 'unfamiliar'}", relations, negatives, meta)
    return rows


def social_signal_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cases = [
        ("mom smiles", "smile", True, "smile helps baby"),
        ("dad speaks gentle voice", "gentle voice", True, "gentle voice helps baby"),
        ("caregiver sings song", "song", True, "song helps baby"),
        ("stranger frowns", "frown", False, "frown does not help baby"),
        ("visitor speaks loud voice", "loud voice", False, "loud voice does not help baby"),
        ("doctor gives injection", "pain", False, "pain makes baby not ok"),
        ("sibling claps", "clap", True, "clap can make baby look"),
        ("mom points to ball", "point", True, "point guides baby look"),
    ]
    for index, (scene, signal, ok, fact) in enumerate(cases, start=1):
        full_scene = f"{scene}. baby sees and hears."
        relations = [f"signal is {signal}", fact]
        negatives: list[str] = []
        if ok:
            relations.append("baby ok")
            answer = "yes"
            main_fact = "baby ok"
        else:
            negatives.append("baby not ok")
            answer = "no"
            main_fact = "baby not ok"
        meta = {"thing": signal, "outcome": "social_ok" if ok else "social_not_ok", "positive": ok}
        add_question(rows, "social_signal_response", str(index), "ok", full_scene, "is baby ok?", answer, main_fact, relations, negatives, meta)
        add_question(rows, "social_signal_response", str(index), "signal", full_scene, "what signal?", signal, f"signal is {signal}", relations, negatives, meta)
    return rows


def give_take_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    objects = ("ball", "rattle", "cup", "spoon", "book", "banana", "bottle", "toy")
    agents = ("mom", "dad", "sibling", "stranger")
    for agent in agents:
        for obj in objects:
            for gives in (True, False):
                scene = f"{agent} {'gives' if gives else 'takes'} {obj}. baby looks."
                relations = [f"{agent} is person", f"{obj} is object"]
                negatives: list[str] = []
                if gives:
                    relations.extend([f"{agent} gives {obj}", f"baby has {obj}"])
                    answer = "yes"
                    fact = f"baby has {obj}"
                else:
                    relations.append(f"{agent} takes {obj}")
                    negatives.append(f"baby does not have {obj}")
                    answer = "no"
                    fact = f"baby does not have {obj}"
                meta = {"thing": obj, "agent": agent, "outcome": "has_object" if gives else "lost_object", "positive": gives}
                scenario = f"{agent}.{obj}.{gives}"
                add_question(rows, "give_take", scenario, "has_object", scene, f"does baby have {obj}?", answer, fact, relations, negatives, meta)
    return rows


def word_name_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    names = [
        "ball", "cup", "book", "spoon", "toy", "bottle", "shoe", "door",
        "mom", "dad", "hand", "milk", "banana", "dog", "cat", "car",
        "bed", "water", "rattle", "box", "chair", "phone", "key", "flower",
    ]
    visible_names = [name for name in names if name in ENTITY_BY_NAME]
    for index, word in enumerate(visible_names):
        candidates = [word, visible_names[(index + 5) % len(visible_names)], visible_names[(index + 11) % len(visible_names)]]
        for obj in candidates:
            match = word == obj
            scene = f"mom says {word}. {obj} is here. baby looks."
            relations = [f"word {word} names {word}", f"{obj} is here"]
            negatives = [] if match else [f"word {word} does not name {obj}"]
            meta = {"thing": obj, "word": word, "outcome": "name_match" if match else "name_mismatch", "positive": match}
            add_question(rows, "word_name_binding", f"{word}.{obj}", "word_match", scene, f"does word name {obj}?", "yes" if match else "no", f"word {word} {'names' if match else 'does not name'} {obj}", relations, negatives, meta)
            if match:
                add_question(rows, "word_name_binding", f"{word}.{obj}", "what_name", scene, "what does word name?", obj, f"word {word} names {obj}", relations, negatives, meta)
    return rows


def generate_units() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for generator in (
        reach_touch_units,
        push_pull_move_units,
        body_control_units,
        drop_fall_units,
        support_edge_fall_units,
        container_access_units,
        hide_see_units,
        sound_units,
        temperature_units,
        wet_dry_units,
        safe_unsafe_units,
        same_different_units,
        more_less_units,
        path_open_closed_units,
        caregiver_comfort_units,
        familiar_agent_units,
        social_signal_units,
        give_take_units,
        word_name_units,
    ):
        rows.extend(generator())
    seen: set[str] = set()
    unique_rows: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: item["id"]):
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        unique_rows.append(row)
    return unique_rows


def split_units(units: list[dict[str, Any]], seed: int) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in units:
        meta = row["metadata"]
        key = f"{row['rule_family']}|{row['question_type']}|{meta.get('positive', '')}"
        grouped[key].append(row)

    rng = random.Random(seed)
    splits = {split: [] for split in SPLITS}
    for key in sorted(grouped):
        rows = grouped[key][:]
        rng.shuffle(rows)
        total = len(rows)
        if total <= 1:
            train_count = total
            dev_count = 0
        elif total == 2:
            train_count = 1
            dev_count = 0
        elif total == 3:
            train_count = 2
            dev_count = 0
        else:
            train_count = int(total * 0.8)
            dev_count = int(total * 0.1)
            if dev_count == 0:
                dev_count = 1
                train_count -= 1
        for row in rows[:train_count]:
            splits["train"].append(row)
        for row in rows[train_count : train_count + dev_count]:
            splits["dev"].append(row)
        for row in rows[train_count + dev_count :]:
            splits["curriculum_test"].append(row)

    for split in SPLITS:
        splits[split] = sorted(splits[split], key=lambda row: row["id"])
    return splits


def render_pair(variant: str, row: dict[str, Any]) -> tuple[str, str]:
    input_lines = [f"s: {row['scene']}", f"q: {row['question']}", "a:"]
    target_lines = [f"a: {row['answer']}", f"f: {row['main_fact']}"]
    relation_lines = [f"r: {rel}" for rel in row["relations"]]
    negative_lines = [f"n: {rel}" for rel in row["negative_relations"]]
    if variant == "procedural_plain_text":
        return "\n".join(input_lines), "\n".join(target_lines)
    if variant == "procedural_relation_scaffolded":
        return "\n".join(input_lines), "\n".join(target_lines + relation_lines + negative_lines)
    if variant == "procedural_relation_first_then_text":
        return "\n".join(relation_lines + negative_lines + input_lines), "\n".join(target_lines)
    raise ValueError(f"unknown variant: {variant}")


def make_record(experiment_id: str, variant: str, split: str, row: dict[str, Any]) -> dict[str, Any]:
    input_text, target_text = render_pair(variant, row)
    return {
        "id": f"dataset.{experiment_id}.{variant}.{row['id']}",
        "source_example_id": row["id"],
        "experiment_id": experiment_id,
        "variant": variant,
        "split": split,
        "task_type": row["rule_family"],
        "input": input_text,
        "target": target_text,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target_text},
        ],
        "metadata": {
            **row["metadata"],
            "domain_id": "procedural_foundation_world",
            "rule_family": row["rule_family"],
            "representation": variant,
        },
    }


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
    return dict(sorted(Counter(row.get(key, "unknown") for row in rows).items()))


def nested_count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("metadata", {}).get(key, "unknown")).lower() for row in rows).items()))


def file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        name: {"path": str(path), "sha256": sha256_file(path)}
        for name, path in sorted(paths.items())
    }


def build_base_world() -> dict[str, Any]:
    category_counts = Counter(item.category for item in ENTITIES)
    return {
        "schema_version": "0.1.0",
        "world_id": "procedural_foundation_v3_world",
        "purpose": "Expanded baby + physical + simple social base world for procedural relation generation.",
        "scope": {
            "included": ["baby body", "household objects", "food and liquid", "places and surfaces", "simple social agents", "simple social signals", "primitive comparison"],
            "excluded_for_now": ["formal arithmetic", "formal logic", "history", "geography", "medicine as expert domain", "adult institutions"],
        },
        "counts": {
            "entities": len(ENTITIES),
            "categories": dict(sorted(category_counts.items())),
            "colors": len(COLORS),
            "shapes": len(SHAPES),
            "counts": len(COUNTS),
        },
        "entities": [asdict(item) for item in ENTITIES],
        "primitive_values": {
            "colors": list(COLORS),
            "shapes": list(SHAPES),
            "counts": list(COUNTS),
            "familiar_people": list(FAMILIAR_PEOPLE),
            "unfamiliar_people": list(UNFAMILIAR_PEOPLE),
        },
    }


def build_training_config(experiment_id: str, output_dir: Path, dataset_manifest: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "baseline_model": {
            "name": "nanochat",
            "role": "from-scratch local smoke and later one-GPU signal testing",
            "reason": "V3 is designed for shared-tokenizer nanochat comparison.",
        },
        "dataset_manifest": str(dataset_manifest),
        "output_root": f"runs/{experiment_id}/nanochat",
        "format": {
            "prompt_template": "{input}\n",
            "target_template": "{target}",
        },
        "training": {
            "max_seq_length": 512,
            "seed": 1729,
            "note": "Use nanochat conversion script before training; this config is a dataset contract, not a full nanochat run config.",
        },
        "frozen_commands": {
            variant: f"python3 scripts/train_tiny_causal_lm.py --config {output_dir / 'training_config.json'} --variant {variant} --dry-run"
            for variant in VARIANTS
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/procedural_foundation_v3"),
    )
    parser.add_argument("--experiment-id", default="procedural_foundation_v3")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ensure_output_dir(args.output_dir, args.overwrite)
    base_world_path = args.output_dir / "base_world.json"
    write_json(base_world_path, build_base_world())

    units = generate_units()
    splits = split_units(units, args.seed)
    for split, rows in splits.items():
        write_jsonl(args.output_dir / f"{split}.jsonl", rows)

    records: dict[str, dict[str, list[dict[str, Any]]]] = {
        variant: {split: [] for split in SPLITS}
        for variant in VARIANTS
    }
    output_paths: dict[str, Path] = {}
    for variant in VARIANTS:
        for split in SPLITS:
            rows = [make_record(args.experiment_id, variant, split, row) for row in splits[split]]
            records[variant][split] = rows
            path = args.output_dir / "datasets" / variant / f"{split}.jsonl"
            write_jsonl(path, rows)
            output_paths[f"{variant}.{split}"] = path

    dataset_manifest_path = args.output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "output_dir": str(args.output_dir / "datasets"),
        "base_world": str(base_world_path),
        "source": {
            "rule_families": sorted({row["rule_family"] for row in units}),
            "question_types": sorted({row["question_type"] for row in units}),
        },
        "variants": {
            variant: {
                split: {
                    "total": len(records[variant][split]),
                    "task_type_counts": count_by(records[variant][split], "task_type"),
                    "question_type_counts": nested_count(records[variant][split], "question_type"),
                    "outcome_counts": nested_count(records[variant][split], "outcome"),
                    "positive_counts": nested_count(records[variant][split], "positive"),
                    "vocabulary": vocab_stats(records[variant][split]),
                }
                for split in SPLITS
            }
            for variant in VARIANTS
        },
        "outputs": file_manifest(output_paths),
        "notes": [
            "V3 expands base entities before expanding row count.",
            "V3 combines baby, physical, and simple social worlds.",
            "Formal math is excluded except primitive comparison roots.",
            "Scenario grammars remain rule-family owned and coherent.",
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
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "base_world": str(base_world_path),
        "base_world_counts": build_base_world()["counts"],
        "total_units": len(units),
        "splits": {split: len(rows) for split, rows in splits.items()},
        "variants": list(VARIANTS),
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
