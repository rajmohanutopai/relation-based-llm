# Independent World V0

Date: 2026-11-07

Status: run complete (2026-11-07); all three rules passed; the gain is real and small

**Correction, 2026-11-10:** the 30 test objects used here were an unlucky choice. With the same code and 60 other
random choices of 30, answers scored 0.674 on new objects against 0.516 for answers on the wrong objects, and won
in 60 of 60. The numbers below (0.569 against 0.498) are right for this one test set, and understate the gain by
more than half. "Small" in the status line and the reading no longer holds. See the check at the end, and
`docs/language-transfer-cv-v0.md`.

Experiment ID: `independent_world_v0`

## Why

Blind Claude answers helped the world model: 0.779 on new objects against 0.648 for names
(`docs/object-properties-v0.md`). Three things weakened that result. Claude helped write
that world. I worded the questions knowing what the simulator meant. And the 7 fields were
the simulator's own rule inputs.

This test removes all three as far as I can.

## The world

- **Physics:** MuJoCo 4.0.0, a real physics engine.
- **Objects:** Google's Scanned Objects as MuJoCo models (kevinzakka/mujoco_scanned_objects,
  MIT, commit `6ff8d275`). 150 picked by a fixed random seed from all 1,030, with no hand
  filtering. The set contains many shoes and boxes, because the dataset does.
- **Actions:** a gentle push, a hard push, and a drop from 30 cm. Pushes use a fixed impulse,
  so heavier things move less.
- **Surfaces:** low friction (0.2) and high friction (1.0).
- **Noise:** each case runs 6 times with a random starting turn. The agent sees one of these
  at random. The truth for scoring is the majority of the 6.

**Outcomes, fixed now:**

| Action | Bit | True when |
|---|---|---|
| push | moved | centre travels more than 5 cm |
| push | rolled | total turning about a level axis exceeds 180° |
| push | tipped | its up direction ends more than 45° from the start |
| drop | rolled away | settles more than 10 cm sideways from where it first touched |
| drop | tipped | its up direction ends more than 45° from the start |

## Order of work

1. Sample the objects (done).
2. One fresh agent chooses the properties. It's told the actions, but not the outcomes, the
   objects or this project.
3. A second fresh agent answers them for each object name, with no files or tools. Neither
   agent sees any physics.
4. Answers are frozen in the repo.
5. Physics runs. The impulse sizes may be tuned once, on outcome rates only, so that every bit
   is true between 10% and 90% of the time. This is the only tuning. It happens before any
   score is computed.
6. Run the test once.

## Changes after calibration (before any score)

Calibration looked at 24 objects and outcome rates only.

- **Impulses:** gentle 0.5 N·s, hard 2.0 N·s. These are the only tuned values. At 3.0, "moved" was
  above 90%.
- **The drop action is out.** Both of its bits were false in every run, because objects start
  level and land level. They fail the 10–90% rule, and the design allowed tuning only impulses,
  so I didn't redesign the drop. This narrows the world to pushes.
- **Unstable runs are dropped.** MuJoCo resets a run that goes numerically unstable, which would
  give garbage. Such a run now counts for nothing; each case's truth and samples use the rest.
- **Masses:** the model files give none, so MuJoCo uses its default density on overlapping collision
  shapes. Calibration masses ran from 0.03 to 6.9 kg, median 0.8. So "heavy" here means "big", and
  the world's weights don't match the real objects.

## Test

A random agent acts for 3,000 steps, in rooms as in `docs/acting-agent-v1-design.md`, with the
same world-model network. 120 objects to learn on, 30 held out, split by fixed seed. 5 seeds.

| World model | Features |
|---|---|
| names | learned slot only |
| answers | the blind answers, plus a small learned slot |
| answers_shuffled | the same answers given to the wrong objects, plus a small slot |
| geometry | measured from the model: three sizes, mass, plus a small slot |

`answers_shuffled` is the control. If it matches `answers`, then the features help just by being
features, and the content doesn't matter. `geometry` shows what real measurements can give.

## Pass rules (at least 4 of 5 seeds)

- **R1:** answers beats names on new-object balanced accuracy.
- **R2:** answers beats answers_shuffled on new-object balanced accuracy. **This is the main rule.**
- **R3:** answers beats names on training curve area.

## Prediction (written before any physics)

- R1 passes, with a much smaller gain than before: about 0.60 against 0.55.
- R2 passes.
- R3 fails. The earlier gain on speed came with a table built for that world.
- geometry beats answers on new objects.

Low to moderate confidence. Rigid models also lack softness and breaking, so some properties
can't matter in this world.

