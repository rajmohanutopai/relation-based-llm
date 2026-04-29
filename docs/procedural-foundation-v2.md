# Procedural Foundation V2

Date: 2026-04-28

Experiment ID:

```text
procedural_foundation_v2
```

## Purpose

Expand the coherent procedural foundation world without going back to
free-form generation.

V2 keeps V1's scenario grammars and adds two kinds of growth:

```text
1. derived questions from the same scenario
2. new rule families for support, comparison, path, comfort, and word naming
```

The point is to create many relation-learning situations from a small noun
world, while keeping each line understandable by itself.

## Output

```text
data/developmental_graph/experiments/procedural_foundation_v2/
```

Generator:

```text
scripts/create_procedural_foundation_world_v2.py
```

Generated variants:

```text
procedural_plain_text
procedural_relation_scaffolded
procedural_relation_first_then_text
```

Split counts per variant:

```text
train:           2477
dev:              302
curriculum_test:  378
total:           3157
```

Train cases:

```text
positive: 1136
negative: 1341
```

Train vocabulary:

```text
procedural_plain_text:                133 alpha words
procedural_relation_scaffolded:       155 alpha words
procedural_relation_first_then_text:  155 alpha words
```

## Rule Families

```text
reach_touch:             1106 total
push_move:                344 total
drop_fall:                162 total
shake_sound:               60 total
hide_see:                 459 total
container_open_closed:    540 total
hot_cold_touch:            72 total
support_edge_fall:         72 total
same_different_match:     102 total
more_less_count:          120 total
path_open_closed:          36 total
caregiver_comfort:         12 total
word_name_binding:         72 total
```

## Question Types

V2 asks multiple questions over the same underlying world state:

```text
main
what_happened
touch
feel
move
why_no_touch
open_closed
block
cover
see
in_hand
hear_sound
ok_touch
fall
edge
why
same_color
same_shape
more
less
go_through
open
ok
help
word_match
what_name
```

This is important because the model should not learn only one answer shape. It
should learn that the same relation packet can answer different questions.

## Example Scenarios

Reach/touch:

```text
s: ball is on bed near baby. baby reaches hand.
q: does hand touch ball?
a:
```

Relation target:

```text
a: yes
f: hand touches ball
r: baby can move hand
r: ball is near
r: ball is middle
r: ball is on bed
r: hand touches ball
r: baby feels ball
r: ball is soft
r: ball is small
r: ball is light
r: hand can make ball move
```

Support/edge/fall:

```text
s: ball is on edge of bed. baby bumps bed.
q: does ball fall?
a:
```

Relation target:

```text
a: yes
f: ball falls down
r: ball is on edge of bed
r: baby bumps bed
r: ball is at edge
r: ball falls down
r: ball hits floor
```

More/less:

```text
s: left has zero ball. right has one ball. baby looks.
q: which has less?
a:
```

Relation target:

```text
a: left
f: left has less
r: left has 0
r: right has 1
r: right has more
r: left has less
```

Open/closed path:

```text
s: box is closed. baby pushes ball to box.
q: can ball go through?
a:
```

Relation target:

```text
a: no
f: ball cannot go through box
r: box is closed
n: closed box blocks ball
n: ball cannot go through box
```

Caregiver comfort:

```text
s: baby cries. mom comes near. mom holds baby.
q: what helps?
a:
```

Relation target:

```text
a: mom near helps baby
f: mom near helps baby
r: baby not ok
r: mom near helps baby
r: baby ok
```

Word-name binding:

```text
s: mom says ball. ball is here. baby looks.
q: does word name ball?
a:
```

Relation target:

```text
a: yes
f: word ball names ball
r: word ball names ball
r: ball is here
```

## Quality Decision

V2 was the best procedural foundation dataset at the time it was created.
It has since been superseded by `procedural_foundation_v3`, which expands the
base world before generating rows.

It is better than V1 because it teaches:

```text
same scenario -> many question views
object state -> effect
reachable/unreachable -> touch/no touch
open/closed -> path/block
edge/middle -> fall/stay
same/different -> comparison
more/less -> quantity comparison
caregiver near/action -> comfort change
word sound -> object name binding
```

It is still useful as a historical comparison point. It is better than V1
because it has more rows while keeping vocabulary small, but V3 should be used
for the next active nanochat smoke test.

## Validation

Completed checks:

```text
python -m py_compile scripts/create_procedural_foundation_world_v2.py
python scripts/create_procedural_foundation_world_v2.py --overwrite
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v2/manifest.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v2/datasets/manifest.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v2/training_config.json
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v2/training_config.json --variant procedural_plain_text --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v2/training_config.json --variant procedural_relation_scaffolded --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v2/training_config.json --variant procedural_relation_first_then_text --dry-run
```

Source example IDs match across all variants for every split.

No model training has been run for V2 yet.
