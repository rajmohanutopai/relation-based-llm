# Experiment Log

This is the running chronological log for experiments. New entries go at the
top so the latest result is always visible first.

## 2026-04-26: Physical V0.2 Closed-Vocabulary Candidate Selection

Experiment ID:

```text
physical_v0_2
```

Purpose:

```text
Test whether held-out graph transfer improves when the valid relation IDs and
graph anchors are shown as candidates instead of generated from memory.
```

Data:

```text
train: 1041
dev: 123
curriculum_test: 142
held-out: 33
```

Model/run:

```text
model: HuggingFaceTB/SmolLM2-135M
run: candidate_selection_options_outputmarker_512_s160
max_seq_length: 512
max_steps: 160
```

Training result:

```text
train loss: 0.610
dev loss:   0.337
```

Held-out result:

```text
case pass:          0.000
family precision:   0.247
family recall:      0.407
anchor precision:   0.168
anchor recall:      0.596
gap precision:      0.200
gap recall:         0.026
non-candidate IDs:  0
```

Interpretation:

```text
The closed-vocabulary setup solved the invented-ID problem, but not exact
selection. The model often over-selected candidates, especially all anchor
options, so recall improved while precision stayed poor and exact case pass
remained zero.
```

Decision:

```text
The direction is useful, but the next run should make selection less generative:
separate relation-family and anchor prompts, include expected count or binary
yes/no candidate scoring, and train/evaluate a full stable run only after the
selection head stops over-selecting.
```

Detailed report:

```text
docs/physical-v0-2-candidate-selection.md
```

## 2026-04-26: Physical V0.1 Held-Out Comparison

Experiment ID:

```text
physical_v0_1
```

Purpose:

```text
Test whether adding bridge tasks improves held-out graph-transfer performance.
```

Change from previous experiment:

```text
Added bridge tasks:
- node_id_from_paraphrase
- relation_family_from_prompt
- graph_anchor_from_prompt
- explanation_with_relations
```

Model:

```text
HuggingFaceTB/SmolLM2-135M
```

Data:

```text
train: 488
dev: 58
curriculum_test: 66
held-out: 33
```

Result:

```text
variant                final dev loss  heldout pass  relation recall  anchor recall
plain_text             1.816           0.000         0.011            0.000
flat_triples           1.101           0.000         0.022            0.000
relation_scaffolded    0.491           0.000         0.000            0.000
```

Interpretation:

```text
The bridge curriculum improved local fit, but held-out graph transfer still
failed. The model produced plausible labels, invented schema IDs, or JSON-like
objects instead of recovering fixed graph vocabulary.
```

Decision:

```text
Do not expand domains.
Move to closed-vocabulary candidate selection in physical_v0_2.
```

Detailed report:

```text
docs/physical-v0-1-heldout-comparison.md
```

## 2026-04-26: Physical V0.1 Bridge Curriculum Generation

Experiment ID:

```text
physical_v0_1
```

Purpose:

```text
Create a bridge curriculum after physical_v0 showed that relation scaffolding
fit train/dev but did not transfer to held-out graph recovery.
```

Generated tasks:

```text
node_id_from_paraphrase:     298
graph_anchor_from_prompt:    128
relation_family_from_prompt:  24
explanation_with_relations:   14
```

Data:

```text
base examples:   148
bridge examples: 464
total examples:  612
```

Validation:

```text
OK: data/developmental_graph/curricula/seed_everyday_physical_world_physical_v0_1_curriculum.jsonl
```

Decision:

```text
Train the same three variants as physical_v0 and rerun held-out scoring.
```

Detailed report:

```text
docs/physical-v0-1-bridge-curriculum.md
```

## 2026-04-26: Physical V0 Held-Out Comparison

Experiment ID:

```text
physical_v0
```

Purpose:

```text
Test the first complete physical-world vertical slice.
```

Model:

```text
HuggingFaceTB/SmolLM2-135M
```

Data:

```text
train: 118
dev: 14
curriculum_test: 16
held-out: 33
```

Result:

```text
variant                final dev loss  heldout pass  relation recall  anchor recall
plain_text             3.667           0.000         0.011            0.000
flat_triples           2.282           0.000         0.000            0.000
relation_scaffolded    0.808           0.000         0.011            0.000
```

Interpretation:

```text
Relation scaffolding fit train/dev best, but did not improve held-out graph
transfer.
```

Decision:

```text
Do not expand domains.
Add bridge curriculum to connect natural prompts to graph relation vocabulary.
```

Detailed report:

```text
docs/physical-v0-heldout-comparison.md
```

## 2026-04-26: Physical V0 Overfit Sanity Check

Experiment ID:

```text
physical_v0_overfit_relation_scaffolded
```

Purpose:

```text
Verify that the local training pipeline, dependencies, data formatting,
checkpointing, and generation path work.
```

Setup:

```text
variant: relation_scaffolded
overfit_limit: 8
max_steps: 30
```

Result:

```text
train loss step 5:  1.712
train loss step 30: 1.007
eval loss step 1:   1.864
eval loss step 30:  1.048
```

Interpretation:

```text
Infrastructure sanity passed. This was not a model-quality result.
```

Decision:

```text
Proceed to full physical_v0 three-way comparison.
```

Detailed report:

```text
docs/physical-v0-overfit-sanity.md
```
