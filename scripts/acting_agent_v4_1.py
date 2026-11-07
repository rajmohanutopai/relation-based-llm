#!/usr/bin/env python3
"""Acting agent v4.1: which part of the spike rule removes the pull to noise?

Design: docs/acting-agent-v4-1-design.md
Builds on scripts/acting_agent_v4.py. Three switches, 8 versions:

  low_pay  forming a general link pays felt(1) = 0.11 instead of its strength
  fading   links count confirmations, fade and dissolve until consolidated
  scurve   confirmations pay the S-curve (each thing once) instead of the v3 rise

  --gate                 corners must match v4 exactly on seed 1, condition A
  --seeds 1 --out DIR    happiness arm, all 8 versions, both conditions
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_agent_v4 as V4  # noqa: E402
from output_state import atomic_write_text, claim_results  # noqa: E402

V = V4.V
OUT = Path("runs/acting_agent_v4_1")
V4_RUNS = Path("runs/acting_agent_v4")
VERSIONS = {"".join("LFS"[i] if on else "-" for i, on in enumerate(bits)): bits
            for bits in itertools.product((False, True), repeat=3)}
CORNERS = {"---": "current", "LFS": "spike"}


class Store(V4.Store):
    def __init__(self, low_pay, fading, scurve):
        super().__init__(False, "guard" if fading or scurve else None)
        self.low_pay, self.fading, self.scurve = low_pay, fading, scurve
        self.paid: set[tuple] = set()

    def confirm_pay(self, c):
        """Payment for a confirmation that takes the count from c to c + 1."""
        return (V4.felt(c + 1) - V4.felt(c)) * (1 - V4.felt(c))

    def form_pay(self, key, strength):
        return V4.felt(1.0) if self.low_pay else strength

    def fade(self, key):
        return super().fade(key) if self.fading else self.felt[key]

    def peek_c(self, key):
        return super().peek_c(key) if self.fading else self.felt[key].c

    def alive(self, key):
        return super().alive(key) if self.fading else key in self.gen

    def update(self, t, action, surface, bits):
        self.step += 1
        happy = sad = 0.0
        formed = hits = 0
        for b, y in enumerate(bits):
            y = float(y)
            cover = 0.0
            for key in self.gen_keys(t, action, surface, b):
                G = self.gen.get(key)
                if G is not None and self.fading and self.fade(key) is None:
                    G = None
                if G is not None:
                    s0 = G.s
                    sad += G.hurt(y)
                    cover = max(cover, s0)
                    right = (y == 1.0) == (G.p > 0.5)
                    G.add(y)
                    if self.spike:
                        f = self.felt[key]
                        if not right:
                            if not f.done:
                                f.c = max(0.0, f.c - 1)
                        elif t not in f.things:
                            f.things.add(t)
                            crossed = f.c < 3 and f.c + 1 >= 2
                            if self.scurve:
                                happy += self.confirm_pay(f.c)
                                hits += crossed
                            f.c += 1
                            if f.c >= V4.CONSOLIDATED:
                                f.done = True
                    if not self.scurve:
                        happy += (G.s - s0) * (1 - s0)
                    continue
                members = self.cand.setdefault(key, {})
                m = members.setdefault(t, V.Link())
                m.add(y)
                ready = [x for x in members.values() if x.n >= V.MIN_TRIES * V.DECAY ** 3]
                if len(ready) >= V.MIN_THINGS and m in ready:
                    ps = [x.p for x in ready]
                    if max(ps) - min(ps) <= V.MAX_SPREAD:
                        G = V.Link(sum(x.a for x in members.values()), sum(x.n for x in members.values()))
                        self.gen[key] = G
                        del self.cand[key]
                        if self.spike:
                            self.felt[key] = V4.Felt(self.step, t)
                        happy += self.form_pay(key, G.s)
                        self.paid.add(key)
                        formed += 1
                    else:
                        self.fails[key] += 1
            L = self.spec.setdefault((t, action, surface, b), V.Link())
            s0 = L.s
            if L.n > 0:
                sad += L.hurt(y)
            L.add(y)
            happy += (L.s - s0) * (1 - s0) * (1 - cover)
        self.hits.append(hits)
        return happy, sad, formed

    def expected_happiness(self, t, action, surface):
        total = 0.0
        for b in range(V.W.N_BITS[action]):
            cover = 0.0
            for key in self.gen_keys(t, action, surface, b):
                G = self.gen.get(key)
                if G is not None and self.alive(key):
                    cover = max(cover, G.s)
                    if not self.scurve:
                        total += (V.strength(G.n * V.DECAY + 1) - G.s) * (1 - G.s)
                    elif t not in self.felt[key].things:
                        c = self.peek_c(key)
                        total += max(G.p, 1 - G.p) * self.confirm_pay(c)
                    continue
                members = self.cand.get(key)
                if not members:
                    continue
                others = [x for k2, x in members.items() if k2 != t and x.n >= V.MIN_TRIES * V.DECAY ** 3]
                mine = members.get(t)
                if len(others) >= V.MIN_THINGS - 1 and mine is not None and \
                        mine.n * V.DECAY + 1 >= V.MIN_TRIES * V.DECAY ** 3:
                    ps = [x.p for x in others]
                    if max(ps) - min(ps) <= V.MAX_SPREAD:
                        pay = self.form_pay(key, V.strength(sum(x.n for x in members.values()) + 1))
                        total += pay / (2 + self.fails[key])
            L = self.spec.get((t, action, surface, b))
            n = L.n if L else 0.0
            s0 = V.strength(n)
            total += (V.strength(n * V.DECAY + 1) - s0) * (1 - s0) * (1 - cover)
        return total


def run(version, seed, args, fresh, arm="happiness"):
    made = []

    def factory():
        made.append(Store(*VERSIONS[version]))
        return made[-1]

    V.Store = factory
    res = V.run(arm, seed, args, fresh)
    store = made[-1]
    log = res.pop("log")
    tail = log[200:]
    keep = ("arm", "seed", "fresh", "curve_area", "final_acc", "new_acc", "general_links",
            "gadget_general_links", "seconds", "curve")
    return {k: res[k] for k in keep} | {
        "version": version, "gadget_share": sum(r[3] for r in tail) / (len(tail) or 1),
        "false": V4.false_share(store, fresh), "dissolved": store.dissolved,
        "formed_total": sum(r[2] for r in log)}


def gate(args):
    old = {(r["version"], r["arm"]): r for r in json.loads((V4_RUNS / "seed1" / "results.json").read_text())
           if r["seed"] == 1 and not r["fresh"]}
    ok = True
    for version, name in CORNERS.items():
        r = run(version, 1, args, False)
        o = old[(name, "happiness")]
        same = r["curve"] == o["curve"] and abs(r["gadget_share"] - o["gadget_share"]) < 1e-12
        ok &= same
        print(f"{'PASS' if same else 'FAIL'} {version} = v4 {name}: area {r['curve_area']:.4f} vs {o['curve_area']:.4f}, "
              f"gadget {r['gadget_share']:.4f} vs {o['gadget_share']:.4f} ({r['seconds']}s)", flush=True)
    print("Gate:", "PASS" if ok else "FAIL")


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
                r = run(version, s, args, fresh)
                results.append(r)
                print(f"[{version} {'B' if fresh else 'A'} s{s}] area {r['curve_area']:.3f} new {r['new_acc']:.3f} "
                      f"gadget {r['gadget_share']:.3f} false {r['false']['share']:.3f} links {r['general_links']} "
                      f"dissolved {r['dissolved']} ({r['seconds']}s)", flush=True)
                atomic_write_text(results_path, json.dumps(results))


if __name__ == "__main__":
    main()
