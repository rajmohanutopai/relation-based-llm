# Core Relation Curriculum Plan

Status: core5_v0 and procedural_foundation_v3 generated; nanochat smoke test pending.

Date: 2026-04-27

## Purpose

This document defines the first multi-domain relation curriculum for testing the
main claim:

```text
Small models should learn more efficiently when training exposes relation
structure directly, instead of forcing the model to infer all structure from
plain text alone.
```

The immediate goal is not to cover all human knowledge. The goal is to build a
controlled core curriculum large enough for a tiny from-scratch nanochat model
to learn something real, while still keeping the result interpretable.

Generated artifact:

```text
data/developmental_graph/experiments/core5_v0/
data/developmental_graph/experiments/core5_v0_controlled/
data/developmental_graph/experiments/core5_v0_childlang/
data/developmental_graph/experiments/core5_v0_foundation/
data/developmental_graph/experiments/procedural_foundation_v0/
data/developmental_graph/experiments/procedural_foundation_v1/
data/developmental_graph/experiments/procedural_foundation_v2/
data/developmental_graph/experiments/procedural_foundation_v3/
data/developmental_graph/experiments/tinystories_v0/
```

Current generated size:

```text
total examples: 3055
train: 2428
dev: 296
curriculum_test: 331
held-out cases: 108
```

Controlled vocabulary size:

```text
controlled train union: 1370 alpha words
controlled_plain_text train: 1367 alpha words
controlled_relation_scaffolded train: 1369 alpha words
controlled_relation_first_then_text train: 1370 alpha words
```

Child-language vocabulary size:

```text
child_plain_text train: 1342 alpha words
child_relation_scaffolded train: 1342 alpha words
child_relation_first_then_text train: 1343 alpha words
```

Foundation ladder size:

```text
train/dev/curriculum_test: 403 / 60 / 53
foundation train union: 93 alpha words
stages: f0 facts, f1 handle introduction, f2 handle questions, f3 later names
```

Procedural foundation size:

```text
train/dev/curriculum_test: 2994 / 302 / 592
total generated units: 3888
train vocabulary: 59-73 alpha words depending on variant
rule family: hand action + height + distance + touch/reach/move outcomes
```

Procedural foundation V1:

```text
train/dev/curriculum_test: 542 / 66 / 81
total generated units: 689
train vocabulary: 79-106 alpha words depending on variant
rule families: reach/touch, push/move, drop/fall, shake/sound, hide/see,
container open/closed, hot/cold touch
status: quality seed, needs expansion before training
```

Procedural foundation V2:

```text
train/dev/curriculum_test: 2477 / 302 / 378
total generated units: 3157
train vocabulary: 133-155 alpha words depending on variant
rule families: V1 families plus support/edge/fall, same/different, more/less,
path open/closed, caregiver comfort, word-name binding
status: historical expansion step; superseded by V3 for the active smoke test
```

Procedural foundation V3:

```text
train/dev/curriculum_test: 4536 / 553 / 623
total generated units: 5712
base entities: 208
train vocabulary: 302-334 alpha words depending on variant
rule families: baby body, reach/touch, push/pull, support/edge/fall,
container open/closed, hide/see, sound, hot/cold, wet/dry, safe/unsafe,
same/different, more/less, path open/closed, caregiver comfort, familiar agent,
social signal, give/take, word-name binding
status: current active procedural nanochat smoke-test candidate
```

TinyStories V0 baseline:

```text
train/dev/curriculum_test stories: 1607 / 208 / 225
train/dev/curriculum_test words: 270421 / 33008 / 36695
source: roneneldan/TinyStories
status: normal simple-text control for the procedural V3 comparison
```

## Core Test

Train the same nanochat model on matched corpora:

```text
A. normal_simple_text
B. relation_designed_plain_text
C. relation_scaffolded
D. relation_first_then_text
```

Keep fixed:

```text
same tokenizer
same model depth
same max sequence length
same token budget
same train/dev/held-out split policy
same optimizer settings
same evaluation prompts
```

Only the representation changes.

## Why Five Domains

The current repo already has two strong roots:

```text
1. six-month child root world
2. everyday physical world
```

Those are not enough for a meaningful from-scratch language model test. A model
trained only on those will mostly learn a small controlled physical dataset. It
will not test whether relation-first structure helps with the broader move from
root experience to abstraction and language.

The first serious core curriculum should include:

```text
1. 6mo root world
2. everyday physical world
3. simple social world
4. math/abstraction roots
5. language binding
```

This is still narrow. It intentionally excludes geography, history, law,
economics, politics, formal science, medicine, and metaphysics.

## Domain Readiness

