# Project Handoff

Last updated: 2026-04-27

Working directory:

```text
/Users/rajmohan/OpenSource/adi-llm
```

Important instruction:

```text
Do not commit or push unless Rajmohan explicitly asks.
```

## Current Git State

Latest commits:

```text
aa69e06 Add physical v0.3 binary candidate scoring experiment
e69aecc Add physical v0.2 candidate selection experiment
58e850c Add physical v0.1 bridge experiment
```

Known untracked files at time of handoff:

```text
Chapter_12_Mind_Your_Reality.pdf
docs/book-theory-implementation-notes.md
docs/core-relation-curriculum-plan.md
docs/social-world-200-situations.md
docs/social-world-firstset-relation-audit.md
docs/math-abstraction-200-situations.md
docs/math-abstraction-firstset-relation-audit.md
docs/language-binding-400-situations.md
docs/tiny-from-scratch-relation-experiment.md
handoff.md
data/developmental_graph/core_curriculum_plan.json
data/developmental_graph/seeds/social_world.json
data/developmental_graph/evaluations/social_world_heldout.json
data/developmental_graph/seeds/math_abstraction.json
data/developmental_graph/evaluations/math_abstraction_heldout.json
scripts/create_nanochat_pretrain_shards.py
```

Known tracked files modified after the last commit:

```text
docs/execution-roadmap.md
docs/experiment-log.md
plan.md
requirements-training.txt
```

The untracked PDF should not be committed unless explicitly requested.

## Project Goal

The project is testing Rajmohan's theory that:

```text
information is relation
meaning is relation structure
cognition is activation over relation structure
abstraction is compressed relation structure
```

The practical AI goal is to see whether a small model can become more capable or
better aligned by training with explicit relation structure.

## Current Conceptual Split

There are now two tracks.

### Track A: Relation Memory For Cognition

Claim:

```text
The model knows by relation structure.
```

Examples:

```text
ball -> has_property -> round
ball -> can_do -> bounce
rubber -> has_property -> elastic
elastic_object + impact -> causes -> bounce
```

Goal:

```text
Improve sample efficiency and transfer in small models by giving relation
structure directly instead of expecting the model to infer all relations from
plain text.
```

### Track B: Affect-Relation Model For Alignment

Claim:

```text
The model values by relation dynamics.
```

Current formulation:

```text
happiness =
  pain_absence_or_reduction
  + positive_relation_gain
  - relation_gain_toward_pain_or_unhappiness
```

Diminishing return rule:

```text
happiness_gain = relation_delta * (1 - current_relation_strength)
```

Examples:

```text
new useful relation forms -> happiness
existing weak relation strengthens -> moderate happiness
already strong relation strengthens -> low happiness gain
pain relation activates -> unhappiness
relation to pain/loss/shame/harm cluster strengthens -> unhappiness
strong relation breaks -> sadness
repeated praise -> diminishing happiness
harmful shortcut pleasure -> immediate positive activation but long-term relation loss
```

Track B is an extension of Track A, not a separate theory:

```text
Track A = cognition/meaning
Track B = motivation/affect/alignment
```

## Important Theory Documents

Existing canonical theory note:

```text
docs/information-cognition-abstraction-theory.md
```

New broader implementation note:

```text
docs/book-theory-implementation-notes.md
```

The new note captures book-level implementation ideas beyond Chapter 12:

```text
dependency
self-boundary as influence boundary
happiness as relation dynamics
Lethe/reward saturation
success and alienation
ethics as positive reinforcement
meaning in life as relation density
group identity and fulfillment
```

## Book Review Context

All 13 chapter PDFs were reviewed from:

```text
/Users/rajmohan/Downloads/utopai_split/
```

Temporary extracted text was created in:

```text
/tmp/utopai_text/
```

This extraction is temporary and should not be assumed persistent.

Theory-bearing chapters:

```text
Chapter 02: meaning, real emotions, self-sufficiency, shallow vs real happiness
Chapter 04: Lethe, reward tolerance, habituation, growth suppression
Chapter 07: abundance, scarcity, motivation, value, social control
Chapter 08: dependency, usefulness, family/social relations, humanity
Chapter 09: success, alienation, ethics, respect, scarcity, collectivism
Chapter 11: self as area of influence, group-self extension
Chapter 12: relation/information/cognition/abstraction/domino model
Chapter 13: meaning in life as relations, group size, free will, justice
```

## Current Experiment Status

