#!/usr/bin/env python3
"""Acting agent v1: shared features, so learning about one thing can carry over
to similar things, and "useful gain" becomes measurable.

Design: docs/acting-agent-v1-design.md

Builds on scripts/acting_agent_v0.py (same world, arms, training and scoring)
and changes three things:

  gadgets   real words (tv, tablet, night light, ...) instead of "tv#17".
            Condition A uses 3 fixed gadgets; --fresh-gadgets draws each
            room's 2 gadgets from all 30 words.
  features  --features names : a learned slot per thing (as v0)
            --features words : frozen MiniLM vector of the name, projected,
                               plus a small learned slot
            --features graph : property features from a simulated relation
                               graph (the property table with 10% errors
                               and 15% gaps, drawn once), plus a small slot
  gate      --gate runs the random arm with the transfer test switched on and
            reports mean transfer for ordinary things vs gadgets.

Word vectors use the world_sim phrase "a {w} in a family home with a baby",
cached in runs/acting_agent_v1/word_vectors.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_agent_v0 as A  # noqa: E402

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GADGET_WORDS = [
    "tv", "tablet", "laptop", "computer screen", "video monitor", "game console", "projector", "night light",
    "lava lamp", "disco light", "light-up toy", "flashing toy", "glow stick", "fairy lights", "star projector",
    "light-up wand", "bubble machine", "spinning light", "smart speaker", "radio", "music player", "music box",
    "digital photo frame", "clock radio", "toy robot that beeps", "singing toy", "musical mobile", "blinking sign",
    "color-changing lamp", "led strip",
]
FIXED_GADGETS = ["tv", "light-up toy", "music box"]
GADGET_SET = set(GADGET_WORDS)
VEC_CACHE = Path("runs/acting_agent_v1/word_vectors.json")


def word_vectors(words: list[str]) -> dict[str, list[float]]:
    cached = json.loads(VEC_CACHE.read_text()) if VEC_CACHE.exists() else {"vectors": {}}
    vecs = cached["vectors"]
    missing = [w for w in words if w not in vecs]
    if missing:
        from transformers import AutoModel, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(EMBED_MODEL)
        model = AutoModel.from_pretrained(EMBED_MODEL)
        enc = tok([f"a {w} in a family home with a baby" for w in missing], padding=True, return_tensors="pt")
        with torch.no_grad():
            hidden = model(**enc).last_hidden_state
        mask = enc["attention_mask"].unsqueeze(-1).float()
        out = nn.functional.normalize((hidden * mask).sum(1) / mask.sum(1), dim=1)
        vecs.update({w: [round(float(x), 5) for x in v] for w, v in zip(missing, out)})
        VEC_CACHE.parent.mkdir(parents=True, exist_ok=True)
        VEC_CACHE.write_text(json.dumps({"model": EMBED_MODEL, "vectors": vecs}))
    return {w: vecs[w] for w in words}


# --- patch v0's world: real gadget words -----------------------------------

A.GADGETS = GADGET_WORDS
A.NAMES = A.TRAIN_OBJECTS + GADGET_WORDS + list(A.v0.HELD_OUT_CANDIDATES)
A.is_gadget = lambda thing: thing in GADGET_SET
A.gadget_base = lambda thing: thing
A.GADGET_ACTIONS = {g: ["watch", "push_gentle", "push_hard", "shake", "drop"] for g in GADGET_WORDS}


def new_room(rng, n_gadgets: int, copy: int = 0) -> dict[str, str]:
    """copy > 0 (fresh mode) draws gadgets from all 30 words; else the fixed 3."""
    room = rng.choice(A.v0.ROOMS)
    pool = GADGET_WORDS if copy else FIXED_GADGETS
    things = rng.sample(A.TRAIN_OBJECTS, 6) + rng.sample(pool, n_gadgets)
    return {t: rng.choice(A.ROOM_SURFACES[room]) for t in things}


A.new_room = new_room


class WordWorldModel(A.WorldModel):
    """Thing input = projection of a frozen word vector + a small learned slot."""

    def __init__(self, vectors: torch.Tensor, d: int = 32, slot: int = 8):
        super().__init__(d=d)
        self.register_buffer("vecs", vectors)
        self.proj = nn.Linear(vectors.shape[1], d - slot)
        self.slot = nn.Embedding(len(A.NAMES), slot)
        del self.thing

    def forward(self, t, a, s):
        thing = torch.cat([self.proj(self.vecs[t]), self.slot(t)], -1)
        h = self.net(torch.cat([thing, self.action(a), self.surface(s)], -1))
        h = h.view(-1, len(A.ACTIONS), 3)
        return h[torch.arange(len(a)), a]


GRAPH_FIELDS = ["round", "cylinder", "wheels", "light", "a_bit_heavy", "heavy", "hard", "bouncy", "noisy",
                "breakable", "big", "electronic"]


def true_properties(thing: str) -> dict[str, float]:
    if thing in GADGET_SET:
        # What a graph would say about a gadget: a hard electronic thing.
        return {"round": 0, "cylinder": 0, "wheels": 0, "light": 1, "a_bit_heavy": 0, "heavy": 0, "hard": 1,
                "bouncy": 0, "noisy": 1, "breakable": 1, "big": 0, "electronic": 1}
    p, w = A.OBJECTS[thing], A.WEIGHT[thing]
    return {"round": p["round"], "cylinder": p.get("cylinder", False), "wheels": p.get("wheels", False),
            "light": w == 1, "a_bit_heavy": w == 2, "heavy": w == 3, "hard": p["hard"], "bouncy": p["bouncy"],
            "noisy": p["noisy"], "breakable": p["breakable"] and p.get("breaks_on") != "sharp",
            "big": p["size"] >= 3, "electronic": False}


def graph_features(error: float = 0.1, missing: float = 0.15, seed: int = 0) -> torch.Tensor:
    """A simulated relation graph: the property table with errors and gaps,
    drawn once (seed 0) so every run sees the same imperfect graph. Each field
    gives a value and a known/unknown bit."""
    import random
    rng = random.Random(seed)
    rows = []
    for name in A.NAMES:
        props = true_properties(name)
        row = []
        for f in GRAPH_FIELDS:
            if rng.random() < missing:
                row += [0.0, 0.0]
            else:
                v = float(props[f])
                if rng.random() < error:
                    v = 1.0 - v
                row += [2 * v - 1, 1.0]
        rows.append(row)
    return torch.tensor(rows)


HAND_FIELDS = ["round_like", "hard", "bouncy", "breakable", "heavy_like", "noisy", "closable"]


def hand_graph_cells() -> dict[tuple[str, str], bool]:
    """(thing, field) -> value, as stated in the 6mo hand-written relations,
    read through the world_sim_v1 audit's claim map. Later rows win ties."""
    import glob
    import re
    wv1 = A.wv1
    rows = [json.loads(l) for f in sorted(glob.glob(wv1.HANDWRITTEN_GLOB)) for l in open(f)]
    cells = {}
    for r in rows:
        if r["subject"] not in A.OBJECTS:
            continue
        for rels, pattern, field, value in wv1.CLAIMS:
            if r["relation"] in rels and re.search(pattern, r["object"]) and not re.search(r"\bnot\b|\boften\b", r["object"]):
                cells[(r["subject"], field)] = value
    return cells


