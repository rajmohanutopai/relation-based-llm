# Curriculum Generation

The curriculum generator converts a validated relation graph into supervised
JSONL examples. It is deliberately deterministic: the graph is the source of
truth, and the script does not call an LLM or invent extra facts.

## Current Command

```bash
python3 scripts/generate_developmental_curriculum.py \
  data/developmental_graph/seeds/everyday_physical_world.json
```

Default outputs:

```text
data/developmental_graph/curricula/seed_everyday_physical_world_curriculum.jsonl
data/developmental_graph/curricula/seed_everyday_physical_world_curriculum.manifest.json
```

Current physical-world curriculum count:

```text
relation_completion: 114
state_action_effect: 10
counterfactual_contrast: 10
explanation_path: 14
total: 148
```

## Task Types

`relation_completion` asks the model to complete a typed edge from source node
and relation type to target node. This tests whether the model can learn the
graph's explicit relation inventory.

`state_action_effect` gives a short event trace from a micro-experience and asks
for the relation changes observed in that event. This is the first step from
static graph edges to learning through experience.

`counterfactual_contrast` asks what changes when a property, object, or physical
condition is swapped for its contrast. This is where relation strength and
property boundaries become testable.

`explanation_path` gives a question plus expected relation path and asks for a
natural-language answer. This links the graph to ordinary explanation while
keeping the relation chain visible.

## Design Rules

Raw encounter inventories stay separate from relation annotations.

The generator should expose relations already present in the graph. It should
not silently add adult abstractions, teacher-model guesses, or facts from
outside the seed.

The first experiment should compare a plain-text baseline against the same
small transformer trained with these relation-scaffolded examples.

Later generators can add paraphrases, difficulty levels, language-binding
examples, valence examples, and teacher-model expansion, but only after the
first controlled baseline exists.

## Physical V0 Split

The first experiment split is generated from the physical-world curriculum:

```bash
python3 scripts/create_developmental_experiment_splits.py \
  data/developmental_graph/curricula/seed_everyday_physical_world_curriculum.jsonl \
  --heldout data/developmental_graph/evaluations/everyday_physical_world_heldout.json \
  --experiment-id physical_v0 \
  --overwrite
```

Current split counts:

```text
train: 118
dev: 14
curriculum_test: 16
heldout_prompts: 33
```

The split is deterministic and stratified by task type. The held-out prompts
come from the separate evaluation file and remain outside training.

## Physical V0 Dataset Variants

The first matched dataset variants are generated from the `physical_v0` split:

```bash
python3 scripts/create_developmental_dataset_variants.py \
  data/developmental_graph/experiments/physical_v0 \
  --overwrite
```

Current variants:

```text
plain_text
flat_triples
relation_scaffolded
```

Each variant has the same split counts:

```text
train: 118
dev: 14
curriculum_test: 16
```

The variants differ only in representation:

```text
plain_text:
  ordinary language, no relation IDs

flat_triples:
  source --relation_type--> target triples

relation_scaffolded:
  scaffolded input plus structured JSON target
```

All records include `input`, `target`, and a two-message `messages` field for
later supervised fine-tuning scripts.
