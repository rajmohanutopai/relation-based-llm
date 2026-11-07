# Object Properties V0

Date: 2026-11-07

Status: run complete (2026-11-07); sourced facts failed both rules; blind LLM answers passed, with limits on what that shows

Experiment ID: `object_properties_v0`

## Why

The acting-agent v1 tests found that a complete, true table of 7 properties for
the world's objects cut actions to 85% by about 40%. The user's hand-written
6mo graph gives only 23 of 294 of those cells, and none for objects the agent
hasn't met. Those rows describe senses, use and feelings far more than physical
properties.

So the graph lacks about 300 physical facts. Project rules forbid an LLM writing
rows in bulk, and copying the simulator's table would make any test circular.
This experiment tries the third way: pull the facts from ConceptNet and Visual
Genome through a mapper.

## Method

`scripts/create_object_properties_v0.py`:

- **Raw evidence stays apart.** Each source's evidence goes to its own file.
- **Rules are fixed in code before scoring,** and the mapper doesn't read the
  simulator. A fixed table maps ConceptNet relations and Visual Genome
  attributes to the 7 fields.
- **Each source votes alone,** by total weight. Visual Genome needs at least 5
  mentions. If sources disagree, the cell stays a gap. No fact gets filled in by
  an LLM or by hand.
- **Validator:** one value per cell, known objects and fields, a source named.
- **Noise report:** agreement with the simulator by source and field, read only
  after the facts are written. A review sheet lists each cell with its evidence
  and an empty verdict column for the user, disagreements first.

**A limit of the rule:** the rules can't be tuned after seeing the score. If the
mapping turns out poor, the report says so, and any change is a new version.

## Test

Same as the hand-written graph test in `docs/acting-agent-v1-design.md`: random
agent, 10% flips, same 3 gadgets, 3,000 actions, 5 seeds. World models: names,
hand, sourced (the new facts), sourced_cells_true (same cells, simulator values),
table7. All but names use graph features plus an 8-dim learned slot.

**Pass rule (written before running):** sourced beats names on train curve area
and on new-object accuracy, in at least 4 of 5 seeds.

**Second rule:** sourced beats hand on new-object accuracy, in at least 4 of 5
seeds.

## Prediction (written before running)

- Coverage rises to 25–40% of 385 cells (55 objects × 7 fields), and held-out
  objects now get some cells.
- About 75% of cells agree with the simulator. Sources state few negatives, and
  "soft", "broken" and "closed" will carry wrong senses.
- The pass rule fails or just scrapes through on new-object accuracy, and fails
  on train area, because the graph models have a smaller learned slot.
- The second rule passes, since hand has no held-out cells at all.

## Results

**Mapping (`data/developmental_graph/experiments/object_properties_v0/`):**
54 of 385 cells (14%), of which 6 are on held-out objects. 33 of the 54 (61%)
agree with the simulator: ConceptNet alone 6 of 8, Visual Genome alone 24 of 42,
both together 3 of 4. The sources never disagreed with each other.

Coverage and agreement both came in below my prediction (25–40%, about 75%).

**Agreement here doesn't equal truth.** Many disagreements are a clash of
meaning. A cup is round, and sources say so, but the simulator's `round_like`
means "rolls" (12 of the 21 disagreements are in this field). A phone does ring;
the simulator lists it as not noisy. Other cases are real mapper errors: the
ConceptNet phrase `soft_or_hard` counted as soft, and `break_window` counted as
"the ball can break". Under the rule above, these stay in v0.

**Test (5 seeds, `runs/object_properties_v0/`):**

| World model | train curve area | new objects | actions to 85% |
|---|---:|---:|---:|
| names | 0.823 | 0.648 | ~1,420 |
| hand | 0.805 | 0.625 | ~1,590 |
| sourced | 0.803 | 0.623 | ~1,620 |
| sourced_cells_true | 0.809 | 0.663 | ~1,650 |
| table7 | **0.862** | **0.830** | **~760** |

**Check on the rebuilt measure:** the original test's script never saved
new-object accuracy, so I rebuilt it. It matches the old table exactly on new
objects (0.648, 0.625, 0.830) and within 0.003 on area. My first run used 3
gadgets per room instead of 2 and didn't match; I found and fixed that. The fix
touched the setting only, not the rules or facts.

| rule | result | predicted |
|---|---|---|
| sourced beats names on both measures | **fail** (0 of 5) | fail or scrape through on new objects, fail on area |
| sourced beats hand on new objects | **fail** (2 of 5) | **pass (wrong)** |
| coverage 25–40% | **wrong**: 14% | |
| about 75% agreement | **wrong**: 61% | |

**Reading:**

1. **The sources can't supply this table.** They rarely state plain physical
   facts such as "a spoon is not bouncy", and they almost never state negatives.
