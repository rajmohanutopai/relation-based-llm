#!/usr/bin/env python3
"""Acting agent v0: does the plan.md happiness rule, used as an agent's only
reward, build a better world model sooner than surprise, novelty, pleasure or
chance?

Design: docs/acting-agent-v0-design.md

The world uses the world_sim v0/v1 rules without text. Each episode is one
room with 6 ordinary things (train objects) and some gadgets (TV, blinking
toy, music box) on random surfaces. The agent picks a (thing, action) pair,
sees the outcome bits, and its world model trains on it. Gadgets answer every
action with random bits, so nothing about them can be learned.

Actions and outcome bits:
  push_gentle, push_hard -> moves, rolls, falls   (push_outcome_v1)
  drop                   -> loud, bounce, breaks  (drop_outcome; things of size <= 2)
  shake                  -> sound                 (noisy flag; things of size <= 2)
  watch                  -> change                (always 0 for ordinary things)

The world model sees the thing's name, the action and the surface, and never
the thing's properties.

Arms (only the region reward differs; a region is one (thing, action) pair):
  random                  uniform over the room's pairs
  surprise                mean prequential loss over the last 10 tries
  novelty                 1 / sqrt(tries + 1)
  pleasure                mean outcome activation (lights, sound, motion)
  happiness               activation + gain - loss - shortcut   (plan.md)
  happiness_no_shortcut   activation + gain - loss
  happiness_pleasure      activation + gain - loss - activation * (1 - strength)
                          (shortcut read as pleasure from what can't be predicted)
  happiness_noact         gain - loss
  happiness_forget        as happiness_pleasure, with loss = rise in loss on the
                          region's earlier cases (forgetting)
  happiness_useful        as happiness_forget, with gain scaled by how well the
                          lesson carries over (gradient agreement with other
                          regions' cases)
  happiness_transfer      activation + useful gain - forget - shortcut, where
                          useful gain = fall in other regions' loss after one
                          step on this case alone, x (1 - strength)
  learning_progress       max(fall in prequential loss, 0): no saturation weight,
                          no loss term, no shortcut, no activation

Prequential loss: the world model's loss on a new outcome before it trains on
it, so it is always a loss on unseen data.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_world_sim_v1 as wv1  # noqa: E402

v0 = wv1.v0
OBJECTS, WEIGHT, SURFACES, ROOM_SURFACES = wv1.OBJECTS, wv1.WEIGHT, v0.SURFACES, v0.ROOM_SURFACES
TRAIN_OBJECTS = [w for w in OBJECTS if w not in v0.HELD_OUT_CANDIDATES]
GADGETS = ["tv", "blinking toy", "music box"]
GADGET_ACTIONS = {"tv": ["watch", "push_gentle", "push_hard"],
                  "blinking toy": ["watch", "push_gentle", "push_hard", "shake", "drop"],
                  "music box": ["watch", "push_gentle", "push_hard", "shake", "drop"]}
ACTIONS = ["push_gentle", "push_hard", "drop", "shake", "watch"]
N_BITS = {"push_gentle": 3, "push_hard": 3, "drop": 3, "shake": 1, "watch": 1}
SURFACE_LIST = list(SURFACES)
MAX_GADGET_COPIES = 400  # fresh-gadget mode gives each room new gadget names: "tv#17"
NAMES = TRAIN_OBJECTS + [f"{g}#{k}" for g in GADGETS for k in range(MAX_GADGET_COPIES)]


def is_gadget(thing: str) -> bool:
    return "#" in thing


def gadget_base(thing: str) -> str:
    return thing.split("#")[0]
GADGET_ACTIVATION = 0.8  # same as the feel_shortcut "shortcut" kind in world_sim_v1
OUT = Path("runs/acting_agent_v0")


def actions_for(thing: str) -> list[str]:
    if is_gadget(thing):
        return GADGET_ACTIONS[gadget_base(thing)]
    acts = ["push_gentle", "push_hard", "watch"]
    if OBJECTS[thing]["size"] <= 2:
        acts += ["drop", "shake"]
    return acts


def outcome(thing: str, action: str, surface: str, rng: random.Random, flip: float = 0.0) -> list[int]:
    """Outcome bits. With flip > 0, each bit of an ordinary thing is flipped with
    that chance (a baby's push or drop is never quite the same twice)."""
    bits = true_outcome(thing, action, surface, rng)
    if flip and not is_gadget(thing):
        bits = [b != (rng.random() < flip) for b in bits]
    return bits


def true_outcome(thing: str, action: str, surface: str, rng: random.Random) -> list[int]:
    n = N_BITS[action]
    if is_gadget(thing):
        return [rng.random() < 0.5 for _ in range(n)]
    if action.startswith("push"):
        r = wv1.push_outcome_v1(thing, surface, 1 if action == "push_gentle" else 2)
        return [r["moves"][0], r["rolls"][0], r["falls"][0]]
    if action == "drop":
        r = v0.drop_outcome(thing, surface)
        return [r["loud"][0], r["bounce"][0], r["break"][0]]
    if action == "shake":
        return [OBJECTS[thing]["noisy"]]
    return [False]  # watch: an ordinary thing does nothing by itself


def activation(thing: str, bits: list[int]) -> float:
    """Raw pleasure of an outcome: lights, sound, motion."""
    if is_gadget(thing):
        return GADGET_ACTIVATION
    return min(0.2 * sum(bits), 0.6)


def test_cases() -> list[tuple[str, str, str]]:
    """Every learnable (thing, action, surface) case, weighted equally."""
    return [(t, a, s) for t in TRAIN_OBJECTS for a in actions_for(t) for s in SURFACE_LIST]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


class WorldModel(nn.Module):
    def __init__(self, d: int = 32, hidden: int = 128):
        super().__init__()
        self.thing = nn.Embedding(len(NAMES), d)
        self.action = nn.Embedding(len(ACTIONS), d)
        self.surface = nn.Embedding(len(SURFACE_LIST), d)
        self.net = nn.Sequential(nn.Linear(3 * d, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.GELU(),
                                 nn.Linear(hidden, 3 * len(ACTIONS)))

    def forward(self, t, a, s):
        h = self.net(torch.cat([self.thing(t), self.action(a), self.surface(s)], -1))
        h = h.view(-1, len(ACTIONS), 3)
        return h[torch.arange(len(a)), a]  # 3 logits for the chosen action


def make_world_model(args) -> nn.Module:
    return WorldModel()


def encode(cases):
    t = torch.tensor([NAMES.index(c[0]) for c in cases])
    a = torch.tensor([ACTIONS.index(c[1]) for c in cases])
    s = torch.tensor([SURFACE_LIST.index(c[2]) for c in cases])
    y = torch.zeros(len(cases), 3)
    m = torch.zeros(len(cases), 3)
    for i, c in enumerate(cases):
        n = N_BITS[c[1]]
        m[i, :n] = 1
        if len(c) > 3:
            y[i, :n] = torch.tensor([float(b) for b in c[3]])
    return t, a, s, y, m


def losses(model, cases) -> torch.Tensor:
    t, a, s, y, m = encode(cases)
    raw = F.binary_cross_entropy_with_logits(model(t, a, s), y, reduction="none")
    return (raw * m).sum(1) / m.sum(1)


@torch.no_grad()
def accuracy(model, cases, truth) -> float:
    """Balanced accuracy: for each (action, bit) with both answers present, the
    mean of the hit rate on true cases and on false cases; then the mean over
    those bits. Guessing "nothing happens" scores 0.5."""
    t, a, s, y, m = encode([c + (truth[c],) for c in cases])
    pred = (model(t, a, s) > 0).float()
    scores = []
    for ai, act in enumerate(ACTIONS):
        rows = a == ai
        for b in range(N_BITS[act]):
            yb, pb = y[rows, b], pred[rows, b]
            if yb.sum() == 0 or yb.sum() == len(yb):
                continue
            tpr = float((pb[yb == 1] == 1).float().mean())
            tnr = float((pb[yb == 0] == 0).float().mean())
            scores.append((tpr + tnr) / 2)
    return sum(scores) / len(scores)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class Region:
    def __init__(self):
        self.pq: list[float] = []    # prequential (unseen) loss at each try
        self.seen: list[float] = []  # loss on this region's earlier samples, at each try
        self.act: list[float] = []
        self.samples: list[tuple] = []
        self.cos: list[float] = []   # gradient agreement with other regions' cases


def windows(xs: list[float], k: int = 10) -> tuple[float, float]:
    """Mean of the older and newer halves of the last 2k values."""
    recent = xs[-2 * k:]
    half = len(recent) // 2
    return sum(recent[:half]) / half, sum(recent[half:]) / (len(recent) - half)


def region_score(arm: str, r: Region, args) -> float | None:
    """None means untried or too few tries: the caller gives it the top score."""
    if arm == "novelty":
        return 1 / math.sqrt(len(r.pq) + 1)
    if len(r.pq) < 2:
        return None
    if arm == "surprise":
        return sum(r.pq[-10:]) / len(r.pq[-10:])
    if arm == "pleasure":
        return sum(r.act[-10:]) / len(r.act[-10:])
    before, now = windows(r.pq)
    fall = before - now
    if arm == "learning_progress":  # plain learning progress (Oudeyer et al. 2007)
        return max(fall, 0.0)
    s_now, s_before = math.exp(-now), math.exp(-before)
    gain = max(fall, 0.0) * (1 - s_now)
    loss = max(-fall, 0.0) * s_before
    act = args.activation * sum(r.act[-10:]) / len(r.act[-10:])
    if arm == "happiness_noact":
        return gain - loss
    score = act + gain - loss
    if arm == "happiness":  # shortcut = memorized but not learned
        sb, sn = windows(r.seen)
        score -= max((sb - sn) - fall, 0.0)
    elif arm == "happiness_pleasure":  # shortcut = pleasure from what the agent can't predict
        score -= act * (1 - s_now)
    elif arm == "happiness_useful":
        # Gain counts only as far as it carries over to other regions.
        sb, sn = windows(r.seen)
        forget = max(sn - sb, 0.0) * math.exp(-sb)
        cos = r.cos[-10:]
        useful = max(sum(cos) / len(cos), 0.0) if cos else 0.0
        score = act + gain * useful - forget - act * (1 - s_now)
    elif arm == "happiness_transfer":
        # Useful gain = how much learning this region's cases lowered the loss
        # elsewhere (direct one-step test), weighted by how new the region is.
        sb, sn = windows(r.seen)
        forget = max(sn - sb, 0.0) * math.exp(-sb)
        tr = r.cos[-10:]
        useful_gain = max(sum(tr) / len(tr), 0.0) * (1 - s_now) if tr else 0.0
        score = act + useful_gain - forget - act * (1 - s_now)
    elif arm == "happiness_forget":
        # Same as happiness_pleasure, but connection loss means forgetting: a rise
        # in loss on this region's earlier cases (already trained on), not one
        # unlucky new outcome.
        sb, sn = windows(r.seen)
        forget = max(sn - sb, 0.0) * math.exp(-sb)
        score = act + gain - forget - act * (1 - s_now)
    return score


def group_of(key: tuple, args) -> tuple:
    """The unit that gets a score: one (thing, action) pair, or (kind, action)."""
    if args.group == "region":
        return key
    thing, action = key
    return ("gadget" if is_gadget(thing) else OBJECTS[thing]["kind"], action)


def transfer_cos(model, sample, buffer, key, rng, n: int = 64) -> float:
    """Would learning this outcome help predict other things? Cosine between the
    loss gradient of this one case and that of up to n recent cases from other
    regions. Positive: the lesson carries over. Near zero or negative: it
    doesn't."""
    others = [x for x in buffer[-500:] if (x[0], x[1]) != key]
    if not others:
        return 0.0
    ref = rng.sample(others, min(n, len(others)))
    params = [p for p in model.parameters() if p.requires_grad]
    g1 = torch.autograd.grad(losses(model, [sample]).mean(), params)
    g2 = torch.autograd.grad(losses(model, ref).mean(), params)
    a = torch.cat([x.flatten() for x in g1])
    b = torch.cat([x.flatten() for x in g2])
    return float(torch.dot(a, b) / (a.norm() * b.norm() + 1e-12))


def transfer_direct(model, sample, buffer, key, rng, n: int = 64, step: float = 0.05) -> float:
    """Direct test of carry-over: take one plain gradient step on this case alone
    (on a copy of the weights) and measure how much the loss on up to n recent
    cases from other regions falls. The real model is not changed."""
    others = [x for x in buffer[-500:] if (x[0], x[1]) != key]
    if not others:
        return 0.0
    ref = rng.sample(others, min(n, len(others)))
    names = [k for k, _ in model.named_parameters()]
    params = [p for _, p in model.named_parameters()]
    grads = torch.autograd.grad(losses(model, [sample]).mean(), params, allow_unused=True)
    grads = [torch.zeros_like(p) if g is None else g for p, g in zip(params, grads)]
    stepped = {k: (p - step * g).detach() for k, p, g in zip(names, params, grads)}
    with torch.no_grad():
        before = float(losses(model, ref).mean())
        after = float(losses_with(model, stepped, ref).mean())
    return before - after


def losses_with(model, params: dict, cases) -> torch.Tensor:
    t, a, s, y, m = encode(cases)
    logits = torch.func.functional_call(model, params, (t, a, s))
    raw = F.binary_cross_entropy_with_logits(logits, y, reduction="none")
    return (raw * m).sum(1) / m.sum(1)


def choose(arm, room_regions, stats, step, rng, args):
    if arm == "random" or step <= args.warmup:
        return rng.choice(room_regions)
    groups = {group_of(k, args) for k in room_regions}
    gscore = {g: region_score(arm, stats[g], args) for g in groups}
    raw = {k: gscore[group_of(k, args)] for k in room_regions}
    known = [v for v in raw.values() if v is not None]
    top = max(known) if known else 1.0
    sc = {k: (top if v is None else v) for k, v in raw.items()}
    scale = max(abs(v) for v in sc.values()) or 1.0
    exps = [math.exp(sc[k] / scale / args.temperature) for k in room_regions]
    z, n = sum(exps), len(room_regions)
    w = [(1 - args.epsilon) * e / z + args.epsilon / n for e in exps]
    return rng.choices(room_regions, weights=w, k=1)[0]


def new_room(rng: random.Random, n_gadgets: int, copy: int = 0) -> dict[str, str]:
    """copy = 0 reuses the same three gadgets; fresh mode passes a new copy number
    for each room, so every room's gadgets are things the agent has never met."""
    room = rng.choice(v0.ROOMS)
    things = rng.sample(TRAIN_OBJECTS, 6) + [f"{g}#{copy}" for g in rng.sample(GADGETS, n_gadgets)]
    return {t: rng.choice(ROOM_SURFACES[room]) for t in things}


def run(arm: str, seed: int, args) -> dict:
    rng = random.Random(seed)
    env_rng = random.Random(seed * 1000 + 7)  # same rooms for every arm
    noise_rng = random.Random(seed * 1000 + 9)
    ref_rng = random.Random(seed * 1000 + 11)  # only the useful arm draws from it
    torch.manual_seed(seed)
    model = make_world_model(args)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    cases = test_cases()
    truth = {c: true_outcome(*c, rng=noise_rng) for c in cases}  # the rule, without flips
    regions: dict[tuple, Region] = defaultdict(Region)
    stats: dict[tuple, Region] = defaultdict(Region)
    buffer: list[tuple] = []
    picks = Counter()
    gadget_actions = known_actions = 0
    curve = []
    t0 = time.time()
    room_no = 0
    f = args.flip
    floor = 0.0 if f == 0 else -(f * math.log(f) + (1 - f) * math.log(1 - f))  # best possible loss
    room = new_room(env_rng, args.gadgets)
    for step in range(1, args.actions + 1):
        if step > 1 and (step - 1) % args.episode_len == 0:
            room_no += 1
            room = new_room(env_rng, args.gadgets, room_no % MAX_GADGET_COPIES if args.fresh_gadgets else 0)
        room_regions = [(t, a) for t in room for a in actions_for(t)]
        key = choose(arm, room_regions, stats, step, rng, args)
        thing, action = key
        surface = room[thing]
        bits = outcome(thing, action, surface, noise_rng, args.flip)
        sample = (thing, action, surface, bits)
        r = regions[key]
        g = stats[group_of(key, args)]
        with torch.no_grad():
            pq = float(losses(model, [sample])[0])
            seen = float(losses(model, g.samples[-10:]).mean()) if g.samples else pq
        if len(r.pq) >= 2 and sum(r.pq[-10:]) / len(r.pq[-10:]) < floor + 0.05:
            known_actions += 1
        r.pq.append(pq)
        r.seen.append(seen)
        r.act.append(activation(thing, bits))
        r.samples.append(sample)
        if g is not r:
            g.pq.append(pq)
            g.seen.append(seen)
            g.act.append(r.act[-1])
            g.samples.append(sample)
        if arm in ("happiness_useful", "happiness_transfer") or getattr(args, "measure_transfer", False):
            c = (transfer_cos if arm == "happiness_useful" else transfer_direct)(model, sample, buffer, key, ref_rng)
            r.cos.append(c)
            if g is not r:
                g.cos.append(c)
        buffer.append(sample)
        picks[key] += 1
        gadget_actions += is_gadget(thing)
        batch = [sample] + rng.sample(buffer, min(len(buffer), args.batch_size - 1))
        loss = losses(model, batch).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % args.eval_every == 0:
            point = {"step": step, "acc": round(accuracy(model, cases, truth), 4),
                     "gadget_share": round(gadget_actions / step, 4),
                     "known_share": round(known_actions / step, 4)}
            curve.append(point)
    by_action = Counter()
    for (t, a), n in picks.items():
        by_action["gadget" if is_gadget(t) else a] += n
    acc = [p["acc"] for p in curve]
    reach90 = next((p["step"] for p in curve if p["acc"] >= 0.9), None)
    transfer = {}
    for kind in ("ordinary", "gadget"):
        vals = [c for k, r in regions.items() if is_gadget(k[0]) == (kind == "gadget") for c in r.cos]
        if vals:
            m = sum(vals) / len(vals)
            sd = (sum((v - m) ** 2 for v in vals) / max(len(vals) - 1, 1)) ** 0.5
            transfer[kind] = {"mean": m, "se": sd / len(vals) ** 0.5, "n": len(vals)}
    result = {"arm": arm, "seed": seed, "gadgets": args.gadgets, "transfer": transfer, "final_acc": acc[-1],
              "curve_area": round(sum(acc) / len(acc), 4), "steps_to_90": reach90,
              "gadget_share": curve[-1]["gadget_share"], "known_share": curve[-1]["known_share"],
              "pick_by_action": {k: round(v / args.actions, 4) for k, v in sorted(by_action.items())},
              "regions_tried": len(picks), "seconds": round(time.time() - t0, 1), "curve": curve}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arms", default="random,surprise,novelty,pleasure,happiness,happiness_no_shortcut,happiness_pleasure,happiness_noact")
    p.add_argument("--seeds", default="1,2,3,4,5")
    p.add_argument("--gadgets", default="2", help="comma list for the sweep, e.g. 0,1,2,3")
    p.add_argument("--actions", type=int, default=3000)
    p.add_argument("--episode-len", type=int, default=20)
    p.add_argument("--warmup", type=int, default=200)
    p.add_argument("--flip", type=float, default=0.0, help="chance each ordinary outcome bit is flipped")
    p.add_argument("--fresh-gadgets", action="store_true", help="new gadget names in every room")
    p.add_argument("--group", choices=["region", "kind"], default="region",
                   help="score each (thing, action) pair, or pool by (kind of thing, action)")
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=3e-3)
    p.add_argument("--activation", type=float, default=0.02)
    p.add_argument("--temperature", type=float, default=0.3)
    p.add_argument("--epsilon", type=float, default=0.1)
    p.add_argument("--eval-every", type=int, default=50)
    p.add_argument("--out", type=Path, default=OUT)
    args = p.parse_args()
    torch.set_num_threads(1)
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"train objects {len(TRAIN_OBJECTS)}, test cases {len(test_cases())}")
    results = []
    for g in [int(x) for x in args.gadgets.split(",")]:
        args.gadgets = g
        for seed in [int(s) for s in args.seeds.split(",")]:
            for arm in args.arms.split(","):
                res = run(arm, seed, args)
                results.append(res)
                print(f"[g{g} {arm} s{seed}] acc {res['final_acc']:.3f} area {res['curve_area']:.3f} "
                      f"to90 {res['steps_to_90']} gadget {res['gadget_share']:.3f} known {res['known_share']:.3f} "
                      f"({res['seconds']}s)", flush=True)
    (args.out / "results.json").write_text(json.dumps(results, indent=1))
    lines = ["# Acting agent v0 results", "",
             f"actions {args.actions}, episode {args.episode_len}, warm-up {args.warmup}, seeds {args.seeds}, "
             f"flip {args.flip}, fresh gadgets {args.fresh_gadgets}, group {args.group}", ""]
    for g in sorted({r["gadgets"] for r in results}):
        lines += [f"## {g} gadgets per room", "",
                  "| arm | final acc | curve area | steps to 90% | gadget share | known share | wins vs random (area) |",
                  "|---|---:|---:|---:|---:|---:|---:|"]
        rs = [r for r in results if r["gadgets"] == g]
        rand = {r["seed"]: r["curve_area"] for r in rs if r["arm"] == "random"}
        for arm in args.arms.split(","):
            a = [r for r in rs if r["arm"] == arm]
            mean = lambda k: sum(r[k] for r in a) / len(a)
            to90 = [r["steps_to_90"] for r in a if r["steps_to_90"] is not None]
            to90s = f"{sum(to90) / len(to90):.0f} ({len(to90)}/{len(a)})" if to90 else "never"
            wins = sum(r["curve_area"] > rand.get(r["seed"], 9) for r in a) if rand else 0
            lines.append(f"| {arm} | {mean('final_acc'):.3f} | {mean('curve_area'):.3f} | {to90s} | "
                         f"{mean('gadget_share'):.3f} | {mean('known_share'):.3f} | {wins}/{len(a)} |")
        lines.append("")
    text = "\n".join(lines)
    (args.out / "summary.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
