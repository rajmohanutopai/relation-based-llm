#!/usr/bin/env python3
"""World simulator v1: fixes v0's weak physics tasks and adds the parts the
happiness-sampler experiment needs.

Builds on scripts/create_world_sim_v0.py (renderer, reach/sight rules, quality
checks). Changes from v0:

  Physics
  - Weight has three levels (light, a bit heavy, heavy) and pushes have two
    strengths (gentle, hard). An object moves only when the push is strong
    enough for its weight, so the object's name no longer decides the answer.
  - Rolling needs a round, tube-shaped, or wheeled thing AND a smooth surface.
  - Shaking a closed container makes a sound only if something hard is inside.
  - Drop, push and shake rows sample answers 50/50, then pick a case
    uniformly among those with that answer, across all objects and surfaces.
  - More objects: bell, stool, watermelon, beach ball, rolling pin, toy truck,
    can; held-out tambourine and melon.

  Affect
  - feel_shortcut: watching flashing lights gives quick excitement but no new
    link (the "drug" case: activation without relation gain). Real play gives
    happiness from learning, until it saturates.
  - choice_learn: which of two options teaches the baby more, computed from
    each option's link strength with the (1 - strength) rule.

  Sampler support
  - noise_blink rows: answers are random, so nothing can be learned. Written to
    separate files (train_noise.jsonl, test_noise.jsonl) for the
    happiness-sampler test; the main splits stay clean.

  Wording
  - Scene sentences for tracking, novelty and loss now go through the template
    picker, so test_new_wording holds out those sentences too.

  Hand-written relations
  - Audits the 6mo hand-written relations about world objects against the
    property table and writes handwritten_property_audit.json.
"""

from __future__ import annotations

import argparse
import glob
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import create_world_sim_v0 as v0
from create_world_sim_v0 import (
    OBJECTS, SURFACES, ROOM_SURFACES, FACT_TEMPLATES, FAMILIARITY, Episode, Thing,
    drop_outcome, novelty_gain, happiness_label, sadness_value, sadness_label, caregiver_forms, cap,
)

EXPERIMENT_ID = "world_sim_v1"
DEFAULT_OUTPUT = Path("data/developmental_graph/experiments/world_sim_v1")
HANDWRITTEN_GLOB = "data/developmental_graph/relation_authoring/age_6mo_handwritten_relations_v0/*.jsonl"

v0.EXPERIMENT_ID = EXPERIMENT_ID

# ---------------------------------------------------------------------------
# Lexicon changes
# ---------------------------------------------------------------------------

NEW_OBJECTS = {
    "bell":        dict(kind="toy", size=1, heavy=False, round=False, bouncy=False, hard=True, noisy=True, breakable=False, rooms=["play room", "living room"]),
    "stool":       dict(kind="furniture", size=3, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, rooms=["kitchen", "bathroom"]),
    "watermelon":  dict(kind="food", size=3, heavy=True, round=True, bouncy=False, hard=True, noisy=False, breakable=True, rooms=["kitchen"]),
    "beach ball":  dict(kind="toy", size=3, heavy=False, round=True, bouncy=True, hard=False, noisy=False, breakable=False, rooms=["play room", "living room"]),
    "rolling pin": dict(kind="tableware", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, cylinder=True, rooms=["kitchen"]),
    "toy truck":   dict(kind="toy", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, wheels=True, rooms=["play room", "living room"]),
    "soup can":    dict(kind="container", size=2, heavy=False, round=False, bouncy=False, hard=True, noisy=False, breakable=False, cylinder=True, container="lid", opaque=True, rooms=["kitchen"]),
    # held out
    "tambourine":  dict(kind="toy", size=2, heavy=False, round=True, bouncy=False, hard=True, noisy=True, breakable=False, rooms=["play room"]),
    "melon":       dict(kind="food", size=3, heavy=True, round=True, bouncy=False, hard=True, noisy=False, breakable=True, rooms=["kitchen"]),
}
OBJECTS.update(NEW_OBJECTS)
v0.HELD_OUT_CANDIDATES.extend(["tambourine", "melon"])
v0.WORDNET_NAMES.update({"soup can": "can", "toy truck": "toy", "beach ball": "beach_ball", "rolling pin": "rolling_pin"})
v0.KIND_HYPERNYMS["toy"] += ["musical_instrument.n.01", "bell.n.01"]
v0.KIND_HYPERNYMS["tableware"] += ["kitchen_utensil.n.01", "utensil.n.01"]
v0.KIND_HYPERNYMS["food"] += ["melon.n.01", "edible_fruit.n.01"]
v0.CONTAINER_FITS["food"] |= {"soup can"}
v0.CONTAINER_FITS["toy"] |= {"soup can"}

# The hand-written audit found the bottle has a cap; the v0 table missed it.
OBJECTS["bottle"].update(container="clear_lid", opaque=False)

# v0 marked the bottle and toy car with a generic "rolls" flag and called it
# "wheels". v1 splits wheels from tube shapes.
OBJECTS["toy car"]["wheels"] = True
OBJECTS["bottle"]["cylinder"] = True
for props in OBJECTS.values():
    props.pop("rolls", None)

# Weight: 1 light, 2 a bit heavy (needs a hard push), 3 heavy (does not move).
WEIGHT = {name: (3 if p["heavy"] else 1) for name, p in OBJECTS.items()}
WEIGHT.update({"book": 2, "box": 2, "bucket": 2, "blanket": 2, "stool": 2, "rolling pin": 2,
               "toy truck": 2, "doll": 1, "pillow": 1, "cushion": 1, "chair": 3, "pot": 3,
               "watermelon": 3, "melon": 3, "apple": 1, "orange": 1, "drum": 2, "shoe": 1})

