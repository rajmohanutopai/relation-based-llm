# nanochat V5 Consistent QA 5K Local Run

Date: 2026-04-29

## Purpose

Test whether the relation-scaffolded V5 curriculum helps when the model sees
much fewer distinct training examples.

This run uses the same model shape and the same held-out test set as the 22K
V5 run, but only 5,000 matched train records per variant.

## Important Caveat

This is a data-efficiency test, not yet a compute-efficiency test.

Both 5K models were still trained for 1,000 nanochat iterations:

```text
training tokens per arm: 2048000
```

So the 5K models saw fewer distinct records, but repeated those records for
more epochs. The next test should reduce the token budget too.

## Dataset

Source:

```text
data/developmental_graph/experiments/procedural_foundation_v5_consistent_qa_5k/
```

Selection:

```text
5000 matched train records per variant
matched by source_example_id + prompt_type
seed: 1729
dev set: full V5 dev, 2765 records
test set: full V5 curriculum_test, 3115 records
```

Validation:

```text
ambiguous prompt inputs: 0
shorthand protocol hits: 0
```

The run reused the full V5 tokenizer so the model size stayed fixed. That
isolates training-record count from tokenizer/model-size changes.

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

Training loss proxy:

| Dataset | Model | Validation BPB |
| --- | --- | ---: |
| 22K | word_plain_qa | 0.137033 |
| 22K | word_relation_scaffolded_qa | 0.040710 |
| 5K | word_plain_qa | 0.195234 |
| 5K | word_relation_scaffolded_qa | 0.043949 |

The relation-scaffolded validation BPB remains much lower, but held-out QA is
the real comparison.

## Evaluation

Held-out prompts:

```text
data/developmental_graph/experiments/procedural_foundation_v5_consistent_qa_5k/datasets/word_plain_qa/curriculum_test.jsonl
```

Full 5K result on 3,115 held-out prompts:

| Model | Answer Exact | Reason Exact |
| --- | ---: | ---: |
| word_plain_qa | 86.1% (2682/3115) | 82.7% (2575/3115) |
| word_relation_scaffolded_qa | 86.8% (2703/3115) | 83.3% (2595/3115) |

Comparison with the 22K run:

| Train Records | Model | Answer Exact | Reason Exact |
| ---: | --- | ---: | ---: |
| 22680 | word_plain_qa | 86.4% | 84.8% |
| 22680 | word_relation_scaffolded_qa | 86.1% | 83.7% |
| 5000 | word_plain_qa | 86.1% | 82.7% |
| 5000 | word_relation_scaffolded_qa | 86.8% | 83.3% |

Run output:

```text
runs/nanochat_v5_consistent_qa_5k_20260429/evaluation/full_plain_prompts_d4_i1000/
```

## Interpretation

The 5K result supports the current hypothesis weakly but usefully:

```text
With fewer distinct training records, relation-scaffolded QA slightly beats
plain QA on held-out answer and reason exact match.
```

The effect is small:

```text
answer exact: +0.67 percentage points for relation scaffolded
reason exact: +0.64 percentage points for relation scaffolded
```

The stronger finding is that 5K records are almost enough for this tiny world
when the vocabulary and syntax are controlled. The plain 5K model nearly
matches the 22K plain model on answer accuracy, though its reason accuracy
drops more.

The relation scaffold helps some task families:

```text
more_less_count: 48.1% -> 58.9% answer exact
give_take: 90.0% -> 100.0%
hide_see: 91.1% -> 96.7%
reach_touch: 98.0% -> 99.6%
```

It hurts others:

```text
word_name_binding: 65.5% -> 45.5%
body_control: 76.0% -> 58.0%
social_signal_response: 25.0% -> 20.0%
same_different_match: 56.7% -> 52.6%
```

So relation scaffolding is not universally better in this output form. It may
help procedural relation tasks more than naming, social, and body-control
tasks.

## Next Test

The next test should use the same 5K dataset but reduce training tokens:

```text
250 iterations: 512000 tokens
500 iterations: 1024000 tokens
1000 iterations: 2048000 tokens
```

That will tell us whether relation scaffolding improves learning speed, not
just data efficiency after repeated exposure.

