# Language Transfer CV V0

Date: 2026-11-10

Status: run complete (2026-11-10); all four main rules passed with opaque names: facts learned apart help on new
objects, and better facts help more. With real names of several words the facts don't carry over (addendum).

Experiment ID: `language_transfer_cv_v0`

## Why

Three results rest on one choice of 30 test objects: the physics-world test (`docs/independent-world-v0.md`)
and both language tests (`docs/language-transfer-v0.md`, `docs/language-transfer-opaque-v0.md`). A review on
2026-11-10 found that this choice was an unlucky one.

**The check** (`scripts/check_independent_world_splits.py`): the same world-model code and scoring, with only
the 30 held-out objects changed.

| World model | original 30 objects (5 seeds) | 60 other random choices of 30 (seed 1) |
|---|---:|---:|
| names | 0.504 | 0.516 |
| answers | 0.569 | 0.674 (5th–95th percentile 0.595–0.748) |
| answers on the wrong objects | 0.498 | 0.516 |
| geometry | 0.815 | 0.829 |

- The original numbers reproduce exactly.
- Answers beat wrong-object answers in 60 of 60 other choices, by 0.159 on average. The original gap was 0.071.
- Only 1 of the 60 other choices scored as low for answers as the original.

So the earlier reports understated what the answers carry by about half, and every language result inherited
that test set. A plain logistic fit agrees: it scores 0.72 from the answers when each of the 150 objects is held
out in turn, and 0.59 on the original 30.

A second point: the models answer "yes" when yes is more likely than no. Some outcomes are lopsided ("moved" is
true 89% of the time after a hard push), so a model can rank objects well and still say "yes" to nearly all. The
old score can't see that ranking. A rank-based score (AUC) can.

This experiment reruns the language test with every object held out once. It also runs the measured-facts test
the user approved on 2026-11-08.

## What changes from `language_transfer_opaque_v0`

Nothing in the model or training: same small GPT, 6,000 steps, batch 64, learning rate 1e-3, fact share 25%,
opaque object tokens. The changes:

- **Five test sets in turn.** Fold 0 is the original 30 held-out objects. The other 120 objects are shuffled once
  (seed 20261110) and dealt into folds 1–4. Each fold trains on the other 120. Every object is a new object once.
- **Two scores.** The old one: balanced accuracy at the model's own cut-off, now over all 150 objects. And AUC,
  taken inside each fold for each action and outcome, then averaged. Balanced accuracy stays the main score.
- **One vocabulary for every arm in a block,** built from all arms' text, so those arms have the same parameter
  count (852,352 with opaque names; 955,264 with real names). It is a little larger than before, so fold 0 won't
  match the old run to the last digit.

## Arms

Block A, the main test (opaque names, seeds 1 and 2):

| Arm | Fact rows in training |
|---|---|
| plain_text | none |
| facts_separate | Claude's blind answers (`answers.json`), for all 150 objects |
| facts_separate_shuffled | the same answers on the wrong objects |
| measured_separate | 12 measured yes/no facts per object |
| measured_separate_shuffled | the same measured facts on the wrong objects |

**Measured facts** come from the simulator's own model of each object: its three side lengths at rest, sorted,
and its mass. Each is cut at three fixed round numbers near the quartiles:

- long (longest side) over 15, 24, 29 cm
- wide (middle side) over 9, 13, 20 cm
- thick (shortest side) over 5, 8, 11 cm
- weight over 350, 750, 2000 g

A fact row reads `obj17 : is it over 24 cm long ?` with the answer `yes` or `no`. These are the same four
measurements the `geometry` world model used. Mass here is volume at a default density, so it adds little beyond
size. A logistic fit on these 12 facts scores 0.83 with each object held out in turn.

Block B (opaque names, seed 1): `facts_in_prompt` and `facts_in_prompt_shuffled`, with Claude's answers written
in the prompt. No fact rows.

Block C (real names, seed 1): `plain_text`, `facts_separate`, `facts_separate_shuffled`. This repeats
`language_transfer_v0`'s hard arms on all five test sets.

## Gate

- G1: plain_text reaches at least 0.80 on training objects (mean over runs).
- G2: each arm with true fact rows recalls at least 90% of the facts about its held-out objects (mean over runs).