FACT_TEMPLATES.update({
    "medium_weight": ["the {a} is a bit heavy", "the {a} weighs more than a small toy", "the {a} needs a strong push to move", "the {a} is fairly heavy"],
    "gentle_push": ["the push is gentle", "the baby only taps it", "the push is very soft", "the baby barely pushes"],
    "hard_push": ["the push is strong", "the baby pushes with both hands", "the push is hard", "the baby pushes with all its strength"],
    "smooth_surface": ["the {a} is smooth", "the {a} is flat and hard", "the {a} has a smooth top", "things roll easily on the {a}"],
    "rough_surface": ["the {a} is soft and bumpy", "things sink into the {a}", "the {a} is too soft for rolling", "the {a} is soft underneath"],
    "cylinder": ["the {a} is shaped like a tube", "the {a} has round sides", "the {a} is long and round", "the {a} rests on its round side"],
    "empty": ["the {a} is empty", "there is nothing inside the {a}", "the {a} has nothing in it", "nothing is in the {a}"],
})
# v0's "heavy" list had "too heavy to move", which is only true for weight 3; keep.

SMOOTH = {"floor": True, "table": True, "shelf": True, "mat": False, "rug": False, "bed": False}
GENTLE_ACTIONS = ["the baby taps the {o} with one finger", "the baby gives the {o} a soft tap",
                  "the baby nudges the {o} gently", "the baby pats the {o} lightly"]
HARD_ACTIONS = ["the baby pushes the {o} with both hands", "the baby shoves the {o} hard",
                "the baby leans in and pushes the {o} with all its strength", "the baby pushes the {o} as hard as it can"]


def weight_fact(obj: str) -> tuple:
    return {1: ("light", obj), 2: ("medium_weight", obj), 3: ("heavy", obj)}[WEIGHT[obj]]


def shape_fact(obj: str) -> tuple | None:
    p = OBJECTS[obj]
    if p.get("wheels"):
        return ("wheels", obj)
    if p.get("cylinder"):
        return ("cylinder", obj)
    if p["round"]:
        return ("round", obj)
    return None


def push_outcome_v1(obj: str, surface: str, strength: int) -> dict[str, tuple[bool, list]]:
    push = ("gentle_push",) if strength == 1 else ("hard_push",)
    moves = WEIGHT[obj] <= strength
    move_facts = [weight_fact(obj)] + ([push] if WEIGHT[obj] == 2 or (WEIGHT[obj] == 1 and strength == 1) else [])
    shape = shape_fact(obj)
    if not moves:
        roll = (False, move_facts)
    elif shape is None:
        roll = (False, [("not_round", obj)])
    elif not SMOOTH[surface]:
        roll = (False, [shape, ("rough_surface", surface)])
    else:
        roll = (True, [shape, ("smooth_surface", surface)])
    if not moves:
        fall = (False, move_facts)
    elif SURFACES[surface]["high"]:
        fall = (True, move_facts + [("on", obj, surface), ("high", surface)])
    else:
        fall = (False, [("low", surface)])
    return {"moves": (moves, move_facts), "rolls": roll, "falls": fall}


# ---------------------------------------------------------------------------
# Activities for shortcut and choice tasks
# ---------------------------------------------------------------------------

# Shortcut: bright change the baby only watches; its actions cause nothing.
SHORTCUTS = [
    "the phone screen flashes bright colors over and over",
    "a toy on the shelf blinks colored lights all by itself",
    "the TV shows fast flashing pictures",
    "a buzzing toy spins and flashes on its own",
    "a tablet plays loud cartoons that change every second",
]
# Learning play: the baby's own action causes an effect it can learn.
LEARNING = [
    "the baby drops a block into a cup and finds it again",
    "the baby stacks one cup on top of another",
    "the baby pulls a cloth and finds a toy under it",
    "the baby bangs a spoon on a bowl and hears the sound",
    "the baby pushes a ball and watches it roll",
    "the baby squeezes a soft toy and feels it change shape",
    "the baby fills a cup with water in the bath and pours it out",
]
HELD_OUT_SHORTCUTS = {"a tablet plays loud cartoons that change every second"}
HELD_OUT_LEARNING = {"the baby fills a cup with water in the bath and pours it out",
                     "the baby squeezes a soft toy and feels it change shape"}

# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


def opts(*items: str) -> list[str]:
    """A template option list; needs at least 4 for one to be held out."""
    assert len(items) >= 4, items
    return list(items)


