# nanochat Core4 Local Smoke

Date: 2026-04-29

This was a local pipeline smoke test, not a theory result. The goal was to
verify that the four-arm comparison can be converted, tokenized with one shared
tokenizer, trained from scratch in nanochat, and checkpointed on local MPS.

## Run Setup

```text
run root: /tmp/adi_nanochat_core4_20260429_smoke
workspace copy: runs/nanochat_core4_20260429
nanochat repo: /tmp/nanochat-read
device: mps
dtype: float32
conversion mode: input_target
shared tokenizer vocab request: 4096
shared tokenizer train docs: 15215
shared tokenizer val docs: 1867
```

The earlier verbose `conversation` rendering was not used because labels such
as `EXAMPLE_ID`, `TASK_TYPE`, and `VARIANT` would pollute the pretraining text.
The `input_target` rendering keeps the actual learning surface closer to the
experiment:

```text
TinyStories: story text only
Procedural: scenario/question plus target answer/relation text
```

## Model Setup

All four arms used the same tokenizer, architecture, sequence length, batch
budget, and iteration count.

```text
depth: 2
embedding width: 128
heads: 2
max sequence length: 256
parameters: 1966134
total batch size: 2048 tokens
iterations: 20
training tokens per arm: 40960
eval tokens: 8192
```

## Arms

```text
tinystories_plain_text
procedural_plain_text
procedural_relation_scaffolded
procedural_relation_first_then_text
```

## Results

| Arm | Initial Val BPB | Final Val BPB | Change |
| --- | ---: | ---: | ---: |
| tinystories_plain_text | 3.014457 | 2.894597 | -0.119860 |
| procedural_plain_text | 3.546736 | 3.223261 | -0.323475 |
| procedural_relation_scaffolded | 3.805675 | 3.434072 | -0.371603 |
| procedural_relation_first_then_text | 3.842853 | 3.461918 | -0.380935 |

All four runs completed and saved final checkpoints.

## Checkpoints

```text
/tmp/adi_nanochat_core4_20260429_smoke/tinystories_plain_text/base_checkpoints/core4_tinystories_plain_text_d2_i20
/tmp/adi_nanochat_core4_20260429_smoke/procedural_plain_text/base_checkpoints/core4_procedural_plain_text_d2_i20
/tmp/adi_nanochat_core4_20260429_smoke/procedural_relation_scaffolded/base_checkpoints/core4_procedural_relation_scaffolded_d2_i20
/tmp/adi_nanochat_core4_20260429_smoke/procedural_relation_first_then_text/base_checkpoints/core4_procedural_relation_first_then_text_d2_i20
```

## Interpretation

The smoke test proves the training path works:

```text
JSONL to Parquet conversion works
shared tokenizer training works
the same tokenizer can be copied to all arms
nanochat base training runs locally on MPS
loss decreases for every arm
checkpoints are written for every arm
```

This does not yet prove the relation hypothesis. The model is only about 2M
parameters and each arm saw only 40960 training tokens. It only proves that the
path is healthy enough for a longer run.

## Follow-Up Depth-4 Local Run

After the 20-step smoke passed, a longer local run was executed on the same
four arms using the same shared tokenizer.

```text
depth: 4
embedding width: 256
heads: 4
max sequence length: 256
parameters: 7340162
total batch size: 2048 tokens
iterations: 500
training tokens per arm: 1024000
eval tokens: 32768
```

| Arm | Initial Val BPB | Final Val BPB | Change |
| --- | ---: | ---: | ---: |
| tinystories_plain_text | 2.967028 | 1.221640 | -1.745388 |
| procedural_plain_text | 3.621244 | 0.150843 | -3.470401 |
| procedural_relation_scaffolded | 3.769814 | 0.057640 | -3.712174 |
| procedural_relation_first_then_text | 3.777705 | 0.062668 | -3.715037 |

Checkpoints:

```text
/tmp/adi_nanochat_core4_20260429_smoke/tinystories_plain_text/base_checkpoints/core4_tinystories_plain_text_d4_i500
/tmp/adi_nanochat_core4_20260429_smoke/procedural_plain_text/base_checkpoints/core4_procedural_plain_text_d4_i500
/tmp/adi_nanochat_core4_20260429_smoke/procedural_relation_scaffolded/base_checkpoints/core4_procedural_relation_scaffolded_d4_i500
/tmp/adi_nanochat_core4_20260429_smoke/procedural_relation_first_then_text/base_checkpoints/core4_procedural_relation_first_then_text_d4_i500
```

The full run directory was copied into the ignored workspace path
`runs/nanochat_core4_20260429` so follow-up evaluation can use the checkpoints
without relying on `/tmp`.

Interpretation:

```text
All four depth-4 runs trained successfully.
The procedural arms fit far faster than TinyStories.
The explicit relation arms fit the procedural validation split best.
```

This is still not a proof of the relation hypothesis. The procedural train/dev
splits share the same generator distribution, while TinyStories is broader,
more varied natural text. These BPB numbers mainly show learnability and
format/corpus entropy. The real question remains whether the relation arms
transfer better on held-out relation cases.

## Held-Out Evaluation

The depth-4 checkpoints were evaluated on 623 held-out procedural V3 questions
using the same plain prompt surface for every model.

| Arm | Answer Exact | Fact Exact |
| --- | ---: | ---: |
| tinystories_plain_text | 0.0% | 0.0% |
| procedural_plain_text | 74.6% | 39.3% |
| procedural_relation_scaffolded | 82.2% | 73.4% |
| procedural_relation_first_then_text | 50.7% | 19.4% |

Detailed report:

```text
docs/nanochat-core4-heldout-evaluation-2026-04-29.md
```

Interpretation:

```text
The relation-scaffolded arm produced the strongest held-out result under fair
plain prompts. This is a useful positive signal, but it is still same-generator
transfer inside a tiny controlled language.
```

## Next Step

Run a tighter control before spending rented-GPU money:

```text
plain procedural model with answer protocol exposure but no relation lines
vs relation-scaffolded model at matched token budget
```

If the scaffolded arm still wins, expand the generated world and add a separate
natural-language transfer set.
