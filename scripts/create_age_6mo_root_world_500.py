#!/usr/bin/env python3
"""Create a 500-concept 6-month root world.

This is a concept-handle dataset, not a spoken-vocabulary estimate. A 6-month
child does not know these as words, but a word-trained model needs explicit
handles for the embodied relations the child can already use behaviorally.
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


SEED_ID = "age_6mo_root_world_500"
EXPERIMENT_ID = "age_6mo_root_world_500"
SCHEMA_VERSION = "0.3.0"
DEFAULT_SEED_PATH = Path("data/developmental_graph/seeds") / f"{SEED_ID}.json"
DEFAULT_OUTPUT_DIR = Path("data/developmental_graph/experiments") / EXPERIMENT_ID
WORD_RE = re.compile(r"[a-z]+")


TARGET_CATEGORY_COUNTS = {
    "core_relation": 45,
    "body_part": 35,
    "body_action_control": 40,
    "sensory_input": 55,
    "body_state_valence": 50,
    "space_motion_physics": 55,
    "object_property": 40,
    "common_object": 55,
    "caregiver_social": 35,
    "routine_event": 45,
    "sound_language_precursor": 25,
    "learning_memory": 20,
}

EXTERNAL_ANCHORS = {
    "world": "outside reference for the whole environment",
    "word": "later language handle, not active 6-month concept",
    "new": "novelty marker used before new-pattern concepts",
    "access": "ability to reach, enter, or interact",
    "feeding": "feeding routine anchor shared by food and caregiver events",
}

ALLOWED_RELATION_TYPES = {
    "is_a",
    "part_of",
    "has_part",
    "has_property",
    "contrasts_with",
    "enables",
    "prevents",
    "needs",
    "uses",
    "causes",
    "caused_by",
    "changes",
    "describes",
    "signals",
    "supports",
    "updates",
    "linked_to",
    "comes_through",
    "moves_toward",
    "moves_away",
    "appears_as",
}

RELATION_TYPE_MAP = {
    "is_root_handle_for": "linked_to",
    "links": "linked_to",
    "enters": "linked_to",
    "points_to": "linked_to",
    "controlled_by": "caused_by",
    "can_be": "has_property",
    "can_cause": "causes",
    "comes_from": "caused_by",
    "reduces": "prevents",
    "increases": "causes",
    "locates": "describes",
    "orders": "describes",
    "makes": "causes",
    "is_amount": "describes",
    "is_more_than": "contrasts_with",
    "belongs_to": "part_of",
    "can_support": "supports",
    "separates": "contrasts_with",
    "can_enable": "enables",
    "used_for": "linked_to",
    "moves": "changes",
    "precedes": "describes",
    "can_increase": "causes",
    "is_repeated": "describes",
    "tries": "linked_to",
    "combines": "linked_to",
    "can_change": "changes",
    "built_from": "caused_by",
    "pulls": "signals",
    "affects": "changes",
    "has_property_meaning": "has_property",
    "can_be_near": "linked_to",
    "can": "has_property",
    "can_make": "causes",
    "can_move": "has_property",
    "can_have_state": "linked_to",
    "is_social_relation": "linked_to",
    "can_update": "updates",
    "can_affect": "changes",
    "supports_input_or_action": "supports",
}

RELATION_TARGET_MAP = {
    "body or attention": "attention",
    "thing or event": "event",
    "inside and outside": "inside",
    "control": "body",
    "body part": "part",
    "seen": "see",
    "touched": "touch",
    "living thing": "body",
    "single": "one",
    "sad": "sad precursor",
    "comfort or discomfort": "comfort",
    "sense/action": "input",
    "food/milk": "milk",
    "voice sound": "voice",
    "look direction": "look",
    "body position": "body",
    "touch and taste": "touch",
    "body feel": "feel",
    "sleep": "sleepiness",
    "blocked reach": "reach fail",
    "touch attention": "attention",
    "expected event": "expectation",
    "repetition": "same",
    "same pattern": "familiar pattern",
    "physical relation": "relation",
    "sound relation": "sound",
    "relation strength": "strong link",
    "learning": "new link",
    "feeding": "feeding",
    "play": "play starts",
    "reached": "reach success",
    "open or closed": "open",
    "wet or dry": "wet",
    "visual social signal": "gesture",
}


LATENT_CONCEPTS = {
    "one", "many", "left", "right",
    "red", "blue", "green", "yellow", "white", "black", "word sound",
    "attention word", "pointing seen", "medicine",
}

EMERGING_CONCEPTS = {
    "part", "whole", "same", "different", "more", "less", "object permanence precursor",
    "joint attention", "sustained attention", "new link", "strong link", "broken link",
    "prediction", "expectation", "habituation", "dishabituation", "means-end precursor",
    "new pattern", "familiar pattern", "surprise mismatch", "memory trace", "cause learning",
    "preference", "avoidance", "imitation precursor", "turn expectation", "curiosity",
    "known pattern comfort", "novelty interest", "anticipation",
    "between", "around", "access", "blocked access",
    "attached", "separate", "edge", "middle",
    "openable", "closable", "edible", "drinkable", "breakable", "safe", "unsafe",
    "familiar", "unfamiliar", "wanted", "not wanted", "too much", "enough",
    "can control", "cannot control", "start", "stop", "again", "gone", "back again",
    "body limit", "support", "boundary", "physical support", "contact", "no contact",
    "waiting", "sound pattern", "repetition comfort", "success feeling", "blocked feeling",
}

INTERNAL_CONCEPTS = {
    "relation", "state", "event", "action", "input", "time now",
    "before", "after", "cause", "effect",
}


def r(kind: str, target: str, text: str, strength: float = 0.75, valence: str = "neutral") -> dict[str, Any]:
    return {"type": kind, "target": target, "text": text, "strength": strength, "valence": valence}


def concept(
    word: str,
    category: str,
    domain: str,
    kind: str,
    summary: str,
    prerequisites: list[str],
    relations: list[dict[str, Any]],
    *,
    aliases: list[str] | None = None,
    status: str = "active",
) -> dict[str, Any]:
    return {
        "id": f"6mo.{category}.{word.replace(' ', '_').replace('/', '_')}",
        "word": word,
        "age_level": "age_6mo",
        "category": category,
        "domains": sorted(set([domain, category])),
        "kind": kind,
        "summary": summary,
        "status": status,
        "prerequisites": prerequisites,
        "aliases": aliases or [],
        "relations": relations,
    }


def build_core_relation() -> list[dict[str, Any]]:
    specs = [
        ("thing", "anything that can be related to something else", [], [r("is_root_handle_for", "world", "thing is the broadest handle")]),
        ("relation", "link between two things or states", ["thing"], [r("links", "thing", "relation links things")]),
        ("state", "how a thing is now", ["thing"], [r("describes", "thing", "state describes a thing now")]),
        ("event", "something that happens and can change state", ["state"], [r("changes", "state", "event can change state")]),
        ("action", "body or object event that can change state", ["event"], [r("is_a", "event", "action is an event that can change state")]),
        ("input", "something coming into body or attention", ["event"], [r("enters", "body or attention", "input enters body or attention")]),
        ("attention", "current focus on thing, event, body state, or person", ["input"], [r("points_to", "thing or event", "attention points to thing or event")]),
        ("need", "body requirement that pulls action or care", ["body"], [r("signals", "action", "need can signal action")]),
        ("sound", "input that can be heard", ["input"], [r("comes_through", "ear", "sound comes through ear")]),
        ("see", "visual input through eyes", ["input", "eye"], [r("comes_through", "eye", "see comes through eye")]),
        ("move", "change place or body position", ["event"], [r("changes", "place", "move changes place")]),
        ("support", "relation that keeps body or object up", ["relation"], [r("prevents", "fall", "support prevents fall")]),
        ("surface", "object area that can support or touch", ["object"], [r("can_support", "object", "surface can support object")]),
        ("boundary", "limit between inside and outside", ["relation"], [r("separates", "inside and outside", "boundary separates inside and outside")]),
        ("self", "directly controlled and directly felt body relation", ["body"], [r("controlled_by", "control", "self is built from control and feeling")]),
        ("not self", "thing or event not directly controlled", ["self"], [r("contrasts_with", "self", "not self contrasts with self")]),
        ("body", "living whole directly felt from inside", ["thing"], [r("has_part", "body part", "body has parts")]),
        ("object", "thing outside body that can be seen or touched", ["thing"], [r("can_be", "seen", "object can be seen"), r("can_be", "touched", "object can be touched")]),
        ("person", "living body with face, voice, touch, and action", ["body"], [r("is_a", "living thing", "person is living thing")]),
        ("place", "where a thing or body can be", ["thing"], [r("locates", "thing", "place locates thing")]),
        ("time now", "current happening or state", ["event"], [r("orders", "event", "time now anchors event")]),
        ("before", "earlier than now or another event", ["event"], [r("orders", "event", "before orders events")]),
        ("after", "later than now or another event", ["event"], [r("orders", "event", "after orders events")]),
        ("cause", "earlier state or event making later state", ["event"], [r("makes", "effect", "cause makes effect")]),
        ("effect", "later state from cause", ["cause"], [r("comes_from", "cause", "effect comes from cause")]),
        ("same", "matching thing, state, or pattern", ["thing"], [r("contrasts_with", "different", "same contrasts with different")]),
        ("different", "not matching thing, state, or pattern", ["thing"], [r("contrasts_with", "same", "different contrasts with same")]),
        ("more", "greater amount, strength, or duration", ["thing"], [r("contrasts_with", "less", "more contrasts with less")]),
        ("less", "smaller amount, strength, or duration", ["thing"], [r("contrasts_with", "more", "less contrasts with more")]),
        ("one", "single thing or event", ["thing"], [r("is_amount", "single", "one marks single thing")]),
        ("many", "more than one thing or event", ["one"], [r("is_more_than", "one", "many is more than one")]),
        ("part", "thing understood as belonging to a larger whole", ["thing"], [r("belongs_to", "whole", "part belongs to whole")]),
        ("whole", "larger thing made of parts", ["thing"], [r("has_part", "part", "whole has parts")]),
        ("near", "small distance from body or thing", ["place"], [r("enables", "touch", "near enables touch")]),
        ("far", "large distance from body or thing", ["place"], [r("prevents", "touch", "far prevents touch")]),
        ("inside", "within boundary or container", ["place"], [r("needs", "boundary", "inside needs boundary")]),
        ("outside", "not within boundary or container", ["inside"], [r("contrasts_with", "inside", "outside contrasts with inside")]),
        ("up", "higher place or direction", ["place"], [r("contrasts_with", "down", "up contrasts with down")]),
        ("down", "lower place or direction", ["place"], [r("contrasts_with", "up", "down contrasts with up")]),
        ("on", "supported by surface", ["place"], [r("needs", "support", "on needs support")]),
        ("off", "not on support or surface", ["on"], [r("contrasts_with", "on", "off contrasts with on")]),
        ("open", "allows entry, flow, or movement", ["state"], [r("enables", "access", "open enables access")]),
        ("closed", "blocks entry, flow, or movement", ["state"], [r("prevents", "access", "closed prevents access")]),
        ("good", "toward comfort, relief, or wanted state", ["state"], [r("can_cause", "happy", "good can cause happy", 0.7, "positive")]),
        ("bad", "toward pain, discomfort, or blocked state", ["state"], [r("can_cause", "sad", "bad can cause sad", 0.7, "negative")]),
    ]
    return [concept(w, "core_relation", "root", "root_handle", s, p, rels) for w, s, p, rels in specs]


def simple_entries(category: str, domain: str, kind: str, specs: list[tuple[str, str, list[str], list[dict[str, Any]]]]) -> list[dict[str, Any]]:
    return [concept(word, category, domain, kind, summary, prereq, rels) for word, summary, prereq, rels in specs]


def build_body_part() -> list[dict[str, Any]]:
    names = [
        "head", "face", "eye", "ear", "nose", "mouth", "tongue", "gum", "lip", "cheek",
        "neck", "shoulder", "arm", "elbow", "wrist", "hand", "palm", "finger", "thumb", "fingernail",
        "chest", "belly", "back", "waist", "hip", "leg", "knee", "ankle", "foot", "toe",
        "skin", "hair", "teeth bud", "stomach", "bottom",
    ]
    specs = []
    for name in names:
        prereq = ["body", "part"]
        rels = [r("part_of", "body", f"{name} is part of body"), r("can_have_state", "comfort or discomfort", f"{name} can be comfortable or uncomfortable")]
        if name in {"eye", "ear", "nose", "mouth", "tongue", "skin", "hand", "foot"}:
            rels.append(r("supports_input_or_action", "sense/action", f"{name} supports input or action"))
        specs.append((name, f"body part: {name}", prereq, rels))
    return simple_entries("body_part", "body", "body_part", specs)


def build_body_action_control() -> list[dict[str, Any]]:
    specs = [
        ("look", "turn eyes or face toward something", ["eye", "object"], [r("uses", "eye", "look uses eyes"), r("can_increase", "attention", "look increases attention")]),
        ("hear", "receive sound through ear", ["ear", "sound"], [r("uses", "ear", "hear uses ear")]),
        ("smell", "receive smell through nose", ["nose"], [r("uses", "nose", "smell uses nose")]),
        ("taste", "receive taste through mouth or tongue", ["mouth", "tongue"], [r("uses", "mouth", "taste uses mouth")]),
        ("touch", "contact between body and thing", ["skin", "hand", "near"], [r("needs", "near", "touch needs near"), r("can_cause", "feel", "touch can cause feel")]),
        ("feel", "body input from touch or inside body", ["body", "state"], [r("comes_from", "body", "feel comes from body")]),
        ("reach", "move hand toward thing", ["hand", "near"], [r("can_enable", "touch", "reach can enable touch")]),
        ("grasp", "close hand around thing", ["hand", "object"], [r("can_enable", "hold", "grasp can enable hold")]),
        ("hold", "keep thing in hand or arms", ["hand", "object"], [r("prevents", "drop", "hold can prevent drop")]),
        ("release", "stop holding thing", ["hold"], [r("can_cause", "drop", "release can cause drop")]),
        ("bring to mouth", "move held thing toward mouth", ["hand", "mouth"], [r("can_enable", "taste", "bring to mouth can enable taste")]),
        ("suck", "mouth action for feeding or soothing", ["mouth"], [r("used_for", "milk", "suck can get milk")]),
        ("swallow", "move food or milk into body", ["mouth"], [r("moves", "food/milk", "swallow moves food or milk inside")]),
        ("can control", "body action changes when the baby acts", ["self", "move"], [r("linked_to", "self", "can control is linked to self"), r("contrasts_with", "cannot control", "can control contrasts with cannot control")]),
        ("cry", "loud body signal of need or discomfort", ["sound", "bad"], [r("signals", "need", "cry can signal need", 0.85, "negative")]),
        ("coo", "soft voice sound", ["sound"], [r("is_a", "voice sound", "coo is voice sound")]),
        ("babble", "repeated mouth sound", ["mouth", "sound"], [r("precedes", "word", "babble comes before words")]),
        ("smile", "face signal often linked to comfort or play", ["face", "good"], [r("signals", "happy", "smile can signal happy", 0.8, "positive")]),
        ("laugh", "happy sound and body event", ["sound", "good"], [r("signals", "happy", "laugh can signal happy", 0.85, "positive")]),
        ("fuss", "unsettled sound and body movement", ["bad"], [r("signals", "discomfort", "fuss can signal discomfort", 0.75, "negative")]),
        ("kick", "move leg quickly", ["leg"], [r("uses", "leg", "kick uses leg")]),
        ("wave arm", "move arm through space", ["arm"], [r("uses", "arm", "wave arm uses arm")]),
        ("open hand", "uncurl fingers", ["hand"], [r("changes", "grasp", "open hand changes grasp")]),
        ("close hand", "curl fingers inward", ["hand"], [r("can_enable", "grasp", "close hand can enable grasp")]),
        ("turn head", "move head toward or away", ["head"], [r("changes", "look direction", "turn head changes look direction")]),
        ("roll body", "turn body on surface", ["body", "surface"], [r("changes", "body position", "roll body changes body position")]),
        ("supported sit", "sit with help or support", ["body", "support"], [r("needs", "support", "supported sit needs support")]),
        ("lean", "body tilts toward side or thing", ["body"], [r("changes", "balance", "lean changes balance")]),
        ("push with hand", "hand presses object away", ["hand", "object"], [r("can_cause", "move", "push with hand can move object")]),
        ("pull with hand", "hand draws object toward self", ["hand", "object"], [r("can_cause", "near", "pull with hand can bring object near")]),
        ("pat", "repeated soft hand touch", ["hand", "touch"], [r("is_repeated", "touch", "pat is repeated touch")]),
        ("bang", "strong contact that makes sound", ["hand", "object"], [r("can_cause", "sound", "bang can cause sound")]),
        ("shake", "move object back and forth", ["hand", "object"], [r("can_cause", "sound", "shake can cause sound")]),
        ("drop", "object leaves hand and moves down", ["release", "down"], [r("causes", "fall", "drop causes fall")]),
        ("cannot control", "thing or event does not change when the baby acts", ["not self", "move"], [r("linked_to", "not self", "cannot control is linked to not self"), r("contrasts_with", "can control", "cannot control contrasts with can control")]),
        ("reach fail", "hand moves but touch does not happen", ["reach", "far"], [r("caused_by", "far", "reach fail can be caused by far")]),
        ("reach success", "hand moves and touch happens", ["reach", "near"], [r("caused_by", "near", "reach success can be caused by near")]),
        ("mouth explore", "use mouth to inspect object", ["mouth", "object"], [r("combines", "touch and taste", "mouth explore combines touch and taste")]),
        ("track movement", "eyes follow moving thing", ["eye", "move"], [r("uses", "see", "track movement uses seeing")]),
        ("settle", "body becomes calmer", ["comfort"], [r("caused_by", "comfort", "settle can be caused by comfort", 0.75, "positive")]),
    ]
    return simple_entries("body_action_control", "body", "action", specs)


def build_sensory_input() -> list[dict[str, Any]]:
    visual = ["face seen", "eye contact", "mouth movement seen", "hand movement seen", "near object seen", "moving object seen", "bright color seen", "light seen", "dark seen", "ceiling fan seen", "door movement seen", "mirror image seen", "food seen"]
    sound = ["familiar voice heard", "unfamiliar voice heard", "mother voice", "father voice", "caregiver voice", "name sound", "song heard", "rhyme heard", "rattle sound", "fan hum", "vacuum sound", "traffic horn", "dog bark", "bird sound", "sudden loud sound"]
    touch = ["held touch", "skin contact", "cloth touch", "blanket touch", "mat touch", "water touch", "oil touch", "toy surface touch", "spoon touch", "bottle nipple touch", "air breeze touch", "warm touch", "cool touch"]
    taste_smell = ["milk taste", "sweet taste", "sour taste", "bitter taste", "caregiver smell", "milk smell", "soap smell", "food smell", "medicine smell"]
    body_balance = ["head position feel", "hand position feel", "foot position feel", "belly inside feel", "rolling balance feel"]
    names = visual + sound + touch + taste_smell + body_balance
    specs = []
    for name in names:
        if "seen" in name or name in {"eye contact", "light seen", "dark seen", "shadow seen"}:
            prereq, sense = ["see", "object"], "see"
        elif "sound" in name or "voice" in name or "heard" in name or name in {"fan hum", "traffic horn", "dog bark", "bird sound", "vacuum sound", "doorbell sound", "phone sound"}:
            prereq, sense = ["hear", "sound"], "hear"
        elif "taste" in name:
            prereq, sense = ["taste", "mouth"], "taste"
        elif "smell" in name:
            prereq, sense = ["smell", "nose"], "smell"
        elif "position feel" in name or "inside feel" in name or "balance feel" in name:
            prereq, sense = ["body", "feel"], "body feel"
        else:
            prereq, sense = ["touch", "skin"], "touch"
        specs.append((name, f"sensory input: {name}", prereq, [r("comes_through", sense, f"{name} comes through {sense}"), r("can_change", "attention", f"{name} can change attention")]))
    return simple_entries("sensory_input", "sense", "sensory_input", specs)


def build_body_state_valence() -> list[dict[str, Any]]:
    specs = [
        ("hunger", "body need for milk or food", ["body", "bad"], [r("signals", "need", "hunger signals need", 0.9, "negative")]),
        ("fullness", "body state after enough feeding", ["body", "good"], [r("reduces", "hunger", "fullness reduces hunger", 0.85, "positive")]),
        ("thirst", "body need for liquid", ["body", "need"], [r("signals", "need", "thirst signals need", 0.75, "negative")]),
        ("sleepiness", "body need for sleep", ["body", "need"], [r("signals", "sleep", "sleepiness signals sleep need")]),
        ("tired body", "body has low energy", ["body"], [r("can_cause", "fuss", "tired body can cause fuss")]),
        ("rested body", "body after sleep or rest", ["body", "good"], [r("can_cause", "comfort", "rested body can cause comfort", 0.7, "positive")]),
        ("pain", "bad body feeling", ["body", "bad"], [r("causes", "bad", "pain causes bad", 0.9, "negative")]),
        ("discomfort", "body or situation is not okay", ["body", "bad"], [r("can_cause", "fuss", "discomfort can cause fuss", 0.8, "negative")]),
        ("comfort", "body and situation feel okay", ["body", "good"], [r("can_cause", "settle", "comfort can cause settle", 0.85, "positive")]),
        ("relief", "bad state reduces", ["bad", "good"], [r("reduces", "bad", "relief reduces bad", 0.85, "positive")]),
        ("startle", "sudden body reaction", ["sound", "event"], [r("can_cause", "cry", "startle can cause cry", 0.7, "negative")]),
        ("fear precursor", "avoid state from sudden or unfamiliar input", ["bad"], [r("can_cause", "cry", "fear precursor can cause cry", 0.6, "negative")]),
        ("happy", "positive feeling from comfort, play, or new link", ["good"], [r("caused_by", "comfort", "happy can be caused by comfort", 0.8, "positive")]),
        ("sad precursor", "negative feeling from pain, loss, or blocked relation", ["bad"], [r("caused_by", "pain", "sad precursor can be caused by pain", 0.7, "negative")]),
        ("frustration", "bad state when wanted action is blocked", ["bad"], [r("caused_by", "blocked reach", "frustration can be caused by blocked reach", 0.8, "negative")]),
        ("interest", "attention pulled toward input", ["attention"], [r("increases", "look", "interest increases looking")]),
        ("boredom precursor", "attention drops after repeated known input", ["attention"], [r("reduces", "attention", "boredom precursor reduces attention")]),
        ("surprise", "new or unexpected input changes attention", ["event"], [r("increases", "attention", "surprise increases attention")]),
        ("calm", "low fuss and settled body", ["comfort"], [r("caused_by", "comfort", "calm can be caused by comfort", 0.8, "positive")]),
        ("upset", "fuss or cry state", ["bad"], [r("signals", "need", "upset can signal need", 0.75, "negative")]),
        ("wet discomfort", "bad body state from wet cloth or diaper", ["wet", "discomfort"], [r("causes", "discomfort", "wet discomfort causes discomfort")]),
        ("cold discomfort", "bad body state from cold", ["cold", "discomfort"], [r("causes", "discomfort", "cold discomfort causes discomfort")]),
        ("warm comfort", "good body state from warmth", ["warm", "comfort"], [r("causes", "comfort", "warm comfort causes comfort", 0.7, "positive")]),
        ("hot discomfort", "bad body state from heat", ["hot", "discomfort"], [r("can_cause", "pain", "hot discomfort can cause pain", 0.7, "negative")]),
        ("itch", "skin discomfort that pulls touch attention", ["skin", "discomfort"], [r("causes", "touch attention", "itch causes touch attention")]),
        ("pressure comfort", "good feeling from held pressure", ["held touch", "comfort"], [r("can_cause", "comfort", "pressure comfort can cause comfort", 0.75, "positive")]),
        ("pressure discomfort", "bad feeling from too much pressure", ["touch", "discomfort"], [r("can_cause", "discomfort", "pressure discomfort can cause discomfort")]),
        ("gas discomfort", "belly discomfort after feeding", ["belly", "discomfort"], [r("can_cause", "cry", "gas discomfort can cause cry", 0.75, "negative")]),
        ("mouth comfort", "comfort from sucking or mouthing", ["mouth", "comfort"], [r("can_cause", "settle", "mouth comfort can cause settle")]),
        ("wanted", "state where attention and action pull toward a thing or event", ["attention", "good"], [r("signals", "reach", "wanted can signal reach"), r("causes", "interest", "wanted can cause interest", 0.75, "positive")]),
        ("effort", "body strain during action", ["body", "action"], [r("can_cause", "tired body", "effort can cause tired body")]),
        ("success feeling", "good state after action works", ["good", "effect"], [r("caused_by", "reach success", "success feeling can follow reach success", 0.7, "positive")]),
        ("blocked feeling", "bad state after action fails", ["bad", "effect"], [r("caused_by", "reach fail", "blocked feeling can follow reach fail", 0.75, "negative")]),
        ("anticipation", "attention toward expected event", ["before", "event"], [r("points_to", "expected event", "anticipation points toward expected event")]),
        ("expectation", "relation from repeated before/after pattern", ["before", "after"], [r("built_from", "repetition", "expectation is built from repetition")]),
        ("satiety relief", "relief after hunger reduces", ["hunger", "relief"], [r("reduces", "hunger", "satiety relief reduces hunger", 0.9, "positive")]),
        ("social comfort", "comfort from familiar person", ["person", "comfort"], [r("caused_by", "caregiver", "social comfort can be caused by caregiver", 0.85, "positive")]),
        ("separation distress", "bad state when caregiver is gone", ["caregiver gone", "bad"], [r("caused_by", "caregiver gone", "separation distress can follow caregiver gone", 0.75, "negative")]),
        ("novelty interest", "attention toward new input", ["new", "attention"], [r("increases", "attention", "novelty interest increases attention")]),
        ("repetition comfort", "comfort from familiar repeated pattern", ["same", "comfort"], [r("caused_by", "same pattern", "repetition comfort can come from same pattern")]),
        ("too much", "input or pressure is more than body can settle with", ["more", "bad"], [r("causes", "fuss", "too much can cause fuss", 0.75, "negative")]),
        ("quiet relief", "relief when sound reduces", ["sound", "relief"], [r("reduces", "startle", "quiet relief reduces startle")]),
        ("clean comfort", "comfort after wet or dirty state changes", ["comfort"], [r("reduces", "wet discomfort", "clean comfort reduces wet discomfort")]),
        ("enough", "need or input has reached a settled amount", ["less", "good"], [r("prevents", "hunger", "enough can prevent hunger", 0.8, "positive"), r("causes", "calm", "enough can cause calm", 0.75, "positive")]),
        ("not wanted", "state where attention or body pulls away from a thing or event", ["attention", "bad"], [r("signals", "avoidance", "not wanted can signal avoidance", 0.75, "negative"), r("causes", "fuss", "not wanted can cause fuss", 0.65, "negative")]),
        ("care need", "need that asks for caregiver action", ["need", "caregiver"], [r("pulls", "caregiver", "care need pulls caregiver action", 0.8, "negative")]),
        ("touch pleasure", "good feeling from safe touch", ["touch", "good"], [r("can_cause", "happy", "touch pleasure can cause happy", 0.75, "positive")]),
        ("play pleasure", "good feeling from play relation", ["good", "event"], [r("can_cause", "happy", "play pleasure can cause happy", 0.75, "positive")]),
        ("voice comfort", "comfort from familiar gentle voice", ["sound", "comfort"], [r("can_cause", "settle", "voice comfort can cause settle", 0.75, "positive")]),
        ("known pattern comfort", "comfort from repeated expected relation", ["same", "comfort"], [r("caused_by", "familiar pattern", "known pattern comfort comes from familiar pattern", 0.75, "positive")]),
    ]
    return simple_entries("body_state_valence", "valence", "body_state", specs)


def build_space_motion_physics() -> list[dict[str, Any]]:
    specs = []
    names = [
        ("left", "side direction relative to body"), ("right", "side direction relative to body"), ("front", "space before body or face"), ("behind", "space after or hidden from face"),
        ("above", "higher than thing"), ("below", "lower than thing"), ("between", "space with things on two sides"), ("around", "space surrounding thing"),
        ("toward", "direction closer to thing"), ("away", "direction farther from thing"), ("here", "place of self or current attention"), ("there", "place away from current attention"),
        ("visible", "can be seen"), ("hidden", "not visible though may still exist"), ("appears", "becomes visible or present"), ("disappears", "becomes hidden or gone"),
        ("still", "not moving"), ("moving", "changing place"), ("fast", "more movement in less time"), ("slow", "less movement in same time"),
        ("fall", "move down when support is gone"), ("roll", "turning movement along surface"), ("slide", "smooth movement along surface"), ("bounce", "hit and move back"),
        ("hit", "strong contact"), ("bump", "small hit"), ("push effect", "object moves away after push"), ("pull effect", "object moves closer after pull"),
        ("physical support", "relation that keeps thing from falling"), ("no support", "support missing"), ("balance", "body or object stays up"), ("tip over", "upright thing falls to side"),
        ("edge", "end of surface"), ("middle", "away from edge"), ("container", "object that can hold inside"), ("body limit", "felt edge of what the body can control"),
        ("gone", "thing was present and is not present now"), ("back again", "thing was gone and is present again"), ("access", "can reach or enter"), ("blocked access", "cannot reach or enter"),
        ("contact", "touch relation holds"), ("no contact", "touch relation does not hold"), ("attached", "two things stay together"), ("separate", "two things apart"),
        ("wet", "water on thing"), ("dry", "water absent"), ("warm", "mild heat felt as okay"), ("cold", "low temperature felt by body"),
        ("hot", "high temperature that may hurt"), ("light source", "thing that makes seeing possible"), ("darkness", "low light state"), ("shadow", "dark shape from blocked light"),
        ("sound source", "thing or event making sound"), ("vibration", "repeated small movement"), ("pressure", "force on body or object"),
    ]
    for name, summary in names:
        prereq = ["thing", "state"]
        rels = [r("describes", "physical relation", f"{name} describes a physical relation")]
        if name in {"visible", "hidden", "appears", "disappears"}:
            rels.append(r("affects", "see", f"{name} affects seeing"))
        if name in {"fall", "roll", "slide", "bounce", "hit", "bump", "push effect", "pull effect"}:
            rels.append(r("is_a", "event", f"{name} is an event"))
        specs.append((name, summary, prereq, rels))
    return simple_entries("space_motion_physics", "physical", "physical_relation", specs)


def build_object_property() -> list[dict[str, Any]]:
    names = [
        ("soft", "changes shape easily and may comfort"), ("hard", "does not change shape easily"), ("smooth", "even surface feel"), ("rough", "uneven surface feel"),
        ("sharp", "can cut or hurt"), ("blunt", "not sharp"), ("round", "curved shape"), ("flat", "level surface shape"), ("long", "extended shape"),
        ("short", "small length"), ("big", "large size"), ("small", "small size"), ("heavy", "hard to move"), ("light weight", "easy to move"),
        ("bright", "strong light or color"), ("dim", "low light"), ("colorful", "has many colors"), ("red", "red color"), ("blue", "blue color"),
        ("green", "green color"), ("yellow", "yellow color"), ("white", "white color"), ("black", "black color"), ("clean", "without dirt"),
        ("dirty", "has dirt or mess"), ("sticky", "surface holds to skin or object"), ("slippery", "hard to hold because it slides"), ("squishy", "soft and changes shape"),
        ("bouncy", "returns after hit or press"), ("noisy", "makes sound"), ("quiet", "little or no sound"), ("safe", "unlikely to hurt"), ("unsafe", "may hurt"),
        ("openable", "can become open"), ("closable", "can become closed"), ("edible", "can be eaten"), ("drinkable", "can be drunk"), ("breakable", "can break"),
        ("familiar", "known from repeated experience"), ("unfamiliar", "not known or not repeated"),
    ]
    specs = []
    for name, summary in names:
        rels = [r("has_property_meaning", "object", f"{name} can describe object")]
        if name in {"sharp", "hot", "unsafe"}:
            rels.append(r("can_cause", "pain", f"{name} can cause pain", 0.8, "negative"))
        if name in {"soft", "safe", "familiar"}:
            rels.append(r("can_cause", "comfort", f"{name} can support comfort", 0.7, "positive"))
        specs.append((name, summary, ["object", "state"], rels))
    return simple_entries("object_property", "property", "property", specs)


def build_common_object() -> list[dict[str, Any]]:
    names = [
        "milk", "breast", "bottle", "nipple", "cup", "spoon", "bowl", "banana", "rice", "oatmeal", "applesauce", "puree", "water", "medicine",
        "cloth", "blanket", "towel", "diaper", "wipes", "shirt", "bib", "pillow", "bed", "mat", "floor", "chair", "table",
        "toy", "ball", "rattle", "teether", "doll", "block", "cube", "ring toy", "soft toy", "toy car", "book", "picture book", "paper", "mirror", "comb",
        "oil", "soap", "bath water", "fan", "light bulb", "window", "door", "curtain",
        "box", "basket", "dog", "bird", "mosquito",
    ]
    specs = []
    for name in names:
        prereq = ["object"]
        rels = [r("is_a", "object", f"{name} is an object in the 6mo world")]
        if name in {"milk", "breast", "bottle", "nipple", "cup", "spoon", "bowl", "plate", "banana", "rice", "oatmeal", "applesauce", "puree", "water"}:
            rels.append(r("used_for", "feeding", f"{name} can be linked to feeding", 0.8, "positive"))
            rels.append(r("can_be_near", "mouth", f"{name} can be near mouth during feeding"))
        if name in {"ball", "rattle", "teether", "doll", "block", "cube", "ring toy", "soft toy", "toy car"}:
            rels.append(r("used_for", "play", f"{name} can be used for play", 0.75, "positive"))
            rels.append(r("can_be", "reached", f"{name} can be reached or held"))
        if name in {"ball", "toy car"}:
            rels.append(r("can", "roll", f"{name} can roll"))
        if name in {"rattle"}:
            rels.append(r("can_make", "sound", f"{name} can make sound"))
        if name in {"teether"}:
            rels.append(r("used_for", "mouth comfort", f"{name} can support mouth comfort", 0.7, "positive"))
        if name in {"cloth", "blanket", "towel", "diaper", "wipes", "shirt", "sock", "cap", "bib", "pillow", "bed", "mat"}:
            rels.append(r("can_support", "comfort", f"{name} can support comfort", 0.7, "positive"))
        if name in {"diaper", "wipes", "towel", "cloth"}:
            rels.append(r("can_be", "wet or dry", f"{name} can be wet or dry"))
        if name == "fan":
            rels.extend([r("can_make", "air breeze touch", "fan can make air breeze touch"), r("can_make", "fan hum", "fan can make fan hum")])
        if name == "light bulb":
            rels.append(r("can_cause", "light seen", "light bulb can cause light seen"))
        if name in {"window", "door", "curtain", "box", "basket"}:
            rels.append(r("can_have_state", "open or closed", f"{name} can be open or closed"))
        if name in {"dog", "bird", "mosquito"}:
            rels.append(r("can_move", "moving", f"{name} can move"))
        if name == "dog":
            rels.append(r("can_make", "dog bark", "dog can make dog bark"))
        if name == "bird":
            rels.append(r("can_make", "bird sound", "bird can make bird sound"))
        if name == "mosquito":
            rels.append(r("can_cause", "itch", "mosquito can cause itch", 0.65, "negative"))
        specs.append((name, f"common 6mo object: {name}", prereq, rels))
    return simple_entries("common_object", "object", "object", specs)


def build_caregiver_social() -> list[dict[str, Any]]:
    names = [
        ("caregiver", "familiar person who protects, feeds, and comforts"), ("mother", "primary or familiar caregiver"), ("father", "familiar caregiver"),
        ("grandmother", "familiar elder caregiver"), ("grandfather", "familiar elder caregiver"), ("sibling", "child or young person in family"),
        ("familiar face", "known face from repeated experience"), ("unfamiliar face", "face not yet known"), ("familiar voice", "known voice from repeated experience"),
        ("unfamiliar voice", "voice not yet known"), ("being held", "body supported by person"), ("being picked up", "person moves body upward"),
        ("being put down", "person places body on surface"), ("being rocked", "repeated caregiver movement"), ("being carried", "person moves while holding body"),
        ("being fed", "caregiver gives milk or food"), ("being burped", "held upright after feeding"), ("being changed", "diaper or cloth changed"),
        ("being bathed", "caregiver uses water on body"), ("being dressed", "caregiver puts cloth on body"), ("being soothed", "caregiver reduces distress"),
        ("peekaboo", "face disappears and appears in play"), ("shared smile", "smile exchanged with person"), ("call response", "voice draws attention"),
        ("attention from caregiver", "caregiver looks, talks, or touches"), ("caregiver gone", "familiar caregiver not visible or near"),
        ("caregiver returns", "familiar caregiver appears again"), ("stranger approach", "unfamiliar person comes near"), ("with caregiver", "caregiver is near or holding"),
        ("alone", "caregiver is not near or holding"), ("lap", "place on caregiver body"), ("not held", "body is not supported by caregiver arms"), ("hug", "close body contact"),
        ("safe touch", "touch that does not hurt and can comfort"), ("gentle touch", "soft social touch"),
    ]
    specs = []
    for name, summary in names:
        rels = [r("is_social_relation", "person", f"{name} is linked to person relation")]
        if "caregiver" in name or name in {"mother", "father", "grandmother", "grandfather", "being held", "being soothed", "caregiver returns", "gentle touch"}:
            rels.append(r("can_cause", "comfort", f"{name} can cause comfort", 0.8, "positive"))
        if name in {"caregiver gone", "stranger approach", "unfamiliar face", "unfamiliar voice", "alone", "not held"}:
            rels.append(r("can_cause", "discomfort", f"{name} can cause discomfort", 0.65, "negative"))
        specs.append((name, summary, ["person"], rels))
    return simple_entries("caregiver_social", "social", "social_relation", specs)


def build_routine_event() -> list[dict[str, Any]]:
    names = [
        ("wake from sleep", "sleep state ends"), ("sleep onset", "body moves into sleep"), ("nap", "short sleep event"), ("night sleep", "long dark sleep event"),
        ("feeding starts", "milk or food event begins"), ("feeding pauses", "feeding stops briefly"), ("feeding ends", "milk or food event ends"),
        ("burp event", "air leaves body after feed"), ("spit up", "milk comes back out"), ("new food taste", "new taste enters mouth"),
        ("familiar food taste", "known taste enters mouth"), ("reject taste", "mouth turns away from taste"), ("bath starts", "water routine begins"),
        ("bath ends", "water routine ends"), ("oil massage", "caregiver rubs oil on skin"), ("diaper change", "wet or dirty cloth changes"),
        ("clothes change", "cloth on body changes"), ("play starts", "toy or social play begins"), ("play stops", "play ends"),
        ("toy appears", "toy becomes visible or reachable"), ("toy disappears", "toy becomes hidden or gone"), ("object falls", "object moves down"),
        ("object rolls away", "object moves away by rolling"), ("object comes near", "object becomes reachable"), ("object becomes far", "object becomes unreachable"),
        ("sound starts", "sound event begins"), ("sound stops", "sound event ends"), ("loud sound happens", "sudden strong sound event"),
        ("light turns on", "dark changes to light"), ("light turns off", "light changes to dark"), ("fan starts", "fan movement begins"),
        ("fan stops", "fan movement ends"), ("door opens", "closed path becomes open"), ("door closes", "open path becomes closed"),
        ("caregiver enters", "caregiver appears in place"), ("caregiver leaves", "caregiver disappears from place"), ("pickup after cry", "cry followed by being picked up"),
        ("soothing after cry", "cry followed by comfort action"), ("blocked reach event", "reach does not touch wanted object"), ("successful reach event", "reach touches wanted object"),
        ("shared play event", "person and child play together"), ("waiting", "expected event has not happened yet"),
        ("start", "event begins"), ("stop", "event ends or action ends"), ("again", "same event happens one more time"),
    ]
    specs = [(name, summary, ["event"], [r("is_a", "event", f"{name} is an event"), r("can_update", "expectation", f"{name} can update expectation")]) for name, summary in names]
    return simple_entries("routine_event", "event", "event", specs)


def build_sound_language_precursor() -> list[dict[str, Any]]:
    names = [
        ("voice", "human sound from mouth"), ("high voice", "voice with high pitch"), ("soft voice", "quiet gentle voice"),
        ("loud voice", "strong voice sound"), ("angry voice", "voice pattern linked to bad social state"), ("happy voice", "voice pattern linked to good social state"),
        ("song", "repeated musical voice pattern"), ("rhyme", "repeated sound pattern"), ("name-like sound", "repeated sound linked to attention"),
        ("home language sound", "speech sounds heard often at home"), ("syllable", "small repeated speech sound"),
        ("word sound", "sound pattern that can later name thing"), ("gesture", "body movement used as signal"), ("pointing seen", "hand direction signal seen"),
        ("wave seen", "hand social signal seen"), ("clap sound", "hand sound linked to play"), ("laughter heard", "happy sound heard"),
        ("cry heard", "distress sound heard"), ("shush sound", "soothing sound"), ("no sound", "absence or reduction of sound"),
        ("turn-taking sound", "sound followed by another sound"), ("call", "voice directed toward child"), ("response sound", "sound after call"),
        ("sound pattern", "repeated sound relation"), ("attention word", "sound that pulls attention"),
    ]
    specs = []
    for name, summary in names:
        if name in {"gesture", "pointing seen", "wave seen"}:
            prereq = ["see", "body"]
            rels = [r("is_a", "visual social signal", f"{name} is a visual social signal"), r("can_affect", "attention", f"{name} can affect attention")]
        else:
            prereq = ["sound"]
            rels = [r("is_a", "sound relation", f"{name} is a sound relation"), r("can_affect", "attention", f"{name} can affect attention")]
        specs.append((name, summary, prereq, rels))
    return simple_entries("sound_language_precursor", "language", "language_precursor", specs)


def build_learning_memory() -> list[dict[str, Any]]:
    names = [
        ("sustained attention", "focus stays on thing, event, or person"), ("joint attention", "child and caregiver attend to same thing"), ("familiar pattern", "same relation repeated"),
        ("new pattern", "relation not yet familiar"), ("prediction", "expected next event from pattern"), ("surprise mismatch", "expected relation fails"),
        ("habituation", "attention reduces after repeated known input"), ("dishabituation", "attention returns when input changes"), ("memory trace", "relation remains after event"),
        ("object permanence precursor", "hidden object may still exist"), ("cause learning", "event relation strengthens after repetition"), ("means-end precursor", "action used to get effect"),
        ("preference", "stronger pull toward one thing or event"), ("avoidance", "pull away from bad thing or event"), ("imitation precursor", "body action follows seen action"),
        ("turn expectation", "one event follows another in social rhythm"), ("new link", "new relation is created"), ("strong link", "repeated relation becomes strong"),
        ("broken link", "expected relation fails or disappears"), ("curiosity", "attention toward new relation"),
    ]
    specs = [(name, summary, ["relation", "event"], [r("updates", "relation strength", f"{name} updates relation strength"), r("supports", "learning", f"{name} supports learning")]) for name, summary in names]
    return simple_entries("learning_memory", "learning", "learning_relation", specs)


HUB_RELATIONS = {
    "attention": [
        r("linked_to", "input", "attention is pulled by input"),
        r("linked_to", "look", "attention can guide looking"),
        r("changes", "new link", "attention can support a new link", 0.8, "positive"),
    ],
    "need": [
        r("signals", "cry", "need can signal through cry", 0.8, "negative"),
        r("linked_to", "caregiver", "need can pull caregiver action"),
        r("causes", "action", "need can cause action"),
    ],
    "self": [
        r("linked_to", "body", "self is linked to directly felt body"),
        r("linked_to", "move", "self is linked to controlled movement"),
        r("contrasts_with", "not self", "self contrasts with not self"),
    ],
    "object": [
        r("has_property", "see", "object can be seen"),
        r("has_property", "touch", "object can be touched"),
        r("contrasts_with", "body", "object contrasts with directly felt body"),
    ],
    "person": [
        r("is_a", "body", "person is a body"),
        r("linked_to", "voice", "person can have voice"),
        r("linked_to", "touch", "person can touch"),
        r("causes", "comfort", "familiar person can cause comfort", 0.75, "positive"),
    ],
    "near": [
        r("enables", "touch", "near enables touch"),
        r("enables", "reach success", "near enables reach success"),
        r("contrasts_with", "far", "near contrasts with far"),
    ],
    "far": [
        r("prevents", "touch", "far prevents touch"),
        r("causes", "reach fail", "far can cause reach fail", 0.75, "negative"),
        r("contrasts_with", "near", "far contrasts with near"),
    ],
    "comfort": [
        r("causes", "settle", "comfort can cause settle", 0.85, "positive"),
        r("causes", "happy", "comfort can cause happy", 0.8, "positive"),
        r("contrasts_with", "pain", "comfort contrasts with pain"),
        r("contrasts_with", "discomfort", "comfort contrasts with discomfort"),
    ],
    "pain": [
        r("causes", "bad", "pain causes bad", 0.9, "negative"),
        r("causes", "cry", "pain can cause cry", 0.85, "negative"),
        r("contrasts_with", "comfort", "pain contrasts with comfort"),
        r("linked_to", "body", "pain is felt in body"),
    ],
    "happy": [
        r("caused_by", "comfort", "happy can be caused by comfort", 0.8, "positive"),
        r("caused_by", "new link", "happy can be caused by new link", 0.8, "positive"),
        r("caused_by", "play pleasure", "happy can be caused by play pleasure", 0.75, "positive"),
        r("contrasts_with", "sad precursor", "happy contrasts with sad precursor"),
    ],
    "new link": [
        r("updates", "strong link", "new link can become strong link", 0.85, "positive"),
        r("causes", "happy", "new link can cause happy", 0.8, "positive"),
        r("linked_to", "curiosity", "new link is linked to curiosity"),
    ],
    "broken link": [
        r("causes", "sad precursor", "broken link can cause sad precursor", 0.75, "negative"),
        r("causes", "surprise mismatch", "broken link can cause surprise mismatch"),
        r("contrasts_with", "strong link", "broken link contrasts with strong link"),
    ],
    "body limit": [
        r("linked_to", "self", "body limit is linked to self"),
        r("contrasts_with", "not self", "body limit separates self from not self"),
        r("linked_to", "can control", "body limit is learned through can control"),
        r("linked_to", "cannot control", "body limit is learned through cannot control"),
    ],
    "gone": [
        r("caused_by", "disappears", "gone can be caused by disappears"),
        r("contrasts_with", "visible", "gone contrasts with visible"),
        r("causes", "attention", "gone can pull attention"),
        r("linked_to", "caregiver gone", "gone is linked to caregiver gone"),
    ],
    "back again": [
        r("caused_by", "appears", "back again can be caused by appears"),
        r("contrasts_with", "gone", "back again contrasts with gone"),
        r("causes", "interest", "back again can cause interest", 0.75, "positive"),
        r("causes", "relief", "back again can cause relief", 0.7, "positive"),
    ],
    "safe touch": [
        r("linked_to", "caregiver", "safe touch is linked to caregiver"),
        r("contrasts_with", "pain", "safe touch contrasts with pain"),
        r("causes", "comfort", "safe touch can cause comfort", 0.85, "positive"),
        r("causes", "touch pleasure", "safe touch can cause touch pleasure", 0.75, "positive"),
    ],
}


def add_unique_relations(item: dict[str, Any], additions: list[dict[str, Any]]) -> None:
    seen = {(rel["type"], rel["target"], rel["text"]) for rel in item["relations"]}
    for rel in additions:
        key = (rel["type"], rel["target"], rel["text"])
        if key not in seen:
            item["relations"].append(rel)
            seen.add(key)


def dedupe_relations(item: dict[str, Any]) -> None:
    seen = set()
    deduped = []
    for rel in item["relations"]:
        key = (rel["type"], rel["target"], rel["text"])
        if key not in seen:
            deduped.append(rel)
            seen.add(key)
    item["relations"] = deduped


def normalize_relation(rel: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(rel)
    normalized["type"] = RELATION_TYPE_MAP.get(normalized["type"], normalized["type"])
    normalized["target"] = RELATION_TARGET_MAP.get(normalized["target"], normalized["target"])
    return normalized


def enrich_sparse_relation_bundle(item: dict[str, Any]) -> None:
    if len(item["relations"]) >= 2:
        return
    category = item["category"]
    if category == "core_relation":
        add_unique_relations(item, [r("linked_to", "relation", f"{item['word']} is part of the root relation system")])
    elif category == "body_action_control":
        add_unique_relations(item, [r("linked_to", "body", f"{item['word']} is linked to body action")])
    elif category == "body_state_valence":
        add_unique_relations(item, [r("linked_to", "body", f"{item['word']} is felt through body")])
    elif category == "space_motion_physics":
        add_unique_relations(item, [r("linked_to", "state", f"{item['word']} is a physical state or event")])
    elif category == "object_property":
        add_unique_relations(item, [r("describes", "state", f"{item['word']} describes state")])
    elif category == "common_object":
        add_unique_relations(item, [
            r("has_property", "see", f"{item['word']} can be seen"),
            r("has_property", "touch", f"{item['word']} can be touched"),
        ])
    elif category == "caregiver_social":
        add_unique_relations(item, [r("linked_to", "caregiver", f"{item['word']} is linked to caregiver world")])


def sort_by_prerequisites(concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    word_set = {item["word"] for item in concepts}
    remaining = list(concepts)
    ordered: list[dict[str, Any]] = []
    placed: set[str] = set()
    while remaining:
        ready = [
            item for item in remaining
            if all(prereq not in word_set or prereq in placed for prereq in item["prerequisites"])
        ]
        if not ready:
            ordered.extend(remaining)
            break
        ready_ids = {id(item) for item in ready}
        ordered.extend(ready)
        placed.update(item["word"] for item in ready)
        remaining = [item for item in remaining if id(item) not in ready_ids]
    return ordered


BUILDERS = [
    build_core_relation,
    build_body_part,
    build_body_action_control,
    build_sensory_input,
    build_body_state_valence,
    build_space_motion_physics,
    build_object_property,
    build_common_object,
    build_caregiver_social,
    build_routine_event,
    build_sound_language_precursor,
    build_learning_memory,
]


def build_concepts() -> list[dict[str, Any]]:
    concepts: list[dict[str, Any]] = []
    for builder in BUILDERS:
        concepts.extend(builder())
    for item in concepts:
        if item["word"] in INTERNAL_CONCEPTS:
            item["status"] = "internal"
        elif item["word"] in LATENT_CONCEPTS:
            item["status"] = "latent"
        elif item["word"] in EMERGING_CONCEPTS:
            item["status"] = "emerging"
        add_unique_relations(item, HUB_RELATIONS.get(item["word"], []))
        item["relations"] = [normalize_relation(rel) for rel in item["relations"]]
        dedupe_relations(item)
        enrich_sparse_relation_bundle(item)
        item["relations"] = [normalize_relation(rel) for rel in item["relations"]]
        dedupe_relations(item)
    concepts = sort_by_prerequisites(concepts)
    for index, item in enumerate(concepts):
        item["index"] = index
    return concepts


def validate(concepts: list[dict[str, Any]]) -> dict[str, Any]:
    words = [item["word"] for item in concepts]
    word_set = set(words)
    index_by_word = {item["word"]: index for index, item in enumerate(concepts)}
    duplicate_words = sorted([word for word, count in Counter(words).items() if count > 1])
    category_counts = Counter(item["category"] for item in concepts)
    missing_categories = {category: expected for category, expected in TARGET_CATEGORY_COUNTS.items() if category_counts.get(category) != expected}
    missing_prerequisites = []
    forward_prerequisites = []
    unknown_relation_targets = []
    unknown_relation_types = []
    empty_relations = []
    allowed_anchor_prerequisites = set(EXTERNAL_ANCHORS)
    for item in concepts:
        if not item["relations"]:
            empty_relations.append(item["word"])
        for prereq in item["prerequisites"]:
            if prereq not in word_set and prereq not in allowed_anchor_prerequisites:
                missing_prerequisites.append({"word": item["word"], "missing": prereq})
            if prereq in index_by_word and index_by_word[prereq] > index_by_word[item["word"]]:
                forward_prerequisites.append({"word": item["word"], "prerequisite": prereq})
        for relation in item["relations"]:
            if relation["type"] not in ALLOWED_RELATION_TYPES:
                unknown_relation_types.append({"word": item["word"], "type": relation["type"]})
            if relation["target"] not in word_set and relation["target"] not in EXTERNAL_ANCHORS:
                unknown_relation_targets.append({"word": item["word"], "target": relation["target"]})
    return {
        "expected_total": 500,
        "actual_total": len(concepts),
        "category_counts": dict(category_counts),
        "category_count_mismatches": missing_categories,
        "duplicate_words": duplicate_words,
        "missing_prerequisites": missing_prerequisites,
        "forward_prerequisites": forward_prerequisites,
        "unknown_relation_types": unknown_relation_types,
        "unknown_relation_targets": unknown_relation_targets,
        "empty_relation_bundles": empty_relations,
        "passes": (
            len(concepts) == 500
            and not duplicate_words
            and not missing_categories
            and not missing_prerequisites
            and not forward_prerequisites
            and not unknown_relation_types
            and not unknown_relation_targets
            and not empty_relations
        ),
    }


def curriculum_rows(concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in concepts:
        prereq = ", ".join(item["prerequisites"][:4]) if item["prerequisites"] else "root world"
        rows.append({
            "id": f"{EXPERIMENT_ID}.card.{item['word'].replace(' ', '_')}",
            "concept_id": item["id"],
            "task_type": "concept_card",
            "input": f"Word: {item['word']}\nAge: 6 months\nKnown handles: {prereq}\nQuestion: What does {item['word']} mean in the 6-month root world?\nAnswer:",
            "target": f"answer: {item['summary']}.\nreason: {item['word']} belongs to {item['category']}.",
            "metadata": {"category": item["category"], "domains": item["domains"], "relations": item["relations"]},
        })
        rows.append({
            "id": f"{EXPERIMENT_ID}.prose.{item['word'].replace(' ', '_')}",
            "concept_id": item["id"],
            "task_type": "concept_prose",
            "input": "",
            "target": f"{item['word']} means {item['summary']} in the 6-month root world.",
            "metadata": {"category": item["category"], "domains": item["domains"], "relations": item["relations"]},
        })
        for rel_index, relation in enumerate(item["relations"]):
            rows.append({
                "id": f"{EXPERIMENT_ID}.relation.{item['word'].replace(' ', '_')}.{rel_index:02d}",
                "concept_id": item["id"],
                "task_type": "relation_fact",
                "input": f"Word: {item['word']}\nQuestion: What relation connects {item['word']} and {relation['target']}?\nAnswer:",
                "target": f"answer: {relation['text']}.\nreason: relation type is {relation['type']}.",
                "metadata": {"category": item["category"], "domains": item["domains"], "relation": relation},
            })
            if item["status"] != "latent":
                scene = scene_for_relation(item, relation)
                rows.append({
                    "id": f"{EXPERIMENT_ID}.scene.{item['word'].replace(' ', '_')}.{rel_index:02d}",
                    "concept_id": item["id"],
                    "task_type": "scene_relation",
                    "input": f"{scene}\nQuestion: What relation is shown?\nAnswer:",
                    "target": f"answer: {relation['text']}.\nreason: {item['word']} {relation['type']} {relation['target']}.",
                    "metadata": {
                        "category": item["category"],
                        "status": item["status"],
                        "domains": item["domains"],
                        "relation": relation,
                    },
                })
    return rows


def scene_for_relation(item: dict[str, Any], relation: dict[str, Any]) -> str:
    word = item["word"]
    target = relation["target"]
    rel_type = relation["type"]
    valence = relation.get("valence", "neutral")
    if rel_type == "prevents":
        return f"Scene: The baby tries {target}. {word} is present. {target} does not happen."
    if rel_type == "enables":
        return f"Scene: {word} is present. The baby tries {target}. {target} can happen."
    if rel_type == "causes":
        return f"Scene: {word} happens. After that, {target} happens."
    if rel_type == "caused_by":
        return f"Scene: {target} happens first. After that, {word} happens."
    if rel_type == "part_of":
        return f"Scene: The baby feels the body. {word} belongs with {target}."
    if rel_type == "has_part":
        return f"Scene: The baby attends to {word}. {target} is part of it."
    if rel_type == "comes_through":
        return f"Scene: There is {word}. The baby gets it through {target}."
    if rel_type == "contrasts_with":
        return f"Scene: One moment shows {word}. Another moment shows {target}. They are not the same."
    if rel_type == "uses":
        return f"Scene: The baby does {word}. The baby uses {target}."
    if rel_type == "signals":
        return f"Scene: {word} happens. It tells that {target} may be needed."
    if rel_type == "updates":
        return f"Scene: {word} happens again. The link to {target} changes."
    if rel_type == "supports":
        return f"Scene: {word} is present. It helps {target}."
    if rel_type == "has_property":
        return f"Scene: The baby attends to {word}. It can have relation with {target}."
    if rel_type == "changes":
        return f"Scene: {word} happens. The state of {target} changes."
    if rel_type == "linked_to" and valence == "positive":
        return f"Scene: {word} is present with {target}. The baby settles or smiles."
    if rel_type == "linked_to" and valence == "negative":
        return f"Scene: {word} is present with {target}. The baby fusses or cries."
    return f"Scene: The baby attends to {word}. {word} is linked with {target}."


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(WORD_RE.findall(((row.get("input") or "") + " " + (row.get("target") or "")).lower()))
    return {"unique_alpha_words": len(counter), "top_words": counter.most_common(30)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"{args.output_dir} exists and is not empty; pass --overwrite")
    if args.output_dir.exists() and args.overwrite:
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    concepts = build_concepts()
    validation = validate(concepts)
    if not validation["passes"]:
        raise SystemExit(json.dumps(validation, indent=2, sort_keys=True))

    seed = {
        "schema_version": SCHEMA_VERSION,
        "graph_id": SEED_ID,
        "title": "6-Month Root World 500",
        "description": "Exactly 500 concept handles for the 6-month embodied root world.",
        "age_level": "age_6mo",
        "target_count": 500,
        "category_targets": TARGET_CATEGORY_COUNTS,
        "concepts": concepts,
        "validation": validation,
        "counts": {
            "concepts": len(concepts),
            "relations": sum(len(item["relations"]) for item in concepts),
            "by_category": Counter(item["category"] for item in concepts),
            "by_domain": Counter(domain for item in concepts for domain in item["domains"]),
            "by_kind": Counter(item["kind"] for item in concepts),
        },
    }
    write_json(args.seed_path, seed)

    rows = curriculum_rows(concepts)
    write_jsonl(args.output_dir / "curriculum.jsonl", rows)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "seed": str(args.seed_path),
        "curriculum": str(args.output_dir / "curriculum.jsonl"),
        "counts": seed["counts"],
        "curriculum_rows": len(rows),
        "vocabulary": vocab_stats(rows),
        "validation": validation,
        "outputs": {
            str(args.seed_path): {"sha256": sha256_file(args.seed_path)},
            str(args.output_dir / "curriculum.jsonl"): {"sha256": sha256_file(args.output_dir / "curriculum.jsonl")},
        },
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({"seed": str(args.seed_path), "output_dir": str(args.output_dir), "counts": seed["counts"], "curriculum_rows": len(rows)}, indent=2, default=dict))


if __name__ == "__main__":
    main()
