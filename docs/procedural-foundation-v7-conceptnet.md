# Procedural Foundation V7 ConceptNet

Date: 2026-05-01

Experiment ID:

```text
procedural_foundation_v7_conceptnet
```

Seed graph:

```text
data/developmental_graph/seeds/adi_conceptnet_v7.json
```

## Purpose

V7 starts the reusable project-specific ConceptNet layer.

The goal is not to import ConceptNet raw. Raw ConceptNet is broad, flat, noisy,
and not developmentally ordered. V7 instead creates a curated staged lexicon:

```text
word -> age level -> domain tags -> prerequisite earlier words -> relation bundle
```

A word is treated as a handle to a relation bundle. Later-stage words may use
earlier-stage words in their definitions because the training curriculum should
teach those earlier handles first.

The age level is the learning order. Domain tags are separate labels for
analysis and expansion; they should not control training order by themselves.

## Age Levels

```text
age_6mo  direct embodied roots: body, touch, pain, comfort, near/far, caregiver, basic object handles
age_1yo  object permanence, simple action, containment, food/water, early words, simple social response
age_3yo  richer objects, language, play, animals, places, before/after, simple cause and category
age_5yo  school-ready abstractions: number, measure, story, geography/history seeds, rules, truth, society
```

## Counts

Seed graph:

```text
concepts: 215
relations: 283
```

By stage:

```text
age_6mo: 39
age_1yo: 51
age_3yo: 47
age_5yo: 78
```

Selected domain tag counts:

```text
physical: 39
social: 32
property: 15
root: 14
place: 13
abstract: 12
body: 11
language: 11
living: 11
emotion: 10
math: 8
time: 8
space: 8
```

Generated source rows:

```text
train:           713
dev:             279
curriculum_test: 156
```

Dataset variants:

```text
concept_dense_qa  QA rows only
concept_prose     prose concept rows only
concept_mixed     QA + prose rows
```

Rendered records:

```text
concept_dense_qa: train 498, dev 279, curriculum_test 156
concept_prose:    train 215, dev   0, curriculum_test   0
concept_mixed:    train 713, dev 279, curriculum_test 156
```

## Examples

`ball`:

```text
stage: age_1yo
domains: physical
summary: round toy that can roll and bounce
prerequisites: toy, round, move
relations:
  ball is a toy
  ball is usually round
  ball can roll
  ball can bounce
```

`cube`:

```text
stage: age_1yo
domains: physical
summary: object with flat sides
prerequisites: object, shape
relations:
  cube has flat sides
  cube does not roll easily
```

`puppy`:

```text
stage: age_3yo
domains: living
summary: young dog
prerequisites: dog, young
relations:
  puppy is dog
  puppy is young animal
```

`knowledge`:

```text
stage: age_5yo
domains: abstract
summary: strong remembered relations that can be used
prerequisites: relation, remember
relations:
  knowledge is made of remembered relations
```

## Generated Training Surfaces

Concept card:

```text
Word: ball
Known earlier words: toy, round, move
Question: What kind of thing is ball?
Answer:
```

Target:

```text
answer: round toy that can roll and bounce.
reason: ball is learned as object.
```

Relation fact:

```text
Word: ball
Question: What relation connects ball and roll?
Answer:
```

Target:

```text
answer: ball can roll.
reason: ball has a can_do relation with roll.
```

Held-out prerequisite probe:

```text
Word: geography
Question: Which earlier word helps build the meaning of geography?
Answer:
```

Target:

```text
answer: place.
reason: geography uses place as an earlier relation handle.
```

## Validation

Commands run:

```text
python -m py_compile scripts/create_procedural_foundation_world_v7_conceptnet.py
python scripts/create_procedural_foundation_world_v7_conceptnet.py --overwrite
python -m json.tool data/developmental_graph/seeds/adi_conceptnet_v7.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v7_conceptnet/manifest.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v7_conceptnet/datasets/manifest.json
```

Validation result:

```text
duplicate words: 0
missing prerequisites: 0
forward prerequisites: 0
empty relation bundles: 0
passes: true
```

## Important Limits

This is a first reusable V7 seed, not the final full vocabulary.

It is intentionally small enough to review by hand. The next expansion should
add high-frequency words in batches, but preserve the rule that a later concept
can only depend on same-stage or earlier-stage handles after deliberate review.

The current rows are still mostly definitional QA/prose. Before using V7 for a
serious model comparison, we should add procedural scene renderers that turn
the relation bundles into ordinary examples:

```text
The ball is round. The child pushes it. The ball rolls.
Question: Why does it roll?
Answer: because round things can roll.
```

## Files

Generator:

```text
scripts/create_procedural_foundation_world_v7_conceptnet.py
```

Seed:

```text
data/developmental_graph/seeds/adi_conceptnet_v7.json
```

Generated output:

```text
data/developmental_graph/experiments/procedural_foundation_v7_conceptnet/
```

Manifest:

```text
data/developmental_graph/experiments/procedural_foundation_v7_conceptnet/manifest.json
```

## Decision

Use V7 as the curated relation-lexicon source of truth.

Do not train a serious model on V7 alone yet. Next, add a V7 scene renderer
that converts the word relation bundles into ordinary relation-dense examples,
then compare:

```text
TinyStories/plain text only
vs
V7 staged lexicon -> V7 scene curriculum -> TinyStories
```
