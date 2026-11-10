#!/usr/bin/env python3
"""Relation scaffolding with a job to do: the model states a new object's facts, then answers.

Design: docs/language-scaffold-v0.md
Folds, facts, name styles and scoring come from scripts/train_language_transfer_cv_v0.py.

  --smoke         20 steps of every arm on fold 0; prints no new-object score
  --run           all jobs; finished jobs are skipped
  --score         tables and verdicts
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import random
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_language_transfer_cv_v0 as CV  # noqa: E402
from output_state import atomic_write_text, directory_lock  # noqa: E402
from train_sampler_experiment import GPT  # noqa: E402

L, W = CV.L, CV.W
OUT = Path("runs/language_scaffold_v0")
FACT_KEYS = [f"{q}_{cut}" for q, _, cuts in CV.MEASURES for cut in cuts]
# one token per fact question, so a 12-fact list is 24 tokens: "long_over_15 yes long_over_24 no ..."
ASK = {f"{q}_{cut}": f"{q}_over_{cut}" for q, _, cuts in CV.MEASURES for cut in cuts}
TRAINED = ["direct", "scaffold", "scaffold_shuffled"]
DEVICE = torch.device("cpu")  # the Apple GPU was no faster for rows this short, and it isn't repeatable run to run
# block -> (name style, fact source, arms scored, seeds); scaffold_oracle is the scaffold model given true facts at test
BLOCKS = {"R_real": (False, "measured", TRAINED + ["scaffold_oracle"], (1, 2)),
          "O_opaque": (True, "measured", TRAINED + ["scaffold_oracle"], (1,))}
PAIRS = [("S1 real names: scaffold beats direct (main)", "R_real/scaffold", "R_real/direct"),
         ("S2 real names: scaffold beats wrong-fact scaffold", "R_real/scaffold", "R_real/scaffold_shuffled"),
         ("   real names: oracle minus scaffold", "R_real/scaffold_oracle", "R_real/scaffold"),
         ("   one token: scaffold beats direct", "O_opaque/scaffold", "O_opaque/direct"),
         ("   one token: scaffold beats wrong-fact scaffold", "O_opaque/scaffold", "O_opaque/scaffold_shuffled"),
         ("   one token: oracle minus scaffold", "O_opaque/scaffold_oracle", "O_opaque/scaffold")]


# --- rows: (token ids, [(position, target token id)]) -------------------------------------------------------


def prepare(style):
    """CV.setup, with the fact-question tokens added to the vocabulary."""
    samples, truth, names, facts, vocab, _ = CV.setup(style)
    vocab = L.Vocab([" ".join(vocab.itos[1:] + list(ASK.values()))])
    return samples, truth, names, facts, vocab


def name_ids(vocab, name):
    return vocab.encode(f"{L.spoken(name)} :")


def fact_row(vocab, name, answers):
    """<name> : long_over_15 yes long_over_24 no ...  One target per fact, at its question token."""
    ids, targets = name_ids(vocab, name), []
    for key in FACT_KEYS:
        ids = ids + [vocab.stoi[ASK[key]]]
        targets.append((len(ids) - 1, vocab.stoi[answers[key]]))
        ids.append(vocab.stoi[answers[key]])
    return ids[:-1], targets  # the last answer is a target only


def scaffold_prefix(vocab, name, answers):
    """<name> : <fact list with these answers> ."""
    listed = " ".join(f"{ASK[key]} {answers[key]}" for key in FACT_KEYS)
    return vocab.encode(f"{L.spoken(name)} : {listed} .")


def outcome_tail(vocab, action, surface, bit):
    return vocab.encode(f"{L.ACT[action]} on {L.SURF[surface]} . {L.QUESTION[bit]}")


def outcome_row(vocab, arm, case, bit, answer, table):
    prefix = name_ids(vocab, case[0]) if arm == "direct" else scaffold_prefix(vocab, case[0], table[case[0]])
    ids = prefix + outcome_tail(vocab, case[1], case[2], bit)
    return ids, [(len(ids) - 1, vocab.stoi[answer])]


def context_length(vocab, names, table):
    tail = max(len(outcome_tail(vocab, a, s, b)) for a in L.ACT for s in L.SURF for b in range(W.BITS))
    return max(len(scaffold_prefix(vocab, n, table[n])) for n in names) + tail + 2


# --- model calls ------------------------------------------------------------------------------------------------


def pad(seqs):
    x = torch.zeros(len(seqs), max(map(len, seqs)), dtype=torch.long)
    for i, s in enumerate(seqs):
        x[i, :len(s)] = torch.tensor(s)
    return x.to(DEVICE)


def states(model, ids):
    """The model's last-layer states at every position. Attention is causal, so padding after a row's end can't
    reach the positions before it."""
    x = model.tok(ids) + model.pos(torch.arange(ids.shape[1], device=ids.device))
    for block in model.blocks:
        x = block(x)
    return model.ln(x)


def rows_loss(model, rows):
    """Sum over rows of the mean loss over that row's answers, so each row counts once."""
    h = states(model, pad([ids for ids, _ in rows]))
    row = torch.tensor([i for i, (_, targets) in enumerate(rows) for _ in targets], device=DEVICE)
    pos = torch.tensor([p for _, targets in rows for p, _ in targets], device=DEVICE)
    tok = torch.tensor([t for _, targets in rows for _, t in targets], device=DEVICE)
    weight = torch.tensor([1 / len(targets) for _, targets in rows for _ in targets], device=DEVICE)
    return (F.cross_entropy(model.head(h[row, pos]), tok, reduction="none") * weight).sum()


