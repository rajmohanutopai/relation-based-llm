#!/usr/bin/env python3
"""Do blind property answers help a world model in a physics world they had no part in?

Design: docs/independent-world-v0.md. World model as in scripts/acting_agent_v0.py.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from output_state import atomic_write_text, claim_results  # noqa: E402

WORLD = Path("data/developmental_graph/experiments/independent_world_v0/outcomes.json")
ANSWERS = Path("data/developmental_graph/independent_world_v0/answers.json")
OUT = Path("runs/independent_world_v0")
ACTIONS = ["push_gentle", "push_hard"]
SURFACES = ["slippery", "grippy"]
BITS = 3
SPLIT_SEED = 20261108
SHUFFLE_SEED = 20261109
HELD_OUT = 30


def load_world():
    world = json.loads(WORLD.read_text())["objects"]
    samples, truth = {}, {}
    for obj in world:
        for a in ACTIONS:
            for s in SURFACES:
                runs = [r for r in obj["cases"][f"{a}|{s}"] if r is not None]
                if not runs:
                    continue
                samples[(obj["name"], a, s)] = runs
                truth[(obj["name"], a, s)] = [sum(r[b] for r in runs) * 2 > len(runs) for b in range(BITS)]
    return world, samples, truth


def answer_features(names, shuffle=False):
    data = json.loads(ANSWERS.read_text())
    props = list(data["properties"])
    rows = {n: [x for p in props for x in {"yes": (1.0, 1.0), "no": (-1.0, 1.0), "unsure": (0.0, 0.0)}[data["answers"][n][p]]]
            for n in names}
    if shuffle:
        wrong = names[:]
        random.Random(SHUFFLE_SEED).shuffle(wrong)
        rows = {n: rows[w] for n, w in zip(names, wrong)}
    return torch.tensor([rows[n] for n in names])


def geometry_features(world, names):
    import math
    by = {o["name"]: o for o in world}
    rows = [[math.log(max(x, 1e-3)) for x in sorted(by[n]["size"])] + [math.log(max(by[n]["mass"], 1e-3))] for n in names]
    t = torch.tensor(rows)
    return (t - t.mean(0)) / t.std(0)


class Model(nn.Module):
    """features=None: a 32-dim learned slot only. Else projected features + an 8-dim slot."""

    def __init__(self, n, features=None, d=32, slot=8, hidden=128):
        super().__init__()
        self.features = features
        self.slot = nn.Embedding(n, d if features is None else slot)
        self.proj = None if features is None else nn.Linear(features.shape[1], d - slot)
        self.action, self.surface = nn.Embedding(len(ACTIONS), d), nn.Embedding(len(SURFACES), d)
        self.net = nn.Sequential(nn.Linear(3 * d, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.GELU(),
                                 nn.Linear(hidden, BITS * len(ACTIONS)))

    def forward(self, t, a, s):
        thing = self.slot(t) if self.features is None else torch.cat([self.proj(self.features[t]), self.slot(t)], -1)
        h = self.net(torch.cat([thing, self.action(a), self.surface(s)], -1)).view(-1, len(ACTIONS), BITS)
        return h[torch.arange(len(a)), a]


def encode(cases, index):
    return (torch.tensor([index[c[0]] for c in cases]), torch.tensor([ACTIONS.index(c[1]) for c in cases]),
            torch.tensor([SURFACES.index(c[2]) for c in cases]))


@torch.no_grad()
def accuracy(model, cases, truth, index):
    """Balanced accuracy over each (action, bit) with both answers present. Guessing scores 0.5."""
    t, a, s = encode(cases, index)
    pred = model(t, a, s) > 0
    y = torch.tensor([truth[c] for c in cases])
    scores = []
    for ai in range(len(ACTIONS)):
        rows = a == ai
        for b in range(BITS):
            yb, pb = y[rows, b], pred[rows, b]
            if yb.any() and not yb.all():
                scores.append((float(pb[yb].float().mean()) + float((~pb[~yb]).float().mean())) / 2)
    return sum(scores) / len(scores)


def run(arm, seed, world, samples, truth, train, held, actions=3000, episode=20):
    names = train + held
    index = {n: i for i, n in enumerate(names)}
    features = {"names": None, "answers": answer_features(names), "answers_shuffled": answer_features(names, True),
                "geometry": geometry_features(world, names)}[arm]
    rng = random.Random(seed)
    torch.manual_seed(seed)
    model = Model(len(names), features)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=0.01)
    train_cases = [c for c in truth if c[0] in set(train)]
    new_cases = [c for c in truth if c[0] in set(held)]
    buffer, curve = [], []
    room = {}
    for step in range(1, actions + 1):
        if (step - 1) % episode == 0:
            room = {t: rng.choice(SURFACES) for t in rng.sample(train, 6)}
        t = rng.choice(list(room))
        case = (t, rng.choice(ACTIONS), room[t])
        if case not in samples:
            continue
        buffer.append((case, rng.choice(samples[case])))
        batch = [buffer[-1]] + rng.sample(buffer, min(len(buffer), 31))
        ta, aa, sa = encode([c for c, _ in batch], index)
        loss = F.binary_cross_entropy_with_logits(model(ta, aa, sa), torch.tensor([b for _, b in batch], dtype=torch.float))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % 50 == 0:
            curve.append(accuracy(model, train_cases, truth, index))
    with torch.no_grad():
        for n in held:
            model.slot.weight[index[n]] = 0.0
    return {"arm": arm, "seed": seed, "curve_area": sum(curve) / len(curve), "final": curve[-1],
            "new": accuracy(model, new_cases, truth, index), "steps_to_80": next((50 * (i + 1) for i, v in enumerate(curve) if v >= 0.8), None)}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--seeds", default="1,2,3,4,5")
    p.add_argument("--overwrite", action="store_true")
    cli = p.parse_args()
    torch.set_num_threads(1)
    world, samples, truth = load_world()
    names = sorted(o["name"] for o in world)
    held = sorted(random.Random(SPLIT_SEED).sample(names, HELD_OUT))
    train = [n for n in names if n not in set(held)]
    path = cli.out / "results.json"
    claim_results(path, cli.overwrite)
    results = []
    for seed in [int(s) for s in cli.seeds.split(",")]:
        for arm in ("names", "answers", "answers_shuffled", "geometry"):
            r = run(arm, seed, world, samples, truth, train, held)
            results.append(r)
            print(arm, seed, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k not in ("arm", "seed")}, flush=True)
            atomic_write_text(path, json.dumps(results))


if __name__ == "__main__":
    main()
