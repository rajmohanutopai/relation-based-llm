# Developmental Relation Graph

Status: first project structure for the relation-first SLM idea.

Related note: `docs/information-cognition-abstraction-theory.md`

First concrete seed instance: `docs/seed-agent-6mo-indian-child.md`

## Purpose

This document defines a proposed structure for a "developmental relation graph":
a layered graph that starts from the simplest human-like input channels and
builds progressively toward object concepts, event concepts, social concepts,
language, mathematics, and higher abstractions.

The goal is not to replace transformer learning. The goal is to give a small
model a supporting hand so it does not need to rediscover every useful relation
from raw text alone.

The central hypothesis is:

> A small language model can learn more efficiently if training data makes the
> developmental construction of relations explicit: simple input relations first,
> then object and event relations, then social and abstract relations, then
> language as labels over those relation structures.

## What This Is Not

This is not a flat knowledge graph like ConceptNet.

ConceptNet says things such as:

```text
knife --UsedFor--> cutting
knife --HasProperty--> sharp
ball --HasProperty--> round
```

That is useful, but it skips the lower structure.

This graph tries to represent why those relations matter:

```text
sharp edge + pressure + soft material -> separation
sharp edge + pressure + skin -> pain/injury
round object + push + low friction -> rolling motion
elastic object + impact -> bounce
```

This is also not a full hand-built ontology where every concept is permanently
forced into one rigid schema. It is a training scaffold. The transformer should
still learn from ordinary text. The graph is a curriculum and auxiliary
supervision layer.

## Core Principle

There are very few primitive input channels, but there are many primitive
relations extracted from those channels.

The input channels are the model's simulated "eyes and ears." They are not yet
knowledge.

Knowledge begins when the system detects stable relations across input states:

- this changed when I acted
- this stayed the same
- this came before that
- this caused pain
- this object moved after contact
- this pattern repeated
- this object is similar to that one
- this object is different from that one
- this part is directly controllable
- this part is only indirectly affectable

Concepts are then compressed, reusable clusters of such relations.

## Layer Overview

```text
Layer -1: input channels
Layer  0: relational invariants
Layer  1: sensorimotor schemas
Layer  2: property relations
Layer  3: object concepts
Layer  4: event and affordance concepts
Layer  5: agent and self/other concepts
Layer  6: social concepts
Layer  7: language binding
Layer  8: logical and mathematical abstractions
Layer  9: meta-abstractions
```

Higher layers are not separate substances. They are stable structures built from
lower-layer relations.

## Layer -1: Input Channels

These are the primitive data channels. They are not concepts yet.

### Visual Channel

Raw source for:

- brightness
- color
- outline
- shape
- size
- position
- distance
- motion
- continuity
- disappearance and reappearance

### Sound Channel

Raw source for:

- loudness
- pitch
- rhythm
- suddenness
- duration
- direction/source
- impact sounds
- voice-like sounds

### Touch Channel

Raw source for:

- contact
- pressure
- texture
- temperature
- vibration
- deformation
- resistance
- slip
- wetness/dryness

### Chemical Channel

This combines taste and smell for the first version.

Raw source for:

- sweet/bitter/sour/salty
- freshness/rot
- edible/non-edible cues
- irritation
- attraction/aversion

### Proprioception and Control Channel

Raw source for:

- body position
- joint change
- motor command
- effort
- controllability
- action intention
- body boundary

### Valence Channel

This includes primitive bodily value signals.

Raw source for:

- pain
- pleasure
- hunger/satiety
- fatigue/relief
- startle
- comfort/discomfort

Fear, anger, pride, guilt, laziness, and status are not primitive here. They are
higher concepts built from valence, prediction, agency, social reaction, and
future consequence.

## Layer 0: Relational Invariants

Layer 0 contains the first real information-bearing relations. These are
relations that can be extracted by comparing input states over time.

### Comparison Relations

```text
same_as
different_from
similar_to
more_than
less_than
equal_to
```

These are not high-level logical ideas at first. They are low-level comparisons:
brighter/darker, louder/softer, more pressure/less pressure, same object/different
object.

### Temporal Relations

```text
before
after
during
starts
stops
repeats
persists
changes
```

These arise from sequential observation.

### Spatial Relations