### 1. 6mo Root World

Current status:

```text
raw 200 encounter families exist
top44 relation audit exists
maybe42 relation audit exists
parseable seed graph exists
```

Files:

```text
docs/6mo-child-200-encounters.md
docs/6mo-child-top44-relation-audit.md
docs/6mo-child-maybe42-relation-audit.md
data/developmental_graph/seeds/agent_6mo_indian_child.json
```

Role in curriculum:

```text
root grammar of meaning
input channels
body control
self/non-self boundary
comfort/discomfort
caregiver familiarity
object permanence precursor
action-effect learning
```

Do not treat this as the entire model world. It is the root layer.

### 2. Everyday Physical World

Current status:

```text
raw 200 situation families exist
first-set relation audit exists
parseable seed graph exists
held-out evaluation exists
multiple model-ready physical experiments exist
```

Files:

```text
docs/everyday-physical-world-200-situations.md
docs/everyday-physical-world-top50-relation-audit.md
data/developmental_graph/seeds/everyday_physical_world.json
data/developmental_graph/evaluations/everyday_physical_world_heldout.json
data/developmental_graph/experiments/physical_v0/
data/developmental_graph/experiments/physical_v0_1/
data/developmental_graph/experiments/physical_v0_2/
data/developmental_graph/experiments/physical_v0_3/
```

Role in curriculum:

```text
external object relations
material properties
cause/effect
counterfactual property shifts
thresholds
support, containment, motion, pressure, heat, sound
```

### 3. Simple Social World

Current status:

```text
raw 200 situation inventory exists
first-set relation audit exists
parseable seed graph exists and validates
held-out evaluation exists and validates
```

Required files:

```text
none
```

Existing files:

```text
docs/social-world-200-situations.md
docs/social-world-firstset-relation-audit.md
data/developmental_graph/seeds/social_world.json
data/developmental_graph/evaluations/social_world_heldout.json
```

Role in curriculum:

```text
other agents
attention
approval/disapproval
help/harm
turn-taking
imitation
trust
promise precursor
rule precursor
group belonging precursor
```

Why it is needed:

```text
Without social relations, later adult concepts like ethics, status, law,
politics, fairness, duty, and meaning in life cannot be traced back to simpler
relations.
```

### 4. Math And Abstraction Roots

Current status:

```text
raw 200 situation inventory exists
prioritisation pass complete
first-set relation audit exists
parseable seed graph exists and validates
held-out evaluation exists and validates
```

Required files:

```text
none
```

Existing files:

```text
docs/math-abstraction-200-situations.md
docs/math-abstraction-firstset-relation-audit.md
data/developmental_graph/seeds/math_abstraction.json
data/developmental_graph/evaluations/math_abstraction_heldout.json
```

Role in curriculum:

```text
same/different
one/many
more/less/equal
ordering
matching
mapping
grouping
part/whole
containment
sequence
repetition
invariance
composition
if/then
negation
```

Why it is needed:

```text
This tests the claim that abstraction is compressed relation structure.
```

Do not start with formal algebra. Start with the relation roots that make later
math meaningful.

### 5. Language Binding

Current status:

```text
raw 400 situation inventory exists
first prioritisation pass complete
relation audit generated
seed graph generated and validates
held-out evaluation generated and validates
```

Required files:

```text
none
```

Existing files:

```text
docs/language-binding-400-situations.md
docs/language-binding-firstset-relation-audit.md
data/developmental_graph/seeds/language_binding.json
data/developmental_graph/evaluations/language_binding_heldout.json
```

Role in curriculum:

```text
sound pattern -> word handle
written symbol -> word handle
word handle -> relation cluster
modifier -> property relation
sentence -> event relation
story -> temporal/causal relation chain
metaphor -> relation transfer
```

Important rule:

```text
Language is not the first source of meaning in this curriculum. Language binds
to relation structures that already exist.
```

## Shared Root Relations

All five domains should reuse the same root relation grammar:

```text
same/different
similar/dissimilar
more/less/equal
before/after
during
starts/stops
repeats
persists/changes
near/far
inside/outside
touching/separate
supported/unsupported
open/closed
path blocked/unblocked
direct control
indirect effect
cause/effect
expected/unexpected
threshold
part/whole
group/member
attention/absence
comfort/discomfort
pain/relief
approach/avoid
```

Domain-specific concepts should be traceable back to these roots.

Example:

```text
status =
  attention + priority + compliance + approval + future access
```

Example:

```text
number =
  same/different + one/many + matching + grouping + order + invariance
```

Example:

```text
word meaning =
  stable symbol handle + repeated activation of a relation cluster
```

