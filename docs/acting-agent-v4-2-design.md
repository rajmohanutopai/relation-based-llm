# Acting Agent V4.2: Design

Date: 2026-11-07

Status: run complete (2026-11-07); noise fix confirmed; the peak itself did not matter; re-forming explains fading's harm

Experiment ID: `acting_agent_v4_2`

## Why v4.2

v4.1 left three open points:

1. **The best version was picked after seeing the data.** `--S` needs new seeds.
2. **The peak may not be the active part.** The S-curve also stops paying soon, so
   a plain payment that runs out as fast might do as well.
3. **Fading raised gadget time,** perhaps because a dissolved link pays again when
   it forms again. That was a guess.

**A flaw in my v4.1 summary.** In `--S`, forming a link still pays about 0.7, more
than the 0.35 on the second confirmation. So `--S` doesn't have the user's spike as
its largest payment. Only `L-S` does (0.11 to form, then 0.35). The peak test
therefore runs both ways.

## Versions

World and shared parts as in v4.1. New seeds 6–10, none used before in this line.

| Version | Forming pays | Fading | Confirmations pay |
|---|---|---|---|
| `---` (v3.1) | strength | no | v3 rise |
| `--S` | strength | no | S-curve: 0.35, 0.14, 0.03 |
| `L-S` | 0.11 | no | S-curve |
| `--flat` | strength | no | flat: 0.17, 0.17, 0.17, then nothing |
| `L-flat` | 0.11 | no | flat |
| `-F-` | strength, each time | yes | v3 rise |
| `-F-first` | strength, first time only | yes | v3 rise |
| `-FS` | strength, each time | yes | S-curve |
| `-FS-first` | strength, first time only | yes | S-curve |

Flat pays the same total as the S-curve over the same three confirmations, with
each thing counted once. It removes the peak and keeps the running out.

Rivals: random and surprise, on the `---` store, on the same seeds.

110 runs: 9 happiness versions + 2 rivals, × 2 conditions × 5 seeds.

## Gate

The hooks added to `scripts/acting_agent_v4_1.py` must not change it. `---`, `--S`
and `-FS` must match the v4.1 results curve for curve on seed 1, condition A.

## Pass rules (written before running; condition A; at least 4 of 5 seeds)

- **R1 confirmed:** `--S` and `L-S` each spend less time on gadgets than random.
- **R2 learning:** `--S` beats `---` on area, in A, and also isn't more than 0.01
  below it on average in B.
- **R3 peak:** the peak matters if `L-S` spends less time on gadgets than `L-flat`,
  in at least 4 of 5 seeds, and by at least 2 points on average. Same test for `--S`
  against `--flat`. `L-S` against `L-flat` is the fair test of the user's idea.
- **R4 re-forming:** re-forming explains fading's harm if, in both pairs, the
  first-only version spends less time on gadgets than the pay-again version in at
  least 4 of 5 seeds, and removes at least half of the rise over the version
  without fading (`-F-` over `---`, `-FS` over `--S`) on average.
- **R5 rival:** `--S` and `L-S` beat surprise on area, in A and in B.

## Prediction (written before running)

I got the main v4.1 predictions wrong, so these carry low confidence.

- R1: passes for `L-S`. Passes for `--S`, narrowly.
- R2: passes in A. Unsure in B.
- R3: fails. Flat does about as well, because running out is what matters.
- R4: passes on the `-F-` pair. Even odds on the `-FS` pair.
- R5: fails.

## Gate result (2026-11-07): passed

`---`, `--S` and `-FS` matched v4.1 curve for curve on seed 1, condition A.

## Results (seeds 6–10, `runs/acting_agent_v4_2/seed*_*/`)

Random: A gadget time 17.6%, area 0.721, final 0.812; B 19.1%, 0.710, 0.806.
Surprise: A gadget time 31.5%, area 0.775, final 0.863; B 28.0%, 0.747, 0.852.

| version | A gadget time | below random | A area | A final | B gadget time | B area | B final |
|---|---:|---:|---:|---:|---:|---:|---:|
| `---` | 25.1% | 0 / 5 | 0.757 | 0.813 | 16.1% | 0.724 | 0.792 |
| `--S` | 16.1% | **5 / 5** | 0.750 | 0.833 | 17.1% | 0.733 | 0.820 |
| `L-S` | 13.2% | **5 / 5** | 0.757 | 0.833 | 17.1% | 0.717 | 0.802 |
| `--flat` | 16.0% | **5 / 5** | 0.754 | 0.824 | 16.6% | 0.727 | 0.800 |
| `L-flat` | 12.9% | **5 / 5** | 0.754 | 0.842 | 17.1% | 0.713 | 0.799 |
| `-F-` | 27.9% | 0 / 5 | 0.749 | 0.806 | 16.1% | 0.728 | 0.800 |
| `-F-first` | 25.5% | 0 / 5 | 0.731 | 0.807 | 15.9% | 0.727 | 0.786 |
| `-FS` | 19.6% | 0 / 5 | 0.725 | 0.813 | 15.6% | 0.712 | 0.788 |
| `-FS-first` | 17.6% | 3 / 5 | 0.739 | 0.814 | 15.8% | 0.709 | 0.777 |

| rule | result | predicted |
|---|---|---|
| R1 `--S` and `L-S` below random | **pass** (5 / 5 each) | pass |
| R2 `--S` beats `---` on area in A; no more than 0.01 lower in B | **fail**: 2 / 5 in A (B is 0.009 higher) | pass in A (**wrong**) |
| R3 the peak matters | **fail**: `L-S` beats `L-flat` in 1 / 5, gap −0.4 points; `--S` beats `--flat` in 2 / 5, gap −0.1 | fail (right) |
| R4 re-forming explains fading's harm | **pass**: 5 / 5 in both pairs, removing 86% and 57% of the rise | pass, even odds on the second |
| R5 beats surprise | **fail**: 1 / 5 in A and in B, for both | fail (right) |

**Reading:**

1. **The noise fix holds on new seeds.** Payments that run out keep the baby off gadgets.
2. **The peak isn't what does it.** A flat payment over the same three confirmations
   does as well. Happiness that saturates after a few different things confirm a link
   fixes the noise. This run doesn't support a large spike on the second confirmation
   being needed; it says nothing about whether people feel one.
3. **`--S` was not the better learner I suggested.** Its v4.1 lead on speed in A
   didn't return (0.750 against 0.757 for `---`). It does end higher: 0.833 against 0.813
   in A, 0.820 against 0.792 in B. Saturation seems to help final knowledge a little,
   not speed. That's an after-the-fact reading on 5 seeds.
4. **Fading itself is less to blame than the repeated pay.** Paying only the first
   forming removes most of its harm, though fading still doesn't help.
5. **Surprise leads clearly on these seeds,** by more than on seeds 1–5.

`dissolved` counts in these runs predate the fix for bug SM-5 in
`docs/state-machines.md`. Scores and gadget time aren't affected.
