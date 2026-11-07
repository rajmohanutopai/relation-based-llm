# Acting Agent V2: Design

Date: 2026-11-04

Status: built; both gates failed (2026-11-04)

Experiment ID (planned): `acting_agent_v2`

## Why v2

v0 and v1 tested a weak form of the happiness rule, for two reasons:

1. **The world was small.** 42 objects × 5 actions is few enough that a
   random agent tries everything within 3,000 actions. When random covers
   the world, no rule for choosing what to try can beat it by much.
2. **Useful gain was never measured.** Both usefulness measures (gradient
   cosine, one step tested on all other cases) failed even with a perfect
   graph, where carry-over was known to be large (0.86 on new objects). The
   rule ran without the term that sets it apart.

v2 fixes both at once. It also fixes a third gap: in v0 and v1 every room
had 6 things and 20 actions, so the agent could try most of a room anyway.

## Question

In a world too big to cover, where things share features so learning about
one helps with others, does happiness with useful gain pick what to try
better than random, surprise, novelty and learning progress?

## World

The same rules as world_sim (push, drop, shake, watch on 6 surfaces), applied
to **made-up objects** with a property list:

- weight (1, 2, 3), shape (round, tube, wheels, none), hard, bouncy,
  breakable, noisy, size
- **16 kinds** (ball-like, block-like, cup-like, soft toy, car-like, ...).
  Each kind has a property list. Each object copies its kind's list, then
  flips each property with 10% chance, so objects of a kind are alike but
  not identical.
- **Names carry no meaning** ("thing_0412"), so the only route to
  carry-over is the graph.
- **800 objects**, split three ways:
  - 600 can appear in rooms (the agent learns from these)
  - 100 probe objects: used only by the useful-gain measure, never in rooms
    or tests
  - 100 test objects: never seen, scored zero-shot
- Rooms: **20 objects + 4 gadgets**, about 90 (thing, action) choices, and
  only **15 actions per room**. The agent can try about a sixth of each room.
- 10% outcome bit flips for ordinary things. Gadgets give random bits with
  pleasure 0.8, as before.
- 3,000 actions per run. About 600 objects × 4 actions = 2,400 regions, so
  random can't try most of them.

## World model

Graph features + an 8-dim per-thing slot, as in v1.

- **Graph:** the object's property values, with 5% errors and 10% gaps,
  drawn once. That's between the perfect graph and the 10%-error graph of
  v1.
- **Distractor fields:** 6 more fields that don't affect any rule (colour,
  soft to touch, has a face, ...). They are also drawn from the kind, so they
  match how alike things are but say nothing about outcomes. This weakens
  the main flaw of v1's graph test, where every field fed a rule. The model
  must find which fields matter.
- **Check run:** the names model (slot only, no carry-over). Every result is
  also reported for it.

This is still a toy. The graph fields are close to the rules' inputs. v2
tests the happiness rule given a graph that helps. It doesn't test whether
your 6-month graph helps.

## Useful-gain measure: neighbour transfer

The v1 test measured one step's effect on 64 random other cases. Most of
those cases have nothing to do with the step, so interference swamped the
signal. The new measure looks only where carry-over should show:

- Take the **8 probe objects nearest** to the thing just tried, by graph
  features.
- Take their cases for **the same action** (all 6 surfaces).
- Take one plain step on the new case alone, on a copy of the weights, and
  measure the fall in loss on those cases.

For an ordinary thing, the neighbours are similar things and the step should
help them. For a gadget, the neighbours are other gadgets, whose outcomes are
random, so the step can't help. Probe objects never appear in rooms or tests,
so the measure can't leak the test.

**Gate (one seed, random arm, both gadget conditions), all must hold:**

1. Graph model: ordinary transfer > 0 and above gadgets by at least 2 se.
2. Names model: ordinary transfer within 2 se of zero. This shows the
   measure tracks carry-over, not just any learning.
3. Sizing: random's test accuracy at 3,000 actions is still rising (last
   500 actions gain > 1 point), and random has tried under half the regions.
   Otherwise the world is too easy and gets bigger before going on.

If the gate fails, stop and write up.

## Arms

| Arm | Score for a (thing, action) choice |
|---|---|
| random | none |
| novelty | 1/sqrt(tries + 1) |
| surprise | recent loss before training |
| learning_progress | recent fall in loss |
| happiness_forget | the v0 rule (gain − forgetting − pleasure shortcut) |
| happiness_useful | useful gain − forgetting − pleasure shortcut, where useful gain = neighbour transfer × (1 − strength) |