```text
near
far
inside
outside
above
below
left_of
right_of
in_front_of
behind
touching
separate_from
contained_by
supporting
unsupported
```

Spatial relations come mostly from sight, touch, and proprioception.

### Change Relations

```text
appears
disappears
moves
deforms
breaks
joins
separates
opens
closes
increases
decreases
```

These are the foundation of event understanding.

### Action-Control Relations

```text
commanded_by_self
directly_controlled
indirectly_affected
not_controlled
predictably_moves_with_command
resists_command
```

These are the foundation of self/non-self.

### Valence Relations

```text
causes_pain
reduces_pain
causes_pleasure
reduces_discomfort
requires_effort
causes_startle
causes_relief
positive_activation
connection_gain
connection_loss
positive_saturation
direct_valence_shortcut
```

These are not moral concepts. They are primitive value changes.

Comfort is not identical to happiness. Comfort is relief or stabilization of
body state. Happiness has two project-level mechanisms:

```text
existing positive relation activation:
  current cue activates already learned positive relation clusters

new useful relation formation:
  new relation is created or strengthened
```

These mechanisms need a saturation modifier:

```text
if relation_strength is already high:
  repeated activation gives comfort/maintenance
  additional happiness gain decreases

if activation also creates new useful links:
  happiness can increase again
```

This is important for modeling escalation. A child may stop laughing at the
same repeated trick unless the trick changes. An adult may seek higher status,
greater novelty, stronger intensity, or a more selective audience because the
old connection is already saturated. In the harmful limit, hard drugs or other
direct shortcuts can activate positive valence without building useful relation
structure. That creates high immediate activation but weak long-term relational
growth, and can weaken ordinary sources of happiness by comparison.

For training, the affect signal should therefore be closer to:

```text
happiness_delta =
  positive_relation_activation
  + useful_connection_gain * (1 - current_relation_strength)
  - connection_loss
  - harmful_shortcut_penalty
```

Sadness begins as blocked or lost expected positive relation activation. Later,
grief is modeled as large-scale loss of a dense relation network.

### Prediction Relations

```text
expected
unexpected
predicts
violates_prediction
uncertain
reliable
unreliable
```

These become the basis for surprise, attention, trust, skepticism, and learning.

## Layer 1: Sensorimotor Schemas

Sensorimotor schemas are stable relational patterns built from Layer 0.

They are still simple and pre-linguistic.

### Contact Schema

```text
two objects become touching
pressure may increase
motion may transfer
sound may occur
pain may occur if one object is body/self
```

### Impact Schema

```text
object moves
object contacts another object
motion changes suddenly
sound occurs
deformation or break may occur
pain may occur if body involved
```

### Support Schema

```text
object is above supporting surface
object remains stable
support removed -> object falls
```

### Fall Schema

```text
object unsupported
object moves downward
impact follows
sound/deformation/bounce/break may follow
```

### Pressure Schema

```text
force/contact increases
object resists or deforms
body may feel pain if pressure is high
```

### Deformation Schema

```text
pressure applied
shape changes
shape may return or remain changed
```

### Break Schema

```text
impact/pressure exceeds tolerance
object continuity is lost
parts separate
sharpness and danger may increase
usefulness may decrease
```

### Cut Schema

```text
sharp object contacts softer object
pressure/motion applied along edge
target separates
if target is body -> pain/injury
```

### Burn Schema

```text
hot object/substance contacts body or material
pain/damage or transformation follows
```

### Containment Schema

```text
object inside boundary
boundary restricts movement
opening allows movement in/out
```

### Path Schema

```text
object starts at source
moves through intermediate positions
ends at goal/location
obstacles may block path
```

### Self-Motion Schema

```text
motor command issued
body part changes position predictably
proprioception changes
visual/touch changes match command
```

This schema is the foundation of "this is my body."

### Body Orientation and Balance Schemas

```text
body_orientation_change:
  rolling or assisted movement changes body position
  visual field, pressure, and proprioception change together

posture_support:
  hands, caregiver, lap, floor, cushion, or surface supports body
  supported body position remains more stable

balance_instability:
  support weakens or center of mass shifts
  body tilts or falls
  pain, startle, or caregiver catch may follow
```

