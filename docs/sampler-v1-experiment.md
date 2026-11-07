# Sampler Experiment V1

Date: 2026-11-02

Experiment ID: `sampler_v1`

Trainer: `scripts/train_sampler_experiment.py`

Data: `world_sim_v1` (16,501 train rows + 1,600 noise rows in the pool)

Output (gitignored): `runs/sampler_v1/` (`summary.md`, `<arm>_s<seed>/log.jsonl`,
`result.json`, `train.log`)

## Question

Does choosing what to learn by the plan.md happiness rule beat random or
fixed-order training, with everything else held the same?

## Setup

- **Model:** a small pre-norm GPT, d256, 4 layers, 4 heads, 3,481,088 params.
- **Tokenizer:** word-level, shared by every arm.
- **Training:** loss on target tokens only. AdamW at lr 1e-3, 100 warmup
  steps, cosine decay. 3,000 steps of batch 32 (about 6 passes). 3 seeds.
  Apple MPS, about 4.5 minutes per run.
- **Clusters:** the 15 task types, plus `noise_blink`.
- **Probes:** 16 fixed rows per cluster, measured every 50 steps, identical
  for every arm.

| Arm | Sampling |
|---|---|
| random | uniform over rows |
| fixed | roots first: clusters join one at a time in physics → feelings order, all active by 80% of training; noise keeps its natural 9% share |
| surprise | softmax over current probe loss (temperature 0.3, epsilon 0.1) |
| happiness | softmax over `max(drop,0) * (1 - exp(-loss)) + max(rise,0) * exp(-loss_before)` (same temperature and epsilon) |

**Evaluation:** answer-line exact match under teacher forcing, 60 rows per
task per split.

## Results (3 seeds)

| Arm | test_iid | new wording | new objects (stated facts) | noise picks | curve area (iid) |
|---|---:|---:|---:|---:|---:|
| random | **0.919** | **0.620** | **0.792** | 8.9% | **0.821** |
| happiness | 0.907 | 0.565 | 0.764 | 3.3% | 0.806 |
| surprise | 0.906 | 0.605 | 0.751 | 2.6% | 0.804 |
| fixed | 0.859 | 0.546 | 0.690 | 8.9% | 0.608 |

Early in training (mean over seeds):

| Step | random | happiness | surprise | fixed |
|---|---:|---:|---:|---:|
| 500 (test_iid) | 0.651 | 0.609 | 0.631 | 0.366 |
| 750 (test_iid) | 0.753 | 0.707 | 0.692 | 0.419 |
| 500 (new objects) | 0.576 | 0.469 | 0.496 | 0.177 |
| 750 (new objects) | 0.665 | 0.543 | 0.583 | 0.180 |

## Interpretation

1. **Fixed roots-first order clearly loses** on every measure and at every
   point. This agrees with the May 3 relation-curriculum result and with the
   BabyLM findings.
2. **The happiness sampler does not beat random.** It ties surprise and trails
   random at every point on the curve, most clearly early on.
3. **The happiness sampler barely chose.** Its picks stayed at 7–10% per
   cluster for the whole run, close to equal shares per task. Random gave the
   large feeling clusters 11–12% because they have more rows. With 16 probe
   rows every 50 steps, noise in the loss swamped real progress. So this
   tests a weak implementation more than it tests the formula.
4. **The noise test was flawed.** Noise rows have a fixed reason line that is
   easy to learn, and only the yes/no word is random. Their mean loss looked
   low, so surprise did not chase them. Both adaptive arms cut noise picks to
   about 3%, but this saved little.
5. **New-wording scores are low for every arm (0.55–0.62).** The models learn
   the templates more than the meaning.

## Decision

Treat fixed developmental ordering as not helpful at this scale.

Run one follow-up before judging the happiness sampler:

- 64 probe rows per cluster, smoothed over several probes.
- Noise scored on the answer word only.
- Finer clusters (task × object).
- 1,500 steps, 3 seeds.

If happiness still does not beat random, drop the sampler approach and test
happiness as the reward for an acting agent in the simulator.
