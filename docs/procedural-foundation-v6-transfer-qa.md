# Procedural Foundation V6 Transfer QA

Date: 2026-04-29

## Purpose

V6 is the next dataset after the V5 dense-vs-sparse result. V5 showed that the
tiny model succeeds when ordinary text contains the needed relations and fails
when those relation cues are removed.

V6 now tests the harder question:

```text
Did the model learn reusable relation rules, or did it mainly learn repeated
generator patterns?
```

## Design

V6 keeps the hidden V3 procedural relation world, but the model sees ordinary
QA text only. Relation lines are not rendered to the model.

Variants:

```text
ordinary_dense_qa    main arm; relation-dense ordinary scene text
ordinary_sparse_qa   sparse control; relation cues removed, target unchanged
ordinary_corrupt_qa  negative control; common relation cues flipped, target unchanged
```

Visible example:

```text
Scene: Cube is on table far from baby. Baby reaches hand.
Question: Does hand touch cube?
Answer:
answer: no.
reason: hand does not touch cube.
```

Hidden metadata still stores the procedural relations:

```text
hidden_positive_relations
hidden_negative_relations
counterfactual_group
evaluation_bucket
```

## Evaluation Buckets

Held-out tests are no longer one undifferentiated `curriculum_test`.

```text
test_observation      same distribution, new held-out examples
test_inference        relation consequence must be inferred from scene cues
test_transfer         held-out family/object combinations
test_counterfactual   paired true/false relation groups
```

`curriculum_test` is the union of those four buckets.

## Counts

Base unit splits:

```text
train: 3544
dev: 463
test_observation: 539
test_inference: 340
test_transfer: 476
test_counterfactual: 350
```

Rendered records per variant, with five prompt surfaces per unit:

```text
train: 17720
dev: 2315
test_observation: 2695
test_inference: 1700
test_transfer: 2380
test_counterfactual: 1750
curriculum_test: 8525
```

Transfer and counterfactual structure:

```text
held-out family/object transfer keys: 72
counterfactual groups selected: 146
counterfactual groups with both true and false cases: 146
```

Vocabulary, dense main arm:

```text
train unique alpha words: 305
curriculum_test unique alpha words: 260
shorthand protocol hits: 0
```

Prompt conflict check, dense main arm:

```text
train ambiguous inputs: 0 / 17720
curriculum_test ambiguous inputs: 0 / 8525
```

The sparse arm is expected to have ambiguous prompts because relation cues are
deliberately stripped. That is the control condition, not the main training
surface.

## Files

Generator:

```text
scripts/create_procedural_foundation_world_v6_transfer_qa.py
```

Dataset:

```text
data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/
```

Main training files:

```text
data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/datasets/ordinary_dense_qa/train.jsonl
data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/datasets/ordinary_dense_qa/dev.jsonl
```

Main evaluation files:

```text
data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/datasets/ordinary_dense_qa/test_observation.jsonl
data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/datasets/ordinary_dense_qa/test_inference.jsonl
data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/datasets/ordinary_dense_qa/test_transfer.jsonl
data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/datasets/ordinary_dense_qa/test_counterfactual.jsonl
data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/datasets/ordinary_dense_qa/curriculum_test.jsonl
```

## Validation

Commands run:

```text
python -m py_compile scripts/create_procedural_foundation_world_v6_transfer_qa.py
python -m py_compile scripts/run_nanochat_word_surface_eval.py
python scripts/create_procedural_foundation_world_v6_transfer_qa.py --overwrite --shuffle-train-prompts
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/manifest.json
python -m json.tool data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/datasets/manifest.json
```

Additional checks:

```text
ordinary_dense_qa train ambiguous inputs: 0
ordinary_dense_qa curriculum_test ambiguous inputs: 0
visible relation tag leaks: 0
counterfactual groups with both polarities: 146 / 146
```

## nanochat Training Run

Three nanochat models were trained from scratch with the same tiny architecture
and tokenizer:

```text
model variants: ordinary_dense_qa, ordinary_sparse_qa, ordinary_corrupt_qa
parameters: 4325506
layers: 4
embedding width: 256
context length: 256
tokenizer vocab: 1146
train records per variant: 17720
dev records per variant: 2315
iterations: 1000
training tokens per variant: 2048000
```

Training validation bpb:

```text
ordinary_dense_qa:   2.448177 -> 0.121423
ordinary_sparse_qa:  2.593039 -> 0.114275
ordinary_corrupt_qa: 2.446165 -> 0.118257
```

The sparse and corrupt controls achieve low validation bpb because they can
learn their own training surface. The real test is whether they answer the
dense held-out questions correctly.

## Held-out Evaluation

All three models were evaluated on:

```text
data/developmental_graph/experiments/procedural_foundation_v6_transfer_qa/datasets/ordinary_dense_qa/curriculum_test.jsonl
```

Overall results:

```text
ordinary_dense_qa:   91.7% answer exact, 90.3% reason exact
ordinary_sparse_qa:  53.1% answer exact, 43.4% reason exact
ordinary_corrupt_qa: 33.9% answer exact, 31.7% reason exact
```

By evaluation bucket:

| Model | Observation | Inference | Transfer | Counterfactual |
| --- | ---: | ---: | ---: | ---: |
| ordinary_dense_qa | 85.0% / 84.3% | 98.1% / 97.0% | 89.0% / 87.4% | 99.4% / 96.9% |
| ordinary_sparse_qa | 50.4% / 41.6% | 55.6% / 42.9% | 55.3% / 48.0% | 51.9% / 40.5% |
| ordinary_corrupt_qa | 34.8% / 30.5% | 48.5% / 46.6% | 34.1% / 33.1% | 18.1% / 17.3% |

Each cell is `answer exact / reason exact`.

Evaluation output:

```text
runs/nanochat_v6_transfer_qa_20260429/evaluation/dense_curriculum_test_d4_i1000/summary.md
runs/nanochat_v6_transfer_qa_20260429/evaluation/dense_curriculum_test_d4_i1000/summary.json
```

## Interpretation

V6 is a stronger positive result than V5. The model trained on ordinary
relation-dense text performs well not only on held-out observations, but also
on inference, held-out transfer combinations, and paired counterfactual cases.

The sparse control fails even though it uses the same targets, model size,
tokenizer, training budget, and evaluation prompts. The corrupt control fails
more strongly, especially on counterfactuals. This supports the current
hypothesis: the gain is coming from relational information in ordinary text,
not from the answer format alone.

This does not yet prove general language understanding. It shows that, in this
controlled world, relation-dense ordinary language gives a tiny transformer a
large sample-efficiency advantage and produces reusable relation behavior.