2. **Correct values on the same cells help a little.** With simulator values on
   those cells, new-object accuracy rose to 0.663, beating names in 4 of 5
   seeds. That's far short of table7's 0.830. Coverage matters most, and accuracy
   comes next.
3. **The gap has narrowed to one job:** 385 yes-or-no answers, clearly defined.

## Next step: a worksheet for the user

`scripts/create_object_properties_v0.py --worksheet` writes
`data/developmental_graph/relation_authoring/age_6mo_object_properties_worksheet_v0.csv`:
385 plain questions such as "ball: rolls when pushed?", with source evidence
shown and simulator values left out. Project rules stop an LLM writing these in
bulk, so the answers need the user. Answering blind to the simulator gives the
first fair test of a person's graph against this world.

## LLM answers: design (2026-11-07)

The user asked to answer the worksheet with Claude Haiku on their own API key. The
rule against bulk LLM rows is the user's, and they approved this exception for this
worksheet only. Answers stay in
`data/developmental_graph/experiments/object_properties_llm_v0/`, marked as
LLM-sourced, apart from the hand-written rows. `scripts/create_object_properties_llm_v0.py`
sends only the worksheet's questions, never a simulator value. "Unsure" stays a gap.

This tests what a language model knows. It's not the user's own knowledge, so the
worksheet stays open for them.

**Test:** as above, with world models llm and llm_cells_true added.

**Pass rule (written before any answers exist):** llm beats names on train curve area
and on new-object accuracy, in at least 4 of 5 seeds.

**Prediction:** at least 90% of cells answered and about 80% agreeing with the
simulator. Some disagreements will again be clashes of meaning. The rule passes, with
new-object accuracy about 0.75, between names (0.648) and table7 (0.830). Earlier, a
graph with 10% errors and 15% gaps did no better than names on new objects, so this
could fail.

## LLM answers: results

**What changed from the design.** No API key was reachable, and the user then waived
the rule and asked Claude to fill the data. A fresh subagent (Claude Opus 5.5, not
Haiku) answered, given only the questions and told to use no tools. Its log shows it
read no files. `scripts/create_object_properties_llm_v0.py` stays unrun; it would give
a Haiku comparison if a key is added. Answers:
`data/developmental_graph/relation_authoring/age_6mo_object_properties_llm_answers_v0.csv`.
The blank worksheet and the hand-written rows are unchanged.

**Answers:** 362 of 385 cells (94%), the rest "unsure", with 87 cells on held-out
objects. 349 of 362 (96.4%) agree with the simulator. Answering "no" every time would
agree on 77.9%, so that's the fair baseline.

| World model | train curve area | new objects | actions to 85% |
|---|---:|---:|---:|
| names | 0.823 | 0.648 | ~1,420 |
| hand | 0.805 | 0.625 | ~1,590 |
| sourced | 0.803 | 0.623 | ~1,620 |
| **llm** | **0.838** | **0.779** | **~1,160** |
| llm_cells_true | 0.855 | 0.841 | ~890 |
| table7 | 0.862 | 0.830 | ~760 |

| rule or guess | result | predicted |
|---|---|---|
| llm beats names on both measures | **pass (5 of 5)** | pass |
| New-object accuracy | 0.779 | about 0.75 |
| Agreement | 96.4% | about 80% (**too low**) |

**Reading:**

1. **A filled, mostly true graph gives a large gain:** about 18% fewer actions to 85%
   than names, and 0.13 more on objects the agent never met. This is the first graph
   not copied from the simulator's table to beat names.
2. **Coverage was the main gap.** The sourced graph (14% of cells) did nothing.
3. **A few errors cost a lot.** 13 wrong cells (3.6%) account for the fall from 0.841
   to 0.779 on new objects, and part of the fall in speed.
4. **Some "errors" are the simulator's.** It calls a blanket hard to push and says
   a key makes no sound when shaken. Those answers may be right.

**Limits. These matter more than the score:**

- **Not independent of the world.** The simulator's table came from earlier work on
  this project with Claude's help, so Claude's common sense agreeing with it 96% of the
  time may partly reflect one author. I haven't checked how the table was written.
- **The questions weren't fully blind.** I worded them after seeing the simulator,
  including that `round_like` means "rolls". The answering agent saw no simulator
  values, but my wording carried that meaning to it.
- **Circular fields.** These 7 fields are the simulator's own rule inputs, as noted
  below.
- **No language yet.** This helps a toy world model. It doesn't show that the same
  facts help a language model, which is the project's aim.

The fairest next check is a world written by someone else, or a set of properties
chosen before the world exists.

## Caveat

The 7 fields match the simulator's rule inputs, so a good result shows that
sourced facts can stand in for a table the world was built from. It doesn't show
that any real graph helps with real language.
