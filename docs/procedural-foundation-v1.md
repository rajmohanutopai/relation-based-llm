# Procedural Foundation V1

Date: 2026-04-28

Experiment ID:

```text
procedural_foundation_v1
```

## Purpose

Replace the rough procedural V0 generator with coherent scenario grammars.

V0 combined independent fields and produced awkward scenes such as:

```text
baby close hand. pen very high. pen far. pen on bed.
```

V1 uses rule-family-specific layouts so the scene itself makes sense.

## Output

```text
data/developmental_graph/experiments/procedural_foundation_v1/
```

Generator:

```text
scripts/create_procedural_foundation_world_v1.py
```

Generated variants:

```text
procedural_plain_text
procedural_relation_scaffolded
procedural_relation_first_then_text
```

Split counts per variant:

```text
train:           542
dev:              66
curriculum_test:  81
total:           689
```

Train cases:

```text
positive: 251
negative: 291
```

Train vocabulary:

```text
procedural_plain_text:                79 alpha words
procedural_relation_scaffolded:      106 alpha words
procedural_relation_first_then_text: 106 alpha words
```

## Rule Families

```text
reach_touch:             205 total
push_move:               104 total
drop_fall:                54 total
shake_sound:              20 total
hide_see:                153 total
container_open_closed:   135 total
hot_cold_touch:           18 total
```

## Example Scenarios

Reach/touch positive:

```text
s: ball is on bed near baby. baby reaches hand.
q: does hand touch ball?
a:
```

Target with relations:

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

Reach/touch negative:

```text
s: pen is on high shelf. baby reaches hand up.
q: does hand touch pen?
a:
```

Expected relation shape:

```text
a: no
f: hand does not touch pen
r: baby can move hand
r: pen is far
r: pen is very high
r: pen is on shelf
n: hand does not touch pen
n: baby does not feel pen
n: hand cannot make pen move
n: pen is too far
n: pen is too high
```

Container negative:

```text
s: ball is in closed bowl. baby puts hand on bowl.
q: does hand touch ball?
a:
```

Target with relations:

```text
a: no
f: hand does not touch ball
r: bowl can hold ball
r: ball is near baby
r: bowl is closed
n: closed bowl blocks hand
n: hand does not touch ball
```

Hide/see negative:

```text
s: ball is under blanket. baby looks.
q: does baby see ball?
a:
```

Target:

```text
a: no
f: baby does not see ball
r: baby can see
r: blanket covers ball
n: baby does not see ball
```

## Quality Decision

V1 is qualitatively better than V0 because the scenario grammar owns the
relation logic:

```text
reach/touch uses reachable layouts
push/move uses reachable + movable + light checks
drop/fall uses in-hand vs not-in-hand
shake/sound uses sound-making objects
hide/see uses cover and uncover layouts
container uses open/closed/in/beside layouts
hot/cold uses touch valence
```

This is still not enough data for serious from-scratch training. It is the
clean seed to expand.

## Next Expansion

Add more derived questions per coherent scenario:

```text
does hand touch X?
does baby feel X?
does X move?
why not?
what blocks touch?
what changed after action?
```

Add more rule families:

```text
support / edge / fall
same / different / match
more / less / count
near / far movement over time
open / closed path
caregiver approach / comfort
word-name binding
```

## Validation

Completed checks:

```text
python -m py_compile scripts/create_procedural_foundation_world_v1.py
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v1/manifest.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v1/datasets/manifest.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v1/training_config.json
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v1/training_config.json --variant procedural_plain_text --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v1/training_config.json --variant procedural_relation_scaffolded --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/procedural_foundation_v1/training_config.json --variant procedural_relation_first_then_text --dry-run
```

Source example IDs match across all variants for every split.
