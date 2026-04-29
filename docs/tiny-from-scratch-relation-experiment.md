# Tiny From-Scratch Relation Experiment Using nanochat

Status: design locked enough to implement.

Date: 2026-04-27

## Purpose

This experiment tests the core engineering claim in the cleanest small form:

```text
With the same tiny transformer, same tokenizer, same token budget, and same
compute budget, does relation-aware pretraining produce better transfer than
plain-text pretraining?
```

The goal is not to make a useful chatbot. A 10M parameter model will not have
general intelligence. The goal is to see whether relation-first data gives a
measurable efficiency advantage.

## Why nanochat

nanochat is useful here because it trains a GPT-style decoder transformer from
scratch and already provides:

```text
tokenizer training
base model pretraining
loss evaluation
checkpointing
sampling
CPU/MPS smoke runs
single-node GPU runs
```

That is closer to the real question than fine-tuning SmolLM2. Fine-tuning asks:

```text
Can relation data steer a model whose internal structure was already learned
from ordinary text?
```

The nanochat experiment asks:

```text
Can relation data shape the model from the beginning?
```

## Can This Be Tested Locally?

Yes, but only as a smoke test.

Local Mac/MPS testing can verify:

```text
data conversion works
tokenizer training works
model starts training
loss decreases
checkpoints save
held-out evaluation scripts can read model outputs
```

Local Mac/MPS testing should not be treated as proof that the idea works. The
model and token budget will be too small for strong capability. The first
meaningful test should be on one rented GPU after the local path is stable.

## Experimental Comparison

Train the same nanochat model four times:

```text
A. normal_simple_text
B. relation_designed_plain_text
C. relation_scaffolded
D. relation_first_then_text
```

Everything else must stay fixed:

```text
same nanochat commit
same architecture depth
same vocab size
same tokenizer
same max sequence length
same batch size
same number of training tokens
same optimizer settings
same train/dev/test split logic
same held-out evaluation
```

For B/C/D, only the training text representation changes. A is the external
normal-simple-text control and must be matched by training token budget.

## Dataset Variants

### A. normal_simple_text

The model sees ordinary simple stories, not relation-designed scenarios.

Current source:

```text
tinystories_v0
```

This is the true normal-text baseline.

### B. relation_designed_plain_text

The model sees relation-designed scenarios rendered as plain text.

Example document:

```text
Question:
Why might a glass cup and a steel tumbler produce different outcomes when
dropped from the same height?

Answer:
The fall-impact frame is the same, but glass is fragile and can shatter, while
steel is less fragile and may make a ringing sound or dent instead.
```

This tests whether relation-designed data helps even without explicit relation
lines.

### C. relation_scaffolded

The model sees the same natural-language facts plus explicit relation structure.

Example document:

```text
Question:
Why might a glass cup and a steel tumbler produce different outcomes when
dropped from the same height?

Relations:
object_fall_impact:
  object -> moves_down -> floor
  impact -> causes -> force_transfer

material_impact_outcome:
  glass -> has_property -> fragile
  fragile + impact -> can_cause -> shatter
  metal + impact -> can_cause -> dent
  metal + impact -> can_cause -> ringing_sound

Answer:
The same fall-impact relation is active, but the material relations change the
outcome.
```

This tests whether explicit relations improve learning.

### D. relation_first_then_text

The model first sees the relation packet, then the text that uses it.

Example document:

```text
RELATION_PACKET:
object_fall_impact:
  object_above_ground -> unsupported -> downward_motion
  downward_motion + hard_contact -> impact

material_impact_outcome:
  brittle_material + impact -> crack_or_shatter
  elastic_material + impact -> deform_then_recover
  metal_container + impact -> dent_or_ring

TEXT_BINDING:
A glass cup may shatter when dropped because glass is brittle. A rubber ball
may bounce because rubber deforms and recovers. A steel tumbler may dent or
ring because metal responds differently to impact.
```

This is closest to the theory:

```text
learn relation structure first
then attach language to it
```

## What We Should Not Do Yet

Do not add custom architecture in this first experiment.

Avoid:

```text
external memory
graph adapters
MoE
retrieval
happiness objective
RL
chat tuning
```

Those may matter later. First we need to know whether the data-side relation
signal helps at all.

## Data Size Ladder

Use a ladder instead of jumping straight to a costly run.

```text
Level 0: local smoke
  10K to 100K tokens
  depth 2 to 4
  purpose: verify plumbing only

Level 1: local overfit/sanity
  0.5M to 2M tokens
  depth 4 to 5
  purpose: see whether tiny models can fit the controlled relation corpus

Level 2: one-GPU signal test
  10M to 50M tokens
  depth 5 to 8
  purpose: compare transfer per token

Level 3: stronger small-model test
  100M+ tokens
  depth 8 to 12
  purpose: decide whether scaling is justified
```

Do not rent a large multi-H200 box until Level 2 shows a real signal.

## Model Sizes