After that, run a smaller model:

```text
depth 2, embedding 128, heads 4
```

That would test whether relation scaffolding preserves accuracy under lower
parameter count.

## 250-Iteration Follow-Up

The first reduced-token run used the same 5K dataset and same model, but only
250 iterations:

```text
training tokens per arm: 512000
```

Result on the same 3,115 held-out prompts:

| Iterations | Model | Answer Exact | Reason Exact |
| ---: | --- | ---: | ---: |
| 250 | word_plain_qa | 82.2% (2561/3115) | 70.7% (2201/3115) |
| 250 | word_relation_scaffolded_qa | 74.5% (2322/3115) | 55.8% (1738/3115) |
| 1000 | word_plain_qa | 86.1% (2682/3115) | 82.7% (2575/3115) |
| 1000 | word_relation_scaffolded_qa | 86.8% (2703/3115) | 83.3% (2595/3115) |

Training loss proxy:

| Iterations | Model | Validation BPB |
| ---: | --- | ---: |
| 250 | word_plain_qa | 0.188111 |
| 250 | word_relation_scaffolded_qa | 0.137097 |
| 1000 | word_plain_qa | 0.195234 |
| 1000 | word_relation_scaffolded_qa | 0.043949 |

Interpretation:

```text
At 250 iterations, output-scaffolded relations do not improve learning speed.
They are much worse than plain QA on held-out answer and reason exact match,
despite having lower validation BPB.
```

This is important: validation BPB is not measuring the thing we care about
because the relation-scaffolded model can reduce BPB by learning repeated
relation text. Held-out answer/reason accuracy is the better signal.

Task-family pattern at 250 iterations:

```text
relation slightly better:
reach_touch: 91.2% -> 93.2%
more_less_count: 50.0% -> 50.6%

relation much worse:
wet_dry: 100.0% -> 0.0%
hide_see: 80.0% -> 33.3%
path_open_closed: 98.0% -> 63.0%
give_take: 80.0% -> 50.0%
push_pull_move: 99.2% -> 75.8%
word_name_binding: 60.0% -> 45.5%
```

Updated conclusion:

```text
Output-scaffolded relations may help after enough repeated exposure, but they
do not help early learning. The next relation design should not require the
model to emit relation scaffolds at answer time.
```

Better next experiment:

```text
5K relation-as-input, answer-only output, at 250/500/1000 iterations.
```

## Relation-As-Input 250-Iteration Follow-Up

This run tested the next design: use relation facts as input, but do not make
the model emit relation scaffolds.

Dataset variant:

```text
word_relation_input_qa
```

Policy:

```text
input: known relation / blocked relation lines + ordinary prompt
target: answer line + reason line only
```

Counts:

```text
train: 5000
dev: 2765
test: 3115
average relation input lines: about 8
ambiguous inputs: 0
shorthand protocol hits: 0
```

Sequence-length check:

```text
plain prompt+target max length: 53 tokens
relation-input prompt+target max length: 149 tokens
context length: 256
```

So the relation-input run was not failing because of context truncation.

Result at 250 iterations:

| Variant | Output Style | Answer Exact | Reason Exact |
| --- | --- | ---: | ---: |
| word_plain_qa | answer/reason only | 82.2% | 70.7% |
| word_relation_scaffolded_qa | answer/reason + emitted relations | 74.5% | 55.8% |
| word_relation_input_qa | relation input + answer/reason only | 81.9% | 59.9% |

Interpretation:

```text
Relation-as-input removes most of the answer-accuracy damage from output
scaffolding, but it still does not beat plain QA at 250 iterations.
```

The main weakness is reason exact match. The model often gets the answer
roughly right, but does not consistently select the exact relation that should
become the reason.

Updated conclusion:

```text
All-relations-as-input is better than emitting relations, but still too noisy.
The next variant should provide only candidate relation anchors relevant to the
question, not every relation attached to the scene.
```

Better next experiment:

```text
5K relation-candidate-input QA:
- input includes 3-5 candidate relation lines
- one candidate is the correct answer/reason anchor
- target remains answer/reason only
- run at 250 iterations
```
