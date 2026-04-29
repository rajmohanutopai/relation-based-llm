# Core5 V0 Curriculum Variants

Date: 2026-04-28

Experiment ID:

```text
core5_v0
```

## Purpose

Generate the first model-ready five-domain curriculum for comparing matched
training representations:

```text
plain_text
relation_scaffolded
relation_first_then_text
```

This is a data-generation milestone, not a model-quality result.

## Domains

```text
6mo root world:              787 examples
everyday physical world:     612 examples
simple social world:         441 examples
math and abstraction roots:  449 examples
language binding:            766 examples
```

Total curriculum examples:

```text
3055
```

Split counts:

```text
train:           2428
dev:              296
curriculum_test:  331
```

Merged held-out evaluation:

```text
cases:           108
gap probes:       64
transfer probes:  44
```

Held-out domain coverage:

```text
everyday physical world: 33
simple social world:     25
math abstraction:        27
language binding:        23
```

The 6mo root domain is included in training but does not yet have a separate
held-out evaluation.

## Generated Artifacts

```text
scripts/create_core5_curriculum_variants.py
data/developmental_graph/experiments/core5_v0/curriculum.jsonl
data/developmental_graph/experiments/core5_v0/train.jsonl
data/developmental_graph/experiments/core5_v0/dev.jsonl
data/developmental_graph/experiments/core5_v0/curriculum_test.jsonl
data/developmental_graph/experiments/core5_v0/heldout.json
data/developmental_graph/experiments/core5_v0/heldout_prompts.jsonl
data/developmental_graph/experiments/core5_v0/datasets/manifest.json
data/developmental_graph/experiments/core5_v0/manifest.json
data/developmental_graph/experiments/core5_v0/training_config.json
```

Variant dataset paths:

```text
data/developmental_graph/experiments/core5_v0/datasets/plain_text/
data/developmental_graph/experiments/core5_v0/datasets/relation_scaffolded/
data/developmental_graph/experiments/core5_v0/datasets/relation_first_then_text/
```

Each variant has the same source examples in each split. Only the input and
target representation changes.

## Generation Command

```bash
python scripts/create_core5_curriculum_variants.py --overwrite
```

The generator can also render one variant at a time:

```bash
python scripts/create_core5_curriculum_variants.py --variant plain_text --overwrite
```

## Validation

Python compile check:

```bash
python -m py_compile scripts/create_core5_curriculum_variants.py
```

Training dry-runs passed for all variants:

```bash
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0/training_config.json --variant plain_text --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0/training_config.json --variant relation_scaffolded --dry-run
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/core5_v0/training_config.json --variant relation_first_then_text --dry-run
```

JSON manifest checks passed:

```bash
python -m json.tool data/developmental_graph/experiments/core5_v0/manifest.json
python -m json.tool data/developmental_graph/experiments/core5_v0/datasets/manifest.json
python -m json.tool data/developmental_graph/experiments/core5_v0/training_config.json
```

Held-out validation passed with one expected warning:

```text
WARNING: source graph not loaded; graph anchor existence checks skipped
```

Reason: `heldout.json` merges four source evaluations, so there is no single
source graph for the merged file. Each source evaluation validates against its
own graph before merge.

## Interpretation

This creates the first common five-domain curriculum surface for local sanity
tests and nanochat conversion. It does not prove the relation-first hypothesis.

The next meaningful test is to convert the three variants with a shared
tokenizer and run a Level 1 local sanity check before renting GPU time.
