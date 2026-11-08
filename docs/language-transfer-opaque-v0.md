# Language Transfer Opaque V0

Date: 2026-11-08

Status: run complete (2026-11-08); main rule passed; the gain is small

Experiment ID: `language_transfer_opaque_v0`

## Why

In `docs/language-transfer-v0.md` the facts gave no clear gain, and plain text alone scored 0.600 on new
objects. Object names such as "reebok breakpoint mid" hint at the kind of object, and so at its size. That
may have left the facts nothing to add. The world model, which saw opaque names, gained from the facts.

This test replaces each name with one opaque token, so the facts are the only thing that can say anything
about a new object.

## Change from v0

- Each object's name becomes one token, `obj0` to `obj149`, by its place in the sorted name list. A held-out
  object's token never appears with an outcome.
- Three arms only: `plain_text`, `facts_separate`, `facts_separate_shuffled`. The prompt arms are dropped
  to save time; they failed in v0 and take three times as long.
- Everything else is as in v0: world, split, answers, wrong-object shuffle, model, steps (6,000), batch,
  learning rate, fact share (25%), seeds 1–5. The vocabulary is smaller, so the parameter count differs from
  v0, but it is the same in all three arms.

## Gate (read from the full run, as in v0)

- G1: plain_text reaches at least 0.80 on training objects.
- G2: facts_separate recalls at least 90% of facts about held-out objects.

If either fails, O1 and O2 can't be read.

## Pass rules (new-object balanced accuracy; at least 4 of 5 seeds)

- **O1, the main rule:** facts_separate beats facts_separate_shuffled.
- **O2:** facts_separate beats plain_text.
- **Check:** plain_text lands within 0.03 of 0.5. If not, the opaque names still leak something, and I'll
  say so.

## Prediction (written before training)

- plain_text near 0.50.
- O1 passes, with facts_separate about 0.55. A held-out token's only training is its facts, so if the model
  joins anything, it shows here.
- O2 passes.

Low confidence. A model this small may store facts as answers to a fact question and never link them to the
outcome question. If O1 fails, that is the likely reason.

## Limits, known now

- Same as v0: templated text, a small model, facts from Claude, a world of pushes where "heavy" means "big".
- Opaque tokens are less like real language than v0. This asks whether the link can form at all, not
  whether it forms from ordinary text.

## Results (5 seeds, 848,000 parameters in every arm, `runs/language_transfer_opaque_v0/seed*/`)

Gate: plain_text train 0.933 (G1 pass); facts_separate recall of held-out facts 0.985 (G2 pass).

| Arm | train | new objects | by seed |
|---|---:|---:|---|
| plain_text | 0.933 | 0.518 | 0.564, 0.494, 0.494, 0.519, 0.516 |
| facts_separate | 0.933 | 0.539 | 0.553, 0.580, 0.530, 0.541, 0.492 |
| facts_separate_shuffled | 0.936 | 0.508 | 0.539, 0.485, 0.500, 0.513, 0.503 |

| rule | result | predicted |
|---|---|---|
| O1 facts_separate beats shuffled (main) | **pass** (4 of 5, mean +0.031) | pass, about 0.55 (score 0.539) |
| O2 facts_separate beats plain_text | **fail** (3 of 5, mean +0.022) | pass (**wrong**) |
| Check: plain_text within 0.03 of 0.5 | **pass** (0.518) | yes |

**Reading:**

1. **The name words carried most of v0's score.** Plain text fell from 0.600 to 0.518 once names were opaque.
2. **With that shortcut gone, the content of the facts helps a little.** Real facts beat the same facts on the
   wrong objects in 4 of 5 seeds. So a model this small can join a fact and an outcome it learned apart, which I
   doubted in v0.
3. **The gain is small and uneven.** 0.031 on average, with one seed at +0.095 and one below zero. O2 failed
   because plain text had one lucky seed (0.564). The world model, given the same answers as direct inputs, gained
   more (0.569 against 0.498).

**What this can't say:** five seeds and one held-out set of 30 objects. Opaque tokens aren't ordinary language,
so this shows the link can form, not that it forms from real text. And the facts still come from Claude.