def sourced_graph_cells(name: str = "object_properties_v0") -> dict[tuple[str, str], bool]:
    """(thing, field) -> value from external sources or the LLM; docs/object-properties-v0.md."""
    path = Path(f"data/developmental_graph/experiments/{name}/cells.json")
    return {(c["object"], c["field"]): c["value"] for c in json.loads(path.read_text())["cells"]}


def hand_features(mode: str) -> torch.Tensor:
    """mode: hand (stated values), hand_cells_true (same cells, true values),
    sourced, sourced_cells_true (same, from external sources),
    table7 (every cell, true values)."""
    if mode.startswith("llm"):
        cells = sourced_graph_cells("object_properties_llm_v0")
    else:
        cells = sourced_graph_cells() if mode.startswith("sourced") else hand_graph_cells()
    rows = []
    for name in A.NAMES:
        row = []
        for f in HAND_FIELDS:
            truth = None if name in GADGET_SET else A.wv1.table_value(name, f)
            if mode == "table7":
                known, v = truth is not None, truth
            else:
                known = (name, f) in cells
                v = cells.get((name, f)) if mode in ("hand", "sourced", "llm") else truth
            row += [2 * float(bool(v)) - 1, 1.0] if known and v is not None else [0.0, 0.0]
        rows.append(row)
    return torch.tensor(rows)


def make_world_model(args):
    if args.features in ("hand", "hand_cells_true", "sourced", "sourced_cells_true", "llm", "llm_cells_true", "table7"):
        return WordWorldModel(hand_features(args.features))
    if args.features == "names":
        return A.WorldModel()
    if args.features == "graph":
        return WordWorldModel(graph_features())
    vecs = word_vectors(A.NAMES)
    return WordWorldModel(torch.tensor([vecs[n] for n in A.NAMES]))


A.make_world_model = make_world_model


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--features", choices=["names", "words", "graph", "hand", "hand_cells_true", "sourced", "sourced_cells_true", "llm", "llm_cells_true", "table7"], default="words")
    p.add_argument("--gate", action="store_true")
    known, rest = p.parse_known_args()
    if known.gate:
        args = argparse.Namespace(actions=3000, episode_len=20, warmup=200, batch_size=32, lr=3e-3, activation=0.02,
                                  temperature=0.3, epsilon=0.1, eval_every=50, gadgets=2, flip=0.1, group="region",
                                  features=known.features, measure_transfer=True)
        print(f"gate: features={known.features}")
        for fresh in (False, True):
            args.fresh_gadgets = fresh
            res = A.run("random", 1, args)
            t = res["transfer"]
            o, g = t["ordinary"], t["gadget"]
            gap, se = o["mean"] - g["mean"], (o["se"] ** 2 + g["se"] ** 2) ** 0.5
            ok = o["mean"] > 0 and gap > 2 * se
            print(f"  {'B fresh' if fresh else 'A fixed'}: ordinary {o['mean']:+.5f} (se {o['se']:.5f}, n {o['n']}) "
                  f"gadget {g['mean']:+.5f} (se {g['se']:.5f}, n {g['n']})  gap {gap:+.5f} = {gap / se:.1f} se  "
                  f"area {res['curve_area']:.3f}  -> {'PASS' if ok else 'fail'}")
        return
    # Full runs: hand the remaining flags to v0's main, keeping --features.
    sys.argv = [sys.argv[0]] + rest
    orig_parse = argparse.ArgumentParser.parse_args

    def parse_with_features(self, *a, **k):
        ns = orig_parse(self, *a, **k)
        ns.features = known.features
        return ns

    argparse.ArgumentParser.parse_args = parse_with_features
    A.main()


if __name__ == "__main__":
    main()
