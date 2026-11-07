# Sampler Experiment V2

Date: 2026-11-03

Experiment ID: `sampler_v2`

Trainer: `scripts/train_sampler_v2.py` (imports the model, data loading and
evaluation from `scripts/train_sampler_experiment.py`)

Data: `world_sim_v1`, with the 1,600 noise rows in the pool

Output (gitignored): `runs/sampler_v2/` (`summary.md`, per run `log.jsonl`,
`scores.jsonl`, `result.json`). The one-seed signal check is in
`runs/sampler_v2_check/`.

## Question

v1 tested one term of the happiness rule, measured it on 16 training rows, and
added forgetting to the score where plan.md subtracts it. With the full plan.md
rule and a cleaner measure, does choosing what to learn by happiness beat
random sampling?

## What changed from v1

- **Probes:** two sets of 64 rows per cluster. "Unseen" rows are taken out of
  the training pool. "Seen" rows stay in it.
- **Loss:** answer word(s) only, so a noise row is scored on its coin flip
  alone.
- **Smoothing:** a moving average (alpha 0.3), with change measured over the
  last 3 checks (150 steps).
- **Rule (plan.md):**
  - strength = exp(−unseen loss)
  - gain = fall in unseen loss × (1 − strength)
  - loss = rise in unseen loss × strength before
  - shortcut = how much more seen loss fell than unseen loss
  - activation = 0.02 × strength
- **Arms:** random; surprise (unseen loss); happiness = activation + gain −
  loss − shortcut; happiness_review = the same with + loss.
- **Budget:** 1,500 steps × batch 32, 3 seeds. The model, tokenizer, learning
  rate and evaluation are the same as v1.

**Pass rule, set before the run:** happiness beats random on curve area for
both test_iid and new objects, in all 3 seeds.

## Signal check

On one seed, happiness picks moved well away from even shares. feel_loss took
39% of picks at step 550, and "see" took 31% at step 1,050. v1 never went past
10%. So the measure now steers.

## Results (3 seeds)

| Arm | test_iid | new wording | new objects (stated) | noise picks | curve area iid | curve area new objects |
|---|---:|---:|---:|---:|---:|---:|
| random | **0.874** | 0.575 | **0.768** | 8.9% | **0.749** | **0.650** |
| surprise | 0.864 | **0.601** | 0.740 | 13.7% | 0.743 | 0.619 |
| happiness | 0.853 | 0.576 | 0.748 | 4.2% | 0.734 | 0.598 |
| happiness_review | 0.863 | 0.575 | 0.747 | 5.0% | 0.738 | 0.605 |

Per seed, random has the higher curve area on both measures in all 3 seeds,
against both happiness arms:

| Seed | random iid | happiness iid | review iid | random new obj | happiness new obj | review new obj |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0.739 | 0.726 | 0.728 | 0.647 | 0.587 | 0.594 |
| 2 | 0.755 | 0.739 | 0.737 | 0.640 | 0.608 | 0.621 |
| 3 | 0.753 | 0.737 | 0.748 | 0.663 | 0.598 | 0.601 |

New-object score at step 250: random 0.39–0.43, happiness 0.21–0.27. Most of
the gap opens in the first few hundred steps and closes by the end.

## Interpretation

1. **Happiness fails the pass rule.** It loses to random in every seed on
   both curve areas. The review variant does no better than the plan.md sign.
2. **The noise test now works, and happiness passes it.** Surprise chased the
   noise (13.7% of picks, up from 8.9% under random). Both happiness arms cut
   it to 4–5%. The rule does tell learnable from unlearnable.
3. **Avoiding noise didn't pay.** Random spends 9% of its steps on noise and
   still wins. In this world every task is learnable and the model has room
   for all of them, so a natural mix of rows is hard to beat. The steering cost
   more, mostly early, than it saved.
4. **The early dip.** In the first checks, every task's loss falls fast, so
   the scores mostly reflect which tasks happened to fall fastest. The sampler
   then puts weight on a few tasks and starves the rest. The new-object score
   at step 250 shows it.
5. **Fixed order was not rerun.** v1 already showed it losing by a wide margin.

## Decision

Per the pass rule, drop the happiness sampler as a way to choose training
rows. Keep the noise result: the rule tells learnable from unlearnable, which
is what an acting agent needs.

Next: test the rule as the reward of an acting agent in the simulator. There,
the agent's choices change what it sees, and an unlearnable source (a
flashing screen, a random light) can take up a real share of its time, so
avoiding it should matter more than it did here.
