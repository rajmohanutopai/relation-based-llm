#!/usr/bin/env python3
"""Create root concept foundation v1.

V1 fixes the main issues in v0:

- split by canonical group id, not by rendered row id
- train root facts only in train; dev/test are application probes
- use clearer relation types instead of overloading can_cause
- reduce meta-language in model-visible text
- generate concrete positive/negative scenarios from root anchors
- include happiness mechanics from the project theory
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


EXPERIMENT_ID = "root_concept_foundation_v1"
SCHEMA_VERSION = "0.1.0"
SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = ("root_prose", "root_qa", "root_mixed")
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")


LAYERS = [
    ("root", 0, "Root", "Thing, kind, part, state, event, relation."),
    ("body_self", 1, "Body And Self", "Body parts, control, touch, pain, proto-self."),
    ("space", 2, "Space", "Near, far, up, down, inside, outside, on, under."),
    ("physical", 3, "Physical", "Move, touch, fall, block, open, closed, push, pull."),
    ("property", 4, "Property", "Size, weight, texture, temperature, wetness, shape, sharpness."),
    ("living", 5, "Living", "Living thing, person, child, animal, plant."),
    ("need_valence", 6, "Need And Valence", "Need, pain, comfort, safety, danger, good, bad."),
    ("emotion", 7, "Emotion", "Happy, sad, afraid, angry, want."),
    ("social", 8, "Social", "Caregiver, friend, help, hurt, give, take, share, pet."),
    ("language", 9, "Language", "Word, name, say, hear, ask, answer, story."),
    ("time_change", 10, "Time And Change", "Before, after, cause, effect, start, stop, again."),
]


NODE_SPECS = [
    ("concept.thing", "thing", "root", "concept", "anything that can have relations"),
    ("concept.kind", "kind", "root", "concept", "a group relation shared by many things"),
    ("concept.part", "part", "root", "concept", "a thing inside a larger thing"),
    ("concept.whole", "whole", "root", "concept", "a thing made of parts"),
    ("concept.state", "state", "root", "concept", "how something is now"),
    ("concept.event", "event", "root", "concept", "something that happens"),
    ("concept.relation", "relation", "root", "concept", "a link between things"),
    ("object.object", "object", "root", "object", "a thing that can be seen or touched"),
    ("object.toy", "toy", "root", "object", "object used for play"),
    ("object.ball", "ball", "root", "object", "round toy that can roll"),
    ("object.cup", "cup", "root", "object", "container for drink"),
    ("object.book", "book", "root", "object", "object with pages and words"),
    ("object.box", "box", "root", "object", "container that can be open or closed"),
    ("object.bag", "bag", "root", "object", "soft container"),
    ("object.door", "door", "root", "object", "thing that opens or closes a path"),
    ("object.food", "food", "root", "object", "thing living things eat"),
    ("object.water", "water", "root", "object", "thing living things drink"),
    ("object.blanket", "blanket", "root", "object", "soft object that can comfort"),
    ("object.needle", "needle", "root", "object", "sharp object"),
    ("object.floor", "floor", "root", "object", "low surface"),
    ("object.table", "table", "root", "object", "high surface"),
    ("place.home", "home", "root", "place", "familiar safe place"),
    ("place.park", "park", "root", "place", "outside play place"),
    ("body.body", "body", "body_self", "body", "living controlled whole"),
    ("body.hand", "hand", "body_self", "body_part", "body part for reach and touch"),
    ("body.mouth", "mouth", "body_self", "body_part", "body part for eat, taste, say"),
    ("body.eye", "eye", "body_self", "body_part", "body part for see"),
    ("body.ear", "ear", "body_self", "body_part", "body part for hear"),
    ("body.nose", "nose", "body_self", "body_part", "body part for smell"),
    ("body.skin", "skin", "body_self", "body_part", "body surface that feels"),
    ("body.leg", "leg", "body_self", "body_part", "body part for walking"),
    ("self.self", "self", "body_self", "concept", "directly controlled and directly felt body"),
    ("sense.touch", "touch sense", "body_self", "sense", "body input from contact"),
    ("sense.see", "see", "body_self", "sense", "eye input"),
    ("sense.hear", "hear", "body_self", "sense", "ear input"),
    ("sense.sound", "sound", "body_self", "signal", "thing that can be heard"),
    ("sense.taste", "taste", "body_self", "sense", "mouth input"),
    ("sense.smell", "smell", "body_self", "sense", "nose input"),
    ("sense.body_feel", "body feel", "body_self", "sense", "inside body input"),
    ("space.near", "near", "space", "space", "small distance"),
    ("space.far", "far", "space", "space", "large distance"),
    ("space.up", "up", "space", "space", "higher place"),
    ("space.down", "down", "space", "space", "lower place"),
    ("space.inside", "inside", "space", "space", "within a boundary"),
    ("space.outside", "outside", "space", "space", "not within a boundary"),
    ("space.on", "on", "space", "space", "supported by a surface"),
    ("space.under", "under", "space", "space", "below another thing"),
    ("physical.move", "move", "physical", "process", "change place"),
    ("physical.touch", "touch", "physical", "process", "make contact"),
    ("physical.reach", "reach", "physical", "process", "move hand toward thing"),
    ("physical.push", "push", "physical", "process", "move thing away"),
    ("physical.pull", "pull", "physical", "process", "move thing toward self"),
    ("physical.fall", "fall", "physical", "process", "move down when support is gone"),
    ("physical.hit", "hit", "physical", "process", "strong contact"),
    ("physical.block", "block", "physical", "process", "stop movement or access"),
    ("physical.open", "open", "physical", "state", "allows entry or movement"),
    ("physical.closed", "closed", "physical", "state", "blocks entry or movement"),
    ("physical.hold", "hold", "physical", "process", "keep in hand or arms"),
    ("physical.find", "find", "physical", "process", "see or get what was missing"),
    ("physical.lose", "lose", "physical", "process", "wanted thing is gone or not found"),
    ("physical.fix", "fix", "physical", "process", "make broken thing work again"),
    ("physical.clean", "clean", "physical", "process", "remove dirt"),
    ("physical.broken", "broken", "physical", "state", "does not work as expected"),
    ("physical.walk", "walk", "physical", "process", "move body with legs"),
    ("physical.run", "run", "physical", "process", "move fast with legs"),
    ("physical.look", "look", "physical", "process", "use eyes toward a thing"),
    ("property.hard", "hard", "property", "property", "does not change shape easily"),
    ("property.soft", "soft", "property", "property", "changes shape easily"),
    ("property.hot", "hot", "property", "property", "high temperature"),
    ("property.cold", "cold", "property", "property", "low temperature"),
    ("property.wet", "wet", "property", "property", "has water on it"),
    ("property.dry", "dry", "property", "property", "has no water on it"),
    ("property.big", "big", "property", "property", "large size"),
    ("property.small", "small", "property", "property", "small size"),
    ("property.heavy", "heavy", "property", "property", "hard to move"),
    ("property.light", "light weight", "property", "property", "easy to move"),
    ("property.sharp", "sharp", "property", "property", "can cut or hurt"),
    ("property.round", "round", "property", "property", "curved shape"),
    ("property.safe", "safe", "property", "property", "unlikely to hurt"),
    ("property.danger", "danger", "property", "property", "may hurt or break"),
    ("living.living_thing", "living thing", "living", "kind", "thing that grows or needs"),
    ("living.person", "person", "living", "kind", "living thing with social agency"),
    ("living.child", "child", "living", "kind", "young person"),
    ("living.adult", "adult", "living", "kind", "grown person"),
    ("living.animal", "animal", "living", "kind", "living thing that can move and feel"),
    ("living.young_animal", "young animal", "living", "kind", "young animal"),
    ("living.plant", "plant", "living", "kind", "living thing that grows in place"),
    ("need.food", "food need", "need_valence", "need", "need for eating"),
    ("need.water", "water need", "need_valence", "need", "need for drinking"),
    ("need.sleep", "sleep", "need_valence", "need", "need for rest"),
    ("need.air", "air", "need_valence", "need", "need for breathing"),
    ("valence.pain", "pain", "need_valence", "valence", "bad body feeling"),
    ("valence.comfort", "comfort", "need_valence", "valence", "body and situation are okay"),
    ("valence.good", "good", "need_valence", "valence", "toward okay or happy"),
    ("valence.bad", "bad", "need_valence", "valence", "toward pain, danger, or loss"),
    ("emotion.happy", "happy", "emotion", "emotion", "positive feeling"),
    ("emotion.sad", "sad", "emotion", "emotion", "negative feeling from pain, loss, or broken relation"),
    ("emotion.afraid", "afraid", "emotion", "emotion", "negative feeling from possible danger"),
    ("emotion.angry", "angry", "emotion", "emotion", "negative feeling when want is blocked"),
    ("emotion.want", "want", "emotion", "emotion", "pull toward object or state"),
    ("emotion.excited", "excited", "emotion", "emotion", "strong happy feeling before or during new event"),
    ("social.caregiver", "caregiver", "social", "role", "person who protects, feeds, comforts"),
    ("social.role", "role", "social", "role", "a social position with expected relations"),
    ("social.mom", "mom", "social", "role", "familiar caregiver"),
    ("social.dad", "dad", "social", "role", "familiar caregiver"),
    ("social.friend", "friend", "social", "role", "person who plays, helps, shares"),
    ("social.pet", "pet", "social", "role", "animal living near people and cared for"),
    ("social.help", "help", "social", "action", "reduce problem or pain"),
    ("social.hurt", "hurt", "social", "action", "cause pain or damage"),
    ("social.give", "give", "social", "action", "move object to another person"),
    ("social.take", "take", "social", "action", "get object from person or place"),
    ("social.share", "share", "social", "action", "let another person use or have too"),
    ("social.play", "play", "social", "action", "pleasant action with toy, person, or pet"),
    ("social.smile", "smile", "social", "signal", "face signal often linked to happy"),
    ("social.cry", "cry", "social", "signal", "sound and face signal often linked to pain or sad"),
    ("language.word", "word", "language", "symbol", "sound or text that can name"),
    ("language.name", "name", "language", "symbol", "word used for a thing or person"),
    ("language.say", "say", "language", "action", "make words by mouth"),
    ("language.hear_word", "hear word", "language", "event", "hear a spoken word"),
    ("language.ask", "ask", "language", "action", "use words to request answer or help"),
    ("language.answer", "answer", "language", "action", "give words back to question"),
    ("language.tell", "tell", "language", "action", "give words to another person"),
    ("language.story", "story", "language", "structure", "words about events"),
    ("time.before", "before", "time_change", "time", "earlier"),
    ("time.after", "after", "time_change", "time", "later"),
    ("time.cause", "cause", "time_change", "relation", "earlier state makes later state"),
    ("time.effect", "effect", "time_change", "relation", "later state from cause"),
    ("time.start", "start", "time_change", "time", "begin"),
    ("time.stop", "stop", "time_change", "time", "end"),
    ("time.again", "again", "time_change", "time", "repeat"),
    ("learning.new_link", "new link", "time_change", "process", "a new relation is learned"),
    ("learning.strong_link", "strong link", "time_change", "process", "a relation is already strong"),
    ("learning.broken_link", "broken link", "time_change", "process", "an expected relation breaks"),
]


RELATION_SPECS = [
    ("concept.kind", "is_a", "concept.relation", 0.80, "neutral"),
    ("concept.part", "is_a", "concept.relation", 0.80, "neutral"),
    ("concept.whole", "has_part", "concept.part", 0.80, "neutral"),
    ("concept.state", "has_part", "concept.relation", 0.80, "neutral"),
    ("object.object", "is_a", "concept.thing", 0.95, "neutral"),
    ("object.toy", "is_a", "object.object", 0.95, "positive"),
    ("object.ball", "is_a", "object.toy", 0.95, "positive"),
    ("object.cup", "is_a", "object.object", 0.95, "neutral"),
    ("object.book", "is_a", "object.object", 0.95, "neutral"),
    ("object.box", "is_a", "object.object", 0.95, "neutral"),
    ("object.bag", "is_a", "object.object", 0.95, "neutral"),
    ("object.door", "is_a", "object.object", 0.95, "neutral"),
    ("object.food", "is_a", "object.object", 0.90, "positive"),
    ("object.water", "is_a", "object.object", 0.90, "positive"),
    ("object.blanket", "is_a", "object.object", 0.90, "positive"),
    ("object.needle", "is_a", "object.object", 0.90, "negative"),
    ("object.floor", "is_a", "object.object", 0.90, "neutral"),
    ("object.table", "is_a", "object.object", 0.90, "neutral"),
    ("body.body", "is_a", "object.object", 0.95, "neutral"),
    ("body.hand", "part_of", "body.body", 0.95, "neutral"),
    ("body.mouth", "part_of", "body.body", 0.95, "neutral"),
    ("body.eye", "part_of", "body.body", 0.95, "neutral"),
    ("body.ear", "part_of", "body.body", 0.95, "neutral"),
    ("body.nose", "part_of", "body.body", 0.95, "neutral"),
    ("body.skin", "part_of", "body.body", 0.95, "neutral"),
    ("body.leg", "part_of", "body.body", 0.95, "neutral"),
    ("body.hand", "controlled_by", "self.self", 0.95, "positive"),
    ("body.mouth", "controlled_by", "self.self", 0.85, "positive"),
    ("body.leg", "controlled_by", "self.self", 0.80, "positive"),
    ("body.skin", "feels", "sense.touch", 0.95, "neutral"),
    ("body.skin", "feels", "valence.pain", 0.95, "negative"),
    ("body.eye", "uses", "sense.see", 0.95, "neutral"),
    ("body.ear", "uses", "sense.hear", 0.95, "neutral"),
    ("body.nose", "uses", "sense.smell", 0.90, "neutral"),
    ("body.mouth", "uses", "sense.taste", 0.90, "neutral"),
    ("body.body", "uses", "sense.body_feel", 0.90, "neutral"),
    ("body.hand", "can_do", "physical.reach", 0.95, "neutral"),
    ("body.hand", "can_do", "physical.touch", 0.95, "neutral"),
    ("body.hand", "can_do", "physical.push", 0.85, "neutral"),
    ("body.hand", "can_do", "physical.pull", 0.85, "neutral"),
    ("body.mouth", "can_do", "language.say", 0.85, "neutral"),
    ("body.leg", "can_do", "physical.walk", 0.80, "neutral"),
    ("body.leg", "can_do", "physical.run", 0.70, "neutral"),
    ("body.eye", "can_do", "physical.look", 0.90, "neutral"),
    ("space.near", "enables", "physical.touch", 0.95, "positive"),
    ("space.far", "prevents", "physical.touch", 0.90, "negative"),
    ("space.on", "supports", "object.object", 0.80, "neutral"),
    ("space.inside", "contrasts_with", "space.outside", 0.95, "neutral"),
    ("space.near", "contrasts_with", "space.far", 0.95, "neutral"),
    ("space.up", "contrasts_with", "space.down", 0.95, "neutral"),
    ("space.on", "contrasts_with", "space.under", 0.75, "neutral"),
    ("physical.open", "enables", "physical.touch", 0.85, "positive"),
    ("physical.closed", "prevents", "physical.touch", 0.90, "negative"),
    ("physical.closed", "makes", "physical.block", 0.90, "negative"),
    ("physical.hold", "prevents", "physical.fall", 0.85, "positive"),
    ("physical.fall", "causes", "physical.hit", 0.80, "negative"),
    ("physical.hit", "causes", "valence.pain", 0.85, "negative"),
    ("physical.push", "can_make", "physical.move", 0.80, "neutral"),
    ("physical.pull", "can_make", "physical.move", 0.80, "neutral"),
    ("physical.block", "prevents", "physical.move", 0.90, "negative"),
    ("physical.find", "causes", "emotion.happy", 0.65, "positive"),
    ("physical.lose", "causes", "emotion.sad", 0.75, "negative"),
    ("physical.fix", "causes", "valence.good", 0.65, "positive"),
    ("physical.clean", "causes", "valence.good", 0.55, "positive"),
    ("physical.broken", "causes", "valence.bad", 0.65, "negative"),
    ("property.hot", "causes", "valence.pain", 0.90, "negative"),
    ("property.sharp", "causes", "valence.pain", 0.90, "negative"),
    ("property.hard", "can_make", "physical.hit", 0.55, "negative"),
    ("property.soft", "reduces", "physical.hit", 0.65, "positive"),
    ("property.heavy", "prevents", "physical.move", 0.70, "negative"),
    ("property.light", "enables", "physical.move", 0.75, "positive"),
    ("property.round", "enables", "physical.move", 0.55, "neutral"),
    ("property.safe", "prevents", "valence.pain", 0.65, "positive"),
    ("property.danger", "can_make", "valence.pain", 0.75, "negative"),
    ("property.wet", "contrasts_with", "property.dry", 0.95, "neutral"),
    ("property.hot", "contrasts_with", "property.cold", 0.95, "neutral"),
    ("property.hard", "contrasts_with", "property.soft", 0.95, "neutral"),
    ("property.big", "contrasts_with", "property.small", 0.95, "neutral"),
    ("property.heavy", "contrasts_with", "property.light", 0.95, "neutral"),
    ("property.safe", "contrasts_with", "property.danger", 0.85, "neutral"),
    ("living.living_thing", "is_a", "concept.thing", 0.95, "neutral"),
    ("living.person", "is_a", "living.living_thing", 0.95, "neutral"),
    ("living.child", "is_a", "living.person", 0.95, "neutral"),
    ("living.adult", "is_a", "living.person", 0.95, "neutral"),
    ("living.animal", "is_a", "living.living_thing", 0.95, "neutral"),
    ("living.young_animal", "is_a", "living.animal", 0.95, "neutral"),
    ("living.plant", "is_a", "living.living_thing", 0.90, "neutral"),
    ("living.living_thing", "needs", "need.food", 0.80, "neutral"),
    ("living.living_thing", "needs", "need.water", 0.85, "neutral"),
    ("living.living_thing", "needs", "need.sleep", 0.75, "neutral"),
    ("living.living_thing", "needs", "need.air", 0.75, "neutral"),
    ("living.animal", "can_do", "physical.move", 0.85, "neutral"),
    ("living.animal", "can_do", "physical.walk", 0.70, "neutral"),
    ("living.animal", "can_do", "physical.run", 0.55, "neutral"),
    ("living.animal", "can_make", "sense.sound", 0.70, "neutral"),
    ("living.animal", "can_feel", "valence.pain", 0.90, "negative"),
    ("living.young_animal", "has_property", "property.small", 0.70, "neutral"),
    ("living.young_animal", "needs", "social.help", 0.70, "positive"),
    ("living.person", "can_do", "language.say", 0.90, "neutral"),
    ("living.person", "can_feel", "emotion.happy", 0.90, "positive"),
    ("living.person", "can_feel", "emotion.sad", 0.90, "negative"),
    ("living.person", "can_feel", "emotion.afraid", 0.75, "negative"),
    ("living.person", "can_feel", "emotion.angry", 0.70, "negative"),
    ("living.person", "can_feel", "emotion.want", 0.85, "neutral"),
    ("living.plant", "needs", "need.water", 0.85, "neutral"),
    ("social.caregiver", "is_a", "living.person", 0.95, "positive"),
    ("social.mom", "is_a", "social.caregiver", 0.95, "positive"),
    ("social.dad", "is_a", "social.caregiver", 0.95, "positive"),
    ("social.friend", "is_a", "living.person", 0.90, "positive"),
    ("social.pet", "is_a", "social.role", 0.65, "positive"),
    ("social.pet", "usually_near", "living.person", 0.70, "positive"),
    ("social.caregiver", "can_do", "social.help", 0.90, "positive"),
    ("social.caregiver", "can_make", "valence.comfort", 0.85, "positive"),
    ("social.friend", "can_do", "social.play", 0.80, "positive"),
    ("social.friend", "can_do", "social.share", 0.75, "positive"),
    ("social.help", "reduces", "valence.pain", 0.85, "positive"),
    ("social.help", "can_make", "valence.comfort", 0.80, "positive"),
    ("social.hurt", "causes", "valence.pain", 0.90, "negative"),
    ("social.hurt", "causes", "emotion.sad", 0.80, "negative"),
    ("social.give", "changes_owner_to", "living.person", 0.70, "neutral"),
    ("social.take", "changes_owner_to", "self.self", 0.65, "neutral"),
    ("social.share", "is_a", "social.give", 0.70, "positive"),
    ("social.play", "can_make", "emotion.happy", 0.80, "positive"),
    ("social.smile", "signals", "emotion.happy", 0.80, "positive"),
    ("social.cry", "signals", "valence.pain", 0.65, "negative"),
    ("social.cry", "signals", "emotion.sad", 0.75, "negative"),
    ("valence.pain", "contrasts_with", "valence.comfort", 0.90, "neutral"),
    ("valence.good", "contrasts_with", "valence.bad", 0.90, "neutral"),
    ("valence.pain", "causes", "emotion.sad", 0.80, "negative"),
    ("valence.pain", "causes", "emotion.afraid", 0.55, "negative"),
    ("valence.comfort", "causes", "emotion.happy", 0.80, "positive"),
    ("valence.good", "causes", "emotion.happy", 0.70, "positive"),
    ("valence.bad", "causes", "emotion.sad", 0.70, "negative"),
    ("property.danger", "causes", "emotion.afraid", 0.75, "negative"),
    ("emotion.want", "can_make", "physical.move", 0.65, "neutral"),
    ("emotion.want", "can_make", "language.ask", 0.60, "neutral"),
    ("emotion.angry", "can_make", "social.hurt", 0.45, "negative"),
    ("emotion.happy", "can_make", "social.smile", 0.65, "positive"),
    ("emotion.sad", "can_make", "social.cry", 0.65, "negative"),
    ("learning.new_link", "causes", "emotion.happy", 0.80, "positive"),
    ("learning.new_link", "can_make", "emotion.excited", 0.65, "positive"),
    ("learning.strong_link", "reduces", "emotion.excited", 0.55, "neutral"),
    ("learning.broken_link", "causes", "emotion.sad", 0.85, "negative"),
    ("language.word", "is_a", "concept.thing", 0.90, "neutral"),
    ("language.name", "is_a", "language.word", 0.95, "neutral"),
    ("language.name", "names", "concept.thing", 0.95, "neutral"),
    ("language.say", "makes", "sense.sound", 0.80, "neutral"),
    ("language.hear_word", "uses", "sense.hear", 0.95, "neutral"),
    ("language.hear_word", "can_wake", "language.word", 0.75, "neutral"),
    ("language.ask", "requests", "language.answer", 0.90, "neutral"),
    ("language.tell", "uses", "language.word", 0.90, "neutral"),
    ("language.story", "has_part", "concept.event", 0.80, "neutral"),
    ("language.story", "has_part", "concept.relation", 0.80, "neutral"),
    ("time.before", "contrasts_with", "time.after", 0.95, "neutral"),
    ("time.cause", "before", "time.effect", 0.80, "neutral"),
    ("time.start", "contrasts_with", "time.stop", 0.85, "neutral"),
    ("time.again", "repeats", "concept.event", 0.85, "neutral"),
    ("object.ball", "has_property", "property.round", 0.90, "neutral"),
    ("object.ball", "has_property", "property.light", 0.70, "neutral"),
    ("object.book", "has_property", "property.light", 0.60, "neutral"),
    ("object.blanket", "has_property", "property.soft", 0.90, "positive"),
    ("object.needle", "has_property", "property.sharp", 0.95, "negative"),
    ("object.table", "has_property", "property.heavy", 0.65, "neutral"),
    ("object.floor", "supports", "object.object", 0.65, "neutral"),
    ("object.box", "can_have_state", "physical.open", 0.80, "neutral"),
    ("object.box", "can_have_state", "physical.closed", 0.80, "neutral"),
    ("object.bag", "can_have_state", "physical.open", 0.75, "neutral"),
    ("object.bag", "can_have_state", "physical.closed", 0.75, "neutral"),
    ("object.door", "can_have_state", "physical.open", 0.85, "neutral"),
    ("object.door", "can_have_state", "physical.closed", 0.85, "neutral"),
    ("place.home", "has_property", "property.safe", 0.65, "positive"),
    ("place.park", "enables", "social.play", 0.65, "positive"),
]


RELATION_RENDER = {
    "is_a": "{source} is {target}",
    "part_of": "{source} is part of {target}",
    "controlled_by": "{source} is controlled by {target}",
    "feels": "{source} feels {target}",
    "uses": "{source} uses {target}",
    "can_do": "{source} can {target}",
    "can_make": "{source} can make {target}",
    "can_feel": "{source} can feel {target}",
    "can_have_state": "{source} can be {target}",
    "has_property": "{source} is {target}",
    "needs": "{source} needs {target}",
    "enables": "{source} lets {target} happen",
    "prevents": "{source} stops {target}",
    "supports": "{source} supports {target}",
    "causes": "{source} causes {target}",
    "makes": "{source} makes {target}",
    "reduces": "{source} reduces {target}",
    "contrasts_with": "{source} is not {target}",
    "usually_near": "{source} is often near {target}",
    "signals": "{source} shows {target}",
    "changes_owner_to": "{source} moves having to {target}",
    "names": "{source} names {target}",
    "can_wake": "{source} can wake {target}",
    "requests": "{source} asks for {target}",
    "has_part": "{source} has {target}",
    "before": "{source} comes before {target}",
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


def lower_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip()).lower()
    if not text:
        return ""
    if text[-1] not in ".?!":
        text += "."
    return text


def stable_percent(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16) % 100


def split_for_group(group_id: str, *, train_only: bool = False) -> str:
    if train_only:
        return "train"
    value = stable_percent(group_id)
    if value < 80:
        return "train"
    if value < 90:
        return "dev"
    return "curriculum_test"


def label_map() -> dict[str, str]:
    return {node_id: label for node_id, label, *_ in NODE_SPECS}


LABELS = label_map()


def label(node_id: str) -> str:
    return LABELS.get(node_id, node_id)


def relation_text(source: str, rel_type: str, target: str) -> str:
    template = RELATION_RENDER.get(rel_type, "{source} " + rel_type.replace("_", " ") + " {target}")
    return template.format(source=label(source), target=label(target))


def relation_dict(source: str, rel_type: str, target: str) -> dict[str, str]:
    return {"source": source, "type": rel_type, "target": target}


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
        retire_output_dir(path)
    path.mkdir(parents=True, exist_ok=True)


def rel(source: str, rel_type: str, target: str) -> tuple[str, str, str]:
    return source, rel_type, target


def make_unit(
    group_id: str,
    unit_id: str,
    task_type: str,
    input_text: str,
    target_text: str,
    relations: list[tuple[str, str, str]],
    *,
    train_only: bool = False,
) -> dict[str, Any]:
    return {
        "group_id": group_id,
        "unit_id": unit_id,
        "task_type": task_type,
        "split": split_for_group(group_id, train_only=train_only),
        "input": input_text,
        "target": target_text,
        "relations": [relation_dict(*relation) for relation in relations],
    }


def add_prose_and_qa(
    units: list[dict[str, Any]],
    group_id: str,
    task_type: str,
    scene: str,
    question: str,
    answer: str,
    reason: str,
    relations: list[tuple[str, str, str]],
) -> None:
    split_group = group_id
    prose = clean_sentence(f"{scene} {answer}")
    units.append(
        make_unit(
            split_group,
            f"{group_id}.prose",
            f"{task_type}_prose",
            "",
            prose,
            relations,
        )
    )
    units.append(
        make_unit(
            split_group,
            f"{group_id}.qa",
            f"{task_type}_qa",
            f"Scene: {clean_sentence(scene)}\nQuestion: {question}\nAnswer:",
            f"answer: {lower_sentence(answer)}\nreason: {lower_sentence(reason)}",
            relations,
        )
    )
    units.append(
        make_unit(
            split_group,
            f"{group_id}.why",
            f"{task_type}_why",
            f"Scene: {clean_sentence(scene)}\nQuestion: Why?\nAnswer:",
            f"answer: {lower_sentence(reason)}",
            relations,
        )
    )


def build_fact_units() -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for index, (source, rel_type, target, _strength, _valence) in enumerate(RELATION_SPECS, start=1):
        group_id = f"fact.{source}.{rel_type}.{target}"
        fact = clean_sentence(relation_text(source, rel_type, target))
        relations = [rel(source, rel_type, target)]
        units.append(
            make_unit(
                group_id,
                f"fact.{index:03d}.prose",
                "root_fact_prose",
                "",
                fact,
                relations,
                train_only=True,
            )
        )
        units.append(
            make_unit(
                group_id,
                f"fact.{index:03d}.qa",
                "root_fact_qa",
                f"Question: What is true about {label(source)}?\nAnswer:",
                f"answer: {fact.lower()}",
                relations,
                train_only=True,
            )
        )
    return units


INHERITANCE_PROBES = [
    ("inherit.child.living", "child", "living.child", "is_a", "living.person", "is_a", "living.living_thing", "A child is a person. A person is a living thing.", "Child is a living thing."),
    ("inherit.mom.person", "mom", "social.mom", "is_a", "social.caregiver", "is_a", "living.person", "Mom is a caregiver. A caregiver is a person.", "Mom is a person."),
    ("inherit.friend.living", "friend", "social.friend", "is_a", "living.person", "is_a", "living.living_thing", "A friend is a person. A person is a living thing.", "A friend is a living thing."),
    ("inherit.young_animal.needs_food", "young animal", "living.young_animal", "is_a", "living.animal", "is_a", "living.living_thing", "A young animal is an animal. An animal is a living thing.", "A young animal is a living thing."),
    ("inherit.animal.food", "animal", "living.animal", "is_a", "living.living_thing", "needs", "need.food", "An animal is a living thing. A living thing needs food.", "An animal needs food."),
    ("inherit.animal.water", "animal", "living.animal", "is_a", "living.living_thing", "needs", "need.water", "An animal is a living thing. A living thing needs water.", "An animal needs water."),
    ("inherit.person.sleep", "person", "living.person", "is_a", "living.living_thing", "needs", "need.sleep", "A person is a living thing. A living thing needs sleep.", "A person needs sleep."),
    ("inherit.hand.object", "hand", "body.hand", "part_of", "body.body", "is_a", "object.object", "A hand is part of body. Body is an object.", "A hand is part of an object."),
    ("inherit.ball.toy", "ball", "object.ball", "is_a", "object.toy", "is_a", "object.object", "A ball is a toy. A toy is an object.", "A ball is an object."),
    ("inherit.name.word", "name", "language.name", "is_a", "language.word", "is_a", "concept.thing", "A name is a word. A word is a thing.", "A name is a thing."),
]


def build_inheritance_units() -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for group_id, subject, source, source_rel, middle, middle_rel, target, scene, answer in INHERITANCE_PROBES:
        relations = [rel(source, source_rel, middle), rel(middle, middle_rel, target)]
        reason = f"{label(source)} connects through {label(middle)}."
        add_prose_and_qa(
            units,
            group_id,
            "inheritance",
            scene,
            f"What follows for {subject}?",
            answer,
            reason,
            relations,
        )
    return units


TOUCH_OBJECTS = [
    ("ball", "object.ball"),
    ("cup", "object.cup"),
    ("book", "object.book"),
    ("toy", "object.toy"),
    ("blanket", "object.blanket"),
    ("needle", "object.needle"),
]


CONTAINERS = [("box", "object.box"), ("bag", "object.bag")]


def object_path(node_id: str) -> list[tuple[str, str, str]]:
    if node_id == "object.ball":
        return [rel("object.ball", "is_a", "object.toy"), rel("object.toy", "is_a", "object.object")]
    return [rel(node_id, "is_a", "object.object")]


def living_path(node_id: str) -> list[tuple[str, str, str]]:
    if node_id == "living.child":
        return [rel("living.child", "is_a", "living.person"), rel("living.person", "is_a", "living.living_thing")]
    if node_id == "living.person":
        return [rel("living.person", "is_a", "living.living_thing")]
    if node_id == "living.young_animal":
        return [rel("living.young_animal", "is_a", "living.animal"), rel("living.animal", "is_a", "living.living_thing")]
    return [rel(node_id, "is_a", "living.living_thing")]


def build_scenario_units() -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []

    for name, node in TOUCH_OBJECTS:
        add_prose_and_qa(
            units,
            f"touch.{name}.near",
            "touch_distance",
            f"The hand is near the {name}. The hand reaches.",
            f"Does the hand touch the {name}?",
            f"The hand touches the {name}.",
            "Near lets touch happen, and hand can touch.",
            [rel("space.near", "enables", "physical.touch"), rel("body.hand", "can_do", "physical.touch")] + object_path(node),
        )
        add_prose_and_qa(
            units,
            f"touch.{name}.far",
            "touch_distance",
            f"The {name} is far from the hand. The hand reaches.",
            f"Does the hand touch the {name}?",
            f"The hand does not touch the {name}.",
            "Far stops touch.",
            [rel("space.far", "prevents", "physical.touch"), rel("body.hand", "can_do", "physical.reach")] + object_path(node),
        )

    for obj_name, obj_node in TOUCH_OBJECTS[:5]:
        for container_name, container_node in CONTAINERS:
            add_prose_and_qa(
                units,
                f"container.{obj_name}.{container_name}.open",
                "container_access",
                f"The {obj_name} is inside an open {container_name}. The hand reaches inside.",
                f"Can the hand touch the {obj_name}?",
                f"The hand can touch the {obj_name}.",
                "Open lets touch happen.",
                [rel("physical.open", "enables", "physical.touch"), rel(container_node, "can_have_state", "physical.open")] + object_path(obj_node),
            )
            add_prose_and_qa(
                units,
                f"container.{obj_name}.{container_name}.closed",
                "container_access",
                f"The {obj_name} is inside a closed {container_name}. The hand reaches the {container_name}.",
                f"Can the hand touch the {obj_name}?",
                f"The closed {container_name} blocks the hand.",
                "Closed stops touch.",
                [rel("physical.closed", "prevents", "physical.touch"), rel("physical.closed", "makes", "physical.block"), rel(container_node, "can_have_state", "physical.closed")],
            )

    for obj_name, obj_node, prop_node, answer in [
        ("cup", "object.cup", "property.hot", "The hot cup can hurt the hand."),
        ("needle", "object.needle", "property.sharp", "The sharp needle can hurt the skin."),
        ("blanket", "object.blanket", "property.soft", "The soft blanket does not hurt the skin."),
        ("ball", "object.ball", "property.round", "The round ball can roll."),
    ]:
        if prop_node == "property.soft":
            reason = "Soft reduces hard hit."
            relations = [rel("property.soft", "reduces", "physical.hit"), rel(obj_node, "has_property", prop_node)]
        elif prop_node == "property.round":
            reason = "Round lets movement happen."
            relations = [rel("property.round", "enables", "physical.move"), rel(obj_node, "has_property", prop_node)]
        else:
            reason = f"{label(prop_node)} causes pain."
            relations = [rel(prop_node, "causes", "valence.pain"), rel(obj_node, "has_property", prop_node)]
        add_prose_and_qa(
            units,
            f"property_touch.{obj_name}.{prop_node.split('.')[-1]}",
            "property_touch",
            f"The {obj_name} is {label(prop_node)}. The hand touches the {obj_name}.",
            "What happens?",
            answer,
            reason,
            relations,
        )

    for obj_name, obj_node, weight_node in [
        ("ball", "object.ball", "property.light"),
        ("book", "object.book", "property.light"),
        ("box", "object.box", "property.heavy"),
        ("table", "object.table", "property.heavy"),
    ]:
        if weight_node == "property.light":
            add_prose_and_qa(
                units,
                f"move_weight.{obj_name}.light",
                "move_weight",
                f"The {obj_name} is light weight. The hand pushes the {obj_name}.",
                f"Does the {obj_name} move?",
                f"The {obj_name} moves.",
                "Light weight lets movement happen.",
                [rel("property.light", "enables", "physical.move"), rel("body.hand", "can_do", "physical.push"), rel(obj_node, "has_property", "property.light")],
            )
        else:
            add_prose_and_qa(
                units,
                f"move_weight.{obj_name}.heavy",
                "move_weight",
                f"The {obj_name} is heavy. The hand pushes the {obj_name}.",
                f"Does the {obj_name} move?",
                f"The {obj_name} does not move.",
                "Heavy stops movement.",
                [rel("property.heavy", "prevents", "physical.move"), rel("body.hand", "can_do", "physical.push"), rel(obj_node, "has_property", "property.heavy")],
            )

    for obj_name, obj_node in TOUCH_OBJECTS[:4]:
        add_prose_and_qa(
            units,
            f"fall.{obj_name}.hold",
            "support_fall",
            f"The hand holds the {obj_name}. The {obj_name} is up.",
            f"Does the {obj_name} fall?",
            f"The {obj_name} does not fall.",
            "Hold stops fall.",
            [rel("physical.hold", "prevents", "physical.fall")] + object_path(obj_node),
        )
        add_prose_and_qa(
            units,
            f"fall.{obj_name}.release",
            "support_fall",
            f"The {obj_name} is up. The hand stops holding it.",
            f"Does the {obj_name} fall?",
            f"The {obj_name} falls down.",
            "When support stops, fall can happen.",
            [rel("physical.fall", "causes", "physical.hit")] + object_path(obj_node),
        )

    for living_name, living_node in [
        ("child", "living.child"),
        ("person", "living.person"),
        ("animal", "living.animal"),
        ("young animal", "living.young_animal"),
    ]:
        for need_name, need_node in [("food", "need.food"), ("water", "need.water")]:
            add_prose_and_qa(
                units,
                f"living_need.{living_name.replace(' ', '_')}.{need_name}",
                "living_need",
                f"The {living_name} is a living thing. The {living_name} does not have {need_name}.",
                f"What does the {living_name} need?",
                f"The {living_name} needs {need_name}.",
                "A living thing has needs.",
                living_path(living_node) + [rel("living.living_thing", "needs", need_node)],
            )

    for place_name, place_node in [("home", "place.home"), ("park", "place.park")]:
        add_prose_and_qa(
            units,
            f"place.{place_name}.play",
            "place_play",
            f"The child is at the {place_name}. The friend is near the child.",
            "What can happen?",
            "The child can play with the friend.",
            f"{place_name.title()} can support play.",
            [rel(place_node, "enables" if place_node == "place.park" else "has_property", "social.play" if place_node == "place.park" else "property.safe"), rel("social.friend", "can_do", "social.play")],
        )

    social_cases = [
        ("caregiver_help", "The child feels pain. The caregiver helps the child.", "What happens?", "Help reduces pain and brings comfort.", "Help reduces pain.", [rel("social.help", "reduces", "valence.pain"), rel("social.help", "can_make", "valence.comfort")]),
        ("friend_share", "The child wants the toy. The friend shares the toy.", "What happens?", "The child feels happy.", "Share can make play and happy feeling.", [rel("social.friend", "can_do", "social.share"), rel("social.play", "can_make", "emotion.happy")]),
        ("hurt_pain", "The child is hit. The child is hurt.", "What happens?", "The child feels pain and sadness.", "Hurt causes pain.", [rel("social.hurt", "causes", "valence.pain"), rel("valence.pain", "causes", "emotion.sad")]),
        ("smile_happy", "The child feels happy. The child smiles.", "What does the smile show?", "The smile shows happy feeling.", "Smile shows happy.", [rel("social.smile", "signals", "emotion.happy")]),
        ("cry_sad", "The child feels sad. The child cries.", "What does the cry show?", "The cry shows sad feeling.", "Cry shows sad.", [rel("social.cry", "signals", "emotion.sad")]),
    ]
    for case_id, scene, question, answer, reason, relations in social_cases:
        add_prose_and_qa(units, f"social.{case_id}", "social_effect", scene, question, answer, reason, relations)

    happiness_cases = [
        ("new_link", "The child learns a new word for the ball.", "How does the child feel?", "The child feels happy and excited.", "A new link can cause happy feeling.", [rel("learning.new_link", "causes", "emotion.happy"), rel("learning.new_link", "can_make", "emotion.excited")]),
        ("strong_link", "The child already knows the word ball. Mom says ball again.", "How does the child feel?", "The child feels only a little excited.", "A strong old link reduces new excitement.", [rel("learning.strong_link", "reduces", "emotion.excited")]),
        ("broken_link", "The child keeps the toy near him. Then the toy is gone.", "How does the child feel?", "The child feels sad.", "A broken link causes sadness.", [rel("learning.broken_link", "causes", "emotion.sad"), rel("physical.lose", "causes", "emotion.sad")]),
        ("pain_removed", "The child feels pain. The caregiver helps and the pain goes down.", "How does the child feel?", "The child feels comfort and happiness.", "Pain reduction brings comfort, and comfort causes happy feeling.", [rel("social.help", "reduces", "valence.pain"), rel("valence.comfort", "causes", "emotion.happy")]),
    ]
    for case_id, scene, question, answer, reason, relations in happiness_cases:
        add_prose_and_qa(units, f"happiness.{case_id}", "happiness_mechanism", scene, question, answer, reason, relations)

    for obj_name, obj_node in [("ball", "object.ball"), ("cup", "object.cup"), ("book", "object.book"), ("toy", "object.toy")]:
        add_prose_and_qa(
            units,
            f"language.name.{obj_name}",
            "language_name",
            f"Mom says the word {obj_name}. The child hears the word and looks at the {obj_name}.",
            f"What does the word {obj_name} name?",
            f"The word {obj_name} names the {obj_name}.",
            "A name names a thing, and hearing a word can wake the word.",
            [rel("language.name", "names", "concept.thing"), rel("language.hear_word", "can_wake", "language.word")] + object_path(obj_node),
        )

    time_cases = [
        ("before_after_fall", "The ball is up before. The ball falls after.", "What is the order?", "Up is before fall, and fall is after.", "Before and after mark order.", [rel("time.before", "contrasts_with", "time.after"), rel("physical.fall", "causes", "physical.hit")]),
        ("start_stop", "The child starts running. Then the child stops.", "What changed?", "Running starts and then stops.", "Start and stop contrast.", [rel("time.start", "contrasts_with", "time.stop"), rel("body.leg", "can_do", "physical.run")]),
        ("again_repeat", "The child hears the song. Then the child hears the song again.", "What happened?", "The event repeated.", "Again repeats an event.", [rel("time.again", "repeats", "concept.event")]),
    ]
    for case_id, scene, question, answer, reason, relations in time_cases:
        add_prose_and_qa(units, f"time.{case_id}", "time_change", scene, question, answer, reason, relations)

    return units


def build_units() -> list[dict[str, Any]]:
    units = build_fact_units()
    units.extend(build_inheritance_units())
    units.extend(build_scenario_units())
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, Any]] = []
    for unit in units:
        key = (unit["task_type"], unit["input"], unit["target"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(unit)
    return unique


def variant_accepts(variant: str, unit: dict[str, Any]) -> bool:
    is_qa = unit["task_type"].endswith("_qa") or unit["task_type"].endswith("_why")
    if variant == "root_prose":
        return not is_qa
    if variant == "root_qa":
        return is_qa
    if variant == "root_mixed":
        return True
    raise ValueError(f"unknown variant: {variant}")


def make_record(variant: str, unit: dict[str, Any]) -> dict[str, Any]:
    input_text = unit["input"]
    target_text = unit["target"]
    messages = (
        [{"role": "user", "content": input_text}, {"role": "assistant", "content": target_text}]
        if input_text
        else [{"role": "assistant", "content": target_text}]
    )
    return {
        "id": f"dataset.{EXPERIMENT_ID}.{variant}.{unit['split']}.{unit['unit_id']}",
        "source_example_id": unit["unit_id"],
        "root_group_id": unit["group_id"],
        "experiment_id": EXPERIMENT_ID,
        "variant": variant,
        "split": unit["split"],
        "task_type": unit["task_type"],
        "input": input_text,
        "target": target_text,
        "messages": messages,
        "metadata": {
            "domain_id": EXPERIMENT_ID,
            "stage": "stage_1_root_concept_foundation",
            "representation": variant,
            "relations_visible_to_model": False,
            "root_relations": unit["relations"],
        },
    }


def build_records(units: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    records = {variant: {split: [] for split in SPLITS} for variant in VARIANTS}
    for variant in VARIANTS:
        for unit in units:
            if variant_accepts(variant, unit):
                records[variant][unit["split"]].append(make_record(variant, unit))
        for split in SPLITS:
            records[variant][split].sort(key=lambda row: row["id"])
    return records


def build_graph(units: list[dict[str, Any]]) -> dict[str, Any]:
    layers = [
        {"id": layer_id, "order": order, "label": label_value, "description": description}
        for layer_id, order, label_value, description in LAYERS
    ]
    nodes = [
        {
            "id": node_id,
            "label": label_value,
            "layer": layer,
            "kind": kind,
            "age_status": "emerging",
            "summary": summary,
        }
        for node_id, label_value, layer, kind, summary in NODE_SPECS
    ]
    relations = [
        {
            "source": source,
            "type": rel_type,
            "target": target,
            "strength": strength,
            "valence": valence,
            "age_status": "emerging",
        }
        for source, rel_type, target, strength, valence in RELATION_SPECS
    ]
    micro_experiences = []
    for unit in units:
        if unit["task_type"].endswith("_prose") and not unit["task_type"].startswith("root_fact"):
            micro_experiences.append(
                {
                    "id": "root_v1." + re.sub(r"[^a-z0-9_]+", "_", unit["unit_id"].lower()).strip("_"),
                    "title": unit["task_type"].replace("_", " ").title(),
                    "age_status": "emerging",
                    "events": [unit["target"]],
                    "relations_observed": [
                        {
                            "source": relation["source"],
                            "type": relation["type"],
                            "target": relation["target"],
                            "strength_delta": 0.04,
                        }
                        for relation in unit["relations"]
                    ],
                }
            )
    evaluation_questions = []
    for index, unit in enumerate([u for u in units if u["split"] != "train" and u["input"]], start=1):
        evaluation_questions.append(
            {
                "id": f"root_v1_eval.{index:04d}",
                "question": unit["input"].replace("\nAnswer:", ""),
                "expected_answer": unit["target"],
                "expected_relations": unit["relations"],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "graph_id": EXPERIMENT_ID,
        "metadata": {
            "title": "Root Concept Foundation V1",
            "description": "Corrected root anchors and concrete scenarios for relation-first TinyStories training.",
            "notes": [
                "Root facts are train-only.",
                "Dev/test examples are split by canonical root_group_id.",
                "Model-visible text avoids root/relation meta-language except for the word relation itself.",
            ],
        },
        "layers": layers,
        "nodes": nodes,
        "relations": relations,
        "micro_experiences": micro_experiences[:120],
        "evaluation_questions": evaluation_questions,
    }


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


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(key, "unknown") for row in rows).items()))


def leakage_report(records: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for variant, split_rows in records.items():
        groups = {split: {row["root_group_id"] for row in rows} for split, rows in split_rows.items()}
        report[variant] = {
            "train_dev_group_overlap": sorted(groups["train"] & groups["dev"]),
            "train_test_group_overlap": sorted(groups["train"] & groups["curriculum_test"]),
            "dev_test_group_overlap": sorted(groups["dev"] & groups["curriculum_test"]),
        }
    return report


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

    manifest_path = args.output_dir / "datasets" / "manifest.json"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "seed_graph": str(args.seed_output),
        "output_dir": str(args.output_dir / "datasets"),
        "leakage_report": leakage_report(records),
        "variants": {
            variant: {
                split: {
                    "total": len(rows),
                    "group_count": len({row["root_group_id"] for row in rows}),
                    "task_type_counts": count_by(rows, "task_type"),
                    "vocabulary": vocab_stats(rows),
                }
                for split, rows in split_rows.items()
            }
            for variant, split_rows in records.items()
        },
        "outputs": file_manifest(output_paths),
    }
    write_json(manifest_path, manifest)
    output_paths["dataset_manifest"] = manifest_path

    training_config_path = args.output_dir / "training_config.json"
    training_config = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "dataset_manifest": str(manifest_path),
        "output_root": f"runs/{EXPERIMENT_ID}/nanochat",
        "format": {
            "prompt_template": "{input}",
            "target_template": "{target}",
            "notes": "Empty input records are normal LM prose; QA records are input-target examples.",
        },
        "training": {
            "recommended_stage_order": [
                "root_mixed",
                "tinystories_word_attachment_v0",
                "tinystories_plain_text",
            ],
            "max_seq_length": 256,
            "seed": 1729,
        },
    }
    write_json(training_config_path, training_config)
    output_paths["training_config"] = training_config_path

    top_manifest_path = args.output_dir / "manifest.json"
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
            "micro_experiences": len(graph.get("micro_experiences", [])),
            "evaluation_questions": len(graph.get("evaluation_questions", [])),
        },
        "splits": {
            variant: {split: len(rows) for split, rows in split_rows.items()}
            for variant, split_rows in records.items()
        },
        "outputs": file_manifest(output_paths),
    }
    write_json(top_manifest_path, top_manifest)
    print(json.dumps(top_manifest, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(f"data/developmental_graph/experiments/{EXPERIMENT_ID}"))
    parser.add_argument("--seed-output", type=Path, default=Path(f"data/developmental_graph/seeds/{EXPERIMENT_ID}.json"))
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    units = build_units()
    records = build_records(units)
    graph = build_graph(units)
    write_outputs(args, graph, records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
