#!/usr/bin/env python3
"""Acting agent v4: attach and spike rules for general links.

Design: docs/acting-agent-v4-design.md
Builds on scripts/acting_agent_v3.py (world, predictor, run loop, sadness).

  --gate                 gate checks
  --seeds 1 --out DIR    full grid for those seeds
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_agent_v3 as V  # noqa: E402
from output_state import atomic_write_text, claim_results  # noqa: E402

W = V.W
OUT = Path("runs/acting_agent_v4")
SEEDS = {(W.GRAPH_FIELDS.index(f), True) for f in ("light", "round", "hard", "noisy")}
HALF_LIFE, DISSOLVE, CONSOLIDATED = 300.0, 0.25, 3.0
VERSIONS = {"current": (False, None), "attach": (True, None), "spike_naive": (False, "naive"),
            "spike": (False, "guard"), "both": (True, "guard")}


def felt(c):
    return c ** 3 / (c ** 3 + 8)


class Felt:
    __slots__ = ("c", "last", "done", "things")

    def __init__(self, step, t):
        self.c, self.last, self.done, self.things = 1.0, step, False, {t}


class Store(V.Store):
    def __init__(self, attach=False, spike=None):
        super().__init__()
        self.attach, self.spike = attach, spike
        self.step = 0
        self.frontier = set(SEEDS)
        self.felt: dict[tuple, Felt] = {}
        self.hits: list[int] = []
        self.dissolved = 0

    def touches(self, combo):
        return not self.attach or any(f in self.frontier for f in combo)

    def thing_attached(self, t):
        return not self.attach or any(f in self.frontier for f in V.THING_FEATS[t])

    def fade(self, key):
        """Bring a link's count up to date. Returns its Felt, or None if dissolved."""
        f = self.felt[key]
        if not f.done and self.step > f.last:
            f.c *= 0.5 ** ((self.step - f.last) / HALF_LIFE)
            f.last = self.step
        if not f.done and f.c < DISSOLVE:
            del self.felt[key], self.gen[key]
            self.dissolved += 1
            return None
        return f

    def sweep(self):
        """Settle every link's fading, so dead links stop being stored and counted."""
        for key in list(self.felt):
            self.fade(key)

    def peek_c(self, key):
        f = self.felt[key]
        return f.c if f.done else f.c * 0.5 ** ((self.step - f.last) / HALF_LIFE)

    def alive(self, key):
        if not self.spike:
            return key in self.gen
        return key in self.gen and (self.felt[key].done or self.peek_c(key) >= DISSOLVE)

    def predict(self, t, action, surface, b):
        best, p = 0.0, 0.5
        L = self.spec.get((t, action, surface, b))
        if L is not None:
            best, p = 3 * L.s * abs(2 * L.p - 1), L.p
        for key in self.gen_keys(t, action, surface, b):
            G = self.gen.get(key)
            if G is not None and self.alive(key):
                w = G.s * abs(2 * G.p - 1)
                if w > best:
                    best, p = w, G.p
        return p

    def update(self, t, action, surface, bits):
        self.step += 1
        happy = sad = 0.0
        formed = hits = 0
        attached = self.thing_attached(t)
        for b, y in enumerate(bits):
            y = float(y)
            cover = 0.0
            for key in self.gen_keys(t, action, surface, b):
                G = self.gen.get(key)
                if G is not None and self.spike and self.fade(key) is None:
                    G = None
                if G is not None:
                    s0 = G.s
                    sad += G.hurt(y)
                    cover = max(cover, s0)
                    right = (y == 1.0) == (G.p > 0.5)
                    G.add(y)
                    if not self.spike:
                        if self.touches(key[0]):
                            happy += (G.s - s0) * (1 - s0)
                        continue
                    f = self.felt[key]
                    if not right:
                        if not f.done:
                            f.c = max(0.0, f.c - 1)
                    elif self.spike == "naive" or t not in f.things:
                        f.things.add(t)
                        before = felt(f.c)
                        crossed = f.c < 3 and f.c + 1 >= 2
                        f.c += 1
                        happy += (felt(f.c) - before) * (1 - before)
                        hits += crossed
                        if f.c >= CONSOLIDATED:
                            f.done = True
                    continue
                members = self.cand.setdefault(key, {})
                m = members.setdefault(t, V.Link())
                m.add(y)
                ready = [x for x in members.values() if x.n >= V.MIN_TRIES * V.DECAY ** 3]
                if len(ready) >= V.MIN_THINGS and m in ready:
                    ps = [x.p for x in ready]
                    if max(ps) - min(ps) > V.MAX_SPREAD:
                        self.fails[key] += 1  # the promised grok didn't come
                    elif self.touches(key[0]):  # else attach is holding it back: not a failure
                        G = V.Link(sum(x.a for x in members.values()), sum(x.n for x in members.values()))
                        self.gen[key] = G
                        del self.cand[key]
                        if self.attach:
                            self.frontier.update(key[0])
                        if self.spike:
                            self.felt[key] = Felt(self.step, t)
                            happy += felt(1.0)
                        else:
                            happy += G.s
                        formed += 1
            L = self.spec.setdefault((t, action, surface, b), V.Link())
            s0 = L.s
            if L.n > 0:
                sad += L.hurt(y)
            L.add(y)
            if attached:
                happy += (L.s - s0) * (1 - s0) * (1 - cover)
        self.hits.append(hits)
        return happy, sad, formed

    def expected_happiness(self, t, action, surface):
        total = 0.0
        attached = self.thing_attached(t)
        for b in range(V.W.N_BITS[action]):
            cover = 0.0
            for key in self.gen_keys(t, action, surface, b):
                G = self.gen.get(key)
                if G is not None and self.alive(key):
                    cover = max(cover, G.s)
                    if not self.spike:
                        if self.touches(key[0]):
                            total += (V.strength(G.n * V.DECAY + 1) - G.s) * (1 - G.s)
                    else:
                        f = self.felt[key]
                        if self.spike == "naive" or t not in f.things:
                            c = self.peek_c(key)
                            total += max(G.p, 1 - G.p) * (felt(c + 1) - felt(c)) * (1 - felt(c))
                    continue
                members = self.cand.get(key)
                if not members or not self.touches(key[0]):
                    continue
                others = [x for k2, x in members.items() if k2 != t and x.n >= V.MIN_TRIES * V.DECAY ** 3]
                mine = members.get(t)
                if len(others) >= V.MIN_THINGS - 1 and mine is not None and \
                        mine.n * V.DECAY + 1 >= V.MIN_TRIES * V.DECAY ** 3:
                    ps = [x.p for x in others]
                    if max(ps) - min(ps) <= V.MAX_SPREAD:
                        pay = felt(1.0) if self.spike else V.strength(sum(x.n for x in members.values()) + 1)
                        total += pay / (2 + self.fails[key])
            if attached:
                L = self.spec.get((t, action, surface, b))
                n = L.n if L else 0.0
                s0 = V.strength(n)
                total += (V.strength(n * V.DECAY + 1) - s0) * (1 - s0) * (1 - cover)
        return total


