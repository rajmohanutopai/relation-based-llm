# Acting Agent V1: Design

Date: 2026-11-03

Status: design, not built

Experiment ID (planned): `acting_agent_v1`

## Why v1

Acting agent v0 (`docs/acting-agent-v0-design.md`) left plan.md's key idea
untested: only *useful* connection gain should count. Its world model knew
each thing only by name, so learning about a ball was stored in the ball's
own slot and could not help with an apple. With no carry-over between things,
useful gain is zero everywhere. Neither measure tried in v0 could find it.

v1 gives the world model features that things share. Learning about one thing
can then carry over to similar things, so usefulness becomes something we can
measure. This also gives the hand-written relation graph a direct role: as one
source of those features.

## Questions

1. **Usefulness:** with shared features, does the direct transfer test
   separate toys (positive carry-over) from gadgets (none)? This is the gate:
   if it doesn't, stop.
2. **Happiness:** if it separates, does happiness with useful gain beat
   random, surprise, novelty and plain learning progress?
3. **Graph:** does a world model fed graph-derived features learn faster than
   one fed word vectors, or names only? This tests the hunch that a graph
   speeds up a small learner.

## World

The same as v0's confirmatory world: world_sim rules, 10% outcome bit flips
for ordinary things, 2 gadgets per room, 20 actions per room, 3,000 actions
per run.

Changes:

- **Gadget names come from a list of real words** (tv, tablet, screen,
  light-up toy, toy phone that flashes, night light, ...), about 30 in all.
  In v0, fresh gadgets had made-up names like "tv#17", but with word vectors
  a gadget's name now carries meaning. Half the list is held out for the
  fresh-gadget condition.
- **Held-out objects:** the 11 held-out world_sim objects (mug, melon,
  tambourine, ...) never appear in rooms. They are scored zero-shot.

## World model: three feature sources (the graph question)

The network and size are the same in every version. Only the input for "which
thing" changes.

| Version | Thing input | Can carry over? |
|---|---|---|
| names | a learned slot per name (v0) | no |
| words | the MiniLM vector of the name, frozen, plus a small learned slot | yes, through meaning |
| graph | features read from hand-written relations about the thing, plus a small learned slot | yes, through stated relations |

- **Word vectors** are already cached for every world_sim object in
  `world_sim_v1/word_vectors.json`. Gadget words need adding.
