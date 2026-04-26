# Developmental Relation Graph Data

This directory contains the machine-parseable version of the developmental
relation graph.

## Files

```text
schemas/graph.schema.json
  JSON Schema for the graph file format.

seeds/agent_6mo_indian_child.json
  First concrete seed graph for a 6-month-old child in an Indian household
  context.

seeds/everyday_physical_world.json
  External-world physical relation scaffold built from the first everyday
  physical-world audit.

evaluations/everyday_physical_world_heldout.json
  Held-out physical-world evaluation cases built from `maybe` rows in the
  everyday physical inventory.

curricula/seed_everyday_physical_world_curriculum.jsonl
  Generated supervised curriculum examples from the physical-world seed graph.

curricula/seed_everyday_physical_world_curriculum.manifest.json
  Counts and source metadata for the generated physical-world curriculum.

experiments/physical_v0/
  Deterministic model-ready split for the first physical-world experiment.
  Contains train/dev/curriculum-test JSONL, held-out evaluation copy,
  held-out prompts, and a manifest.

experiments/physical_v0/datasets/
  Matched training dataset variants from the same split: plain text, flat
  triples, and relation-scaffolded examples.

experiments/physical_v0/training_config.json
  Frozen tiny-transformer baseline config and training commands for the first
  physical-world comparison.
```

## Validate

```bash
python3 scripts/validate_developmental_graph.py \
  data/developmental_graph/seeds/agent_6mo_indian_child.json \
  --stats

python3 scripts/validate_developmental_graph.py \
  data/developmental_graph/seeds/everyday_physical_world.json \
  --stats

python3 scripts/validate_developmental_evaluation.py \
  data/developmental_graph/evaluations/everyday_physical_world_heldout.json \
  --stats

python3 scripts/validate_developmental_curriculum.py \
  data/developmental_graph/curricula/seed_everyday_physical_world_curriculum.jsonl \
  --stats
```

## Generate Curriculum

```bash
python3 scripts/generate_developmental_curriculum.py \
  data/developmental_graph/seeds/everyday_physical_world.json
```

The generator writes JSONL examples to `curricula/` and a manifest beside it.
The first generator supports:

```text
relation_completion
state_action_effect
counterfactual_contrast
explanation_path
```

## Run Held-Out Evaluation

The first evaluation runner scores model-output JSONL against a held-out
evaluation file. Model outputs should contain at least `case_id` and `answer`.

```bash
python3 scripts/run_heldout_evaluation.py \
  data/developmental_graph/evaluations/everyday_physical_world_heldout.json \
  model_outputs.jsonl
```

For a smoke test of the scorer itself:

```bash
python3 scripts/run_heldout_evaluation.py \
  data/developmental_graph/evaluations/everyday_physical_world_heldout.json \
  --oracle
```

## Create Experiment Splits

```bash
python3 scripts/create_developmental_experiment_splits.py \
  data/developmental_graph/curricula/seed_everyday_physical_world_curriculum.jsonl \
  --heldout data/developmental_graph/evaluations/everyday_physical_world_heldout.json \
  --experiment-id physical_v0 \
  --overwrite
```

This writes:

```text
experiments/physical_v0/train.jsonl
experiments/physical_v0/dev.jsonl
experiments/physical_v0/curriculum_test.jsonl
experiments/physical_v0/heldout.json
experiments/physical_v0/heldout_prompts.jsonl
experiments/physical_v0/manifest.json
```

`curriculum_test.jsonl` is an in-curriculum test split. `heldout.json` and
`heldout_prompts.jsonl` are transfer evaluation artifacts and should not be
used for training.

## Create Dataset Variants

```bash
python3 scripts/create_developmental_dataset_variants.py \
  data/developmental_graph/experiments/physical_v0 \
  --overwrite
```

This writes matched variants:

```text
experiments/physical_v0/datasets/plain_text/
experiments/physical_v0/datasets/flat_triples/
experiments/physical_v0/datasets/relation_scaffolded/
experiments/physical_v0/datasets/manifest.json
```

Each variant keeps the same `source_example_id`, `split`, and `task_type`.
Only the `input` and `target` representation changes.

## Core Format

The canonical graph format is JSON:

```json
{
  "layers": [],
  "nodes": [],
  "relations": [],
  "micro_experiences": [],
  "evaluation_questions": []
}
```

Every concept is a node. Every meaningful connection is a typed, weighted
relation. Micro-experiences are event records that strengthen or demonstrate
relations. Evaluation questions specify expected relation paths.

Markdown documents in `docs/` are explanatory. Code should consume the JSON
files in this directory.