These are needed before abstractions such as stability, falling, caution,
capability, effort, and bodily confidence.

### Feeding Start, Feeding Completion, and Spoon Approach

```text
feeding_relief:
  hunger/discomfort -> feeding -> satiety/relief

feeding_completion:
  satiety/fullness -> reduced interest
  turn away / close mouth -> feeding slows or stops

spoon_approach_mouth:
  caregiver-controlled object approaches mouth
  mouth contact brings taste, texture, temperature, or refusal
```

Starting feeding and stopping feeding are different relation patterns. The first
is relief-seeking; the second is regulation and refusal.

### Bath and Water Contact

```text
bath_water_contact:
  water touches body
  water temperature is felt
  body becomes wet
  caregiver support and routine shape comfort/discomfort
```

This should be separate from wet diaper. Wet diaper is usually discomfort, while
bath water can be positive, neutral, negative, or startling depending on
temperature and handling.

### Push-Roll Schema

```text
round object on surface
push or release occurs
object changes position by rolling
```

This makes the ball relation explicit: roundness is not just shape; it predicts
a motion pattern under action.

### Face Proximity Attention

```text
familiar face moves close
eyes, mouth, expression, and voice become salient
attention shifts to face
comfort/arousal may change
```

This is a social visual precursor, not an abstract person concept.

### Open-Close Boundary

```text
door/curtain/boundary changes open/closed state
sound may occur
person/object/room may appear or disappear
attention shifts toward boundary
```

Door and boundary events are useful because they combine visual change, sound,
appearance/disappearance, and later social expectation.

### Caregiver Safety Blocking

```text
baby reaches/mouths/moves toward object or place
caregiver blocks, removes object, or changes baby position
intended action stops or redirects
frustration may increase
```

This is not morality. It is a precursor to danger, permission, prohibition,
rule, and later social norms.

### Illness, Medical Care, and Exploration Readiness

```text
medical_pain_care:
  unfamiliar care setting/adult + medicine/vaccination/exam
  discomfort or pain may occur
  primary caregiver repairs comfort

illness_discomfort:
  feverishness / blocked breathing / tiredness / unusual fussiness
  exploration decreases
  care need increases

comfort_exploration_readiness:
  body needs are regulated
  attention opens
  play/exploration/new relation gain becomes easier
```

Comfort is not happiness, but comfort changes the probability of exploration and
therefore supports later happiness from new connection formation.

### Regulation, Orienting, and Early Binding Schemas

These schemas fill practical early-world gaps without introducing adult
abstractions too early.

```text
wake_transition:
  sleep state changes toward waking
  sound/light/movement/temperature/hunger/internal discomfort may trigger waking
  familiar context can stabilize the transition

stimulation_regulation:
  sound/light/movement/touch/activity intensity changes arousal
  too much input can decrease comfort
  reduced stimulation can support calming or sleep

feeding_interruption_delay:
  expected feeding relief pauses or is delayed before satiety
  discomfort/frustration may increase

internal_discomfort_gas:
  internal pressure/gas/burping discomfort changes body valence
  caregiver holding, posture, or time may change state

orienting_to_sound_motion:
  salient sound or motion occurs
  head/eyes/attention turn toward source

carry_context_transition:
  caregiver moves body through place/room contexts
  visual scene and body orientation change without direct control

light_change:
  brightness/darkness changes
  attention, wakefulness, or comfort may change

mirror_reflection:
  visual image moves with similarity/contingency
  no direct touch/proprioception comes from the image itself

unfamiliar_agent_approach:
  lower familiarity plus approach changes prediction confidence
  comfort, attention, or uncertainty may change

other_cry_arousal:
  distress-like sound from another child changes arousal

routine_word_action:
  repeated word sound co-occurs with action routines
  the action sequence gives the sound a weak temporal anchor

picture_word_exposure:
  picture/image plus caregiver speech plus joint attention
  begins a weak word-to-relation binding

object_removal_frustration:
  expected access to object stops
  blocked access may increase frustration
```

This is the relation-first version of early experience: the word or object
label is not primary. The relation pattern is primary; language can bind to it
later.

## Layer 2: Property Relations

Properties are summaries of how objects behave across sensorimotor schemas.

A property is not a label. It is a predictive relation.

### Shape Properties