- **Graph features:** only 364 hand-written 6mo relations mention world
  objects, and only 34 of those map to a property field. Coverage has to be
  checked before this version is worth running. If too thin, write a small
  hand-made relation file for the world objects. It would hold the things a
  6-month-old graph would plausibly have ("a ball is round", "a cup is
  light"), reviewed, and kept separate from the simulator's truth table.
- **Leak guard:** the graph must not just copy the truth table. Its
  properties get the same 10% error rate as the world, plus gaps. The
  agent's world model then has to learn which features to trust.

## Usefulness measure

The direct transfer test from v0: one plain gradient step on the new case
alone, on a copy of the weights, then the fall in mean loss on 64 recent
cases from other regions.

**Gate (signal check, one seed, words version):** mean transfer for ordinary
things must be above zero and clearly above gadgets, at least 2× their
spread over tries, in both gadget conditions. If not, stop here and write up.

## Arms (only after the gate passes)

random, surprise, novelty, learning_progress, happiness_forget (the v0 rule,
gain unscaled), happiness_transfer (useful gain = transfer × (1 −
strength)).

## Measures

- World-model learning speed on the true rule (curve area), as in v0
- New-object accuracy, zero-shot, on the 11 held-out objects
- Time on gadgets
- Mean transfer per region type (the gate)

## Pass rules (to be fixed after the gate, before the full run)

Draft:

- **Happiness:** happiness_transfer beats random, surprise, novelty and
  learning_progress on curve area in both gadget conditions, in at least 4
  of 5 seeds.
- **Graph:** with the random arm, the graph version beats the names version
  on curve area and on new-object accuracy in all 5 seeds. The words version
  is reported beside it.

## Cost

About 9 seconds per run with the transfer test. The full grid is 3 feature
sources × 6 arms × 2 conditions × 5 seeds = 180 runs, about 30 minutes. The
graph file, if needed, is the slow part: a few hours of careful writing.

## Build plan

1. Add a feature-source option and real gadget words to
   `scripts/acting_agent_v0.py` (or make a v1 file that imports it).
2. Run the gate with the words version.
3. If it passes, check graph coverage and write the small relation file if
   needed.
4. Fix the pass rules in this doc, then run the full grid.

## Gate result (2026-11-03): failed

Built `scripts/acting_agent_v1.py`: real gadget words (30, with 3 fixed for
condition A), and `--features words`, where the thing input is the frozen
MiniLM vector projected to 24 dims plus an 8-dim learned slot. Gate: the
random arm, seed 1, transfer measured on every action.

| Features | Condition | ordinary transfer | gadget transfer | gap (in se) |
|---|---|---:|---:|---:|
| names | A | −0.0031 | −0.0015 | −2.3 |
| names | B | −0.0025 | −0.0044 | +2.4 |
| words | A | −0.0040 | −0.0023 | −1.6 |
| words | B | −0.0030 | −0.0029 | −0.1 |

Ordinary transfer is negative in every case, so the gate fails. One step on a
single case makes the other recent cases slightly worse on average, with or
without word vectors.

Diagnostic (random arm, 3 seeds): zero-shot balanced accuracy on the 11
held-out objects.

| Features | new-object accuracy | training curve area |
|---|---:|---:|
| names | 0.597 (0.572–0.637) | 0.847 |
| words | 0.654 (0.609–0.685) | 0.834 |

Word vectors carry over a little: about +6 points on objects the agent never
met. That is far weaker than the interference one step causes across mixed
cases. Names score above 0.5 because the action and surface alone predict
some outcomes.

**Reading:** carry-over through word vectors exists but is weak, and a
one-step test across all other cases can't see it. Per the gate, the full
grid is not run.

**Next, if continued:** the graph version, with features such as round,
heavy, hard, bouncy, noisy and breakable from a relation file (with 10%
errors and gaps). Carry-over there is direct, and it tests the "graph speeds
up a small learner" hunch. If even that can't pass the gate, the transfer
test itself is the problem.

## Graph features (exploratory, 2026-11-03)

`--features graph`: 12 property fields (round, tube, wheels, light / a bit
heavy / heavy, hard, bouncy, noisy, breakable, big, electronic), each with a
value and a known bit. **This graph is simulated:** it is the simulator's
property table with errors and gaps drawn once. It is not the hand-written
6mo graph, which covers only 34 of these facts. Gadgets are listed as hard,
noisy, breakable electronic things.

**Graph vs names** (random arm, 10% outcome flips, 3,000 actions; names on 3
seeds, graph on 5; "graph only" = no per-thing learned slot):

| World model | train curve area | new objects (zero-shot) | actions to 85% |
|---|---:|---:|---:|
| names | 0.826 | 0.597 | ~1,530 |
| word vectors | 0.814 | 0.654 | ~1,630 |
| graph only, perfect | **0.902** | **0.860** | **~700** |
| graph only, 2% errors | 0.875 | 0.834 | ~820 |
| graph only, 5% errors | 0.863 | 0.773 | ~940 |
| graph only, 10% errors | 0.831 | 0.760 | ~1,320 |
| graph only, 15% gaps | 0.848 | 0.732 | ~1,140 |
| graph only, 30% gaps | 0.835 | 0.728 | ~1,280 |
| graph + slot, 10% errors + 15% gaps | 0.832 | 0.653 | ~1,400 |

**Reading:**

1. **An accurate graph makes this small learner about twice as fast** (half
   the actions to 85%), and much better on objects it never met (0.86 vs
   0.60). This supports the "graph speeds up a small learner" hunch, in this
   toy world.
2. **The gain falls off fast with graph quality.** At 10% wrong values, most
   of the speed gain is gone, though new-object accuracy holds better (0.76).
   Gaps hurt less than errors on speed.
3. **A free per-thing slot lets the model ignore a noisy graph.** With the
   slot, a 10% / 15% graph did no better than names on new objects.

**Transfer gate with the perfect graph: still fails** (ordinary −0.0053 vs
gadget −0.0029 in A; −0.0043 vs −0.0028 in B). Real carry-over is now large
(0.86 on new objects), so the one-step test is what's broken: it can't see
carry-over even when it exists. Measuring usefulness that way is dropped.
Any future useful-gain measure has to be checked first against a world model
known to carry over (this one).

Fix made during this run: `transfer_direct` now allows weights that a case
doesn't touch (needed for the graph-only model).

## Hand-written graph test: fixed before running (2026-11-03)

**Graph source:** the 6mo hand-written relations
(`age_6mo_handwritten_relations_v0`), read through the same regex claim map
the world_sim_v1 audit used (`CLAIMS` in `scripts/create_world_sim_v1.py`).
Fields: round_like, hard, bouncy, breakable, heavy_like, noisy, closable.
Facts not stated are gaps. No facts are added by hand or by an LLM.
Coverage: 364 rows mention 28 of 55 objects, and about 34 map to a field.

**World models** (all use graph features + an 8-dim per-thing slot, since
gaps leave many things otherwise identical):

| Version | Features |
|---|---|
| names | slot only (32 dims) |
| hand | the hand-written graph, as stated |
| hand_cells_true | the same known cells, with the simulator's true values |
| table7 | all 7 fields, true values, no gaps (ceiling at this field set) |

**Setting:** random agent, 10% outcome flips, same 3 gadgets, 3,000
actions, 5 seeds.

**Pass rule:** hand beats names on train curve area and on new-object
accuracy, in at least 4 of 5 seeds.

**Prediction, written before running:** fail. Coverage is too thin (most
cells are gaps), and the 30%-gap sweep already lost most of the gain.
hand_cells_true shows how much of any shortfall is coverage and how much is
wrong facts.

## Hand-written graph test: results (5 seeds)

Coverage: the claim map finds **23 known cells out of 294** (42 train
objects × 7 fields), which is 8%. 2 of the 23 disagree with the simulator
(the bowl and toothbrush cases from the world_sim_v1 audit). **No held-out
object has any known cell.**

| World model | train curve area | new objects (slot zeroed) | actions to 85% |
|---|---:|---:|---:|
| names | 0.826 | 0.648 | ~1,440 |
| hand | 0.808 | 0.625 | ~1,640 |
| hand_cells_true | 0.805 | 0.637 | ~1,640 |
| table7 | **0.865** | **0.830** | **~860** |

hand beats names on both measures in 0/5 seeds. **Fails, as predicted.**

**Reading:**

1. **Coverage is the problem, not correctness.** hand and hand_cells_true
   score the same, so the 2 wrong facts don't matter. 8% coverage is too
   little to help.
2. **hand scores slightly below names, but not because of the graph.** The
   graph versions have an 8-dim learned slot, while names has 32 dims. With
   92% of the features empty, the graph models have less room to memorize
   each thing.
3. **The same 7 fields, complete and true (table7), cut actions to 85% by
   about 40%** (860 vs 1,440) and lift new-object accuracy from 0.65 to
   0.83.
4. **What the graph would need:** about 300 facts (42 objects × 7
   properties), all filled and accurate. That is a small hand-authoring job,
   or a job for an audited external-source mapping (WordNet, ConceptNet,
   Visual Genome), which the project already has mappers for. The current
   6mo rows describe objects mostly through senses, use and feelings ("can be
   smelled", "given as comfort"), not the physical properties these rules use.
