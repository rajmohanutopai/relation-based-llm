#!/usr/bin/env python3
"""Acting agent v4.3: a room that is half noise.

Design: docs/acting-agent-v4-3-design.md
Builds on scripts/acting_agent_v4_2.py; the only change is how many ordinary things a room holds.

  --gate         with 20 things per room, must match v4.2's stored --S curve (seed 6, A)
  --run          all jobs; finished jobs are skipped
  --score        tables and rule verdicts
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_agent_v4_2 as V42  # noqa: E402
from output_state import atomic_write_text, directory_lock  # noqa: E402

V = V42.V
W = V.W
OUT = Path("runs/acting_agent_v4_3")
THINGS_PER_ROOM = 4
SEEDS = (11, 12, 13, 14, 15)
BABIES = {"random": ("---", "random"), "surprise": ("---", "surprise"), "happiness": ("--S", "happiness")}


def room_maker(things_per_room):
    def new_room(rng, fresh, room_no):
        room = rng.choice(W.ROOMS)
        gadgets = W.GADGETS[4 + 4 * room_no: 8 + 4 * room_no] if fresh else W.FIXED_GADGETS
        things = rng.sample(W.ROOM_OBJS, things_per_room) + list(gadgets)
        return {t: rng.choice(W.ROOM_SURFACES[room]) for t in things}
    return new_room


def settings():
    return argparse.Namespace(actions=3000, episode_len=15, warmup=200, flip=0.1, temperature=0.3, epsilon=0.1, eval_every=150)


def run_baby(version, arm, seed, fresh):
    """As V42.run, but keeps the share of late turns spent on gadgets and drops the false-link count,
    which assumes 20 things per room."""
    V.Store = lambda: V42.Store(*V42.VERSIONS[version])
    res = V.run(arm, seed, settings(), fresh)
    log = res.pop("log")
    keep = ("arm", "seed", "fresh", "curve_area", "final_acc", "new_acc", "general_links", "seconds", "curve")
    share = lambda rows: sum(r[3] for r in rows) / len(rows)
    return {k: res[k] for k in keep} | {"version": version, "gadget_share": share(log[200:]), "gadget_late": share(log[-1000:])}


def run_job(job):
    out, baby, cond, seed = job
    path = out / f"{baby}_{cond}_seed{seed}.json"
    if path.exists():
        return str(path), "skipped"
    W.new_room = room_maker(THINGS_PER_ROOM)
    version, arm = BABIES[baby]
    r = run_baby(version, arm, seed, cond == "B")
    r.update({"baby": baby, "cond": cond})
    atomic_write_text(path, json.dumps(r))
    return str(path), {k: r[k] for k in ("curve_area", "final_acc", "new_acc", "gadget_share", "gadget_late", "seconds")}


def gate():
    W.new_room = room_maker(20)
    old = next(r for r in json.loads(Path("runs/acting_agent_v4_2/seed6_A/results.json").read_text())
               if r["version"] == "--S" and r["arm"] == "happiness" and r["seed"] == 6 and not r["fresh"])
    r = run_baby("--S", "happiness", 6, False)
    same = r["curve"] == old["curve"] and abs(r["gadget_share"] - old["gadget_share"]) < 1e-12
    print(f"{'PASS' if same else 'FAIL'} gate: area {r['curve_area']:.4f} vs {old['curve_area']:.4f}, "
          f"gadget {r['gadget_share']:.4f} vs {old['gadget_share']:.4f} ({r['seconds']}s)")


def score(out):
    rows = {}
    for baby in BABIES:
        for cond in "AB":
            runs = [json.loads(p.read_text()) for s in SEEDS if (p := out / f"{baby}_{cond}_seed{s}.json").exists()]
            if len(runs) == len(SEEDS):
                rows[(baby, cond)] = runs
    mean = lambda runs, k: sum(r[k] for r in runs) / len(runs)
    print(f"{'baby':10} {'cond':4} {'area':>6} {'final':>6} {'new':>6} {'gadget time':>11} {'last 1000':>9}")
    for (baby, cond), runs in rows.items():
        print(f"{baby:10} {cond:4} {mean(runs, 'curve_area'):.3f} {mean(runs, 'final_acc'):.3f} {mean(runs, 'new_acc'):.3f} "
              f"{mean(runs, 'gadget_share'):>11.3f} {mean(runs, 'gadget_late'):>9.3f}")
    rules = [("N1 happiness beats surprise on curve area (main)", "happiness", "surprise", "curve_area"),
             ("N2 happiness beats surprise on final score", "happiness", "surprise", "final_acc"),
             ("N3 happiness beats random on curve area", "happiness", "random", "curve_area")]
    print()
    summary = {}
    for label, first, second, key in rules:
        parts = []
        for cond in "AB":
            if (first, cond) not in rows or (second, cond) not in rows:
                parts.append(f"{cond}: not finished")
                continue
            wins = sum(a[key] > b[key] for a, b in zip(rows[(first, cond)], rows[(second, cond)]))
            gap = mean(rows[(first, cond)], key) - mean(rows[(second, cond)], key)
            summary[f"{label} {cond}"] = {"wins": wins, "gap": gap}
            parts.append(f"{cond}: {wins} of {len(SEEDS)} seeds, mean gap {gap:+.3f}, {'PASS' if wins >= 4 else 'fail'}")
        print(f"{label}: " + "; ".join(parts))
    atomic_write_text(out / "summary.json", json.dumps(summary, indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gate", action="store_true")
    p.add_argument("--run", action="store_true")
    p.add_argument("--score", action="store_true")
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--workers", type=int, default=2)
    cli = p.parse_args()
    if cli.gate:
        gate()
    if cli.run:
        # the quick babies first, so a look at progress shows whole rows early
        jobs = [(cli.out, baby, cond, seed) for baby in ("random", "surprise", "happiness") for cond in "AB" for seed in SEEDS]
        with directory_lock(cli.out), mp.Pool(cli.workers) as pool:
            for path, info in pool.imap_unordered(run_job, jobs, chunksize=1):
                print(path, info, flush=True)
    if cli.score:
        score(cli.out)


if __name__ == "__main__":
    main()
