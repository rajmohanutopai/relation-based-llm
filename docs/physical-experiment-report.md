# Physical Experiment Report

Status: current through `physical_v0_1`.

This report records the first two physical-world experiment loops so the project
has one place to see what was tried, what happened, and why the next step
changed.

For the concise running experiment list, see:

```text
docs/experiment-log.md
```

## Experiment Timeline

### Physical V0

Goal:

```text
Test whether relation-scaffolded curriculum beats plain text and flat triples
on held-out physical graph transfer.
```

Setup:

```text
model: HuggingFaceTB/SmolLM2-135M
train/dev/curriculum-test: 118 / 14 / 16
held-out cases: 33
variants: plain_text, flat_triples, relation_scaffolded
```

Result:

```text
variant                final dev loss  case pass  relation recall  anchor recall
plain_text             3.667           0.000      0.011            0.000
flat_triples           2.282           0.000      0.000            0.000
relation_scaffolded    0.808           0.000      0.011            0.000
```

Conclusion:

```text
Relation scaffolding improved train/dev fit but did not transfer to held-out
graph recovery.
```

Decision:

```text
Do not expand domains. Add bridge examples that connect natural physical
language to graph node IDs, relation family IDs, and graph anchors.
```

Detailed report:

```text
docs/physical-v0-heldout-comparison.md
```

### Physical V0.1

Goal:

```text
Add bridge curriculum while keeping the same model and held-out evaluation.
```

New bridge tasks:

```text
node_id_from_paraphrase
relation_family_from_prompt
graph_anchor_from_prompt
explanation_with_relations
```

Setup:

```text
model: HuggingFaceTB/SmolLM2-135M
train/dev/curriculum-test: 488 / 58 / 66
held-out cases: 33
variants: plain_text, flat_triples, relation_scaffolded
```

Training result:

```text
variant                final dev loss
plain_text             1.816
flat_triples           1.101
relation_scaffolded    0.491
```

Held-out result:

```text
variant                case pass  relation recall  anchor recall
plain_text             0.000      0.011            0.000
flat_triples           0.000      0.022            0.000
relation_scaffolded    0.000      0.000            0.000
```

Output pattern:

```text
plain_text: broad semantic phrases, not graph IDs
flat_triples: plausible but invented schema IDs
relation_scaffolded: JSON-like objects with invented IDs
```

Conclusion:

```text
The bridge curriculum improved local fitting, but free-form generation still
does not reliably recover fixed graph vocabulary.
```

Decision:

```text
Do not expand domains. Do not just add more free-form bridge examples.
Move to closed-vocabulary candidate selection.
```

Detailed reports:

```text
docs/physical-v0-1-bridge-curriculum.md
docs/physical-v0-1-heldout-comparison.md
```

## Current Next Step

Create `physical_v0_2`:

```text
held-out-like prompt + candidate relation family IDs -> selected relation IDs
held-out-like prompt + candidate graph anchors -> selected graph anchors
node paraphrase + candidate node IDs -> selected node ID
```

Each example should include hard negatives from nearby graph areas:

```text
correct: schema.material_impact_outcome
negative: schema.surface_friction_motion
negative: schema.elastic_stretch_return
negative: schema.object_stack_stability
```

Reason:

```text
The model should select from the known graph vocabulary before being asked to
generate graph IDs freely.
```
