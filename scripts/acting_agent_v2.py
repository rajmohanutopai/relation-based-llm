#!/usr/bin/env python3
"""Acting agent v2: a fair test of the happiness rule with useful gain.

Design: docs/acting-agent-v2-design.md

A world too big to cover at random: 800 made-up objects in 16 kinds, rooms of
20 objects + 4 gadgets, 15 actions per room. Names carry no meaning, so the
only route for carry-over is the graph features (property fields with 5%
errors and 10% gaps, plus 6 fields no rule uses).

Useful gain = neighbour transfer: one plain step on the new case alone (on a
copy of the weights), then the fall in loss on the same action's cases for
the 8 probe things nearest by graph features. Probe things (100 objects + 40
gadgets) never appear in rooms or tests.

Untried choices borrow the mean score of the same action on the 8 nearest
tried things (graph model) or get the top score (names model).

  --gate   random arm, seed 1, both gadget conditions, graph and names models,
           with neighbour transfer measured on every action; prints the three
           gate checks.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_agent_v0 as A  # noqa: E402  (Region, windows, region_score)

OUT = Path("runs/acting_agent_v2")
ACTIONS = A.ACTIONS
N_BITS = A.N_BITS
SURFACES = A.SURFACES
SURFACE_LIST = A.SURFACE_LIST
SMOOTH = A.wv1.SMOOTH
ROOMS = A.v0.ROOMS
ROOM_SURFACES = A.ROOM_SURFACES

# --- kinds -------------------------------------------------------------------
# weight 1-3, shape, size 1-3, then binary rule fields, then distractors
# (red, soft_to_touch, has_face, striped, shiny, smells) that no rule uses.
RULE_BINS = ["hard", "bouncy", "breakable", "noisy"]
DISTRACTORS = ["red", "soft_to_touch", "has_face", "striped", "shiny", "smells"]
SHAPES = ["none", "round", "tube", "wheels"]
K = lambda w, sh, sz, hard, bouncy, brk, noisy, *d: dict(
    weight=w, shape=sh, size=sz, hard=hard, bouncy=bouncy, breakable=brk, noisy=noisy, electronic=0,
    **dict(zip(DISTRACTORS, d)))
KINDS = {
    "ball_like":     K(1, "round", 2, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0),
    "hard_ball":     K(1, "round", 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0),
    "block_like":    K(1, "none", 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0),
    "rattle_like":   K(1, "none", 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0),
    "cup_like":      K(1, "tube", 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0),
    "glass_like":    K(1, "tube", 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0),
    "bowl_like":     K(2, "round", 2, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1),
    "soft_toy":      K(1, "none", 2, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0),
    "squeaky_toy":   K(1, "none", 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0),
    "car_like":      K(1, "wheels", 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0),
    "big_car":       K(2, "wheels", 3, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0),
    "bottle_like":   K(2, "tube", 2, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1),
    "fruit_like":    K(2, "round", 2, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1),
    "pot_like":      K(3, "tube", 3, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0),
    "cloth_like":    K(1, "none", 2, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1),
    "box_like":      K(3, "none", 3, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0),
}
GADGET_KIND = K(1, "none", 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0) | {"electronic": 1}

N_ROOM, N_PROBE, N_TEST = 600, 100, 100
N_PROBE_GADGETS = 40
FIXED_GADGETS = [f"gadget_{k}" for k in range(4)]
FRESH_GADGETS = 800  # 200 rooms x 4
GADGET_ACTIVATION = 0.8


def vary(proto: dict, rng: random.Random, p: float = 0.1) -> dict:
    o = dict(proto)
    for f in RULE_BINS + DISTRACTORS + ["electronic"]:
        if rng.random() < p:
            o[f] = 1 - o[f]
    if rng.random() < p:
        o["weight"] = rng.randint(1, 3)
    if rng.random() < p:
        o["shape"] = rng.choice(SHAPES)
    if rng.random() < p:
        o["size"] = rng.randint(1, 3)
    return o


def random_kinds(n: int, seed: int = 0) -> dict:
    rng = random.Random(seed)
    return {f"kind_{i:03d}": K(rng.randint(1, 3), rng.choice(SHAPES), rng.randint(1, 3),
                               *[rng.randint(0, 1) for _ in RULE_BINS + DISTRACTORS]) for i in range(n)}


WORLDS = {  # name: (kinds, room objects, probe objects, test objects)
    "small": (KINDS, 600, 100, 100),          # first gate
    "big": (random_kinds(100), 1200, 150, 150),  # second gate
}


def build_world(world: str = "small", seed: int = 0):
    """Objects are drawn once (seed 0) so every run sees the same world."""
    kinds_d, n_room, n_probe, n_test = WORLDS[world]
    rng = random.Random(seed)
    props, kind_of = {}, {}
    kinds = list(kinds_d)
    for i in range(n_room + n_probe + n_test):
        k = kinds[i % len(kinds)]
        name = f"thing_{i:04d}"
        props[name], kind_of[name] = vary(kinds_d[k], rng), k
    names = list(props)
    rng.shuffle(names)
    room_objs = sorted(names[:n_room])
    probe_objs = sorted(names[n_room:n_room + n_probe])
    test_objs = sorted(names[n_room + n_probe:])
    gadgets = FIXED_GADGETS + [f"gadget_{k}" for k in range(4, 4 + FRESH_GADGETS)]
    probe_gadgets = [f"probe_gadget_{k}" for k in range(N_PROBE_GADGETS)]
    for g in gadgets + probe_gadgets:
        props[g], kind_of[g] = vary(GADGET_KIND, rng), "gadget"
    return props, kind_of, room_objs, probe_objs, test_objs, gadgets, probe_gadgets




def is_gadget(t: str) -> bool:
    return t in GADGET_SET


def actions_for(t: str) -> list[str]:
    acts = ["push_gentle", "push_hard", "watch"]
    if PROPS[t]["size"] <= 2:
        acts += ["drop", "shake"]
    return acts


def true_outcome(t: str, action: str, surface: str, rng: random.Random) -> list[bool]:
    if is_gadget(t):
        return [rng.random() < 0.5 for _ in range(N_BITS[action])]
    p, s = PROPS[t], SURFACES[surface]
    if action.startswith("push"):
        moves = p["weight"] <= (1 if action == "push_gentle" else 2)
        return [moves, moves and p["shape"] != "none" and SMOOTH[surface], moves and s["high"]]
    if action == "drop":
        return [bool(p["hard"] and s["hard"]), bool(p["bouncy"] and s["hard"]), bool(p["breakable"] and s["hard"])]
    if action == "shake":
        return [bool(p["noisy"])]
    return [False]


def outcome(t, action, surface, rng, flip):
    bits = true_outcome(t, action, surface, rng)
    if flip and not is_gadget(t):
        bits = [b != (rng.random() < flip) for b in bits]
    return bits


def activation(t, bits):
    return GADGET_ACTIVATION if is_gadget(t) else min(0.2 * sum(bits), 0.6)


# --- graph features ----------------------------------------------------------
GRAPH_FIELDS = ["light", "heavy", "round", "tube", "wheels", "small", "big", *RULE_BINS, "electronic", *DISTRACTORS]


def field_values(p: dict) -> list[int]:
    return [p["weight"] == 1, p["weight"] == 3, p["shape"] == "round", p["shape"] == "tube",
            p["shape"] == "wheels", p["size"] == 1, p["size"] == 3] + [p[f] for f in RULE_BINS] + \
           [p["electronic"]] + [p[f] for f in DISTRACTORS]


def graph_features(error: float = 0.05, missing: float = 0.10, seed: int = 0) -> torch.Tensor:
    rng = random.Random(seed)
    rows = []
    for n in NAMES:
        row = []
        for v in field_values(PROPS[n]):
            if rng.random() < missing:
                row += [0.0, 0.0]
            else:
                v = float(v)
                if rng.random() < error:
                    v = 1 - v
                row += [2 * v - 1, 1.0]
        rows.append(row)
    return torch.tensor(rows)




# --- world model -------------------------------------------------------------
class WorldModel(nn.Module):
    """features=None: names model (32-dim slot). Else graph projection + 8-dim slot."""

    def __init__(self, feats: torch.Tensor | None, d: int = 32, slot: int = 8, hidden: int = 128):
        super().__init__()
        self.graph = feats is not None
        if self.graph:
            self.register_buffer("feats", feats)
            self.proj = nn.Linear(feats.shape[1], d - slot)
            self.slot = nn.Embedding(len(NAMES), slot)
        else:
            self.slot = nn.Embedding(len(NAMES), d)
        self.action = nn.Embedding(len(ACTIONS), d)
        self.surface = nn.Embedding(len(SURFACE_LIST), d)
        self.net = nn.Sequential(nn.Linear(3 * d, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.GELU(),
                                 nn.Linear(hidden, 3 * len(ACTIONS)))

    def thing(self, t, zero_slot=False):
        slot = self.slot(t) * (0.0 if zero_slot else 1.0)
        return torch.cat([self.proj(self.feats[t]), slot], -1) if self.graph else slot

    def forward(self, t, a, s, zero_slot=False):
        h = self.net(torch.cat([self.thing(t, zero_slot), self.action(a), self.surface(s)], -1))
        return h.view(-1, len(ACTIONS), 3)[torch.arange(len(a)), a]


AI = {a: i for i, a in enumerate(ACTIONS)}
SI = {s: i for i, s in enumerate(SURFACE_LIST)}


def encode(cases):
    t = torch.tensor([INDEX[c[0]] for c in cases])
    a = torch.tensor([AI[c[1]] for c in cases])
    s = torch.tensor([SI[c[2]] for c in cases])
    y = torch.zeros(len(cases), 3)
    m = torch.zeros(len(cases), 3)
    for i, c in enumerate(cases):
        n = N_BITS[c[1]]
        m[i, :n] = 1
        y[i, :n] = torch.tensor([float(b) for b in c[3]])
    return t, a, s, y, m


def losses(model, cases, params=None) -> torch.Tensor:
    t, a, s, y, m = encode(cases)
    logits = model(t, a, s) if params is None else torch.func.functional_call(model, params, (t, a, s))
    raw = F.binary_cross_entropy_with_logits(logits, y, reduction="none")
    return (raw * m).sum(1) / m.sum(1)


@torch.no_grad()
def accuracy(model, cases, zero_slot=False) -> float:
    """Balanced accuracy over (action, bit) with both answers present."""
    t, a, s, y, m = encode(cases)
    pred = (model(t, a, s, zero_slot) > 0).float()
    scores = []
    for act, ai in AI.items():
        rows = a == ai
        for b in range(N_BITS[act]):
            yb, pb = y[rows, b], pred[rows, b]
            if yb.sum() == 0 or yb.sum() == len(yb):
                continue
            scores.append((float((pb[yb == 1] == 1).float().mean()) + float((pb[yb == 0] == 0).float().mean())) / 2)
    return sum(scores) / len(scores)


def all_cases(things, rng):
    return [(t, a, s, true_outcome(t, a, s, rng)) for t in things for a in actions_for(t) for s in SURFACE_LIST]


# --- world setup -------------------------------------------------------------
def setup(world: str):
    global PROPS, KIND_OF, ROOM_OBJS, PROBE_OBJS, TEST_OBJS, GADGETS, PROBE_GADGETS
    global NAMES, INDEX, GADGET_SET, FEATS, PROBES, PROBE_IDX
    PROPS, KIND_OF, ROOM_OBJS, PROBE_OBJS, TEST_OBJS, GADGETS, PROBE_GADGETS = build_world(world)
    NAMES = ROOM_OBJS + PROBE_OBJS + TEST_OBJS + GADGETS + PROBE_GADGETS
    INDEX = {n: i for i, n in enumerate(NAMES)}
    GADGET_SET = set(GADGETS) | set(PROBE_GADGETS)
    FEATS = graph_features()
    PROBES = PROBE_OBJS + PROBE_GADGETS
    PROBE_IDX = torch.tensor([INDEX[p] for p in PROBES])


setup("small")


# --- neighbour transfer ------------------------------------------------------


def nearest(t: str, pool_idx: torch.Tensor, k: int = 8) -> list[int]:
    d = ((FEATS[pool_idx] - FEATS[INDEX[t]]) ** 2).sum(1)
    return d.topk(min(k, len(d)), largest=False).indices.tolist()


def stepped_copy(model, sample, step):
    names = [k for k, _ in model.named_parameters()]
    params = [p for _, p in model.named_parameters()]
    grads = torch.autograd.grad(losses(model, [sample]).mean(), params, allow_unused=True)
    stepped = {k: (p - step * (0 if g is None else g)).detach() for k, p, g in zip(names, params, grads)}
    stepped.update({k: b for k, b in model.named_buffers()})
    return stepped


def neighbour_transfer(model, sample, probe_cases, step: float = 0.05, measure: str = "loss") -> float:
    """loss: fall in neighbour loss after one step on this case alone.
    decision: neighbour answer bits going wrong->right minus right->wrong, per bit."""
    thing, action = sample[0], sample[1]
    ref = [c for j in nearest(thing, PROBE_IDX) for c in probe_cases.get((PROBES[j], action), [])]
    if not ref:
        return 0.0
    stepped = stepped_copy(model, sample, step)
    with torch.no_grad():
        if measure == "loss":
            return float(losses(model, ref).mean() - losses(model, ref, stepped).mean())
        t, a, s, y, m = encode(ref)
        before = (model(t, a, s) > 0).float() == y
        after = (torch.func.functional_call(model, stepped, (t, a, s)) > 0).float() == y
        fixed = ((~before) & after).float() * m
        broke = (before & (~after)).float() * m
        return float((fixed.sum() - broke.sum()) / m.sum())


# --- agent -------------------------------------------------------------------
ARM_RULE = {"happiness_useful": "happiness_transfer"}  # v0's name for the same score


def new_room(rng, fresh: bool, room_no: int) -> dict[str, str]:
    room = rng.choice(ROOMS)
    gadgets = GADGETS[4 + 4 * room_no: 8 + 4 * room_no] if fresh else FIXED_GADGETS
    things = rng.sample(ROOM_OBJS, 20) + list(gadgets)
    return {t: rng.choice(ROOM_SURFACES[room]) for t in things}


def choose(arm, room_regions, cache, step, rng, args):
    if arm == "random" or step <= args.warmup:
        return rng.choice(room_regions)
    raw = {k: cache.get(k) for k in room_regions}
    untried = [k for k, v in raw.items() if v is None]
    if untried and args.graph and arm != "novelty":
        by_action = {}
        for (t, a), v in cache.items():
            if v is not None:
                by_action.setdefault(a, ([], []))
                by_action[a][0].append(INDEX[t])
                by_action[a][1].append(v)
        for k in untried:
            if k[1] in by_action:
                idx, vals = by_action[k[1]]
                near = nearest(k[0], torch.tensor(idx))
                raw[k] = sum(vals[j] for j in near) / len(near)
    known = [v for v in raw.values() if v is not None]
    top = max(known) if known else 1.0
    sc = {k: (top if v is None else v) for k, v in raw.items()}
    scale = max(abs(v) for v in sc.values()) or 1.0
    exps = [math.exp(sc[k] / scale / args.temperature) for k in room_regions]
    z, n = sum(exps), len(room_regions)
    w = [(1 - args.epsilon) * e / z + args.epsilon / n for e in exps]
    return rng.choices(room_regions, weights=w, k=1)[0]


def run(arm: str, seed: int, args) -> dict:
    rng = random.Random(seed)
    env_rng = random.Random(seed * 1000 + 7)
    noise_rng = random.Random(seed * 1000 + 9)
    torch.manual_seed(seed)
    model = WorldModel(FEATS if args.graph else None)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    case_rng = random.Random(0)
    room_cases = all_cases(ROOM_OBJS, case_rng)
    test_room = case_rng.sample(room_cases, 3000)
    test_new = all_cases(TEST_OBJS, case_rng)
    probe_cases = {}
    for c in all_cases(PROBES, random.Random(1)):  # gadget probes get one fixed random draw
        probe_cases.setdefault((c[0], c[1]), []).append(c)
    regions: dict[tuple, A.Region] = {}
    cache: dict[tuple, float | None] = {}
    buffer, picks = [], Counter()
    gadget_actions = 0
    curve = []
    rule = ARM_RULE.get(arm, arm)
    measure = arm == "happiness_useful" or args.measure_transfer
    t0 = time.time()
    room_no = 0
    room = new_room(env_rng, args.fresh_gadgets, room_no)
    for step in range(1, args.actions + 1):
        if step > 1 and (step - 1) % args.episode_len == 0:
            room_no += 1
            room = new_room(env_rng, args.fresh_gadgets, room_no)
        room_regions = [(t, a) for t in room for a in actions_for(t)]
        key = choose(arm, room_regions, cache, step, rng, args)
        thing, action = key
        bits = outcome(thing, action, room[thing], noise_rng, args.flip)
        sample = (thing, action, room[thing], bits)
        r = regions.setdefault(key, A.Region())
        with torch.no_grad():
            pq = float(losses(model, [sample])[0])
            seen = float(losses(model, r.samples[-10:]).mean()) if r.samples else pq
        r.pq.append(pq)
        r.seen.append(seen)
        r.act.append(activation(thing, bits))
        r.samples.append(sample)
        if measure:
            r.cos.append(neighbour_transfer(model, sample, probe_cases, measure=args.measure))
        if arm != "random":
            cache[key] = A.region_score(rule, r, args)
        buffer.append(sample)
        picks[key] += 1
        gadget_actions += is_gadget(thing)
        batch = [sample] + rng.sample(buffer, min(len(buffer), args.batch_size - 1))
        loss = losses(model, batch).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % args.eval_every == 0:
            curve.append({"step": step, "acc": round(accuracy(model, test_room), 4),
                          "new": round(accuracy(model, test_new, zero_slot=True), 4),
                          "gadget_share": round(gadget_actions / step, 4)})
    acc = [p["acc"] for p in curve]
    transfer = {}
    for kind in ("ordinary", "gadget"):
        vals = [c for k, rr in regions.items() if is_gadget(k[0]) == (kind == "gadget") for c in rr.cos]
        if vals:
            m = sum(vals) / len(vals)
            sd = (sum((v - m) ** 2 for v in vals) / max(len(vals) - 1, 1)) ** 0.5
            transfer[kind] = {"mean": m, "se": sd / len(vals) ** 0.5, "n": len(vals)}
    n_regions = sum(len(actions_for(t)) for t in ROOM_OBJS)
    last = [p["acc"] for p in curve if p["step"] >= args.actions - 500]
    return {"arm": arm, "seed": seed, "graph": args.graph, "fresh": args.fresh_gadgets, "transfer": transfer,
            "final_acc": acc[-1], "curve_area": round(sum(acc) / len(acc), 4), "new_acc": curve[-1]["new"],
            "to85": next((p["step"] for p in curve if p["acc"] >= 0.85), None),
            "late_gain": round(last[-1] - last[0], 4),
            "regions_tried": round(sum(1 for k in picks if not is_gadget(k[0])) / n_regions, 4),
            "gadget_share": curve[-1]["gadget_share"], "seconds": round(time.time() - t0, 1), "curve": curve}


def gate(args):
    args.measure_transfer = True
    lines = ["# Acting agent v2 gate", "", f"random arm, seed 1, world {args.world}, measure {args.measure}", "",
             "| model | gadgets | ordinary transfer | gadget transfer | gap (se) | final acc | late gain | regions tried | new objects |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    checks = []
    for graph in (True, False):
        for fresh in (False, True):
            args.graph, args.fresh_gadgets = graph, fresh
            res = run("random", 1, args)
            o, g = res["transfer"]["ordinary"], res["transfer"]["gadget"]
            se = (o["se"] ** 2 + g["se"] ** 2) ** 0.5
            gap = (o["mean"] - g["mean"]) / se
            model = "graph" if graph else "names"
            cond = "B fresh" if fresh else "A fixed"
            lines.append(f"| {model} | {cond} | {o['mean']:+.5f} ± {o['se']:.5f} | {g['mean']:+.5f} ± {g['se']:.5f} | "
                         f"{gap:+.1f} | {res['final_acc']:.3f} | {res['late_gain']:+.3f} | {res['regions_tried']:.2f} | "
                         f"{res['new_acc']:.3f} |")
            print(lines[-1], f"({res['seconds']}s)", flush=True)
            if graph:
                checks.append((f"1 graph {cond}: ordinary > 0 and gap > 2 se", o["mean"] > 0 and gap > 2))
                checks.append((f"3 sizing {cond}: late gain > 0.01 and regions tried < 0.5",
                               res["late_gain"] > 0.01 and res["regions_tried"] < 0.5))
            else:
                checks.append((f"2 names {cond}: ordinary within 2 se of 0", abs(o["mean"]) < 2 * o["se"]))
    lines += ["", *[f"- {'PASS' if ok else 'fail'}: {name}" for name, ok in sorted(checks)]]
    lines.append(f"\nGate: {'PASS' if all(ok for _, ok in checks) else 'FAIL'}")
    text = "\n".join(lines)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"gate_{args.world}_{args.measure}.md").write_text(text)
    print(text)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gate", action="store_true")
    p.add_argument("--world", choices=list(WORLDS), default="big")
    p.add_argument("--measure", choices=["loss", "decision"], default="decision")
    p.add_argument("--arms", default="random,novelty,surprise,learning_progress,happiness_forget,happiness_useful")
    p.add_argument("--seeds", default="1,2,3,4,5")
    p.add_argument("--models", default="graph,names")
    p.add_argument("--conditions", default="fixed,fresh")
    p.add_argument("--actions", type=int, default=3000)
    p.add_argument("--episode-len", type=int, default=15)
    p.add_argument("--warmup", type=int, default=200)
    p.add_argument("--flip", type=float, default=0.1)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=3e-3)
    p.add_argument("--activation", type=float, default=0.02)
    p.add_argument("--temperature", type=float, default=0.3)
    p.add_argument("--epsilon", type=float, default=0.1)
    p.add_argument("--eval-every", type=int, default=100)
    p.add_argument("--out", type=Path, default=OUT)
    args = p.parse_args()
    args.measure_transfer = False
    torch.set_num_threads(1)
    setup(args.world)
    print(f"room objects {len(ROOM_OBJS)}, regions {sum(len(actions_for(t)) for t in ROOM_OBJS)}, "
          f"kinds {len(KINDS)}, graph dims {FEATS.shape[1]}")
    if args.gate:
        return gate(args)
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for model in args.models.split(","):
        for cond in args.conditions.split(","):
            args.graph, args.fresh_gadgets = model == "graph", cond == "fresh"
            for seed in [int(s) for s in args.seeds.split(",")]:
                for arm in args.arms.split(","):
                    res = run(arm, seed, args)
                    results.append(res)
                    print(f"[{model} {cond} {arm} s{seed}] area {res['curve_area']:.3f} final {res['final_acc']:.3f} "
                          f"new {res['new_acc']:.3f} to85 {res['to85']} gadget {res['gadget_share']:.3f} "
                          f"({res['seconds']}s)", flush=True)
                    (args.out / "results.json").write_text(json.dumps(results))


if __name__ == "__main__":
    main()
