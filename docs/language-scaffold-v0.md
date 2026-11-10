# Language Scaffold V0: State the Facts, Then Answer

Date: 2026-11-10

Status: run complete (2026-11-10); both rules passed in every fold; stating the facts first lets the model use them, with real names too

Experiment ID: `language_scaffold_v0`

## Why

The project's first idea was relation scaffolding: have the model write out the relations before it answers. In
the April runs it made no difference, because every fact the answer needed was already in the scene text.

`docs/language-transfer-cv-v0.md` found a case where the facts are not in front of the model. With real names the
model stores a new object's facts (98% recalled) and doesn't use them when asked what the object will do: 0.518
with measured facts against 0.505 with wrong-object facts. Facts written in the prompt did get used. So the test
is whether the model can do that writing itself.

## Rows

Facts are the 12 measured yes/no facts of `language_transfer_cv_v0`, always in the same order. Each fact
question is one token here, where it was six words there ("is it over 15 cm long ?"). The facts and the yes/no
answers are the same; the shorter form halves the running time. (Changed before any run.) An object's fact list
reads:

```text
long_over_15 yes long_over_24 no long_over_29 no wide_over_9 yes ... weight_over_2000 no
```

- **Fact row** (every object, new ones too): `<name> : <fact list>`. The model is trained on the 12 answers.
- **Direct outcome row** (training objects): `<name> : pushed gently on a slippery table . did it move ?`
- **Scaffold outcome row** (training objects): `<name> : <fact list> . pushed gently on a slippery table . did it
  move ?` The model is trained on the last answer only.

As before, 25% of rows are fact rows, and each row counts once however many answers it holds.

## Arms

| Arm | Fact rows | Outcome rows | Test on a new object |
|---|---|---|---|
| direct | true facts | direct | name, then the question |
| scaffold | true facts | scaffold | name; the model answers the 12 fact questions itself, one by one; then the question |
| scaffold_shuffled | wrong-object facts | scaffold, with those wrong facts | the same |

In the scaffold arms each fact's question token is supplied at test, as it is in training. Every yes or no in
the list is the model's own. No fact about a new object is given to it.

Also scored, with no extra training: **scaffold_oracle**, the scaffold model with the true fact list supplied at
test. The gap between it and scaffold is what the model's own slips cost.

`direct` differs from Block D of `language_transfer_cv_v0` only in the form of the fact rows: one row lists all
12 facts, with one-token questions. It should score about the same (0.518). It is here so that scaffold is
compared with a model that learned the facts in the same form.

## Blocks

- **Block R, the main test:** real names. This is where direct carry-over failed.
- **Block O:** one opaque token per object, where direct carry-over worked (0.688). It shows whether stating the
  facts adds anything when the model already uses them.

Same model, steps (6,000), batch, learning rate, folds and scoring as `language_transfer_cv_v0`. Block R uses
seeds 1 and 2. Block O uses seed 1 only: a scaffold run takes several times as long as the earlier runs, and
Block O carries no pass rule. (Changed before any run.) Within a block every arm has the same vocabulary and
parameter count.

## Gate

- The scaffold arm states at least 90% of a new object's facts correctly.
- Each arm reaches at least 0.80 on training objects.

## Pass rules (Block R; gap in pooled new-object balanced accuracy over both seeds; 95% interval above zero)

- **S1, the main rule:** scaffold beats direct.
- **S2:** scaffold beats scaffold_shuffled.

Reported with no rule: Block O, scaffold_oracle, AUC, scores by fold.

## Prediction (written before any run)

- New objects' facts are stated at 95% or better.
- Block R: direct about 0.52; scaffold about 0.64; scaffold_shuffled about 0.50. S1 and S2 pass. The oracle is
  within 0.02 of scaffold.
- Block O: direct about 0.68; scaffold about the same, within 0.03.

Moderate confidence, about two in three for S1. The way it could fail: on training objects the model can answer
from the memorised name and ignore the list in front of it, as it seemed to in `language_transfer_v0`'s prompt
arms. Measured facts predict outcomes much better than Claude's answers did, which should pull the model toward
using them.

## Limits, known now

- The fact questions are supplied in a fixed order. This tests whether the model can use what it states, not
  whether it would think to state it.
- The scaffold arms read about twice as many tokens per outcome row. They see the same number of rows and the
  same number of answers.
- Same narrow world, measured facts that are true by construction, templated text and small model as before.

## Gate result: passed

- The scaffold arm stated 99.9% of new objects' facts correctly with real names, and 99.8% with one-token names.
- Every arm reached 0.93 on training objects.

## Results (45 trainings, `runs/language_scaffold_v0/`)

"New objects" is balanced accuracy over all 150 objects, each scored by a model that never saw its outcomes.
0.5 means guessing.

**Block R: real names, 956,032 parameters in every arm, seeds 1 and 2**

