#!/usr/bin/env python3
"""At which step from one made-up token to a real name is the carry-over of facts lost?

Design: docs/language-transfer-names-v0.md
Same model, training, folds and scoring as scripts/train_language_transfer_cv_v0.py; only the form of the names changes.

  --show          print a few names in each style, and the checks on rung 3
  --smoke         20 steps of every arm on fold 0; prints no new-object score
  --run           all jobs; finished jobs are skipped
  --score         tables and verdicts
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_language_transfer_cv_v0 as CV  # noqa: E402
from output_state import directory_lock  # noqa: E402

L = CV.L
OUT = Path("runs/language_transfer_names_v0")
SCRAMBLE_SEED = 20261111
RUNG0_GAP = 0.210  # one token per object, measured facts (docs/language-transfer-cv-v0.md)


def real_tokens(names):
    """Real names as token lists. Relies on CV.setup clearing L.OPAQUE before a style is built."""
    return {n: L.spoken(n).split() for n in names}


def two_unique(names):
    return {n: f"ka{i} zu{i}" for i, n in enumerate(names)}


def own_token(i, words, word):
    """A token only object i has. A word repeated inside a name stays one token."""
    return f"u{i}x{words.index(word)}"


def unique_var(names):
    tokens = real_tokens(names)
    return {n: " ".join(own_token(i, tokens[n], w) for w in tokens[n]) for i, n in enumerate(names)}


def shared_scrambled(names):
    """The real names' form, with shared tokens dealt to objects at random.

    A slot is "shared" if its real word is in more than one name. Each name keeps its length and which slots are
    shared; each shared token keeps how many names it is in; which names those are is random."""
    tokens = real_tokens(names)
    in_names = Counter(w for n in names for w in set(tokens[n]))
    shared_words = sorted(w for w, c in in_names.items() if c > 1)
    word_id = {w: j for j, w in enumerate(shared_words)}
    # one entry per (name, distinct shared word); repeats of a word inside a name stay repeats
    slots = [(n, w) for n in names for w in sorted(set(tokens[n])) if w in word_id]
    rng = random.Random(SCRAMBLE_SEED)
    for _ in range(1000):
        dealt = [word_id[w] for _, w in slots]
        rng.shuffle(dealt)
        new = {}
        for (n, w), j in zip(slots, dealt):
            new.setdefault(n, {})[w] = j
        if all(len(set(m.values())) == len(m) for m in new.values()):  # no token twice in one name by accident
            break
    else:
        raise SystemExit("could not deal shared tokens without repeats inside a name")
    out = {}
    for i, n in enumerate(names):
        out[n] = " ".join(f"s{new[n][w]}" if w in word_id else own_token(i, tokens[n], w) for w in tokens[n])
    return out


STYLES = {"two_unique": two_unique, "unique_var": unique_var, "shared_scrambled": shared_scrambled}
CV.NAME_STYLES.update(STYLES)
BLOCKS = {style: (style, "measured", ["facts_separate", "facts_separate_shuffled"], (1, 2)) for style in STYLES}
CV.BLOCKS.update(BLOCKS)
PAIRS = [(f"{style}: measured beat wrong-object measured", f"{style}/facts_separate", f"{style}/facts_separate_shuffled")
         for style in STYLES]


def show():
    names = sorted(o["name"] for o in CV.W.load_world()[0])
    L.OPAQUE.clear()
    real = real_tokens(names)
    for style, make in STYLES.items():
        L.OPAQUE.clear()
        made = make(names)
        print(style, "|", " | ".join(made[n] for n in names[:150:37]))
    L.OPAQUE.clear()
    made = {n: v.split() for n, v in shared_scrambled(names).items()}
    assert all(len(made[n]) == len(real[n]) for n in names), "lengths must match the real names"
    real_counts = sorted(Counter(w for n in names for w in set(real[n])).values())
    made_counts = sorted(Counter(w for n in names for w in set(made[n])).values())
    assert real_counts == made_counts, "each token must be in as many names as its real word was"
    # how much of the real sharing survives by chance: pairs of names sharing a token, before and after
    def sharing_pairs(tok):
        return {(a, b) for i, a in enumerate(names) for b in names[i + 1:] if set(tok[a]) & set(tok[b])}
    before, after = sharing_pairs(real), sharing_pairs(made)
    print(f"rung 3 checks pass: same lengths, same sharing counts. Pairs of names that share a token: "
          f"{len(before)} real, {len(after)} scrambled, {len(before & after)} in both")
    L.OPAQUE.clear()


def verdict(rule):
    if rule["low"] <= 0:
        return "gone"
    return "holds" if rule["gap"] >= RUNG0_GAP / 2 else "weakened"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--show", action="store_true")
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--run", action="store_true")
    p.add_argument("--score", action="store_true")
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--workers", type=int, default=9)
    cli = p.parse_args()
    if cli.show:
        show()
    if cli.smoke:
        for block, (_, _, arms, _) in BLOCKS.items():
            for arm in arms:
                print(block, arm, CV.run_job((cli.out, block, arm, 0, 1, 20, False))[1], flush=True)
    if cli.run:
        jobs = [(cli.out, block, arm, fold, seed, CV.STEPS, True)
                for seed in (1, 2) for block, (_, _, arms, _) in BLOCKS.items() for fold in range(CV.FOLDS) for arm in arms]
        with directory_lock(cli.out), mp.Pool(cli.workers) as pool:
            for path, info in pool.imap_unordered(CV.run_job, jobs, chunksize=1):
                print(path, info, flush=True)
    if cli.score:
        result = CV.score(cli.out, BLOCKS, PAIRS)
        print()
        for label, rule in result["rules"].items():
            print(f"{label.split(':')[0]:18} gap {rule['gap']:+.3f}, {rule['gap'] / RUNG0_GAP:.0%} of rung 0's: {verdict(rule)}")


if __name__ == "__main__":
    main()
