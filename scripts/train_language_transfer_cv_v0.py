#!/usr/bin/env python3
"""The language transfer test with every object held out once. Design: docs/language-transfer-cv-v0.md

  --smoke         20 steps of every arm on fold 0; prints no new-object score
  --run           all jobs; finished jobs are skipped, so a stopped run can be started again
  --reference     the independent_world_v0 world model on the same folds, for comparison
  --score         tables and rule verdicts from the finished jobs
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
import train_language_transfer_v0 as L  # noqa: E402
from output_state import atomic_write_text, directory_lock  # noqa: E402

OUT = Path("runs/language_transfer_cv_v0")
FOLD_SEED = 20261110
FOLDS = 5
STEPS = 6000
# (quantity, phrase ending, cut-offs): the measured facts, fixed in the design
MEASURES = [("long", "cm long", (15, 24, 29)), ("wide", "cm wide", (9, 13, 20)), ("thick", "cm thick", (5, 8, 11)),
            ("weight", "g", (350, 750, 2000))]
# block -> (opaque names?, fact source, arms run through L.run under these names, seeds)
BLOCKS = {
    "A_answers": (True, "answers", ["plain_text", "facts_separate", "facts_separate_shuffled"], (1, 2)),
    "A_measured": (True, "measured", ["facts_separate", "facts_separate_shuffled"], (1, 2)),
    "B_prompt": (True, "answers", ["facts_in_prompt", "facts_in_prompt_shuffled"], (1,)),
    # Block C was designed with seed 1; seed 2 and Block D are the addendum in the design
    "C_names": (False, "answers", ["plain_text", "facts_separate", "facts_separate_shuffled"], (1, 2)),
    "D_names_measured": (False, "measured", ["facts_separate", "facts_separate_shuffled"], (1, 2)),
}
BIT_NAMES = ["moved", "rolled", "tipped"]


def fold_sets(names):
    first = sorted(random.Random(W.SPLIT_SEED).sample(names, W.HELD_OUT))
    rest = [n for n in names if n not in set(first)]
    random.Random(FOLD_SEED).shuffle(rest)
    return [first] + [sorted(rest[i::FOLDS - 1]) for i in range(FOLDS - 1)]


def measured_facts(world):
    out = {}
    for o in world:
        thick, wide, long_ = (100 * x for x in sorted(o["size"]))
        value = {"long": long_, "wide": wide, "thick": thick, "weight": 1000 * o["mass"]}
        out[o["name"]] = {f"{q}_{cut}": ("yes" if value[q] > cut else "no") for q, _, cuts in MEASURES for cut in cuts}
    return out


def setup(opaque):
    """Everything a job needs that doesn't depend on the fold. Sets the name style and the measured phrases."""
    world, samples, truth = W.load_world()
    names = sorted(o["name"] for o in world)
    L.OPAQUE.clear()
    if opaque:
        L.OPAQUE.update({n: f"obj{i}" for i, n in enumerate(names)})
    L.PHRASE.update({f"{q}_{cut}": f"over {cut} {tail}" for q, tail, cuts in MEASURES for cut in cuts})
    wrong = names[:]
    random.Random(W.SHUFFLE_SEED).shuffle(wrong)
    answers = json.loads(W.ANSWERS.read_text())["answers"]
    measured = measured_facts(world)
    facts = {"answers": ({n: answers[n] for n in names}, {n: answers[w] for n, w in zip(names, wrong)}),
             "measured": ({n: measured[n] for n in names}, {n: measured[w] for n, w in zip(names, wrong)})}
    both_real = {n: {**facts["answers"][0][n], **facts["measured"][0][n]} for n in names}
    both_fake = {n: {**facts["answers"][1][n], **facts["measured"][1][n]} for n in names}
    vocab = L.build_vocab(truth, names, both_real, both_fake)
    ctx = L.context_length((samples, truth, names, [], *facts["answers"]), vocab)
    return samples, truth, names, facts, vocab, ctx


def job_path(out, block, arm, fold, seed):
    return out / block / f"fold{fold}_seed{seed}_{arm}.json"


def run_job(job):
    out, block, arm, fold, seed, steps, keep_scores = job
    path = job_path(out, block, arm, fold, seed)
    if path.exists():
        return str(path), "skipped"
    torch.set_num_threads(1)
    opaque, source, _, _ = BLOCKS[block]
    samples, truth, names, facts, vocab, ctx = setup(opaque)
    held = fold_sets(names)[fold]
    train = [n for n in names if n not in set(held)]
    real, fake = facts[source]
    yes, no = vocab.stoi["yes"], vocab.stoi["no"]
    cases = [c for c in truth if c[0] in set(held)]

    @torch.no_grad()
    def held_out_logits(model, inline_for):
        rows = []
        for case in cases:
            prompts = [(L.prompt(case[0], case, bit, inline_for(case[0])), None) for bit in range(W.BITS)]
            rows.append([case[0], case[1], case[2], L.answer_logits(model, prompts, vocab, yes, no)[1].tolist()])
        return {"cases": rows}

    result = L.run(arm, seed, steps, (samples, truth, train, held, real, fake), vocab, ctx, keep_scores,
                   extra=held_out_logits if keep_scores else None)
    result.update({"block": block, "fold": fold, "vocab": len(vocab.itos), "ctx": ctx})
    if keep_scores:
        atomic_write_text(path, json.dumps(result))
    return str(path), {k: v for k, v in result.items() if k in ("params", "vocab", "ctx", "seconds", "train_acc", "recall_held")}