# --- false links -------------------------------------------------------------
THINGS = W.ROOM_OBJS + W.GADGETS
IS_GADGET = np.array([W.is_gadget(t) for t in THINGS])
FEAT_MASK = {}
for i, t in enumerate(THINGS):
    for f in V.THING_FEATS[t]:
        FEAT_MASK.setdefault(f, np.zeros(len(THINGS), bool))[i] = True
TRUTH = {}
_rng = __import__("random").Random(0)
for a in W.ACTIONS:
    usable = np.array([a in W.actions_for(t) for t in THINGS])
    for s in W.SURFACE_LIST:
        rows = [[0.5] * W.N_BITS[a] if W.is_gadget(t) else [float(x) for x in W.true_outcome(t, a, s, _rng)]
                for t in THINGS]
        TRUTH[(a, s)] = (usable, np.array(rows))


def false_share(store, fresh):
    weight = np.full(len(THINGS), 20 / len(W.ROOM_OBJS))
    weight[IS_GADGET] = 0.0
    idx = np.where(IS_GADGET)[0]
    if fresh:
        weight[idx[4:]] = 4 / (len(idx) - 4)
    else:
        weight[idx[:4]] = 1.0
    sure = false = gadget_false = 0
    for key, G in store.gen.items():
        if not store.alive(key) or abs(G.p - 0.5) < 0.2:
            continue
        combo, a, k, sv, b = key
        mask = np.ones(len(THINGS), bool)
        for f in combo:
            mask &= FEAT_MASK.get(f, np.zeros(len(THINGS), bool))
        num = den = 0.0
        for s, feats in V.SURF_FEATS.items():
            if feats[k][1] != sv:
                continue
            usable, rows = TRUTH[(a, s)]
            w = weight * mask * usable
            num += float((w * rows[:, b]).sum())
            den += float(w.sum())
        if den == 0:
            continue
        rate = num / den
        sure += 1
        if (G.p > 0.5) != (rate > 0.5) or 0.4 <= rate <= 0.6:
            false += 1
            gadget_false += (V.ELECTRONIC, True) in combo
    return {"sure": sure, "false": false, "share": false / sure if sure else 0.0, "gadget_false": gadget_false}