## Pass rules (Block A)

For each pair, the gap is the difference in pooled balanced accuracy, averaged over the two seeds. Its 95%
interval comes from resampling the 150 objects 5,000 times. A rule passes when the whole interval is above zero.

- **C1, the main rule:** facts_separate beats facts_separate_shuffled.
- **C2:** measured_separate beats measured_separate_shuffled.
- **C3:** facts_separate beats plain_text.
- **C4:** measured_separate beats plain_text.

Also reported, with no pass rule: wins by fold, AUC for every arm, and Blocks B and C.

## Prediction (written before any run)

On the original test set the language model kept about 44% of the world model's gap (0.031 of 0.071). If that
share holds:

- plain_text and both shuffled arms: about 0.52.
- facts_separate: about 0.58. C1 and C3 pass.
- measured_separate: about 0.65. C2 and C4 pass.
- AUC: about 0.62 for facts_separate and 0.72 for measured_separate.
- Fold 0 is the weakest or second weakest fold for facts_separate.
- Block B: facts in the prompt beat their control, at about 0.60. Low confidence: a new object's name token is
  never trained in these arms, and the model may lean on names it has memorised.
- Block C: plain_text about 0.62 from the words in names; real facts add about 0.03 over wrong facts. I can't
  say whether that will be clear.

Moderate confidence in C2 and C4, lower in C1 and C3.

## Limits, known now

- I looked at the outcomes and answers for all 150 objects before writing this, through the logistic fit and the
  world-model check. The language model has not been run on folds 1–4. So this is a test of a forecast, not a
  blind test.
- The folds share training objects, so fold results aren't independent. The object resampling treats the trained
  models as fixed.
- Same as before: templated text, a small model, a world of pushes where "heavy" means "big". Claude wrote the
  answers. The measured facts come from the simulator, so they are true by construction.

## Addendum: Block D (written 2026-11-10 after Blocks A–C were scored, before Block D ran)

