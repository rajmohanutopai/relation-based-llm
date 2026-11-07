# World Simulator V0

Date: 2026-11-02

Experiment ID: `world_sim_v0`

Generator: `scripts/create_world_sim_v0.py`

Output (gitignored): `data/developmental_graph/experiments/world_sim_v0/`

## Why

`root_bridge_600_v1` had five problems:

- Four task types made up two thirds of the rows.
- "Yes" or "no" was the answer in 46% of rows.
- One word often gave the answer away ("closed" means no).
- The 714 happiness rows had only 4 distinct answers.
- Lint found 9,611 sentences that start in lowercase.

V0 replaces template-first generation with a small simulated world. The
simulator computes each answer from world state, then writes sentences from
templates.

## How it works

World: a room, a baby (on the floor, a mat, a lap, or in a high chair), one
caregiver, objects on surfaces or inside containers, and covers.

Rules:

- **Touch:** the baby can touch a thing when it is near, at the baby's height,
  and not inside a closed container.
- **Sight:** a thing is hidden when it is under a cover, inside a closed
  opaque container, or inside an open opaque container across the room. A
  clear container shows what is inside even when closed.
- **Drop:** a drop is loud when a hard thing lands on a hard surface. It
  bounces when a bouncy thing lands on a hard surface. It breaks when a
  breakable thing lands on a hard surface.
- **Push:** a light thing moves. A round or wheeled thing rolls. A light thing
  on a high surface falls off.
- **Shake:** makes a sound only for things with parts that rattle or jingle.
- **Track:** the answer is the last place the caregiver put the thing, after
  two to four moves.

Affect follows `plan.md`:

```text
happiness_gain = 0.5 * (1 - strength), applied once per repeat
strength starts at: new 0.0, seen once 0.3, known well 0.75, favorite 0.9
labels: >=0.3 very happy and excited, >=0.15 happy, >=0.06 a little interested, else bored

sadness = strength * (1 + 0.15 * (links - 1)) * lasting
lasting: gone for good 1.0, gone for now 0.6, back right away 0.2
labels: >=0.8 very sad, >=0.45 sad, >=0.2 a little sad, else calm
```

Each novelty and loss row stores the numbers (`happiness_gain`,
`strength_after`, `sadness`) in its metadata, for the happiness-sampler
experiment.

## Lexical sources

| Source | Use |
|---|---|
| Curated property table | Size, weight, round, bouncy, hard, noisy, breakable. WordNet has no data on these. |
| WordNet | Checks each object's kind (container, food, toy, ...) through its hypernyms. It also picks the held-out test objects by Wu-Palmer similarity: mug~pot, orange~apple, slipper~shoe, fork~spoon, and so on. "block" is a known gap, since WordNet has no toy-block sense. |
| MiniLM word closeness | Ranks containers and rooms for an object, but only among options the rules allow. On its own it paired sock→cup and rattle→glass, so a container-fit table now decides what is allowed and closeness only orders it. Without embeddings, it falls back to room tags (`--no-embeddings`). |

## Design choices against shortcuts

- **Minimal pairs:** touch and sight rows come in pairs that differ in one
  fact. Some pairs keep the same answer, for example removing "closed" while
  the thing is still far away.
- **Decoys:** a second container, open or closed, that has no bearing on the
  question, so the cue words appear without deciding the answer.
- **Several facts per reason:** touch and sight reasons list every fact the
  rule used.
- **Balance:** no single answer may exceed the cap within a task. Yes/no tasks
  are held at 50/50 by construction.

## Splits

| Split | Rows | What differs from train |
|---|---:|---|
| train | 14,420 | |
| dev | 1,448 | new episodes, same objects and wording |
| test_iid | 1,026 | new episodes, same objects and wording |
| test_new_wording | 1,015 | every fourth template is held out (facts, actions, questions, frames) |
| test_new_object | 2,003 | 11 objects never seen in training |

No input appears in both train and a test split. Pair groups stay inside one
split. Training vocabulary: 321 words.

## Quality checks (from `quality_report.json`)

The best-single-word baseline asks whether one word gives the answer away.
The word-bag baseline uses all words, so it scores high whenever the answer
follows from the text, which is expected for rule-built data.

On `test_new_object`, for the reasoning tasks:

| Task | Majority | Best single word | Word bag |
|---|---:|---:|---:|
| touch_reach | 0.506 | 0.593 | 0.593 |
| see | 0.511 | 0.626 | 0.737 |
| feel_reach | 0.455 | 0.601 | 0.725 |
| track_location | 0.142 | 0.243 | 0.331 |
| feel_novelty | 0.414 | 0.534 | 0.873 |
| feel_loss | 0.446 | 0.584 | 1.000 |

No single word solves these tasks. The answer needs two or more facts
together.

## Known weaknesses

- **Single-object physics tasks** (push_moves, push_rolls, drop_*,
  shake_sound): the object's name alone decides the answer, because each
  object has fixed properties. Only the pot and the chair are heavy, so
  push_moves comes down to "pot" (single word 1.000). On new objects these
  tasks have few rows and lopsided answers. V1 needs more heavy, round and
  noisy objects, plus a second factor such as a soft vs hard surface for
  rolling.
- **feel_loss** is solvable with a word bag (1.000). The label follows from
  two phrases (familiarity and how lasting the loss is). That is rule-faithful,
  but it is still a shallow task.
- **Missing parts:** no shortcut ("drug") cases yet, and no noise cluster.
  Both are needed for the happiness-sampler test.
- **Prompts are still close to training:** `test_new_wording` shares 29% of
  its sentences with train, and `test_iid` shares 93%. A hand-written or
  LLM-reworded test set is still needed.
- **Narrow world:** 36 training objects. None of the 9,253 hand-written 6mo
  relations are used yet.

## Commands

```bash
.venv/bin/python scripts/create_world_sim_v0.py            # full run, ~1 min
.venv/bin/python scripts/create_world_sim_v0.py --no-embeddings
python3 scripts/create_world_sim_v0.py --audit <folder with train.jsonl and test files>
```

## Decision

Use `world_sim_v0` as the base for the first happiness-sampler run once v1
adds shortcut cases, a noise cluster, and the physics fixes. Do not train a
comparison on v0 alone.
