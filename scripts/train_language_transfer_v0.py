#!/usr/bin/env python3
"""Does a small language model use object facts on objects it has no outcomes for?

Design: docs/language-transfer-v0.md

  --gate [--steps N]     fit checks on seed 1; no new-object score is computed
  --seeds 1 --out DIR    all arms for those seeds
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acting_agent_independent_v0 as W  # noqa: E402
from output_state import atomic_write_text, claim_results  # noqa: E402
from train_sampler_experiment import GPT  # noqa: E402

OUT = Path("runs/language_transfer_v0")
ARMS = ["plain_text", "facts_separate", "facts_separate_shuffled", "facts_in_prompt", "facts_in_prompt_shuffled"]
PHRASE = {"heavy": "heavy", "large": "large", "tall_narrow": "tall and narrow", "flat_base": "flat based",
          "can_roll": "able to roll", "top_heavy": "top heavy", "grippy_surface": "grippy", "bouncy": "bouncy"}
ACT = {"push_gentle": "pushed gently", "push_hard": "pushed hard"}
SURF = {"slippery": "a slippery table", "grippy": "a grippy table"}
QUESTION = ["did it move ?", "did it roll over ?", "did it tip over ?"]
FACT_SHARE = 0.25
D, LAYERS, HEADS, BATCH, LR = 128, 4, 4, 64, 1e-3


# Filled by --opaque: each name becomes one token (docs/language-transfer-opaque-v0.md).
OPAQUE: dict[str, str] = {}


def spoken(name: str) -> str:
    if OPAQUE:
        return OPAQUE[name]
    return " ".join(w.lower() for w in re.findall(r"[A-Za-z0-9]+", name))


def load():
    world, samples, truth = W.load_world()
    names = sorted(o["name"] for o in world)
    held = sorted(random.Random(W.SPLIT_SEED).sample(names, W.HELD_OUT))
    train = [n for n in names if n not in set(held)]
    data = json.loads(W.ANSWERS.read_text())["answers"]
    wrong = names[:]
    random.Random(W.SHUFFLE_SEED).shuffle(wrong)
    real = {n: data[n] for n in names}
    fake = {n: data[w] for n, w in zip(names, wrong)}
    return samples, truth, train, held, real, fake


def facts_text(answers: dict) -> str:
    parts = []
    for prop, value in answers.items():
        if value == "yes":
            parts.append(f"it is {PHRASE[prop]} .")
        elif value == "no":
            parts.append(f"it is not {PHRASE[prop]} .")
    return " ".join(parts)


def prompt(name, case, bit, inline=None):
    middle = f"{inline} " if inline is not None else ""
    return f"{spoken(name)} : {middle}{ACT[case[1]]} on {SURF[case[2]]} . {QUESTION[bit]}"


def fact_rows(names, answers):
    return [(f"{spoken(n)} : is it {PHRASE[p]} ?", v) for n in names for p, v in answers[n].items() if v != "unsure"]


class Vocab:
    def __init__(self, texts):
        words = sorted({w for t in texts for w in t.split()})
        self.itos = ["<pad>"] + words
        self.stoi = {w: i for i, w in enumerate(self.itos)}

    def encode(self, text):
        return [self.stoi[w] for w in text.split()]


def build_vocab(truth, names, real, fake):
    texts = ["yes no"]
    for n in names:
        texts.append(f"{spoken(n)} {facts_text(real[n])} {facts_text(fake[n])}")
        texts += [q for q, _ in fact_rows([n], real)] + [q for q, _ in fact_rows([n], fake)]
    for a in ACT.values():
        for s in SURF.values():
            texts += [f"{a} on {s} . {q}" for q in QUESTION]
    return Vocab(texts)


def batch_tensors(rows, vocab):
    seqs = [vocab.encode(p) for p, _ in rows]
    n = max(map(len, seqs))
    ids = torch.zeros(len(seqs), n, dtype=torch.long)
    for i, s in enumerate(seqs):
        ids[i, :len(s)] = torch.tensor(s)
    return ids, torch.tensor([len(s) - 1 for s in seqs])


def answer_logits(model, rows, vocab, yes, no):
    ids, last = batch_tensors(rows, vocab)
    logits = model(ids)[torch.arange(len(rows)), last]
    return logits, logits[:, yes] - logits[:, no]


@torch.no_grad()
def balanced(model, names, truth, vocab, inline_for):
    """Balanced accuracy over each (action, bit), as in the world-model tests."""
    yes, no = vocab.stoi["yes"], vocab.stoi["no"]
    cases = [c for c in truth if c[0] in set(names)]
    scores = []
    for action in ACT:
        for bit in range(3):
            chosen = [c for c in cases if c[1] == action]
            rows = [(prompt(c[0], c, bit, inline_for(c[0])), None) for c in chosen]
            preds = []
            for i in range(0, len(rows), 256):
                preds += (answer_logits(model, rows[i:i + 256], vocab, yes, no)[1] > 0).tolist()
            y = [truth[c][bit] for c in chosen]
            pos = [p for p, t in zip(preds, y) if t]
            neg = [not p for p, t in zip(preds, y) if not t]
            if pos and neg:
                scores.append((sum(pos) / len(pos) + sum(neg) / len(neg)) / 2)
    return sum(scores) / len(scores)


@torch.no_grad()
def recall(model, rows, vocab):
    yes, no = vocab.stoi["yes"], vocab.stoi["no"]
    good = 0
    for i in range(0, len(rows), 256):
        chunk = rows[i:i + 256]
        d = answer_logits(model, chunk, vocab, yes, no)[1]
        good += sum((v > 0) == (a == "yes") for v, (_, a) in zip(d.tolist(), chunk))
    return good / len(rows)


def run(arm, seed, steps, data, vocab, ctx, score_new):
    samples, truth, train, held, real, fake = data
    rng = random.Random(seed)
    torch.manual_seed(seed)
    answers = fake if arm.endswith("shuffled") else real
    separate = arm.startswith("facts_separate")
    inline_on = arm.startswith("facts_in_prompt")
    inline_for = (lambda n: facts_text(answers[n])) if inline_on else (lambda n: None)
    facts = fact_rows(train + held, answers) if separate else []
    outcome_cases = [c for c in truth if c[0] in set(train)]
    model = GPT(len(vocab.itos), D, LAYERS, HEADS, ctx)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    t0 = time.time()
    for _ in range(steps):
        rows = []
        for _ in range(BATCH):
            if separate and rng.random() < FACT_SHARE:
                rows.append(rng.choice(facts))
            else:
                case = rng.choice(outcome_cases)
                bit = rng.randrange(3)
                result = rng.choice(samples[case])[bit]
                rows.append((prompt(case[0], case, bit, inline_for(case[0])), "yes" if result else "no"))
        logits, _ = answer_logits(model, rows, vocab, vocab.stoi["yes"], vocab.stoi["no"])
        target = torch.tensor([vocab.stoi[a] for _, a in rows])
        loss = F.cross_entropy(logits, target)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    model.eval()
    out = {"arm": arm, "seed": seed, "steps": steps, "seconds": round(time.time() - t0, 1),
           "params": sum(p.numel() for p in model.parameters()),
           "train_acc": balanced(model, train, truth, vocab, inline_for)}
    if separate:
        out["recall_held"] = recall(model, fact_rows(held, answers), vocab)
        out["recall_train"] = recall(model, fact_rows(train, answers), vocab)
    if score_new:
        out["new_acc"] = balanced(model, held, truth, vocab, inline_for)
    return out


def context_length(data, vocab):
    samples, truth, train, held, real, fake = data
    longest = max(len(vocab.encode(prompt(c[0], c, b, facts_text(a[c[0]])))) for c in truth for b in range(3) for a in (real, fake))
    return longest + 2


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gate", action="store_true")
    p.add_argument("--steps", type=int, default=6000)
    p.add_argument("--seeds", default="1,2,3,4,5")
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--opaque", action="store_true", help="one opaque token per object name")
    p.add_argument("--arms", default=",".join(ARMS))
    cli = p.parse_args()
    torch.set_num_threads(1)
    data = load()
    samples, truth, train, held, real, fake = data
    if cli.opaque:
        OPAQUE.update({n: f"obj{i}" for i, n in enumerate(sorted(train + held))})
    vocab = build_vocab(truth, train + held, real, fake)
    ctx = context_length(data, vocab)
    if cli.gate:
        print("vocab", len(vocab.itos), "ctx", ctx, flush=True)
        a = run("plain_text", 1, cli.steps, data, vocab, ctx, False)
        b = run("facts_separate", 1, cli.steps, data, vocab, ctx, False)
        print(a, b, sep="\n")
        g1, g2 = a["train_acc"] >= 0.8, b["recall_held"] >= 0.9
        print(f"{'PASS' if g1 else 'fail'} G1 train {a['train_acc']:.3f}; {'PASS' if g2 else 'fail'} G2 recall {b['recall_held']:.3f}")
        return
    path = cli.out / "results.json"
    claim_results(path, cli.overwrite)
    results = []
    for seed in [int(s) for s in cli.seeds.split(",")]:
        for arm in cli.arms.split(","):
            r = run(arm, seed, cli.steps, data, vocab, ctx, True)
            results.append(r)
            print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
            atomic_write_text(path, json.dumps(results))


if __name__ == "__main__":
    main()