Blocks A–C left one cell empty: real names with measured facts. Block C (real names, Claude's answers, seed 1)
showed no clear gain: +0.020, with an interval from −0.018 to +0.057. That leaves two readings. Either the answers
add little because the words in a name already say what kind of thing it is, or a model this small can't tie
facts to a name of several words. Measured facts carry far more than names do, so they separate the two.

- **Block D** (real names, seeds 1 and 2): `measured_separate` and `measured_separate_shuffled`, as in Block A.
- **Block C gets seed 2,** so that both real-name blocks have two seeds, as Block A has. I add this having seen
  seed 1; the seed-1 scores are reported as designed.

Rules, same test as C1–C4:

- **D1:** with real names, measured facts beat wrong-object measured facts.
- **D2:** with real names, measured facts beat plain text.

Prediction: measured facts score about 0.64 with real names, against about 0.50 for wrong-object facts and 0.53
for plain text, so D1 and D2 pass; AUC about 0.75. Tying facts to a name of several words may lose some of what
Block A showed. With two seeds, the Block C gap for Claude's answers stays near +0.02 and its interval still
includes zero. Moderate confidence.

## Gate result: passed

- G1: plain_text reached 0.934 on training objects.
- G2: held-out facts were recalled at 0.990 (Claude's answers) and 0.963 (measured facts).

## Results, Blocks A–C as designed (75 runs, `runs/language_transfer_cv_v0/`)

"New objects" is balanced accuracy over all 150 objects, each scored by the model that never saw its outcomes.
0.5 means guessing.

**Block A: opaque names, 852,352 parameters in every arm, seeds 1 and 2**

| Arm | train | new objects | AUC | by fold (fold 0 is the old test set) | by seed |
|---|---:|---:|---:|---|---|
| plain_text | 0.934 | 0.506 | 0.536 | 0.514, 0.526, 0.516, 0.493, 0.519 | 0.485, 0.526 |
| facts_separate | 0.935 | **0.564** | 0.596 | 0.531, 0.590, 0.632, 0.505, 0.575 | 0.541, 0.586 |
| facts_separate_shuffled | 0.936 | 0.491 | 0.492 | 0.532, 0.485, 0.490, 0.466, 0.483 | 0.475, 0.507 |
| measured_separate | 0.939 | **0.688** | 0.804 | 0.705, 0.656, 0.716, 0.688, 0.696 | 0.664, 0.712 |
| measured_separate_shuffled | 0.937 | 0.478 | 0.473 | 0.480, 0.510, 0.505, 0.401, 0.531 | 0.488, 0.467 |

**Block B: opaque names, Claude's answers written in the prompt, seed 1**

| Arm | train | new objects | AUC |
|---|---:|---:|---:|
| facts_in_prompt | 0.937 | 0.563 | 0.636 |
| facts_in_prompt_shuffled | 0.937 | 0.481 | 0.467 |

**Block C: real names, Claude's answers, 955,264 parameters, seed 1**

| Arm | train | new objects | AUC |
|---|---:|---:|---:|
| plain_text | 0.939 | 0.530 | 0.581 |
| facts_separate | 0.941 | 0.548 | 0.582 |
| facts_separate_shuffled | 0.942 | 0.528 | 0.522 |

**Rules**

| rule | gap and 95% interval | result | folds won | predicted |
|---|---|---|---|---|
| C1 answers beat wrong-object answers (main) | +0.072 (+0.040 to +0.105) | **pass** | 4 of 5 | pass; I guessed 0.58 against 0.52, and got 0.564 against 0.491 |
| C2 measured beat wrong-object measured | +0.210 (+0.179 to +0.243) | **pass** | 5 of 5 | pass; I guessed 0.65, and got 0.688 |
| C3 answers beat plain text | +0.058 (+0.025 to +0.089) | **pass** | 5 of 5 | pass |
| C4 measured beat plain text | +0.182 (+0.151 to +0.212) | **pass** | 5 of 5 | pass |

Other forecasts:

- AUC: 0.596 for Claude's answers (I guessed 0.62) and 0.804 for measured facts (I guessed 0.72).
- Fold 0 was the second weakest fold for facts_separate, as forecast.
- Block B: prompt facts beat their control by 0.082 (+0.039 to +0.126), as forecast, at 0.563 where I guessed 0.60.
- Block C: plain text scored 0.530, far below my guess of 0.62 (**wrong**). Real facts beat wrong facts by 0.020
  (−0.018 to +0.057), which isn't clear. I had said I couldn't call it.

**The same facts as direct inputs** (the `independent_world_v0` world model on these folds, seeds 1 and 2;
`--reference`): names 0.504, answers 0.664, wrong-object answers 0.502, geometry 0.824.

## Reading

1. **A small language model uses facts it learned apart from any outcome.** With Claude's answers it scored 0.564
   on new objects, against 0.491 with the same answers on the wrong objects and 0.506 with none. Both gaps are
   clear, and both have the same sign in each seed.
2. **The earlier "small gain" was the old test set.** On fold 0 the real and wrong facts tie again (0.531 against
   0.532). On the other four folds real facts lead by 0.04 to 0.14.
3. **Better facts give a bigger gain.** Measured facts took the model to 0.688, and to 0.804 by rank. The facts
   set the ceiling, as the check of the world model suggested.
4. **The language model keeps about half of what the facts are worth as direct inputs:** 45% for Claude's answers
   (a gap of 0.072 where the world model's is 0.162) and 57% for measured facts (0.182 of 0.319).
5. **Facts learned apart did as well as facts in the prompt** (0.564 against 0.563). So the step of joining two
   things learned separately cost nothing here. A new object's name token is never trained in the prompt arms,
   which may hold them back.
6. **Wrong facts mislead.** Both wrong-object arms fell below plain text (0.491 and 0.478 against 0.506).
7. **With real names, Claude's answers add nothing clear.** Names alone gave 0.530, and 0.581 by rank, which is
   close to what the answers give with opaque names (0.596). Claude wrote the answers from the names, so they may
   hold little that the words don't. `language_transfer_v0` read 0.600 for plain text off the old test set; over
   all objects the words carry less than that. (The addendum results below show this cause is wrong.)
8. **The old score hides skill on lopsided outcomes.** Take "moved after a hard push", true 89% of the time. With
   measured facts the model ranks new objects well there (AUC 0.84), but it says yes 93–97% of the time, so its
   balanced accuracy on that outcome is 0.59.

## What this can't say

- Pooled scores moved by 0.02 to 0.05 between the two seeds. The intervals come from resampling objects and leave
  that out. The four Block A gaps are larger than that spread.
- I had seen every object's outcomes when I forecast, so the forecasts weren't blind.
- The world is narrow. One fact, "large", carries most of what Claude's answers hold, and the measured facts are
  sizes and a mass that follows size. This shows that a small model can carry facts across to things it has never
  seen act, when each thing has its own token. It doesn't show that a rich relation graph helps with ordinary text.

## Addendum results: Block D, and Block C with two seeds (35 more runs)

**Real names, 955,264 parameters in every arm, seeds 1 and 2**

| Arm | train | recall of held-out facts | new objects | AUC | by seed |
|---|---:|---:|---:|---:|---|
| plain_text | 0.935 | n/a | 0.536 | 0.574 | 0.530, 0.542 |
| facts_separate (Claude's answers) | 0.943 | 0.987 | 0.545 | 0.573 | 0.548, 0.542 |
| facts_separate_shuffled | 0.934 | 0.994 | 0.540 | 0.540 | 0.528, 0.552 |
| measured_separate | 0.939 | 0.976 | 0.518 | 0.524 | 0.511, 0.525 |
| measured_separate_shuffled | 0.934 | 0.973 | 0.505 | 0.510 | 0.526, 0.485 |

| rule | gap and 95% interval | result | predicted |
|---|---|---|---|
| D1 measured beat wrong-object measured, real names | +0.013 (−0.025 to +0.051) | **fail** | pass (**wrong**) |
| D2 measured beat plain text, real names | −0.018 (−0.051 to +0.016) | **fail** | pass (**wrong**) |
| Block C, two seeds: answers beat wrong-object answers | +0.005 (−0.022 to +0.033) | not clear | near +0.02, not clear (right) |
| Block C, two seeds: answers beat plain text | +0.008 (−0.024 to +0.042) | not clear | no forecast |

**Reading:**

1. **With real names the facts don't carry over, however good they are.** Measured facts took the model to 0.688
   with opaque names, and to 0.518 with real names. By rank that is 0.80 against 0.52. I forecast about 0.64, and
   was wrong.
2. **The model stores the facts all the same.** It recalled 98% of the facts about new objects under their real
   names. It doesn't use them when asked what a new object will do.
3. **So reading 7 above doesn't hold as the cause.** I suggested Claude's answers added little because the words
   in a name already said it. Measured facts say far more than the names do, and they failed too. The trouble is
   in how facts attach to a name of several words.
4. **Fact rows even cost a little of what the names gave.** By rank, plain text scored 0.574 with real names, and
   0.524 once measured fact rows were added.
5. **Why, I don't know.** Two candidates. With one token, a fact and an outcome both pass through that token's
   own vector, so what the facts write there is in reach of the outcome question. A name of several words has no
   single place like that, and nothing in training ties the two uses together. Or: the model can memorise each of
   the 120 training objects by name, so it never has to learn a rule from facts to outcomes. A run with made-up
   two-token names would tell these apart, and so would a world with many more objects and fewer looks at each.

**What the whole experiment says:** a small language model carries facts over to things it has never seen act
when each thing has its own token, and the better the facts, the more it carries. With ordinary names of several
words it carries nothing, in this set-up. The first language test's null result (`docs/language-transfer-v0.md`)
therefore stands for real names, and the opaque-name result is stronger than first reported.

**A test this points to:** the project's first idea was to have the model write out the relations before it
answers. In the April runs that made no difference, because the facts were already in the scene. Here they
aren't: the model knows the facts about a new object and fails to bring them to the question. Having it state the
object's facts first, then answer, is the usual remedy, and Block B shows that facts in the prompt do get used.
That is now the sharpest test of relation scaffolding in this repo. It hasn't been run.

**Later the same day:** both follow-ups ran. Names longer than a token or two are what blocks the carry-over
(`docs/language-transfer-names-v0.md`). And stating the facts first works: 0.716 against 0.544 with real names
(`docs/language-scaffold-v0.md`).
