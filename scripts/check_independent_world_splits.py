#!/usr/bin/env python3
"""Was the one 30-object test set of independent_world_v0 a typical choice?

Reruns that experiment's own world model and scoring with other random choices of the
held-out objects, and fits a plain logistic model as a second opinion. Reads the frozen
answers and outcomes; changes neither. Report: docs/language-transfer-cv-v0.md
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import random
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_agent_independent_v0 as W  # noqa: E402
from output_state import atomic_write_text, claim_results  # noqa: E402

OUT = Path("runs/independent_world_split_check")
ARMS = ("names", "answers", "answers_shuffled", "geometry")
OTHER_SPLITS = 60


def held_out(names, split_id):
    seed = W.SPLIT_SEED if split_id == 0 else 1000 + split_id
    return sorted(random.Random(seed).sample(names, W.HELD_OUT))


def world_model_job(job):
    split_id, seed = job
    torch.set_num_threads(1)
    world, samples, truth = W.load_world()
    names = sorted(o["name"] for o in world)
    held = held_out(names, split_id)
    train = [n for n in names if n not in set(held)]
    return {"split": split_id, "seed": seed,
            "new": {arm: W.run(arm, seed, world, samples, truth, train, held)["new"] for arm in ARMS}}


def logistic_new_object_score(features, truth, held):
    """Class-balanced logistic fit per action and outcome; balanced accuracy on the held-out objects."""
    scores = []
    for action in W.ACTIONS:
        cases = [c for c in truth if c[1] == action]
        train = [c for c in cases if c[0] not in held]
        test = [c for c in cases if c[0] in held]

        def design(rows):
            out = []
            for c in rows:
                f, s = features[c[0]], (1.0 if c[2] == "slippery" else -1.0)
                out.append(np.concatenate([f, [s], f * s]))
            return torch.tensor(np.array(out), dtype=torch.float32)

        x_train, x_test = design(train), design(test)
        for bit in range(W.BITS):
            y = torch.tensor([float(truth[c][bit]) for c in train])
            y_test = np.array([truth[c][bit] for c in test])
            if y_test.all() or not y_test.any():
                continue
            torch.manual_seed(0)
            net = torch.nn.Linear(x_train.shape[1], 1)
            share = y.mean().clamp(0.02, 0.98)
            weight = torch.where(y > 0.5, 0.5 / share, 0.5 / (1 - share))
            opt = torch.optim.LBFGS(net.parameters(), lr=0.5, max_iter=200, line_search_fn="strong_wolfe")

            def closure():
                opt.zero_grad()
                loss = (torch.nn.functional.binary_cross_entropy_with_logits(net(x_train).squeeze(1), y, reduction="none") * weight).mean()
                loss = loss + (net.weight ** 2).sum() / len(x_train)
                loss.backward()
                return loss

            opt.step(closure)
            with torch.no_grad():
                pred = (net(x_test).squeeze(1) > 0).numpy()
            scores.append((pred[y_test].mean() + (~pred[~y_test]).mean()) / 2)
    return float(np.mean(scores))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--overwrite", action="store_true")
    cli = p.parse_args()
    path = cli.out / "results.json"
    claim_results(path, cli.overwrite)

    jobs = [(0, s) for s in (1, 2, 3, 4, 5)] + [(i, 1) for i in range(1, OTHER_SPLITS + 1)]
    with mp.Pool(cli.workers) as pool:
        runs = pool.map(world_model_job, jobs, chunksize=1)

    world, _, truth = W.load_world()
    names = sorted(o["name"] for o in world)
    index = {n: i for i, n in enumerate(names)}
    feature_sets = {"answers": W.answer_features(names).numpy(), "answers_shuffled": W.answer_features(names, True).numpy(),
                    "geometry": W.geometry_features(world, names).numpy()}
    # each of the eight answers alone: its yes/no column and its "known" column
    props = list(json.loads(W.ANSWERS.read_text())["properties"])
    for i, prop in enumerate(props):
        feature_sets[f"only {prop}"] = feature_sets["answers"][:, 2 * i: 2 * i + 2]
    logistic = {}
    for label, table in feature_sets.items():
        features = {n: table[index[n]] for n in names}
        logistic[label] = {"original": logistic_new_object_score(features, truth, set(held_out(names, 0))),
                           "other": [logistic_new_object_score(features, truth, set(held_out(names, i)))
                                     for i in range(1, OTHER_SPLITS + 1)]}
    atomic_write_text(path, json.dumps({"world_model": runs, "logistic": logistic}))

    original = [r["new"] for r in runs if r["split"] == 0]
    other = [r["new"] for r in runs if r["split"] != 0]
    print(f"world model: original 30 objects (5 seeds) | {OTHER_SPLITS} other choices (seed 1): mean [5th, 95th percentile]")
    for arm in ARMS:
        v = np.array([r[arm] for r in other])
        print(f"  {arm:17} {np.mean([r[arm] for r in original]):.3f} | {v.mean():.3f} [{np.percentile(v, 5):.3f}, {np.percentile(v, 95):.3f}]")
    gap = np.array([r["answers"] - r["answers_shuffled"] for r in other])
    low = np.mean([r["answers"] for r in original])
    print(f"  answers minus shuffled: {np.mean([r['answers'] - r['answers_shuffled'] for r in original]):+.3f} | {gap.mean():+.3f}, "
          f"above zero in {int((gap > 0).sum())} of {len(gap)}")
    print(f"  other choices scoring at or below the original for answers: {sum(r['answers'] <= low for r in other)} of {len(other)}")
    print("logistic fit: original | other choices, mean")
    for label, r in logistic.items():
        print(f"  {label:17} {r['original']:.3f} | {np.mean(r['other']):.3f}")


if __name__ == "__main__":
    main()
