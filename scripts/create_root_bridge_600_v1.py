#!/usr/bin/env python3
"""Create a 600-word bridge curriculum after root irregular QA.

The bridge is designed to test staged relation learning without the large
vocabulary/style jump that hurt the root -> handwritten age-6mo transfer.

It keeps:
- all root_procedural_irregular_v1 training rows
- the same prompt/answer/reason style
- model-visible ordinary QA, with relations hidden in metadata

It adds:
- nearby 6-month concepts using the existing root words as anchors
- enough bridge units to bring the actual train alpha vocabulary from 300 to
  about 600 words
"""

from __future__ import annotations

import argparse
import hashlib
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
from output_state import retire_output_dir  # noqa: E402


EXPERIMENT_ID = "root_bridge_600_v1"
VARIANT = "root_bridge_600_qa"
SOURCE_EXPERIMENT_ID = root_irregular.EXPERIMENT_ID
SOURCE_VARIANT = root_irregular.VARIANT
ROOT_DIR = Path("data/developmental_graph/experiments/root_procedural_irregular_v1")
WORD_RE = re.compile(r"[a-z]+")
RAW_RE = re.compile(r"\S+")
SPLITS = root_irregular.SPLITS
TEST_SPLITS = root_irregular.TEST_SPLITS


BRIDGE_CONCEPT_ROWS: tuple[tuple[str, str, str, str, str], ...] = (
    ("object", "thing", "can_be_seen", "An object is a thing the baby can see.", "object is a seen thing"),
    ("surface", "thing", "can_be_touched", "A surface is a part of a thing the hand can touch.", "surface is touchable"),
    ("body", "baby", "has_parts", "The body has hand, skin, mouth, eye, ear, and leg.", "body has parts"),
    ("face", "body", "can_be_seen", "A face is a body part the baby can see.", "face is seen"),
    ("voice", "sound", "can_be_heard", "A voice is a sound the baby can hear.", "voice is heard"),
    ("noise", "sound", "can_be_heard", "A noise is a sound the baby can hear.", "noise is heard"),
    ("tone", "voice", "changes_feeling", "A gentle tone can bring comfort.", "gentle tone brings comfort"),
    ("mouth", "body", "makes_sound", "The mouth can make sound.", "mouth makes sound"),
    ("nose", "body", "smells", "The nose can smell.", "nose smells"),
    ("tongue", "body", "tastes", "The tongue can taste.", "tongue tastes"),
    ("tummy", "body", "feels_hunger", "The tummy can feel hunger.", "tummy feels hunger"),
    ("head", "body", "turns", "The head can turn toward sound.", "head turns toward sound"),
    ("back", "body", "can_be_touched", "The back can be touched.", "back can be touched"),
    ("foot", "body", "part_of_body", "The foot is part of the body.", "foot is body part"),
    ("toe", "foot", "part_of_foot", "The toe is part of the foot.", "toe is foot part"),
    ("arm", "body", "moves", "The arm can move.", "arm can move"),
    ("knee", "leg", "part_of_leg", "The knee is part of the leg.", "knee is leg part"),
    ("elbow", "arm", "part_of_arm", "The elbow is part of the arm.", "elbow is arm part"),
    ("cheek", "face", "part_of_face", "The cheek is part of the face.", "cheek is face part"),
    ("hair", "head", "part_of_head", "Hair is on the head.", "hair is on head"),
    ("hunger", "need", "causes_discomfort", "Hunger can cause discomfort.", "hunger causes discomfort"),
    ("hungry", "hunger", "is_state", "Hungry is a hunger state.", "hungry is hunger state"),
    ("full", "food", "reduces_hunger", "Full means hunger is less.", "full reduces hunger"),
    ("thirst", "water", "is_need", "Thirst is a need for water.", "thirst needs water"),
    ("thirsty", "thirst", "is_state", "Thirsty is a thirst state.", "thirsty is thirst state"),
    ("tired", "sleep", "is_need_state", "Tired can mean the body needs sleep.", "tired needs sleep"),
    ("rest", "sleep", "reduces_tired", "Rest can reduce tired feeling.", "rest reduces tired"),
    ("awake", "sleep", "contrasts", "Awake is not sleep.", "awake is not sleep"),
    ("diaper", "body", "can_be_wet", "A diaper can be wet.", "diaper can be wet"),
    ("wet", "touch", "is_feeling", "Wet is a touch feeling.", "wet is touch feeling"),
    ("dry", "wet", "contrasts", "Dry is not wet.", "dry is not wet"),
    ("cold", "touch", "can_cause_discomfort", "Cold touch can cause discomfort.", "cold causes discomfort"),
    ("warm", "touch", "can_make_comfort", "Warm touch can bring comfort.", "warm brings comfort"),
    ("discomfort", "pain", "near", "Discomfort is a bad feeling near pain.", "discomfort is bad feeling"),
    ("distress", "pain", "caused_by", "Pain can cause distress.", "pain causes distress"),
    ("calm", "comfort", "caused_by", "Comfort can make the baby calm.", "comfort makes calm"),
    ("soothe", "comfort", "can_make", "A caregiver can soothe the baby.", "caregiver can soothe baby"),
    ("familiar", "again", "made_by", "Familiar means seen or heard again and again.", "familiar comes from again"),
    ("unfamiliar", "new", "contrasts", "Unfamiliar means not familiar.", "unfamiliar is not familiar"),
    ("memory", "again", "made_by", "A memory is a link kept after an event.", "memory keeps link"),
    ("attention", "eye", "uses", "Attention can make the eye look at one thing.", "attention guides eye"),
    ("expectation", "before", "uses", "Expectation is a before-link about what may happen.", "expectation is before link"),
    ("surprise", "new", "caused_by", "A new event can cause surprise.", "new event causes surprise"),
    ("control", "hand", "seen_by", "Control is seen when the hand moves after the baby tries.", "control follows try"),
    ("self", "body", "controlled_body", "Self begins with the body the baby can control.", "self is controlled body"),
    ("other", "caregiver", "not_controlled", "Other is a thing the baby cannot control.", "other is not controlled"),
    ("boundary", "skin", "marked_by", "Skin marks a body boundary.", "skin marks boundary"),
    ("own", "self", "belongs_to", "Own means with the self.", "own means with self"),
    ("mine", "own", "means", "Mine means own thing.", "mine means own"),
    ("yours", "other", "means", "Yours means with another person.", "yours means with other"),
    ("peek", "eye", "uses", "Peek means see for a short time.", "peek is short see"),
    ("hide", "see", "prevents", "Hide can stop seeing.", "hide stops seeing"),
    ("hidden", "hide", "state", "Hidden means not seen now.", "hidden means not seen"),
    ("cover", "hide", "can_make", "A cover can hide a thing.", "cover can hide"),
    ("under", "space", "place", "Under is a place below a thing.", "under means below"),
    ("behind", "space", "place", "Behind is a place not in front.", "behind is place"),
    ("front", "space", "place", "Front is a place the face can turn toward.", "front is place"),
    ("left", "space", "place", "Left is a side place.", "left is side"),
    ("right", "space", "place", "Right is a side place.", "right is side"),
    ("middle", "space", "place", "Middle is between sides.", "middle is between"),
    ("edge", "surface", "part", "An edge is the end of a surface.", "edge is surface end"),
    ("corner", "edge", "part", "A corner is where edges meet.", "corner has edges"),
    ("top", "above", "place", "Top is the above part.", "top is above"),
    ("bottom", "under", "place", "Bottom is the under part.", "bottom is under"),
    ("side", "thing", "part", "A side is a part of a thing.", "side is part"),
    ("inside", "container", "place", "Inside is a place in a container.", "inside is in container"),
    ("outside", "container", "place", "Outside is not inside.", "outside is not inside"),
    ("roll", "ball", "action", "A ball can roll.", "ball can roll"),
    ("bounce", "ball", "action", "A ball can bounce.", "ball can bounce"),
    ("squishy", "soft", "property", "Squishy means soft and easy to push.", "squishy is soft"),
    ("flat", "surface", "property", "Flat means the surface is even.", "flat is even surface"),
    ("round", "ball", "property", "Round helps a ball roll.", "round helps roll"),
    ("smooth", "touch", "property", "Smooth is a gentle touch property.", "smooth is gentle touch"),
    ("rough", "touch", "property", "Rough touch can cause discomfort.", "rough causes discomfort"),
    ("sticky", "touch", "property", "Sticky touch makes things hold together.", "sticky holds together"),
    ("slippery", "touch", "property", "Slippery things are hard to hold.", "slippery hard to hold"),
    ("softness", "soft", "property", "Softness can reduce hurt.", "softness reduces hurt"),
    ("hardness", "hard", "property", "Hardness can make hit hurt.", "hardness can hurt"),
    ("weight", "heavy", "property", "Weight tells if a thing is heavy or light.", "weight tells heavy"),
    ("size", "big", "property", "Size tells if a thing is big or small.", "size tells big"),
    ("big", "thing", "property", "Big things can be hard to move.", "big can be hard to move"),
    ("small", "thing", "property", "Small things can be easy to hold.", "small can be held"),
    ("tiny", "small", "property", "Tiny means very small.", "tiny means small"),
    ("long", "thing", "property", "Long means more length.", "long means length"),
    ("short", "thing", "property", "Short means less length.", "short means less length"),
    ("color", "eye", "property", "Color is a thing the eye can see.", "color is seen"),
    ("red", "color", "example", "Red is a color.", "red is color"),
    ("blue", "color", "example", "Blue is a color.", "blue is color"),
    ("green", "color", "example", "Green is a color.", "green is color"),
    ("yellow", "color", "example", "Yellow is a color.", "yellow is color"),
    ("white", "color", "example", "White is a color.", "white is color"),
    ("black", "color", "example", "Black is a color.", "black is color"),
    ("bright", "light", "property", "Bright light is easy to see.", "bright light is seen"),
    ("dark", "light", "property", "Dark means less light.", "dark means less light"),
    ("quiet", "sound", "property", "Quiet means less sound.", "quiet means less sound"),
    ("loud", "sound", "property", "Loud sound can cause discomfort.", "loud sound causes discomfort"),
    ("music", "sound", "kind", "Music is a sound pattern.", "music is sound pattern"),
    ("rhythm", "again", "pattern", "Rhythm is sound again and again.", "rhythm repeats sound"),
    ("pattern", "again", "relation", "A pattern is something that happens again.", "pattern repeats"),
    ("repeat", "again", "action", "Repeat means do again.", "repeat means again"),
    ("change", "event", "relation", "Change means a thing is not the same after.", "change means not same after"),
    ("still", "move", "contrast", "Still means not moving.", "still means not moving"),
    ("moving", "move", "state", "Moving means changing place.", "moving changes place"),
    ("start", "before", "time", "Start is before an action.", "start is before action"),
    ("stop", "after", "time", "Stop is after an action ends.", "stop is after action"),
    ("wait", "time", "action", "Wait means time passes before action.", "wait uses time"),
    ("turn", "move", "action", "Turn means move to face another way.", "turn changes way"),
    ("shake", "move", "action", "Shake means move again and again.", "shake repeats move"),
    ("kick", "leg", "action", "Kick is an action with the leg.", "kick uses leg"),
    ("grab", "hand", "action", "Grab means hold with the hand.", "grab uses hand"),
    ("drop", "fall", "action", "Drop can make a thing fall.", "drop causes fall"),
    ("lift", "up", "action", "Lift moves a thing up.", "lift moves up"),
    ("press", "push", "action", "Press is a kind of push.", "press is push"),
    ("carry", "hold", "action", "Carry means hold while moving.", "carry is hold and move"),
    ("crawl", "move", "action", "Crawl is moving with body near floor.", "crawl is body move"),
    ("sit", "body", "action", "Sit means the body is on a support.", "sit uses support"),
    ("stand", "leg", "action", "Stand uses legs and support.", "stand uses leg"),
    ("falling", "fall", "state", "Falling means moving down.", "falling moves down"),
    ("feeding", "food", "event", "Feeding gives food or milk.", "feeding gives food"),
    ("bath", "water", "event", "A bath uses water on the body.", "bath uses water"),
    ("nap", "sleep", "event", "A nap is a short sleep.", "nap is sleep"),
    ("hugging", "hug", "event", "Hugging can bring comfort.", "hugging brings comfort"),
    ("crying", "cry", "event", "Crying can show distress.", "crying shows distress"),
    ("smiling", "smile", "event", "Smiling can show happy feeling.", "smiling shows happy"),
    ("looking", "eye", "event", "Looking uses the eye.", "looking uses eye"),
    ("listening", "ear", "event", "Listening uses the ear.", "listening uses ear"),
    ("smelling", "nose", "event", "Smelling uses the nose.", "smelling uses nose"),
    ("tasting", "tongue", "event", "Tasting uses the tongue.", "tasting uses tongue"),
    ("touchable", "touch", "property", "Touchable means the hand can touch it.", "touchable can be touched"),
    ("visible", "see", "property", "Visible means the eye can see it.", "visible can be seen"),
    ("audible", "hear", "property", "Audible means the ear can hear it.", "audible can be heard"),
    ("edible", "food", "property", "Edible means can be food.", "edible can be food"),
    ("careful", "dangerous", "response", "Careful action can reduce pain.", "careful reduces pain"),
    ("gentle", "soft", "property", "Gentle touch can bring comfort.", "gentle brings comfort"),
    ("roughly", "rough", "manner", "Roughly means with rough touch.", "roughly is rough touch"),
    ("slowly", "slow", "manner", "Slowly means moving with more time.", "slowly uses time"),
    ("quickly", "fast", "manner", "Quickly means moving with less time.", "quickly uses less time"),
    ("slow", "time", "property", "Slow means more time for movement.", "slow uses more time"),
    ("fast", "time", "property", "Fast means less time for movement.", "fast uses less time"),
    ("nearer", "near", "comparison", "Nearer means more near.", "nearer is more near"),
    ("farther", "far", "comparison", "Farther means more far.", "farther is more far"),
    ("higher", "high", "comparison", "Higher means more high.", "higher is more high"),
    ("lower", "down", "comparison", "Lower means more down.", "lower is more down"),
    ("brighter", "bright", "comparison", "Brighter means more bright.", "brighter is more bright"),
    ("quieter", "quiet", "comparison", "Quieter means less sound.", "quieter is less sound"),
    ("louder", "loud", "comparison", "Louder means more sound.", "louder is more sound"),
    ("better", "good", "comparison", "Better means more good.", "better is more good"),
    ("worse", "pain", "comparison", "Worse means more bad feeling.", "worse is more bad"),
    ("choice", "action", "relation", "Choice means one action and not another.", "choice selects action"),
    ("try", "action", "relation", "Try means the baby starts an action.", "try starts action"),
    ("success", "good", "outcome", "Success means the action works.", "success means action works"),
    ("fail", "not", "outcome", "Fail means the action does not work.", "fail means not work"),
    ("goal", "want", "relation", "Goal means a wanted result.", "goal is wanted result"),
    ("want", "need", "relation", "Want means the baby moves toward a thing.", "want moves toward thing"),
    ("avoid", "pain", "action", "Avoid means move away from pain.", "avoid moves away from pain"),
    ("away", "far", "place", "Away means more far.", "away means far"),
    ("towards", "toward", "place", "Towards means moving to a thing.", "towards means toward"),
    ("approach", "toward", "action", "Approach means move toward.", "approach moves toward"),
    ("leave", "away", "action", "Leave means move away.", "leave moves away"),
    ("return", "again", "action", "Return means come again.", "return means come again"),
    ("request", "want", "signal", "A request shows want.", "request shows want"),
    ("response", "event", "relation", "A response happens after a signal.", "response is after signal"),
    ("share", "give", "social", "Share means give for play.", "share is give for play"),
    ("take", "hold", "action", "Take means make a thing held.", "take makes held"),
    ("offer", "give", "action", "Offer means show give can happen.", "offer can give"),
    ("refuse", "no", "action", "Refuse means say no.", "refuse means no"),
    ("accept", "yes", "action", "Accept means say yes.", "accept means yes"),
    ("turntaking", "again", "social", "Turntaking means one then another.", "turntaking uses then"),
    ("together", "with", "relation", "Together means with another.", "together means with"),
    ("alone", "without", "relation", "Alone means not with another.", "alone means not with"),
    ("without", "not", "relation", "Without means not with.", "without means not with"),
    ("nearby", "near", "place", "Nearby means near.", "nearby means near"),
    ("present", "there", "state", "Present means there now.", "present means there"),
    ("absent", "gone", "state", "Absent means gone.", "absent means gone"),
    ("missing", "gone", "state", "Missing means gone and wanted.", "missing is gone wanted"),
    ("found", "finds", "state", "Found means not missing now.", "found means not missing"),
    ("gone", "away", "state", "Gone means not there now.", "gone means not there"),
    ("arrival", "comes", "event", "Arrival means comes here.", "arrival means comes"),
    ("comes", "toward", "action", "Comes means moves toward here.", "comes means toward here"),
    ("leaves", "away", "action", "Leaves means moves away.", "leaves means away"),
    ("openable", "open", "property", "Openable means can become open.", "openable can open"),
    ("closable", "closed", "property", "Closable means can become closed.", "closable can close"),
    ("locked", "closed", "state", "Locked means closed and hard to open.", "locked blocks open"),
    ("loose", "open", "state", "Loose means easy to move or open.", "loose enables move"),
    ("tight", "closed", "state", "Tight means hard to move or open.", "tight blocks move"),
    ("empty", "inside", "state", "Empty means no thing inside.", "empty has no inside thing"),
    ("filled", "inside", "state", "Filled means something is inside.", "filled has inside thing"),
    ("spilled", "fall", "event", "Spilled means liquid fell out.", "spilled means liquid fell"),
    ("clean", "good", "state", "Clean can feel good.", "clean feels good"),
    ("dirty", "bad", "state", "Dirty can cause discomfort.", "dirty causes discomfort"),
    ("bad", "pain", "valence", "Bad feeling is near pain.", "bad is near pain"),
    ("okay", "good", "valence", "Okay means not bad.", "okay means not bad"),
    ("better", "good", "valence", "Better means more good.", "better means more good"),
    ("worse", "bad", "valence", "Worse means more bad.", "worse means more bad"),
    ("favorite", "happy", "relation", "Favorite means a thing often brings happy feeling.", "favorite brings happy"),
    ("boring", "old", "feeling", "Boring means old link gives little excitement.", "boring gives less excitement"),
    ("interesting", "new", "feeling", "Interesting means a new link can form.", "interesting can make new link"),
    ("curious", "new", "feeling", "Curious means wanting a new link.", "curious wants new link"),
    ("learning", "new", "process", "Learning means making new links.", "learning makes new links"),
    ("known", "old", "state", "Known means the link is old.", "known means old link"),
    ("unknown", "new", "state", "Unknown means the link is not made yet.", "unknown means no link yet"),
    ("remember", "memory", "action", "Remember means a memory link wakes again.", "remember wakes memory"),
    ("forget", "memory", "action", "Forget means a memory link does not wake.", "forget stops memory"),
    ("stronger", "strong", "comparison", "Stronger means more strong.", "stronger means more strong"),
    ("weaker", "weak", "comparison", "Weaker means less strong.", "weaker means less strong"),
    ("weak", "less", "property", "Weak means less strong.", "weak means less strong"),
    ("relation", "link", "name", "A relation is a link between things.", "relation means link"),
    ("meaning", "relation", "name", "Meaning is made from many relations.", "meaning uses relations"),
    ("simple", "less", "property", "Simple means fewer relations.", "simple means fewer relations"),
    ("complex", "many", "property", "Complex means many relations.", "complex means many relations"),
    ("many", "more", "quantity", "Many means more things.", "many means more"),
    ("few", "less", "quantity", "Few means less things.", "few means less"),
    ("number", "many", "quantity", "Number tells how many.", "number tells many"),
    ("one", "number", "quantity", "One is a number for a single thing.", "one means single"),
    ("two", "number", "quantity", "Two is one and one.", "two means one and one"),
    ("more", "many", "quantity", "More means many or extra.", "more means extra"),
    ("less", "few", "quantity", "Less means not as many.", "less means fewer"),
    ("all", "many", "quantity", "All means every thing in a group.", "all means every thing"),
    ("some", "few", "quantity", "Some means part of a group.", "some means part"),
    ("none", "no", "quantity", "None means no thing.", "none means no thing"),
    ("group", "many", "relation", "A group has many things together.", "group has many"),
    ("part", "thing", "relation", "A part belongs to a thing.", "part belongs to thing"),
    ("whole", "all", "relation", "Whole means all parts together.", "whole means all parts"),
)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


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