```text
roundness:
  visual outline is circular/curved
  rolling is likely when pushed
  orientation matters less

flatness:
  has broad surface
  stable support is likely
  stacking may be possible

pointedness:
  small contact area
  pressure concentrates
  puncture/pain risk increases
```

### Material/Resistance Properties

```text
hardness:
  resists deformation under pressure
  can cause pain on impact

softness:
  deforms under pressure
  usually lower impact pain

squishiness:
  deforms substantially under pressure
  may return shape after release

elasticity/bounciness:
  impact stores and returns motion
  object rebounds after falling/contact

fragility:
  breaks under impact/pressure
  continuity loss likely
```

### Surface Properties

```text
smoothness:
  low texture variation
  lower friction

roughness:
  high texture variation
  higher friction

sharpness:
  small edge/contact area
  cut/puncture/pain risk
```

### Weight and Force Properties

```text
heaviness:
  requires more effort to lift
  impact sound/force higher
  harder to move

lightness:
  requires less effort
  moves easily
  impact lower
```

### Temperature Properties

```text
hotness:
  touch may cause pain/damage
  distance cues may exist

coldness:
  touch changes comfort/pain
  may change material behavior
```

### Food and Body-State Properties

```text
fullness:
  satiety after feeding
  reduced feeding interest
  turning away or closing mouth may follow

food_texture:
  mouth touch + taste/smell
  smooth/lumpy/sticky/warm/cool input

food_familiarity:
  repeated taste/smell/texture
  prediction and acceptance may change

wet_body:
  body wetness from bath, cleaning, sweat, or spill
  valence depends on temperature and context

water_temperature:
  water touch temperature
  comfort/discomfort changes with intensity

feverishness:
  unusual body heat
  discomfort/low energy/care need

blocked_breathing:
  blocked nose or breathing discomfort
  sleep/play disruption

gas_discomfort:
  internal pressure or stomach discomfort
  cry/fuss/body movement may follow

bright_light:
  high visual brightness
  can increase attention/wakefulness or discomfort depending on intensity

darkness:
  low visual brightness
  can support sleep context or uncertainty depending on other cues

overstimulating:
  too much sound/light/motion/touch/activity for current regulation state
  comfort decreases and attention becomes unstable
```

### Social Visual and Safety Properties

```text
familiar_face:
  repeated caregiver face pattern
  eyes/mouth/expression
  predicts attention and familiar care

smiling_face:
  familiar or friendly eyes/mouth expression
  predicts play, approach, or comfort more often than threat

unsafe_object:
  caregiver blocks access
  possible choking/pain/contamination/break risk
```

### Value/Risk Properties

```text
dangerous:
  predicts pain/damage/loss
  increases avoidance/caution

safe:
  low predicted pain/damage under normal interaction

useful:
  reliably enables desired effect

pleasant:
  predicts positive valence
```

## Layer 3: Object Concepts

An object concept is a weighted cluster of property relations, action relations,
and expected event outcomes.

It is not a definition. It is a prototype distribution with flexible boundaries.

### Example: Ball

```text
concept: ball
relations:
  has_shape.roundness = high
  has_property.bounciness = medium_to_high
  has_property.squishiness = low_to_medium
  has_property.hardness = low_to_medium
  action.push -> effect.roll = high
  action.drop -> effect.bounce = medium_to_high
  action.catch -> possible = high
  action.throw -> possible = high
  impact.body -> pain_risk = low_to_medium
  category.toy_or_sports_object = common
contrasts:
  stone: less_bouncy, harder, higher_pain_on_impact
  sponge: more_squishy, less_bouncy, less_roll_stability
  slime: less_stable_shape, less_object_boundary
```

A ball can be somewhat squishy, but if squishiness becomes too high and stable
roundness/rolling/bouncing becomes too low, the object moves toward sponge/slime
rather than ball.

This boundary is not a rule. It is a shift in relation strengths.

### Example: Knife

```text
concept: knife
relations:
  has_part.blade = typical
  has_part.handle = typical
  blade.has_property.sharpness = high
  handle.has_property.safe_grip = high
  action.apply_blade_with_pressure -> effect.cut = high
  blade + skin + pressure -> pain/injury = high
  location.kitchen = common
  used_for.cut_food = common
contrasts:
  spoon: lower_sharpness, lower_cutting_ability
  sword: larger, weapon_use_higher
  razor: finer_edge, shaving_use_higher
```