class GeneratorV1(v0.Generator):

    def candidates(self, obj: str, pool: list[str]) -> list[str]:
        if obj not in self.train_objects:
            return [obj]
        return [o for o in pool if not OBJECTS[o].get("cover") and not OBJECTS[o].get("container") or o in ("soup can", "box", "bucket")]

    def pick_case(self, cases: list[tuple], want: bool):
        options = [c for c in cases if c[-2] == want]
        return self.rng.choice(options) if options else None

    # drop: case = (obj, surface, ok, facts) -------------------------------

    def drop(self, obj: str, pool: list[str]) -> list[Episode]:
        prop = self.rng.choice(["loud", "bounce", "break"])
        room = self.room_for(obj) if obj not in self.train_objects else self.rng.choice(v0.ROOMS)
        low = [sf for sf in ROOM_SURFACES[room] if not SURFACES[sf]["high"]]
        cases = []
        for o in self.candidates(obj, pool):
            if OBJECTS[o]["size"] > 3 or WEIGHT[o] == 3 and o not in ("watermelon", "melon"):
                continue
            for sf in low:
                ok, facts = drop_outcome(o, sf)[prop]
                cases.append((o, sf, ok, facts))
        out = []
        for want in (True, False):
            case = self.pick_case(cases, want)
            if not case:
                continue
            o, surface, ok, facts = case
            world = self.baby_and_world(room, high=True)
            world.things[o] = Thing(o, surface=surface)
            qs = {
                "loud": ["Does the {o} make a loud sound?", "Is there a loud bang when the {o} lands?",
                         "Does the {o} land with a loud noise?", "Will the {o} make a big noise?"],
                "bounce": ["Does the {o} bounce?", "Will the {o} bounce back up?",
                           "Does the {o} spring up again?", "Does the {o} bounce when it lands?"],
                "break": ["Does the {o} break?", "Will the {o} break?", "Is the {o} broken after it lands?", "Does the {o} crack?"],
            }[prop]
            scene = [("opening", None),
                     ("text", opts("the baby holds the {o}", "the baby has the {o} in one hand",
                                   "the baby is holding the {o}", "the baby grips the {o}")),
                     ("action", opts(f"the baby lets go of the {{o}}, and it falls onto the {surface}",
                                     f"the {{o}} slips out of the baby's hand and drops onto the {surface}",
                                     f"the baby drops the {{o}} on purpose, and it lands on the {surface}",
                                     f"the baby opens its hand, and the {{o}} falls to the {surface}"))]
            out.append(Episode(f"drop_{prop}", scene, (qs[0], qs), "yes" if ok else "no", facts, None, o, [o],
                               f"drop|{o}|{prop}|{self.rng.random():.6f}", {"world": world, "surface": surface}))
        return out

    # push: case = (obj, surface, strength, ok, facts) ------------------------

    def push(self, obj: str, pool: list[str]) -> list[Episode]:
        prop = self.rng.choice(["moves", "rolls", "falls"])
        room = self.room_for(obj) if obj not in self.train_objects else self.rng.choice(v0.ROOMS)
        cases = []
        for o in self.candidates(obj, pool):
            for sf in ROOM_SURFACES[room]:
                if SURFACES[sf]["high"] and OBJECTS[o]["size"] > 3:
                    continue
                for strength in (1, 2):
                    ok, facts = push_outcome_v1(o, sf, strength)[prop]
                    cases.append((o, sf, strength, ok, facts))
        out = []
        for want in (True, False):
            case = self.pick_case(cases, want)
            if not case:
                continue
            o, surface, strength, ok, facts = case
            world = self.baby_and_world(room, high=SURFACES[surface]["high"])
            world.things[o] = Thing(o, surface=surface, near=True)
            qs = {
                "moves": ["Does the {o} move?", "Will the {o} slide away?", "Does the {o} shift?", "Does the push move the {o}?"],
                "rolls": ["Does the {o} roll?", "Will the {o} roll away?", "Does the {o} start rolling?", "Does the {o} roll across the {s}?"],
                "falls": ["Does the {o} fall off the {s}?", "Will the {o} drop off the {s}?", "Does the {o} go over the edge?", "Does the {o} end up falling?"],
            }[prop]
            qs = [q.replace("{s}", surface) for q in qs]
            scene = [("opening", None),
                     ("text", opts(f"the {o} is on the {surface} in front of the baby",
                                   f"the {o} sits on the {surface} right by the baby",
                                   f"the {o} lies on the {surface} next to the baby",
                                   f"the {o} is on the {surface}, close to the baby")),
                     ("action", GENTLE_ACTIONS if strength == 1 else HARD_ACTIONS)]
            out.append(Episode(f"push_{prop}", scene, (qs[0], qs), "yes" if ok else "no", facts, None, o, [o],
                               f"push|{o}|{prop}|{self.rng.random():.6f}",
                               {"world": world, "surface": surface, "push_strength": strength, "weight": WEIGHT[o]}))
        return out

    # shake: a solid thing, or a closed container with or without something hard inside

    def shake(self, obj: str, pool: list[str]) -> list[Episode]:
        holders = [c for c in pool if OBJECTS[c].get("container") in ("lid", "clear_lid") and WEIGHT[c] < 3 and OBJECTS[c]["size"] <= 3]
        new_obj = obj not in self.train_objects
        mode = self.rng.choice(["solid", "container"])
        if new_obj and OBJECTS[obj].get("container") in ("lid", "clear_lid"):
            mode = "container"
            holders = [obj]
        want = self.rng.random() < 0.5
        room = self.room_for(obj)
        world = self.baby_and_world(room)
        if mode == "solid":
            solids = [obj] if new_obj else [o for o in pool if not OBJECTS[o].get("container") and OBJECTS[o]["size"] <= 2]
            solids = [o for o in solids if OBJECTS[o]["noisy"] == want] or solids
            target = self.rng.choice(solids)
            ok = OBJECTS[target]["noisy"]
            facts = [("noisy", target)] if ok else [("quiet", target)]
            world.things[target] = Thing(target, surface="floor")
            scene = [("opening", None),
                     ("text", opts("the baby holds the {o}", "the baby has the {o} in one hand",
                                   "the baby is holding the {o}", "the baby grips the {o}"))]
            meta = {"world": world, "mode": "solid"}
        else:
            box = self.rng.choice(holders) if holders else None
            if box is None:
                return []
            fits = [c for c in ([obj] if new_obj and obj != box else pool)
                    if not OBJECTS[c].get("container") and OBJECTS[c]["size"] < OBJECTS[box]["size"] and not OBJECTS[c].get("cover")]
            hard_inside = [c for c in fits if OBJECTS[c]["hard"]]
            soft_inside = [c for c in fits if not OBJECTS[c]["hard"]]
            if want and hard_inside:
                content = self.rng.choice(hard_inside)
            elif not want:
                content = self.rng.choice(soft_inside + [None]) if soft_inside else None
            else:
                content = None
            target = box
            world.things[box] = Thing(box, surface="floor", closed=True)
            if content:
                world.things[content] = Thing(content, inside=box)
                ok = OBJECTS[content]["hard"]
                facts = [("inside", content, box), ("closed", box), ("hard_obj", content) if ok else ("soft_obj", content)]
            else:
                ok = False
                facts = [("empty", box)]
            c = world.caregiver
            put = (opts(f"{c} puts the {content} in the {box} and closes it",
                        f"{c} drops the {content} into the {box} and shuts the lid",
                        f"{c} hides the {content} in the {box} and puts the lid on",
                        f"{c} places the {content} inside the {box} and closes it") if content else
                   opts(f"{c} closes the empty {box}", f"{c} puts the lid on the empty {box}",
                        f"{c} shuts the {box}, which has nothing inside", f"{c} closes the {box}; nothing is in it"))
            scene = [("opening", None), ("text", put),
                     ("text", opts("{C} gives the {o} to the baby".replace("{C}", cap(c)), f"{cap(c)} hands the baby the {{o}}",
                                   f"the baby takes the {{o}} from {c}", f"{cap(c)} sets the {{o}} in the baby's hands"))]
            meta = {"world": world, "mode": "container", "content": content}
        scene.append(("action", opts("the baby shakes the {o}", "the baby waves the {o} up and down",
                                     "the baby shakes the {o} hard", "the baby swings the {o} back and forth")))
        qs = ["Does the {o} make a sound?", "Is there a noise when the baby shakes the {o}?",
              "Does the baby hear a sound from the {o}?", "Will shaking the {o} make a noise?"]
        return [Episode("shake_sound", scene, (qs[0], qs), "yes" if ok else "no", facts, None, target, [target],
                        f"shake|{target}|{self.rng.random():.6f}", meta)]

    # tracking with picked wording ------------------------------------------

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
        for _ in range(steps - 1):
            current = self.rng.choice([l for l in locations if l != current])
            history.append(current)
        c, C = world.caregiver, cap(world.caregiver)
        first_kind, first_where = history[0]
        scene: list = [("opening", None),
                       ("text", opts(f"the {obj} is on the {first_where}", f"the {obj} lies on the {first_where}",
                                     f"the {obj} sits on the {first_where}", f"at first, the {obj} is on the {first_where}"))]
        for kind, where in history[1:]:
            if kind == "on":
                scene.append(("text", opts(f"{C} puts the {obj} on the {where}", f"{C} picks up the {obj} and sets it on the {where}",
                                           f"{C} moves the {obj} onto the {where}", f"then {c} places the {obj} on the {where}")))
            else:
                scene.append(("text", opts(f"{C} puts the {obj} into the {where}", f"{C} picks up the {obj} and drops it in the {where}",
                                           f"{C} moves the {obj} into the {where}", f"then {c} tucks the {obj} inside the {where}")))
        distract = self.distractor(pool, {obj}, room)
        if distract:
            where = self.surface_in(room)
            scene.insert(self.rng.randint(2, len(scene)), ("text", opts(
                f"{C} puts the {distract} on the {where}", f"{C} sets the {distract} on the {where}",
                f"{C} moves the {distract} onto the {where}", f"then {c} leaves the {distract} on the {where}")))
        prep = "on" if current[0] == "on" else "in"
        answer = f"{prep} the {current[1]}"
        reason = f"{c} put it {prep} the {current[1]} last"
        qs = ["Where is the {o} now?", "Where is the {o} at the end?", "Where can the baby find the {o} now?", "Where did the {o} end up?"]
        return [Episode("track_location", scene, (qs[0], qs), answer, None, reason, obj, [obj] + boxes[:1],
                        f"track|{obj}|{self.rng.random():.6f}", {"steps": steps, "world": world})]

    # novelty with picked wording -------------------------------------------

    def novelty(self, obj: str, pool: list[str]) -> list[Episode]:
        p = OBJECTS[obj]
        if p["noisy"]:
            effect, acts = "sound", opts("the baby shakes the {o}, and it makes a sound", "the baby shakes the {o} and hears it jingle",
                                         "the baby waves the {o}, and a sound comes out", "the baby moves the {o}, and it rattles")
        elif shape_fact(obj):
            effect, acts = "roll", opts("the baby pushes the {o}, and it rolls away", "the baby gives the {o} a push and watches it roll",
                                        "the baby taps the {o}, and it rolls off", "the baby nudges the {o}, and it rolls across the floor")
        elif p["bouncy"]:
            effect, acts = "bounce", opts("the baby drops the {o}, and it bounces", "the baby lets go of the {o} and watches it bounce",
                                          "the baby drops the {o} and sees it spring up", "the {o} falls from the baby's hand and bounces")
        else:
            effect, acts = "feel", opts("the baby squeezes the {o} and feels it in both hands", "the baby turns the {o} over in its hands",
                                        "the baby feels every side of the {o}", "the baby rubs the {o} with its fingers")
        group = f"novelty|{obj}|{self.rng.random():.6f}"
        out = []
        for fam in self.rng.sample(list(FAMILIARITY), 2):
            repeats = self.rng.choice([1, 1, 2, 3, 5])
            gain, strength = novelty_gain(FAMILIARITY[fam], repeats)
            world = self.baby_and_world(self.room_for(obj))
            fam_text = {
                "new": opts(f"the {obj} is new, and the baby has never played with it", f"today the baby sees the {obj} for the first time",
                            f"the {obj} is brand new to the baby", f"the baby has never touched the {obj} before"),
                "seen_once": opts(f"the baby has played with the {obj} once before", f"the baby met the {obj} one time before today",
                                  f"the baby has seen the {obj} just once", f"the {obj} is a little familiar; the baby played with it once"),
                "knows_well": opts(f"the baby has played with the {obj} many times", f"the baby knows the {obj} well",
                                   f"the {obj} is an old toy the baby has used a lot", f"the baby has handled the {obj} again and again"),
                "favorite": opts(f"the {obj} is the baby's favorite, and the baby plays with it every day", f"the baby plays with the {obj} every single day",
                                 f"the {obj} is the baby's best-loved thing", f"every day, the baby reaches first for the {obj}"),
            }[fam]
            scene: list = [("opening", None), ("text", fam_text), ("action", acts)]
            count = {2: "twice", 3: "three times", 5: "five times in a row"}.get(repeats)
            if count:
                scene.append(("text", opts(f"the baby does this {count}", f"the baby tries it {count}",
                                           f"the baby repeats this {count}", f"the same thing happens {count}")))
            if gain >= 0.15:
                reason = f"the baby is still learning what the {obj} does, so each try teaches something new"
            elif gain >= 0.06:
                reason = f"the baby mostly knows what the {obj} does, so there is only a little left to learn"
            else:
                reason = f"the baby already knows what the {obj} does, so doing it again teaches nothing new"
            qs = ["How does the baby feel after the last try?", "How does the baby feel now?",
                  "What does the baby feel at the end?", "How does the last try make the baby feel?"]
            out.append(Episode("feel_novelty", scene, (qs[0], qs), happiness_label(gain), None, reason, obj, [obj], group,
                               {"familiarity": fam, "repeats": repeats, "start_strength": FAMILIARITY[fam],
                                "happiness_gain": round(gain, 4), "strength_after": round(strength, 4), "effect": effect,
                                "world": world}))
        return out

    # loss with picked wording ------------------------------------------------

    def loss(self, obj: str, pool: list[str]) -> list[Episode]:
        group = f"loss|{obj}|{self.rng.random():.6f}"
        boxes = self.containers_for(obj, pool, need="opaque_closable")
        out = []
        for fam in self.rng.sample(list(FAMILIARITY), 2):
            links = {"new": 1, "seen_once": 1, "knows_well": 3, "favorite": 5}[fam]
            value = sadness_value(FAMILIARITY[fam] if fam != "new" else 0.1, links)
            world = self.baby_and_world(self.room_for(obj))
            c, C, pos = world.caregiver, cap(world.caregiver), caregiver_forms(world.caregiver)["c_pos"]
            fam_text = {
                "new": opts(f"the baby got the {obj} today and has not played with it yet", f"the {obj} arrived today; the baby has not used it yet",
                            f"the baby has only just seen the {obj}", f"the {obj} is new, and the baby has not touched it"),
                "seen_once": opts(f"the baby has played with the {obj} once before", f"the baby used the {obj} one time before",
                                  f"the baby knows the {obj} a little", f"the baby has seen the {obj} once"),
                "knows_well": opts(f"the baby plays with the {obj} often and knows it well", f"the baby uses the {obj} most days",
                                   f"the {obj} is very familiar to the baby", f"the baby has played with the {obj} many times"),
                "favorite": opts(f"the {obj} is the baby's favorite; the baby holds it at meals, in the bath, and at bedtime",
                                 f"the baby keeps the {obj} close all day, even at bedtime",
                                 f"the {obj} is the baby's favorite and goes everywhere with the baby",
                                 f"the baby carries the {obj} at meals, at bath time, and in bed"),
            }[fam]
            lasting = self.rng.choice([1.0, 0.6, 0.2])
            if lasting == 1.0:
                event = (opts(f"the {obj} rolls under the couch, where nobody can reach it", f"the {obj} rolls behind the heavy cupboard and is stuck there",
                              f"the {obj} rolls out the door and is lost", f"the {obj} rolls into a gap nobody can reach")
                         if shape_fact(obj) else
                         opts(f"{C} takes the {obj} away and leaves the house with it", f"{C} gives the {obj} away to a neighbor",
                              f"{C} takes the {obj} out of the house for good", f"the {obj} is thrown away and does not come back"))
            elif lasting == 0.6:
                b = self.rng.choice(boxes) if boxes else None
                event = (opts(f"{C} puts the {obj} in the {b}, closes it, and carries it to another room",
                              f"{C} shuts the {obj} in the {b} and takes it away", f"{C} packs the {obj} in the {b} and leaves the room with it",
                              f"{C} closes the {obj} inside the {b} and carries it off") if b else
                         opts(f"{C} puts the {obj} up on a high shelf in another room", f"{C} takes the {obj} to another room for now",
                              f"{C} puts the {obj} away until tomorrow", f"{C} carries the {obj} off to put it away"))
            else:
                event = opts(f"{C} hides the {obj} behind {pos} back and gives it back a moment later",
                             f"the {obj} drops out of sight for a moment, and {c} hands it right back",
                             f"{C} covers the {obj} for a second, then shows it again",
                             f"{C} takes the {obj} for a moment and gives it straight back")
            value *= lasting
            strong = {"new": "the baby has almost no link to the {o} yet", "seen_once": "the baby has only a weak link to the {o}",
                      "knows_well": "the baby has a strong link to the {o}", "favorite": "the {o} is linked to many parts of the baby's day"}[fam].replace("{o}", obj)
            how = {1.0: "and the {o} is gone for good", 0.6: "and the {o} is gone for now", 0.2: "and the {o} comes back right away"}[lasting].replace("{o}", obj)
            qs = ["How does the baby feel?", "How does the baby feel when the {o} is gone?",
                  "What does the baby feel now?", "How does losing the {o} make the baby feel?"]
            out.append(Episode("feel_loss", [("opening", None), ("text", fam_text), ("action", event)], (qs[0], qs),
                               sadness_label(value), None, f"{strong}, {how}", obj, [obj], group,
                               {"familiarity": fam, "links": links, "lasting": lasting, "sadness": round(value, 4), "world": world}))
        return out

    # shortcut: quick excitement without a new link ---------------------------

    def shortcut(self, obj: str, pool: list[str], held_out: bool = False) -> list[Episode]:
        shortcuts = [s for s in SHORTCUTS if (s in HELD_OUT_SHORTCUTS) == held_out]
        learning = [s for s in LEARNING if (s in HELD_OUT_LEARNING) == held_out]
        kind = self.rng.choice(["shortcut", "learning_fresh", "learning_saturated"])
        world = self.baby_and_world(self.rng.choice(["living room", "play room", "bedroom"]))
        if kind == "shortcut":
            activity = self.rng.choice(shortcuts)
            minutes = self.rng.choice(["a few minutes", "ten minutes", "a long time"])
            watch = (opts(f"the baby stares at it for {minutes}", f"the baby watches it for {minutes} without moving",
                          f"the baby keeps looking at it for {minutes}", f"for {minutes}, the baby just watches")
                     if self.rng.random() < 0.5 else
                     opts("the baby stares at it", "the baby watches it without moving",
                          "the baby keeps looking at it", "the baby just watches"))
            scene = [("opening", None), ("text", activity), ("text", watch)]
            answer = "quick excitement but no new learning"
            reason = "the change happens by itself, so nothing the baby does causes it, and no new link forms"
            gain, activation = 0.0, 0.8
        else:
            activity = self.rng.choice(learning)
            if kind == "learning_fresh":
                rep = opts("this is the first time the baby tries it", "the baby has never done this before",
                           "the baby tries this for the first time today", "this is new for the baby")
                gain = novelty_gain(0.0, 1)[0]
                answer = "happiness from learning something new"
                reason = "the baby's own action causes the effect, so a new link forms between doing and seeing"
            else:
                rep = opts("the baby has done this every day for weeks", "the baby has already done this many, many times",
                           "this game is very old for the baby", "the baby has repeated this hundreds of times")
                gain = novelty_gain(0.9, 5)[0]
                answer = "little happiness, because nothing new is left"
                reason = "the link between the action and the effect is already strong, so another try adds almost nothing"
            activation = 0.4
            scene = [("opening", None), ("text", activity), ("text", rep)]
            if self.rng.random() < 0.5:
                minutes = self.rng.choice(["a few minutes", "ten minutes", "a long time"])
                scene.append(("text", opts(f"the baby keeps at it for {minutes}", f"the baby plays like this for {minutes}",
                                           f"for {minutes}, the baby keeps going", f"the baby stays with it for {minutes}")))
        qs = ["What kind of happiness does this give the baby?", "What does this do for the baby's happiness?",
              "Which kind of happiness is this for the baby?", "How does this make the baby happy, if at all?"]
        return [Episode("feel_shortcut", scene, (qs[0], qs), answer, None, reason, "activity", [],
                        f"shortcut|{activity}|{self.rng.random():.6f}",
                        {"world": world, "kind": kind, "activity": activity, "relation_gain": round(gain, 4),
                         "positive_activation": activation})]

    # choice: which option teaches more ---------------------------------------

    def choice(self, obj: str, pool: list[str], held_out: bool = False) -> list[Episode]:
        toys = [o for o in pool if OBJECTS[o]["kind"] == "toy" or o in ("spoon", "cup", "bowl", "book", "box", "basket", "sock", "hat")]
        toys = [o for o in toys if o != obj]
        if obj not in toys and obj in self.train_objects:
            obj = self.rng.choice(toys)
            toys = [o for o in toys if o != obj]
        other = self.rng.choice(toys)
        options = []
        for name in (obj, other):
            fam = self.rng.choice(list(FAMILIARITY))
            repeats = self.rng.choice([0, 0, 3, 10]) if fam != "new" else 0
            strength = FAMILIARITY[fam]
            if repeats:
                strength = novelty_gain(strength, repeats)[1]
            options.append((name, fam, repeats, strength, 0.5 * (1 - strength)))
        # Sometimes the second option is a shortcut with zero relation gain.
        use_shortcut = self.rng.random() < 0.3
        if use_shortcut:
            sc = self.rng.choice([s for s in SHORTCUTS if (s in HELD_OUT_SHORTCUTS) == held_out])
            options[1] = ("flashing screen", "shortcut", 0, None, 0.0)
        a, b = options
        if abs(a[4] - b[4]) < 0.05:
            return []
        best = a if a[4] > b[4] else b
        worst = b if best is a else a

        def describe(o):
            name, fam, repeats, _, _ = o
            if fam == "shortcut":
                return opts("there is also a phone with a flashing screen that changes by itself",
                            "a screen nearby flashes bright colors on its own",
                            "a phone plays flashing lights that the baby can only watch",
                            "a screen shows bright pictures that change without the baby doing anything")
            base = {"new": f"the {name} is new to the baby", "seen_once": f"the baby has played with the {name} once",
                    "knows_well": f"the baby knows the {name} well", "favorite": f"the {name} is the baby's favorite"}[fam]
            alt = {"new": f"the baby has never seen the {name}", "seen_once": f"the baby has seen the {name} one time",
                   "knows_well": f"the {name} is very familiar to the baby", "favorite": f"the baby plays with the {name} every day"}[fam]
            more = f", and today the baby has already played with it {repeats} times" if repeats else ""
            return opts(base + more, alt + more, base + more + " so far", alt + more + " so far")

        order = [a, b]
        self.rng.shuffle(order)
        world = self.baby_and_world(self.room_for(obj))
        scene = [("opening", None), ("text", describe(order[0])), ("text", describe(order[1]))]
        n0, n1 = (o[0] if o[1] != "shortcut" else "flashing screen" for o in order)
        qs = [f"Which will teach the baby more right now: the {n0} or the {n1}?",
              f"What should the baby play with to learn the most: the {n0} or the {n1}?",
              f"Which gives the baby more to learn: the {n0} or the {n1}?",
              f"If the baby wants to learn something new, the {n0} or the {n1}?"]
        why_best = "the baby still has a lot to learn from it" if best[4] >= 0.2 else "the baby still has a little to learn from it"
        why_worst = ("the screen changes by itself, so nothing new is learned" if worst[1] == "shortcut"
                     else "the baby already knows it well, so it teaches less")
        reason = f"the {best[0]} is better because {why_best}, and the {worst[0]} teaches less because {why_worst.replace('it teaches less', 'there is less to learn')}"
        return [Episode("choice_learn", scene, (qs[0], qs), f"the {best[0]}", None, reason, obj, [a[0], b[0]],
                        f"choice|{a[0]}|{b[0]}|{self.rng.random():.6f}",
                        {"world": world, "options": [{"name": o[0], "familiarity": o[1], "repeats": o[2],
                                                      "strength": None if o[3] is None else round(o[3], 4),
                                                      "gain": round(o[4], 4)} for o in (a, b)]})]

    # noise: unlearnable on purpose ---------------------------------------------

    def noise(self, obj: str, pool: list[str]) -> list[Episode]:
        world = self.baby_and_world(self.rng.choice(v0.ROOMS))
        thing = self.rng.choice(["the light by the window", "a small lamp in the corner", "the screen on the wall", "a light on the radio"])
        scene = [("opening", None),
                 ("text", opts(f"{thing} blinks now and then", f"{thing} flickers from time to time",
                               f"{thing} goes on and off with no pattern", f"every so often, {thing} blinks"))]
        qs = ["Will it blink again in the next second?", "Does it blink right after this?",
              "Is the next moment a blink?", "Will it flicker again right away?"]
        answer = self.rng.choice(["yes", "no"])
        return [Episode("noise_blink", scene, (qs[0], qs), answer, None, "the light blinks at random, so nothing tells", "light", [],
                        f"noise|{self.rng.random():.6f}", {"world": world, "unlearnable": True})]


