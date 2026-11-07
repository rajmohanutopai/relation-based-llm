# Acting Agent V3: Design

Date: 2026-11-04

Status: v3 and v3.1 run (2026-11-04); mixed result

Experiment ID: `acting_agent_v3`

## Why v3

v0 to v2 measured happiness through a neural network's loss. Four measures of
"useful gain" failed, and the user's own account of the theory showed why
(`memory: happiness-theory-meaning`, and the 2026-11-04 discussion):

- Happiness is the strengthening of **connections**, summed over every
  connection an experience touches, each counted more the weaker it was.
- A child has many weak connections, so one try gives a lot. An adult needs
  something that strengthens many connections at once.
- The biggest happiness is **grokking**: a general link forms from specific
  ones and ties many known things into a whole.
- Learning "this toy does random stuff" is a real connection: small joy,
  then boredom.
- **Sadness** is strong connections predicting something that no longer
  happens (grief: many strong links to a father keep failing; few to a
  neighbour). It comes in waves and fades as the links are revised.

v3 gives the agent explicit connections, so happiness and sadness can be
computed as the theory states rather than through a proxy.

## World

The v2 "big" world, unchanged: 1,200 room objects in 100 kinds, 150 test
objects never met, 20 objects + 4 gadgets per room, 15 actions per room,
3,000 actions, 10% outcome flips. The agent sees each thing's features (the
v2 graph fields: 5% wrong, 10% missing) and each surface's features (high,
hard, smooth). It never sees kinds.

## Connections

Every connection predicts one outcome bit, holds a count of evidence, and
estimates the chance the bit is 1.

- **Strength** s = n / (n + 5), where n is the evidence count. Old evidence
  fades slowly (each update multiplies past counts by 0.99), so links can be
  revised when the world changes.
- **Specific links:** (this thing, action, surface) → bit.
- **General links:** (thing feature, action, surface feature) → bit, for
  example "round things, pushed gently, on smooth surfaces → roll". **None
  exist at the start.** A general link forms when at least 3 different things
  with that feature have tried it at least twice each and their own estimates
  agree (spread ≤ 0.25). It starts with their pooled evidence, which is the
  grokking jump.

## Happiness and sadness of one try

For every connection the try touches:

- **Happiness** = Σ (rise in strength) × (1 − strength before).
  - A newly formed general link counts its whole starting strength.
  - A specific link that a strong general link already explains counts
    little: its gain is also multiplied by (1 − the strongest matching
    general link). A new ball rolling teaches an adult little.
- **Sadness** = Σ strength before × miss, where miss is how far the outcome
  fell on the wrong side of the link's estimate (0 if it was right, up to 1
  if the link was sure and wrong). Gadget links sit near 50/50, so they never
  cause sadness.

There is no pleasure term and no shortcut penalty. In the user's account,
gadget time isn't harmful in itself: it saturates.

## Predicting

All arms share the same connection store and the same predictor. A case's
estimate is the mean of the matching links' estimates, weighted by strength
× how sure each is (specific links count 3 times). With no links it guesses
50/50.

## Arms (only the choice rule differs)

| Arm | Picks by |
|---|---|
| random | nothing |
| novelty | 1/sqrt(tries + 1) for this (thing, action) |
| surprise | the predictor's uncertainty about this choice |
| learning_progress | recent fall in prediction error for this (thing, action) |
| happiness | expected happiness: the strength each touched link would gain, weighted as above, plus the chance of forming a general link |

Softmax over scores (temperature 0.3, 10% random), 200 random actions first.

## Tests

**Gate (random arm, seed 1, fixed gadgets).** All must hold, or stop:

- G1: final accuracy on room cases ≥ 0.75, and on never-met objects ≥ 0.65
  (the store can learn, and general links carry over).
- G2: at least 30 general links form, including at least one covering gadgets
  (feature "electronic").
- G3: a happiness-arm run takes under 2 minutes.

**Main (5 seeds, fixed gadgets A and fresh gadgets B):**

- M1: happiness beats novelty, surprise and learning_progress on curve area
  in at least 4 of 5 seeds, in both conditions.
- M2: happiness beats random on curve area in at least 4 of 5 seeds, in both
  conditions.

**Shape of the feelings (happiness arm, condition A, 5 seeds):**

- S1 (ageing): mean happiness per try in actions 2,501–3,000 is less than
  half of that in actions 201–700, in 5 of 5 seeds.
- S2 (grokking): among the top 1% happiest tries, more than half include a
  general link forming, in at least 4 of 5 seeds.
