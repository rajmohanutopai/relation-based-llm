# Independent World V0

Date: 2026-11-07

Status: rules written; no physics run yet

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
