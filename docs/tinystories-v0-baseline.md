# TinyStories V0 Baseline

Date: 2026-04-29

Experiment ID:

```text
tinystories_v0
```

## Purpose

Create a normal simple-text baseline for the V3 relation experiment.

The procedural V3 data is relation-designed even when rendered as plain text.
So the fuller comparison needs a fourth arm:

```text
A. normal simple text
B. relation-designed plain text
C. relation-scaffolded text
D. relation-first text
```

TinyStories is a good first normal-simple baseline because it is a large
synthetic corpus of short stories using a small child-level vocabulary.

Sources:

```text
dataset: https://huggingface.co/datasets/roneneldan/TinyStories
paper:   https://arxiv.org/abs/2305.07759
```

## Output

```text
data/developmental_graph/experiments/tinystories_v0/
```

Generator:

```text
scripts/create_tinystories_baseline.py
```

Variant:

```text
tinystories_plain_text
```

## Budget Match

This slice is word-budget matched to the V3 relation variants, not row-count
matched.

Requested budget:

```text
train: 270309 words
dev:    32772 words
test:   36626 words
```

Actual complete-story budget:

```text
train: 270421 words
dev:    33008 words
test:   36695 words
```

Complete stories are kept, so the actual totals are slightly above the target.

## Counts

```text
train stories: 1607
dev stories:    208
test stories:   225
```

Vocabulary:

```text
train alpha words: 5211 unique
dev alpha words:   2043 unique
test alpha words:  2179 unique
```

This is much broader vocabulary than procedural V3. That is expected and should
be recorded as a difference, not hidden.

## Validation

Completed checks:

```text
python -m py_compile scripts/create_tinystories_baseline.py
python scripts/create_tinystories_baseline.py --overwrite
python -m json.tool data/developmental_graph/experiments/tinystories_v0/manifest.json
python -m json.tool data/developmental_graph/experiments/tinystories_v0/datasets/manifest.json
python -m json.tool data/developmental_graph/experiments/tinystories_v0/training_config.json
python scripts/train_tiny_causal_lm.py --config data/developmental_graph/experiments/tinystories_v0/training_config.json --variant tinystories_plain_text --dry-run
```

Overlap check:

```text
train/dev overlap: 0
train/test overlap: 0
dev/test overlap: 0
```

No model training has been run for this baseline yet.
