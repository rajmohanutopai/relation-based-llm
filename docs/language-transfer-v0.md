# Language Transfer V0

Date: 2026-11-07

Status: run complete (2026-11-07); no evidence that the facts help; main rule failed

Experiment ID: `language_transfer_v0`

## Why

In a physics world Claude didn't write, blind property answers helped a world model with objects
it had never met (`docs/independent-world-v0.md`). This asks the project's real question: does the
same knowledge help a small language model, when the facts and the outcomes arrive only as text?

## Data

The world, objects, split and answers from `independent_world_v0`, unchanged. 120 objects with
outcomes in training; 30 held out. Answers came from Claude and stay in this experiment's files,
apart from the hand-written rows. The user approved using them here.

Each row is a prompt and a one-word answer, for example:

```text
reebok breakpoint mid : pushed gently on a slippery table . did it move ?  ->  yes
```

The agent's noise stays: a training row takes one of the 6 physics runs at random.

## Arms

| Arm | Training text | Test prompt |
|---|---|---|
| plain_text | outcome rows only | name and question |
| facts_separate | 75% outcome rows, 25% fact rows such as "reebok breakpoint mid : is it large ?" | name and question |
| facts_separate_shuffled | the same, with facts on the wrong objects | name and question |
| facts_in_prompt | outcome rows with the object's facts written in the prompt | same form |
| facts_in_prompt_shuffled | the same, with facts of the wrong object | same form |

**In the two `facts_separate` arms, fact rows cover held-out objects too.** The model reads facts about
a new object, and never sees that object's outcomes. To use them, it must join two things learned apart.
That's the hard test, and the closest to the project's hypothesis. `facts_in_prompt` is the easy test:
the fact is right there.

## Fixed across arms

Same small GPT (`scripts/train_sampler_experiment.py`): 128 dims, 4 layers, 4 heads. Same vocabulary, built
from all arms' text, and same context length, so same parameter count. Same steps, batch 64, learning rate
1e-3, seeds 1–5. Only the text differs. `facts_separate` sees fewer outcome rows, which works against it.

## Gate (seed 1; no new-object score is computed or shown)

- G1: plain_text reaches at least 0.80 balanced accuracy on training objects.
- G2: facts_separate recalls at least 90% of facts about held-out objects.

Starting at 6,000 steps. If the gate fails, steps may rise, and that's the only tuning. Unless both pass,
L2 and L3 can't be read: the model wouldn't have learned what they test.

## Pass rules (new-object balanced accuracy; at least 4 of 5 seeds)

- **L1 easy:** facts_in_prompt beats facts_in_prompt_shuffled.
- **L2 hard, the main rule:** facts_separate beats facts_separate_shuffled.
- **L3:** facts_separate beats plain_text.

## Prediction (written before training)

- L1 passes, at about 0.60.
- L2 fails. A model this small rarely joins two separately learned facts: about 0.52.
- L3 fails.
- plain_text may beat 0.5 a little, since shared words such as "reebok" hint at the kind of object.

Moderate confidence.

## Limits, known now

- The text is templated, so this says little about ordinary language.
- Facts come from Claude, and the world is pushes only, with "heavy" meaning "big".
- The world-model result was small, so a null here may mean the signal is too weak, not that language can't
  carry it.

## Gate result: passed

A quick look at 1,500 steps passed (train 0.912, recall 0.995), showing no new-object score. The full run
used the written 6,000 steps and also meets both checks: plain_text train 0.936; facts_separate recall of
held-out facts 0.990 on average.

## Results (5 seeds, 952,192 parameters in every arm, `runs/language_transfer_v0/seed*/`)

| Arm | train | new objects | by seed |
|---|---:|---:|---|
| plain_text | 0.936 | 0.600 | 0.637, 0.633, 0.580, 0.630, 0.521 |
| facts_separate | 0.940 | 0.616 | 0.568, 0.685, 0.614, 0.631, 0.581 |
| facts_separate_shuffled | 0.930 | 0.605 | 0.569, 0.672, 0.635, 0.596, 0.556 |
| facts_in_prompt | 0.937 | 0.590 | 0.625, 0.535, 0.571, 0.640, 0.577 |
| facts_in_prompt_shuffled | 0.927 | 0.580 | 0.562, 0.628, 0.516, 0.596, 0.597 |

| rule | result | predicted |
|---|---|---|
| L1 facts_in_prompt beats its shuffled control | **fail** (3 of 5, mean +0.010) | pass, about 0.60 (**wrong**) |
| L2 facts_separate beats its shuffled control (main) | **fail** (3 of 5, mean +0.010) | fail, about 0.52 (right on the verdict; the score was far higher) |
| L3 facts_separate beats plain_text | **pass** (4 of 5, mean +0.016) | fail (**wrong**) |
| plain_text a little above 0.5 | 0.600, well above | a little |

**Reading:**

1. **This test shows no evidence that the facts help a small language model.** Both controlled rules fail. The
   model remembered the facts (99%), so forgetting isn't the cause. Real facts did no better than wrong facts by
   more than about 0.01, far below the spread between seeds.
2. **Don't read the L3 pass as a win.** It passes the written rule, but L3 has no control. Wrong facts also beat
   plain text in 3 of 5 seeds, and the gain is well inside seed spread. L2 is the rule that tests content.
3. **Writing the fact in the prompt didn't help either.** I expected this easy case to pass, and it failed. That
   suggests the trouble isn't only in joining two separately learned things.
4. **The words in names already carry much of this.** plain_text scored 0.600 with no facts, where the world model
   with opaque names scored 0.504. Words such as "mens", "reebok" and "perricone" hint at the kind of object, and
   so at its size. This is a likely reason the facts added little, but I haven't tested it.

**What this can't say:** with this seed spread, five seeds can't detect a gain near 0.01. A small real effect isn't
ruled out. The training text is templated, the model is small, and the signal was weak to begin with.

## A possible next test (not run)

Replace names with opaque labels in all arms. That removes the word shortcut, and matches the world-model test,
where facts did help. If facts then help, the words were hiding them. If not, the problem lies in carrying this
knowledge through language at this size.
