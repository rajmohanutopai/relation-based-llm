#!/usr/bin/env python3
"""Acting agent v3: explicit connections, happiness and sadness as the theory
states them.

Design: docs/acting-agent-v3-design.md

World: the v2 "big" world (scripts/acting_agent_v2.py). Knowledge is a store of
connections, each predicting one outcome bit:
  specific  (thing, action, surface) -> bit
  general   (thing feature, action, surface feature) -> bit, formed only once
            >= 3 things with that feature tried it >= 2 times and agree
Strength s = n / (n + 5). Happiness of a try = sum over touched links of
(rise in s) x (1 - s before); a new general link counts its whole starting
strength; a specific link's gain is also x (1 - strongest matching general
link). Sadness = sum of s before x miss.

  --gate               gate checks (random arm, seed 1, fixed gadgets)
  --suite main|shape|grief|all
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_agent_v2 as W  # noqa: E402
from output_state import atomic_write_text, claim_results  # noqa: E402

W.setup("big")
A = W.A  # v0, for windows()
OUT = Path("runs/acting_agent_v3")
K = 5.0
DECAY = 0.99
MIN_THINGS, MIN_TRIES, MAX_SPREAD = 3, 2, 0.25
ELECTRONIC = W.GRAPH_FIELDS.index("electronic")
SURF_FEATS = {s: [(0, v["high"]), (1, v["hard"]), (2, W.SMOOTH[s])] for s, v in W.SURFACES.items()}
THING_FEATS = {}
COMBOS = {}  # each thing's known features, singly and in pairs
for n in W.NAMES:
    row = W.FEATS[W.INDEX[n]]
    fs = [(j, bool(row[2 * j] > 0)) for j in range(len(W.GRAPH_FIELDS)) if row[2 * j + 1] > 0]
    THING_FEATS[n] = fs
    COMBOS[n] = [(f,) for f in fs] + [(f, g) for i, f in enumerate(fs) for g in fs[i + 1:]]


class Link:
    __slots__ = ("a", "n", "recent", "usual")

    def __init__(self, a=0.0, n=0.0):
        self.a, self.n = a, n
        self.recent = self.usual = 0.0

    def hurt(self, y):
        """v3.1 sadness: strength x how far recent misses exceed the usual rate."""
        m = miss(self.p, y)
        self.recent += 0.1 * (m - self.recent)
        self.usual += 0.01 * (m - self.usual)
        return self.s * max(0.0, self.recent - self.usual - 0.1)

    @property
    def p(self):
        return (self.a + 1) / (self.n + 2)

    @property
    def s(self):
        return self.n / (self.n + K)

    def add(self, y):
        self.a = self.a * DECAY + y
        self.n = self.n * DECAY + 1


def strength(n):
    return n / (n + K)


def miss(p, y):
    return max(0.0, abs(y - p) - 0.5) * 2


class Store:
    def __init__(self):
        self.spec: dict[tuple, Link] = {}
        self.gen: dict[tuple, Link] = {}
        self.cand: dict[tuple, dict[str, Link]] = {}
        self.fails: Counter = Counter()  # v3.1: promised groks that didn't come

    def gen_keys(self, t, action, surface, b):
        return [(c, action, k, sv, b) for c in COMBOS[t] for k, sv in SURF_FEATS[surface]]

    def predict(self, t, action, surface, b):
        """The strongest, surest matching link gives the estimate (specific
        links count 3 times). No links: 50/50."""
        best, p = 0.0, 0.5
        L = self.spec.get((t, action, surface, b))
        if L is not None:
            best, p = 3 * L.s * abs(2 * L.p - 1), L.p
        for key in self.gen_keys(t, action, surface, b):
            G = self.gen.get(key)
            if G is not None:
                w = G.s * abs(2 * G.p - 1)
                if w > best:
                    best, p = w, G.p
        return p

    def update(self, t, action, surface, bits):
        """Apply one outcome; return (happiness, sadness, general links formed)."""
        happy = sad = 0.0
        formed = 0
        for b, y in enumerate(bits):
            y = float(y)
            cover = 0.0
            for key in self.gen_keys(t, action, surface, b):
                G = self.gen.get(key)
                if G is not None:
                    s0 = G.s
                    sad += G.hurt(y)
                    cover = max(cover, s0)
                    G.add(y)
                    happy += (G.s - s0) * (1 - s0)
                    continue
                members = self.cand.setdefault(key, {})
                m = members.setdefault(t, Link())
                m.add(y)
                ready = [x for x in members.values() if x.n >= MIN_TRIES * DECAY ** 3]
                if len(ready) >= MIN_THINGS and m in ready:
                    ps = [x.p for x in ready]
                    if max(ps) - min(ps) <= MAX_SPREAD:
                        G = Link(sum(x.a for x in members.values()), sum(x.n for x in members.values()))
                        self.gen[key] = G
                        del self.cand[key]
                        happy += G.s
                        formed += 1
                    else:
                        self.fails[key] += 1
            L = self.spec.setdefault((t, action, surface, b), Link())
            s0 = L.s
            if L.n > 0:
                sad += L.hurt(y)
            L.add(y)
            happy += (L.s - s0) * (1 - s0) * (1 - cover)
        return happy, sad, formed

    def expected_happiness(self, t, action, surface):
        total = 0.0
        for b in range(W.N_BITS[action]):
            cover = 0.0
            for key in self.gen_keys(t, action, surface, b):
                G = self.gen.get(key)
                if G is not None:
                    cover = max(cover, G.s)
                    total += (strength(G.n * DECAY + 1) - G.s) * (1 - G.s)
                    continue
                members = self.cand.get(key)
                if not members:
                    continue
                others = [x for k2, x in members.items() if k2 != t and x.n >= MIN_TRIES * DECAY ** 3]
                mine = members.get(t)
                if len(others) >= MIN_THINGS - 1 and mine is not None and mine.n * DECAY + 1 >= MIN_TRIES * DECAY ** 3:
                    ps = [x.p for x in others]
                    if max(ps) - min(ps) <= MAX_SPREAD:
                        total += strength(sum(x.n for x in members.values()) + 1) / (2 + self.fails[key])
            L = self.spec.get((t, action, surface, b))
            n = L.n if L else 0.0
            s0 = strength(n)
            total += (strength(n * DECAY + 1) - s0) * (1 - s0) * (1 - cover)
        return total


def balanced_accuracy(store, cases):
    by = {}
    for t, a, s, bits in cases:
        for b, y in enumerate(bits):
            pred = store.predict(t, a, s, b) > 0.5
            d = by.setdefault((a, b), [0, 0, 0, 0])  # true-pos, pos, true-neg, neg
            if y:
                d[0] += pred
                d[1] += 1
            else:
                d[2] += not pred
                d[3] += 1
    scores = [(d[0] / d[1] + d[2] / d[3]) / 2 for d in by.values() if d[1] and d[3]]
    return sum(scores) / len(scores)


CHANGE_STEP = 2000
SMALL_CHANGE = next(t for t in W.ROOM_OBJS if W.PROPS[t]["bouncy"] and W.PROPS[t]["size"] <= 2)
CHANGE_RNG = random.Random(4242)
SMALL_LIGHT = next(t for t in W.ROOM_OBJS if W.PROPS[t]["weight"] == 1)


def affected(t, action, step, change):
    if step <= CHANGE_STEP or W.is_gadget(t):
        return False
    if change in ("light_big", "light_small"):
        return action.startswith("push") and W.PROPS[t]["weight"] == 1 and (change == "light_big" or t == SMALL_LIGHT)
    return False


def outcome(t, action, surface, rng, flip, step, change):
    bits = W.outcome(t, action, surface, rng, flip)
    if action == "drop" and step > CHANGE_STEP and not W.is_gadget(t):
        if (change == "big" and W.PROPS[t]["bouncy"]) or (change == "small" and t == SMALL_CHANGE):
            bits[1] = False
    if affected(t, action, step, change):
        # a light thing that no longer moves; the usual 10% flips still apply
        bits = [CHANGE_RNG.random() < flip for _ in range(3)]  # own source keeps runs matched
    return bits


def model_score(arm, store, t, a, surface):
    if arm == "happiness":
        return store.expected_happiness(t, a, surface)
    ps = [store.predict(t, a, surface, b) for b in range(W.N_BITS[a])]
    return sum(1 - abs(2 * p - 1) for p in ps) / len(ps)  # surprise: uncertainty


def choose(arm, store, room, regions, tries, err_hist, step, rng, args, hcache=None):
    if arm == "random" or step <= args.warmup:
        return rng.choice(regions)
    raw = {}
    for key in regions:
        t, a = key
        if arm == "novelty":
            raw[key] = 1 / math.sqrt(tries[key] + 1)
        elif arm == "surprise":
            raw[key] = hcache[key]
        elif arm == "learning_progress":
            e = err_hist.get(key, [])
            if len(e) < 2:
                raw[key] = None
            else:
                before, now = A.windows(e)
                raw[key] = max(before - now, 0.0)
        elif arm == "happiness":
            raw[key] = hcache[key]
    known = [v for v in raw.values() if v is not None]
    top = max(known) if known else 1.0
    sc = {k: (top if v is None else v) for k, v in raw.items()}
    scale = max(abs(v) for v in sc.values()) or 1.0
    exps = [math.exp(sc[k] / scale / args.temperature) for k in regions]
    z, n = sum(exps), len(regions)
    w = [(1 - args.epsilon) * e / z + args.epsilon / n for e in exps]
    return rng.choices(regions, weights=w, k=1)[0]


def run(arm, seed, args, fresh=False, change="none"):
    global CHANGE_RNG
    CHANGE_RNG = random.Random(4242)  # fresh per run, so a run doesn't depend on earlier ones
    rng = random.Random(seed)
    env_rng = random.Random(seed * 1000 + 7)
    noise_rng = random.Random(seed * 1000 + 9)
    case_rng = random.Random(0)
    room_cases = W.all_cases(W.ROOM_OBJS, case_rng)
    test_room = case_rng.sample(room_cases, 3000)
    test_new = W.all_cases(W.TEST_OBJS, case_rng)
    store = Store()
    hcache = {}
    tries, err_hist = Counter(), {}
    log, curve = [], []
    t0 = time.time()
    room_no = 0
    room = W.new_room(env_rng, fresh, room_no)
    for step in range(1, args.actions + 1):
        if step > 1 and (step - 1) % args.episode_len == 0:
            room_no += 1
            room = W.new_room(env_rng, fresh, room_no)
        regions = [(t, a) for t in room for a in W.actions_for(t)]
        cached = arm in ("happiness", "surprise")
        if cached and (step > args.warmup and (step - 1) % args.episode_len == 0 or step == args.warmup + 1):
            # Expected happiness for the whole room, worked out at room start;
            # after each try only the tried thing's choices are redone.
            hcache = {k: model_score(arm, store, k[0], k[1], room[k[0]]) for k in regions}
        key = choose(arm, store, room, regions, tries, err_hist, step, rng, args, hcache)
        t, a = key
        bits = outcome(t, a, room[t], noise_rng, args.flip, step, change)
        err = sum(abs(float(y) - store.predict(t, a, room[t], b)) for b, y in enumerate(bits)) / len(bits)
        err_hist.setdefault(key, []).append(err)
        happy, sad, formed = store.update(t, a, room[t], bits)
        tries[key] += 1
        if cached and step > args.warmup:
            for k in regions:
                if k[0] == t:
                    hcache[k] = model_score(arm, store, t, k[1], room[t])
        log.append((round(happy, 5), round(sad, 5), formed, int(W.is_gadget(t)), int(affected(t, a, step, change))))
        if step % args.eval_every == 0:
            curve.append({"step": step, "acc": round(balanced_accuracy(store, test_room), 4),
                          "new": round(balanced_accuracy(store, test_new), 4)})
    acc = [p["acc"] for p in curve]
    if hasattr(store, "sweep"):
        store.sweep()  # links that faded since last touched mustn't count as formed links
    gadget_formed = sum(1 for k in store.gen if (ELECTRONIC, True) in k[0])
    return {"arm": arm, "seed": seed, "fresh": fresh, "change": change, "curve_area": round(sum(acc) / len(acc), 4),
            "final_acc": acc[-1], "new_acc": curve[-1]["new"], "general_links": len(store.gen),
            "gadget_general_links": gadget_formed, "seconds": round(time.time() - t0, 1), "curve": curve, "log": log}


def span(log, lo, hi, i):
    xs = [r[i] for r in log[lo - 1:hi]]
    return sum(xs) / len(xs)


def shape_stats(res):
    log = res["log"]
    early, late = span(log, 201, 700, 0), span(log, 2501, 3000, 0)
    happy = sorted(range(len(log)), key=lambda i: -log[i][0])[:max(1, len(log) // 100)]
    grok_share = sum(1 for i in happy if log[i][2] > 0) / len(happy)
    return {"happy_early": early, "happy_late": late, "grok_share_top1": grok_share,
            "gadget_early": span(log, 201, 700, 3), "gadget_late": span(log, 2001, 3000, 3)}


def gate(args):
    res = run("random", 1, args)
    hres = run("happiness", 1, args)
    checks = [
        (f"G1 room acc {res['final_acc']:.3f} >= 0.75 and new-object acc {res['new_acc']:.3f} >= 0.65",
         res["final_acc"] >= 0.75 and res["new_acc"] >= 0.65),
        (f"G2 general links {res['general_links']} >= 30, gadget general links {res['gadget_general_links']} >= 1",
         res["general_links"] >= 30 and res["gadget_general_links"] >= 1),
        (f"G3 happiness run {hres['seconds']}s < 120s", hres["seconds"] < 120),
    ]
    lines = ["# Acting agent v3 gate", "", "random arm, seed 1, fixed gadgets", "",
             *[f"- {'PASS' if ok else 'fail'}: {name}" for name, ok in checks], "",
             f"Gate: {'PASS' if all(ok for _, ok in checks) else 'FAIL'}", "",
             f"(happiness arm, same seed: area {hres['curve_area']:.3f}, final {hres['final_acc']:.3f}, "
             f"new {hres['new_acc']:.3f}; random area {res['curve_area']:.3f})"]
    text = "\n".join(lines)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "gate.md").write_text(text)
    print(text)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gate", action="store_true")
    p.add_argument("--suite", choices=["main", "shape", "grief", "grief2", "all"])
    p.add_argument("--seeds", default="1,2,3,4,5")
    p.add_argument("--actions", type=int, default=3000)
    p.add_argument("--episode-len", type=int, default=15)
    p.add_argument("--warmup", type=int, default=200)
    p.add_argument("--flip", type=float, default=0.1)
    p.add_argument("--temperature", type=float, default=0.3)
    p.add_argument("--epsilon", type=float, default=0.1)
    p.add_argument("--eval-every", type=int, default=150)
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--overwrite", action="store_true", help="Replace an existing results file")
    args = p.parse_args()
    torch.set_num_threads(1)
    if args.gate:
        return gate(args)
    args.out.mkdir(parents=True, exist_ok=True)
    seeds = [int(s) for s in args.seeds.split(",")]
    results = []
    results_path = args.out / f"results_{args.suite}.json"
    claim_results(results_path, args.overwrite)
    jobs = []
    if args.suite in ("main", "shape", "all"):
        jobs += [(arm, s, fresh, "none") for fresh in (False, True) for s in seeds
                 for arm in ("random", "novelty", "surprise", "learning_progress", "happiness")]
    if args.suite in ("grief", "all"):
        jobs += [("random", s, False, ch) for s in seeds for ch in ("big", "small")]
    if args.suite == "grief2":
        jobs += [("random", s, False, ch) for s in seeds for ch in ("light_big", "light_small")]
    for arm, s, fresh, ch in jobs:
        res = run(arm, s, args, fresh, ch)
        res["shape"] = shape_stats(res)
        g = res["log"]
        res["sad_2001_2500"] = sum(r[1] for r in g[2000:2500])
        res["sad_2501_3000"] = sum(r[1] for r in g[2500:3000])
        results.append(res)
        print(f"[{arm} {'B' if fresh else 'A'} {ch} s{s}] area {res['curve_area']:.3f} final {res['final_acc']:.3f} "
              f"new {res['new_acc']:.3f} gen {res['general_links']} happy {res['shape']['happy_early']:.3f}->"
              f"{res['shape']['happy_late']:.3f} grok {res['shape']['grok_share_top1']:.2f} gadget "
              f"{res['shape']['gadget_early']:.3f}->{res['shape']['gadget_late']:.3f} sad "
              f"{res['sad_2001_2500']:.2f}/{res['sad_2501_3000']:.2f} ({res['seconds']}s)", flush=True)
        atomic_write_text(results_path, json.dumps(results))


if __name__ == "__main__":
    main()
