# Language Transfer Names V0: Why Real Names Block the Facts

Date: 2026-11-10

Status: run complete (2026-11-10); the carry-over is lost at rung 2: names longer than a token or two

Experiment ID: `language_transfer_names_v0`

## Why

In `docs/language-transfer-cv-v0.md` a small language model carried measured facts over to new objects when each
object was one made-up token (0.688 against 0.478 for wrong-object facts). With real names it carried nothing
(0.518 against 0.505), though it recalled 98% of the facts. This experiment looks for the step at which the
carry-over is lost.

## What is already known (from the saved runs, no new training)

The model is trained from scratch, so a real word means no more to it than a made-up token. "Real names" differ
from one made-up token only in their form:

1. a name has several tokens (1 to 17, median 5);
2. names vary in length;
3. some tokens are shared between objects ("game" is in 11 names, "reebok" in 6);
4. the sharing follows kinds of object, so shared tokens say something about outcomes.

One guess was that a real name has no token of its own to hold the facts. That is wrong: 143 of the 150 names
contain a word no other name has. For those 143, measured facts still gave 0.516 against 0.507 for wrong-object
facts.

## The ladder

Each rung adds one of the four properties. All rungs use made-up tokens, measured facts, and the same model,
training, folds and scoring as `language_transfer_cv_v0`.

| Rung | Names | Adds |
|---|---|---|
| 0 | one token of its own: `obj17` | (done: 0.688 against 0.478) |
| 1 `two_unique` | two tokens of its own: `ka17 zu17` | several tokens |
| 2 `unique_var` | as many tokens as the real name has, all its own: `u17x0 u17x1 u17x2` | varying length, up to 17 |
| 3 `shared_scrambled` | the real name's form, token for token, but shared tokens are dealt to objects at random (seed 20261111) | shared tokens that say nothing |
| 4 | real names | shared tokens that follow kinds of object (done: 0.518 against 0.505) |

In rung 3 every name keeps its length, and each slot stays "own" or "shared" as in the real name. Each shared
token still appears in as many names as before. Only which objects share it changes.

Arms per rung: `measured_separate` and `measured_separate_shuffled`. Seeds 1 and 2, five folds: 60 runs.

## Rules

For each rung, the gap is measured facts minus wrong-object measured facts on pooled new-object balanced accuracy,
with a 95% interval from resampling objects, as before. Rung 0's gap was 0.210.

- **holds:** the interval is above zero and the gap is at least half of rung 0's (0.105 or more);
- **weakened:** the interval is above zero and the gap is under 0.105;
- **gone:** the interval includes zero.

The cause is the property added at the first rung that is "gone". If the gap shrinks rung by rung with no rung
"gone" before rung 4, the cause is the last property: shared tokens that follow kinds of object.

Gate: each `measured_separate` arm recalls at least 90% of held-out facts.

## Prediction (written before any run)

I expect a slide more than one sharp break:

- rung 1: about 0.66; holds.
- rung 2: about 0.60; weakened.
- rung 3: about 0.57; weakened.

Low confidence. I have been wrong about real names once already.

## Limits, known now

- Three rungs can't separate every cause. Position in the sequence and name length change together at rung 2.
- One fact source (measured) and one world. Same model size and training as before.

## Gate result: passed

Every `measured_separate` arm recalled at least 97% of held-out facts.

## Results (60 runs, seeds 1 and 2, `runs/language_transfer_names_v0/`)

| Rung | Names | measured facts | wrong-object facts | gap and 95% interval | share of rung 0's gap | verdict | predicted |
|---|---|---:|---:|---|---:|---|---|
| 0 | one token of its own | 0.688 | 0.478 | +0.210 (+0.179 to +0.243) | 100% | (done earlier) | |
| 1 | two tokens of its own | 0.630 | 0.497 | +0.133 (+0.101 to +0.164) | 63% | **holds** | holds, about 0.66 |
| 2 | 1 to 17 tokens, all its own | 0.481 | 0.476 | +0.005 (−0.035 to +0.044) | 2% | **gone** | weakened, about 0.60 (**wrong**) |
| 3 | real form, shared tokens dealt at random | 0.484 | 0.482 | +0.001 (−0.029 to +0.032) | 1% | **gone** | weakened, about 0.57 (**wrong**) |
| 4 | real names | 0.518 | 0.505 | +0.013 (−0.025 to +0.051) | 6% | (done earlier) | |

By rank (AUC), measured facts scored 0.748 at rung 1 and 0.444 at rung 2. Both seeds agree at every rung: 0.636
and 0.623 at rung 1; 0.486 and 0.475 at rung 2; 0.490 and 0.477 at rung 3.

**Reading:**

1. **The carry-over is lost when names get long, and for no other reason these rungs can see.** At rung 2 every
   token still belongs to one object, and nothing is shared. The only change from rung 1 is that a name has as
   many tokens as its real name: from 1 to 17, with a median of 5. By the rule set beforehand, that is the cause.
2. **Shared words aren't needed to explain the failure.** Rungs 3 and 4 add shared tokens and then shared tokens
   that follow kinds of object, and neither changes the score once it is already at guessing.
3. **Two tokens already cost something.** Rung 1 kept 63% of the one-token gap.
4. **I expected a slide and got a break.** I forecast about 0.60 for rung 2. It scored 0.481.

## A look inside the rungs (after the run, so weak evidence)

Splitting new objects by the length of their name, on balanced accuracy (measured facts against wrong-object
facts):

| Name length | objects | rung 2 | rung 3 | rung 4, real names |
|---|---:|---|---|---|
| 1–2 tokens | 21 | 0.609 against 0.506 | 0.586 against 0.542 | 0.593 against 0.505 |
| 3–4 tokens | 45 | 0.490 against 0.482 | 0.497 against 0.501 | 0.558 against 0.504 |
| 5–6 tokens | 36 | 0.488 against 0.456 | 0.480 against 0.439 | 0.513 against 0.476 |
| 7 or more | 48 | 0.393 against 0.456 | 0.418 against 0.452 | 0.435 against 0.505 |

The groups are small, and I chose the split after seeing the scores. Still, it fits the ladder: inside every rung
the short names keep a gain and the long ones don't. The longest names score below guessing with true facts, in
all three rungs. I have no tested account of that.

## What I think is happening (not tested)

With one token, the facts and the outcomes of a training object are written into the same vector, so what fact
rows write for a new object lands where the outcome question reads. With a long name the model has many tokens to
choose from. It can file the facts under one of them and look outcomes up under another, and nothing in training
makes it use the same one. That would also explain why recall stays at 97% while carry-over falls to nothing.

## What this means

- For a model this small, trained this way, facts learned apart carry over only for things with a handle of one
  or two tokens. Most real names are longer than that.
- It points the same way as the scaffold test (`docs/language-scaffold-v0.md`): the facts are stored but not
  brought to the question. Having the model state them first puts them in front of the question whatever the
  name looks like.
- A cheap remedy to try alongside: give each thing a short handle, a token of its own after its full name.

## Limits

- Position in the sequence and name length change together at rung 2, as the design said. These runs can't say
  which of the two does the harm.
- Measured facts only, one world, one model size, 6,000 steps.
