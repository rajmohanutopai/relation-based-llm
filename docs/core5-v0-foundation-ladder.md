# Core5 V0 Foundation Ladder

Date: 2026-04-28

Experiment ID:

```text
core5_v0_foundation
```

## Purpose

Create a staged pre-curriculum before `core5_v0_childlang`.

This is not a vocabulary ban. It is a relation-support ladder:

```text
f0: simple fact first
f1: introduce a handle after support facts
f2: ask using the handle
f3: attach a later name to the learned handle
```

Example ladder:

```text
f0
l: f0
s: baby move hand
q: ?
a:

a: baby can move hand
```

```text
f1
l: f1
s: baby can move hand
q: name
a:

a: body
r: hand is body
```

```text
f2
l: f2
s: hand body
q: can baby move hand
a:

a: yes
r: baby can move hand
```

```text
f3
l: f3
s: hand body
q: later name
a:

a: own body
r: own body name body
```

## Output

```text
data/developmental_graph/experiments/core5_v0_foundation/
```

Generated variants:

```text
foundation_plain_text
foundation_relation_scaffolded
foundation_relation_first_then_text
```

Split counts per variant:

```text
train:            403
dev:               60
curriculum_test:   53
held-out:         108
```

Train stage counts:

```text
f0: 353
f1:  28
f2:  14
f3:   8
```

## Vocabulary

Train split vocabulary counts:

```text
foundation_plain_text:                92 alpha words, 96 raw tokens
foundation_relation_scaffolded:       93 alpha words, 97 raw tokens
foundation_relation_first_then_text:  93 alpha words, 97 raw tokens
```

Union across all foundation train variants:

```text
93 alpha words
```

The vocabulary list is stored at:

```text
data/developmental_graph/experiments/core5_v0_foundation/vocabulary/train_alpha_words.txt
```

## Interpretation

This is now the first rung, not the final training set.

Use order:

```text
1. core5_v0_foundation
2. core5_v0_childlang
3. core5_v0_controlled or full core5_v0
```

The reason is conceptual:

```text
body / own body are not banned
they are introduced only after baby can move hand / baby can feel hand
```

This better matches the project theory: a word with high relation-load should be
introduced only after its supporting relations have appeared.

## Validation

Completed checks:

```text
python -m py_compile scripts/create_core5_foundation_variants.py
python -m json.tool data/developmental_graph/experiments/core5_v0_foundation/manifest.json
python -m json.tool data/developmental_graph/experiments/core5_v0_foundation/datasets/manifest.json
python -m json.tool data/developmental_graph/experiments/core5_v0_foundation/training_config.json
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0_foundation/training_config.json --variant foundation_plain_text --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0_foundation/training_config.json --variant foundation_relation_scaffolded --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0_foundation/training_config.json --variant foundation_relation_first_then_text --dry-run
```

The source foundation unit IDs match across all variants for every split.

Held-out validation passes with the expected merged-source warning:

```text
WARNING: source graph not loaded; graph anchor existence checks skipped
```
