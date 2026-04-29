# Core5 V0 Controlled Vocabulary

Date: 2026-04-28

Experiment ID:

```text
core5_v0_controlled
```

## Purpose

Create a smaller language surface before nanochat from-scratch training.

The original `core5_v0` data preserves richer prose and JSON-like relation
targets. This controlled pass keeps the same examples and splits, but renders
them with lower-case fixed templates and compact relation packets.

## Output

```text
data/developmental_graph/experiments/core5_v0_controlled/
```

Generated variants:

```text
controlled_plain_text
controlled_relation_scaffolded
controlled_relation_first_then_text
```

Split counts per variant:

```text
train:           2428
dev:              296
curriculum_test:  331
```

## Vocabulary

Train split vocabulary counts:

```text
controlled_plain_text:                1367 alpha words, 1832 raw tokens
controlled_relation_scaffolded:       1369 alpha words, 1838 raw tokens
controlled_relation_first_then_text:  1370 alpha words, 1840 raw tokens
```

Union across all controlled train variants:

```text
1370 alpha words
```

The vocabulary list is stored at:

```text
data/developmental_graph/experiments/core5_v0_controlled/vocabulary/train_alpha_words.txt
```

## Comparison To Core5 V0

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

This removes most JSON/schema token noise and reduces the surface vocabulary
while keeping concept words such as body parts, objects, properties, actions,
social cues, math roots, and language-binding terms.

## Generation Command

```bash
python scripts/create_core5_controlled_vocabulary_variants.py --overwrite
```

Generator:

```text
scripts/create_core5_controlled_vocabulary_variants.py
```

## Validation

Completed checks:

```text
python -m py_compile scripts/create_core5_controlled_vocabulary_variants.py
python -m json.tool data/developmental_graph/experiments/core5_v0_controlled/manifest.json
python -m json.tool data/developmental_graph/experiments/core5_v0_controlled/datasets/manifest.json
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0_controlled/training_config.json --variant controlled_plain_text --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0_controlled/training_config.json --variant controlled_relation_scaffolded --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0_controlled/training_config.json --variant controlled_relation_first_then_text --dry-run
```

The source examples match across all variants for every split.

Held-out validation also passes with the expected merged-source warning:

```text
WARNING: source graph not loaded; graph anchor existence checks skipped
```

The warning is expected because the held-out file merges multiple source graphs.

## Interpretation

This is the better starting point for nanochat training than raw `core5_v0`.
The model still sees meaningful words, but the representation is less noisy and
more regular.

If the first nanochat run still struggles, the next tightening step would be a
stricter concept-code variant. That would reduce vocabulary further, but it
would also weaken the word-understanding test.