def all_jobs(out, steps):
    """Seed 1 of the main block first, then the side blocks, then seed 2."""
    def block_jobs(block, seed):
        return [(out, block, arm, fold, seed, steps, True) for fold in range(FOLDS) for arm in BLOCKS[block][2]]
    order = [("A_answers", 1), ("A_measured", 1), ("B_prompt", 1), ("C_names", 1), ("A_answers", 2), ("A_measured", 2),
             ("D_names_measured", 1), ("C_names", 2), ("D_names_measured", 2)]
    return [j for block, seed in order for j in block_jobs(block, seed)]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def load_arm(out, block, arm, seed, truth, index):
    """Logit gaps for every object from the fold that held it out, or None if a fold is missing."""
    gaps = np.full((len(index), len(W.ACTIONS), len(W.SURFACES), W.BITS), np.nan)
    runs = []
    for fold in range(FOLDS):
        path = job_path(out, block, arm, fold, seed)
        if not path.exists():
            return None
        r = json.loads(path.read_text())
        runs.append(r)
        for name, action, surface, d in r["cases"]:
            gaps[index[name], W.ACTIONS.index(action), W.SURFACES.index(surface)] = d
    return gaps, runs


def object_counts(pred, y):
    """Per object, action and bit: hits and totals for yes and no cases (summed over surfaces)."""
    n = len(y)
    return ((pred & y).sum(2).reshape(n, -1), y.sum(2).reshape(n, -1), (~pred & ~y).sum(2).reshape(n, -1), (~y).sum(2).reshape(n, -1))


def pooled_balanced(counts, weights):
    """weights: (draws, objects). Balanced accuracy per action and bit over the weighted objects, then the mean."""
    tp, pos, tn, neg = (weights @ c for c in counts)
    return ((tp / pos + tn / neg) / 2).mean(1)


