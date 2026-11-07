# Age 6mo Relation Audit V0

Date: 2026-11-07

Status: audit complete; no row or status changed. Decisions are the user's.

Experiment ID: `age_6mo_relation_audit_v0`

## What this is

The 9,253 hand-written rows have never been reviewed: all 520 concepts read
`not_reviewed`. This audit runs machine checks on every row and has one reader,
Claude, judge a fixed random sample of 200. It's a guide to where review effort
should go and doesn't replace the user's review.

`python3 scripts/audit_age_6mo_relations.py --sample 200` writes findings to
`data/developmental_graph/experiments/age_6mo_relation_audit_v0/`.

## Short answer

**The rows are mostly true, and most of them don't connect.** Reading all 9,253
one by one would find few wrong facts. The larger problem is that the same idea
appears under many different phrases, so the rows form little of a graph.

## Machine checks (all rows)

| Check | Count | Reading |
|---|---:|---|
| Missing fields, repeated IDs, self-links | 0 | clean |
| Row counts match the status file | 9,253 | clean |
| Same pair with opposite relations | 0 | clean, for the 7 opposite pairs checked |
| Repeated triples | 106 groups | small clean-up |
| Same triple with both polarities | 2 groups | check by hand: "wet surface is slippery", "closed box blocks seeing inside" |
| Plain text lacks the subject word | 120 | mostly rewording, on a sample of 8 |
| Plain text lacks the object word | 1,303 | mostly rewording or the answer "yes", on a sample of 8 |
| Relation name uses a theory or adult term | 1,231 (13%) | see below |

The word checks are crude, so those two counts overstate real faults.

## Do the rows join up?

Nodes here are exact phrases. "Yes" counts as an answer and not as a node.

| Measure | Value |
|---|---:|
| Distinct nodes | 8,415 |
| Nodes that appear in one row only | 6,905 (82%) |
| Rows with both ends in the 520-concept list | 1,167 of 8,607 (14%) |
| Rows whose subject isn't a concept word | 4,456 of 9,253 (48%) |
| Separate groups of nodes | 1,482 |
| Largest group | 59% of nodes |
| Median rows per node, leaving out baby and caregiver | 1 |

For example, "familiar grandmother face" and a row about "grandmother" share no
node, though a person sees the link at once. Exact matching understates joining,
so a phrase-to-concept step would raise these numbers by an amount not yet
measured.

**Why it matters:** the hypothesis needs relation structure. A row that reaches
nothing else adds a sentence and no structure.

## Reading the sample (200 rows, one reader)

| Judgement | Rows | Examples |
|---|---:|---|
| Wrong or doubtful fact | 1 | 005916 "Feeding ending causes comfort" |
| Garbled | 2 | 004492, 003803 "After supports predicting the outcome of an action" |
| Relation doesn't fit the sentence | 7 | 001641, 004287, 006005, 007224, 007841, 008056, 008237 |
| Adult or theory language for a 6-month-old | 18 | 006987 "means-end precursor", 006910 "memory trace", 004972, 007041 |
| Says nothing | 1 | 001838 "A short toy has the property of being short" |

That leaves 171 of 200 with no fault found, a rate of about 85%. These are my
judgements, and another reader would differ at the edges. With 200 rows, the
18 in the adult-language group means about 9%, give or take 4 points.

The project rule bans adult abstractions as primitives. These rows state them as
facts about a baby, so they deserve the user's closest look. Machine checks flag
1,231 rows on relation name alone; the two sets overlap but differ.

## Recommendation

Don't start with a row-by-row review of all 9,253. In this order:

1. **Decide what to do with theory-language rows.** The user can keep, reword or
   drop them, using the 1,231 flagged rows as the starting list.
2. **Add a phrase-to-concept step**, then remeasure joining. This is the largest
   gain, and it needs a design of its own since it interprets rows. The raw rows
   should stay unchanged.
3. **Clear the small faults:** 106 repeated triples, 2 polarity conflicts.
4. **Sample the rest by batch** for review, and accept a batch when its sample
   passes.

## Caveat

This audit checks form and reads a sample. It doesn't test whether the rows help
a model learn, which is what the training experiments are for.
