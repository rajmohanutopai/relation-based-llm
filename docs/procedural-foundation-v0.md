# Procedural Foundation V0

Date: 2026-04-28

Experiment ID:

```text
procedural_foundation_v0
```

## Purpose

Generate scenarios from relation rules instead of simple repetition.

The generator reuses a small noun world across many states and actions:

```text
28 things
4 height states
2 distance states
6 hand actions
3 support surfaces
```

It derives outcomes using rules:

```text
near + reachable height + action -> hand touches thing
far or very high -> hand does not touch thing
touch -> baby feels thing
touch + movable thing -> hand can make thing move
unsafe thing -> not ok
heavy or big thing -> movement resistance
```

## Output

```text
data/developmental_graph/experiments/procedural_foundation_v0/
```

Generator:

```text
scripts/create_procedural_foundation_world.py
```

Generated variants:

```text
procedural_plain_text
procedural_relation_scaffolded
procedural_relation_first_then_text
```

Split counts per variant:

```text
train:           2994
dev:              302
curriculum_test:  592
total:           3888
```

Train examples include both positive and negative outcomes:

```text
touch/reach true:   835
touch/reach false: 2159
```

## Example

Positive:

```text
s: baby lift hand. ball high. ball near. ball on floor.
q: does hand touch ball?
a:
```

Target with relations:

```text
a: yes
f: hand touch ball
r: baby can move hand
r: hand go up
r: ball near hand
r: ball high
r: ball on floor
r: ball is soft
r: hand touch ball
r: baby feel ball
r: hand can make ball move
r: ball can roll
```

Negative:

```text
s: baby close hand. pen very high. pen far. pen on bed.
q: does hand touch pen?
a:
```

Target with relations:

```text
a: no
f: hand not touch pen
n: hand not touch pen
n: baby cannot feel pen
n: hand cannot make pen move
n: baby cannot reach pen
n: pen too far
```

## Vocabulary

Train split vocabulary:

```text
procedural_plain_text:                59 alpha words
procedural_relation_scaffolded:       73 alpha words
procedural_relation_first_then_text:  73 alpha words
```

## Interpretation

This is closer to the intended theory than template repetition. The model sees
many different concrete states where primitive relations combine into outcomes.

This dataset should be expanded by adding more procedural rule families:

```text
drop/support/fall
container/in/out
open/closed/path blocked
hot/cold/pain/avoid
sound from shake/hit
hide/see/not see
caregiver approach/comfort
same/different/more/less
word-name binding
```

## Validation

Completed checks:

```text
python -m py_compile scripts/create_procedural_foundation_world.py
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v0/manifest.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v0/datasets/manifest.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v0/training_config.json
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v0/training_config.json --variant procedural_plain_text --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v0/training_config.json --variant procedural_relation_scaffolded --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v0/training_config.json --variant procedural_relation_first_then_text --dry-run
```

Source example IDs match across all variants for every split.
