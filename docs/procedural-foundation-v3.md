# Procedural Foundation V3

Date: 2026-04-28

Experiment ID:

```text
procedural_foundation_v3
```

## Purpose

Expand the base world before generating more rows.

V2 was useful, but its base world was still too small. V3 keeps the same
relation-first experiment shape and builds a larger baby + physical + simple
social world.

Formal math is still excluded, except primitive comparison roots:

```text
same/different
more/less
open/closed
near/far
touch/no touch
safe/unsafe
comfort/discomfort
```

## Output

```text
data/developmental_graph/experiments/procedural_foundation_v3/
```

Generator:

```text
scripts/create_procedural_foundation_world_v3.py
```

Base world:

```text
data/developmental_graph/experiments/procedural_foundation_v3/base_world.json
```

Generated variants:

```text
procedural_plain_text
procedural_relation_scaffolded
procedural_relation_first_then_text
```

Split counts per variant:

```text
train:           4536
dev:              553
curriculum_test:  623
total:           5712
```

Train cases:

```text
positive: 2449
negative: 2087
```

Train vocabulary:

```text
procedural_plain_text:                302 alpha words
procedural_relation_scaffolded:       334 alpha words
procedural_relation_first_then_text:  334 alpha words
```

## Base World

V3 has 208 base entities:

```text
body:           25
person:         18
surface:        13
place:          15
toy:             9
object:         42
container:      10
food:           28
material:       24
social_signal:  24
```

It also has:

```text
colors: 7
shapes: 6
count values: 0-4
```

This is the important improvement over V2: the generator no longer creates
many rows from only a tiny toy world.

## Rule Families

```text
reach_touch:              1332
push_pull_move:            472
body_control:               64
drop_fall:                 268
support_edge_fall:        1072
container_open_closed:     395
hide_see:                  180
shake_sound:                47
temperature_touch:          45
wet_dry:                   160
safe_unsafe_touch:          81
same_different_match:      505
more_less_count:           720
path_open_closed:          168
caregiver_comfort:          24
familiar_agent:             11
social_signal_response:     16
give_take:                  64
word_name_binding:          88
```

## Example Rows

Body control:

```text
s: baby tries to move arm.
q: can baby move arm?
a:
```

Relation target:

```text
a: yes
f: baby can move arm
r: arm is body
r: baby has body
r: baby can move arm
r: arm moves with baby
```

Blocked touch:

```text
s: apple is behind closed door. baby reaches hand.
q: does baby feel apple?
a:
```

Relation target:

```text
a: no
f: baby does not feel apple
r: baby can move hand
r: apple is near
r: apple is blocked
r: apple is behind door
n: hand does not touch apple
n: baby does not feel apple
n: closed door blocks hand
```

Temperature:

```text
s: bottle is hot. baby touches bottle.
q: is touch ok?
a:
```

Relation target:

```text
a: no
f: touching bottle is not ok
r: bottle is hot
r: hand touches bottle
n: touching bottle can hurt baby
n: baby not ok
```

Caregiver comfort:

```text
s: baby is hungry. mom gives milk.
q: what helps?
a:
```

Relation target:

```text
a: milk helps baby
f: milk helps baby
r: baby not ok
r: milk helps baby
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

V3 is now the current active procedural dataset.

V2 is still useful historically, but V3 is better for the next nanochat smoke
test because it has:

```text
larger base entity world
more baby/body grounding
more everyday physical grounding
more simple social grounding
still controlled vocabulary
same three matched representation variants
```

Known limitation:

```text
V3 is still generated symbolic data. It is a stronger local smoke-test corpus,
not a real replacement for broader natural text or human observation.
```

## Validation

Completed checks:

```text
python -m py_compile scripts/create_procedural_foundation_world_v3.py
python scripts/create_procedural_foundation_world_v3.py --overwrite
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v3/base_world.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v3/manifest.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v3/datasets/manifest.json
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v3/training_config.json --variant procedural_plain_text --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v3/training_config.json --variant procedural_relation_scaffolded --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v3/training_config.json --variant procedural_relation_first_then_text --dry-run
```

Source example IDs match across all variants for every split.

No model training has been run for V3 yet.
