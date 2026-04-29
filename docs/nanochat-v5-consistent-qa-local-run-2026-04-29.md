# nanochat V5 Consistent QA Local Run

Date: 2026-04-29

## Purpose

Train a tiny nanochat model from scratch on the procedural foundation world
using proper word prompts, not shorthand labels. V5 replaces V4 for this run
because V4 had many identical prompts with different target formats. That
created conflicting next-token supervision for a small causal model.

## Dataset

Source:

```text
data/developmental_graph/experiments/procedural_foundation_v5_consistent_qa/
```

Counts per variant:

```text
train: 22680 records
dev: 2765 records
curriculum_test: 3115 records
base source units: 5712
train base units: 4536
dev base units: 553
test base units: 623
prompt phrasings per unit: 5
```

Validation:

```text
ambiguous prompt inputs: 0
shorthand protocol hits: 0
word_plain_qa train vocabulary: 305 unique alpha words
word_relation_scaffolded_qa train vocabulary: 337 unique alpha words
```

Variants trained:

```text
word_plain_qa
word_relation_scaffolded_qa
```

The relation-scaffolded variant appends full-word `known relation:` and
`blocked relation:` lines after the answer and reason.

## Model

nanochat from-scratch decoder-only model:

```text
layers: 4
embedding size: 256
attention heads: 4
context length: 256
vocabulary size: 1216
parameters: 4391042
training tokens per arm: 2048000
iterations per arm: 1000
device: MPS
```

Checkpoints:

```text
runs/nanochat_v5_consistent_qa_20260429/word_plain_qa/base_checkpoints/v5_word_plain_qa_d4_i1000/model_001000.pt
runs/nanochat_v5_consistent_qa_20260429/word_relation_scaffolded_qa/base_checkpoints/v5_word_relation_scaffolded_qa_d4_i1000/model_001000.pt
```

Training loss proxy:

```text
word_plain_qa: validation bpb 2.466605 -> 0.137033
word_relation_scaffolded_qa: validation bpb 2.289457 -> 0.040710
```

The lower validation BPB for the relation-scaffolded model mostly means it
learned the repeated relation text well. Held-out QA is the important comparison.

## Evaluation

Held-out prompts:

```text
data/developmental_graph/experiments/procedural_foundation_v5_consistent_qa/datasets/word_plain_qa/curriculum_test.jsonl
```

Evaluator:

```text
scripts/run_nanochat_word_surface_eval.py
```

Important evaluator detail:

```text
prompt_suffix: "\n\n"
```

This suffix matches the nanochat `input_target` pretraining shard format:
`input + blank line + target`. Without it, generation starts from a prefix the
model did not train on and scores are artificially lower.

Full result on 3115 held-out prompts:

| Model | Answer Exact | Reason Exact |
| --- | ---: | ---: |
| word_plain_qa | 86.4% (2691/3115) | 84.8% (2643/3115) |
| word_relation_scaffolded_qa | 86.1% (2683/3115) | 83.7% (2608/3115) |

By prompt type:

| Model | Prompt Type | Answer Exact | Reason Exact |
| --- | --- | ---: | ---: |
| word_plain_qa | scene_question_answer | 86.2% | 84.8% |
| word_plain_qa | natural_scene_question | 85.7% | 84.3% |
| word_plain_qa | direct_question | 86.2% | 84.8% |
| word_plain_qa | answer_and_reason_request | 86.5% | 84.9% |
| word_plain_qa | question_then_scene | 87.3% | 85.6% |
| word_relation_scaffolded_qa | scene_question_answer | 86.5% | 83.9% |
| word_relation_scaffolded_qa | natural_scene_question | 86.2% | 83.5% |
| word_relation_scaffolded_qa | direct_question | 86.7% | 84.6% |
| word_relation_scaffolded_qa | answer_and_reason_request | 85.4% | 82.7% |
| word_relation_scaffolded_qa | question_then_scene | 85.9% | 83.9% |

Run output:

```text
runs/nanochat_v5_consistent_qa_20260429/evaluation/full_plain_prompts_d4_i1000/
```

## Interpretation

The cleaned proper-word dataset worked: a 4.39M parameter model trained from
scratch reached about 86% exact answer accuracy and about 85% exact reason
accuracy on held-out procedural prompts.

This specific relation-scaffolded target design did not beat the plain QA arm.
It fit the training/validation text better, but that did not transfer into
better held-out answer/reason accuracy. The likely reason is that relation
lines in the output target make the model spend capacity learning to emit
scaffold text, not just to use relational structure internally.

The next relation experiment should move relation support away from answer-time
generation. Better candidates:

```text
1. relation-as-input: provide relation facts in the prompt during training and test.
2. hidden/auxiliary relation prediction: train relation heads or side objectives, but decode only the answer.
3. two-stage curriculum: first train relation completion, then train answer-only QA using the same base world.
```

The current result is still useful. It proves the procedural child-world data
is trainable by a very small transformer and gives a clean baseline for testing
whether relation structure improves sample efficiency.
