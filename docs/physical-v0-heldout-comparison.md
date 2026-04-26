# Physical V0 Held-Out Comparison

Status: completed locally. This is the first real comparison run, and it should
be treated as a useful failure report.

## Setup

All three runs used the same baseline:

```text
model: HuggingFaceTB/SmolLM2-135M
training examples: 118
dev examples: 14
held-out cases: 33
epochs: 10
learning rate: 5e-5
batch size: 1
gradient accumulation: 8
```

Only the dataset representation changed:

```text
plain_text
flat_triples
relation_scaffolded
```

## Commands

Generate held-out outputs:

```bash
python3 scripts/generate_heldout_outputs.py \
  --config data/developmental_graph/experiments/physical_v0/training_config.json \
  --variant plain_text \
  --model-dir runs/physical_v0/smollm2_135m/plain_text/final \
  --prompts data/developmental_graph/experiments/physical_v0/heldout_prompts.jsonl \
  --output runs/physical_v0/smollm2_135m/plain_text/heldout_outputs.jsonl
```

Repeat with `flat_triples` and `relation_scaffolded`.

Score held-out outputs:

```bash
python3 scripts/run_heldout_evaluation.py \
  data/developmental_graph/experiments/physical_v0/heldout.json \
  runs/physical_v0/smollm2_135m/plain_text/heldout_outputs.jsonl \
  --output runs/physical_v0/smollm2_135m/plain_text/heldout_scores.json
```

Repeat with `flat_triples` and `relation_scaffolded`.

## Training Loss

```text
variant                first train loss  final train loss  first dev loss  final dev loss
plain_text             5.126             3.090             5.588           3.667
flat_triples           4.211             2.102             3.864           2.282
relation_scaffolded    2.467             0.917             2.109           0.808
```

The relation-scaffolded format fits the small train/dev split much more easily.
That is not enough by itself; the held-out probes measure transfer.

## Held-Out Scores

```text
variant                case pass rate  relation family recall  anchor recall  gap recall
plain_text             0.000           0.011                   0.000          0.053
flat_triples           0.000           0.000                   0.000          0.053
relation_scaffolded    0.000           0.011                   0.000          0.053
```

No variant passed any held-out case under the current evaluator thresholds.

## What The Outputs Show

The models generated non-empty answers for all 33 held-out prompts. The issue is
not blank output.

Examples:

```text
plain_text:
The metal spoon will make the sharper sound because the metal is harder than the wood.

flat_triples:
The metal spoon will make the sharper sound because the metal is harder than the wood...

relation_scaffolded:
The metal spoon will make the sharper sound.
```

These answers contain some ordinary pretrained physics knowledge, but they do
not reliably recover the project graph vocabulary:

```text
schema.material_impact_outcome
schema.impact_force_sound_amplitude
property.metallic_resonance
```

The evaluator therefore sees almost no relation-family or anchor recall.

## Interpretation

This is a real failure of the first experiment design:

```text
relation scaffolding improved local train/dev fit
relation scaffolding did not yet improve held-out graph transfer
```

Likely causes:

1. The training set is too small for the model to learn both task behavior and
   graph vocabulary transfer.
2. The held-out prompts are natural language, while two variants were trained on
   specialized input formats.
3. The relation-scaffolded targets teach local JSON output patterns, but not
   enough prompt-to-graph retrieval.
4. The evaluator requires explicit graph-family and anchor recovery, while the
   model often answers in ordinary language.

## Decision

Do not expand domains yet.

The next step should revise the physical-v0 training/evaluation bridge before
adding social, math, geography, history, or medical domains.

## Next Experiment

Create a `physical_v0.1` bridge curriculum:

```text
natural prompt -> relation family IDs
natural prompt -> graph anchors
natural prompt -> short explanation with explicit relation names
object/property/situation paraphrase -> graph node IDs
```

Then rerun the same three-way comparison.

Success criterion:

```text
relation_scaffolded should beat both baselines on relation-family recall or
anchor recall before the project moves to the next domain.
```