def run(version, arm, seed, args, fresh):
    attach, spike = VERSIONS[version]
    made = []

    def factory():
        made.append(Store(attach, spike))
        return made[-1]

    V.Store = factory
    res = V.run(arm, seed, args, fresh)
    store = made[-1]
    log = res.pop("log")
    gadget = sum(r[3] for r in log[200:]) / (len(log[200:]) or 1)
    order = sorted(range(len(log)), key=lambda i: -log[i][0])[:len(log) // 100]
    out = {k: res[k] for k in ("arm", "seed", "fresh", "curve_area", "final_acc", "new_acc", "general_links",
                               "gadget_general_links", "seconds", "curve")}
    out |= {"version": version, "gadget_share": gadget, "false": false_share(store, fresh),
            "dissolved": store.dissolved, "frontier": len(store.frontier),
            "top_with_hit": sum(store.hits[i] > 0 for i in order) / len(order),
            "base_with_hit": sum(h > 0 for h in store.hits) / len(store.hits),
            "happy_early": sum(r[0] for r in log[200:700]) / 500, "happy_late": sum(r[0] for r in log[2500:]) / 500}
    return out


def gate(args):
    ok = True
    for version in ("attach", "spike_naive", "spike", "both"):
        r = run(version, "random", 1, args, False)
        passed = r["final_acc"] >= 0.75 and r["new_acc"] >= 0.65
        ok &= passed
        print(f"{'PASS' if passed else 'fail'} G1 {version}: room {r['final_acc']:.3f} new {r['new_acc']:.3f} "
              f"links {r['general_links']} dissolved {r['dissolved']} frontier {r['frontier']} ({r['seconds']}s)", flush=True)
    h = run("both", "happiness", 1, args, False)
    print(f"{'PASS' if h['seconds'] < 240 else 'fail'} G2 both happiness: {h['seconds']}s, area {h['curve_area']:.3f} "
          f"gadget {h['gadget_share']:.3f}")
    print("Gate:", "PASS" if ok and h["seconds"] < 240 else "FAIL")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gate", action="store_true")
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
    if args.gate:
        return gate(args)
    results_path = args.out / "results.json"
    claim_results(results_path, args.overwrite)
    results = []
    for s in [int(x) for x in args.seeds.split(",")]:
        for fresh in (False, True):
            for version in VERSIONS:
                for arm in ("happiness", "random"):
                    r = run(version, arm, s, args, fresh)
                    results.append(r)
                    print(f"[{version} {arm} {'B' if fresh else 'A'} s{s}] area {r['curve_area']:.3f} new {r['new_acc']:.3f} "
                          f"gadget {r['gadget_share']:.3f} false {r['false']['share']:.3f} links {r['general_links']} "
                          f"dissolved {r['dissolved']} ({r['seconds']}s)", flush=True)
                    atomic_write_text(results_path, json.dumps(results))


if __name__ == "__main__":
    main()
