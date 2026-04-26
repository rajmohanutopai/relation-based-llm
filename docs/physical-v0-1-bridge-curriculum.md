# Physical V0.1 Bridge Curriculum

Status: generated and validated locally.

The first held-out run is summarized in:

```text
docs/physical-v0-1-heldout-comparison.md
```

Result: local train/dev fit improved, but held-out graph-transfer scoring still
failed.

## Reason

The first `physical_v0` comparison failed on held-out graph transfer:

```text
relation scaffolding fit train/dev best
held-out relation-family recall stayed near zero
anchor recall stayed zero
```

The model was not learning the bridge from ordinary physical language to the
project graph vocabulary. `physical_v0_1` adds that bridge without changing the
model architecture.

## Boundary

The held-out physical prompts remain outside training.

Bridge examples are generated from:

```text
seed graph node labels and summaries
seed graph relation anchors
seed graph evaluation questions
seed graph micro-experiences
```

They are not generated from:

```text
data/developmental_graph/experiments/physical_v0_1/heldout.json
data/developmental_graph/experiments/physical_v0_1/heldout_prompts.jsonl
```

## New Bridge Tasks

```text
node_id_from_paraphrase
relation_family_from_prompt
graph_anchor_from_prompt
explanation_with_relations
```

The intent is to teach four missing bindings:

```text
description -> graph node
natural situation -> relation family IDs
natural situation -> graph anchors
answer -> answer plus explicit relation families
```

## Generated Data

Combined curriculum:

```text
data/developmental_graph/curricula/seed_everyday_physical_world_physical_v0_1_curriculum.jsonl
```

Counts:

```text
base examples:   148
bridge examples: 464
total examples:  612
```

Bridge count by task:

```text
node_id_from_paraphrase:     298
graph_anchor_from_prompt:    128
relation_family_from_prompt:  24
explanation_with_relations:   14
```

Experiment split:

```text
train:           488
dev:              58
curriculum_test:  66
held-out:         33
```

## Dataset Variants

The three-way comparison remains:

```text
plain_text
flat_triples
relation_scaffolded
```

Plain text uses human-readable labels. Flat triples uses source/type/target
IDs. Relation-scaffolded uses compact JSON targets.

## Commands

Generate combined bridge curriculum:

```bash
python3 scripts/generate_developmental_bridge_curriculum.py \
  data/developmental_graph/seeds/everyday_physical_world.json \
  --base-curriculum data/developmental_graph/curricula/seed_everyday_physical_world_curriculum.jsonl \
  --output data/developmental_graph/curricula/seed_everyday_physical_world_physical_v0_1_curriculum.jsonl
```

Validate:

```bash
python3 scripts/validate_developmental_curriculum.py \
  data/developmental_graph/curricula/seed_everyday_physical_world_physical_v0_1_curriculum.jsonl \
  --stats
```

Create splits:

```bash
python3 scripts/create_developmental_experiment_splits.py \
  data/developmental_graph/curricula/seed_everyday_physical_world_physical_v0_1_curriculum.jsonl \
  --heldout data/developmental_graph/evaluations/everyday_physical_world_heldout.json \
  --experiment-id physical_v0_1 \
  --output-dir data/developmental_graph/experiments/physical_v0_1
```

Create matched dataset variants:

```bash
python3 scripts/create_developmental_dataset_variants.py \
  data/developmental_graph/experiments/physical_v0_1 \
  --overwrite
```

Train:

```bash
python3 scripts/train_tiny_causal_lm.py \
  --config data/developmental_graph/experiments/physical_v0_1/training_config.json \
  --variant relation_scaffolded
```

## Decision Test

The bridge is useful only if `physical_v0_1` improves held-out graph transfer:

```text
relation family recall should rise materially
anchor recall should become non-zero
relation_scaffolded should beat or clearly differ from the baselines
```

Actual result:

```text
relation-scaffolded fit dev best, but held-out relation recall and anchor recall
did not improve.
```
