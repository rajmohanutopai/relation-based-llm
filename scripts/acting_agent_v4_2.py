#!/usr/bin/env python3
"""Acting agent v4.2: confirm v4.1 on new seeds, and test why its parts work.

Design: docs/acting-agent-v4-2-design.md
Builds on scripts/acting_agent_v4_1.py.

  --gate                          refactored store must match v4.1 on seed 1, condition A
  --seeds 6 --conds A --out DIR   all versions and rivals for that seed and condition
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_agent_v4 as V4  # noqa: E402
from output_state import atomic_write_text, claim_results  # noqa: E402
import acting_agent_v4_1 as V41  # noqa: E402

V = V4.V
OUT = Path("runs/acting_agent_v4_2")
FLAT_PAY = 0.17  # mean of the S-curve's three payments: 0.346, 0.136, 0.027
# name: low_pay, fading, scurve, flat, first_only
VERSIONS = {
    "---": (False, False, False, False, False),
    "--S": (False, False, True, False, False),
    "L-S": (True, False, True, False, False),
    "--flat": (False, False, True, True, False),
    "L-flat": (True, False, True, True, False),
    "-F-": (False, True, False, False, False),
    "-F-first": (False, True, False, False, True),
    "-FS": (False, True, True, False, False),
    "-FS-first": (False, True, True, False, True),
}
RIVALS = ("random", "surprise")


class Store(V41.Store):
    def __init__(self, low_pay, fading, scurve, flat, first_only):
        super().__init__(low_pay, fading, scurve)
        self.flat, self.first_only = flat, first_only

    def confirm_pay(self, c):
        if self.flat:
            return FLAT_PAY if c < 4 else 0.0
        return super().confirm_pay(c)

    def form_pay(self, key, strength):
        if self.first_only and key in self.paid:
            return 0.0
        return super().form_pay(key, strength)


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
    keep = ("arm", "seed", "fresh", "curve_area", "final_acc", "new_acc", "general_links", "seconds", "curve")
    return {k: res[k] for k in keep} | {
        "version": version, "gadget_share": sum(r[3] for r in tail) / (len(tail) or 1),
        "false": V4.false_share(store, fresh), "dissolved": store.dissolved,
        "formed_total": sum(r[2] for r in log)}


def gate(args):
    old = {r["version"]: r for r in json.loads(Path("runs/acting_agent_v4_1/seed1/results.json").read_text())
           if not r["fresh"]}
    ok = True
    for version in ("---", "--S", "-FS"):
        r = run(version, 1, args, False)
        same = r["curve"] == old[version]["curve"] and abs(r["gadget_share"] - old[version]["gadget_share"]) < 1e-12
        ok &= same
        print(f"{'PASS' if same else 'FAIL'} {version}: area {r['curve_area']:.4f} vs {old[version]['curve_area']:.4f}, "
              f"gadget {r['gadget_share']:.4f} vs {old[version]['gadget_share']:.4f} ({r['seconds']}s)", flush=True)
    print("Gate:", "PASS" if ok else "FAIL")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gate", action="store_true")
    p.add_argument("--seeds", default="6,7,8,9,10")
    p.add_argument("--conds", default="A,B")
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
        for cond in args.conds.split(","):
            fresh = cond == "B"
            jobs = [("---", a) for a in RIVALS] + [(v, "happiness") for v in VERSIONS]
            for version, arm in jobs:
                r = run(version, s, args, fresh, arm)
                results.append(r)
                print(f"[{version} {arm} {cond} s{s}] area {r['curve_area']:.3f} new {r['new_acc']:.3f} "
                      f"gadget {r['gadget_share']:.3f} dissolved {r['dissolved']} formed {r['formed_total']} "
                      f"({r['seconds']}s)", flush=True)
                atomic_write_text(results_path, json.dumps(results))


if __name__ == "__main__":
    main()
