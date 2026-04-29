# Project Handoff

Last updated: 2026-04-29

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
624562a Build core relation curriculum foundation
aa69e06 Add physical v0.3 binary candidate scoring experiment
e69aecc Add physical v0.2 candidate selection experiment
```

Known untracked files at time of handoff:

```text
Chapter_12_Mind_Your_Reality.pdf
data/developmental_graph/experiments/core5_v0/
data/developmental_graph/experiments/core5_v0_controlled/
data/developmental_graph/experiments/core5_v0_childlang/
data/developmental_graph/experiments/core5_v0_foundation/
data/developmental_graph/experiments/procedural_foundation_v0/
data/developmental_graph/experiments/procedural_foundation_v1/
data/developmental_graph/experiments/procedural_foundation_v2/
data/developmental_graph/experiments/procedural_foundation_v3/
data/developmental_graph/experiments/tinystories_v0/
docs/core5-v0-curriculum-variants.md
docs/core5-v0-controlled-vocabulary.md
docs/core5-v0-child-language.md
docs/core5-v0-foundation-ladder.md
docs/procedural-foundation-v0.md
docs/procedural-foundation-v1.md
docs/procedural-foundation-v2.md
docs/procedural-foundation-v3.md
docs/tinystories-v0-baseline.md
docs/nanochat-core4-local-smoke-2026-04-29.md
docs/procedural-foundation-v3.md
scripts/create_core5_curriculum_variants.py
scripts/create_core5_controlled_vocabulary_variants.py
scripts/create_core5_child_language_variants.py
scripts/create_core5_foundation_variants.py
scripts/create_procedural_foundation_world.py
scripts/create_procedural_foundation_world_v1.py
scripts/create_procedural_foundation_world_v2.py
scripts/create_procedural_foundation_world_v3.py
scripts/create_tinystories_baseline.py
scripts/create_tinystories_baseline.py
```

Known tracked files modified after the last commit:

```text
data/developmental_graph/core_curriculum_plan.json
docs/core-relation-curriculum-plan.md
docs/experiment-log.md
handoff.md
plan.md
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
docs/core5-v0-curriculum-variants.md
docs/core5-v0-controlled-vocabulary.md
docs/core5-v0-child-language.md
docs/core5-v0-foundation-ladder.md
docs/procedural-foundation-v0.md
docs/procedural-foundation-v1.md
docs/procedural-foundation-v2.md
data/developmental_graph/core_curriculum_plan.json
data/developmental_graph/experiments/core5_v0/
data/developmental_graph/experiments/core5_v0_controlled/
data/developmental_graph/experiments/core5_v0_childlang/
data/developmental_graph/experiments/core5_v0_foundation/
data/developmental_graph/experiments/procedural_foundation_v0/
data/developmental_graph/experiments/procedural_foundation_v1/
data/developmental_graph/experiments/procedural_foundation_v2/
data/developmental_graph/experiments/procedural_foundation_v3/
docs/tiny-from-scratch-relation-experiment.md
scripts/create_nanochat_pretrain_shards.py
scripts/create_core5_curriculum_variants.py
scripts/create_core5_controlled_vocabulary_variants.py
scripts/create_core5_child_language_variants.py
scripts/create_core5_foundation_variants.py
scripts/create_procedural_foundation_world.py
scripts/create_procedural_foundation_world_v1.py
scripts/create_procedural_foundation_world_v2.py
scripts/create_procedural_foundation_world_v3.py
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

Core5 curriculum generation is now complete:

```text
experiment:       core5_v0
domains:          5
total examples:   3055
train/dev/test:   2428 / 296 / 331
held-out cases:   108
variants:         plain_text, relation_scaffolded, relation_first_then_text
report:           docs/core5-v0-curriculum-variants.md
```

Validation completed:

```text
python -m py_compile scripts/create_core5_curriculum_variants.py
training dry-run passed for all three variants
JSON manifests validated
held-out evaluation validated with expected merged-source warning
variant source IDs match for every split
```

Controlled-vocabulary core5 is also complete:

```text
experiment:       core5_v0_controlled
train/dev/test:   2428 / 296 / 331
variants:         controlled_plain_text, controlled_relation_scaffolded, controlled_relation_first_then_text
train vocabulary: 1367-1370 alpha words per variant
report:           docs/core5-v0-controlled-vocabulary.md
```

Child-language core5 remains the broader core5 candidate after smaller smoke
tests:

```text
experiment:       core5_v0_childlang
train/dev/test:   2428 / 296 / 331
variants:         child_plain_text, child_relation_scaffolded, child_relation_first_then_text
train vocabulary: 1342-1343 alpha words per variant
report:           docs/core5-v0-child-language.md
```

Foundation ladder is now the recommended prelude:

```text
experiment:       core5_v0_foundation
train/dev/test:   403 / 60 / 53
stages:           f0 facts, f1 handles, f2 handle questions, f3 later names
variants:         foundation_plain_text, foundation_relation_scaffolded, foundation_relation_first_then_text
train vocabulary: 92-93 alpha words per variant
report:           docs/core5-v0-foundation-ladder.md
```

