# Acting Agent V4.3: A Room That Is Half Noise

Date: 2026-11-10

Status: run complete (2026-11-10); all three rules passed in every seed; happiness learned best when half the room was noise

Experiment ID: `acting_agent_v4_3`

## Why

In every world so far, 4 of the 24 things in a room were gadgets, so noise was 17% of what the baby could play
with. Surprise learned best there (`docs/acting-agent-v4-2-design.md`), though it spent up to 39% of its time on
gadgets. The summary named the reason this may not be a fair trial: time on gadgets cost only lost turns, and
there were few gadgets to lose turns on. The theory's distinct claim is that a learner chasing saturating
happiness is safe from noise where a surprise-seeker is not. That claim has only been tested on time spent, never
on what was learned in a world where noise is common.

## The world

As v4.2, with one change: a room holds **4 ordinary things and 4 gadgets**, where it held 20 and 4. Gadgets have
more actions on average, so a baby choosing at random spends about 55% of its turns on them.

- A: the same 4 gadgets in every room.
- B: 4 new gadgets in every room.

Everything else is unchanged: 3,000 actions, 15 per room, 10% of outcomes flipped, the same link store and the
same quiz on ordinary things.

## Babies

| Baby | Version |
|---|---|
| random | picks at random |
| surprise | picks what it is least sure about |
| happiness | `--S`: the S-curve only, the best version in v4.1, confirmed on new seeds in v4.2 |

One happiness version, named before the run. Seeds 11–15, which no earlier run used.

## Gate

With 20 things per room, the new script must reproduce v4.2's stored curve for `--S`, seed 6, condition A. This
shows the room change is the only change.

## Pass rules (at least 4 of 5 seeds, in A and in B)

- **N1, the main rule:** happiness beats surprise on curve area.
- **N2:** happiness beats surprise on final score.
- **N3:** happiness beats random on curve area.

## Prediction (written before any run)

- Surprise spends well over half its time on gadgets by the end, in both conditions. Its uncertainty about a
  gadget never falls, and once it knows the ordinary things, gadgets are all that's left to wonder about.
- Happiness spends far less time on gadgets than random in A, because a gadget's links stop paying. In B it
  spends about as much as random, because every new gadget pays once, as any new thing does.
- N1 passes in A and in B.
- N2 passes in A. In B I can't say.
- N3 passes in A and fails in B.

Moderate confidence in N1, lower in the rest.

## Limits, known now

- I chose a noise share that should favour the theory. If happiness loses even here, the claim that it makes a
  good learner is in serious trouble. If it wins, the claim holds only where noise is common.
- Rooms now hold fewer ordinary things, so every baby sees less of the world per room. Scores aren't comparable
  with v4.2's.
- All babies share one link store. The test is about what they choose to play with, not how they learn from it.
- This is my toy world. It says whether the rule works once written down exactly, and nothing about people.

## Gate result: passed

With 20 things per room the script reproduced v4.2's stored `--S` run for seed 6, condition A, exactly (area
0.7216, gadget time 0.1675).

## Results (seeds 11–15, 30 runs, `runs/acting_agent_v4_3/`)

| Baby | Condition | curve area | final score | new objects | time on gadgets | in the last 1,000 actions |
|---|---|---:|---:|---:|---:|---:|
| random | A | 0.686 | 0.774 | 0.765 | 52% | 52% |
| surprise | A | 0.690 | 0.753 | 0.752 | 77% | 83% |
| happiness | A | **0.743** | **0.815** | **0.806** | 29% | 28% |
| random | B | 0.683 | 0.740 | 0.733 | 54% | 54% |
| surprise | B | 0.691 | 0.755 | 0.747 | 70% | 73% |
| happiness | B | **0.726** | **0.798** | **0.788** | 40% | 38% |

Curve area by seed: A happiness 0.740, 0.742, 0.747, 0.711, 0.774; surprise 0.677, 0.673, 0.740, 0.667, 0.693.
B happiness 0.713, 0.725, 0.748, 0.732, 0.710; surprise 0.652, 0.724, 0.702, 0.694, 0.682.

| rule | A | B | predicted |
|---|---|---|---|
| N1 happiness beats surprise on curve area (main) | **pass**, 5 of 5, +0.053 | **pass**, 5 of 5, +0.035 | pass in both |
| N2 happiness beats surprise on final score | **pass**, 5 of 5, +0.062 | **pass**, 5 of 5, +0.044 | pass in A; no call in B |
| N3 happiness beats random on curve area | **pass**, 5 of 5, +0.057 | **pass**, 5 of 5, +0.043 | pass in A; fail in B (**wrong**) |

**Reading:**

1. **When half the room is noise, the happiness baby learns best.** It is ahead of surprise and of random on
   speed, on final score and on new objects, in every seed and in both conditions. This is the first run in which
   chasing happiness made the best learner.
2. **Surprise is caught by the noise, as predicted.** It spent 70–77% of its turns on gadgets, more by the end,
   and learned no faster than random (0.690 against 0.686 in A). In A it ended below random.
3. **Happiness avoided fresh gadgets too, which I didn't expect.** In B it spent 40% of its turns on gadgets
   where random spent 54%. I had predicted they would match. So N3 passed in B against my prediction.
4. **In B, two of the ten speed comparisons were near ties,** won by 0.001: one against surprise (seed 12: 0.725
   against 0.724) and one against random. The final scores in B were clear in every seed, by about 0.02 or more.

**What this adds to v4.2:** there, with noise at 17% of the room, surprise led (0.775 against 0.750 in A). Here,
with noise at half the room, the order turns over. The claim that survives is conditional: a learner that chases
saturating connection gain learns more than a surprise-seeker **when noise is common**, and somewhat less when
noise is rare. Where the order turns over, between 17% and 50%, hasn't been mapped.

**Still not shown:** this ran one happiness version in one new setting that I picked to suit the theory. Novelty
and learning progress weren't run here. And every baby learns through the same link store, so this is about what
to play with, not how to learn from it.