@torch.no_grad()
def last_logits(model, seqs):
    h = states(model, pad(seqs))
    return model.head(h[torch.arange(len(seqs), device=DEVICE), torch.tensor([len(s) - 1 for s in seqs], device=DEVICE)]).cpu()


def train_model(arm, seed, steps, samples, truth, train, held, table, vocab, ctx):
    rng = random.Random(seed)
    torch.manual_seed(seed)
    model = GPT(len(vocab.itos), L.D, L.LAYERS, L.HEADS, ctx).to(DEVICE)
    opt = torch.optim.AdamW(model.parameters(), lr=L.LR, weight_decay=0.01)
    names = train + held
    cases = [c for c in truth if c[0] in set(train)]
    for _ in range(steps):
        facts, outcomes = [], []
        for _ in range(L.BATCH):
            if rng.random() < L.FACT_SHARE:
                name = rng.choice(names)
                facts.append(fact_row(vocab, name, table[name]))
            else:
                case = rng.choice(cases)
                bit = rng.randrange(W.BITS)
                result = rng.choice(samples[case])[bit]
                outcomes.append(outcome_row(vocab, arm, case, bit, "yes" if result else "no", table))
        # two passes, one per row type, so short rows aren't padded to the long ones; the gradient is the same
        loss = sum(rows_loss(model, rows) for rows in (facts, outcomes) if rows) / L.BATCH
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    model.eval()
    return model


# --- test ---------------------------------------------------------------------------------------------------------


@torch.no_grad()
def state_facts(model, vocab, names):
    """Ask the 12 fact questions after each name, feeding the model's own answers back in.
    Returns each name's '<name> : <its own fact list> .' and the answers it gave."""
    yes, no = vocab.stoi["yes"], vocab.stoi["no"]
    seqs = [name_ids(vocab, n) for n in names]
    said = [[] for _ in names]
    for key in FACT_KEYS:
        seqs = [s + [vocab.stoi[ASK[key]]] for s in seqs]
        logits = last_logits(model, seqs)
        for i, is_yes in enumerate((logits[:, yes] > logits[:, no]).tolist()):
            seqs[i].append(yes if is_yes else no)
            said[i].append("yes" if is_yes else "no")
    stop = vocab.encode(".")
    return {n: s + stop for n, s in zip(names, seqs)}, dict(zip(names, said))


@torch.no_grad()
def case_gaps(model, vocab, cases, prefix_for):
    """Yes-minus-no logit gap for every case and outcome, in the row form CV.load_arm reads."""
    yes, no = vocab.stoi["yes"], vocab.stoi["no"]
    rows = []
    for case in cases:
        logits = last_logits(model, [prefix_for(case[0]) + outcome_tail(vocab, case[1], case[2], bit) for bit in range(W.BITS)])
        rows.append([case[0], case[1], case[2], (logits[:, yes] - logits[:, no]).tolist()])
    return rows