## Training Unit

Each model-ready unit should contain the same underlying content rendered three
ways.

Canonical internal shape:

```json
{
  "id": "core5.social.turn_taking.0001",
  "domain": "social_world",
  "stage": "core5_v0",
  "source_observation": "A child gives a toy, waits, and receives it back.",
  "relation_packet": [
    {
      "source": "agent.child",
      "relation": "gives_object_to",
      "target": "agent.other_child"
    }
  ],
  "root_relations": ["before_after", "turn_taking", "self_other"],
  "expected_transfer": ["sharing", "reciprocity", "waiting"],
  "heldout_tags": ["social_transfer", "sequence", "reciprocity"]
}
```

The exact JSON schema can be added later. The important point is that the same
unit must render into all variants.

## Representation Variants

### A. plain_text

The model sees only ordinary text.

Example:

```text
A baby shakes a rattle. The rattle moves and makes a sound. The baby hears the
sound and may shake again.
```

Purpose:

```text
baseline normal language pretraining
```

### B. relation_scaffolded

The model sees text plus explicit relation structure.

Example:

```text
SCENE:
A baby shakes a rattle.

RELATIONS:
baby_hand -> direct_control -> hand_motion
hand_motion -> causes -> rattle_motion
rattle_motion -> causes -> sound
sound -> detected_by -> hearing
repeated_effect -> strengthens -> action_effect_prediction

TEXT:
The baby learns that moving the hand can make the rattle sound.
```

Purpose:

```text
test whether explicit relation scaffolding improves learning
```

### C. relation_first_then_text

The model sees the relation packet before the ordinary text.

Example:

```text
RELATION_PACKET:
controllable_body_part -> action -> external_effect
external_effect -> sensory_input -> prediction_update
repeated_prediction_success -> relation_strengthening

TEXT_BINDING:
A baby learns that shaking a rattle makes sound.
```

Purpose:

```text
test the sharper version of the theory:
learn relation structure first, then attach language to it
```

## Domain Examples

### 6mo Root World

Plain:

```text
A baby moves his hand and sees the hand move. When he touches the cloth, he
feels contact. When he moves the hand again, the cloth may move.
```

Relation-scaffolded:

```text
hand -> direct_control -> hand_motion
hand_motion -> changes -> visual_hand_position
hand + cloth_contact -> causes -> touch_pressure
hand_motion + contact -> can_cause -> cloth_motion
```

Relation-first:

```text
RELATION_PACKET:
motor_command -> reliable_body_change -> direct_control
body_contact -> touch_input -> body_boundary
body_action + external_contact -> external_effect

TEXT_BINDING:
The baby learns that the hand is part of the controllable self and that touching
cloth can move the cloth.
```

### Everyday Physical World

Plain:

```text
A rubber ball may bounce after hitting the floor because it deforms and then
returns toward its old shape.
```

Relation-scaffolded:

```text
rubber -> has_property -> elastic
falling_object + floor_contact -> causes -> impact
elastic_object + impact -> causes -> deformation
deformation + elastic_recovery -> causes -> bounce
```

Relation-first:

```text
RELATION_PACKET:
impact -> deformation
elastic_material -> shape_recovery
shape_recovery + contact_surface -> rebound_motion

TEXT_BINDING:
A rubber ball bounces because impact deforms it and elasticity makes it recover
shape.
```

### Simple Social World

Plain:

```text
A caregiver smiles and speaks gently. The child becomes calm and looks toward
the caregiver.
```

Relation-scaffolded:

```text
caregiver_voice -> has_property -> gentle_tone
gentle_tone -> predicts -> low_threat
familiar_face -> activates -> caregiver_relation
caregiver_relation + low_threat -> increases -> comfort
```

Relation-first:

```text
RELATION_PACKET:
familiar_agent -> predicts -> care
gentle_signal -> reduces -> threat_prediction
reduced_threat -> increases -> comfort

TEXT_BINDING:
The child feels comfort when a familiar caregiver speaks gently.
```

### Math And Abstraction Roots

Plain:

```text
Two red blocks match because their color is the same. A red block and a blue
block do not match in color.
```

Relation-scaffolded:

```text
block_1 -> has_color -> red
block_2 -> has_color -> red
block_3 -> has_color -> blue
red -> same_as -> red
red -> different_from -> blue
same_property -> supports -> matching
different_property -> blocks -> color_match
```

Relation-first:

```text
RELATION_PACKET:
object_a.property_x == object_b.property_x -> match_on_property
object_a.property_x != object_b.property_y -> contrast_on_property

TEXT_BINDING:
Two red blocks match in color. A red block and a blue block do not match in
color.
```

