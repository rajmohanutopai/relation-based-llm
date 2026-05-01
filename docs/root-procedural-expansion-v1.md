# Root Procedural Expansion V1

Date: 2026-04-30

Experiment ID:

```text
root_procedural_expansion_v1
```

## Purpose

This is the larger procedural dataset after `root_concept_foundation_v1`.

The root foundation is a clean seed, but it is too small for serious training
by itself. This expansion turns the root relations into many ordinary-language
scenarios while keeping the root graph hidden in metadata.

The model sees normal QA text. It does not see relation tags.

## Design

Main arm:

```text
root_dense_qa
```

Controls:

```text
root_sparse_qa   removes discriminating cues while preserving targets
root_corrupt_qa  flips common cues while preserving targets
```

The dense arm is the real training candidate. The sparse and corrupt arms are
controls for checking whether relation-dense ordinary text is doing useful
work.

## Root Anchoring

Surface words attach to root anchors from `root_concept_foundation_v1`.

Examples:

```text
puppy -> young animal
dog -> animal
doll -> toy
banana -> food
knife -> needle/sharp object
mom -> caregiver
friend -> person/friend
```

The model-visible text remains ordinary:

```text
Scene: The child learns a new word for the blanket.
Question: How does the child feel?
Answer:
```

Target:

```text
answer: happy and excited.
reason: a new link can cause happy feeling.
```

Hidden metadata stores the root relations:

```text
learning.new_link causes emotion.happy
learning.new_link can_make emotion.excited
blanket attaches to object.blanket
```

## Scenario Families

Generated families:

```text
touch_distance
container_access
property_touch
move_weight
support_fall
living_need
social_effect
social_signal
language_name
happiness_mechanism
object_change
place_context
time_change
```

Examples:

```text
near/far -> touch/no touch
open/closed container -> can touch/blocked
hot/sharp/not safe -> pain
soft/safe -> no pain
push/pull + near/far/weight -> move/no move
hold/release -> no fall/fall
living thing -> food/water/sleep/air need
help/share/play -> comfort/happy
hurt/cry -> pain/sad
new link/strong link/broken link -> happy/excited/less excited/sad
find/lose/fix/clean -> happy/sad/good
```

## Counts

Source units:

```text
3276
```

Unit splits:

```text
train:               1926
dev:                  258
test_observation:     380
test_inference:        53
test_transfer:        375
test_counterfactual:  284
```

Rendered records per variant, with five prompt surfaces per unit:

```text
train:               9630
dev:                 1290
test_observation:    1900
test_inference:       265
test_transfer:       1875
test_counterfactual: 1420
curriculum_test:     5460
```

Dense vocabulary:

```text
train unique alpha words: 254
curriculum_test unique alpha words: 236
shorthand protocol hits: 0
```

Visible-text quality checks:

```text
bare "Question: Why?" prompts: 0
visible relation-label phrases like "open lets touch happen": 0
tautological movement/fall reasons: 0
```

## Validation

Commands run:

```text
python -m py_compile scripts/create_root_procedural_expansion_v1.py
python scripts/create_root_procedural_expansion_v1.py --overwrite --shuffle-train-prompts
```

Leakage checks:

```text
train/test source-id overlap: none
train/test counterfactual-group overlap: none
selected transfer-key train overlap: none
```

Prompt conflicts:

```text
root_dense_qa train ambiguous inputs: 0
root_sparse_qa train ambiguous inputs: expected by design
```

The sparse arm is deliberately ambiguous because the relation cues have been
removed while the targets are preserved.

## Local Nanochat Run

Run directory:

```text
runs/nanochat_root_procedural_v1_20260430/
```

Model:

```text
nanochat decoder-only transformer
depth: 4
heads: 4
embedding dim: 256
parameters: about 4.06M
context length: 256
tokenizer vocab: 881, padded to 896 at runtime
device: Apple MPS
```

Training:

```text
variants: root_dense_qa, root_sparse_qa, root_corrupt_qa
iterations per variant: 1000
training tokens per variant: 2048000
```

Training validation bpb:

```text
root_dense_qa:   final 0.129592, min 0.115348
root_sparse_qa:  final 0.132896, min 0.121064
root_corrupt_qa: final 0.131706, min 0.120557
```

Evaluation:

```text
dataset: data/developmental_graph/experiments/root_procedural_expansion_v1/datasets/root_dense_qa/curriculum_test.jsonl
examples: 5460
temperature: 0.0
max generated tokens: 48
summary: runs/nanochat_root_procedural_v1_20260430/evaluation/dense_curriculum_test_d4_i1000/summary.md
```

Overall exact-match results:

```text
root_dense_qa:   answer 94.5% (5162/5460), reason 94.2% (5144/5460)
root_sparse_qa:  answer 52.7% (2879/5460), reason 36.9% (2016/5460)
root_corrupt_qa: answer 45.3% (2474/5460), reason 44.5% (2431/5460)
```

Dense bucket results:

```text
test_observation:    answer 95.5%, reason 94.2%
test_inference:      answer 100.0%, reason 99.6%
test_transfer:       answer 92.7%, reason 93.2%
test_counterfactual: answer 94.6%, reason 94.6%
```

Interpretation:

```text
The dense arm learned the ordinary-language relation cues far better than the
sparse and corrupt controls. This supports continuing the relation-first
curriculum path.
```

Known weakness:

```text
language_name is weak even in the dense model: answer 51.1%, reason 51.1%.
Failures often flip whether a heard word names the looked-at object. The next
revision should strengthen naming data before TinyStories word attachment.
```

## Files

Generator:

```text
scripts/create_root_procedural_expansion_v1.py
```

Generated output:

```text
data/developmental_graph/experiments/root_procedural_expansion_v1/
```

Main train/dev files:

```text
data/developmental_graph/experiments/root_procedural_expansion_v1/datasets/root_dense_qa/train.jsonl
data/developmental_graph/experiments/root_procedural_expansion_v1/datasets/root_dense_qa/dev.jsonl
```

Main evaluation files:

```text
data/developmental_graph/experiments/root_procedural_expansion_v1/datasets/root_dense_qa/test_observation.jsonl
data/developmental_graph/experiments/root_procedural_expansion_v1/datasets/root_dense_qa/test_inference.jsonl
data/developmental_graph/experiments/root_procedural_expansion_v1/datasets/root_dense_qa/test_transfer.jsonl
data/developmental_graph/experiments/root_procedural_expansion_v1/datasets/root_dense_qa/test_counterfactual.jsonl
data/developmental_graph/experiments/root_procedural_expansion_v1/datasets/root_dense_qa/curriculum_test.jsonl
```

## Decision

The dense ordinary-language relation arm strongly beats the sparse and corrupt
controls on the same dense held-out curriculum, so the relation-first curriculum
path is worth continuing.

Before TinyStories word attachment, fix the weak `language_name` family. That
task should get clearer naming examples and more positive/negative coverage.

Then continue:

```text
root_concept_foundation_v1
-> root_procedural_expansion_v1
-> TinyStories word attachment
-> raw TinyStories
```
