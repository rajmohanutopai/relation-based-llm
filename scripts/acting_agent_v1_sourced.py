#!/usr/bin/env python3
"""Does a graph of externally sourced facts help the random agent's world model?

Design: docs/object-properties-v0.md. Same setting as the hand-written graph
test in docs/acting-agent-v1-design.md, and it saves new-object accuracy, which
that test's script didn't. New-object accuracy: balanced accuracy on the held-out
objects, with their learned slot set to zero.

  --features sourced --seeds 1,2,3,4,5 --out runs/object_properties_v0
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_agent_v1 as V1  # noqa: E402

A = V1.A


def new_object_accuracy(model) -> float:
    held = list(A.v0.HELD_OUT_CANDIDATES)
    table = model.slot if hasattr(model, "slot") else model.thing
    with torch.no_grad():
        for t in held:
            table.weight[A.NAMES.index(t)] = 0.0
    cases = [(t, a, s) for t in held for a in A.actions_for(t) for s in A.SURFACE_LIST]
    rng = random.Random(0)
    truth = {c: A.true_outcome(*c, rng=rng) for c in cases}
    return A.accuracy(model, cases, truth)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--features", required=True)
    p.add_argument("--seeds", default="1,2,3,4,5")
    p.add_argument("--out", type=Path, default=Path("runs/object_properties_v0"))
    cli = p.parse_args()
    args = argparse.Namespace(actions=3000, episode_len=20, warmup=200, batch_size=32, lr=3e-3, activation=0.02,
                              temperature=0.3, epsilon=0.1, eval_every=50, gadgets=2, flip=0.1, group="region",
                              features=cli.features, fresh_gadgets=False)
    torch.set_num_threads(1)
    made = []
    build = V1.make_world_model

    def keep(a):
        made.append(build(a))
        return made[-1]

    A.make_world_model = keep
    cli.out.mkdir(parents=True, exist_ok=True)
    results = []
    for seed in [int(s) for s in cli.seeds.split(",")]:
        r = A.run("random", seed, args)
        acc85 = next((c["step"] for c in r["curve"] if c["acc"] >= 0.85), None)
        results.append({"features": cli.features, "seed": seed, "curve_area": r["curve_area"], "final_acc": r["final_acc"],
                        "steps_to_85": acc85, "new_acc": new_object_accuracy(made[-1]), "seconds": r["seconds"],
                        "curve": r["curve"]})
        x = results[-1]
        print(f"[{cli.features} s{seed}] area {x['curve_area']:.3f} final {x['final_acc']:.3f} new {x['new_acc']:.3f} "
              f"to85 {acc85} ({x['seconds']}s)", flush=True)
        (cli.out / f"{cli.features}.json").write_text(json.dumps(results))


if __name__ == "__main__":
    main()
