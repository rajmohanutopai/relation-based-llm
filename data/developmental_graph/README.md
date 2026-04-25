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
```

## Validate

```bash
python3 scripts/validate_developmental_graph.py \
  data/developmental_graph/seeds/agent_6mo_indian_child.json \
  --stats
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