nanochat uses `--depth` as the main model-size dial. Width and related settings
are derived from depth, unless overridden.

For local smoke:

```text
depth 2 or 4
vocab size 4096 or 8192
max sequence length 256
```

For the first meaningful small run:

```text
depth 5 to 8
vocab size 8192 or 16384
max sequence length 512
```

The exact parameter count should be read from nanochat's printed
`Parameter counts` section for each run. Do not rely on hand estimates.

## Data Conversion For nanochat

nanochat pretraining expects Parquet files with a `text` column.

It reads them from:

```text
$NANOCHAT_BASE_DIR/base_data_climbmix/
```

The last sorted parquet file is used as validation. All earlier parquet files
are used as training.

For our custom runs, create one train shard and one validation shard:

```text
$NANOCHAT_BASE_DIR/base_data_climbmix/shard_00000.parquet
$NANOCHAT_BASE_DIR/base_data_climbmix/shard_06542.parquet
```

The script added for this project is:

```text
scripts/create_nanochat_pretrain_shards.py
```

Example:

```bash
python scripts/create_nanochat_pretrain_shards.py \
  --train-jsonl data/developmental_graph/experiments/physical_v0/datasets/plain_text/train.jsonl \
  --val-jsonl data/developmental_graph/experiments/physical_v0/datasets/plain_text/dev.jsonl \
  --base-dir /tmp/adi_nanochat_plain_smoke \
  --train-repeat 100 \
  --val-repeat 20
```

That creates:

```text
/tmp/adi_nanochat_plain_smoke/base_data_climbmix/shard_00000.parquet
/tmp/adi_nanochat_plain_smoke/base_data_climbmix/shard_06542.parquet
/tmp/adi_nanochat_plain_smoke/base_data_climbmix/manifest.json
```

Repeat the same for `relation_scaffolded`.

## Tokenizer Rule

For a fair comparison, all dataset variants should use the same tokenizer.

Bad comparison:

```text
plain_text uses tokenizer trained only on plain_text
relation_scaffolded uses tokenizer trained only on relation_scaffolded
```

That confounds representation format with tokenization.

Preferred comparison:

```text
train one shared tokenizer on a mixed corpus
copy the same tokenizer directory into each variant base dir
train each model with that same tokenizer
```

Smoke tests can violate this temporarily to prove the path works, but real
results should use the shared tokenizer.

## Local Smoke Commands

Assume nanochat is checked out at:

```text
/tmp/nanochat-read
```

Create a plain-text smoke dataset from this repo:

```bash
cd /Users/rajmohan/OpenSource/adi-llm

python scripts/create_nanochat_pretrain_shards.py \
  --train-jsonl data/developmental_graph/experiments/physical_v0/datasets/plain_text/train.jsonl \
  --val-jsonl data/developmental_graph/experiments/physical_v0/datasets/plain_text/dev.jsonl \
  --base-dir /tmp/adi_nanochat_plain_smoke \
  --train-repeat 100 \
  --val-repeat 20
```

Run nanochat tokenizer and tiny pretraining:

```bash
cd /tmp/nanochat-read
export NANOCHAT_BASE_DIR=/tmp/adi_nanochat_plain_smoke

uv sync --extra cpu
source .venv/bin/activate

python -m scripts.tok_train \
  --max-chars=5000000 \
  --vocab-size=4096

python -m scripts.base_train \
  --device-type=mps \
  --depth=2 \
  --aspect-ratio=64 \
  --head-dim=64 \
  --window-pattern=L \
  --max-seq-len=256 \
  --device-batch-size=4 \
  --total-batch-size=2048 \
  --eval-every=20 \
  --eval-tokens=8192 \
  --core-metric-every=-1 \
  --sample-every=50 \
  --save-every=-1 \
  --num-iterations=100 \
  --run=dummy \
  --model-tag=adi_plain_d2_smoke
```

If MPS has issues, switch:

```text
--device-type=cpu
```

CPU will be slower but useful for debugging.

## Relation-Scaffolded Smoke Commands

Create the relation-scaffolded dataset:

```bash
cd /Users/rajmohan/OpenSource/adi-llm

python scripts/create_nanochat_pretrain_shards.py \
  --train-jsonl data/developmental_graph/experiments/physical_v0/datasets/relation_scaffolded/train.jsonl \
  --val-jsonl data/developmental_graph/experiments/physical_v0/datasets/relation_scaffolded/dev.jsonl \
  --base-dir /tmp/adi_nanochat_relation_smoke \
  --train-repeat 100 \
  --val-repeat 20
```

Then in nanochat:

```bash
cd /tmp/nanochat-read
export NANOCHAT_BASE_DIR=/tmp/adi_nanochat_relation_smoke
source .venv/bin/activate

python -m scripts.tok_train \
  --max-chars=5000000 \
  --vocab-size=4096

python -m scripts.base_train \
  --device-type=mps \
  --depth=2 \
  --aspect-ratio=64 \
  --head-dim=64 \
  --window-pattern=L \
  --max-seq-len=256 \
  --device-batch-size=4 \
  --total-batch-size=2048 \
  --eval-every=20 \
  --eval-tokens=8192 \
  --core-metric-every=-1 \
  --sample-every=50 \
  --save-every=-1 \
  --num-iterations=100 \
  --run=dummy \
  --model-tag=adi_relation_d2_smoke
```

Again, this only proves the local path runs.

## Evaluation

The primary metric is not training loss.

Training loss answers:

```text
Did the model fit this representation?
```

The real question is:

```text
Did the model learn relations that transfer to held-out cases?
```

Evaluation should measure:

```text
held-out relation family recall
held-out graph anchor recall
false relation rejection
counterfactual transfer
object/property transfer
natural-language answer quality
sample efficiency
```

The strongest early signal would be:

```text
relation_first_then_text reaches the same held-out score with fewer tokens
than plain_text
```

## Success Criteria

Level 0 local smoke succeeds if:

```text
Parquet shards are created
tokenizer trains
base_train starts and completes
loss decreases
checkpoint is written
the run can generate text
```

Level 1 sanity succeeds if:

```text
the relation model fits controlled relation documents faster than plain text
and does not collapse into format-only memorization
```

Level 2 signal succeeds if:

```text
relation-scaffolded or relation-first beats plain_text on held-out transfer
using the same model size and token budget
```

The result is not useful if relation training only improves exact-format recall
but does not improve transfer.

## Failure Modes To Watch

1. Format memorization:

```text
The model learns JSON-looking output but does not understand the relation.
```

2. Tokenizer confound:

```text
The relation model looks better or worse because its tokenizer differs.
```

3. Tiny-data illusion:

```text
The repeated small corpus makes loss go down but teaches no transfer.
```

4. Evaluation too brittle:

```text
The model says the right thing in different words and the exact scorer marks it
wrong.
```

5. Evaluation too loose:

```text
An LLM judge gives credit for plausible generic answers without checking the
intended relation path.
```

## Next Implementation Steps

1. Use `scripts/create_nanochat_pretrain_shards.py` to create local plain and
   relation smoke datasets. Done.
2. Run `python -m scripts.tok_train` inside nanochat on one smoke dataset. Done.
3. Run `python -m scripts.base_train` with `depth=2` and `max_seq_len=256`.
   Done.
4. Repeat with the second dataset. Done.
5. Confirm both runs complete locally. Done.
6. Add a shared-tokenizer procedure before any serious comparison.
7. Add `relation_first_then_text` data generation.
8. Run a depth 4 or 5 local sanity pass.
9. Move to one rented GPU for the first meaningful signal test.

## Local Smoke Result: 2026-04-27

This was a path verification, not a theory result.

Generated datasets:

```text
/tmp/adi_nanochat_plain_smoke
/tmp/adi_nanochat_relation_smoke
```

Each dataset contains:

```text
train shard: 11800 docs
val shard:   280 docs
```

nanochat environment:

```text
repo: /tmp/nanochat-read
device: mps
dtype: float32
```

Plain-text smoke run:

```text
tokenizer vocab request: 4096
effective vocab size:    1504
model tag:               adi_plain_d2_smoke20
parameters:              983,094
training tokens:         40,960
initial validation bpb:  2.379064
final validation bpb:    1.992483
checkpoint:              /tmp/adi_nanochat_plain_smoke/base_checkpoints/adi_plain_d2_smoke20
```

Relation-scaffolded smoke run:

```text
tokenizer vocab request: 4096
effective vocab size:    2012
model tag:               adi_relation_d2_smoke20
parameters:              1,179,702
training tokens:         40,960
initial validation bpb:  2.412748
final validation bpb:    2.027082
checkpoint:              /tmp/adi_nanochat_relation_smoke/base_checkpoints/adi_relation_d2_smoke20
```

Interpretation:

```text
The custom project data can be converted into nanochat pretraining shards.
nanochat tokenizer training works on those shards.
nanochat base pretraining works locally on MPS for both variants.
Loss moves down and checkpoints save.
```

Important caveat:

```text
The two smoke runs used separately trained tokenizers, so they are not a fair
plain-vs-relation comparison. The different effective vocabulary sizes changed
the parameter counts. The next serious run must use one shared tokenizer across
all variants.
```

## Current Recommendation

The shared-tokenizer four-arm local smoke has now completed. See:

```text
docs/nanochat-core4-local-smoke-2026-04-29.md
```

The depth-4 local run and first held-out relation evaluation have completed.
See:

```text
docs/nanochat-core4-local-smoke-2026-04-29.md
docs/nanochat-core4-heldout-evaluation-2026-04-29.md
```

Current recommendation:

```text
Run one tighter local control before spending Vast.ai money:
plain procedural model with answer protocol exposure but no explicit relation
lines vs relation-scaffolded at matched token budget.
```