### Example: Pen

```text
concept: pen
relations:
  has_shape.long_thin = high
  used_for.writing = high
  action.drop -> sound = small_to_medium
  action.drop -> damage = usually_low
  action.press_tip_on_surface -> mark = high
  pain_risk = low
```

### Example: Glass Cup

```text
concept: glass_cup
relations:
  material.glass = high
  has_property.fragility = high
  has_property.transparency = medium_to_high
  used_for.holding_liquid = high
  action.drop -> sound = loud
  action.drop -> break = high
break -> sharp_fragments = high
sharp_fragments + touch -> pain/injury = high
```

### Early Developmental Handles

These are not yet mature concepts. They are weak handles for common encounter
families that later grow into object, place, social, and language concepts.

```text
other_child:
  other agent-like body/voice
  cry/laugh/play sounds affect arousal

book_picture:
  flat visual image
  supports picture-word exposure through joint attention

mirror:
  reflective surface
  supports visual same/different and contingency relations

feeding_setup:
  bowl/spoon/bottle/cloth/caregiver routine
  predicts feeding relief or feeding action

kitchen_appliance_sound:
  loud household sound
  can startle or shift attention

room_place:
  recurring visual/touch/sound context
  supports carried context transition

routine_word:
  repeated household sound pattern
  co-occurs with action routines

object_name_sound:
  repeated naming sound
  co-occurs with joint attention to object/picture
```

## Layer 4: Events and Affordances

An event concept is an action/change schema with participants, conditions,
effects, and expected valence.

### Event Template

```text
event:
  agent:
  object:
  action:
  preconditions:
  effect:
  side_effect:
  valence:
  confidence:
```

### Drop Event

```text
event: drop
preconditions:
  object is held/supported
  support is removed
relations:
  object moves downward
  object impacts surface
effects_by_property:
  bouncy object -> bounce
  fragile object -> break
  heavy object -> louder sound / higher damage
  soft object -> lower sound / deformation
```

### Push Event

```text
event: push
preconditions:
  contact with object
  force applied
effects_by_property:
  round object -> roll
  heavy object -> little motion / high effort
  sliding object -> translation
  fixed object -> resistance
```

### Squeeze Event

```text
event: squeeze
preconditions:
  object grasped/contacted
  pressure applied
effects_by_property:
  squishy object -> deformation
  hard object -> resistance
  fragile object -> break risk
  sharp object -> pain risk
```

### Eat Event

```text
event: eat
preconditions:
  object is edible or treated as food
  object enters body
effects:
  taste occurs
  hunger may reduce
  pleasure/disgust may occur
  poison/illness risk for bad food
```

## Layer 5: Self, Agency, and Other Minds

The self is not a primitive label. It is built from control, prediction, direct
sensation, and body continuity.

### Self/Body Concept

```text
self_body:
  motor_command -> predictable movement
  touch_on_part -> direct sensation
  damage_to_part -> pain
  visual_motion matches proprioception
  continuity across time
```

### External Object Concept

```text
external_object:
  not directly controlled by motor command
  can be indirectly affected through contact/tool/action
  may affect self through contact
  persists independently
```

### Agent Concept

An agent is inferred when an external object behaves like a self from its own
point of view.

```text
agent:
  initiates action
  pursues goal-like state
  avoids pain/damage
  responds to obstacles
  has attention direction
  can affect self and other objects
```

### Goal Concept

```text
goal:
  predicted desired future state
  action sequence selected toward state
  obstacles cause effort/frustration
  success causes relief/pleasure
```

### Emotion Foundations

Emotions are not primitives here. They are compressed predictions and value
patterns.

```text
fear:
  predicted pain/loss
  uncertainty or threat
  avoidance/readiness

anger:
  goal blocked or harm caused
  agent attribution likely
  action tendency toward correction/confrontation

sadness:
  loss of valued relation
  reduced expected future reward
  low action energy

surprise:
  prediction violation
  attention increases
```

### Happiness Saturation and Escalation

Happiness is not linear in repeated reward. Once a relation is strong, repeating
the same activation mostly maintains comfort or confidence. It does not keep
creating the same amount of happiness.

