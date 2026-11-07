#!/usr/bin/env python3
"""Sampler experiment v2: the full plan.md happiness rule, measured on unseen rows.

v1 (scripts/train_sampler_experiment.py) used one term of the rule, measured on
16 training rows per cluster, and added forgetting to the score. v2 fixes that.
The model, tokenizer, data, training loop and evaluation are imported from v1
unchanged, so only the sampler differs.

Measurement, every 50 steps, per cluster (task type, plus noise_blink):
  unseen probes  64 rows taken out of the training pool (never trained on)
  seen probes    64 rows that stay in the pool (trained on)
  loss           on the answer word(s) only: "answer: <this part>."
  smoothing      moving average (alpha 0.3); change is measured over the last
                 3 checks (150 steps)

The plan.md rule, from those numbers:
  strength   = exp(-unseen loss)
  gain       = max(fall in unseen loss, 0) * (1 - strength now)
  loss       = max(rise in unseen loss, 0) * strength before
  shortcut   = max(fall in seen loss - fall in unseen loss, 0)
               (learning that does not carry over to new rows)
  activation = a * strength now          (a = --activation, default 0.02)

Arms
  random            uniform over rows (as v1)
  surprise          softmax over unseen loss
  happiness         activation + gain - loss - shortcut      (plan.md sign)
  happiness_review  activation + gain + loss - shortcut      (forgetting pulls
                                                              the sampler back)

Softmax over score / max(|score|), temperature 0.3, plus a 10% even share.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_sampler_experiment as v1  # noqa: E402

OUT = Path("runs/sampler_v2")


def answer_span(x: dict) -> tuple[int, int]:
    """Token positions of the answer word(s): skip 'answer', ':' and the final '.'."""
    s = x["start"]
    return s + 2, s + x["answer_len"] - 1


@torch.no_grad()
def answer_losses(model, items: list[dict], device: str) -> float:
    model.eval()
    ids, _ = v1.make_batch(items, device)
    logits = model(ids[:, :-1])
    loss = F.cross_entropy(logits.transpose(1, 2), ids[:, 1:], reduction="none")
    m = torch.zeros_like(loss)
    for i, x in enumerate(items):
        a, b = answer_span(x)
        m[i, a - 1: b - 1] = 1.0  # logits at t predict token t+1
    model.train()
    return float(((loss * m).sum(1) / m.sum(1).clamp(min=1)).mean())


class Sampler:
    def __init__(self, arm, pool, rng, args):
        self.arm, self.pool, self.rng, self.args = arm, pool, rng, args
        self.clusters = sorted(pool)
        self.ema = {"unseen": {}, "seen": {}}
        self.hist = {"unseen": defaultdict(lambda: deque(maxlen=args.window + 1)),
                     "seen": defaultdict(lambda: deque(maxlen=args.window + 1))}
        self.picks = Counter()
        self.last_terms: dict[str, dict] = {}

    def update(self, kind: str, losses: dict[str, float]):
        a = self.args.alpha
        for c, v in losses.items():
            prev = self.ema[kind].get(c)
            self.ema[kind][c] = v if prev is None else a * v + (1 - a) * prev
            self.hist[kind][c].append(self.ema[kind][c])

    def terms(self, c: str) -> dict:
        hu, hs = self.hist["unseen"][c], self.hist["seen"][c]
        u_now, u_before = hu[-1], hu[0]
        fall_u, fall_s = u_before - u_now, hs[0] - hs[-1]
        s_now, s_before = math.exp(-u_now), math.exp(-u_before)
        return {"unseen_loss": u_now, "strength": s_now,
                "activation": self.args.activation * s_now,
                "gain": max(fall_u, 0.0) * (1 - s_now),
                "loss": max(-fall_u, 0.0) * s_before,
                "shortcut": max(fall_s - fall_u, 0.0)}

    def scores(self) -> dict[str, float]:
        out = {}
        for c in self.clusters:
            t = self.terms(c)
            self.last_terms[c] = t
            if self.arm == "surprise":
                out[c] = t["unseen_loss"]
            elif self.arm == "happiness":
                out[c] = t["activation"] + t["gain"] - t["loss"] - t["shortcut"]
            else:  # happiness_review
                out[c] = t["activation"] + t["gain"] + t["loss"] - t["shortcut"]
        return out

    def weights(self) -> dict[str, float]:
        if self.arm == "random":
            total = sum(len(v) for v in self.pool.values())
            return {c: len(self.pool[c]) / total for c in self.clusters}
        sc = self.scores()
        scale = max(abs(v) for v in sc.values()) or 1.0
        exps = {c: math.exp(v / scale / self.args.temperature) for c, v in sc.items()}
        z, n = sum(exps.values()), len(self.clusters)
        return {c: (1 - self.args.epsilon) * exps[c] / z + self.args.epsilon / n for c in self.clusters}

    def batch(self, w: dict[str, float], size: int) -> list[dict]:
        names = list(w)
        chosen = self.rng.choices(names, weights=[w[c] for c in names], k=size)
        self.picks.update(chosen)
        return [self.rng.choice(self.pool[c]) for c in chosen]


def build_pool(encoded, args):
    """Same pool and probes for every arm and seed."""
    by = defaultdict(list)
    for x in encoded["train"] + encoded["train_noise"]:
        by[x["task"]].append(x)
    prng = random.Random(0)
    pool, unseen, seen = {}, {}, {}
    for c, rows in sorted(by.items()):
        rows = rows[:]
        prng.shuffle(rows)
        unseen[c] = rows[: args.probe_rows]
        pool[c] = rows[args.probe_rows:]
        seen[c] = pool[c][: args.probe_rows]
    return pool, unseen, seen


def run(arm, seed, args, vocab, encoded, device):
    rng = random.Random(seed)
    torch.manual_seed(seed)
    pool, unseen, seen = build_pool(encoded, args)
    evals = {name: v1.stratified(encoded[name], args.eval_per_task, random.Random(1))
             for name in ("dev", "test_iid", "test_new_wording", "test_new_object", "test_noise") if encoded[name]}

    model = v1.GPT(len(vocab.itos), args.d_model, args.layers, args.heads, args.ctx).to(device)
    params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.1, betas=(0.9, 0.95))
    sampler = Sampler(arm, pool, rng, args)

    def probe():
        sampler.update("unseen", {c: answer_losses(model, v, device) for c, v in unseen.items()})
        sampler.update("seen", {c: answer_losses(model, v, device) for c, v in seen.items()})

    probe()
    out_dir = OUT / f"{arm}_s{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = (out_dir / "log.jsonl").open("w")
    slog = (out_dir / "scores.jsonl").open("w")
    tokens_seen, t0, curve = 0, time.time(), []
    w = sampler.weights()
    for step in range(1, args.steps + 1):
        lr = args.lr * min(1.0, step / args.warmup) * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * step / args.steps)))
        for g in opt.param_groups:
            g["lr"] = lr
        items = sampler.batch(w, args.batch_size)
        ids, mask = v1.make_batch(items, device)
        tokens_seen += int(mask.sum())
        losses, _ = v1.token_losses(model, ids, mask)
        loss = losses.mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step % args.probe_every == 0:
            probe()
            w = sampler.weights()
            if arm == "random":
                sampler.scores()  # fill terms for the log only
            slog.write(json.dumps({"step": step, "weights": {c: round(v, 4) for c, v in w.items()},
                                   "terms": {c: {k: round(v, 4) for k, v in t.items()}
                                             for c, t in sampler.last_terms.items()}}) + "\n")
        if step % args.eval_every == 0 or step == args.steps:
            point = {"step": step, "tokens": tokens_seen, "loss": round(float(loss.detach()), 4),
                     "seconds": round(time.time() - t0, 1)}
            for name, items_e in evals.items():
                acc = v1.answer_accuracy(model, items_e, device)
                point[name] = {k: round(v, 4) for k, v in acc.items()}
                point[name + "_mean"] = round(acc.get("noise_blink", float("nan")) if name == "test_noise"
                                              else v1.summarize(acc), 4)
                if name == "test_new_object":
                    point["test_new_object_stated_mean"] = round(v1.summarize(acc, v1.STATED_TASKS), 4)
            total = sum(sampler.picks.values())
            point["noise_share"] = round(sampler.picks["noise_blink"] / total, 4)
            point["pick_share"] = {c: round(n / total, 4) for c, n in sorted(sampler.picks.items())}
            log.write(json.dumps(point) + "\n")
            log.flush()
            slog.flush()
            curve.append(point)
            print(f"[{arm} s{seed}] step {step:5d} loss {float(loss.detach()):.3f} iid {point.get('test_iid_mean', 0):.3f} "
                  f"new_obj(stated) {point.get('test_new_object_stated_mean', 0):.3f} "
                  f"noise_share {point['noise_share']:.3f} ({point['seconds']}s)", flush=True)
    log.close()
    slog.close()
    result = {"arm": arm, "seed": seed, "params": params, "final": curve[-1], "curve": curve}
    (out_dir / "result.json").write_text(json.dumps(result, indent=1))
    return result


def report(results, args):
    v1.OUT = OUT
    v1.report(results, args)
    by_arm = defaultdict(list)
    for r in results:
        by_arm[r["arm"]].append(r)
    lines = ["", "Area under the test_new_object (stated) curve:", ""]
    for arm, rs in by_arm.items():
        aucs = [sum(p["test_new_object_stated_mean"] for p in r["curve"]) / len(r["curve"]) for r in rs]
        lines.append(f"- {arm}: {sum(aucs) / len(aucs):.3f} (seeds: {', '.join(f'{a:.3f}' for a in aucs)})")
    lines += ["", "Pick share per cluster (mean over seeds, whole run):", ""]
    clusters = sorted({c for r in results for c in r["final"]["pick_share"]})
    lines.append("| cluster | " + " | ".join(by_arm) + " |")
    lines.append("|---|" + "---:|" * len(by_arm))
    for c in clusters:
        cells = [f"{sum(r['final']['pick_share'].get(c, 0) for r in rs) / len(rs):.3f}" for rs in by_arm.values()]
        lines.append(f"| {c} | " + " | ".join(cells) + " |")
    text = "\n".join(lines) + "\n"
    with (OUT / "summary.md").open("a") as f:
        f.write(text)
    print(text)


def main():
    global OUT
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arms", default="random,surprise,happiness,happiness_review")
    p.add_argument("--seeds", default="1,2,3")
    p.add_argument("--steps", type=int, default=1500)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--warmup", type=int, default=100)
    p.add_argument("--d-model", type=int, default=256)
    p.add_argument("--layers", type=int, default=4)
    p.add_argument("--heads", type=int, default=4)
    p.add_argument("--ctx", type=int, default=192)
    p.add_argument("--probe-every", type=int, default=50)
    p.add_argument("--probe-rows", type=int, default=64)
    p.add_argument("--alpha", type=float, default=0.3)
    p.add_argument("--window", type=int, default=3)
    p.add_argument("--activation", type=float, default=0.02)
    p.add_argument("--eval-every", type=int, default=250)
    p.add_argument("--eval-per-task", type=int, default=60)
    p.add_argument("--temperature", type=float, default=0.3)
    p.add_argument("--epsilon", type=float, default=0.1)
    p.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    p.add_argument("--out", type=Path, default=OUT)
    args = p.parse_args()
    OUT = args.out

    names = ["train", "dev", "test_iid", "test_new_wording", "test_new_object", "train_noise", "test_noise"]
    raw = {n: v1.load(n) for n in names}
    vocab = v1.Vocab([r for v in raw.values() for r in v])
    encoded = {n: [v1.encode_row(vocab, r) for r in v] for n, v in raw.items()}
    print(f"vocab {len(vocab.itos)}, train rows {len(encoded['train'])}, device {args.device}")
    results = []
    for seed in [int(s) for s in args.seeds.split(",")]:
        for arm in args.arms.split(","):
            results.append(run(arm, seed, args, vocab, encoded, args.device))
    report(results, args)


if __name__ == "__main__":
    main()