def fold_auc(gaps, y, folds, index):
    scores = []
    for a in range(len(W.ACTIONS)):
        for b in range(W.BITS):
            per_fold = []
            for fold in folds:
                rows = [index[n] for n in fold]
                s, t = gaps[rows, a, :, b].ravel(), y[rows, a, :, b].ravel()
                if t.all() or not t.any():
                    continue
                pos, neg = s[t], s[~t]
                per_fold.append(((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()))
            scores.append(np.mean(per_fold))
    return float(np.mean(scores))


def score(out):
    _, truth, names, _, _, _ = setup(True)
    index = {n: i for i, n in enumerate(names)}
    folds = fold_sets(names)
    y = np.zeros((len(names), len(W.ACTIONS), len(W.SURFACES), W.BITS), dtype=bool)
    for (name, action, surface), bits in truth.items():
        y[index[name], W.ACTIONS.index(action), W.SURFACES.index(surface)] = bits
    rng = np.random.default_rng(0)
    draws = rng.multinomial(len(names), np.full(len(names), 1 / len(names)), size=5000).astype(float)
    ones = np.ones((1, len(names)))
    summary, arms = {}, {}
    for block, (_, _, block_arms, seeds) in BLOCKS.items():
        for arm in block_arms:
            loaded = [load_arm(out, block, arm, seed, truth, index) for seed in seeds]
            if any(x is None for x in loaded):
                continue
            key = f"{block}/{arm}"
            counts = [object_counts(g > 0, y) for g, _ in loaded]
            runs = [r for _, rs in loaded for r in rs]
            arms[key] = counts
            by_fold = [float(np.mean([r["new_acc"] for r in runs if r["fold"] == f])) for f in range(FOLDS)]
            summary[key] = {
                "seeds": list(seeds), "params": runs[0]["params"],
                "train": float(np.mean([r["train_acc"] for r in runs])),
                "recall_held": float(np.mean([r["recall_held"] for r in runs])) if "recall_held" in runs[0] else None,
                "pooled_balanced": float(np.mean([pooled_balanced(c, ones)[0] for c in counts])),
                "by_seed": [float(pooled_balanced(c, ones)[0]) for c in counts],
                "auc": float(np.mean([fold_auc(g, y, folds, index) for g, _ in loaded])),
                "by_fold": by_fold,
            }
    print(f"{'arm':38} {'params':>8} {'train':>6} {'recall':>6} {'new objects':>11} {'AUC':>6}  by fold (fold 0 is the old test set)")
    for key, s in summary.items():
        recall = f"{s['recall_held']:.3f}" if s["recall_held"] is not None else "   -  "
        print(f"{key:38} {s['params']:>8} {s['train']:.3f} {recall:>6} {s['pooled_balanced']:>11.3f} {s['auc']:.3f}  "
              + " ".join(f"{v:.3f}" for v in s["by_fold"]))
    pairs = [("C1 answers beat wrong-object answers (main)", "A_answers/facts_separate", "A_answers/facts_separate_shuffled"),
             ("C2 measured beat wrong-object measured", "A_measured/facts_separate", "A_measured/facts_separate_shuffled"),
             ("C3 answers beat plain text", "A_answers/facts_separate", "A_answers/plain_text"),
             ("C4 measured beat plain text", "A_measured/facts_separate", "A_answers/plain_text"),
             ("B  prompt facts beat wrong-object prompt facts", "B_prompt/facts_in_prompt", "B_prompt/facts_in_prompt_shuffled"),
             ("C  real names: answers beat wrong-object answers", "C_names/facts_separate", "C_names/facts_separate_shuffled"),
             ("C  real names: answers beat plain text", "C_names/facts_separate", "C_names/plain_text"),
             ("D1 real names: measured beat wrong-object measured", "D_names_measured/facts_separate", "D_names_measured/facts_separate_shuffled"),
             ("D2 real names: measured beat plain text", "D_names_measured/facts_separate", "C_names/plain_text")]
    print()
    verdicts = {}
    for label, first, second in pairs:
        if first not in arms or second not in arms:
            print(f"{label}: not finished")
            continue
        gap = lambda w: np.mean([pooled_balanced(c, w) for c in arms[first]], 0) - np.mean([pooled_balanced(c, w) for c in arms[second]], 0)
        point, boot = float(gap(ones)[0]), gap(draws)
        low, high = (float(v) for v in np.percentile(boot, [2.5, 97.5]))
        wins = sum(a > b for a, b in zip(summary[first]["by_fold"], summary[second]["by_fold"]))
        verdicts[label] = {"gap": point, "low": low, "high": high, "fold_wins": wins, "passes": low > 0,
                           "auc_gap": summary[first]["auc"] - summary[second]["auc"]}
        print(f"{label}: gap {point:+.3f} [{low:+.3f}, {high:+.3f}] {'PASS' if low > 0 else 'fail'}; "
              f"folds won {wins} of {FOLDS}; AUC gap {verdicts[label]['auc_gap']:+.3f}")
    atomic_write_text(out / "summary.json", json.dumps({"arms": summary, "rules": verdicts}, indent=1))


def reference_job(job):
    """The world model of independent_world_v0, given the facts as direct inputs, on one fold."""
    fold, seed = job
    torch.set_num_threads(1)
    world, samples, truth = W.load_world()
    names = sorted(o["name"] for o in world)
    held = fold_sets(names)[fold]
    train = [n for n in names if n not in set(held)]
    return {arm: W.run(arm, seed, world, samples, truth, train, held)["new"] for arm in ("names", "answers", "answers_shuffled", "geometry")}


def reference(out, workers):
    jobs = [(fold, seed) for fold in range(FOLDS) for seed in (1, 2)]
    with mp.Pool(workers) as pool:
        rows = pool.map(reference_job, jobs, chunksize=1)
    means = {arm: float(np.mean([r[arm] for r in rows])) for arm in rows[0]}
    by_fold = {arm: [float(np.mean([r[arm] for (f, _), r in zip(jobs, rows) if f == fold])) for fold in range(FOLDS)] for arm in rows[0]}
    print("world model with the facts as direct inputs, same folds, seeds 1 and 2 (mean of per-fold scores)")
    for arm, v in means.items():
        print(f"  {arm:17} {v:.3f}  by fold " + " ".join(f"{x:.3f}" for x in by_fold[arm]))
    atomic_write_text(out / "reference.json", json.dumps({"mean": means, "by_fold": by_fold}, indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--reference", action="store_true", help="world model on the same folds, for comparison")
    p.add_argument("--run", action="store_true")
    p.add_argument("--score", action="store_true")
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--workers", type=int, default=8)
    cli = p.parse_args()
    if cli.smoke:
        for block, (_, _, block_arms, _) in BLOCKS.items():
            for arm in block_arms:
                print(block, arm, run_job((cli.out, block, arm, 0, 1, 20, False))[1], flush=True)
        names = sorted(o["name"] for o in W.load_world()[0])
        print("fold sizes", [len(f) for f in fold_sets(names)], "objects covered", len(set().union(*fold_sets(names))))
    if cli.run:
        with directory_lock(cli.out), mp.Pool(cli.workers) as pool:
            for path, info in pool.imap_unordered(run_job, all_jobs(cli.out, STEPS), chunksize=1):
                print(path, info, flush=True)
    if cli.reference:
        reference(cli.out, cli.workers)
    if cli.score:
        score(cli.out)


if __name__ == "__main__":
    main()