```text
first discovery:
  weak relation becomes strong -> large connection_gain -> happiness

repetition after learning:
  strong relation reactivates -> comfort/positive_activation -> smaller gain

escalation:
  agent seeks new relation, stronger intensity, broader scope, or higher-level
  audience to create additional gain
```

This also explains a social pattern from Chapter 09. Society teaches that money,
respect, success, ethics, belonging, or achievement are happiness-linked. But if
one reward relation saturates, the person may climb to a higher reference group:
respect from family becomes insufficient, then respect from peers, then respect
from experts, then legacy after death. The person thinks happiness lies ahead,
but part of the mechanism is that each previous relation has lost marginal
power.

This should be represented as a relation-strength curve, not as a moral defect.
The same mechanism powers healthy exploration, learning, art, science, ambition,
and harmful addictive escalation.

## Layer 6: Social Concepts

Social abstractions must be built from lower relations. They should not be
declared as primitives.

### Ownership

```text
ownership:
  object is controlled/used by agent
  agent expects continued access
  others recognize access boundary
  violation causes conflict/disapproval
```

### Trust

```text
trust:
  agent prediction reliability is high
  promises/actions match outcomes
  expected harm is low
  cooperation risk decreases
```

### Fairness

```text
fairness:
  agents receive comparable outcome under comparable condition
  effort/reward relation is balanced
  rule application is consistent
  violation causes anger/disapproval
```

### Status

Status is not a primitive.

```text
status:
  others allocate more attention to agent
  others comply more often with agent requests
  agent gets priority in resource/conflict decisions
  agent's approval/disapproval changes others' behavior
  status loss predicts pain/shame/fear
  status gain predicts reward/pride/security
```

Status is a compressed graph over attention, compliance, resource access,
approval, and prediction of future treatment.

### Laziness

Laziness is not a primitive trait.

```text
laziness:
  agent has capability to act
  action has effort cost
  action is expected/obligatory/useful
  agent avoids or delays action
  short_term_comfort increases
  long_term_cost or social_disapproval increases
contrasts:
  tiredness: capability/energy is reduced
  illness: action capacity is impaired
  rest: obligation may be absent or recovery is useful
  strategic_delay: delay improves future outcome
```

This structure lets the model distinguish:

```text
sick person not working -> not laziness
exhausted person resting -> not laziness
capable person avoiding necessary effort -> laziness
```

### Responsibility

```text
responsibility:
  agent action caused outcome
  agent could predict outcome to some degree
  future behavior can be changed by reward/punishment/social response
  responsibility attribution changes future decision calculations
```

### Justice

```text
justice:
  social response to action/outcome
  modifies future incentives
  stabilizes group expectations
  balances harm, intent, predictability, and prevention
```

## Layer 7: Language Binding

Language should attach to existing relation structures. It should not be the
first source of meaning.

### Reading Ladder

```text
visual marks -> character identity
character sequence -> word form
word form -> concept handle
concept handle -> relation cluster
sentence syntax -> relation composition
discourse context -> relation selection
```

### Example: "Ball"

```text
letters: b a l l
word_form: ball
binds_to:
  concept.ball relation cluster
```

### Example: "The glass fell and broke"

```text
text:
  The glass fell and broke.

relation parse:
  object = glass_cup
  event1 = fall
  event2 = break
  cause_relation = fall/impact -> break
  implied_properties:
    fragility high
    impact likely
    sharp_fragment_risk possible
```

### Example: "He was lazy"

```text
text:
  He was lazy.

relation parse:
  agent = he
  expected_action = implied by context
  capability = assumed unless contradicted
  effort_cost = present
  avoidance/delay = present
  moral/social evaluation = negative unless context changes
```

Language training should include cases where context changes the relation:

```text
He did not work because he had fever. -> illness, not laziness.
He did not work because he wanted to avoid effort. -> laziness.
He rested after finishing the task. -> recovery/rest, not laziness.
```

## Layer 8: Logical and Mathematical Abstractions

Mathematical concepts are not sensory objects, but they are still relation
structures. They can be built from invariants such as sameness, difference,
order, repetition, matching, grouping, transformation, and preservation.

### Number

