# nanochat Core4 Held-Out Relation Evaluation

Date: 2026-04-29

This evaluates the depth-4 nanochat checkpoints on held-out procedural V3
questions. Unlike the BPB validation run, this asks each model to answer
generated relation questions it did not train on.

## Setup

```text
checkpoints: runs/nanochat_core4_20260429
script: scripts/run_nanochat_relation_eval.py
dataset: data/developmental_graph/experiments/procedural_foundation_v3/datasets/procedural_plain_text/curriculum_test.jsonl
examples: 623
prompt mode: same plain prompt for every model
max generated tokens: 32
temperature: 0.0
device: mps
```

The scoring parser is strict. If a model drifts into a new generated `q:` block
and answers that new question, that later answer is not counted.

## Command

```bash
/tmp/nanochat-read/.venv/bin/python scripts/run_nanochat_relation_eval.py \
  --models tinystories_plain_text procedural_plain_text procedural_relation_scaffolded procedural_relation_first_then_text \
  --progress-every 100
```

## Results

| Model | Answer exact | Fact exact |
| --- | ---: | ---: |
| tinystories_plain_text | 0.0% (0/623) | 0.0% (0/623) |
| procedural_plain_text | 74.6% (465/623) | 39.3% (245/623) |
| procedural_relation_scaffolded | 82.2% (512/623) | 73.4% (457/623) |
| procedural_relation_first_then_text | 50.7% (316/623) | 19.4% (121/623) |

Raw predictions and full task breakdown:

```text
runs/nanochat_core4_20260429/evaluation/procedural_v3_plain_prompt_d4_i500/
```

## Interpretation

This is the first positive signal for the data-side relation scaffold:

```text
relation_scaffolded beats procedural_plain_text on the same held-out plain prompts
answer exact: 82.2% vs 74.6%
fact exact:   73.4% vs 39.3%
```

The result is still limited:

```text
the train/dev/test examples come from the same procedural world generator
the task language is tiny and controlled
the model is only 7.34M parameters
the result does not yet prove transfer to normal language or broad commonsense
```

But it is stronger than the previous validation-BPB result because the model
had to generate answers for held-out cases using the same prompt surface across
all procedural arms.

## Notable Failure Pattern

The relation-first-then-text arm underperformed under plain prompts. This is
expected because it was trained to see relation hints before the natural
question, but the evaluation intentionally withheld those hints to keep the
prompt surface fair across models.

The TinyStories arm produced story continuations instead of structured answers.
This confirms it is a useful format/control baseline but not a relation-task
baseline unless it is also taught the answer protocol.

## Next Step

The next evaluation was the natural-input held-out test:

```text
docs/nanochat-core4-natural-heldout-evaluation-2026-04-29.md
```

That result showed the scaffolded model still wins under naturalized input, but
all models drop sharply. The next training run should therefore mix structured
prompts, natural prompts, natural Q&A, and short event-continuation text before
spending rented-GPU money.
