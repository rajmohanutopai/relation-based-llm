# Physical V0 Training

This document freezes the first tiny transformer baseline and command shape.
It does not claim model quality; it exists so the three dataset variants can be
compared with the same model and hyperparameters.

## Baseline

```text
Model: HuggingFaceTB/SmolLM2-135M
Task: causal language-model supervised fine-tuning
Variants: plain_text, flat_triples, relation_scaffolded
```

Reason for this baseline:

```text
small enough for local experiment plumbing
real pretrained causal transformer
same architecture and hyperparameters across all variants
```

The debug/sanity objective is modest: verify that the pipeline can train,
overfit a few examples, generate answers, and feed the held-out evaluator.

## Install Training Dependencies

The validators and generators do not need these packages. Training does.

```bash
python3 -m pip install -r requirements-training.txt
```

## Dry Run

Dry run validates the config and prints a formatted training sample without
loading PyTorch or the model.

```bash
python3 scripts/train_tiny_causal_lm.py \
  --config data/developmental_graph/experiments/physical_v0/training_config.json \
  --variant relation_scaffolded \
  --dry-run
```

## Frozen Commands

Plain text:

```bash
python3 scripts/train_tiny_causal_lm.py \
  --config data/developmental_graph/experiments/physical_v0/training_config.json \
  --variant plain_text
```

Flat triples:

```bash
python3 scripts/train_tiny_causal_lm.py \
  --config data/developmental_graph/experiments/physical_v0/training_config.json \
  --variant flat_triples
```

Relation-scaffolded:

```bash
python3 scripts/train_tiny_causal_lm.py \
  --config data/developmental_graph/experiments/physical_v0/training_config.json \
  --variant relation_scaffolded
```

## Overfit Sanity Check

Before full comparison, run one tiny overfit check:

```bash
python3 scripts/train_tiny_causal_lm.py \
  --config data/developmental_graph/experiments/physical_v0/training_config.json \
  --variant relation_scaffolded \
  --overfit-limit 8 \
  --max-steps 30 \
  --output-dir runs/physical_v0/overfit_relation_scaffolded
```

Expected result:

```text
training runs without data-format errors
loss decreases on the tiny repeated set
model artifacts are written under runs/
```

The first completed local sanity run is summarized in:

```text
docs/physical-v0-overfit-sanity.md
```

## Main Comparison Boundary

For the first comparison, change only `--variant`.

Do not change:

```text
model
epochs
learning rate
batch size
gradient accumulation
prompt template
train/dev/curriculum-test split membership
```

This keeps the comparison focused on representation:

```text
plain language vs flat triples vs relation-scaffolded structure
```