```text
number:
  abstraction over collections
  stable under object identity change
  based on one-to-one matching and repetition
```

### Two

```text
two:
  one object + one object
  successor_of one
  predecessor_of three
  can be matched one-to-one with any pair
  invariant across object type
```

### Addition

```text
addition:
  combine two collections
  count/result relation preserved across object type
  1 + 1 -> 2
  2 + 3 -> 5
```

### Equality

```text
equality:
  two expressions/collections map to same value or structure
  substitution preserves truth
```

### Variable

```text
variable:
  placeholder relation
  can bind to many values
  relation must remain consistent under binding
```

### Function

```text
function:
  input -> rule -> output
  same input gives same output under same function
  relation can be composed with another function
```

### Proof

```text
proof:
  sequence of valid transformations
  each step preserves truth under rules
  conclusion follows from premises
```

This preserves abstraction because the graph is not limited to physical
relations. It starts from physical/sensory channels, but extracts invariants that
can become non-physical relation structures.

## Layer 9: Meta-Abstractions

Meta-abstractions are learned ways to operate over relation structures.

```text
category:
  group by shared relation pattern

analogy:
  mapping between relation structures

counterfactual:
  change one relation and propagate expected effects

exception:
  relation pattern usually holds but fails under condition

definition:
  compressed language handle for a relation structure

explanation:
  path through relations showing why an outcome follows

skepticism:
  weak alternative relation remains active despite dominant relation

abstraction:
  remove incidental relations, preserve stable structure
```

These are central to the theory. They are how the model should move from
examples to general concepts.

## Representation Format

The training system should support three views of the same knowledge:

1. relation records
2. generated natural language
3. prediction/counterfactual tasks

### Relation Record

```text
CONCEPT ball
  REL has_shape roundness high 0.92
  REL has_property bounciness high 0.83
  REL has_property squishiness low_medium 0.31
  REL action_effect push roll 0.89
  REL action_effect drop bounce 0.78
  REL impact_body pain_risk low_medium 0.28
  CONTRAST stone bounciness lower
  CONTRAST sponge squishiness lower_for_ball
```

### Event Record

```text
EVENT glass_cup_fall
  OBJECT glass_cup
  ACTION drop
  PRE unsupported true
  EFFECT impact true 0.95
  EFFECT sound loud 0.82
  EFFECT break high 0.77
  EFFECT sharp_fragments high 0.74
  EFFECT pain_risk_if_touched high 0.70
```

### Natural Language Paraphrases

```text
A glass cup often breaks if it falls from a table.
When a glass cup breaks, it can leave sharp pieces.
You should be careful touching broken glass because it can hurt you.
```

### Counterfactual Task

```text
Input:
  A cup is made of rubber instead of glass. It falls from the table.

Expected relation change:
  break decreases
  bounce/deformation increases
  sharp_fragment_risk decreases
```

## Model Training Use

The model should be trained with ordinary language loss plus auxiliary relation
losses.

### Losses

```text
next_token_loss:
  learn normal language fluency

relation_reconstruction_loss:
  recover relation records from natural language

effect_prediction_loss:
  predict effects from object + action + context

contrastive_concept_loss:
  same relation pattern clusters together even with different words/entities

counterfactual_loss:
  update expected effects when a relation changes

abstraction_loss:
  identify which relations are essential vs incidental
```

### Relation Slots

The first model can remain a transformer, but it should have explicit relation
slot tokens during training:

```text
<OBJ>
<PROP>
<ACTION>
<EFFECT>
<VALENCE>
<CAUSE>
<CONTEXT>
<AGENT>
<GOAL>
<CONTRAST>
```

These are scaffolding tokens. They are not final truth. They pressure the model
to organize representations relationally.

### Training Curriculum

```text
Phase 1: primitive micro-events
  contact, fall, impact, pressure, pain, sound, motion

Phase 2: property learning
  hard/soft, round/flat, sharp/blunt, fragile/elastic

Phase 3: object concepts
  ball, stone, glass, knife, food, hand, fire

Phase 4: event consequences
  drop, push, squeeze, cut, burn, eat, give, hide

Phase 5: agent/self/social concepts
  want, avoid, help, harm, own, trust, fair, lazy, status

Phase 6: language attachment
  words, definitions, paraphrases, stories, questions

Phase 7: mathematical/logical abstractions
  same, different, count, order, equality, function, proof

Phase 8: ordinary text mixing
  let the model connect scaffolded relations to real-world language
```