**Untried choices.** With 2,400 regions, most choices in a room are untried.
v0 gave untried choices the top score, which turns every arm into novelty.
In v2, an untried choice borrows the mean score of the same action on the 8
nearest tried things (by graph). The names model has no neighbours, so it
falls back to the top score. Every arm uses the same rule.

## Measures

- Test accuracy over time (curve area), on all cases of the 600 room objects
  (sampled, 3,000 fixed cases)
- Zero-shot accuracy on the 100 test objects
- Actions to 85%
- Time on gadgets

## Pass rules (fixed before running)

Conditions: A (same 4 gadgets) and B (fresh gadgets each room). 5 seeds.

- **Main:** happiness_useful beats learning_progress, novelty and surprise
  on curve area, in both conditions, in at least 4 of 5 seeds each.
- **Second:** happiness_useful beats random on curve area, in both
  conditions, in at least 4 of 5 seeds.
- **Useful gain matters:** happiness_useful beats happiness_forget in at
  least 4 of 5 seeds in both conditions. Without this, any win isn't from the
  new term.
- **Names check:** on the names model, happiness_useful should not beat
  happiness_forget (no carry-over, so useful gain is noise). If it does, the
  win comes from something else.

## Prediction (written before running)

- Gate: passes. Neighbours share kind, and the perfect-graph model carried
  over strongly in v1.
- Main: passes. Learning progress and novelty both chased gadgets in v0's
  fresh-gadget condition.
- Second: **fails.** In v0 and v1 random was hard to beat, and a bigger world
  helps every rule that steers, random's rivals included. I'd put this at
  even odds.
- Useful gain matters: unsure.

## Cost

About 2,400 regions and 800 objects. The neighbour transfer test needs a
weight copy and a step per action: about 20 seconds a run. The grid is 6
arms × 2 conditions × 5 seeds × 2 models = 120 runs, about 40 minutes on
CPU.

## Build plan

1. `scripts/acting_agent_v2.py`, importing v0: made-up objects and kinds, the
   rules over a property list, bigger rooms, graph and distractor features,
   neighbour transfer, borrowed scores for untried choices.
2. Run the gate. Stop if it fails.
3. Run the grid. Report against the pass rules above, with no changes to
   them.

## Gate result (2026-11-04): failed

Built `scripts/acting_agent_v2.py` as designed. Gate: random arm, seed 1, 10%
flips, neighbour transfer (step 0.05) measured on every action. Output:
`runs/acting_agent_v2/gate.md`.

| model | gadgets | ordinary transfer | gadget transfer | gap (se) | final acc | late gain | regions tried | new objects |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| graph | A fixed | −0.122 ± 0.018 | −0.010 ± 0.011 | −5.3 | 0.815 | +0.014 | 0.58 | 0.848 |
| graph | B fresh | −0.164 ± 0.017 | −0.488 ± 0.046 | +6.7 | 0.806 | +0.002 | 0.58 | 0.825 |
| names | A fixed | +0.003 ± 0.005 | +0.024 ± 0.009 | −2.0 | 0.701 | +0.012 | 0.58 | 0.664 |
| names | B fresh | +0.010 ± 0.005 | +0.042 ± 0.014 | −2.2 | 0.671 | +0.012 | 0.58 | 0.623 |

- Check 1 (graph: ordinary > 0, above gadgets by 2 se): **fail** in both.
- Check 2 (names: ordinary near zero): pass in both.
- Check 3 (sizing): **fail**. Random tried 58% of regions, and the graph
  model had nearly stopped improving after about 1,600 actions.

Per the rule, the full grid is not run.

**Diagnostics (exploratory, graph model, condition A, seed 1):**

| change | ordinary transfer | gadget transfer |
|---|---:|---:|
| no flips, 3,000 actions | −0.152 ± 0.023 | −0.021 ± 0.021 |
| no flips, first 300 actions | +0.074 ± 0.039 | +0.084 ± 0.087 |
| step 0.005 | +0.0078 ± 0.0013 | +0.0105 ± 0.0020 |
| step 0.005, names model | +0.0066 ± 0.0006 | +0.0081 ± 0.0014 |
| step 0.0005 | +0.0011 ± 0.0001 | +0.0012 ± 0.0002 |

**Reading:**

1. **Step 0.05 is too big once the model is trained.** It harms the
   neighbours even with no flips. Early in a run, it helps.
