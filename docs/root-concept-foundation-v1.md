# Root Concept Foundation V1

Date: 2026-04-30

Experiment ID:

```text
root_concept_foundation_v1
```

## Purpose

This is the corrected root concept foundation for the TinyStories
relation-first path.

V0 was useful as a first sketch, but it had problems for a serious experiment:

```text
1. Some root facts could leak across train/dev/test through different renderings.
2. Dev/test included definition-style rows instead of mostly application probes.
3. Relation types were too overloaded.
4. The root set under-modeled concrete positive/negative cases.
5. The happiness mechanism was present only lightly.
```

V1 fixes those issues and should replace V0 as the root foundation candidate.

## Core Idea

The root model should not memorize every future word directly.

Instead, it should learn reusable anchors:

```text
animal is living thing
living thing needs food
animal needs food
```

Later word attachment can then be compact:

```text
dog is animal
puppy is young animal
pet is animal near people
```

The expected benefit is that TinyStories words attach to an already learned
relational base instead of needing all meaning to be learned from raw story text.

## Current Scope

Generator:

```text
scripts/create_root_concept_foundation_v1.py
```

Seed graph:

```text
data/developmental_graph/seeds/root_concept_foundation_v1.json
```

Generated dataset:

```text
data/developmental_graph/experiments/root_concept_foundation_v1/
```

Graph counts:

```text
layers: 11
nodes: 133
relations: 172
micro experiences: 84
evaluation questions: 34
```

Layer counts:

```text
root: 23
body_self: 16
space: 8
physical: 19
property: 14
living: 7
need_valence: 8
emotion: 6
social: 14
language: 8
time_change: 10
```

## Dataset Variants

```text
root_prose   ordinary text only
root_qa      QA/probe format only
root_mixed   prose + QA together
```

Counts:

```text
root_prose: 239 train,  6 dev, 11 curriculum_test
root_qa:    306 train, 12 dev, 22 curriculum_test
root_mixed: 545 train, 18 dev, 33 curriculum_test
```

## What Changed From V0

V1 splits by canonical group id:

```text
touch.ball.near
touch.ball.far
container.cup.box.open
container.cup.box.closed
```

This prevents the same underlying fact or scenario from appearing in both train
and held-out data through a different wording.

V1 also keeps root fact rows in train only. Dev/test rows are mostly scenario
applications:

```text
Scene: The needle is sharp. The hand touches the needle.
Question: What happens?
Answer:
```

Target:

```text
answer: the sharp needle can hurt the skin.
reason: sharp causes pain.
```

V1 uses clearer relation names:

```text
is_a
part_of
controlled_by
uses
feels
has_property
can_do
can_make
causes
prevents
enables
reduces
signals
needs
contrasts_with
```

This avoids forcing too many different meanings into one relation type.

## Scenario Families

V1 includes concrete positive/negative contrasts:

```text
near hand -> can touch
far hand -> cannot touch
open container -> can touch inside object
closed container -> cannot touch inside object
soft object -> comfort/touch
hot or sharp object -> pain
light object -> can move
heavy object -> does not move
hold support -> does not fall
release support -> falls
```

It also includes early social/language cases:

```text
caregiver helps -> pain reduces -> comfort
friend shares -> play/happy
person hurts -> pain/sad
name names object
hear word wakes word/name relation
story has event
```

## Happiness Mechanism

V1 adds the project-specific happiness theory as root data:

```text
new link causes happy
new link can make excited
strong link causes less excited
broken link causes sad
pain causes bad
comfort causes good
help reduces pain
```

Example:

```text
The child learns a new word for the ball.
```

Expected answer:

```text
The child feels happy and excited.
```

This is still a small first encoding. The next version should make this more
procedural by generating many relation-strength and diminishing-return cases.

## Validation

Commands run:

```text
python -m py_compile scripts/create_root_concept_foundation_v1.py
python scripts/create_root_concept_foundation_v1.py --overwrite
python scripts/validate_developmental_graph.py data/developmental_graph/seeds/root_concept_foundation_v1.json --stats
jq '.leakage_report' data/developmental_graph/experiments/root_concept_foundation_v1/datasets/manifest.json
```

Result:

```text
Graph validation passes.
No train/dev/test group leakage found for root_prose, root_qa, or root_mixed.
```

Leakage report:

```text
root_mixed: no train/dev/test group overlap
root_prose: no train/dev/test group overlap
root_qa:    no train/dev/test group overlap
```

## Current Limitation

This is a clean root foundation, not yet enough data for a strong neural
training run by itself.

The next serious training dataset should expand from this seed into a larger
procedural curriculum:

```text
1. More objects, people, places, actions, and properties.
2. More near/far, open/closed, support/fall, hot/sharp/soft cases.
3. More living/social/language cases.
4. More happiness-strength cases.
5. Matched controls: sparse text, corrupt relations, and raw TinyStories.
```

## Next Stage

Use V1 as the root seed for:

```text
tinystories_word_attachment_v0
```

Process:

```text
1. Extract frequent TinyStories content words.
2. Map them to V1 root anchors.
3. Add compact inheritance definitions.
4. Train root foundation first.
5. Continue training on word attachment.
6. Continue training on TinyStories text.
7. Compare against TinyStories-only from scratch with the same token budget.
```

Main comparison:

```text
A. TinyStories only
B. root foundation -> TinyStories
C. root foundation -> word attachment -> TinyStories
D. corrupt/shuffled attachment -> TinyStories
```

The key question is whether C learns better generation and held-out
understanding than A and D at the same model size and token budget.