| Arm | train | new objects | AUC | by fold (fold 0 is the old test set) | by seed |
|---|---:|---:|---:|---|---|
| direct | 0.934 | 0.544 | 0.597 | 0.568, 0.528, 0.560, 0.558, 0.541 | 0.526, 0.562 |
| scaffold | 0.930 | **0.716** | 0.831 | 0.733, 0.728, 0.754, 0.714, 0.680 | 0.704, 0.727 |
| scaffold_shuffled | 0.928 | 0.559 | 0.593 | 0.634, 0.493, 0.542, 0.538, 0.586 | 0.553, 0.565 |
| scaffold_oracle | 0.930 | 0.715 | 0.831 | 0.732, 0.728, 0.754, 0.714, 0.679 | 0.704, 0.726 |

**Block O: one opaque token per object, 852,864 parameters in every arm, seed 1**

| Arm | train | new objects | AUC | by fold |
|---|---:|---:|---:|---|
| direct | 0.936 | 0.550 | 0.624 | 0.598, 0.505, 0.518, 0.620, 0.541 |
| scaffold | 0.937 | **0.772** | 0.883 | 0.702, 0.784, 0.853, 0.758, 0.754 |
| scaffold_shuffled | 0.939 | 0.499 | 0.494 | 0.541, 0.496, 0.492, 0.504, 0.466 |
| scaffold_oracle | 0.937 | 0.773 | 0.883 | 0.702, 0.786, 0.853, 0.758, 0.754 |

**Rules**

| rule | gap and 95% interval | result | folds won | predicted |
|---|---|---|---|---|
| S1 scaffold beats direct, real names (main) | +0.172 (+0.127 to +0.214) | **pass** | 5 of 5 | pass; I guessed 0.64 against 0.52, and got 0.716 against 0.544 |
| S2 scaffold beats wrong-fact scaffold, real names | +0.157 (+0.115 to +0.197) | **pass** | 5 of 5 | pass; I guessed 0.50 for the control, and got 0.559 |

Other forecasts:

- Facts stated correctly: 99.9%, where I said 95% or better.
- The oracle matched scaffold to within 0.001, as forecast.
- Block O, direct: 0.550, where I guessed 0.68 (**wrong**).
- Block O, scaffold: 0.772, a gain of 0.222 (+0.180 to +0.263) over direct. I guessed it would add nothing (**wrong**).

For scale: with the same measured facts as direct inputs, the world model scores 0.824 on these folds, and a
logistic fit on the 12 yes/no facts scores 0.83.

## Reading

1. **Stating the facts first lets the model use what it knows.** With real names it went from 0.544 to 0.716 on
   new objects. Taught wrong-object facts, the same procedure gave 0.559. Both rules passed in every fold and in
   both seeds.
2. **The model's own statements were good enough.** It got 99.9% of a new object's facts right, so handing it the
   true list changed nothing (0.715).
3. **All of the gain is on new objects.** Every arm fits the training objects equally (0.93).
4. **It works for long names too** (split made after the run, so weak evidence). By name length, scaffold against
   direct: 0.811 against 0.604 for 1–2 tokens; 0.705 against 0.546 for 3–4; 0.715 against 0.498 for 5–6; 0.692
   against 0.530 for 7 or more. The long names were where direct carry-over failed in
   `docs/language-transfer-names-v0.md`.
5. **The form in which facts are learned matters for direct carry-over.** With one token per object, `direct`
   scored 0.550 here. In `language_transfer_cv_v0` the same facts, learned one question per row, gave 0.688. Here
   one row lists all 12. My guess, untested: in a list the model can read later answers off earlier ones (not
   over 15 cm, so not over 24), and writes less into the name itself.
6. **So stating the facts helped even where the name is one token:** 0.772 against 0.550, and 0.88 by rank. That
   is the highest new-object score any language arm has reached in this world.
7. **Lopsided outcomes still hide skill.** On "moved after a hard push" scaffold scores 0.57 at its own cut-off,
   against 0.83 on "moved after a gentle push".

## What this means

Relation scaffolding was the project's first idea, and this is its first clear result. It helps in the case it is
meant for: the model holds the relations and doesn't bring them to the question. In the April runs the relations
were already in the scene text, so writing them out again had nothing to add.

Together with `docs/language-transfer-names-v0.md`: asked directly, a model this small uses stored facts only
for things with a very short handle. Asked to state them first, it uses them whatever the name looks like.

## What this can't say

- **The model was told which questions to ask itself,** always the same 12 in the same order. Whether a model can
  pick the relations that matter is a harder test, and it is the one a relation graph would have to pass.
- **The facts were measured from the simulator,** so they are complete, true and to the point. Claude's answers
  and the hand-written rows are none of those. This run didn't try them.
- **The idea isn't new in general form.** Having a model write out steps before it answers is known as
  chain-of-thought or a scratchpad. What this adds is a clean case inside this project, with the control that
  wrong facts don't help.
- Same narrow world of pushes, templated text and small model. Block O has one seed. Pooled scores moved by 0.01
  to 0.04 between seeds in Block R, well under the gaps.