def words_in_text(text: str) -> set[str]:
    return set(WORD_RE.findall(text.lower()))


def vocab(rows: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(WORD_RE.findall(f"{row['input']}\n{row['target']}".lower()))
    return counter


def raw_vocab(rows: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(RAW_RE.findall(f"{row['input']}\n{row['target']}".lower()))
    return counter


def make_bridge_unit(index: int, concept: str, anchor: str, relation: str, scene: str, fact: str) -> dict[str, Any]:
    question = f"what does {concept} mean"
    if relation in {"contrasts", "prevents"}:
        question = f"what does {concept} tell"
    return {
        "id": f"rootbridge.v1.word_meaning.{index:04d}.{root_irregular.clean_spaces(concept)}",
        "rule_family": "bridge_word_meaning",
        "question_type": "meaning",
        "scene": root_irregular.sentence(scene),
        "question": root_irregular.question(question),
        "answer": fact.strip().lower(),
        "main_fact": fact.strip().lower(),
        "relations": [f"{concept} {relation} {anchor}".lower()],
        "negative_relations": [],
        "root_relations": [],
        "negative_root_relations": [],
        "surface_bindings": [
            {"surface": concept, "root_anchor": anchor, "text": f"{concept} attaches near {anchor}"}
        ],
        "metadata": {
            "thing": concept,
            "anchor": anchor,
            "relation": relation,
            "question_type": "meaning",
            "root_seed_id": "root_concept_foundation_v1",
            "bridge_source": "controlled_600_word_bridge",
            "positive": True,
            "outcome": "meaning",
        },
    }


def bridge_record(split: str, unit: dict[str, Any], surface: dict[str, str], surface_index: int) -> dict[str, Any]:
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


def build_bridge_records(
    split: str,
    units: list[dict[str, Any]],
    seed: int,
    prompt_indices: set[int] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for unit in units:
        scene = root_irregular.irregular_scene(unit)
        surfaces = root_irregular.prompt_surfaces(unit, scene)
        for index, surface in enumerate(surfaces, 1):
            if prompt_indices is not None and index not in prompt_indices:
                continue
            rows.append(bridge_record(split, unit, surface, index))
    random.Random(seed + root_irregular.stable_int("bridge", split)).shuffle(rows)
    return rows


def retag_source_rows(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    retagged: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["id"] = str(item["id"]).replace(SOURCE_EXPERIMENT_ID, EXPERIMENT_ID).replace(SOURCE_VARIANT, VARIANT)
        item["experiment_id"] = EXPERIMENT_ID
        item["variant"] = VARIANT
        item["split"] = split
        item["evaluation_bucket"] = split
        item["metadata"] = {
            **item.get("metadata", {}),
            "domain_id": EXPERIMENT_ID,
            "representation": VARIANT,
            "source_world": SOURCE_EXPERIMENT_ID,
            "bridge_includes_source_root": True,
        }
        retagged.append(item)
    return retagged


def split_bridge_units(units: list[dict[str, Any]], seed: int) -> dict[str, list[dict[str, Any]]]:
    splits = {split: [] for split in SPLITS}
    for unit in units:
        score = root_irregular.stable_int("bridge-split", seed, unit["id"]) % 100
        if score < 10:
            split = "dev"
        elif score < 16:
            split = "test_observation"
        elif score < 22:
            split = "test_inference"
        elif score < 28:
            split = "test_transfer"
        elif score < 34:
            split = "test_counterfactual"
        else:
            split = "train"
        splits[split].append(unit)
    return splits


def pick_train_bridge_units(
    root_train_rows: list[dict[str, Any]],
    all_units: list[dict[str, Any]],
    target_words: int,
) -> list[dict[str, Any]]:
    rows = retag_source_rows(root_train_rows, "train")
    selected: list[dict[str, Any]] = []
    current = set(vocab(rows))
    for unit in all_units:
        candidate_records = build_bridge_records("train", [unit], seed=1729, prompt_indices={1, 2, 3, 4, 5})
        candidate_words = set(vocab(candidate_records))
        if len(current | candidate_words) <= target_words:
            selected.append(unit)
            rows.extend(candidate_records)
            current |= candidate_words
        if len(current) >= target_words:
            break
    return selected


def stats(rows: list[dict[str, Any]], root_words: set[str]) -> dict[str, Any]:
    word_counts = vocab(rows)
    raw_counts = raw_vocab(rows)
    words = set(word_counts)
    return {
        "total": len(rows),
        "unique_words_alpha": len(words),
        "total_words_alpha": sum(word_counts.values()),
        "unique_raw_whitespace_tokens": len(raw_counts),
        "total_raw_whitespace_tokens": sum(raw_counts.values()),
        "root_words_present": len(words & root_words),
        "root_words_missing": sorted(root_words - words),
        "added_words": sorted(words - root_words),
        "added_word_count": len(words - root_words),
        "prompt_conflicts": prompt_conflict_stats(rows),
        "task_type_counts": dict(sorted(Counter(str(row.get("task_type", "unknown")) for row in rows).items())),
    }


def prompt_conflict_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets_by_input: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        targets_by_input[row["input"]].add(row["target"])
    conflicts = sum(1 for values in targets_by_input.values() if len(values) > 1)
    return {
        "unique_inputs": len(targets_by_input),
        "ambiguous_inputs": conflicts,
    }


def write_dataset(output_dir: Path, records: dict[str, list[dict[str, Any]]], root_words: set[str]) -> None:
    output_paths: dict[str, Path] = {}
    for split, rows in records.items():
        path = output_dir / "datasets" / VARIANT / f"{split}.jsonl"
        write_jsonl(path, rows)
        output_paths[split] = path
    for split in ("train", "dev", "curriculum_test"):
        write_jsonl(output_dir / f"{split}.jsonl", records[split])

    dataset_manifest_path = output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": EXPERIMENT_ID,
        "variant": VARIANT,
        "source_experiment_id": SOURCE_EXPERIMENT_ID,
        "source_variant": SOURCE_VARIANT,
        "target_train_alpha_vocabulary": 600,
        "same_visible_style_as": SOURCE_EXPERIMENT_ID,
        "splits": {split: stats(rows, root_words) for split, rows in records.items()},
        "outputs": {
            split: {"path": str(path), "sha256": sha256_file(path)}
            for split, path in sorted(output_paths.items())
        },
        "notes": [
            "Train contains all root irregular training rows, retagged under this experiment.",
            "Bridge rows use the same answer/reason target format.",
            "Bridge rows use the same irregular prompt renderer.",
            "For selected bridge units, prompt surfaces 1-5 are train, surface 6 is dev, and surface 7 is test_transfer.",
            "Added words are selected greedily so train alpha vocabulary reaches exactly 600.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)

    write_json(
        output_dir / "training_config.json",
        {
            "schema_version": "0.1.0",
            "experiment_id": EXPERIMENT_ID,
            "dataset_manifest": str(dataset_manifest_path),
            "format": {"prompt_template": "{input}\n", "target_template": "{target}"},
            "training": {"max_seq_length": 256, "seed": 1729, "recommended_depth": 4},
        },
    )
    write_json(
        output_dir / "manifest.json",
        {
            "schema_version": "0.1.0",
            "experiment_id": EXPERIMENT_ID,
            "variant": VARIANT,
            "dataset_manifest": str(dataset_manifest_path),
            "training_config": str(output_dir / "training_config.json"),
            "record_splits": {split: len(rows) for split, rows in records.items()},
            "train_alpha_vocabulary": dataset_manifest["splits"]["train"]["unique_words_alpha"],
            "train_added_alpha_words": dataset_manifest["splits"]["train"]["added_word_count"],
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/developmental_graph/experiments/root_bridge_600_v1"),
    )
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--target-words", type=int, default=600)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_output_dir(args.output_dir, args.overwrite)

    source_records = {
        split: read_jsonl(ROOT_DIR / "datasets" / SOURCE_VARIANT / f"{split}.jsonl")
        for split in (*SPLITS, "curriculum_test")
    }
    root_words = set(vocab(source_records["train"]))
    if len(root_words) != 300:
        raise SystemExit(f"expected 300 root train words, found {len(root_words)}")

    candidate_units = [
        make_bridge_unit(index, concept, anchor, relation, scene, fact)
        for index, (concept, anchor, relation, scene, fact) in enumerate(BRIDGE_CONCEPT_ROWS, 1)
    ]
    selected_train_units = pick_train_bridge_units(
        source_records["train"],
        candidate_units,
        args.target_words,
    )
    selected_ids = {unit["id"] for unit in selected_train_units}
    remaining_units = [unit for unit in candidate_units if unit["id"] not in selected_ids]
    bridge_splits = split_bridge_units(remaining_units, args.seed)
    bridge_splits["train"] = selected_train_units

    records: dict[str, list[dict[str, Any]]] = {}
    for split in SPLITS:
        rows = retag_source_rows(source_records[split], split)
        if split == "train":
            rows.extend(build_bridge_records(split, selected_train_units, args.seed, prompt_indices={1, 2, 3, 4, 5}))
        elif split == "dev":
            rows.extend(build_bridge_records(split, bridge_splits[split], args.seed))
            rows.extend(build_bridge_records(split, selected_train_units, args.seed, prompt_indices={6}))
        elif split == "test_transfer":
            rows.extend(build_bridge_records(split, bridge_splits[split], args.seed))
            rows.extend(build_bridge_records(split, selected_train_units, args.seed, prompt_indices={7}))
        else:
            rows.extend(build_bridge_records(split, bridge_splits[split], args.seed))
        random.Random(args.seed + root_irregular.stable_int("records", split)).shuffle(rows)
        records[split] = rows
    curriculum_rows = [row for split in TEST_SPLITS for row in records[split]]
    curriculum_rows.sort(key=lambda row: row["id"])
    records["curriculum_test"] = curriculum_rows

    write_jsonl(args.output_dir / "bridge_units" / "train.jsonl", selected_train_units)
    for split in TEST_SPLITS + ("dev",):
        write_jsonl(args.output_dir / "bridge_units" / f"{split}.jsonl", bridge_splits[split])
    write_dataset(args.output_dir, records, root_words)

    manifest = json.loads((args.output_dir / "manifest.json").read_text(encoding="utf-8"))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
