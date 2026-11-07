#!/usr/bin/env python3
"""Happiness-sampler experiment: does choosing what to learn by relation gain
beat random or fixed-order training?

One small GPT (about 4M params), one word-level tokenizer, one data pool and
one token budget for every arm. Only the sampler changes.

Arms
  random     uniform over all rows in the pool (noise rows included)
  fixed      roots first: clusters are added in a fixed order, physics before
             feelings, then sampled uniformly among the active clusters
  surprise   pick the clusters with the highest current loss (a plain
             "seek surprise" learner; expected to get stuck on noise)
  happiness  the plan.md rule per cluster:
               strength  = exp(-loss)            (how well the link is known)
               happiness = max(drop in loss, 0) * (1 - strength)
               sadness   = max(rise in loss, 0) * strength_before
               score     = happiness + sadness
             Sadness means a strong link is weakening, so the sampler goes
             back to it (replay).

Clusters are task types from world_sim_v1, plus one noise cluster
(noise_blink: random answers, nothing to learn).

Every arm sees the same probe rows to measure cluster loss, and those probes
cost no training steps.

Evaluation: answer-line exact match under teacher forcing (equal to greedy
decoding for the answer line), per task, on dev, test_iid, test_new_wording
and test_new_object.

test_new_object note: a from-scratch model has never seen the new words
(mug, melon, ...). Tasks whose facts are stated in the scene can still be
solved; tasks that need the object's own properties (drop, push, solid
shake) cannot. The summary reports these two groups separately.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

DATA = Path("data/developmental_graph/experiments/world_sim_v1")
OUT = Path("runs/sampler_v1")

# Fixed order for the "fixed" arm: physical roots first, feelings later.
FIXED_ORDER = [
    "touch_reach", "see", "push_moves", "push_rolls", "push_falls", "drop_loud", "drop_bounce", "drop_break",
    "shake_sound", "track_location", "feel_reach", "feel_novelty", "feel_loss", "feel_shortcut", "choice_learn",
]
STATED_TASKS = {"touch_reach", "see", "feel_reach", "track_location", "feel_novelty", "feel_loss",
                "feel_shortcut", "choice_learn"}
TOKEN_RE = re.compile(r"[a-z']+|[0-9]+|[.,?!;:\-]|\n")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def load(name: str) -> list[dict]:
    path = DATA / f"{name}.jsonl"
    return [json.loads(l) for l in path.open()] if path.exists() else []


class Vocab:
    def __init__(self, rows: list[dict]):
        counts = Counter(t for r in rows for t in tokenize(r["input"] + "\n" + r["target"]))
        self.itos = ["<pad>", "<eos>", "<unk>"] + sorted(counts)
        self.stoi = {t: i for i, t in enumerate(self.itos)}

    def encode(self, text: str) -> list[int]:
        return [self.stoi.get(t, 2) for t in tokenize(text)]


def encode_row(vocab: Vocab, row: dict) -> dict:
    prompt = vocab.encode(row["input"] + "\n")
    target = vocab.encode(row["target"]) + [1]
    first_line = vocab.encode(row["target"].split("\n")[0])
    return {"ids": prompt + target, "start": len(prompt), "answer_len": len(first_line),
            "task": row["task_type"]}


def make_batch(items: list[dict], device: str):
    n = max(len(x["ids"]) for x in items)
    ids = torch.zeros(len(items), n, dtype=torch.long)
    mask = torch.zeros(len(items), n, dtype=torch.bool)
    for i, x in enumerate(items):
        ids[i, : len(x["ids"])] = torch.tensor(x["ids"])
        mask[i, x["start"]: len(x["ids"])] = True
    return ids.to(device), mask.to(device)


# ---------------------------------------------------------------------------
# Model: small pre-norm GPT
# ---------------------------------------------------------------------------


class Block(nn.Module):
    def __init__(self, d: int, heads: int):
        super().__init__()
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv, self.proj = nn.Linear(d, 3 * d), nn.Linear(d, d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d))
        self.heads = heads

    def forward(self, x):
        b, t, d = x.shape
        q, k, v = self.qkv(self.ln1(x)).split(d, dim=2)
        q, k, v = (z.view(b, t, self.heads, d // self.heads).transpose(1, 2) for z in (q, k, v))
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.proj(y.transpose(1, 2).reshape(b, t, d))
        return x + self.mlp(self.ln2(x))


class GPT(nn.Module):
    def __init__(self, vocab: int, d: int, layers: int, heads: int, ctx: int):
        super().__init__()
        self.tok, self.pos = nn.Embedding(vocab, d), nn.Embedding(ctx, d)
        self.blocks = nn.ModuleList(Block(d, heads) for _ in range(layers))
        self.ln, self.head = nn.LayerNorm(d), nn.Linear(d, vocab, bias=False)

    def forward(self, ids):
        x = self.tok(ids) + self.pos(torch.arange(ids.shape[1], device=ids.device))
        for blk in self.blocks:
            x = blk(x)
        return self.head(self.ln(x))


def token_losses(model, ids, mask):
    """Per-row mean loss over target tokens."""
    logits = model(ids[:, :-1])
    loss = F.cross_entropy(logits.transpose(1, 2), ids[:, 1:], reduction="none")
    m = mask[:, 1:].float()
    return (loss * m).sum(1) / m.sum(1).clamp(min=1), logits


# ---------------------------------------------------------------------------
# Samplers
# ---------------------------------------------------------------------------


class Sampler:
    def __init__(self, arm: str, pool: dict[str, list[dict]], steps: int, rng: random.Random, args):
        self.arm, self.pool, self.steps, self.rng = arm, pool, steps, rng
        self.clusters = sorted(pool)
        self.loss_now: dict[str, float] = {}
        self.loss_prev: dict[str, float] = {}
        self.picks = Counter()
        self.temp, self.eps = args.temperature, args.epsilon
        self.history = deque(maxlen=3)

    def update_probe(self, losses: dict[str, float]):
        self.loss_prev = dict(self.loss_now) if self.loss_now else dict(losses)
        self.loss_now = dict(losses)

    def scores(self) -> dict[str, float]:
        out = {}
        for c in self.clusters:
            now, prev = self.loss_now.get(c, 5.0), self.loss_prev.get(c, 5.0)
            if self.arm == "surprise":
                out[c] = now
            else:  # happiness
                s_now, s_prev = math.exp(-now), math.exp(-prev)
                drop = prev - now
                happy = max(drop, 0.0) * (1 - s_now)
                sad = max(-drop, 0.0) * s_prev
                out[c] = happy + sad
        return out

    def weights(self, step: int) -> dict[str, float]:
        if self.arm == "random":
            total = sum(len(v) for v in self.pool.values())
            return {c: len(self.pool[c]) / total for c in self.clusters}
        if self.arm == "fixed":
            ordered = [c for c in FIXED_ORDER if c in self.pool]
            # Clusters join one at a time, evenly spaced; all are active by 80% of training.
            k = 1 + int(step / (self.steps * 0.8) * len(ordered))
            active = ordered[: min(k, len(ordered))]
            extra = [c for c in self.clusters if c not in FIXED_ORDER]  # noise keeps its natural pool share
            total = sum(len(v) for v in self.pool.values())
            extra_w = {c: len(self.pool[c]) / total for c in extra}
            rest = 1 - sum(extra_w.values())
            return {c: extra_w.get(c, rest / len(active) if c in active else 0.0) for c in self.clusters}
        sc = self.scores()
        top = max(sc.values()) or 1.0
        exps = {c: math.exp((v / top) / self.temp) for c, v in sc.items()}
        z = sum(exps.values())
        n = len(self.clusters)
        return {c: (1 - self.eps) * exps[c] / z + self.eps / n for c in self.clusters}

    def batch(self, step: int, size: int) -> list[dict]:
        w = self.weights(step)
        names = list(w)
        chosen = self.rng.choices(names, weights=[w[c] for c in names], k=size)
        self.picks.update(chosen)
        return [self.rng.choice(self.pool[c]) for c in chosen]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


@torch.no_grad()
def answer_accuracy(model, items: list[dict], device: str, bs: int = 128) -> dict[str, float]:
    model.eval()
    per_task = defaultdict(list)
    for i in range(0, len(items), bs):
        chunk = items[i: i + bs]
        ids, mask = make_batch(chunk, device)
        logits = model(ids[:, :-1])
        pred = logits.argmax(-1)
        for j, x in enumerate(chunk):
            s, n = x["start"], x["answer_len"]
            ok = bool((pred[j, s - 1: s - 1 + n] == ids[j, s: s + n]).all())
            per_task[x["task"]].append(ok)
    model.train()
    return {t: sum(v) / len(v) for t, v in per_task.items()}


@torch.no_grad()
def probe_losses(model, probes: dict[str, list[dict]], device: str) -> dict[str, float]:
    model.eval()
    out = {}
    for c, items in probes.items():
        ids, mask = make_batch(items, device)
        losses, _ = token_losses(model, ids, mask)
        out[c] = float(losses.mean())
    model.train()
    return out


def stratified(items: list[dict], per_task: int, rng: random.Random) -> list[dict]:
    by = defaultdict(list)
    for x in items:
        by[x["task"]].append(x)
    out = []
    for t, v in sorted(by.items()):
        rng.shuffle(v)
        out += v[:per_task]
    return out


def summarize(acc: dict[str, float], tasks: set[str] | None = None) -> float:
    vals = [v for t, v in acc.items() if t != "noise_blink" and (tasks is None or t in tasks)]
    return sum(vals) / len(vals) if vals else float("nan")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run(arm: str, seed: int, args, vocab: Vocab, encoded: dict[str, list[dict]], device: str) -> dict:
    rng = random.Random(seed)
    torch.manual_seed(seed)
    pool = defaultdict(list)
    for x in encoded["train"] + encoded["train_noise"]:
        pool[x["task"]].append(x)
    probe_rng = random.Random(0)  # same probe rows for every arm and seed
    probes = {c: probe_rng.sample(v, min(args.probe_rows, len(v))) for c, v in sorted(pool.items())}
    evals = {name: stratified(encoded[name], args.eval_per_task, random.Random(1))
             for name in ("dev", "test_iid", "test_new_wording", "test_new_object", "test_noise") if encoded[name]}

    model = GPT(len(vocab.itos), args.d_model, args.layers, args.heads, args.ctx).to(device)
    params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.1, betas=(0.9, 0.95))
    sampler = Sampler(arm, pool, args.steps, rng, args)
    sampler.update_probe(probe_losses(model, probes, device))

    out_dir = OUT / f"{arm}_s{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = (out_dir / "log.jsonl").open("w")
    tokens_seen, t0 = 0, time.time()
    curve = []
    for step in range(1, args.steps + 1):
        lr = args.lr * min(1.0, step / args.warmup) * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * step / args.steps)))
        for g in opt.param_groups:
            g["lr"] = lr
        items = sampler.batch(step, args.batch_size)
        ids, mask = make_batch(items, device)
        tokens_seen += int(mask.sum())
        losses, _ = token_losses(model, ids, mask)
        loss = losses.mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step % args.probe_every == 0:
            sampler.update_probe(probe_losses(model, probes, device))
        if step % args.eval_every == 0 or step == args.steps:
            point = {"step": step, "tokens": tokens_seen, "loss": round(float(loss.detach()), 4),
                     "seconds": round(time.time() - t0, 1)}
            for name, items_e in evals.items():
                acc = answer_accuracy(model, items_e, device)
                point[name] = {k: round(v, 4) for k, v in acc.items()}
                point[name + "_mean"] = round(acc.get("noise_blink", float("nan")) if name == "test_noise" else summarize(acc), 4)
                if name == "test_new_object":
                    point["test_new_object_stated_mean"] = round(summarize(acc, STATED_TASKS), 4)
            total_picks = sum(sampler.picks.values())
            point["noise_share"] = round(sampler.picks["noise_blink"] / total_picks, 4)
            point["pick_share"] = {c: round(n / total_picks, 4) for c, n in sorted(sampler.picks.items())}
            point["probe_loss"] = {c: round(v, 4) for c, v in sampler.loss_now.items()}
            log.write(json.dumps(point) + "\n")
            log.flush()
            curve.append(point)
            print(f"[{arm} s{seed}] step {step:5d} loss {float(loss.detach()):.3f} iid {point.get('test_iid_mean', 0):.3f} "
                  f"new_obj(stated) {point.get('test_new_object_stated_mean', 0):.3f} noise_share {point['noise_share']:.3f} "
                  f"({point['seconds']}s)", flush=True)
    log.close()
    final = curve[-1]
    result = {"arm": arm, "seed": seed, "params": params, "final": final, "curve": curve}
    (out_dir / "result.json").write_text(json.dumps(result, indent=1))
    return result


def report(results: list[dict], args) -> None:
    by_arm = defaultdict(list)
    for r in results:
        by_arm[r["arm"]].append(r)
    metrics = ["dev_mean", "test_iid_mean", "test_new_wording_mean", "test_new_object_stated_mean", "test_noise_mean", "noise_share"]
    lines = ["# Sampler experiment results", "",
             f"steps {args.steps}, batch {args.batch_size}, model d{args.d_model} L{args.layers} H{args.heads}, "
             f"params {results[0]['params']:,}, seeds {args.seeds}", "",
             "Final values, mean ± spread (min-max) across seeds.", "",
             "| arm | " + " | ".join(metrics) + " |", "|---|" + "---:|" * len(metrics)]
    for arm, rs in by_arm.items():
        cells = []
        for m in metrics:
            vals = [r["final"].get(m, float("nan")) for r in rs]
            mean = sum(vals) / len(vals)
            cells.append(f"{mean:.3f} ({min(vals):.3f}-{max(vals):.3f})")
        lines.append(f"| {arm} | " + " | ".join(cells) + " |")
    # Area under the learning curve on test_iid (higher = learned sooner).
    lines += ["", "Area under the test_iid curve (mean over eval points; higher means it learned sooner):", ""]
    for arm, rs in by_arm.items():
        aucs = [sum(p["test_iid_mean"] for p in r["curve"]) / len(r["curve"]) for r in rs]
        lines.append(f"- {arm}: {sum(aucs) / len(aucs):.3f} (seeds: {', '.join(f'{a:.3f}' for a in aucs)})")
    text = "\n".join(lines) + "\n"
    (OUT / "summary.md").write_text(text)
    print(text)


def main() -> None:
    global OUT
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arms", default="random,fixed,surprise,happiness")
    p.add_argument("--seeds", default="1,2,3")
    p.add_argument("--steps", type=int, default=3000)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--warmup", type=int, default=100)
    p.add_argument("--d-model", type=int, default=256)
    p.add_argument("--layers", type=int, default=4)
    p.add_argument("--heads", type=int, default=4)
    p.add_argument("--ctx", type=int, default=192)
    p.add_argument("--probe-every", type=int, default=50)
    p.add_argument("--probe-rows", type=int, default=16)
    p.add_argument("--eval-every", type=int, default=250)
    p.add_argument("--eval-per-task", type=int, default=60)
    p.add_argument("--temperature", type=float, default=0.3)
    p.add_argument("--epsilon", type=float, default=0.1)
    p.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    p.add_argument("--out", type=Path, default=OUT)
    args = p.parse_args()
    OUT = args.out

    names = ["train", "dev", "test_iid", "test_new_wording", "test_new_object", "train_noise", "test_noise"]
    raw = {n: load(n) for n in names}
    vocab = Vocab([r for v in raw.values() for r in v])
    encoded = {n: [encode_row(vocab, r) for r in v] for n, v in raw.items()}
    longest = max(len(x["ids"]) for v in encoded.values() for x in v)
    assert longest <= args.ctx, f"row of {longest} tokens exceeds ctx {args.ctx}"
    print(f"vocab {len(vocab.itos)}, train rows {len(encoded['train'])}, noise rows {len(encoded['train_noise'])}, device {args.device}")

    results = []
    for seed in [int(s) for s in args.seeds.split(",")]:
        for arm in args.arms.split(","):
            results.append(run(arm, seed, args, vocab, encoded, args.device))
    report(results, args)


if __name__ == "__main__":
    main()