Procedural foundation V0 is generated:

```text
experiment:       procedural_foundation_v0
train/dev/test:   2994 / 302 / 592
things:           28
states:           height, distance, action, surface
outcomes:         touch/no-touch, feel/no-feel, move/no-move
train vocabulary: 59-73 alpha words per variant
report:           docs/procedural-foundation-v0.md
```

Procedural foundation V1 replaces V0 as the quality seed:

```text
experiment:       procedural_foundation_v1
train/dev/test:   542 / 66 / 81
rule families:    reach/touch, push/move, drop/fall, shake/sound, hide/see,
                  container open/closed, hot/cold touch
train vocabulary: 79-106 alpha words per variant
report:           docs/procedural-foundation-v1.md
```

Procedural foundation V2 was the first expanded procedural candidate:

```text
experiment:       procedural_foundation_v2
train/dev/test:   2477 / 302 / 378
rule families:    V1 families plus support/edge/fall, same/different,
                  more/less, path open/closed, caregiver comfort,
                  word-name binding
question views:   main, what_happened, touch, feel, move, why_no_touch,
                  open_closed, block, cover, see, in_hand, more, less,
                  go_through, help, word_match, what_name
train vocabulary: 133-155 alpha words per variant
report:           docs/procedural-foundation-v2.md
status:           generated and validated; no model training run yet
```

Procedural foundation V3 is the current active procedural arm for the local nanochat smoke test:

```text
experiment:       procedural_foundation_v3
base entities:    208
train/dev/test:   4536 / 553 / 623
rule families:    baby body, reach/touch, push/pull, support/edge/fall,
                  container open/closed, hide/see, sound, hot/cold, wet/dry,
                  safe/unsafe, same/different, more/less, path open/closed,
                  caregiver comfort, familiar agent, social signal, give/take,
                  word-name binding
train vocabulary: 302-334 alpha words per variant
report:           docs/procedural-foundation-v3.md
status:           generated and validated; no model training run yet
```

TinyStories V0 is the normal simple-text control:

```text
experiment:       tinystories_v0
source:           roneneldan/TinyStories
train/dev/test:   1607 / 208 / 225 stories
word budget:      270421 / 33008 / 36695 words
variant:          tinystories_plain_text
report:           docs/tinystories-v0-baseline.md
status:           generated and validated; no model training run yet
```

The new design doc fixes the from-scratch experiment shape:

```text
same tiny nanochat model
same tokenizer
same token budget
same compute budget
four-arm comparison:
  normal simple text
  relation-designed plain text
  relation-scaffolded text
  relation-first text
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
Convert tinystories_v0 and procedural_foundation_v3 into nanochat-compatible
shards and run a small local four-arm smoke training pass with a shared
tokenizer.
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
1. Convert tinystories_v0 and procedural_foundation_v3 to nanochat-compatible shards. Done.
2. Use one shared tokenizer and identical model shape across all variants. Done.
3. Run a tiny four-arm local sanity. Done.
4. Inspect whether normal simple text, relation-designed plain text,
   relation_scaffolded, and relation_first_then_text train stably under equal
   conditions. Done for 20-step smoke.
5. Then repeat with core5_v0_foundation and core5_v0_childlang.
6. Move to one rented GPU only after local sanity passes.
```

Latest nanochat smoke result:

```text
report: docs/nanochat-core4-local-smoke-2026-04-29.md
run root: /tmp/adi_nanochat_core4_20260429_smoke
model: nanochat depth 2, 1966134 parameters
tokenizer: shared 4096-vocab BPE
training tokens per arm: 40960
tinystories_plain_text:                 3.014457 -> 2.894597 val BPB
procedural_plain_text:                  3.546736 -> 3.223261 val BPB
procedural_relation_scaffolded:         3.805675 -> 3.434072 val BPB
procedural_relation_first_then_text:    3.842853 -> 3.461918 val BPB
```

Latest depth-4 local result:

```text
run root: /tmp/adi_nanochat_core4_20260429_smoke
workspace copy: runs/nanochat_core4_20260429
model: nanochat depth 4, 7340162 parameters
training tokens per arm: 1024000
tinystories_plain_text:                 2.967028 -> 1.221640 val BPB
procedural_plain_text:                  3.621244 -> 0.150843 val BPB
procedural_relation_scaffolded:         3.769814 -> 0.057640 val BPB
procedural_relation_first_then_text:    3.777705 -> 0.062668 val BPB
next: held-out relation transfer evaluation against the depth-4 checkpoints
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
docs/procedural-foundation-v2.md
docs/procedural-foundation-v3.md
docs/procedural-foundation-v4-word-surface.md
docs/tinystories-v0-baseline.md
docs/nanochat-core4-local-smoke-2026-04-29.md
docs/nanochat-core4-heldout-evaluation-2026-04-29.md
docs/nanochat-core4-natural-heldout-evaluation-2026-04-29.md
docs/execution-roadmap.md
docs/experiment-log.md
```