2. **With small steps, the measure is positive for everything, gadgets
   included, and the graph and names models score the same.** It sees what
   any one case teaches about all cases (how pushes on a table usually end,
   or that gadgets are 50/50), not carry-over between similar things.
3. **Learning that a gadget is random is real learning, as far as loss goes.**
   A model that moves its gadget guesses toward 50/50 lowers its loss on
   other gadgets. Any measure built on loss will count this as useful. If
   "useful" is to exclude it, it has to mean a change in what the agent
   would predict or do, not just how sure it is.
4. **A good graph makes a big world small.** 600 objects in 16 kinds is, to
   the graph model, about 16 things. Random met enough of each kind to
   finish learning by halfway. For choice to matter, the world needs many
   more kinds, or kinds the graph doesn't reveal.

Three measures of useful gain have now failed (gradient cosine, one step on
all other cases, one step on similar things). All three ask how one step
changes loss, and that's the shared flaw.

## Second gate: fixed before running (2026-11-04)

Two changes, each answering a gate failure. Everything else stays as above.

**1. Decision transfer (replaces neighbour transfer).** Take the same plain
step (0.05) on the new case alone, on a copy of the weights. On the same
neighbour cases (8 nearest probe things, same action, all surfaces), count
answer bits that go from wrong to right, minus bits that go from right to
wrong, divided by the number of bits. Ordinary probes are scored against the
true rule. Gadget probes are scored against one fixed random draw, so for
them flips should cancel. A step that only makes the model surer changes no
answers and scores zero.

**2. A harder world.** 100 kinds instead of 16, with prototypes drawn at
random over the property fields (seed 0), and 1,500 objects: 1,200 in
rooms, 150 probes, 150 tests. About 5,400 room regions, so random can't try
most of them in 3,000 actions.

**Gate:** the same three checks as before, with decision transfer in place of
neighbour transfer.

**Prediction:** check 1 passes (decisions only move where there's something
left to learn); check 2 fails (the names model also learns which way each
action and surface usually goes, and that flips answers on things it never
met); check 3 passes.

If check 2 fails but checks 1 and 3 pass, I'll report that and ask before
going on, since it means the measure partly counts general learning.

## Second gate result (2026-11-04): failed

`--world big --measure decision`. Output:
`runs/acting_agent_v2/gate_big_decision.md`.

| model | gadgets | ordinary transfer | gadget transfer | gap (se) | final acc | late gain | regions tried | new objects |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| graph | A fixed | −0.0162 ± 0.0024 | −0.0027 ± 0.0015 | −4.8 | 0.801 | +0.006 | 0.35 | 0.822 |
| graph | B fresh | −0.0145 ± 0.0023 | −0.0040 ± 0.0027 | −3.0 | 0.763 | −0.005 | 0.35 | 0.782 |
| names | A fixed | +0.0023 ± 0.0016 | −0.0023 ± 0.0011 | +2.5 | 0.630 | +0.002 | 0.35 | 0.643 |
| names | B fresh | +0.0060 ± 0.0013 | −0.0034 ± 0.0013 | +5.2 | 0.622 | +0.007 | 0.35 | 0.617 |

- Check 1 (graph: ordinary > 0, above gadgets): **fail** in both.
- Check 2 (names near zero): pass in A, **fail** in B.
- Check 3 (sizing): **fail** in both. Random now tries only 35% of regions,
  but the graph model still stops improving early (late gain under 1 point).

Prediction was check 1 pass, check 2 fail, check 3 pass. Two of three were
wrong.

**Reading:**

1. **With the graph model, one try breaks more answers about similar things
   than it fixes:** about 1.6% of neighbour bits net. Once the model is near
   80%, most of what a single new case adds is its noise (10% flipped bits,
   plus each object's own quirks), and a step toward it moves the whole
   kind.
2. **The graph model's ceiling comes from the graph, not from the world's
   size.** It reaches about 0.80 fast and then sits there. What's left to
   learn is each object's quirks and the graph's errors, and that takes many
   tries per object. 100 kinds didn't change this, because the graph hands
   over each kind's properties directly.
3. **The names model shows small positive transfer** while the graph model
   shows negative. That's the reverse of what a measure of carry-over
   between similar things should give.

**Stopping here.** Four ways of measuring useful gain on a single try have
failed. The remaining design choices (step size, how many neighbours,
what counts as a flip) could be tuned until one passes, but a measure tuned
to pass its own check isn't evidence. The question goes back to the user.