## Data Sources

The graph can be built from a mix of seed design, existing datasets, and model
generated examples.

### Seeded Manually

Manual seed is needed for:

- input channels
- Layer 0 invariants
- sensorimotor schemas
- a small number of clean object/event examples

These must be high quality.

### Existing Sources

Useful sources:

- ConceptNet for broad commonsense relations
- WordNet for lexical hierarchy
- FrameNet for event frames
- VerbNet for action/event structure
- ATOMIC for social and causal commonsense
- dictionaries for definitions
- ordinary text corpora for language variety

### LLM-Assisted Expansion

An LLM can propose decompositions:

```text
concept -> lower relations
event -> preconditions/effects
abstract concept -> social/agentic relation graph
counterfactual variants
contrast sets
```

But generated graph entries must be validated by consistency checks and sampled
human review.

## Consistency Checks

The graph should be checked for contradictions and missing lower links.

Examples:

```text
If X is fragile, there should be some break-under-force schema.
If X is sharp, there should be cut/pain-risk links under pressure.
If X is lazy, there must be capability + effort + avoidance; otherwise it may be illness or fatigue.
If X is status, it must link to attention/compliance/resource/approval relations.
```

## Minimal Viable Version

The first version should be small enough to build and test.

```text
Layer -1 channels: 6
Layer 0 invariants: ~40
Layer 1 schemas: ~30
Layer 2 property relations: ~80
Layer 3 object concepts: ~300
Layer 4 event concepts: ~100
Layer 5 agent/self concepts: ~60
Layer 6 social concepts: ~80
Layer 8 math/logical concepts: ~80
Generated micro-experiences: 100k-1M
Natural language paraphrases: 1M-10M
```

This is enough to test the hypothesis without building a world-scale ontology.

## Evaluation

The graph is useful only if it improves learning or generalization.

### Baselines

Compare:

```text
same-size transformer trained on plain text
same-size transformer trained on ConceptNet-style triples
same-size transformer trained on developmental relation graph curriculum
```

### Tests

```text
object-action effect prediction:
  What happens if a glass cup falls?

counterfactual:
  What changes if the cup is rubber instead of glass?

concept boundary:
  Is a very squishy, non-bouncy round object still a typical ball?

essential/incidental:
  If a ball is blue instead of red, is it still a ball?

abstract distinction:
  Is a sick person who cannot work lazy?

math abstraction:
  If two apples and two stones can both match the same count, what is preserved?

analogy:
  A knife cuts food like scissors cut paper. What relation is shared?

language attachment:
  Learn a new word from relation structure, then use it in paraphrased questions.
```

### Success Condition

The developmental relation graph is useful if it lets a smaller model match or
beat the baseline on relational generalization with fewer examples or fewer
training tokens.

The first target should not be "beat a general LLM." The first target should be:

```text
same model size + same compute + relation curriculum > same model size + plain text
```

## Key Design Risks

### Risk: The Graph Becomes Too Rigid

Mitigation: keep relation strengths probabilistic and allow text training to
override weak scaffold assumptions.

### Risk: Human-Written Graph Encodes Wrong Concepts

Mitigation: use the graph as curriculum, not final authority. Test against held
out counterfactuals and ordinary text.

### Risk: Sensory Grounding Blocks Abstraction

Mitigation: make primitive relation invariants, not raw senses, the foundation
of higher abstraction. Mathematics and logic arise from invariants such as
same/different, order, matching, transformation, and preservation.

### Risk: It Becomes Just DRAGON

Mitigation: do not stop at flat triples. The distinctive part is the layered
construction:

```text
input channel -> invariant -> schema -> property -> object/event -> abstraction
```

DRAGON injects graph facts. This project teaches the model how graph facts are
developmentally constructed.

## One-Sentence Summary

A developmental relation graph is a layered training scaffold that starts from
primitive input channels, extracts simple relational invariants, builds concepts
as weighted relation clusters, binds language to those clusters, and tests
whether this explicit construction helps small models learn abstractions more
efficiently than text alone.