### Language Binding

Plain:

```text
The word ball is used for round things that can roll or bounce.
```

Relation-scaffolded:

```text
word.ball -> labels -> concept.ball
concept.ball -> has_property -> round
concept.ball -> affords -> rolling
concept.ball -> may_afford -> bouncing
round + push + surface -> causes -> roll
elastic + impact -> causes -> bounce
```

Relation-first:

```text
RELATION_PACKET:
round_shape + push -> rolling_motion
elastic_body + impact -> bouncing_motion
stable_cluster(round, roll, bounce) -> concept_handle

TEXT_BINDING:
The word ball points to this relation cluster.
```

## Data Volume Ladder

Start small, but not as small as the first smoke test.

### Level 0: Smoke

Already done with physical data only.

```text
purpose: verify nanochat path
model: depth 2
tokens: ~40K per run
result: pipeline works, not a theory result
```

### Level 1: Core5 Local Sanity

```text
domains: 5
base units: 50 to 100 per domain
rendered docs: 500 to 2000 per domain after template variation
target tokens: 0.5M to 2M
model: depth 4 or 5
purpose: check fitting and format stability
```

### Level 2: One-GPU Signal Test

```text
domains: 5
base units: 200+ per domain
rendered docs: 5000+ per domain after variation
target tokens: 10M to 50M
model: depth 5 to 8
purpose: compare held-out transfer per token
```

### Level 3: Stronger Small Model

```text
domains: 5 plus carefully selected general text
target tokens: 100M+
model: depth 8 to 12
purpose: decide whether relation-first scaling is worth GPU spend
```

## Evaluation

Evaluation must be built before the serious run.

Required held-out probes:

```text
1. relation recall
2. unseen object/property transfer
3. counterfactual relation shift
4. false relation rejection
5. root-trace explanation
6. language-to-relation binding
7. relation-to-language generation
8. cross-domain transfer
```

Examples:

```text
If a soft rubber toy hits the floor, what relations explain its motion?
```

Expected:

```text
impact -> deformation
elasticity -> shape recovery
shape recovery -> rebound or bounce
```

Example:

```text
Why is a promise different from a sound?
```

Expected:

```text
promise = agent + future action + expectation + trust + violation consequence
sound = sensory event + source + duration + loudness
```

Example:

```text
Why does the word "ball" still work for a blue ball?
```

Expected:

```text
color is not core to ball relation cluster
roundness and roll/bounce affordances are more central
```

## Success Criteria

A result is useful only if relation-aware training improves held-out transfer.

Useful signal:

```text
relation_first_then_text beats plain_text on held-out transfer with the same
token budget and same tokenizer
```

Weak signal:

```text
relation_scaffolded fits faster but does not transfer better
```

Not useful:

```text
the model only copies relation IDs
the model only learns JSON shape
the relation model wins because it had a different tokenizer
the relation model wins because it saw more content
```

## Immediate Build Order

1. Freeze this plan.
2. Create the missing simple social-world raw 200 situations. Done.
3. Audit first-set social situations into relation families. Done.
4. Create `social_world.json` seed graph. Done.
5. Create social-world held-out evaluation. Done.
6. Create math/abstraction raw 200 situations. Done.
7. Prioritise math/abstraction raw situations. Done.
8. Audit first-set math situations into relation families. Done.
9. Create `math_abstraction.json` seed graph. Done.
10. Create math-abstraction held-out evaluation. Done.
11. Create language-binding raw 400 situations. Done.
12. Prioritise language-binding raw situations. Done.
13. Audit first-set language-binding situations into relation families. Done.
14. Create `language_binding.json` seed graph and held-out evaluation. Done.
15. Add a cross-domain core5 curriculum generator. Done.
16. Add `relation_first_then_text` rendering. Done.
17. Validate matched source examples across all variants. Done.
18. Add controlled-vocabulary core5 rendering. Done.
19. Add child-language core5 rendering. Done.
20. Add staged foundation ladder. Done.
21. Add first procedural relation-world generator. Done.
22. Replace rough procedural generator with coherent scenario grammar. Done.
23. Expand procedural V1 with derived questions and more rule families.
24. Add shared tokenizer procedure for nanochat.
25. Run Level 1 procedural/foundation local sanity, then child-language local sanity.
26. Only then run the first one-GPU signal test.

## Do Not Do Yet

Do not add:

```text
history
geography
law
economics
politics
medicine
formal science
metaphysics
custom transformer architecture
external memory
happiness objective
RL
```

Those are future phases. The first serious test should stay focused on the
smallest curriculum that includes body, world, other agents, abstraction roots,
and language binding.
