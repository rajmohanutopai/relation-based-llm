# World Simulator V1

Date: 2026-11-02

Experiment ID: `world_sim_v1`

Generator: `scripts/create_world_sim_v1.py` (imports the renderer, reach/sight
rules and quality checks from `scripts/create_world_sim_v0.py`)

Output (gitignored): `data/developmental_graph/experiments/world_sim_v1/`

## What changed from v0

**Physics with two causes**

| Task | v0 rule | v1 rule |
|---|---|---|
| push_moves | moves unless heavy | moves when push strength ≥ weight (light / a bit heavy / heavy × gentle / hard push) |
| push_rolls | round or "rolls" flag | round, tube-shaped or wheeled **and** on a smooth surface (floor, table, shelf); soft mats, rugs and beds stop it |
| shake_sound | the object is noisy | a solid thing is noisy, **or** a closed container has something hard inside (soft thing inside or empty → no sound) |
| drop, push | answers balanced by downsampling | the answer is drawn 50/50 first, then a case is picked uniformly among all objects × surfaces × push strengths with that answer |

New objects: bell, stool, watermelon, beach ball, rolling pin, toy truck, soup
can. New held-out objects: tambourine (WordNet nearest: toy truck), melon
(nearest: watermelon). The bottle now has a cap; the hand-written audit caught
that the v0 table missed it.

**New affect tasks**

- `feel_shortcut` (the "drug" case). Three kinds, chosen evenly:
  - Shortcut: flashing screens or self-blinking toys. The baby only watches,
    so activation is high (0.8) and relation gain is 0. Answer: "quick
    excitement but no new learning".
  - Fresh learning play: the baby's action causes an effect, gain 0.5.
    Answer: "happiness from learning something new".
  - Saturated learning play: done hundreds of times, gain near 0. Answer:
    "little happiness, because nothing new is left".

  One shortcut and two learning activities are held out for
  `test_new_object`.
- `choice_learn`: two options, each with a familiarity level and a count of
  today's plays. The answer is the option with the higher `0.5 * (1 -
  strength)`. In 30% of rows, one option is a flashing screen with zero gain.
  The order is random, and near-ties (gap < 0.05) are dropped. Options are
  limited to toys and safe household things.

**Noise for the sampler test**

`train_noise.jsonl` (1,600 rows) and `test_noise.jsonl` (400 rows) hold
`noise_blink` rows: a light blinks at random, and the answer is a coin flip.
Nothing in them can be learned. They are kept out of the main splits. The
happiness sampler should learn to ignore them; a plain surprise-seeking
sampler should keep chasing them.

**Wording**

Scene sentences for tracking, novelty, loss, shake and the new tasks now go
through the template picker (at least 4 options each), so `test_new_wording`
holds them out too. Its sentence overlap with train fell from 29% (v0) to 18%.

**Hand-written relation audit**

`handwritten_property_audit.json` checks the 364 hand-written 6mo relations
about world objects against the property table.

- 34 could be checked: 32 agree, 2 differ.
- "A bowl is usually round" is about shape, while the table's "round" means
  "rolls like a ball". This is a meaning gap, not an error.
- "A baby toothbrush has soft bristles": the table calls the toothbrush hard,
  which is true of the handle only.
- The first audit draft read "can be heard when tapped" as "rattles when
  shaken" and reported 19 false conflicts. That mapping was removed.

## Splits

| Split | Rows |
|---|---:|
| train | 16,501 |
| dev | 1,663 |
| test_iid | 1,231 |
| test_new_wording | 1,233 |
| test_new_object | 3,086 |
| train_noise / test_noise | 1,600 / 400 |

Train vocabulary: 442 words. Lint finds no issues. No test input appears in
train.

## Quality checks on test_new_object

| Task | Majority | Best single word | v0 best single word |
|---|---:|---:|---:|
| push_moves | 0.204 | 0.495 | 1.000 ("pot") |
| push_rolls | 0.179 | 0.528 | 0.054 (few rows, lopsided) |
| shake_sound | 0.239 | 0.244 | 0.910 ("key") |
| drop_loud | 0.369 | 0.846 | 0.885 |
| push_falls | 0.525 | 0.836 | 0.848 |
| touch_reach | 0.535 | 0.588 | 0.593 |
| see | 0.483 | 0.631 | 0.626 |
| feel_shortcut | 0.360 | 0.528 | (new) |
| choice_learn | 0.034 | 0.047 | (new) |
| track_location | 0.114 | 0.223 | 0.243 |

## Known weaknesses

- **drop_* and push_falls still lean on surface words** (single word
  0.6–0.85). The answer is "both A and B", so one factor alone predicts a lot.
  Any AND rule does this; a lower score would need rows where the surface
  word appears but doesn't decide (for example, a baby on the floor dropping
  something onto a table).
- **The feel_shortcut word bag scores 0.94 on held-out activities.** Words
  like "watches" and "first time" still separate the three kinds. A better
  test would use activities where the baby acts but the effect is random,
  which looks like play but teaches nothing.
- **The test sets are still generator-made.** A hand-written or reworded test
  set is still needed.
- **The 9,253 hand-written relations are audited, not used for scenes.**
  Only 364 mention world objects, and 34 of those map to a table field.

## Commands

```bash
.venv/bin/python scripts/create_world_sim_v1.py              # ~1 min
.venv/bin/python scripts/create_world_sim_v1.py --no-embeddings
```

## Decision

v1 is ready as the dataset for the first happiness-sampler run: random vs
fixed order vs happiness sampler, 4M nanochat, 3 seeds, a tight token budget,
with the noise files added to the sampler's pool. The next step is the sampler
code in the nanochat training loop.