## Limits, known now

- The models use one density assumption unless the files say otherwise, so "heavy" in this world
  may mean "big". A porcelain pot and a shoe may differ less than they really do.
- I chose the outcomes and thresholds, though before seeing any physics or answers.
- The answers still come from Claude. This removes Claude from the world, not from the graph.
- This is still no test of language.

## Results (5 seeds, `runs/independent_world_v0/seed*/`)

**World check before the test:** heavier objects moved less (correlation of log mass with moving,
−0.84), and things moved more on the slippery surface (60% against 44%). So the physics behaves
sensibly. Repeats of one case disagreed on about 6% of bits. The test ran once.

| World model | train curve area | train final | new objects | actions to 80% |
|---|---:|---:|---:|---:|
| names | 0.856 | 0.945 | 0.504 | ~740 |
| answers | **0.870** | 0.942 | **0.569** | ~610 |
| answers_shuffled | 0.844 | 0.942 | 0.498 | ~800 |
| geometry | 0.905 | 0.946 | 0.815 | ~130 |

New objects by seed: answers 0.612, 0.577, 0.558, 0.529, 0.570; names 0.500, 0.506, 0.506, 0.506,
0.506; shuffled 0.494, 0.463, 0.509, 0.509, 0.514. A score of 0.5 means guessing.

| rule | result | predicted |
|---|---|---|
| R1 answers beats names on new objects | **pass** (5 of 5) | pass; 0.569 against 0.504, where I guessed 0.60 against 0.55 |
| R2 answers beats shuffled on new objects (main rule) | **pass** (5 of 5) | pass |
| R3 answers beats names on train area | **pass** (5 of 5) | fail (**wrong**) |
| geometry beats answers on new objects | yes (5 of 5) | yes |

**Reading:**

1. **The content of the answers helps, in a world Claude didn't write.** The same answers on the wrong
   objects gave nothing (0.498), so the gain comes from what they say about each object.
2. **The gain is real but small.** About 0.07 above guessing on new objects, and about 130 fewer actions
   to reach 80%. In the earlier world, whose table Claude helped write, the gain was 0.13. Measured
   geometry reaches 0.815, so these answers carry only a fraction of what's available.
3. **Most of it may be size** (looked at after the test, so weak evidence). "large" agreed with measured
   length 95% of the time at an 18 cm cut-off, and "large" objects moved 62 points less often. In this
   world mass follows volume, so size decides most of what happens. "tall_narrow" also tracked real shape.
   "grippy_surface" lines up with outcomes, but the world gives every object the same friction, so that
   can only come through what kind of object it is, mostly shoes. "bouncy" never got a yes.

**What this removes:** Claude writing the world, and my wording of the questions.

**What remains:**

- The graph still comes from Claude, not from Rajmohan or any measured source.
- I chose the outcomes and thresholds, before seeing physics or answers.
- The world is narrow: pushes only, rigid objects, default density, so "heavy" means "big". A real pot and
  shoe of equal size would differ, and here they don't. Real masses might make the answers look better or
  worse.
- Five seeds and one 30-object held-out set. Another split could shift the size of the gain.
- This is not language.

## Check of the test set (2026-11-10, `scripts/check_independent_world_splits.py`)

The last limit above turned out to matter. The same world model and scoring, with only the 30 held-out objects
changed:

| World model | these 30 objects (5 seeds) | 60 other random choices (seed 1), mean and 5th–95th percentile |
|---|---:|---:|
| names | 0.504 | 0.516 (0.504–0.531) |
| answers | 0.569 | 0.674 (0.595–0.748) |
| answers_shuffled | 0.498 | 0.516 (0.459–0.567) |
| geometry | 0.815 | 0.829 (0.762–0.882) |

- Answers beat shuffled answers in 60 of 60 other choices, by 0.159 on average, against 0.071 here.
- 1 of the 60 scored as low for answers as this test set did.
- A class-balanced logistic fit on the answers gives 0.719 across the other choices and 0.593 here, so the low
  score belongs to these 30 objects and not to the world model.
- One fact does most of the work. In the same logistic fit across the 60 other choices, "large" alone scores 0.70
  and all eight facts together score 0.72; a fact that carries nothing scores about 0.57 there. On these 30
  objects "large" alone scores 0.57, which is why this test set was hard. So the earlier reading stands on what
  the gain is made of: mostly size.

**Revised reading:** blind answers take a world model from guessing to about 0.67 on objects it has never met,
where measured geometry reaches about 0.83. The gain is about twice what this report first said. It is still
mostly a judgement of size, in a world where size decides most outcomes.
