#!/usr/bin/env python3
"""World simulator v0: rule-based episodes rendered as QA rows.

Every answer is computed from a small simulated world (objects, containers,
surfaces, a baby, caregivers, and relation strengths for affect). Sentences are
rendered from many templates after the answer is known, so the text never
decides the truth.

Lexical sources:
  - A curated property table (size, weight, round, hard, noisy, ...). WordNet has
    no weight or bounce data, so physics properties stay hand-written.
  - WordNet: checks each object's kind (container, food, toy, clothing, ...)
    against the table, and picks the held-out "new object" for each kind by
    taxonomy similarity (Wu-Palmer) to the training objects.
  - Word closeness (MiniLM embeddings, optional): ranks plausible pairings that
    already pass the physical rules, e.g. spoon -> bowl, sock -> basket, and
    which objects belong in which room. Without embeddings, falls back to
    hand-written room tags.

Affect follows the project formula:
  happiness_gain = rate * (1 - current_strength)
  sadness        = lost_link_strength * (1 + density_bonus)

Outputs (gitignored experiment folder):
  train.jsonl, dev.jsonl, test_iid.jsonl, test_new_object.jsonl,
  test_new_wording.jsonl, manifest.json, quality_report.json

The --audit mode runs the same quality checks on an existing dataset folder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

EXPERIMENT_ID = "world_sim_v0"
DEFAULT_OUTPUT = Path("data/developmental_graph/experiments/world_sim_v0")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Lexicon
# ---------------------------------------------------------------------------

# size: 1 tiny, 2 small, 3 medium, 4 big
# container: None | "lid" (closes, hides inside) | "open" (no lid) | "clear_lid"
#            (closes, but you can see inside)
# kind must match a WordNet check in KIND_HYPERNYMS.
OBJECTS: dict[str, dict[str, Any]] = {
    # toys
    "ball":       dict(kind="toy", size=2, heavy=False, round=True, bouncy=True, hard=False, noisy=False, breakable=False, rooms=["play room", "living room"]),
    "rattle":     dict(kind="toy", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=True, breakable=False, rooms=["play room", "bedroom"]),
    "block":      dict(kind="toy", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["play room"]),
    "doll":       dict(kind="toy", size=2, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["play room", "bedroom"]),
    "toy car":    dict(kind="toy", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rolls=True, rooms=["play room", "living room"]),
    "ring toy":   dict(kind="toy", size=1, heavy=False, round=True, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["play room"]),
    "balloon":    dict(kind="toy", size=2, heavy=False, round=True, bouncy=True, hard=False, noisy=False, breakable=True, breaks_on="sharp", rooms=["living room", "play room"]),
    # food and dishes
    "spoon":      dict(kind="tableware", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["kitchen"]),
    "cup":        dict(kind="container", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, container="open", opaque=True, rooms=["kitchen"]),
    "bowl":       dict(kind="container", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, container="open", opaque=True, rooms=["kitchen"]),
    "bottle":     dict(kind="container", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rolls=True, rooms=["kitchen", "bedroom"]),
    "banana":     dict(kind="food", size=2, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["kitchen"]),
    "cracker":    dict(kind="food", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=True, rooms=["kitchen"]),
    "apple":      dict(kind="food", size=2, heavy=False, round=True, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["kitchen"]),
    # clothes and cloth
    "sock":       dict(kind="clothing", size=1, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["bedroom"]),
    "shoe":       dict(kind="clothing", size=2, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["bedroom", "living room"]),
    "hat":        dict(kind="clothing", size=2, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["bedroom"]),
    "towel":      dict(kind="cloth", size=3, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, cover=True, rooms=["bathroom"]),
    "blanket":    dict(kind="cloth", size=4, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, cover=True, rooms=["bedroom"]),
    # bath and care
    "soap":       dict(kind="toiletry", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["bathroom"]),
    "comb":       dict(kind="toiletry", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["bathroom", "bedroom"]),
    "toothbrush": dict(kind="toiletry", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["bathroom"]),
    # other things
    "key":        dict(kind="device", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=True, breakable=False, rooms=["living room", "kitchen"]),
    "book":       dict(kind="book", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["bedroom", "living room"]),
    "phone":      dict(kind="device", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=True, rooms=["living room", "kitchen"]),
    "pillow":     dict(kind="bedding", size=3, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["bedroom"]),
    "pot":        dict(kind="container", size=3, heavy=True, round=False, bouncy=False, hard=True, noisy=False, breakable=False, container="lid", opaque=True, rooms=["kitchen"]),
    "chair":      dict(kind="furniture", size=4, heavy=True, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["kitchen", "living room"]),
    "plate":      dict(kind="tableware", size=2, heavy=False, round=True, bouncy=False, hard=True, noisy=False, breakable=True, rooms=["kitchen"]),
    "glass":      dict(kind="container", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=True, container="open", opaque=False, holds=["tableware"], rooms=["kitchen"]),
    # containers that hold things
    "box":        dict(kind="container", size=3, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, container="lid", opaque=True, rooms=["play room", "bedroom", "living room"]),
    "basket":     dict(kind="container", size=3, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, container="open", opaque=False, rooms=["play room", "bedroom", "bathroom"]),
    "bag":        dict(kind="container", size=3, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, container="lid", opaque=True, rooms=["living room", "bedroom"]),
    "jar":        dict(kind="container", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=True, container="clear_lid", opaque=False, rooms=["kitchen"]),
    "bucket":     dict(kind="container", size=3, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, container="open", opaque=True, rooms=["bathroom", "play room"]),
    # held-out candidates (WordNet picks one per kind for test_new_object)
    "mug":        dict(kind="container", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=True, container="open", opaque=True, rooms=["kitchen"]),
    "tin":        dict(kind="container", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, container="lid", opaque=True, rooms=["kitchen"]),
    "teddy bear": dict(kind="toy", size=2, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["bedroom", "play room"]),
    "drum":       dict(kind="toy", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=True, breakable=False, rooms=["play room"]),
    "orange":     dict(kind="food", size=2, heavy=False, round=True, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["kitchen"]),
    "slipper":    dict(kind="clothing", size=2, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["bedroom", "living room"]),
    "mitten":     dict(kind="clothing", size=1, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["bedroom"]),
    "sponge":     dict(kind="toiletry", size=1, heavy=False, round=False, bouncy=True, hard=False, noisy=False, breakable=False, rooms=["bathroom", "kitchen"]),
    "brush":      dict(kind="toiletry", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["bathroom", "bedroom"]),
    "cushion":    dict(kind="bedding", size=3, heavy=False, round=False, bouncy=False, hard=False, noisy=False, breakable=False, rooms=["living room", "bedroom"]),
    "fork":       dict(kind="tableware", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["kitchen"]),
}

WORDNET_NAMES = {"toy car": "toy", "ring toy": "toy", "teddy bear": "teddy", "phone": "telephone"}

# WordNet hypernyms that confirm each kind. The check passes if any synset of
# the word reaches one of these.
KIND_HYPERNYMS = {
    "toy": ["toy.n.01", "plaything.n.01", "doll.n.01", "ball.n.01", "game_equipment.n.01", "drum.n.01", "balloon.n.01", "rattle.n.02"],
    "container": ["container.n.01", "vessel.n.03", "receptacle.n.01", "drawer.n.01"],
    "food": ["food.n.01", "food.n.02", "edible_fruit.n.01", "cracker.n.01"],
    "clothing": ["clothing.n.01", "footwear.n.02", "covering.n.02", "glove.n.02"],
    "cloth": ["fabric.n.01", "bedclothes.n.01", "towel.n.01", "covering.n.02"],
    "tableware": ["tableware.n.01", "cutlery.n.02", "crockery.n.01", "container.n.01", "dish.n.01"],
    "toiletry": ["toiletry.n.01", "toilet_articles.n.01", "brush.n.02", "cleansing_agent.n.01", "comb.n.01", "sponge.n.01", "implement.n.01"],
    "device": ["device.n.01", "telephone.n.01", "key.n.01", "instrumentality.n.03"],
    "book": ["book.n.01", "publication.n.01"],
    "bedding": ["bedclothes.n.01", "pillow.n.01", "cushion.n.03", "padding.n.01", "bedding.n.01"],
    "furniture": ["furniture.n.01", "seat.n.03"],
}

# Which kinds of things go in which containers. Physical rules and this table
# decide what is allowed; word closeness only ranks the allowed options.
CONTAINER_FITS = {
    "toy": {"box", "basket", "bag", "bucket", "tin"},
    "food": {"bowl", "jar", "tin", "box", "cup", "mug"},
    "clothing": {"basket", "bag", "box"},
    "cloth": {"basket", "bag"},
    "tableware": {"cup", "mug", "bowl", "glass", "jar", "box"},
    "toiletry": {"cup", "mug", "basket", "bag", "bucket", "box"},
    "device": {"bag", "box", "basket"},
    "book": {"bag", "basket", "box"},
    "bedding": {"basket"},
    "container": {"box", "basket", "bag", "bucket"},
}

# Words WordNet cannot check (recorded in the manifest, not silently passed).
WORDNET_GAPS = {"block": "WordNet has no toy-block sense; block.n.01 is a generic solid piece"}

HELD_OUT_CANDIDATES = ["mug", "tin", "teddy bear", "drum", "orange", "slipper", "mitten", "sponge", "brush", "cushion", "fork"]

ROOMS = ["kitchen", "bedroom", "bathroom", "play room", "living room"]

# Surfaces: high surfaces are out of reach for a baby on the floor.
SURFACES = {
    "floor": dict(high=False, hard=True),
    "mat": dict(high=False, hard=False),
    "rug": dict(high=False, hard=False),
    "table": dict(high=True, hard=True),
    "bed": dict(high=True, hard=False),
    "shelf": dict(high=True, hard=True),
}

ROOM_SURFACES = {
    "kitchen": ["floor", "mat", "table", "shelf"],
    "bedroom": ["floor", "rug", "bed", "shelf"],
    "bathroom": ["floor", "mat", "shelf"],
    "play room": ["floor", "mat", "rug", "table", "shelf"],
    "living room": ["floor", "rug", "mat", "table", "shelf"],
}

CAREGIVERS = ["Mom", "Dad", "Grandma", "Grandpa", "the big sister"]

# ---------------------------------------------------------------------------
# WordNet and word closeness
# ---------------------------------------------------------------------------


def wordnet_synsets(word: str):
    from nltk.corpus import wordnet as wn

    key = WORDNET_NAMES.get(word, word).replace(" ", "_")
    return wn.synsets(key, pos="n")


def wordnet_kind_check(word: str, kind: str) -> bool:
    from nltk.corpus import wordnet as wn

    targets = {wn.synset(name) for name in KIND_HYPERNYMS[kind]}
    for synset in wordnet_synsets(word)[:4]:
        closure = set(synset.closure(lambda s: s.hypernyms())) | {synset}
        if closure & targets:
            return True
    return False


def wup(a: str, b: str) -> float:
    sa, sb = wordnet_synsets(a), wordnet_synsets(b)
    if not sa or not sb:
        return 0.0
    return max((x.wup_similarity(y) or 0.0) for x in sa[:3] for y in sb[:3])


class Closeness:
    """Association score between words. Embeddings if available, else room tags."""

    def __init__(self, use_embeddings: bool, cache_path: Path):
        self.vectors: dict[str, list[float]] = {}
        self.mode = "room_tags"
        if not use_embeddings:
            return
        words = sorted(set(OBJECTS) | set(ROOMS) | set(SURFACES))
        if cache_path.exists():
            cached = json.loads(cache_path.read_text())
            if cached.get("model") == EMBED_MODEL and set(words) <= set(cached["vectors"]):
                self.vectors = cached["vectors"]
                self.mode = "embeddings"
                return
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            tok = AutoTokenizer.from_pretrained(EMBED_MODEL)
            model = AutoModel.from_pretrained(EMBED_MODEL)
            # A short household phrase steers single words toward the home
            # sense ("bowl" as a dish rather than a toilet bowl).
            phrases = [f"a {w} in a family home with a baby" for w in words]
            enc = tok(phrases, padding=True, return_tensors="pt")
            with torch.no_grad():
                hidden = model(**enc).last_hidden_state
            mask = enc["attention_mask"].unsqueeze(-1).float()
            vec = torch.nn.functional.normalize((hidden * mask).sum(1) / mask.sum(1), dim=1)
            self.vectors = {w: [round(float(x), 5) for x in v] for w, v in zip(words, vec)}
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps({"model": EMBED_MODEL, "vectors": self.vectors}))
            self.mode = "embeddings"
        except Exception as exc:  # offline or missing torch
            print(f"embeddings unavailable ({exc}); using room tags", file=sys.stderr)

    def score(self, a: str, b: str) -> float:
        if self.mode == "embeddings":
            va, vb = self.vectors[a], self.vectors[b]
            return sum(x * y for x, y in zip(va, vb))
        ra = set(OBJECTS.get(a, {}).get("rooms", [])) | ({a} if a in ROOMS else set())
        rb = set(OBJECTS.get(b, {}).get("rooms", [])) | ({b} if b in ROOMS else set())
        return len(ra & rb) / max(1, len(ra | rb))


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------


@dataclass
class Thing:
    name: str
    surface: str | None = None     # on which surface
    inside: str | None = None      # inside which container
    under: str | None = None       # under which cover
    closed: bool = False           # for containers
    near: bool = True              # near the baby (for low surfaces)


@dataclass
class World:
    room: str
    baby_on: str                   # "floor", "mat", "lap", "high chair"
    things: dict[str, Thing] = field(default_factory=dict)
    caregiver: str = "Mom"
    caregiver_present: bool = True

    def place(self, name: str) -> Thing:
        thing = self.things[name]
        if thing.inside:
            return self.place(thing.inside)
        return thing

    def baby_high(self) -> bool:
        return self.baby_on in ("lap", "high chair")


Fact = tuple  # ("inside", obj, container) etc.


def can_touch(world: World, name: str) -> tuple[bool, list[Fact]]:
    blockers: list[Fact] = []
    thing = world.things[name]
    if thing.inside:
        box = world.things[thing.inside]
        if box.closed:
            blockers += [("inside", name, box.name), ("closed", box.name)]
    holder = world.place(name)
    surface_high = bool(holder.surface and SURFACES[holder.surface]["high"])
    if surface_high and not world.baby_high():
        blockers += [("on", holder.name, holder.surface), ("high", holder.surface), ("baby_on", world.baby_on)]
    elif not surface_high and world.baby_high():
        blockers += [("baby_on", world.baby_on), ("on", holder.name, holder.surface), ("low", holder.surface)]
    if not holder.near:
        blockers += [("far", holder.name)]
    if blockers:
        return False, blockers
    support: list[Fact] = []
    if thing.inside:
        support += [("inside", name, thing.inside), ("open", thing.inside)]
    support += [("near", holder.name)]
    return True, support


def can_see(world: World, name: str) -> tuple[bool, list[Fact]]:
    thing = world.things[name]
    if thing.under:
        return False, [("under", name, thing.under)]
    if thing.inside:
        box = world.things[thing.inside]
        props = OBJECTS[box.name]
        if box.closed and props.get("opaque", True):
            return False, [("inside", name, box.name), ("closed", box.name)]
        if box.closed and not props.get("opaque", True):
            return True, [("inside", name, box.name), ("clear", box.name)]
        if props.get("opaque", True):
            if not box.near:
                # From across the room the baby cannot see over the sides.
                return False, [("inside", name, box.name), ("far", box.name)]
            return True, [("inside", name, box.name), ("open", box.name), ("near", box.name)]
        return True, [("inside", name, box.name), ("clear", box.name)]
    return True, [("in_view", name)]


def drop_outcome(obj: str, surface: str) -> dict[str, tuple[bool, list[Fact]]]:
    p, s = OBJECTS[obj], SURFACES[surface]
    loud = p["hard"] and s["hard"]
    loud_facts = [("hard_obj", obj), ("hard_surface", surface)] if loud else (
        [("soft_surface", surface)] if not s["hard"] else [("soft_obj", obj)])
    bounce = p["bouncy"] and s["hard"]
    bounce_facts = [("bouncy", obj), ("hard_surface", surface)] if bounce else (
        [("not_bouncy", obj)] if not p["bouncy"] else [("soft_surface", surface)])
    breaks = p["breakable"] and p.get("breaks_on") != "sharp" and s["hard"]
    if breaks:
        break_facts = [("breakable", obj), ("hard_surface", surface)]
    elif not p["breakable"] or p.get("breaks_on") == "sharp":
        break_facts = [("not_breakable", obj)]
    else:
        break_facts = [("soft_surface", surface)]
    return {"loud": (loud, loud_facts), "bounce": (bounce, bounce_facts), "break": (breaks, break_facts)}


def push_outcome(obj: str, surface: str) -> dict[str, tuple[bool, list[Fact]]]:
    p = OBJECTS[obj]
    moves = not p["heavy"]
    move_facts = [("light", obj)] if moves else [("heavy", obj)]
    rolls = moves and (p["round"] or p.get("rolls", False))
    roll_facts = ([("round", obj)] if p["round"] else [("wheels", obj)]) if rolls else (
        [("heavy", obj)] if not moves else [("not_round", obj)])
    falls = moves and SURFACES[surface]["high"]
    fall_facts = [("light", obj), ("on", obj, surface), ("high", surface)] if falls else (
        [("heavy", obj)] if not moves else [("low", surface)])
    return {"moves": (moves, move_facts), "rolls": (rolls, roll_facts), "falls": (falls, fall_facts)}


# Affect -------------------------------------------------------------------

FAMILIARITY = {
    # statement key -> starting strength of the baby's link to this effect
    "new": 0.0,
    "seen_once": 0.3,
    "knows_well": 0.75,
    "favorite": 0.9,
}
LEARN_RATE = 0.5


def novelty_gain(start: float, repeats: int) -> tuple[float, float]:
    """Return (gain on the last repeat, strength after). Formula from plan.md."""
    strength = start
    gain = 0.0
    for _ in range(repeats):
        gain = LEARN_RATE * (1 - strength)
        strength += gain
    return gain, strength


def happiness_label(gain: float) -> str:
    if gain >= 0.3:
        return "very happy and excited"
    if gain >= 0.15:
        return "happy"
    if gain >= 0.06:
        return "a little interested"
    return "bored"


def sadness_value(strength: float, links: int) -> float:
    return strength * (1 + 0.15 * max(0, links - 1))


def sadness_label(value: float) -> str:
    if value >= 0.8:
        return "very sad"
    if value >= 0.45:
        return "sad"
    if value >= 0.2:
        return "a little sad"
    return "calm"


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

# Each template list: training uses indexes where i % 4 != 3; the rest are held
# out for test_new_wording. Lists with fewer than 4 entries are all trainable.


def heldout_index(i: int, n: int) -> bool:
    return n >= 4 and i % 4 == 3


FACT_TEMPLATES: dict[str, list[str]] = {
    "inside": ["the {a} is inside the {b}", "the {a} is in the {b}", "the {b} has the {a} in it", "the {a} sits inside the {b}"],
    "closed": ["the {a} is closed", "the lid of the {a} is shut", "the {a} is shut", "nobody has opened the {a}"],
    "open": ["the {a} is open", "the {a} has no lid on it", "the top of the {a} is open", "the {a} is not closed"],
    "clear": ["you can see through the {a}", "the {a} is clear", "the sides of the {a} are see-through", "the {a} lets light through"],
    "on": ["the {a} is on the {b}", "the {a} sits on the {b}", "the {a} rests on the {b}", "the {a} lies on the {b}"],
    "high": ["the {a} is high up", "the {a} is too high for the baby", "the {a} is above the baby's reach", "the top of the {a} is far above the floor"],
    "baby_on": ["the baby is on the {a}", "the baby sits on the {a}", "the baby is down on the {a}", "the baby stays on the {a}"],
    "far": ["the {a} is far from the baby", "the {a} is out of the baby's reach", "the {a} is across the room", "the {a} is too far away"],
    "near": ["the {a} is near the baby", "the {a} is close to the baby", "the {a} is right next to the baby", "the {a} is within the baby's reach"],
    "under": ["the {a} is under the {b}", "the {b} covers the {a}", "the {a} is hidden under the {b}", "the {b} is on top of the {a}"],
    "in_view": ["nothing covers the {a}", "the {a} is out in the open", "the {a} is in plain view", "the {a} is not covered"],
    "hard_obj": ["the {a} is hard", "the {a} is made of something hard", "the {a} is not soft", "the {a} is firm"],
    "soft_obj": ["the {a} is soft", "the {a} is made of something soft", "the {a} is not hard", "the {a} is squishy"],
    "hard_surface": ["the {a} is hard", "the {a} has a hard top", "the {a} is not soft", "the {a} is firm"],
    "soft_surface": ["the {a} is soft", "the {a} is padded", "the {a} is not hard", "the {a} is cushioned"],
    "bouncy": ["the {a} is bouncy", "the {a} springs back", "the {a} can bounce", "the {a} is springy"],
    "not_bouncy": ["the {a} is not bouncy", "the {a} does not spring back", "the {a} cannot bounce", "the {a} is not springy"],
    "breakable": ["the {a} can break", "the {a} is easy to break", "the {a} is fragile", "the {a} breaks easily"],
    "not_breakable": ["the {a} does not break easily", "the {a} is tough", "the {a} is hard to break", "the {a} is strong"],
    "light": ["the {a} is light", "the {a} weighs very little", "the {a} is not heavy", "the {a} is easy to move"],
    "heavy": ["the {a} is heavy", "the {a} weighs a lot", "the {a} is too heavy to move", "the {a} is not light"],
    "round": ["the {a} is round", "the {a} has a round shape", "the {a} is shaped like a circle", "the {a} curves all the way around"],
    "wheels": ["the {a} has wheels", "the {a} sits on wheels", "the {a} has little wheels", "the {a} can roll on its wheels"],
    "not_round": ["the {a} is not round", "the {a} has flat sides", "the {a} has corners", "the {a} is not shaped like a ball"],
    "low": ["the {a} is low", "the {a} is down low", "the {a} is close to the ground", "the {a} is not high"],
    "noisy": ["the {a} makes noise when it moves", "the {a} has little bits that rattle", "shaking the {a} makes a sound", "the {a} jingles when it moves"],
    "quiet": ["the {a} makes no noise when it moves", "the {a} has nothing inside to rattle", "shaking the {a} makes no sound", "the {a} is silent when it moves"],
}


def article(word: str) -> str:
    return "an" if word[0] in "aeiou" else "a"


def cap(text: str) -> str:
    return text[0].upper() + text[1:] if text else text


def sentence(text: str) -> str:
    text = cap(text.strip())
    return text if text.endswith((".", "?", "!")) else text + "."


def join_clauses(parts: list[str]) -> str:
    parts = [p for p in parts if p]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


class Renderer:
    def __init__(self, rng: random.Random, wording: str):
        self.rng = rng
        self.wording = wording  # "train" or "heldout"
        self.used: list[str] = []

    def pick(self, key: str, options: list[str]) -> str:
        n = len(options)
        allowed = [i for i in range(n) if heldout_index(i, n) == (self.wording == "heldout")]
        if not allowed:  # short lists are always trainable
            allowed = list(range(n))
        i = self.rng.choice(allowed)
        self.used.append(f"{key}:{i}")
        return options[i]

    def fact(self, f: Fact) -> str:
        kind = f[0]
        tpl = self.pick(f"fact.{kind}", FACT_TEMPLATES[kind])
        a = f[1] if len(f) > 1 else ""
        b = f[2] if len(f) > 2 else ""
        if kind == "baby_on" and a in ("lap", "high chair"):
            return {"lap": "the baby is up on a lap", "high chair": "the baby is up in the high chair"}[a]
        return tpl.format(a=a, b=b)

    def facts(self, fs: list[Fact]) -> str:
        return join_clauses([self.fact(f) for f in dedupe(fs)])


def dedupe(items: list) -> list:
    seen, out = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def describe_place(r: Renderer, world: World, name: str) -> str:
    t = world.things[name]
    parts = []
    if t.under:
        parts.append(r.fact(("under", name, t.under)))
    elif t.inside:
        box = world.things[t.inside]
        parts.append(r.fact(("inside", name, box.name)))
        parts.append(r.fact(("closed", box.name)) if box.closed else r.fact(("open", box.name)))
        parts.append(describe_location(r, world, box.name))
    else:
        parts.append(describe_location(r, world, name))
        if OBJECTS.get(name, {}).get("container") in ("lid", "clear_lid"):
            parts.append(r.fact(("closed", name)) if t.closed else r.fact(("open", name)))
    return join_clauses(parts)


def describe_location(r: Renderer, world: World, name: str) -> str:
    t = world.things[name]
    loc = r.fact(("on", name, t.surface))
    return loc + (" " + r.pick("near_tail", ["close to the baby", "near the baby", "right by the baby", "next to the baby"]) if t.near
                  else " " + r.pick("far_tail", ["far from the baby", "across the room", "out of the baby's reach", "a long way from the baby"]))


BABY_POSITIONS = {
    "floor": ["The baby sits on the floor", "The baby is down on the floor", "The baby plays on the floor", "The baby lies on the floor"],
    "mat": ["The baby sits on the play mat", "The baby is lying on the mat", "The baby plays on the mat", "The baby rests on the mat"],
    "lap": ["The baby sits in {c}'s lap", "{C} holds the baby on {c_pos} lap", "The baby is on {c}'s lap", "{C} has the baby on {c_pos} knee"],
    "high chair": ["The baby sits in the high chair", "The baby is strapped into the high chair", "The baby waits in the high chair", "The baby is up in the high chair"],
}

ROOM_OPENERS = ["In the {r}", "This morning in the {r}", "After a nap in the {r}", "Later in the {r}"]


def caregiver_forms(name: str) -> dict[str, str]:
    pos = {"Mom": "her", "Grandma": "her", "the big sister": "her", "Dad": "his", "Grandpa": "his"}[name]
    return {"c": name, "C": cap(name), "c_pos": pos}


def render_opening(r: Renderer, world: World) -> str:
    opener = r.pick("room", ROOM_OPENERS).format(r=world.room)
    pos = r.pick(f"baby.{world.baby_on}", BABY_POSITIONS[world.baby_on]).format(**caregiver_forms(world.caregiver))
    pos = pos[0].lower() + pos[1:] if not pos.startswith(("Mom", "Dad", "Grandma", "Grandpa")) else pos
    return sentence(f"{opener}, {pos}")


PROMPT_FRAMES = [
    "{scene}\nQuestion: {q}\nAnswer:",
    "Story: {scene}\n{q}\nAnswer:",
    "{scene}\nNow tell me: {q}\nAnswer:",
    "Here is what happens. {scene}\nQuestion: {q}\nAnswer:",
    "{scene}\nThink about it. {q}\nAnswer:",
    "Look at this. {scene}\n{q}\nAnswer:",
    "{scene}\nPlease answer: {q}\nAnswer:",
    "Picture this. {scene}\nQuestion: {q}\nAnswer:",
]

# ---------------------------------------------------------------------------
# Episode families
# ---------------------------------------------------------------------------


@dataclass
class Episode:
    family: str
    scene_parts: list[str]
    question: str
    answer: str
    reason_facts: list[Fact] | None
    reason_text: str | None
    main_object: str
    objects: list[str]
    group: str
    meta: dict[str, Any]


class Generator:
    def __init__(self, rng: random.Random, closeness: Closeness, train_objects: list[str], new_objects: list[str]):
        self.rng = rng
        self.close = closeness
        self.train_objects = train_objects
        self.new_objects = new_objects

    # helpers --------------------------------------------------------------

    def room_for(self, obj: str) -> str:
        scores = sorted(ROOMS, key=lambda room: -self.close.score(obj, room))
        return self.rng.choice(scores[:2])

    def containers_for(self, obj: str, pool: list[str], need: str | None = None) -> list[str]:
        size = OBJECTS[obj]["size"]
        options = []
        for c in pool:
            p = OBJECTS[c]
            if c == obj or not p.get("container"):
                continue
            if p["size"] <= size:
                continue
            if c not in CONTAINER_FITS.get(OBJECTS[obj]["kind"], set()):
                continue
            if need == "closable" and p["container"] not in ("lid", "clear_lid"):
                continue
            if need == "opaque_closable" and p["container"] != "lid":
                continue
            options.append(c)
        options.sort(key=lambda c: -self.close.score(obj, c))
        return options[:3]

    def distractor(self, pool: list[str], exclude: set[str], room: str) -> str | None:
        options = [o for o in pool if o not in exclude and not OBJECTS[o].get("container") and o != "chair"]
        if not options:
            return None
        options.sort(key=lambda o: -self.close.score(o, room))
        return self.rng.choice(options[:6])

    def surface_in(self, room: str, high: bool | None = None) -> str:
        options = [sf for sf in ROOM_SURFACES[room] if high is None or SURFACES[sf]["high"] == high]
        return self.rng.choice(options)

    def add_decoy(self, world: World, pool: list[str], exclude: set[str]) -> str | None:
        """A second container whose state (open/closed) does not matter for the question."""
        options = [c for c in pool if OBJECTS[c].get("container") in ("lid", "clear_lid", "open")
                   and c not in exclude and OBJECTS[c]["size"] >= 3]
        if not options:
            return None
        c = self.rng.choice(options)
        world.things[c] = Thing(c, surface=self.surface_in(world.room), near=self.rng.random() < 0.5,
                                closed=OBJECTS[c]["container"] != "open" and self.rng.random() < 0.5)
        return c

    def baby_and_world(self, room: str, high: bool | None = None) -> World:
        if high is None:
            high = self.rng.random() < 0.3
        if high:
            baby_on = self.rng.choice(["lap", "high chair"])
        else:
            baby_on = self.rng.choice(["floor", "mat"])
        return World(room=room, baby_on=baby_on, caregiver=self.rng.choice(CAREGIVERS))

    # touch / reach ----------------------------------------------------------

    def touch_pair(self, obj: str, pool: list[str]) -> list[Episode]:
        """A minimal pair: two worlds that differ in one fact."""
        room = self.room_for(obj)
        boxes = self.containers_for(obj, pool)
        flags = {
            "inside": bool(boxes) and self.rng.random() < 0.7,
            "closed": self.rng.random() < 0.5,
            "high_surface": self.rng.random() < 0.35,
            "far": self.rng.random() < 0.35,
            "baby_high": self.rng.random() < 0.25,
        }
        box = self.rng.choice(boxes) if flags["inside"] and boxes else None
        if box and OBJECTS[box]["container"] == "open":
            closable = self.containers_for(obj, pool, need="closable")
            if flags["closed"] and closable:
                box = self.rng.choice(closable)
            else:
                flags["closed"] = False
        flippable = [k for k in ("closed", "high_surface", "far", "baby_high") if (k != "closed" or box)]
        flip = self.rng.choice(flippable)
        twin = dict(flags, **{flip: not flags[flip]})
        group = f"touch|{obj}|{box}|{self.rng.random():.6f}"
        distract = self.distractor(pool, {obj, box or ""}, room)
        out = []
        for variant, fl in (("a", flags), ("b", twin)):
            world = self.baby_and_world(room, high=fl["baby_high"])
            surface = self.surface_in(room, fl["high_surface"])
            holder = box or obj
            world.things[holder] = Thing(holder, surface=surface, near=not fl["far"], closed=fl["closed"] if box else False)
            if box:
                world.things[obj] = Thing(obj, inside=box)
            if distract:
                d_surface = self.surface_in(room)
                world.things[distract] = Thing(distract, surface=d_surface, near=self.rng.random() < 0.5)
            decoy = self.add_decoy(world, pool, {obj, box or "", distract or ""})
            ok, facts = can_touch(world, obj)
            out.append(self._touch_episode(world, obj, ok, facts, group, flip, distract))
        return out

    def _touch_episode(self, world: World, obj: str, ok: bool, facts: list[Fact], group: str, flip: str, distract: str | None) -> Episode:
        scene = [("opening", None), ("place", obj)]
        others = [n for n in world.things if n not in (obj, world.things[obj].inside)]
        self.rng.shuffle(others)
        for n in others:
            scene.insert(self.rng.randint(1, len(scene)), ("place", n))
        scene.append(("action", [
            "the baby reaches for the {o}", "the baby stretches a hand toward the {o}",
            "the baby wants the {o} and reaches out", "the baby tries to grab the {o}",
            "the baby leans toward the {o}"]))
        q = ("Can the baby touch the {o}?", ["Can the baby touch the {o}?", "Will the baby's hand get to the {o}?",
                                              "Is the baby able to touch the {o}?", "Does the baby reach the {o}?"])
        return Episode("touch_reach", scene, q, "yes" if ok else "no", facts, None, obj,
                       [n for n in world.things], group, {"world": world, "flip": flip})

    # visibility ------------------------------------------------------------

    def see_pair(self, obj: str, pool: list[str]) -> list[Episode]:
        room = self.room_for(obj)
        boxes = self.containers_for(obj, pool)
        covers = [c for c in pool if OBJECTS[c].get("cover")]
        mode = self.rng.choice(["box", "box", "cover", "none"]) if boxes else self.rng.choice(["cover", "none"])
        group = f"see|{obj}|{self.rng.random():.6f}"
        out = []
        if mode == "box":
            box = self.rng.choice(boxes)
            variants = [("closed", True), ("open", False)]
        elif mode == "cover":
            box = self.rng.choice(covers)
            variants = [("covered", True), ("uncovered", False)]
        else:
            box = None
            variants = [("plain", False)]
        for _, flag in variants:
            world = self.baby_and_world(room)
            world.things[box or obj] = Thing(box or obj, surface=self.surface_in(room), near=self.rng.random() < 0.6)
            if mode == "box":
                world.things[box].closed = flag and OBJECTS[box]["container"] in ("lid", "clear_lid")
                world.things[obj] = Thing(obj, inside=box)
            elif mode == "cover":
                world.things[obj] = Thing(obj, surface=world.things[box].surface, near=world.things[box].near, under=box if flag else None)
            decoy = self.add_decoy(world, pool, {obj, box or ""})
            ok, facts = can_see(world, obj)
            scene = [("opening", None), ("place", obj)]
            if decoy:
                scene.insert(self.rng.randint(1, 2), ("place", decoy))
            scene += [("action", [
                "the baby looks around for the {o}", "the baby turns to look for the {o}",
                "the baby searches with its eyes for the {o}", "the baby looks toward where the {o} is"])]
            q = ("Can the baby see the {o}?", ["Can the baby see the {o}?", "Is the {o} visible to the baby?",
                                                "Does the baby see the {o}?", "Will the baby spot the {o}?"])
            out.append(Episode("see", scene, q, "yes" if ok else "no", facts, None, obj, list(world.things), group, {"world": world}))
        return out

    # drop -----------------------------------------------------------------

    def matching(self, pool: list[str], obj: str, surfaces: list[str], fn, prop: str, want: bool) -> tuple[str, str] | None:
        """Find (object, surface) with the wanted outcome; prefer the given object."""
        candidates = [obj] + [o for o in pool if o != obj and not OBJECTS[o].get("cover") and o != "chair"]
        if obj not in self.train_objects:  # new-object test keeps its object
            candidates = [obj]
        for o in candidates:
            options = [sf for sf in surfaces if fn(o, sf)[prop][0] == want]
            if options:
                return o, self.rng.choice(options)
        return None

    def drop(self, obj: str, pool: list[str]) -> list[Episode]:
        out = []
        prop = self.rng.choice(["loud", "bounce", "break"])
        for want in (True, False):
            room = self.room_for(obj)
            low = [sf for sf in ROOM_SURFACES[room] if not SURFACES[sf]["high"]]
            found = self.matching(pool, obj, low, drop_outcome, prop, want)
            if not found:
                continue
            o, surface = found
            group = f"drop|{o}|{prop}|{self.rng.random():.6f}"
            world = self.baby_and_world(room, high=True)
            world.things[o] = Thing(o, surface=surface)
            ok, facts = drop_outcome(o, surface)[prop]
            obj_name = o
            qs = {
                "loud": ["Does the {o} make a loud sound?", "Is there a loud bang when the {o} lands?",
                         "Does the {o} land with a loud noise?", "Will the {o} make a big noise?"],
                "bounce": ["Does the {o} bounce?", "Will the {o} bounce back up?",
                           "Does the {o} spring up again?", "Does the {o} bounce when it lands?"],
                "break": ["Does the {o} break?", "Will the {o} break?", "Is the {o} broken after it lands?", "Does the {o} crack?"],
            }[prop]
            scene = [("opening", None), ("text", ["the baby holds the {o}", "the baby has the {o} in one hand",
                                                  "the baby is holding the {o}", "the baby grips the {o}"]),
                     ("action", ["the baby lets go of the {o}, and it falls onto the " + surface,
                                                 "the {o} slips out of the baby's hand and drops onto the " + surface,
                                                 "the baby drops the {o} on purpose, and it lands on the " + surface,
                                                 "the baby opens its hand, and the {o} falls to the " + surface])]
            out.append(Episode(f"drop_{prop}", scene, (qs[0], qs), "yes" if ok else "no", facts, None, obj_name, [obj_name], group,
                               {"world": world, "surface": surface}))
        return out

    # push -----------------------------------------------------------------

    def push(self, obj: str, pool: list[str]) -> list[Episode]:
        out = []
        prop = self.rng.choice(["moves", "rolls", "falls"])
        for want in (True, False):
            room = self.room_for(obj)
            found = self.matching(pool, obj, ROOM_SURFACES[room], push_outcome, prop, want)
            if not found:
                continue
            o, surface = found
            group = f"push|{o}|{prop}|{self.rng.random():.6f}"
            world = self.baby_and_world(room, high=SURFACES[surface]["high"])
            world.things[o] = Thing(o, surface=surface, near=True)
            ok, facts = push_outcome(o, surface)[prop]
            obj = o
            qs = {
                "moves": ["Does the {o} move?", "Will the {o} slide away?", "Does the {o} shift when pushed?", "Does the push move the {o}?"],
                "rolls": ["Does the {o} roll?", "Will the {o} roll away?", "Does the {o} start rolling?", "Does the {o} roll across the {s}?"],
                "falls": ["Does the {o} fall off the {s}?", "Will the {o} drop off the {s}?", "Does the {o} go over the edge?", "Does the {o} end up falling?"],
            }[prop]
            qs = [q.replace("{s}", surface) for q in qs]
            scene = [("opening", None), ("text", [f"the {obj} is on the {surface} in front of the baby",
                                                  f"the {obj} sits on the {surface} right by the baby",
                                                  f"the {obj} lies on the {surface} next to the baby",
                                                  f"the {obj} is on the {surface}, close to the baby"]),
                     ("action", ["the baby pushes the {o} hard", "the baby gives the {o} a shove",
                                                 "the baby swats the {o} with one hand", "the baby pushes the {o} away"])]
            out.append(Episode(f"push_{prop}", scene, (qs[0], qs), "yes" if ok else "no", facts, None, obj, [obj], group,
                               {"world": world, "surface": surface}))
        return out

    # shake ----------------------------------------------------------------

    def shake(self, obj: str, pool: list[str]) -> list[Episode]:
        if obj in self.train_objects:
            want = self.rng.random() < 0.5
            options = [o for o in pool if OBJECTS[o]["noisy"] == want and OBJECTS[o]["size"] <= 2]
            obj = self.rng.choice(options) if options else obj
        room = self.room_for(obj)
        world = self.baby_and_world(room)
        noisy = OBJECTS[obj]["noisy"]
        facts = [("noisy", obj)] if noisy else [("quiet", obj)]
        scene = [("opening", None), ("text", ["the baby holds the {o}", "the baby has the {o} in one hand",
                                              "the baby is holding the {o}", "the baby grips the {o}"]),
                 ("action", ["the baby shakes the {o}", "the baby waves the {o} up and down",
                                             "the baby shakes the {o} hard", "the baby swings the {o} back and forth"])]
        qs = ["Does the {o} make a sound?", "Is there a noise when the baby shakes the {o}?",
              "Does the baby hear a sound from the {o}?", "Will shaking the {o} make a noise?"]
        return [Episode("shake_sound", scene, (qs[0], qs), "yes" if noisy else "no", facts, None, obj, [obj],
                        f"shake|{obj}|{self.rng.random():.6f}", {"world": world})]

    # where is it (multi-step tracking) --------------------------------------

    def track(self, obj: str, pool: list[str]) -> list[Episode]:
        room = self.room_for(obj)
        world = self.baby_and_world(room)
        boxes = self.containers_for(obj, pool)
        if not boxes:
            return []
        locations = [("on", sf) for sf in ROOM_SURFACES[room]] + [("in", b) for b in boxes]
        steps = self.rng.randint(2, 4)
        current = ("on", self.surface_in(room))
        history = [current]
        c = world.caregiver
        for _ in range(steps - 1):
            nxt = self.rng.choice([l for l in locations if l != current])
            history.append(nxt)
            current = nxt
        texts = [f"the {obj} is {'on' if history[0][0] == 'on' else 'in'} the {history[0][1]}"]
        for kind, where in history[1:]:
            verb = self.rng.choice(["puts", "moves", "places", "sets"])
            prep = ("on" if verb in ("puts", "sets", "places") else "onto") if kind == "on" else "into"
            texts.append(f"{c} {verb} the {obj} {prep} the {where}")
        distract = self.distractor(pool, {obj}, room)
        if distract:
            texts.insert(self.rng.randint(1, len(texts)), f"{c} {self.rng.choice(['puts', 'sets'])} the {distract} on the {self.surface_in(room)}")
        answer = f"{'on' if current[0] == 'on' else 'in'} the {current[1]}"
        reason = f"{c} put it {'on' if current[0] == 'on' else 'in'} the {current[1]} last"
        scene = [("opening", None)] + [("text", t) for t in texts]
        qs = ["Where is the {o} now?", "Where is the {o} at the end?", "Where can the baby find the {o} now?", "Where did the {o} end up?"]
        return [Episode("track_location", scene, (qs[0], qs), answer, None, reason, obj, [obj] + boxes[:1],
                        f"track|{obj}|{self.rng.random():.6f}", {"steps": steps, "world": world})]

    # feelings: novelty and saturation --------------------------------------

    def novelty(self, obj: str, pool: list[str]) -> list[Episode]:
        """Same effect repeated: gain shrinks as the link gets strong."""
        room = self.room_for(obj)
        p = OBJECTS[obj]
        if p["noisy"]:
            effect, act = "sound", "shakes the {o}, and it makes a sound"
        elif p["round"] or p.get("rolls"):
            effect, act = "roll", "pushes the {o}, and it rolls away"
        elif p["bouncy"]:
            effect, act = "bounce", "drops the {o}, and it bounces"
        else:
            effect, act = "feel", "squeezes the {o} and feels it in both hands"
        group = f"novelty|{obj}|{self.rng.random():.6f}"
        out = []
        fam_options = list(FAMILIARITY)
        for fam in self.rng.sample(fam_options, 2):
            repeats = self.rng.choice([1, 1, 2, 3, 5])
            gain, strength = novelty_gain(FAMILIARITY[fam], repeats)
            world = self.baby_and_world(room)
            fam_text = {
                "new": f"the {obj} is new, and the baby has never played with it",
                "seen_once": f"the baby has played with the {obj} once before",
                "knows_well": f"the baby has played with the {obj} many times",
                "favorite": f"the {obj} is the baby's favorite, and the baby plays with it every day",
            }[fam]
            count = {2: "twice", 3: "three times", 5: "five times in a row"}.get(repeats)
            scene = [("opening", None), ("text", fam_text), ("action", f"the baby {act}")]
            if count:
                scene.append(("text", [f"the baby does this {count}", f"the baby tries it {count}",
                                       f"the baby repeats this {count}", f"the same thing happens {count}"]))
            label = happiness_label(gain)
            if gain >= 0.15:
                reason = f"the baby is still learning what the {obj} does, so each try teaches something new"
            elif gain >= 0.06:
                reason = f"the baby mostly knows what the {obj} does, so there is only a little left to learn"
            else:
                reason = f"the baby already knows what the {obj} does, so doing it again teaches nothing new"
            qs = ["How does the baby feel after the last try?", "How does the baby feel now?",
                  "What does the baby feel at the end?", "How does the last try make the baby feel?"]
            out.append(Episode("feel_novelty", scene, (qs[0], qs), label, None, reason, obj, [obj], group,
                               {"familiarity": fam, "repeats": repeats, "start_strength": FAMILIARITY[fam],
                                "happiness_gain": round(gain, 4), "strength_after": round(strength, 4), "effect": effect}))
        return out

    # feelings: loss ---------------------------------------------------------

    def loss(self, obj: str, pool: list[str]) -> list[Episode]:
        room = self.room_for(obj)
        group = f"loss|{obj}|{self.rng.random():.6f}"
        out = []
        boxes = self.containers_for(obj, pool, need="opaque_closable")
        for fam in self.rng.sample(list(FAMILIARITY), 2):
            links = {"new": 1, "seen_once": 1, "knows_well": 3, "favorite": 5}[fam]
            value = sadness_value(FAMILIARITY[fam] if fam != "new" else 0.1, links)
            label = sadness_label(value)
            world = self.baby_and_world(room)
            c = world.caregiver
            fam_text = {
                "new": f"the baby got the {obj} today and has not played with it yet",
                "seen_once": f"the baby has played with the {obj} once before",
                "knows_well": f"the baby plays with the {obj} often and knows it well",
                "favorite": f"the {obj} is the baby's favorite; the baby holds it at meals, in the bath, and at bedtime",
            }[fam]
            # how lasting the loss is: 1.0 gone for good, 0.6 gone for now, 0.2 back soon
            lasting = self.rng.choice([1.0, 0.6, 0.2])
            if lasting == 1.0:
                event = (f"the {obj} rolls under the couch, where nobody can reach it" if (OBJECTS[obj]["round"] or OBJECTS[obj].get("rolls"))
                         else f"{c} takes the {obj} away and leaves the house with it")
            elif lasting == 0.6:
                b = self.rng.choice(boxes) if boxes else None
                event = (f"{c} puts the {obj} in the {b}, closes it, and carries it to another room" if b
                         else f"{c} puts the {obj} up on a high shelf in another room")
            else:
                event = self.rng.choice([f"{c} hides the {obj} behind {caregiver_forms(c)['c_pos']} back and gives it back a moment later",
                                         f"the {obj} drops out of sight for a moment, and {c} hands it right back"])
            value *= lasting
            label = sadness_label(value)
            scene = [("opening", None), ("text", fam_text), ("action", event)]
            strong = {"new": "the baby has almost no link to the {o} yet",
                      "seen_once": "the baby has only a weak link to the {o}",
                      "knows_well": "the baby has a strong link to the {o}",
                      "favorite": "the {o} is linked to many parts of the baby's day"}[fam].replace("{o}", obj)
            how = {1.0: "and the {o} is gone for good", 0.6: "and the {o} is gone for now",
                   0.2: "and the {o} comes back right away"}[lasting].replace("{o}", obj)
            reason = f"{strong}, {how}"
            qs = ["How does the baby feel?", "How does the baby feel when the {o} is gone?",
                  "What does the baby feel now?", "How does losing the {o} make the baby feel?"]
            out.append(Episode("feel_loss", scene, (qs[0], qs), label, None, reason, obj, [obj], group,
                               {"familiarity": fam, "links": links, "lasting": lasting, "sadness": round(value, 4)}))
        return out

    # feelings: blocked reach (links affect to physics) -----------------------

    def blocked(self, obj: str, pool: list[str]) -> list[Episode]:
        eps = self.touch_pair(obj, pool)
        out = []
        for ep in eps:
            ok = ep.answer == "yes"
            ep.family = "feel_reach"
            ep.answer = "happy" if ok else "upset"
            ep.question = ("How does the baby feel?", ["How does the baby feel?", "How does the baby feel after reaching?",
                                                      "What does the baby feel then?", "How does the baby feel about the {o}?"])
            ep.meta["touch"] = ok
            out.append(ep)
        return out


FAMILIES: dict[str, Callable] = {
    "touch_reach": Generator.touch_pair,
    "see": Generator.see_pair,
    "drop": Generator.drop,
    "push": Generator.push,
    "shake_sound": Generator.shake,
    "track_location": Generator.track,
    "feel_novelty": Generator.novelty,
    "feel_loss": Generator.loss,
    "feel_reach": Generator.blocked,
}


# ---------------------------------------------------------------------------
# Episode -> row
# ---------------------------------------------------------------------------


def render_episode(ep: Episode, rng: random.Random, wording: str) -> dict[str, Any]:
    r = Renderer(rng, wording)
    world: World | None = ep.meta.get("world")
    parts: list[str] = []
    for kind, value in ep.scene_parts:
        if kind == "opening" and world:
            parts.append(render_opening(r, world))
        elif kind == "place" and world:
            parts.append(sentence(describe_place(r, world, value)))
        elif kind in ("action", "text"):
            if isinstance(value, list):
                value = r.pick(f"{kind}.{ep.family}.{len(value)}", value)
            parts.append(sentence(value.replace("{o}", ep.main_object)))
    scene = " ".join(parts)
    q = r.pick(f"q.{ep.family}", ep.question[1]).replace("{o}", ep.main_object)
    frame = r.pick("frame", PROMPT_FRAMES)
    prompt = frame.format(scene=scene, q=q)
    if ep.reason_facts is not None:
        reason = r.facts(ep.reason_facts)
        if ep.family == "feel_reach":
            reason = (f"the baby gets the {ep.main_object} because " if ep.meta.get("touch") else
                      f"the baby wants the {ep.main_object} but cannot get it, because ") + reason
    else:
        reason = ep.reason_text or ""
    target = f"answer: {ep.answer}.\nreason: {reason}."
    meta = {k: v for k, v in ep.meta.items() if k != "world"}
    if world:
        meta["world"] = {
            "room": world.room, "baby_on": world.baby_on, "caregiver": world.caregiver,
            "things": {n: {k: v for k, v in vars(t).items() if v not in (None, False) and k != "name"} for n, t in world.things.items()},
        }
    if ep.reason_facts is not None:
        meta["reason_facts"] = [list(f) for f in dedupe(ep.reason_facts)]
    meta["templates"] = r.used
    return {"input": prompt, "target": target, "task_type": ep.family, "main_object": ep.main_object,
            "group": ep.group, "metadata": meta}


# ---------------------------------------------------------------------------
# Quality checks
# ---------------------------------------------------------------------------

WORD_RE = re.compile(r"[a-z']+")


def tokens(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def answer_of(row: dict[str, Any]) -> str:
    return row["target"].split("\n")[0].strip()


def question_line(row: dict[str, Any]) -> str:
    lines = [l for l in row["input"].split("\n") if l.strip()]
    return lines[-2] if len(lines) >= 2 else lines[-1]


class NaiveBayes:
    """Multinomial naive Bayes on word counts. A crude 'does one word give it away' check."""

    def __init__(self):
        self.class_counts: Counter = Counter()
        self.word_counts: dict[str, Counter] = defaultdict(Counter)
        self.vocab: set[str] = set()

    def fit(self, texts: list[str], labels: list[str]) -> "NaiveBayes":
        for text, label in zip(texts, labels):
            self.class_counts[label] += 1
            for w in set(tokens(text)):
                self.word_counts[label][w] += 1
                self.vocab.add(w)
        return self

    def predict(self, text: str) -> str:
        words = set(tokens(text)) & self.vocab
        total = sum(self.class_counts.values())
        best, best_score = None, -math.inf
        for label, n in self.class_counts.items():
            score = math.log(n / total)
            wc = self.word_counts[label]
            for w in words:
                score += math.log((wc[w] + 1) / (n + 2))
            if score > best_score:
                best, best_score = label, score
        return best


class BestSingleWord:
    """Pick the one word whose presence best predicts the answer (train), then apply it."""

    def fit(self, texts: list[str], labels: list[str]) -> "BestSingleWord":
        sets = [set(tokens(t)) for t in texts]
        self.default = Counter(labels).most_common(1)[0][0]
        vocab = Counter(w for ws in sets for w in ws)
        best = (-1.0, None, None, None)
        for w, n in vocab.items():
            if n < 5 or n == len(texts):
                continue
            with_w = Counter(l for ws, l in zip(sets, labels) if w in ws)
            without = Counter(l for ws, l in zip(sets, labels) if w not in ws)
            a_with = with_w.most_common(1)[0][0]
            a_without = without.most_common(1)[0][0] if without else self.default
            acc = (with_w[a_with] + without[a_without]) / len(texts)
            if acc > best[0]:
                best = (acc, w, a_with, a_without)
        _, self.word, self.a_with, self.a_without = best
        return self

    def predict(self, text: str) -> str:
        if self.word is None:
            return self.default
        return self.a_with if self.word in set(tokens(text)) else self.a_without


def lint(text: str) -> list[str]:
    issues = []
    if "  " in text:
        issues.append("double space")
    if re.search(r"\b(\w+) \1\b", text, re.I) and not re.search(r"\b(that that|had had)\b", text, re.I):
        issues.append("repeated word")
    if re.search(r"[.?!] [a-z]", text):
        issues.append("lowercase sentence start")
    if re.search(r"\b(a) [aeiou]", text):
        issues.append("a before vowel")
    if " ," in text or ",," in text or ".." in text:
        issues.append("punctuation")
    return issues


def quality_report(splits: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    train = splits.get("train", [])
    report: dict[str, Any] = {"counts": {k: len(v) for k, v in splits.items()}}
    task_of = lambda r: r.get("task_type") or r.get("metadata", {}).get("task_type") or "all"
    tasks = sorted({task_of(r) for r in train})
    report["answer_balance"] = {}
    for t in tasks:
        answers = Counter(answer_of(r) for r in train if task_of(r) == t)
        total = sum(answers.values())
        report["answer_balance"][t] = {"rows": total, "distinct_answers": len(answers),
                                       "top_share": round(answers.most_common(1)[0][1] / total, 3)}
    overall = Counter(answer_of(r) for r in train)
    report["overall_top_answer_share"] = round(overall.most_common(1)[0][1] / max(1, len(train)), 3)
    report["distinct_targets_train"] = len({r["target"] for r in train})
    report["distinct_reasons_train"] = len({r["target"].split("\n")[1] for r in train if "\n" in r["target"]})

    # Baselines, per task, trained on train and scored on each test split.
    report["baselines"] = {}
    for split, rows in splits.items():
        if split in ("train", "dev") or not rows:
            continue
        res = {}
        for t in tasks:
            tr = [r for r in train if task_of(r) == t]
            te = [r for r in rows if task_of(r) == t]
            if not te or not tr:
                continue
            labels = [answer_of(r) for r in tr]
            majority = Counter(labels).most_common(1)[0][0]
            full = NaiveBayes().fit([r["input"] for r in tr], labels)
            qonly = NaiveBayes().fit([question_line(r) for r in tr], labels)
            single = BestSingleWord().fit([r["input"] for r in tr], labels)
            res[t] = {
                "rows": len(te),
                "majority": round(sum(answer_of(r) == majority for r in te) / len(te), 3),
                "single_word": round(sum(single.predict(r["input"]) == answer_of(r) for r in te) / len(te), 3),
                "single_word_cue": single.word,
                "word_bag": round(sum(full.predict(r["input"]) == answer_of(r) for r in te) / len(te), 3),
                "question_only": round(sum(qonly.predict(question_line(r)) == answer_of(r) for r in te) / len(te), 3),
            }
        report["baselines"][split] = res

    # Leakage and lint.
    train_inputs = {r["input"] for r in train}
    train_sents = {s for r in train for s in re.split(r"(?<=[.?!])\s+", r["input"])}
    report["leakage"] = {}
    for split, rows in splits.items():
        if split == "train" or not rows:
            continue
        sents = [s for r in rows for s in re.split(r"(?<=[.?!])\s+", r["input"])]
        report["leakage"][split] = {
            "exact_input_overlap": sum(r["input"] in train_inputs for r in rows),
            "sentence_overlap_share": round(sum(s in train_sents for s in sents) / max(1, len(sents)), 3),
        }
    lint_counts = Counter()
    examples = defaultdict(list)
    for rows in splits.values():
        for r in rows:
            for issue in lint(r["input"] + " " + r["target"]):
                lint_counts[issue] += 1
                if len(examples[issue]) < 3:
                    examples[issue].append(r["input"][:200])
    report["lint"] = {"counts": dict(lint_counts), "examples": dict(examples)}
    report["vocabulary_train"] = len({w for r in train for w in tokens(r["input"] + " " + r["target"])})
    return report


def print_report(report: dict[str, Any]) -> None:
    print(json.dumps(report["counts"]))
    print(f"vocabulary (train): {report['vocabulary_train']}; distinct targets: {report['distinct_targets_train']}; "
          f"overall top answer share: {report['overall_top_answer_share']}")
    print("answer balance (train):")
    for t, v in report["answer_balance"].items():
        print(f"  {t:22s} rows={v['rows']:6d} answers={v['distinct_answers']:4d} top_share={v['top_share']}")
    for split, res in report["baselines"].items():
        print(f"baselines on {split} (majority / best single word [cue] / word bag / question only):")
        for t, v in res.items():
            print(f"  {t:22s} n={v['rows']:5d}  {v['majority']:.3f} / {v['single_word']:.3f} [{v['single_word_cue']}] / {v['word_bag']:.3f} / {v['question_only']:.3f}")
    print("leakage:", json.dumps(report["leakage"]))
    print("lint:", json.dumps(report["lint"]["counts"]))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def stable_hash(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:12], 16)


def balance(rows: list[dict[str, Any]], rng: random.Random, max_share: float) -> list[dict[str, Any]]:
    """Downsample so no answer exceeds max_share within its task (keeps pair groups whole when possible)."""
    out = []
    by_task = defaultdict(list)
    for r in rows:
        by_task[r["task_type"]].append(r)
    for task, items in by_task.items():
        counts = Counter(answer_of(r) for r in items)
        if len(counts) < 2:
            out += items
            continue
        if len(counts) == 2:
            cap_n = min(counts.values())
        else:
            cap_n = max(1, int(max_share * len(items)))
            cap_n = max(cap_n, min(counts.values()))
        kept = Counter()
        rng.shuffle(items)
        for r in items:
            a = answer_of(r)
            if kept[a] < cap_n:
                kept[a] += 1
                out.append(r)
    return out


def choose_split_objects(rng: random.Random) -> tuple[list[str], list[str], dict[str, Any]]:
    """Hold out one candidate per kind, chosen by WordNet similarity to training objects."""
    info: dict[str, Any] = {"kind_check": {}, "held_out": {}}
    for word, props in OBJECTS.items():
        if word in WORDNET_GAPS:
            info["kind_check"][word] = "gap: " + WORDNET_GAPS[word]
            continue
        try:
            info["kind_check"][word] = wordnet_kind_check(word, props["kind"])
        except Exception as exc:
            info["kind_check"][word] = f"error: {exc}"
    base = [w for w in OBJECTS if w not in HELD_OUT_CANDIDATES]
    new = []
    for cand in HELD_OUT_CANDIDATES:
        same_kind = [w for w in base if OBJECTS[w]["kind"] == OBJECTS[cand]["kind"]]
        if not same_kind:
            continue
        sims = sorted(((wup(cand, w), w) for w in same_kind), reverse=True)
        info["held_out"][cand] = {"nearest_train": sims[0][1], "wup": round(sims[0][0], 3)}
        new.append(cand)
    return base, new, info


def generate(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    out_dir: Path = args.output_dir
    closeness = Closeness(not args.no_embeddings, out_dir / "word_vectors.json")
    train_objects, new_objects, lex_info = choose_split_objects(rng)
    gen = Generator(rng, closeness, train_objects, new_objects)

    pairings = {o: gen.containers_for(o, train_objects) for o in train_objects if not OBJECTS[o].get("container")}
    lex_info["container_pairings"] = pairings
    lex_info["closeness_mode"] = closeness.mode

    rows: list[dict[str, Any]] = []
    for family, fn in FAMILIES.items():
        for i in range(args.episodes_per_family):
            obj = rng.choice([o for o in train_objects if o not in ("chair", "drawer") and not OBJECTS[o].get("cover")])
            for ep in fn(gen, obj, train_objects):
                g = stable_hash(ep.group) % 100
                split = "train" if g < 80 else ("dev" if g < 88 else "test_iid")
                wording = "train"
                if split == "test_iid" and stable_hash(ep.group + "w") % 2 == 0:
                    split, wording = "test_new_wording", "heldout"
                row = render_episode(ep, rng, wording)
                row["split"] = split
                rows.append(row)
        # New-object test: same rules, unseen objects, training wording.
        for i in range(max(1, args.episodes_per_family // 8)):
            obj = rng.choice(new_objects)
            pool = train_objects + [obj]
            for ep in fn(gen, obj, pool):
                row = render_episode(ep, rng, "train")
                row["split"] = "test_new_object"
                rows.append(row)

    rows = balance(rows, rng, args.max_answer_share)
    # Drop duplicate inputs, and any non-train row whose input also appears in train.
    seen_inputs: set[str] = set()
    train_inputs = {r["input"] for r in rows if r["split"] == "train"}
    deduped = []
    for r in sorted(rows, key=lambda r: r["split"] != "train"):
        if r["input"] in seen_inputs or (r["split"] != "train" and r["input"] in train_inputs):
            continue
        seen_inputs.add(r["input"])
        deduped.append(r)
    rows = deduped
    splits: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        splits[r.pop("split")].append(r)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, items in splits.items():
        items.sort(key=lambda r: stable_hash(r["input"]))
        with (out_dir / f"{name}.jsonl").open("w", encoding="utf-8") as handle:
            for n, r in enumerate(items):
                r["id"] = f"{EXPERIMENT_ID}.{name}.{n:06d}"
                r["experiment_id"] = EXPERIMENT_ID
                r["evaluation_bucket"] = name
                r["messages"] = [{"role": "user", "content": r["input"]}, {"role": "assistant", "content": r["target"]}]
                handle.write(json.dumps(r, sort_keys=True) + "\n")

    report = quality_report(dict(splits))
    (out_dir / "quality_report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "seed": args.seed,
        "episodes_per_family": args.episodes_per_family,
        "max_answer_share": args.max_answer_share,
        "counts": report["counts"],
        "families": list(FAMILIES),
        "train_objects": train_objects,
        "new_objects": new_objects,
        "lexicon": lex_info,
        "affect": {"learn_rate": LEARN_RATE, "familiarity_strengths": FAMILIARITY,
                   "happiness_gain": "rate * (1 - strength)", "sadness": "strength * (1 + 0.15 * (links - 1))"},
        "format": {"prompt_template": "{input}\n", "target_template": "{target}"},
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"closeness: {closeness.mode}")
    failed = [w for w, ok in lex_info["kind_check"].items() if ok is not True and not str(ok).startswith("gap")]
    print(f"WordNet kind check failures: {failed or 'none'}")
    print("held out:", ", ".join(f"{k}~{v['nearest_train']}({v['wup']})" for k, v in lex_info["held_out"].items()))
    print_report(report)


def audit(path: Path) -> None:
    splits = {}
    for f in sorted(path.glob("*.jsonl")):
        splits[f.stem] = [json.loads(l) for l in f.open()]
    if "train" not in splits:
        sys.exit(f"no train.jsonl in {path}")
    report = quality_report(splits)
    print_report(report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--episodes-per-family", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--max-answer-share", type=float, default=0.35)
    parser.add_argument("--no-embeddings", action="store_true", help="use room tags instead of MiniLM closeness")
    parser.add_argument("--audit", type=Path, help="run quality checks on an existing dataset folder and exit")
    args = parser.parse_args()
    if args.audit:
        audit(args.audit)
        return
    generate(args)


if __name__ == "__main__":
    main()