FAMILIES = dict(v0.FAMILIES)
FAMILIES.update({
    "drop": GeneratorV1.drop,
    "push": GeneratorV1.push,
    "shake_sound": GeneratorV1.shake,
    "track_location": GeneratorV1.track,
    "feel_novelty": GeneratorV1.novelty,
    "feel_loss": GeneratorV1.loss,
    "feel_shortcut": GeneratorV1.shortcut,
    "choice_learn": GeneratorV1.choice,
})

# ---------------------------------------------------------------------------
# Hand-written relation audit
# ---------------------------------------------------------------------------

CLAIMS = [
    # (relation set, regex on object text, table field, value)
    ({"has_property"}, r"\bround\b", "round_like", True),
    ({"has_property"}, r"\bhard\b", "hard", True),
    ({"has_property"}, r"\bsoft\b", "hard", False),
    ({"has_property"}, r"\bbouncy\b", "bouncy", True),
    ({"can_do"}, r"\bbounce\b", "bouncy", True),
    ({"can_do", "can_be_done_to"}, r"\broll", "round_like", True),
    ({"cannot_do"}, r"\broll", "round_like", False),
    ({"has_property", "can_be_done_to"}, r"\bbreak", "breakable", True),
    ({"has_property"}, r"\bheavy\b", "heavy_like", True),
    ({"has_property"}, r"\blight\b(?! source)", "heavy_like", False),
    ({"has_property"}, r"\b(noisy|rattl|jingl)", "noisy", True),
    ({"has_property", "has_state"}, r"\b(closable|closed)\b", "closable", True),
]


