# Physical V0.1 Held-Out Comparison

Status: completed locally. This is the second controlled failure report.

## Setup

`physical_v0_1` keeps the same baseline as `physical_v0`:

```text
model: HuggingFaceTB/SmolLM2-135M
variants: plain_text, flat_triples, relation_scaffolded
train examples: 488
dev examples: 58
curriculum-test examples: 66
held-out cases: 33
```

The only data change is the bridge curriculum:

```text
description -> graph node
natural situation -> relation family IDs
natural situation -> graph anchors
answer -> answer plus explicit relation families
```

Held-out prompts were not used for bridge training.

## Prompt Style

Raw held-out prompts did not reliably trigger graph recovery in the
relation-scaffolded model. The scored run therefore used the shared bridge-style
held-out wrapper:

```text
Which relation family IDs are needed for this physical situation?
QUESTION: <held-out prompt>
RELATION_FAMILY_IDS:
```

This prompt style is recorded in the generated output rows as:

```text
prompt_style: relation_families
```

## Training Loss

```text
variant                first train loss  final train loss  first dev loss  final dev loss
plain_text             4.409             1.433             2.609           1.816
flat_triples           3.832             0.963             2.078           1.101
relation_scaffolded    2.673             0.477             1.263           0.491
```

The bridge curriculum strongly improved local fit, especially for the
relation-scaffolded format.

## Held-Out Scores

```text
variant                case pass rate  relation family recall  anchor recall  gap recall
plain_text             0.000           0.011                   0.000          0.053
flat_triples           0.000           0.022                   0.000          0.000
relation_scaffolded    0.000           0.000                   0.000          0.000
```

No variant passed any held-out case. Anchor recall stayed zero.

## Output Pattern

Plain text stayed semantically broad:

```text
slip, fall, wet
metal spoon-wood spoon
hard-soft collision
```

Flat triples learned ID-like syntax, but invented IDs:

```text
schema.slip_fall_slip_slip...
schema.sound_sharp_ring_sound...
schema.elastic_compression_failure...
```

Relation-scaffolded learned JSON-like shape, but not graph-grounded IDs:

```text
{"kind":"property_relation","objectid":"object.slip_fall", ...}
{"kind":"relation_family","relation_family_ids":["schema","object","property", ...]}
```

## Interpretation

This result is important:

```text
The bridge curriculum improved local fit.
It did not teach reliable open-ended graph ID retrieval.
```

The failure is not that the model cannot produce structured text. It can. The
failure is that free-form generation lets the model invent plausible-looking
relation IDs instead of selecting from the fixed graph vocabulary.

## Decision

Do not expand domains yet.

Do not just add more broad bridge examples yet. The next experiment should make
the graph vocabulary closed and force selection from candidates.

## Next Experiment

Create `physical_v0_2` as a closed-vocabulary selection experiment:

```text
held-out prompt + candidate relation family IDs -> selected relation family IDs
held-out prompt + candidate graph anchors -> selected graph anchors
node paraphrase + candidate node IDs -> selected node ID
```

Each training example should include hard negatives from the same layer or
nearby relation family:

```text
correct: schema.material_impact_outcome
negative: schema.surface_friction_motion
negative: schema.elastic_stretch_return
negative: schema.object_stack_stability
```

This tests whether the model can recognize the right relation when the valid
graph vocabulary is present, instead of asking it to generate exact IDs from
memory.
