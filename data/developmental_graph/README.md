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