Core graph/data:

```text
data/developmental_graph/core_curriculum_plan.json
data/developmental_graph/experiments/core5_v0/
data/developmental_graph/experiments/core5_v0_controlled/
data/developmental_graph/experiments/core5_v0_childlang/
data/developmental_graph/experiments/core5_v0_foundation/
data/developmental_graph/experiments/procedural_foundation_v0/
data/developmental_graph/experiments/procedural_foundation_v1/
data/developmental_graph/experiments/procedural_foundation_v2/
data/developmental_graph/experiments/procedural_foundation_v3/
data/developmental_graph/experiments/procedural_foundation_v4_word_surface/
data/developmental_graph/experiments/procedural_foundation_v5_consistent_qa/
data/developmental_graph/experiments/procedural_foundation_v5_consistent_qa_5k/
data/developmental_graph/experiments/tinystories_v0/
data/developmental_graph/seeds/agent_6mo_indian_child.json
data/developmental_graph/seeds/everyday_physical_world.json
data/developmental_graph/seeds/social_world.json
data/developmental_graph/seeds/math_abstraction.json
data/developmental_graph/seeds/language_binding.json
data/developmental_graph/evaluations/everyday_physical_world_heldout.json
data/developmental_graph/evaluations/social_world_heldout.json
data/developmental_graph/evaluations/math_abstraction_heldout.json
data/developmental_graph/evaluations/language_binding_heldout.json
data/developmental_graph/experiments/physical_v0_3/
```

Scripts for physical experiments:

```text
scripts/create_binary_candidate_experiment.py
scripts/create_nanochat_pretrain_shards.py
scripts/create_procedural_foundation_world_v4_word_surface.py
scripts/create_procedural_foundation_world_v5_consistent_qa.py
scripts/run_nanochat_relation_eval.py
scripts/run_nanochat_word_surface_eval.py
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
V5 relation-as-input or auxiliary-relation nanochat experiment
or Track B affect-relation scenarios
or physical_v0_4 relation-ranking repair
```

Current recommendation:

```text
V5 supersedes V4 for the proper-word nanochat run. V4 had about 36% ambiguous
prompts because identical inputs mapped to multiple target styles. V5 keeps the
same source world and record count, but has 0 ambiguous inputs and 0 shorthand
protocol hits.

Latest local result:
word_plain_qa, 4.39M parameter nanochat from scratch, 2.048M training tokens:
86.4% answer exact and 84.8% reason exact on 3115 held-out V5 plain prompts.

word_relation_scaffolded_qa, same model/token budget:
86.1% answer exact and 83.7% reason exact on the same held-out prompts.

Interpretation:
the proper-word procedural child-world dataset is trainable and gives a clean
baseline. This specific relation-scaffolded-output design did not beat plain
QA. Next relation experiment should avoid making the model emit relation
scaffolds at answer time; try relation-as-input, auxiliary relation prediction,
or a two-stage relation-pretrain then answer-only QA curriculum.

Detailed report:
docs/nanochat-v5-consistent-qa-local-run-2026-04-29.md

5K follow-up:
using only 5000 matched train records per variant, same model/tokenizer and
same 2.048M training tokens:

word_plain_qa:
86.1% answer exact and 82.7% reason exact.

word_relation_scaffolded_qa:
86.8% answer exact and 83.3% reason exact.

Interpretation:
relation scaffolding weakly helps when distinct training records are reduced,
but this still used the same token budget. Next test should use the same 5K
dataset with 250/500/1000 iterations to measure learning speed.

Detailed 5K report:
docs/nanochat-v5-consistent-qa-5k-local-run-2026-04-29.md

5K 250-iteration follow-up:
same 5K data and model, but only 512K training tokens:

word_plain_qa:
82.2% answer exact and 70.7% reason exact.

word_relation_scaffolded_qa:
74.5% answer exact and 55.8% reason exact.

Interpretation:
output-scaffolded relations do not help early learning in this form. They have
lower validation BPB but worse held-out QA, so BPB is being improved by learning
the repeated scaffold text rather than by better answer behavior.

Next recommended experiment:
5K relation-as-input with answer-only target, run at 250/500/1000 iterations.

Relation-as-input 250 result:
variant word_relation_input_qa prepends about 8 known/blocked relation lines to
the input and keeps output as answer/reason only.

Result:
81.9% answer exact and 59.9% reason exact on 3115 held-out relation-input
prompts.

Comparison at 5K/250:
plain QA: 82.2% answer, 70.7% reason.
relation-output QA: 74.5% answer, 55.8% reason.
relation-input QA: 81.9% answer, 59.9% reason.

Sequence check:
relation-input prompt+target max length was 149 tokens, under the 256-token
context, so the failure is not context truncation.

Updated recommendation:
relation-as-input is better than emitting relations, but all-relations input is
too noisy. Next try relation-candidate-input QA: provide only 3-5 candidate
relation anchors, including the correct reason anchor, output answer/reason
only, at 250 iterations.
```