The active empirical path has been the physical-world vertical slice.

Rule from roadmap:

```text
Do not expand broadly until one narrow vertical slice has measurable signal.
```

Current roadmap file:

```text
docs/execution-roadmap.md
```

Experiment log:

```text
docs/experiment-log.md
```

### Physical V0

Model:

```text
HuggingFaceTB/SmolLM2-135M
```

Compared:

```text
plain_text
flat_triples
relation_scaffolded
```

Result:

```text
relation_scaffolded fit train/dev best but did not transfer on held-out graph scoring
```

### Physical V0.1

Added bridge curriculum:

```text
node_id_from_paraphrase
relation_family_from_prompt
graph_anchor_from_prompt
explanation_with_relations
```

Result:

```text
local fit improved, held-out graph transfer still failed
```

### Physical V0.2

Changed to closed-vocabulary candidate selection.

Result:

```text
invented IDs eliminated
model over-selected candidates
exact held-out pass remained zero
```

### Physical V0.3

Changed to binary candidate scoring:

```text
one prompt per candidate -> ANSWER: YES/NO
```

Data:

```text
train: 2376
dev: 283
curriculum_test: 343
held-out binary prompts: 794
```

Run:

```text
runs/physical_v0_3/smollm2_135m/binary_candidate_scoring_s300
```

Task-matched greedy held-out result:

```text
case pass:        0.000
family precision: 0.750
family recall:    0.066
anchor precision: 0.400
anchor recall:    0.038
gap precision:    0.287
gap recall:       0.868
```

YES/NO logit top-k diagnostic:

```text
case pass:        0.000
family precision: 0.407
family recall:    0.407
anchor precision: 0.288
anchor recall:    0.288
gap precision:    0.289
gap recall:       0.289
```

Interpretation:

```text
Binary scoring fixed over-selection only by creating under-selection and
calibration problems. Logits contain weak relation-ranking signal, but transfer
is not yet good.
```

Detailed report:

```text
docs/physical-v0-3-binary-candidate-scoring.md
```

## Gemini Semantic Judge

A one-call Gemini judge was run over 33 physical_v0_3 case summaries comparing:

```text
Model A = base SmolLM2-135M
Model B = fine-tuned physical_v0_3 SmolLM2-135M
```

Artifacts:

```text
runs/physical_v0_3/exports/gemini_semantic_judge_input.json
runs/physical_v0_3/exports/gemini_semantic_judge_raw_response.txt
runs/physical_v0_3/exports/gemini_semantic_judge_result.json
runs/physical_v0_3/exports/gemini_semantic_judge_summary.md
runs/physical_v0_3/exports/gemini_semantic_judge_corrected_summary.md
```

Corrected numeric aggregate:

```text
Model A average: 2.182
Model B average: 2.424
Model A numeric wins: 12
Model B numeric wins: 11
ties: 10
average-score winner: Model B, fine-tuned
```

Interpretation:

```text
Fine-tuning gave a slight semantic improvement on average, especially transfer
probes, but not a dramatic result.
```

## Nanochat Context

Karpathy nanochat was inspected in:

```text
/tmp/nanochat-read
```

Repo commit inspected:

```text
0aaca56
```

Useful files in nanochat:

```text
nanochat/gpt.py
scripts/base_train.py
scripts/chat_sft.py
scripts/chat_rl.py
nanochat/tokenizer.py
nanochat/dataloader.py
nanochat/engine.py
runs/runcpu.sh
runs/speedrun.sh
```

Relevant understanding:

```text
nanochat is a full small-LLM pipeline:
tokenizer -> base pretraining -> eval -> SFT -> optional RL -> chat UI
```

Architecture has modern GPT changes:

```text
RoPE
RMSNorm
QK norm
grouped-query attention
sliding-window/full attention pattern
ReLU^2 MLP
no linear bias
untied embeddings
Muon optimizer
explicit dtype control
```

Current guidance:

```text
Do not modify nanochat architecture first.
Use existing Transformer/nanochat pipeline.
Test relation/affect data against baselines.
```

Mac smoke tests are possible with `mps`, but real experiments need cloud GPU.

New nanochat project artifacts:

```text
docs/core-relation-curriculum-plan.md
data/developmental_graph/core_curriculum_plan.json
docs/tiny-from-scratch-relation-experiment.md
scripts/create_nanochat_pretrain_shards.py
```

The core curriculum plan defines the first serious multi-domain test:

```text
1. 6mo root world
2. everyday physical world
3. simple social world
4. math/abstraction roots
5. language binding
```

It also fixes the representation variants:

```text
plain_text
relation_scaffolded
relation_first_then_text
```

The parseable manifest validates as JSON:

```text
data/developmental_graph/core_curriculum_plan.json
```

The new design doc fixes the from-scratch experiment shape:

```text
same tiny nanochat model
same tokenizer
same token budget
same compute budget
only the training representation changes:
  plain_text
  relation_scaffolded
  relation_first_then_text
```

The new adapter script converts project JSONL examples into nanochat-compatible
Parquet shards:

```text
$NANOCHAT_BASE_DIR/base_data_climbmix/shard_00000.parquet
$NANOCHAT_BASE_DIR/base_data_climbmix/shard_06542.parquet
```

The script requires `pyarrow` for actual Parquet writing. The current
environment initially did not have `pyarrow`, so it was installed into the
project venv and pinned in:

```text
requirements-training.txt
```

Level 0 local smoke results:

```text
plain base dir:    /tmp/adi_nanochat_plain_smoke
relation base dir: /tmp/adi_nanochat_relation_smoke
train docs:        11800 per variant
val docs:          280 per variant
nanochat repo:     /tmp/nanochat-read
device:            mps
depth:             2
max_seq_len:       256
iterations:        20
tokens:            40960 per run
```

Plain-text smoke:

```text
model tag:              adi_plain_d2_smoke20
parameters:             983094
initial validation bpb: 2.379064
final validation bpb:   1.992483
checkpoint:             /tmp/adi_nanochat_plain_smoke/base_checkpoints/adi_plain_d2_smoke20
```

Relation-scaffolded smoke:

```text
model tag:              adi_relation_d2_smoke20
parameters:             1179702
initial validation bpb: 2.412748
final validation bpb:   2.027082
checkpoint:             /tmp/adi_nanochat_relation_smoke/base_checkpoints/adi_relation_d2_smoke20
```

Caveat:

```text
These are not comparison results because the two runs used separately trained
tokenizers. That changed effective vocab size and parameter count.
```

Vast.ai note:

```text
8xH200 is not needed for first experiments.
Use Mac for smoke tests, then 1x GPU for first real run, then 4x H200 if scripts
are stable. Use 8x H200 only for speedrun-scale runs.
```

## Recommended Next Steps

Immediate next step:

```text
Generate core5 curriculum variants from the five ready seed/evaluation domains.
```

The Level 0 nanochat smoke path has already completed, the core5 plan exists,
`docs/social-world-200-situations.md` now contains 200 raw social-world
situation families, and `docs/social-world-firstset-relation-audit.md` now
contains the first derived relation audit. `data/developmental_graph/seeds/social_world.json`
now contains the parseable social seed graph and validates cleanly.
`data/developmental_graph/evaluations/social_world_heldout.json` now contains
the parseable social held-out evaluation and validates cleanly. Before any
serious comparison, the remaining missing core domains must be built in the same
raw-inventory -> relation-audit -> seed-graph -> held-out-evaluation pipeline.
`docs/math-abstraction-200-situations.md` now contains the raw 200-row
math/abstraction inventory and its first prioritisation pass. It has 66 first-set
rows marked `yes`. `docs/math-abstraction-firstset-relation-audit.md` now
contains the derived relation audit for those 66 rows.
`data/developmental_graph/seeds/math_abstraction.json` now contains the
parseable math seed graph and validates cleanly.
`data/developmental_graph/evaluations/math_abstraction_heldout.json` now
contains the parseable math held-out evaluation and validates cleanly.
`docs/language-binding-400-situations.md` now contains the raw 400-row
language-binding inventory and its first prioritisation pass. It has 179
first-set rows marked `yes`, 78 marked `maybe`, and 143 marked `no`.
`docs/language-binding-firstset-relation-audit.md` now contains the derived
relation audit for those 179 first-set rows.
`data/developmental_graph/seeds/language_binding.json` now contains the
parseable language seed graph and validates cleanly.
`data/developmental_graph/evaluations/language_binding_heldout.json` now
contains the parseable language held-out evaluation and validates cleanly.

Social seed graph summary:

```text
nodes: 109
relations: 74
micro_experiences: 14
evaluation_questions: 10
validator: OK, no warnings
```

Social held-out evaluation summary:

```text
cases: 25
transfer probes: 6
gap probes: 19
graph anchors: 69
gap indicators: 47
validator: OK
```

Math seed graph summary:

```text
nodes: 109
relations: 81
micro_experiences: 9
evaluation_questions: 11
validator: OK, no warnings
```

Math held-out evaluation summary:

```text
cases: 27
transfer probes: 7
gap probes: 20
graph anchors: 83
gap indicators: 61
validator: OK
```

Language seed graph summary:

```text
nodes: 121
relations: 230
micro_experiences: 12
evaluation_questions: 10
validator: OK, no warnings
```

Language held-out evaluation summary:

```text
cases: 23
transfer probes: 19
gap probes: 4
graph anchors: 57
gap indicators: 10
validator: OK
```

Suggested order:

```text
1. Generate core5 curriculum variants.
2. Add `relation_first_then_text` rendering if the generator does not already cover it.
3. Add shared-tokenizer procedure for nanochat.
4. Run Level 1 core5 local sanity.
5. Move to one rented GPU for the first meaningful signal test.
```

Track B remains important, but the newest direction is to first test the
from-scratch relation-training idea through nanochat.

Track B scenario families:

```text
pain reduction
new learning
repeated praise / saturation
connection loss
harmful pleasure shortcut
long-term relation growth
comfort vs happiness
happiness vs meaning
known pain cluster activation
social shame
trust and repair
effort and mastery
novelty vs repetition
drug/Lethe shortcut
truthful hard feedback vs comforting lie
```

Key evaluation probes:

```text
first praise vs repeated praise
learning new skill vs repeating known action
drug pleasure vs long-term relation loss
friend leaving vs stranger leaving
comfort from safety vs happiness from growth
truth causing short-term pain but long-term relation repair
lie causing short-term comfort but long-term relation damage
```

## Current Important Files

Theory and planning:

```text
docs/information-cognition-abstraction-theory.md
docs/book-theory-implementation-notes.md
docs/core-relation-curriculum-plan.md
docs/social-world-200-situations.md
docs/social-world-firstset-relation-audit.md
docs/math-abstraction-200-situations.md
docs/math-abstraction-firstset-relation-audit.md
docs/language-binding-400-situations.md
docs/tiny-from-scratch-relation-experiment.md
docs/execution-roadmap.md
docs/experiment-log.md
```

Core graph/data:

```text
data/developmental_graph/core_curriculum_plan.json
data/developmental_graph/seeds/agent_6mo_indian_child.json
data/developmental_graph/seeds/everyday_physical_world.json
data/developmental_graph/seeds/social_world.json
data/developmental_graph/seeds/math_abstraction.json
data/developmental_graph/evaluations/everyday_physical_world_heldout.json
data/developmental_graph/evaluations/social_world_heldout.json
data/developmental_graph/evaluations/math_abstraction_heldout.json
data/developmental_graph/experiments/physical_v0_3/
```

Scripts for physical experiments:

```text
scripts/create_binary_candidate_experiment.py
scripts/create_nanochat_pretrain_shards.py
scripts/run_binary_candidate_evaluation.py
scripts/score_binary_candidate_logits.py
scripts/train_tiny_causal_lm.py
```

## Cautions

Do not claim:

```text
"happiness diminishing returns is entirely new"
"alignment training will not be required"
"relation memory is already proven"
```

Better claim:

```text
Known pieces from neuroscience/RL can be synthesized into a relation-dynamics
model of affect, and this can be tested as a small-model alignment scaffold.
```

Relevant existing areas:

```text
reward prediction error
homeostatic reinforcement learning
intrinsic motivation / curiosity / learning progress
hedonic adaptation / habituation
wanting vs liking
aversive learning
```

Distinctive project angle:

```text
Represent affect as explicit relation dynamics:
pain reduction + relation gain with diminishing returns - relation gain toward
pain/loss clusters.
```

## Restart Checklist

On a new session:

```bash
cd /Users/rajmohan/OpenSource/adi-llm
git status --short
sed -n '1,220p' handoff.md
sed -n '1,260p' docs/book-theory-implementation-notes.md
sed -n '1,220p' docs/execution-roadmap.md
```

Then ask Rajmohan whether to continue with:

```text
social-world held-out evaluation
nanochat shared-tokenizer repair
or Track B affect-relation scenarios
or physical_v0_4 relation-ranking repair
```

Current recommendation:

```text
social-world held-out evaluation.
```