- S3 (gadget boredom, condition B): gadget share in actions 2,001–3,000 is
  under half the share in actions 201–700, in at least 4 of 5 seeds.

**Grief (random arm, condition A, 5 seeds).** At action 2,000 the world
changes:

- big change: every bouncy thing stops bouncing (many strong links)
- small change: one bouncy object stops bouncing (few links)

- R1: total sadness over actions 2,001–3,000 is more than twice as large
  for the big change, in 5 of 5 seeds.
- R2: for the big change, sadness in actions 2,501–3,000 is lower than in
  2,001–2,500, in at least 4 of 5 seeds.

## What is built in

Some results follow from the definitions and are checks that the code does
what the theory says, not evidence for it:

- S1 is close to certain: strength saturates by definition.
- R1 is close to certain: the big change touches far more links, and the
  agent meets one object rarely. (This matches the user's account of grief,
  but the run can't test it.)

The real tests are M1 and M2 (does seeking this happiness build better
knowledge?), S2 (are the peaks really grokking?), S3 (does "fits what you
know" make new gadgets boring?) and R2 (does sadness fade as links are
revised?).

Not in v3: watching versus acting (every choice here is an action), and
happiness as a concept of its own.

## Prediction (written before running)

- Gate: pass.
- M1: **fail**. The happiness score is mostly a count of weak links, which is
  close to novelty, so the two will be near each other.
- M2: unsure, even odds.
- S1, R1: pass (built in).
- S2: pass.
- S3: pass.
- R2: pass.

## Gate (2026-11-04)

**First try: failed G1.** Room accuracy 0.595, never-met objects 0.583 (G2
and G3 passed). Cause: every general link described one feature. Gadgets are
light, hard and breakable too, and act at random, so links like "light things
move when pushed" were polluted by gadget outcomes. One feature can't tell a
light toy from a light gadget. Rare outcomes (rolls, falls, bounces) were
almost never predicted.

**Fix (two changes, made before any arm comparison):**

1. General links can also form on **pairs** of thing features (for example
   light and not electronic), under the same forming rule. They're still
   built only from specific links.
2. The predictor uses **the strongest, surest matching link** instead of a
   weighted mean. On the same stored links (replayed random run, seed 1):
   mean 0.694, strongest 0.794, log-odds sum 0.665.

Also, for speed: expected happiness (and the surprise arm's uncertainty) is
worked out for the whole room when the agent enters it, and after each try
only the tried thing's choices are redone. Scores can be up to 15 tries out
of date for other things in the room.

**Second try: passed.** Room accuracy 0.794, never-met objects 0.783;
19,003 general links formed, 995 of them covering gadgets; a happiness run
took 80 s. Pass rules and predictions above are unchanged.

## Results (5 seeds, `runs/acting_agent_v3/seed*/`)

**Learning (curve area of room-case accuracy):**

| arm | A: fixed gadgets | A gadget time | B: fresh gadgets | B gadget time |
|---|---:|---:|---:|---:|
| random | 0.718 | 16% | 0.696 | 19% |
| novelty | 0.706 | 4–7% | 0.643 | 20–23% |
| surprise | **0.751** | 18% → 39% | 0.732 | 21% → 31% |
| learning_progress | 0.735 | 3–6% | 0.692 | 19–21% |
| happiness | 0.714 | **38%** | **0.737** | 16–17% |

Happiness wins (curve area, out of 5 seeds):

| vs | A | B |
|---|---:|---:|
| random | 2 | **5** |
| novelty | 2 | **5** |
| surprise | 0 | 3 |
| learning_progress | 1 | **5** |

**Shape of the feelings (happiness arm):**

- Happiness per try fell from 12.6–16.8 (actions 201–700) to 1.1–1.6
  (2,501–3,000), to 7–11% of its early level, in 5 of 5 seeds.
- In every seed, **all** of the top 1% happiest tries formed a general link.
  Only about 22% of all tries form one, so this isn't chance.
- In B, gadget share went from 16–20% to 14–18%: barely down.

**Grief (random arm, change at action 2,000):** total sadness over actions
2,001–3,000 was the same for the big and the small change (ratio 0.98–0.99
in every seed). Sadness before the change was already about 14,000–15,500
per 500 tries. Per try: about 25 for ordinary things and 60 for gadgets.

**Against the rules:**

| rule | result | predicted |
|---|---|---|
| M1 beats novelty, surprise, LP (both conditions) | **fail** (A fails; B passes except surprise 3/5) | fail |
| M2 beats random (both conditions) | **fail** (A 2/5; B 5/5) | even odds |
| S1 ageing | pass | pass |
| S2 grokking peaks | pass | pass |
| S3 gadget boredom (B) | **fail** | pass |
| R1 big change sadder | **fail** | pass |
| R2 sadness fades | **fail** | pass |

**Reading:**

1. **Grokking is real in this model.** The happiest moments are always a
   general link forming, and happiness per try falls with age. Both follow
   from how the theory defines happiness, and the code behaves as the user
   described.
2. **With fresh gadgets, seeking happiness built the best knowledge** of any
   rule except surprise (beat random, novelty and learning progress in 5 of
   5 seeds). This is the first time any form of the rule beat random.
3. **With the same gadgets in every room, it fell into them** (38% of its
   time) and lost to most rules. The cause isn't pinned down yet. One
   candidate: each gadget try touches hundreds of feature links, so a noisy
   thing that touches many links keeps paying.
4. **Sadness as defined is swamped by everyday noise.** With pair links, one
   flipped outcome contradicts hundreds of strong links, so ordinary life is
   already very "sad" and a real loss doesn't show. The user's own doubt
   fits: a single odd outcome shouldn't hurt. Grief likely needs sadness to
   come from **repeated** failure of strong links (a link failing far more
   often than it usually does), not from each miss.

## v3.1: two fixes, fixed before running (2026-11-04)

**Why fixed gadgets trapped the agent (diagnostic, seed 1, condition A).**
Expected happiness split by part, averaged over a room's choices:

| action | kind | specific links | formed general links | "about to form" bonus |
|---|---|---:|---:|---:|
| 1,000 | gadget | 0.005 | 0.18 | **9.6** |
| 1,000 | ordinary | 0.028 | 0.41 | 0.77 |
| 2,990 | gadget | 0.002 | 0.04 | **4.1** |
| 2,990 | ordinary | 0.018 | 0.13 | 0.12 |

Gadget feature links keep looking ready to form, but their members' random
outcomes never agree, so they never form. The agent expected each to form
with chance 0.5, forever: an insight that is always promised and never
comes.

**Fix 1: the agent learns how often a promised grok really comes.** Each
candidate link counts the times a try could have formed it and didn't. Its
expected chance of forming is 1 / (2 + failures), so it starts at 0.5 as
before.

**Fix 2: sadness from repeated failure.** Each link tracks its recent miss
rate (moving average, weight 0.1) and its usual miss rate (weight 0.01).
Sadness for a link = strength × max(0, recent − usual − 0.1). One flipped
outcome lifts recent by at most 0.1, so it costs nothing. A link that keeps
failing hurts until its estimate is revised and "usual" catches up.

**Rules:** the same M1, M2, S1, S2, S3, R1 and R2, on a full rerun (5 seeds).

**Prediction:**

- Happiness's gadget time in A falls below random's.
- M1: fail (surprise is strong in both conditions).
- M2: pass.
- S1, S2: pass. S3: pass (the failure counts belong to feature links, which
  are shared by all gadgets, so new gadgets inherit the boredom).
- R1: pass. The big change hits many paired general links ("bouncy and X →
  bounces"). One ball changing hits only its own specific links.
- R2: pass.

(Code note: a candidate is now checked for forming only when the tried
thing itself has enough tries, so that "could have formed and didn't" is
counted only for tries that could have formed it.)

## v3.1 results (5 seeds, `runs/acting_agent_v3_1/seed*/`)

Gate still passes (0.794 / 0.783). Only the happiness arm and the sadness
numbers change; the other arms are identical to v3.

| arm | A area | A gadget time | B area | B gadget time |
|---|---:|---:|---:|---:|
| random | 0.718 | 16–17% | 0.696 | 19% |
| surprise | **0.751** | 18% → 39% | 0.732 | 21% → 31% |
| learning_progress | 0.735 | 3–6% | 0.692 | 19–21% |
| happiness v3 | 0.714 | 38% | 0.737 | 16–17% |
| happiness v3.1 | 0.728 | **28% → 25%** | 0.734 | 18% → 16% |

Happiness v3.1 wins (out of 5): A vs random 2, novelty 3, surprise 1,
LP 1; B vs random 5, novelty 5, surprise 2, LP 5.

Happiness per try fell to 2–6% of its early level; all top-1% tries formed a
general link (both conditions, every seed).

**Grief:** big and small change gave the same total sadness again (ratio 1.0
in every seed). Sadness before the change was about 600–830 per 500 tries
(down from about 15,000 in v3, so the repeated-failure rule did remove most
everyday sadness).

**Why grief still doesn't show (seed 1, random arm):** the big change
affected only **29 tries** out of the 1,000 after it (drops of bouncy things
on hard surfaces), and those tries carried 40 of the 1,407 units of sadness
in that span, about the same per try as any other. "Every bouncy thing stops
bouncing" sounded big, but in this world it's a rare event touching a few
dozen links. It's a neighbour, not a father. The test was badly sized.

**Against the rules:**

| rule | v3.1 | predicted |
|---|---|---|
| gadget time in A below random's | **no** (25–28% vs 16–17%) | yes |
| M1 | fail | fail |
| M2 | fail (A 2/5, B 5/5) | pass |
| S1, S2 | pass | pass |
| S3 | fail (B: 18% → 16%) | pass |
| R1 | fail (change too rare to test) | pass |
| R2 | fail | pass |

**Reading:**

1. The slot-machine fix helped: gadget time in A fell from 38% to about
   26%, and curve area rose from 0.714 to 0.728. It's still above random, so
   some other pull toward fixed gadgets remains.
2. The repeated-failure rule cut everyday sadness about 20-fold, as meant.
   Whether it shows grief is still untested, because the change was too
   small.
3. In fresh-gadget rooms the happiness rule keeps beating random, novelty and
   learning progress 5 of 5; with fixed gadgets it doesn't.

## Fair grief test: fixed before running (2026-11-04)

The first grief test changed something rare (29 tries in 1,000). This one
changes something the agent meets all the time.

- **big change ("father"):** from action 2,000, every light thing stops
  moving when pushed, gently or hard (so it also stops rolling and falling).
  Light things are about a third of objects and pushes are most actions.
- **small change ("neighbour"):** one light object stops moving.

v3.1 sadness rule, random arm, fixed gadgets, 5 seeds. Number of affected
tries is reported.

- R1': total sadness over actions 2,001–3,000 is more than twice as large
  for the big change, in 5 of 5 seeds.
- R2': for the big change, sadness in 2,501–3,000 is lower than in
  2,001–2,500, in at least 4 of 5 seeds.
- R3' (waves): for the big change, sadness per affected try in 2,001–2,500
  is more than three times sadness per unaffected try, in 5 of 5 seeds.

**Prediction:** R1' pass, R2' pass, R3' pass.

## Fair grief test: results (2026-11-04)

The big change affected 106–130 of the 1,000 tries after action 2,000
(about 12%, not the half I had guessed). The test ran three times, because
I found two flaws in my own test code. All three are reported.

1. **First run:** a changed try's outcome was set after the 10% noise was
   added, so changed tries lost their noise. Ratio big/small 0.75–1.07.
2. **Second run:** noise kept, but the extra random draws made the big and
   small runs see different noise after action 2,000, so they weren't
   matched. Ratio 0.80–1.31.
3. **Third run (the valid one):** changed outcomes drawn from their own
   random source. The two runs match exactly up to action 2,000 (2,000 of
   2,000 tries identical).

Third run, per seed:

| seed | big / small sadness | extra sadness from the change, 2,001–2,500 then 2,501–3,000 | affected try vs other try (sadness per try) |
|---|---:|---|---:|
| 1 | 1.14 | +190, then +4 | 4.7 vs 1.4 (3.3×) |
| 2 | 0.97 | −34, then −19 | 3.6 vs 1.7 (2.1×) |
| 3 | 0.95 | −67, then −9 | 3.1 vs 1.4 (2.2×) |
| 4 | 0.79 | −147, then −144 | 1.3 vs 0.9 (1.5×) |
| 5 | 0.96 | +23, then −82 | 3.9 vs 1.3 (3.1×) |

- R1' (big > 2× small): **fail**, 0 of 5.
- R2' (big change's sadness lower in the second half): pass, 4 of 5, but
  with no extra sadness to fade, this means little.
- R3' (affected tries > 3× other tries): **fail**, 2 of 5.

Prediction was pass on all three.

**Reading:** each moment that meets the change is sadder, 1.5 to 3.3 times,
so there are waves. But total sadness doesn't rise, and in most seeds it
falls a little. The likely cause is the sadness rule itself: it measures
failure against each link's *usual* failure rate. Many general links are
shared between light and other things, and as they keep failing they "get
used to it", which makes later misses on other things hurt less. The agent
adapts to the loss about as fast as the loss arrives. This wasn't checked
further.