def table_value(obj: str, field: str) -> bool | None:
    p = OBJECTS[obj]
    if field == "round_like":
        return bool(shape_fact(obj))
    if field == "heavy_like":
        return WEIGHT[obj] >= 2
    if field == "closable":
        return p.get("container") in ("lid", "clear_lid") if p.get("container") else False
    return p.get(field)


def audit_handwritten(out_dir: Path) -> dict[str, Any]:
    rows = [json.loads(l) for f in sorted(glob.glob(HANDWRITTEN_GLOB)) for l in open(f)]
    about = [r for r in rows if r["subject"] in OBJECTS]
    agree, conflict, unmapped = [], [], 0
    for r in about:
        matched = False
        for rels, pattern, field, value in CLAIMS:
            if r["relation"] in rels and re.search(pattern, r["object"]) and not re.search(r"\bnot\b|\boften\b", r["object"]):
                matched = True
                tv = table_value(r["subject"], field)
                item = {"id": r["id"], "text": r["plain_text"], "field": field, "hand_value": value, "table_value": tv}
                (agree if tv == value else conflict).append(item)
        unmapped += not matched
    result = {"rows_about_world_objects": len(about), "checked": len(agree) + len(conflict),
              "agree": len(agree), "conflict": len(conflict), "not_checkable": unmapped, "conflicts": conflict}
    (out_dir / "handwritten_property_audit.json").write_text(json.dumps(result, indent=2))
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def generate(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    closeness = v0.Closeness(not args.no_embeddings, out_dir / "word_vectors.json")
    train_objects, new_objects, lex_info = v0.choose_split_objects(rng)
    gen = GeneratorV1(rng, closeness, train_objects, new_objects)
    lex_info["closeness_mode"] = closeness.mode
    lex_info["container_pairings"] = {o: gen.containers_for(o, train_objects) for o in train_objects if not OBJECTS[o].get("container")}
    lex_info["weights"] = WEIGHT

    usable = [o for o in train_objects if o not in ("chair",) and not OBJECTS[o].get("cover")]
    rows: list[dict[str, Any]] = []
    for family, fn in FAMILIES.items():
        for _ in range(args.episodes_per_family):
            for ep in fn(gen, rng.choice(usable), train_objects):
                g = v0.stable_hash(ep.group) % 100
                split = "train" if g < 80 else ("dev" if g < 88 else "test_iid")
                wording = "train"
                if split == "test_iid" and v0.stable_hash(ep.group + "w") % 2 == 0:
                    split, wording = "test_new_wording", "heldout"
                row = v0.render_episode(ep, rng, wording)
                row["split"] = split
                rows.append(row)
        for _ in range(max(1, args.episodes_per_family // 6)):
            obj = rng.choice(new_objects)
            if family in ("feel_shortcut", "choice_learn"):
                eps = fn(gen, obj, train_objects + [obj], held_out=True)
            else:
                eps = fn(gen, obj, train_objects + [obj])
            for ep in eps:
                row = v0.render_episode(ep, rng, "train")
                row["split"] = "test_new_object"
                rows.append(row)

    rows = v0.balance(rows, rng, args.max_answer_share)
    seen, train_inputs, kept = set(), {r["input"] for r in rows if r["split"] == "train"}, []
    for r in sorted(rows, key=lambda r: r["split"] != "train"):
        if r["input"] in seen or (r["split"] != "train" and r["input"] in train_inputs):
            continue
        seen.add(r["input"])
        kept.append(r)

    # Noise rows go to their own files.
    noise_rows = []
    for i in range(args.noise_rows):
        for ep in gen.noise("light", train_objects):
            row = v0.render_episode(ep, rng, "train")
            row["split"] = "train_noise" if i < int(args.noise_rows * 0.8) else "test_noise"
            noise_rows.append(row)

    splits: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in kept + noise_rows:
        splits[r.pop("split")].append(r)
    for name, items in splits.items():
        items.sort(key=lambda r: v0.stable_hash(r["input"]))
        with (out_dir / f"{name}.jsonl").open("w", encoding="utf-8") as handle:
            for n, r in enumerate(items):
                r.update(id=f"{EXPERIMENT_ID}.{name}.{n:06d}", experiment_id=EXPERIMENT_ID, evaluation_bucket=name,
                         messages=[{"role": "user", "content": r["input"]}, {"role": "assistant", "content": r["target"]}])
                handle.write(json.dumps(r, sort_keys=True) + "\n")

    main_splits = {k: v for k, v in splits.items() if "noise" not in k}
    report = v0.quality_report(main_splits)
    report["noise_counts"] = {k: len(v) for k, v in splits.items() if "noise" in k}
    hand = audit_handwritten(out_dir)
    report["handwritten_audit"] = {k: v for k, v in hand.items() if k != "conflicts"}
    (out_dir / "quality_report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    manifest = {
        "experiment_id": EXPERIMENT_ID, "builds_on": "world_sim_v0", "seed": args.seed,
        "episodes_per_family": args.episodes_per_family, "max_answer_share": args.max_answer_share,
        "counts": {k: len(v) for k, v in splits.items()}, "families": list(FAMILIES),
        "train_objects": train_objects, "new_objects": new_objects, "lexicon": lex_info,
        "shortcuts": SHORTCUTS, "learning_play": LEARNING,
        "held_out_activities": sorted(HELD_OUT_SHORTCUTS | HELD_OUT_LEARNING),
        "affect": {"learn_rate": v0.LEARN_RATE, "familiarity_strengths": FAMILIARITY,
                   "happiness_gain": "rate * (1 - strength)",
                   "sadness": "strength * (1 + 0.15 * (links - 1)) * lasting",
                   "shortcut": "positive_activation high, relation_gain 0"},
        "noise": "noise_blink rows have random answers; use only for the sampler test",
        "format": {"prompt_template": "{input}\n", "target_template": "{target}"},
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"closeness: {closeness.mode}")
    failed = [w for w, ok in lex_info["kind_check"].items() if ok is not True and not str(ok).startswith("gap")]
    print(f"WordNet kind check failures: {failed or 'none'}")
    print("held out:", ", ".join(f"{k}~{v['nearest_train']}({v['wup']})" for k, v in lex_info["held_out"].items()))
    print("noise:", report["noise_counts"])
    print("hand-written audit:", json.dumps(report["handwritten_audit"]))
    v0.print_report(report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--episodes-per-family", type=int, default=1500)
    parser.add_argument("--noise-rows", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--max-answer-share", type=float, default=0.35)
    parser.add_argument("--no-embeddings", action="store_true")
    parser.add_argument("--audit", type=Path, help="run quality checks on an existing dataset folder and exit")
    args = parser.parse_args()
    if args.audit:
        v0.audit(args.audit)
        return
    generate(args)


if __name__ == "__main__":
    main()
