# Core5 V0 Child Language

Date: 2026-04-28

Experiment ID:

```text
core5_v0_childlang
```

## Purpose

Create the simplest current Core5 training surface before nanochat
from-scratch training.

This variant starts below the previous controlled-vocabulary dataset:

```text
no JSON
colon-delimited fields
simple field names
technical words rewritten where possible
relations expressed as from/link/to lines
```

Example:

```text
do: why
world: baby world
scene: if the baby moves his hand what link makes the hand part of own body
ask: why
answer:
```

Target:

```text
answer: baby can move hand and can feel hand
links:
link: from hand how can move to own body
```

## Output

```text
data/developmental_graph/experiments/core5_v0_childlang/
```

Generated variants:

```text
child_plain_text
child_relation_scaffolded
child_relation_first_then_text
```

Split counts per variant:

```text
train:           2428
dev:              296
curriculum_test:  331
held-out:         108
```

## Vocabulary

Train split vocabulary counts:

```text
child_plain_text:                1342 alpha words, 1349 raw tokens
child_relation_scaffolded:       1342 alpha words, 1350 raw tokens
child_relation_first_then_text:  1343 alpha words, 1351 raw tokens
```

The following technical words were checked and are absent from
`child_plain_text` train:

```text
proto
sensation
schema
invariant
relation
concept
domain
target
source
graph
anchor
family
valence
proprioception
activation
cluster
binding
contextual
abstraction
scaffolded
```

The vocabulary list is stored at:

```text
data/developmental_graph/experiments/core5_v0_childlang/vocabulary/train_alpha_words.txt
```

## Comparison

Original `core5_v0` train vocabulary:

```text
plain_text:                1842 alpha words, 2981 raw tokens
relation_scaffolded:       1940 alpha words, 5992 raw tokens
relation_first_then_text:  1948 alpha words, 8547 raw tokens
```

Controlled `core5_v0_controlled` train vocabulary:

```text
controlled_plain_text:                1367 alpha words, 1832 raw tokens
controlled_relation_scaffolded:       1369 alpha words, 1838 raw tokens
controlled_relation_first_then_text:  1370 alpha words, 1840 raw tokens
```

Child-language `core5_v0_childlang` train vocabulary:

```text
child_plain_text:                1342 alpha words, 1349 raw tokens
child_relation_scaffolded:       1342 alpha words, 1350 raw tokens
child_relation_first_then_text:  1343 alpha words, 1351 raw tokens
```

## Generation Command

```bash
python scripts/create_core5_child_language_variants.py --overwrite
```

Generator:

```text
scripts/create_core5_child_language_variants.py
```

## Validation

Completed checks:

```text
python -m py_compile scripts/create_core5_child_language_variants.py
python -m json.tool data/developmental_graph/experiments/core5_v0_childlang/manifest.json
python -m json.tool data/developmental_graph/experiments/core5_v0_childlang/datasets/manifest.json
python -m json.tool data/developmental_graph/experiments/core5_v0_childlang/training_config.json
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0_childlang/training_config.json --variant child_plain_text --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0_childlang/training_config.json --variant child_relation_scaffolded --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0_childlang/training_config.json --variant child_relation_first_then_text --dry-run
```

The source examples match across all variants for every split.

Held-out validation passes with the expected merged-source warning:

```text
WARNING: source graph not loaded; graph anchor existence checks skipped
```

## Interpretation

This is now the recommended first nanochat dataset. It better matches the
developmental idea:

```text
learn simple relation patterns first
attach harder words later
avoid making the tiny model learn JSON or adult theory language at the start
```

This is still not as simple as a true one-month or six-month sensory curriculum.
It is a practical bridge: simpler than the full Core5 graph language, but broad
enough to include baby world, physical world, people world, number world, and
word world.
