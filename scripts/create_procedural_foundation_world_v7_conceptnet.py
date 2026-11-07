#!/usr/bin/env python3
"""Create V7 staged concept lexicon and curriculum.

V7 is a reusable "our ConceptNet" layer. It is not a model run.

The source of truth is a staged lexicon:

- each word is a handle to a relation bundle
- stages define when the word can be introduced
- later stages can use earlier-stage words as prerequisites
- the model-visible data is ordinary prose/QA rendered from the lexicon

This is intentionally curated instead of importing ConceptNet raw. ConceptNet
is broad and useful as a mining source, but the project needs a developmental
relation order and cleaner word senses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from output_state import retire_output_dir  # noqa: E402


EXPERIMENT_ID = "procedural_foundation_v7_conceptnet"
SEED_ID = "adi_conceptnet_v7"
SCHEMA_VERSION = "0.1.0"
DEFAULT_OUTPUT_DIR = Path("data/developmental_graph/experiments") / EXPERIMENT_ID
DEFAULT_SEED_PATH = Path("data/developmental_graph/seeds") / f"{SEED_ID}.json"
SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = ("concept_dense_qa", "concept_prose", "concept_mixed")
WORD_RE = re.compile(r"[a-z]+")


STAGES = [
    {
        "id": "age_6mo",
        "order": 0,
        "label": "6 Months",
        "purpose": "Direct embodied roots: body, touch, pain, comfort, near/far, caregiver, basic object handles.",
    },
    {
        "id": "age_1yo",
        "order": 1,
        "label": "1 Year",
        "purpose": "Object permanence, simple action, containment, food/water, early words, simple social response.",
    },
    {
        "id": "age_3yo",
        "order": 2,
        "label": "3 Years",
        "purpose": "Richer objects, language, play, animals, places, before/after, simple cause and category.",
    },
    {
        "id": "age_5yo",
        "order": 3,
        "label": "5 Years",
        "purpose": "School-ready abstractions: number, measure, story, geography/history seeds, rules, truth, society.",
    },
]
STAGE_BY_ID = {stage["id"]: stage for stage in STAGES}


def rel(kind: str, target: str, text: str, strength: float = 0.75, polarity: str = "positive") -> dict[str, Any]:
    return {
        "type": kind,
        "target": target,
        "text": text,
        "strength": strength,
        "polarity": polarity,
    }


def entry(
    word: str,
    stage: str,
    kind: str,
    summary: str,
    relations: list[dict[str, Any]],
    *,
    prerequisites: list[str] | None = None,
    aliases: list[str] | None = None,
    contrast_with: list[str] | None = None,
    domains: list[str] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    inferred_domains = domains or infer_domains(word, kind)
    return {
        "id": f"concept.{word.replace(' ', '_')}",
        "word": word,
        "stage": stage,
        "stage_order": STAGE_BY_ID[stage]["order"],
        "domains": inferred_domains,
        "kind": kind,
        "summary": summary,
        "prerequisites": prerequisites or [],
        "aliases": aliases or [],
        "contrast_with": contrast_with or [],
        "relations": relations,
        "notes": notes,
    }


def infer_domains(word: str, kind: str) -> list[str]:
    domain_map = {
        "root": "root",
        "answer": "root",
        "quantity": "math",
        "symbol": "language",
        "body": "body",
        "body_part": "body",
        "body_relation": "self",
        "relation": "root",
        "sense_action": "body",
        "sense": "body",
        "signal": "sense",
        "space": "space",
        "valence": "emotion",
        "kind": "category",
        "object": "physical",
        "object_part": "physical",
        "tool": "physical",
        "state": "physical",
        "action": "physical",
        "event": "time_change",
        "property": "property",
        "property_kind": "property",
        "role": "social",
        "animal": "living",
        "living thing": "living",
        "need_object": "living",
        "need_event": "living",
        "social_action": "social",
        "emotion": "emotion",
        "emotion_relation": "emotion",
        "language_action": "language",
        "language_event": "language",
        "language_structure": "language",
        "social_role": "social",
        "learning_event": "learning",
        "place": "place",
        "vehicle": "physical",
        "nature": "nature",
        "plant": "living",
        "nature_event": "nature",
        "time": "time",
        "time_relation": "time",
        "mental_action": "learning",
        "domain": "domain",
        "social_group": "social",
        "plural_kind": "category",
        "place_relation": "place",
        "root_place": "place",
        "physical_signal": "sense",
        "physical_state": "physical",
        "physical_property": "physical",
        "object_kind": "physical",
        "abstract": "abstract",
        "abstract_action": "abstract",
        "abstract_relation": "abstract",
        "abstract_social": "social",
        "social_system": "social",
        "social_rule": "social",
    }
    domains = [domain_map.get(kind, "misc")]
    if word in {"history"}:
        domains.append("history")
    if word in {"geography", "map", "country", "city", "river", "mountain"}:
        domains.append("geography")
    if word in {"math", "number", "amount", "measure", "one", "two", "more", "less"}:
        domains.append("math")
    if word in {"science", "cause", "effect", "truth"}:
        domains.append("science")
    return sorted(set(domains))


def build_entries() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    e = rows.append

    # Age 6mo: root handles plus direct embodied relations.
    e(entry("thing", "age_6mo", "root", "anything that can have relations", [rel("is_a", "root", "thing is the most general handle")]))
    e(entry("kind", "age_6mo", "root", "a group of things with shared relations", [rel("is_a", "relation", "kind groups things by shared relations")], prerequisites=["thing"]))
    e(entry("part", "age_6mo", "root", "a thing within a larger thing", [rel("part_of", "whole", "part belongs to a whole")], prerequisites=["thing", "whole"]))
    e(entry("whole", "age_6mo", "root", "a thing made of parts", [rel("has_part", "part", "whole can have parts")], prerequisites=["thing", "part"]))
    e(entry("relation", "age_6mo", "root", "a link between things", [rel("links", "thing", "relation links one thing to another")], prerequisites=["thing"]))
    e(entry("state", "age_6mo", "root", "how a thing is now", [rel("describes", "thing", "state describes a thing now")], prerequisites=["thing"]))
    e(entry("event", "age_6mo", "root", "something that happens", [rel("changes", "state", "event can change state")], prerequisites=["thing", "state"]))
    e(entry("same", "age_6mo", "root", "two handles point to one thing or matching relation", [rel("contrasts_with", "different", "same contrasts with different")], prerequisites=["thing"], contrast_with=["different"]))
    e(entry("different", "age_6mo", "root", "two handles do not point to the same thing or relation", [rel("contrasts_with", "same", "different contrasts with same")], prerequisites=["thing"], contrast_with=["same"]))
    e(entry("yes", "age_6mo", "answer", "answer that relation holds", [rel("confirms", "relation", "yes means the asked relation holds")], prerequisites=["relation"]))
    e(entry("no", "age_6mo", "answer", "answer that relation does not hold", [rel("denies", "relation", "no means the asked relation does not hold")], prerequisites=["relation"], contrast_with=["yes"]))
    e(entry("more", "age_6mo", "quantity", "greater amount", [rel("contrasts_with", "less", "more contrasts with less")], prerequisites=["thing"], contrast_with=["less"]))
    e(entry("less", "age_6mo", "quantity", "smaller amount", [rel("contrasts_with", "more", "less contrasts with more")], prerequisites=["thing"], contrast_with=["more"]))
    e(entry("one", "age_6mo", "quantity", "single thing", [rel("is_a", "number", "one is a number amount")], prerequisites=["thing"]))
    e(entry("two", "age_6mo", "quantity", "one and one", [rel("is_more_than", "one", "two is more than one")], prerequisites=["one", "more"]))
    e(entry("name", "age_6mo", "symbol", "stable handle used for a thing", [rel("points_to", "thing", "name points to a thing")], prerequisites=["thing", "same", "different"]))

    # Age 6mo continued: body, sense, space, proto-self.
    for word, kind, summary, prereq, rels in [
        ("body", "body", "controlled living whole", ["thing", "whole"], [rel("has_part", "hand", "body has hand"), rel("can_feel", "pain", "body can feel pain")]),
        ("hand", "body_part", "body part for reach, hold, touch", ["body", "part"], [rel("part_of", "body", "hand is part of body"), rel("can_do", "touch", "hand can touch"), rel("can_do", "hold", "hand can hold")]),
        ("eye", "body_part", "body part for seeing", ["body", "part"], [rel("part_of", "body", "eye is part of body"), rel("uses", "see", "eye is used to see")]),
        ("ear", "body_part", "body part for hearing", ["body", "part"], [rel("part_of", "body", "ear is part of body"), rel("uses", "hear", "ear is used to hear")]),
        ("mouth", "body_part", "body part for eat, taste, say", ["body", "part"], [rel("part_of", "body", "mouth is part of body"), rel("can_do", "eat", "mouth can eat"), rel("can_do", "say", "mouth can say words")]),
        ("skin", "body_part", "body surface that feels touch and pain", ["body", "part"], [rel("part_of", "body", "skin is part of body"), rel("can_feel", "touch", "skin feels touch"), rel("can_feel", "pain", "skin feels pain")]),
        ("self", "body_relation", "what is controlled and directly felt", ["body", "hand", "control"], [rel("controlled_by", "self", "self controls body parts"), rel("feels", "body", "self directly feels body")]),
        ("control", "relation", "can make something move or stop", ["relation", "event"], [rel("enables", "move", "control enables movement")]),
        ("touch", "sense_action", "contact between body and thing", ["hand", "skin", "thing"], [rel("needs", "near", "touch needs near contact"), rel("can_cause", "feel", "touch can cause feeling")]),
        ("feel", "sense", "body input from touch or inside body", ["body", "state"], [rel("comes_from", "body", "feel comes from body")]),
        ("see", "sense", "eye input from visible thing", ["eye", "thing"], [rel("uses", "eye", "see uses eye")]),
        ("hear", "sense", "ear input from sound", ["ear", "sound"], [rel("uses", "ear", "hear uses ear")]),
        ("sound", "signal", "thing that can be heard", ["hear", "event"], [rel("can_be", "heard", "sound can be heard")]),
        ("near", "space", "small distance", ["thing"], [rel("enables", "touch", "near enables touch")],),
        ("far", "space", "large distance", ["thing"], [rel("prevents", "touch", "far prevents touch")]),
        ("up", "space", "higher place", ["thing"], [rel("contrasts_with", "down", "up contrasts with down")]),
        ("down", "space", "lower place", ["thing"], [rel("contrasts_with", "up", "down contrasts with up")]),
        ("inside", "space", "within a boundary", ["thing"], [rel("needs", "container", "inside needs a container")]),
        ("outside", "space", "not within a boundary", ["inside"], [rel("contrasts_with", "inside", "outside contrasts with inside")]),
        ("on", "space", "supported by a surface", ["thing"], [rel("needs", "surface", "on needs surface support")]),
        ("under", "space", "below another thing", ["up", "down"], [rel("is_below", "thing", "under means below a thing")]),
        ("pain", "valence", "bad body feeling", ["body", "feel"], [rel("causes", "bad", "pain causes bad feeling"), rel("can_signal", "danger", "pain can signal danger")]),
        ("comfort", "valence", "body and situation feel okay", ["body", "feel"], [rel("can_cause", "good", "comfort can cause good feeling"), rel("reduces", "pain", "comfort reduces pain")]),
    ]:
        e(entry(word, "age_6mo", kind, summary, rels, prerequisites=prereq))

    # Age 1yo: physical world and common object handles.
    stage2 = [
        ("object", "kind", "visible or touchable thing", ["thing", "touch"], [rel("is_a", "thing", "object is a thing"), rel("can_be", "touched", "object can be touched")]),
        ("toy", "kind", "object used for play", ["object"], [rel("is_a", "object", "toy is an object"), rel("used_for", "play", "toy is used for play")]),
        ("ball", "object", "round toy that can roll and bounce", ["toy", "round", "move"], [rel("is_a", "toy", "ball is a toy"), rel("has_property", "round", "ball is usually round"), rel("can_do", "roll", "ball can roll"), rel("can_do", "bounce", "ball can bounce")]),
        ("cube", "object", "object with flat sides", ["object", "shape"], [rel("has_property", "flat", "cube has flat sides"), rel("does_not_easily", "roll", "cube does not roll easily", 0.7, "negative")], ["block"]),
        ("cup", "object", "container for drink", ["object", "inside"], [rel("is_a", "container", "cup is a container"), rel("used_for", "drink", "cup is used for drink")]),
        ("bottle", "object", "container for water or milk", ["container", "inside"], [rel("is_a", "container", "bottle is a container"), rel("can_hold", "water", "bottle can hold water")]),
        ("box", "object", "container that can open and close", ["container", "inside"], [rel("is_a", "container", "box is a container"), rel("can_have_state", "open", "box can be open"), rel("can_have_state", "closed", "box can be closed")]),
        ("bag", "object", "soft container", ["container", "soft"], [rel("is_a", "container", "bag is a container"), rel("has_property", "soft", "bag is often soft")]),
        ("book", "object", "object with pages and marks", ["object", "flat"], [rel("has_part", "page", "book has pages"), rel("can_have", "mark", "book can have marks and later words")]),
        ("page", "object_part", "flat part of a book or paper", ["part", "book"], [rel("part_of", "book", "page is part of book")]),
        ("paper", "object", "thin flat object that can hold marks", ["object", "flat"], [rel("has_property", "flat", "paper is flat"), rel("can_have", "word", "paper can have words")]),
        ("pen", "tool", "tool for making marks", ["object", "hand"], [rel("used_for", "write", "pen is used to write")]),
        ("spoon", "tool", "tool for eating or serving", ["object", "hand"], [rel("used_for", "mouth", "spoon helps move food to mouth")]),
        ("plate", "object", "flat object that can hold things for mouth", ["object", "flat"], [rel("can_hold", "object", "plate can hold objects like food")]),
        ("blanket", "object", "soft object for warmth and comfort", ["object", "soft", "comfort"], [rel("has_property", "soft", "blanket is soft"), rel("can_make", "comfort", "blanket can give comfort")]),
        ("pillow", "object", "soft object for head and rest", ["object", "soft", "comfort"], [rel("has_property", "soft", "pillow is soft"), rel("can_make", "comfort", "pillow can give comfort")]),
        ("chair", "object", "object used to sit", ["object", "support"], [rel("used_for", "sit", "chair is used to sit"), rel("can_support", "person", "chair can support person")]),
        ("table", "object", "high surface for objects", ["surface", "on"], [rel("is_a", "surface", "table is a surface"), rel("can_support", "object", "table can support objects")]),
        ("floor", "object", "low surface under body and objects", ["surface", "down"], [rel("is_a", "surface", "floor is a surface"), rel("has_property", "down", "floor is down")]),
        ("door", "object", "thing that opens or closes a way through", ["open", "closed", "inside"], [rel("can_have_state", "open", "door can be open"), rel("can_have_state", "closed", "door can be closed")]),
        ("container", "kind", "object that can have things inside", ["object", "inside"], [rel("can_hold", "object", "container can hold object inside")]),
        ("surface", "kind", "object face that can support contact", ["object", "touch"], [rel("can_support", "object", "surface can support object")]),
        ("open", "state", "allows entry or movement", ["state", "inside"], [rel("enables", "reach", "open enables reach inside")], None, ["closed"]),
        ("closed", "state", "blocks entry or movement", ["state", "inside"], [rel("prevents", "reach", "closed prevents reach inside")], None, ["open"]),
        ("move", "action", "change place", ["event", "state"], [rel("changes", "place", "move changes place")]),
        ("reach", "action", "move hand toward thing", ["hand", "near"], [rel("can_enable", "touch", "reach can enable touch")]),
        ("hold", "action", "keep thing in hand", ["hand", "object"], [rel("prevents", "fall", "hold can prevent fall")]),
        ("drop", "action", "let held thing go", ["hold", "down"], [rel("can_cause", "fall", "drop can cause fall")]),
        ("fall", "event", "move down when support is gone", ["down", "support"], [rel("needs_missing", "support", "fall happens when support is gone")]),
        ("push", "action", "move thing away by force", ["hand", "move"], [rel("can_cause", "move", "push can make object move")]),
        ("pull", "action", "move thing toward self by force", ["hand", "move"], [rel("can_cause", "move", "pull can make object move")]),
        ("roll", "action", "round thing moves by turning", ["round", "move"], [rel("enabled_by", "round", "round shape enables roll")]),
        ("bounce", "action", "hit surface and come back", ["move", "surface"], [rel("needs", "surface", "bounce needs surface contact")]),
        ("break", "event", "stop working or split apart", ["event", "object"], [rel("causes", "bad", "break often causes bad state")]),
        ("fix", "action", "make broken thing work again", ["break", "state"], [rel("reduces", "broken", "fix reduces broken state")]),
        ("clean", "action", "remove dirt", ["object", "state"], [rel("changes", "dirty", "clean changes dirty state")]),
        ("round", "property", "curved shape", ["state", "shape"], [rel("enables", "roll", "round enables roll")]),
        ("flat", "property", "not curved surface", ["shape", "surface"], [rel("supports", "on", "flat can support things")]),
        ("soft", "property", "changes shape easily", ["touch", "feel"], [rel("can_make", "comfort", "soft can make comfort")]),
        ("hard", "property", "does not change shape easily", ["touch", "feel"], [rel("contrasts_with", "soft", "hard contrasts with soft")]),
        ("hot", "property", "high temperature", ["touch", "pain"], [rel("can_cause", "pain", "hot can cause pain")]),
        ("cold", "property", "low temperature", ["touch", "feel"], [rel("contrasts_with", "hot", "cold contrasts with hot")]),
        ("sharp", "property", "can cut or hurt", ["touch", "pain"], [rel("can_cause", "pain", "sharp can cause pain")]),
        ("safe", "property", "unlikely to hurt", ["pain", "danger"], [rel("prevents", "pain", "safe lowers chance of pain")]),
        ("danger", "property", "may hurt or break", ["pain", "state"], [rel("can_cause", "pain", "danger can cause pain")]),
        ("big", "property", "large size", ["more"], [rel("is_more_than", "small", "big is more size than small")]),
        ("small", "property", "small size", ["less"], [rel("is_less_than", "big", "small is less size than big")]),
        ("heavy", "property", "hard to move", ["move"], [rel("prevents", "move", "heavy can prevent move")]),
        ("light weight", "property", "easy to move", ["move"], [rel("enables", "move", "light weight can enable move")]),
        ("shape", "property_kind", "form of object", ["state", "object"], [rel("describes", "object", "shape describes object")]),
        ("support", "relation", "holds thing up", ["on", "fall"], [rel("prevents", "fall", "support prevents fall")]),
    ]
    for item in stage2:
        word, kind, summary, prereq, rels = item[:5]
        aliases = item[5] if len(item) > 5 else None
        contrast = item[6] if len(item) > 6 else None
        e(entry(word, "age_1yo", kind, summary, rels, prerequisites=prereq, aliases=aliases, contrast_with=contrast))

    # Age 3yo: living, social, and language. These use object/body/space words.
    stage3 = [
        ("living thing", "kind", "thing that needs and grows", ["thing", "need"], [rel("needs", "food", "living thing needs food"), rel("needs", "water", "living thing needs water"), rel("needs", "air", "living thing needs air")]),
        ("person", "kind", "living thing with body, words, social relations", ["living thing", "body", "word"], [rel("is_a", "living thing", "person is living thing"), rel("can_use", "word", "person can use words")]),
        ("child", "kind", "young person", ["person"], [rel("is_a", "person", "child is a person"), rel("needs", "care", "child needs care")]),
        ("adult", "kind", "grown person", ["person"], [rel("is_a", "person", "adult is a person"), rel("can_give", "care", "adult can give care")]),
        ("mom", "role", "familiar caregiver", ["adult", "care"], [rel("is_a", "caregiver", "mom is caregiver"), rel("can_give", "comfort", "mom can give comfort")]),
        ("dad", "role", "familiar caregiver", ["adult", "care"], [rel("is_a", "caregiver", "dad is caregiver"), rel("can_give", "comfort", "dad can give comfort")]),
        ("caregiver", "role", "person who protects, feeds, comforts", ["person", "care"], [rel("can_do", "help", "caregiver can help"), rel("reduces", "pain", "caregiver can reduce pain")]),
        ("friend", "role", "person who plays, helps, shares", ["person", "play"], [rel("can_do", "play", "friend can play"), rel("can_do", "share", "friend can share")]),
        ("animal", "kind", "living thing that can move and feel", ["living thing", "move", "feel"], [rel("is_a", "living thing", "animal is living thing"), rel("can_do", "move", "animal can move"), rel("can_feel", "pain", "animal can feel pain")]),
        ("dog", "animal", "animal often near people", ["animal", "pet"], [rel("is_a", "animal", "dog is animal"), rel("can_be", "pet", "dog can be pet")]),
        ("puppy", "animal", "young dog", ["dog", "young"], [rel("is_a", "dog", "puppy is dog"), rel("is_a", "young animal", "puppy is young animal")]),
        ("cat", "animal", "small animal often near people", ["animal", "pet"], [rel("is_a", "animal", "cat is animal"), rel("can_be", "pet", "cat can be pet")]),
        ("bird", "animal", "animal with wings", ["animal"], [rel("is_a", "animal", "bird is animal"), rel("has_part", "wing", "bird has wings")]),
        ("plant", "living thing", "living thing that grows in place", ["living thing"], [rel("is_a", "living thing", "plant is living thing"), rel("needs", "water", "plant needs water")]),
        ("food", "need_object", "thing living things eat", ["living thing", "need"], [rel("satisfies", "food need", "food satisfies food need")]),
        ("water", "need_object", "thing living things drink", ["living thing", "need"], [rel("satisfies", "water need", "water satisfies water need")]),
        ("air", "need_object", "thing needed for breathing", ["living thing", "need"], [rel("satisfies", "air need", "air satisfies air need")]),
        ("sleep", "need_event", "rest needed by body", ["body", "need"], [rel("satisfies", "sleep need", "sleep satisfies rest need")]),
        ("need", "relation", "required for living or comfort", ["living thing", "bad"], [rel("missing_causes", "bad", "missing need can cause bad state")]),
        ("care", "social_action", "help a living thing stay okay", ["help", "living thing"], [rel("reduces", "pain", "care can reduce pain"), rel("causes", "comfort", "care can cause comfort")]),
        ("help", "social_action", "reduce problem or pain", ["person", "bad"], [rel("reduces", "bad", "help reduces bad state"), rel("can_cause", "good", "help can cause good")]),
        ("hurt", "social_action", "cause pain or damage", ["pain", "person"], [rel("causes", "pain", "hurt causes pain"), rel("causes", "sad", "hurt can cause sad")]),
        ("give", "social_action", "move object to another person", ["person", "object"], [rel("moves", "object", "give moves object to person")]),
        ("take", "social_action", "get object from person or place", ["person", "object"], [rel("moves", "object", "take moves object from place or person")]),
        ("share", "social_action", "let another person use too", ["give", "friend"], [rel("can_cause", "happy", "share can cause happy")]),
        ("play", "social_action", "pleasant action with toy, person, or pet", ["toy", "friend"], [rel("uses", "toy", "play can use toy"), rel("can_cause", "happy", "play can cause happy")]),
        ("happy", "emotion", "good feeling", ["good", "comfort"], [rel("caused_by", "comfort", "comfort can cause happy"), rel("caused_by", "new link", "new link can cause happy")]),
        ("sad", "emotion", "bad feeling from pain, loss, or broken relation", ["bad", "pain"], [rel("caused_by", "pain", "pain can cause sad"), rel("caused_by", "loss", "loss can cause sad")]),
        ("afraid", "emotion", "bad feeling from possible danger", ["danger", "bad"], [rel("caused_by", "danger", "danger can cause afraid")]),
        ("angry", "emotion", "bad feeling when want is blocked", ["want", "bad"], [rel("caused_by", "blocked want", "blocked want can cause angry")]),
        ("want", "emotion_relation", "pull toward object or state", ["object", "state"], [rel("points_to", "object", "want points toward object or state")]),
        ("good", "valence", "toward comfort, safety, happy", ["comfort"], [rel("can_cause", "happy", "good can cause happy")]),
        ("bad", "valence", "toward pain, danger, loss", ["pain"], [rel("can_cause", "sad", "bad can cause sad")]),
        ("word", "symbol", "sound or text that can name", ["sound", "name"], [rel("can_name", "thing", "word can name thing")]),
        ("say", "language_action", "make word sound by mouth", ["mouth", "word"], [rel("creates", "sound", "say creates sound")]),
        ("hear word", "language_event", "hear a spoken word", ["hear", "word"], [rel("can_wake", "name", "hearing word can wake name relation")]),
        ("look", "action", "use eyes toward a thing", ["eye", "see"], [rel("uses", "eye", "look uses eyes")]),
        ("ask", "language_action", "use words to request answer or help", ["word", "answer"], [rel("expects", "answer", "ask expects answer")]),
        ("answer", "language_action", "words returned to a question", ["word", "ask"], [rel("responds_to", "ask", "answer responds to ask")]),
        ("tell", "language_action", "give words to another person", ["word", "person"], [rel("moves", "word", "tell moves word to person")]),
        ("story", "language_structure", "words about events", ["word", "event"], [rel("has", "event", "story has events")]),
        ("young", "property", "early in life", ["living thing"], [rel("contrasts_with", "adult", "young contrasts with adult")]),
        ("pet", "social_role", "animal near people and cared for", ["animal", "care"], [rel("is_a", "animal", "pet is animal"), rel("receives", "care", "pet receives care")]),
        ("wing", "body_part", "animal part for flying", ["animal", "part"], [rel("part_of", "bird", "wing is part of bird")]),
        ("loss", "event", "wanted relation breaks or thing is gone", ["want", "sad"], [rel("can_cause", "sad", "loss can cause sad")]),
        ("new link", "learning_event", "new relation is created", ["relation", "happy"], [rel("can_cause", "happy", "new link can cause happy"), rel("can_cause", "excited", "new link can cause excited")]),
        ("excited", "emotion", "strong happy feeling around new event", ["happy", "new link"], [rel("caused_by", "new link", "new link can cause excited")]),
    ]
    for word, kind, summary, prereq, rels in stage3:
        e(entry(word, "age_3yo", kind, summary, rels, prerequisites=prereq))

    # Age 5yo: everyday world, nature, geography, simple history.
    stage4 = [
        ("home", "place", "familiar place for family and care", ["place", "family"], [rel("contains", "person", "home can contain family"), rel("can_give", "comfort", "home can give comfort")]),
        ("room", "place", "part of a home or building", ["place", "part"], [rel("part_of", "home", "room can be part of home")]),
        ("kitchen", "place", "room for food and cooking", ["room", "food"], [rel("used_for", "food", "kitchen is used for food")]),
        ("bed", "object", "object used for sleep", ["sleep", "object"], [rel("used_for", "sleep", "bed is used for sleep")]),
        ("school", "place", "place where children learn", ["child", "learn"], [rel("used_for", "learn", "school is used for learning")]),
        ("teacher", "role", "person who helps child learn", ["person", "learn"], [rel("can_do", "teach", "teacher can teach")]),
        ("student", "role", "person who learns in school", ["person", "learn"], [rel("does", "learn", "student learns")]),
        ("road", "place", "path for people and vehicles", ["path", "move"], [rel("used_for", "move", "road is used for movement")]),
        ("car", "vehicle", "vehicle that moves people", ["object", "road"], [rel("used_for", "move", "car moves people")]),
        ("bus", "vehicle", "large vehicle for many people", ["car", "more"], [rel("is_a", "vehicle", "bus is vehicle"), rel("carries", "people", "bus carries many people")]),
        ("shop", "place", "place where people get things", ["place", "object"], [rel("used_for", "get thing", "shop is used to get things")]),
        ("farm", "place", "place where food is grown", ["place", "food", "plant"], [rel("used_for", "grow food", "farm grows food")]),
        ("village", "place", "small place where people live", ["place", "person"], [rel("contains", "home", "village contains homes")]),
        ("city", "place", "large place where many people live", ["place", "more"], [rel("contains", "road", "city contains roads"), rel("contains", "home", "city contains homes")]),
        ("country", "place", "large land group with people", ["place", "people"], [rel("contains", "city", "country contains cities"), rel("contains", "people", "country contains people")]),
        ("world", "place", "all places and living things together", ["place", "whole"], [rel("contains", "country", "world contains countries")]),
        ("river", "nature", "moving water in a path", ["water", "move"], [rel("is_a", "water", "river is water"), rel("can_flow", "place", "river flows through place")]),
        ("mountain", "nature", "high land", ["up", "place"], [rel("has_property", "up", "mountain is high")]),
        ("tree", "plant", "big plant with trunk and leaves", ["plant"], [rel("is_a", "plant", "tree is plant")]),
        ("flower", "plant", "plant part often seen and smelled", ["plant", "see"], [rel("is_a", "plant part", "flower is plant part")]),
        ("sun", "nature", "bright hot thing in sky", ["hot", "light"], [rel("gives", "light", "sun gives light"), rel("gives", "heat", "sun gives heat")]),
        ("rain", "nature_event", "water falls from sky", ["water", "fall"], [rel("is_a", "event", "rain is event"), rel("gives", "water", "rain gives water")]),
        ("day", "time", "time with light", ["event", "light"], [rel("has", "light", "day has light")]),
        ("night", "time", "time with dark", ["event", "dark"], [rel("contrasts_with", "day", "night contrasts with day")]),
        ("yesterday", "time", "day before today", ["before", "day"], [rel("is_before", "today", "yesterday is before today")]),
        ("today", "time", "current day", ["day"], [rel("is_now", "day", "today is current day")]),
        ("tomorrow", "time", "day after today", ["after", "day"], [rel("is_after", "today", "tomorrow is after today")]),
        ("before", "time_relation", "earlier than event", ["event"], [rel("orders", "event", "before orders events")]),
        ("after", "time_relation", "later than event", ["event"], [rel("orders", "event", "after orders events")]),
        ("learn", "action", "create or strengthen relation", ["new link", "relation"], [rel("creates", "relation", "learn creates relation")]),
        ("teach", "action", "help another person learn", ["learn", "help"], [rel("helps", "learn", "teach helps learning")]),
        ("remember", "mental_action", "keep relation available later", ["learn", "after"], [rel("keeps", "relation", "remember keeps relation")]),
        ("forget", "mental_action", "lose access to relation", ["remember", "loss"], [rel("can_cause", "loss", "forget can cause relation loss")]),
        ("past", "time", "events before now", ["before", "event"], [rel("contains", "event", "past contains earlier events")]),
        ("history", "domain", "remembered past of people and groups", ["past", "story", "person"], [rel("is_about", "past", "history is about past"), rel("has", "event", "history has events")]),
        ("map", "symbol", "picture of places and relations", ["place", "relation"], [rel("shows", "place", "map shows places")]),
        ("geography", "domain", "relations among places, land, water, people", ["place", "map"], [rel("is_about", "place", "geography is about places")]),
        ("family", "social_group", "people connected by care and relation", ["person", "care"], [rel("contains", "person", "family contains people"), rel("can_give", "care", "family can give care")]),
        ("group", "social_group", "many people linked by relation", ["person", "relation", "more"], [rel("contains", "person", "group contains people")]),
        ("people", "plural_kind", "more than one person", ["person", "more"], [rel("is_more_than", "person", "people means more than one person")]),
        ("path", "place_relation", "way from one place to another", ["place", "move"], [rel("enables", "move", "path enables movement")]),
        ("place", "root_place", "where a thing can be", ["thing", "state"], [rel("locates", "thing", "place locates thing")]),
        ("light", "physical_signal", "what makes seeing possible", ["see"], [rel("enables", "see", "light enables seeing")]),
        ("dark", "physical_state", "low light", ["light", "no"], [rel("prevents", "see", "dark can prevent seeing")]),
        ("heat", "physical_property", "hot energy felt by body", ["hot", "feel"], [rel("can_cause", "hot", "heat can cause hot state")]),
        ("vehicle", "object_kind", "object used to move people or things", ["object", "move"], [rel("used_for", "move", "vehicle is used for movement")]),
        ("buy", "social_action", "get thing by giving something accepted", ["give", "thing"], [rel("exchanges", "thing", "buy exchanges something accepted for a thing")]),
    ]
    for word, kind, summary, prereq, rels in stage4:
        e(entry(word, "age_5yo", kind, summary, rels, prerequisites=prereq))

    # Age 5yo continued: abstract domains and social systems.
    stage5 = [
        ("number", "abstract", "stable handle for amount", ["one", "two", "more"], [rel("measures", "amount", "number measures amount")]),
        ("amount", "abstract", "how much or how many", ["more", "less"], [rel("can_be", "more", "amount can be more"), rel("can_be", "less", "amount can be less")]),
        ("measure", "abstract_action", "compare amount, size, time, or weight", ["amount", "same", "different"], [rel("compares", "amount", "measure compares amount")]),
        ("time", "abstract", "ordering of events", ["before", "after", "event"], [rel("orders", "event", "time orders events")]),
        ("cause", "abstract_relation", "earlier state makes later state", ["before", "event"], [rel("makes", "effect", "cause makes effect")]),
        ("effect", "abstract_relation", "later state from cause", ["after", "event"], [rel("comes_from", "cause", "effect comes from cause")]),
        ("rule", "abstract_social", "relation that says what should happen", ["relation", "group"], [rel("guides", "action", "rule guides action")]),
        ("promise", "abstract_social", "word relation that creates expected future action", ["word", "after", "rule"], [rel("creates", "expectation", "promise creates expectation")]),
        ("money", "abstract_social", "shared token used to buy and sell", ["buy", "thing"], [rel("used_for", "buy", "money is used to buy")]),
        ("work", "social_action", "effort used to make value or help", ["event", "person"], [rel("can_create", "value", "work can create value")]),
        ("job", "social_role", "regular work relation", ["work", "person"], [rel("is_a", "relation", "job is a regular social relation"), rel("uses", "work", "job uses work")]),
        ("government", "social_system", "group role that makes and enforces rules", ["group", "rule", "country"], [rel("makes", "rule", "government makes rules")]),
        ("society", "social_system", "large group of people with shared rules and roles", ["people", "rule", "group"], [rel("contains", "people", "society contains people"), rel("has", "rule", "society has rules")]),
        ("law", "social_rule", "formal rule of society or government", ["rule", "government"], [rel("is_a", "rule", "law is rule")]),
        ("right", "abstract_social", "protected allowed relation", ["law", "person"], [rel("protects", "person", "right protects person relation")]),
        ("wrong", "abstract_social", "relation that breaks rule or causes harm", ["rule", "hurt"], [rel("contrasts_with", "right", "wrong contrasts with right")]),
        ("truth", "abstract", "words match relation or event", ["word", "same", "event"], [rel("means", "word matches relation", "truth means words match relation")]),
        ("lie", "abstract_social", "words intentionally do not match relation", ["word", "different", "truth"], [rel("contrasts_with", "truth", "lie contrasts with truth")]),
        ("reason", "abstract", "relation explaining why answer holds", ["cause", "answer"], [rel("explains", "answer", "reason explains answer")]),
        ("question", "language_structure", "words that ask for relation or answer", ["ask", "answer"], [rel("expects", "answer", "question expects answer")]),
        ("explain", "language_action", "give relation chain behind answer", ["reason", "tell"], [rel("gives", "reason", "explain gives reason")]),
        ("category", "abstract", "kind used for grouping", ["kind", "same", "different"], [rel("is_a", "kind", "category is kind")]),
        ("example", "abstract", "one thing inside a category", ["category", "one"], [rel("is_in", "category", "example is in category")]),
        ("idea", "abstract", "relation bundle held in mind", ["relation", "remember"], [rel("has", "relation", "idea has relations")]),
        ("knowledge", "abstract", "strong remembered relations that can be used", ["relation", "remember"], [rel("is_made_of", "relation", "knowledge is made of remembered relations")]),
        ("value", "abstract_social", "relation of usefulness or importance", ["good", "need"], [rel("points_to", "good", "value points toward good or useful")]),
        ("trust", "abstract_social", "strong expectation that person or relation will hold", ["person", "promise", "remember"], [rel("depends_on", "promise", "trust depends on kept relations")]),
        ("fair", "abstract_social", "balanced relation among people", ["people", "same", "rule"], [rel("uses", "same", "fair uses same relation across people")]),
        ("unfair", "abstract_social", "unbalanced relation among people", ["fair", "different"], [rel("contrasts_with", "fair", "unfair contrasts with fair")]),
        ("science", "domain", "method for testing relations in the world", ["truth", "cause", "explain"], [rel("tests", "relation", "science tests relations")]),
        ("math", "domain", "relations among number, amount, shape, pattern", ["number", "measure", "shape"], [rel("is_about", "relation", "math is about formal relations")]),
    ]
    for word, kind, summary, prereq, rels in stage5:
        e(entry(word, "age_5yo", kind, summary, rels, prerequisites=prereq))

    # Stable order by stage then insertion order already gives reviewable file.
    return rows


def sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    if text[-1] not in ".?!":
        text += "."
    return text


def question(text: str) -> str:
    text = sentence(text).rstrip(".")
    if text[-1] != "?":
        text += "?"
    return text


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


def validate_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    words = {row["word"] for row in entries}
    duplicates = [word for word, count in Counter(row["word"] for row in entries).items() if count > 1]
    missing_prereq: list[dict[str, str]] = []
    forward_prereq: list[dict[str, Any]] = []
    for row in entries:
        for prereq in row["prerequisites"]:
            if prereq not in words:
                missing_prereq.append({"word": row["word"], "missing": prereq})
                continue
            prereq_stage = next(item["stage_order"] for item in entries if item["word"] == prereq)
            if prereq_stage > row["stage_order"]:
                forward_prereq.append({"word": row["word"], "stage": row["stage_order"], "prerequisite": prereq, "prerequisite_stage": prereq_stage})
    empty_relations = [row["word"] for row in entries if not row["relations"]]
    return {
        "duplicates": duplicates,
        "missing_prerequisites": missing_prereq,
        "forward_prerequisites": forward_prereq,
        "empty_relation_bundles": empty_relations,
        "passes": not duplicates and not missing_prereq and not forward_prereq and not empty_relations,
    }


def concept_rows(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in entries:
        word = row["word"]
        prereq_text = ", ".join(row["prerequisites"][:4]) if row["prerequisites"] else "thing"
        rows.append(
            {
                "id": f"{EXPERIMENT_ID}.card.{word.replace(' ', '_')}",
                "split_hint": "train",
                "stage": row["stage"],
                "stage_order": row["stage_order"],
                "word": word,
                "task_type": "concept_card",
                "input": f"Word: {word}\nKnown earlier words: {prereq_text}\nQuestion: What kind of thing is {word}?\nAnswer:",
                "target": f"answer: {row['summary']}.\nreason: {word} is learned as {row['kind']}.",
                "metadata": {"concept_id": row["id"], "domains": row["domains"], "relations": row["relations"], "prerequisites": row["prerequisites"]},
            }
        )
        rows.append(
            {
                "id": f"{EXPERIMENT_ID}.prose.{word.replace(' ', '_')}",
                "split_hint": "train",
                "stage": row["stage"],
                "stage_order": row["stage_order"],
                "word": word,
                "task_type": "concept_prose",
                "input": "",
                "target": sentence(f"{word} means {row['summary']}. It uses earlier words like {prereq_text}"),
                "metadata": {"concept_id": row["id"], "domains": row["domains"], "relations": row["relations"], "prerequisites": row["prerequisites"]},
            }
        )
        if row["prerequisites"]:
            first_prereq = row["prerequisites"][0]
            probe_split = "dev" if row["stage_order"] <= 2 else "curriculum_test"
            rows.append(
                {
                    "id": f"{EXPERIMENT_ID}.probe.prereq.{word.replace(' ', '_')}",
                    "split_hint": probe_split,
                    "stage": row["stage"],
                    "stage_order": row["stage_order"],
                    "word": word,
                    "task_type": "prerequisite_probe",
                    "input": f"Word: {word}\nQuestion: Which earlier word helps build the meaning of {word}?\nAnswer:",
                    "target": f"answer: {first_prereq}.\nreason: {word} uses {first_prereq} as an earlier relation handle.",
                    "metadata": {"concept_id": row["id"], "domains": row["domains"], "prerequisites": row["prerequisites"]},
                }
            )
            rows.append(
                {
                    "id": f"{EXPERIMENT_ID}.probe.stage.{word.replace(' ', '_')}",
                    "split_hint": probe_split,
                    "stage": row["stage"],
                    "stage_order": row["stage_order"],
                    "word": word,
                    "task_type": "stage_probe",
                    "input": f"Word: {word}\nQuestion: Should {word} be learned before {first_prereq}?\nAnswer:",
                    "target": f"answer: no.\nreason: {first_prereq} is an earlier handle for {word}.",
                    "metadata": {"concept_id": row["id"], "domains": row["domains"], "prerequisites": row["prerequisites"]},
                }
            )
        for idx, relation in enumerate(row["relations"]):
            target = relation["target"]
            text = relation["text"]
            rows.append(
                {
                    "id": f"{EXPERIMENT_ID}.rel.{word.replace(' ', '_')}.{idx:02d}",
                    "split_hint": "train",
                    "stage": row["stage"],
                    "stage_order": row["stage_order"],
                    "word": word,
                    "task_type": "relation_fact",
                    "input": f"Word: {word}\nQuestion: What relation connects {word} and {target}?\nAnswer:",
                    "target": f"answer: {text}.\nreason: {word} has a {relation['type']} relation with {target}.",
                    "metadata": {"concept_id": row["id"], "domains": row["domains"], "relation": relation, "prerequisites": row["prerequisites"]},
                }
            )
        for contrast in row["contrast_with"]:
            rows.append(
                {
                    "id": f"{EXPERIMENT_ID}.contrast.{word.replace(' ', '_')}.{contrast.replace(' ', '_')}",
                    "split_hint": "dev" if row["stage_order"] <= 2 else "curriculum_test",
                    "stage": row["stage"],
                    "stage_order": row["stage_order"],
                    "word": word,
                    "task_type": "contrast",
                    "input": f"Word one: {word}\nWord two: {contrast}\nQuestion: Are these the same relation?\nAnswer:",
                    "target": f"answer: no.\nreason: {word} contrasts with {contrast}.",
                    "metadata": {"concept_id": row["id"], "domains": row["domains"], "contrast": contrast, "prerequisites": row["prerequisites"]},
                }
            )
    return rows


def split_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    splits = {split: [] for split in SPLITS}
    for row in rows:
        split = row.get("split_hint") or "train"
        if split not in splits:
            split = "train"
        cleaned = dict(row)
        cleaned.pop("split_hint", None)
        splits[split].append(cleaned)
    return splits


def render_variant(rows: list[dict[str, Any]], variant: str) -> list[dict[str, Any]]:
    rendered: list[dict[str, Any]] = []
    for row in rows:
        if variant == "concept_dense_qa":
            if not row["input"]:
                continue
            rendered.append({**row, "variant": variant})
        elif variant == "concept_prose":
            if row["task_type"] != "concept_prose":
                continue
            rendered.append({**row, "variant": variant, "input": "", "target": row["target"]})
        elif variant == "concept_mixed":
            rendered.append({**row, "variant": variant})
        else:
            raise ValueError(f"unknown variant {variant}")
    return rendered


def vocabulary_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    words: Counter[str] = Counter()
    for row in rows:
        text = ((row.get("input") or "") + " " + (row.get("target") or "")).lower()
        words.update(WORD_RE.findall(text))
    return {"unique_alpha_words": len(words), "top_words": words.most_common(30)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED_PATH)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"{args.output_dir} exists and is not empty; pass --overwrite")
    if args.output_dir.exists() and args.overwrite:
        retire_output_dir(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    entries = build_entries()
    validation = validate_entries(entries)
    if not validation["passes"]:
        raise SystemExit(json.dumps(validation, indent=2))

    seed = {
        "schema_version": SCHEMA_VERSION,
        "graph_id": SEED_ID,
        "title": "Adi ConceptNet V7",
        "description": "Curated staged high-frequency concept lexicon. Words are handles to relation bundles.",
        "stages": STAGES,
        "concepts": entries,
        "validation": validation,
        "counts": {
            "concepts": len(entries),
            "relations": sum(len(row["relations"]) for row in entries),
            "by_stage": Counter(row["stage"] for row in entries),
            "by_domain": Counter(domain for row in entries for domain in row["domains"]),
            "by_kind": Counter(row["kind"] for row in entries),
        },
    }
    write_json(args.seed_path, seed)

    source_rows = concept_rows(entries)
    splits = split_rows(source_rows)
    units_dir = args.output_dir / "units"
    for split, split_rows_ in splits.items():
        write_jsonl(units_dir / f"{split}.jsonl", split_rows_)

    dataset_manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "seed_graph": str(args.seed_path),
        "variants": {},
    }
    for variant in VARIANTS:
        variant_dir = args.output_dir / "datasets" / variant
        dataset_manifest["variants"][variant] = {}
        for split, split_rows_ in splits.items():
            rendered = render_variant(split_rows_, variant)
            path = variant_dir / f"{split}.jsonl"
            write_jsonl(path, rendered)
            dataset_manifest["variants"][variant][split] = {
                "path": str(path),
                "records": len(rendered),
                "vocabulary": vocabulary_stats(rendered),
            }

    write_json(args.output_dir / "datasets" / "manifest.json", dataset_manifest)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "seed_graph": str(args.seed_path),
        "output_dir": str(args.output_dir),
        "counts": seed["counts"],
        "validation": validation,
        "splits": {split: len(rows_) for split, rows_ in splits.items()},
        "variants": dataset_manifest["variants"],
        "outputs": {},
    }
    for path in [args.seed_path, args.output_dir / "datasets" / "manifest.json", *sorted(args.output_dir.rglob("*.jsonl"))]:
        manifest["outputs"][str(path)] = {"sha256": sha256_file(path)}
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({"experiment_id": EXPERIMENT_ID, "seed": str(args.seed_path), "output_dir": str(args.output_dir), "counts": seed["counts"], "splits": manifest["splits"]}, indent=2, default=dict))


if __name__ == "__main__":
    main()