def balanced(rows, truth):
    """Balanced accuracy over each (action, outcome) with both answers present, as L.balanced."""
    scores = []
    for action in W.ACTIONS:
        for bit in range(W.BITS):
            pairs = [(r[3][bit] > 0, truth[(r[0], r[1], r[2])][bit]) for r in rows if r[1] == action]
            pos = [p for p, t in pairs if t]
            neg = [not p for p, t in pairs if not t]
            if pos and neg:
                scores.append((sum(pos) / len(pos) + sum(neg) / len(neg)) / 2)
    return sum(scores) / len(scores)


def run_job(job):
    out, block, arm, fold, seed, steps, keep_scores = job
    path = CV.job_path(out, block, arm, fold, seed)
    if path.exists():
        return str(path), "skipped"
    torch.set_num_threads(1)
    style, source, _, _ = BLOCKS[block]
    samples, truth, names, facts, vocab = prepare(style)
    real, fake = facts[source]
    table = fake if arm.endswith("shuffled") else real
    held = CV.fold_sets(names)[fold]
    train = [n for n in names if n not in set(held)]
    ctx = context_length(vocab, names, real)
    t0 = time.time()
    model = train_model(arm, seed, steps, samples, truth, train, held, table, vocab, ctx)
    stated, said = state_facts(model, vocab, train + held)

    def recall(group):
        return sum(said[n][j] == table[n][key] for n in group for j, key in enumerate(FACT_KEYS)) / (len(group) * len(FACT_KEYS))

    prefix_for = (lambda n: name_ids(vocab, n)) if arm == "direct" else stated.__getitem__
    result = {"arm": arm, "seed": seed, "fold": fold, "block": block, "steps": steps, "seconds": round(time.time() - t0, 1),
              "params": sum(p.numel() for p in model.parameters()), "vocab": len(vocab.itos), "ctx": ctx,
              "recall_held": recall(held), "recall_train": recall(train),
              "train_acc": balanced(case_gaps(model, vocab, [c for c in truth if c[0] in set(train)], prefix_for), truth)}
    if keep_scores:
        new_cases = [c for c in truth if c[0] in set(held)]
        if arm == "scaffold":  # the same model with the true fact list supplied; written first, so the main file means both exist
            rows = case_gaps(model, vocab, new_cases, lambda n: scaffold_prefix(vocab, n, real[n]))
            oracle = dict(result, arm="scaffold_oracle", new_acc=balanced(rows, truth), cases=rows)
            atomic_write_text(CV.job_path(out, block, "scaffold_oracle", fold, seed), json.dumps(oracle))
        rows = case_gaps(model, vocab, new_cases, prefix_for)
        result.update({"new_acc": balanced(rows, truth), "cases": rows})
        atomic_write_text(path, json.dumps(result))
    return str(path), {k: v for k, v in result.items() if k in ("params", "vocab", "ctx", "seconds", "train_acc", "recall_held", "recall_train")}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--run", action="store_true")
    p.add_argument("--score", action="store_true")
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--workers", type=int, default=9)
    p.add_argument("--smoke-steps", type=int, default=20)
    cli = p.parse_args()
    if cli.smoke:
        for block in BLOCKS:
            for arm in TRAINED:
                print(block, arm, run_job((cli.out, block, arm, 0, 1, cli.smoke_steps, False))[1], flush=True)
    if cli.run:
        # the main block first, one seed at a time; the long scaffold runs before the short direct ones
        jobs = [(cli.out, block, arm, fold, seed, CV.STEPS, True)
                for block, seed in (("R_real", 1), ("R_real", 2), ("O_opaque", 1))
                for arm in ("scaffold", "scaffold_shuffled", "direct") for fold in range(CV.FOLDS)]
        with directory_lock(cli.out), mp.Pool(cli.workers) as pool:
            for path, info in pool.imap_unordered(run_job, jobs, chunksize=1):
                print(path, info, flush=True)
    if cli.score:
        CV.score(cli.out, BLOCKS, PAIRS)


if __name__ == "__main__":
    main()
