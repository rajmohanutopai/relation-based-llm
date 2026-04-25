# Seed Agent: 6-Month-Old Indian Child

Status: first concrete seed graph for the developmental relation graph.

Related docs:

- `docs/developmental-relation-graph.md`
- `docs/information-cognition-abstraction-theory.md`

## Purpose

This document defines a starting relational structure for a 6-month-old boy
child growing up in India.

The goal is not to simulate a real child medically or psychologically. The goal
is to create a useful training scaffold for a relation-first small model: a
minimal "baby world" built from input channels, body control, caregivers,
objects, events, valence, and early language exposure.

This should be read as a configurable seed graph, not as a stereotype. India is
used here as an environment: multilingual speech, kinship terms, household
sounds, floor/mat life, family caregiving, common foods, climate, and everyday
objects. These are configuration points, not universal claims.

## High-Level Assumptions

```yaml
agent:
  age: 6_months
  sex: male
  country_context: India
  developmental_stage: early_sensorimotor
  language_stage: pre_word_or_early_babbling
  mobility: rolling_reaching_supported_sitting_emerging
  feeding: milk_plus_possible_complementary_foods
  social_world: familiar_caregivers_high_salience
```

At 6 months, the agent should not yet have adult concepts such as status,
ownership, morality, laziness, duty, religion, caste, nation, or mathematics.
Only their lower precursors exist:

```text
familiar/unfamiliar
comfort/discomfort
predictable/unpredictable
approach/avoid
directly controlled/not directly controlled
attention/voice/touch from caregiver
repetition and expectation
```

The graph should let higher concepts grow later from these lower relations.

## Common Graph Grammar

All concepts use one common graph grammar:

```yaml
node:
  id:
  label:
  layer:
  kind:
  age_status: active | emerging | latent | future
  summary:
  relations:
    - type:
      target:
      strength: 0.0-1.0
      valence: negative | neutral | positive | mixed
      conditions: []
      built_from: []
      evidence_pattern: []
```

Relations should be typed and weighted. A strength value does not mean objective
truth. It means the current relation strength for this seed agent.

Example:

```yaml
node:
  id: concept.caregiver_mother
  label: mother/primary caregiver
  layer: agent_relation
  kind: familiar_agent
  age_status: active
  relations:
    - type: predicts
      target: valence.comfort
      strength: 0.92
      valence: positive
      built_from:
        - channel.touch.held
        - channel.sound.familiar_voice
        - schema.feeding_relief
```

## Layer -1: Input Channels for This Agent

These are raw channels, not concepts.

### Visual Channel

High-salience visual inputs at 6 months:

```text
caregiver face
eyes and mouth movement
hand movement
near objects
bright colored toys
ceiling fan movement
light/dark change
door/window motion
human body movement
food/spoon/bottle/bowl
```

Visual resolution and attention should be biased toward near, moving, high
contrast, and face-like patterns.

### Sound Channel

Common sound inputs:

```text
mother/father/caregiver voice
home language phonemes
name-like repeated sounds
rhymes/songs
rattle sound
utensil sound
pressure cooker whistle
fan hum
doorbell/phone
traffic horn
dog/bird sounds
sudden loud sounds
crying/laughter
```

The pressure cooker, traffic horn, fan, and utensil sounds are examples of
Indian household/urban/semi-urban context. They should be configurable.

### Touch Channel

Common touch inputs:

```text
being held
skin contact
cloth/blanket
floor mat
diaper/nappy wetness
water bath
oil massage if present in household routine
toy surface
spoon/bottle contact
mouth exploration
pressure from grasping
```

### Chemical Channel

At this age, chemical input is mostly feeding-related:

```text
milk
warm/cool liquid
simple complementary foods if introduced
banana/rice/dal/ragi/cerelac-like food depending on household
medicine/vitamin taste if present
unpleasant taste
familiar caregiver smell
```

Food entries must be configurable and should not be treated as medical advice.

### Proprioception and Control Channel

Key inputs:

```text
hand position
foot position
head movement
rolling
reaching
grasping
bringing object to mouth
supported sitting
caregiver-assisted movement
effort/fatigue
```

### Valence Channel

Primitive body value signals:

```text
hunger
satiety
pain
startle
comfort
discomfort
sleepiness
relief
pleasure from touch/voice/play/food
frustration from blocked reach
```

## Layer 0: Active Relational Invariants at 6 Months

The agent should have these as active or emerging relation detectors.

### Active Relations

```text
same_as
different_from
near
far
supported
unsupported
appears
disappears
moves
stops
before
after
repeats
expected
unexpected
touching
not_touching
more
less
comfort_increases
comfort_decreases
pain_increases
sound_increases
sound_decreases
positive_activation
connection_gain
positive_saturation
```

### Emerging Relations

```text
inside/outside
behind/in_front
object_persists_when_hidden
action_causes_effect
self_caused_motion
other_caused_motion
body_orientation
agent_attention
shared_attention
connection_loss
```

At 6 months, object permanence and cause-effect should be partial/emerging, not
fully mature.

Comfort, happiness, and sadness are separated in this seed:

```text
comfort:
  body-state relief or stabilization

happiness from existing connection:
  familiar cue activates already learned positive relations

happiness from new connection:
  useful new relation forms or strengthens

sadness/distress from connection loss:
  expected valued relation is absent, blocked, or weakened
```

There is also a saturation modifier:

```text
repeated same positive cue:
  maintains comfort/familiarity
  produces less new happiness over time

changed cue or newly learned relation:
  creates fresh connection_gain
  happiness can rise again
```

At 6 months this is visible as habituation: the same rattle sound or peekaboo
pattern may become less exciting unless timing, intensity, object, voice, or
social response changes. Later, the same rule grows into novelty seeking,
ambition, status escalation, and addiction risk.

At 6 months, sadness is represented as distress from blocked expected comfort,
not as an adult reflective concept.

### Future Relations

```text
mine/yours
fair/unfair
rule
promise
number
status
shame
laziness
duty
```

These should not be active as concepts yet. Only lower precursors may exist.

## Layer 1: Sensorimotor Schemas

### Self-Motion Schema

```yaml
id: schema.self_motion
age_status: active
structure:
  motor_command -> body_part_moves
  body_part_moves -> visual_change
  body_part_moves -> proprioception_change
  body_part_touched -> direct_sensation
```

Examples:

```text
try_move_hand -> hand moves
hand touches mouth -> mouth sensation + hand sensation
try_move_foot -> foot moves
```

This schema is the first foundation of self.

### Body Orientation, Posture Support, and Balance Schemas

```yaml
id: schema.body_orientation_change
age_status: emerging
structure:
  rolling / assisted movement -> body orientation changes
  visual field changes
  touch pressure changes
  proprioception changes

id: schema.posture_support
age_status: emerging
structure:
  hand / caregiver / floor / lap / cushion supports body
  supported posture remains more stable

id: schema.balance_instability
age_status: emerging
structure:
  support weakens or body tilts
  posture becomes unstable
  fall/catch/discomfort may follow
```

These cover rolling, tummy-time pushing, supported sitting, and loss of balance.

### Caregiver-Holding Schema

```yaml
id: schema.held_by_caregiver
age_status: active
structure:
  familiar_agent_arms_contact -> pressure_warmth
  familiar_voice -> prediction_of_comfort
  body_position_stabilizes -> discomfort_decreases
```

### Feeding-Relief Schema

```yaml
id: schema.feeding_relief
age_status: active
structure:
  hunger_discomfort -> cry
  caregiver_approach -> held
  milk_or_food -> satiety
  satiety -> relief/comfort
```

This is one of the strongest early causal loops.

### Feeding Completion and Spoon Approach Schemas

```yaml
id: schema.feeding_completion
age_status: active
structure:
  feeding -> satiety/fullness
  fullness -> reduced interest
  baby turns away / closes mouth
  caregiver slows or stops feeding

id: schema.spoon_approach_mouth
age_status: emerging
structure:
  caregiver moves spoon toward mouth
  spoon/food approaches mouth
  mouth contact may bring taste, texture, temperature, or refusal
```

These are separate from hunger relief. Hunger relief explains why feeding
starts; feeding completion explains why feeding stops.

### Reach-Grasp-Mouth Schema

```yaml
id: schema.reach_grasp_mouth
age_status: active
structure:
  interesting_near_object -> reach_attempt
  hand_contact -> grasp_if_possible
  grasped_object -> mouth_contact
  mouth_contact -> texture/taste/temperature
```

### Drop-Sound Schema

```yaml
id: schema.drop_sound
age_status: emerging
structure:
  held_object_released -> object_moves_down
  object_impacts_surface -> sound
  sound_strength depends_on object/material/height/surface
```

At this age, the child may not intentionally test dropping consistently, but the
relation is learnable through repeated events.

### Shake-Sound Schema

```yaml
id: schema.shake_sound
age_status: active_if_rattle_present
structure:
  hand_motion + rattle -> sound_repeats
  stronger_motion -> louder_or_more_frequent_sound
```

This is a clean early cause-effect training motif.

### Startle-Comfort Schema

```yaml
id: schema.startle_comfort
age_status: active
structure:
  sudden_loud_sound -> startle/discomfort
  caregiver_voice_touch -> comfort_increases
```

Useful Indian-context sounds include pressure cooker whistle, traffic horn,
doorbell, utensils, and festival/firecracker sounds if present.

### Hide-Reappear Schema

```yaml
id: schema.hide_reappear
age_status: emerging
structure:
  object_visible -> covered/hidden
  object_not_visible -> expectation weakly persists
  cover_removed -> object_reappears
```

This is an early object permanence motif.

### Sleep Transition Schema

```yaml
id: schema.sleep_transition
age_status: active
structure:
  sleepiness/fatigue -> fussiness/discomfort
  holding/rocking/lullaby/reduced stimulation -> comfort
  comfort + low stimulation -> sleep transition
```

This is a reusable regulation motif. Later it supports ideas such as tiredness,
rest, routine, and self-regulation.

### Wetness Relief Schema

```yaml
id: schema.wetness_relief
age_status: active
structure:
  wetness/body discomfort -> fussing or crying
  caregiver cleaning/changing -> wetness decreases
  discomfort decreases
```

This is a body-state-to-caregiver-response relation, similar in form to hunger
relief.

### Temperature Comfort Schema

```yaml
id: schema.temperature_comfort
age_status: active
structure:
  too hot / too cold -> discomfort
  fan/clothing/bath/holding changes body temperature
  comfort changes accordingly
```

This becomes useful later for understanding comfort, weather, clothing, illness,
and environment regulation.

### Bath Water Contact Schema

```yaml
id: schema.bath_water_contact
age_status: active
structure:
  caregiver supports baby during bath
  water contacts body
  water temperature is felt
  body becomes wet
  comfort/discomfort depends on temperature, handling, and routine
```

This is separate from wet diaper. Wet diaper is usually discomfort; bath water
can be comforting, neutral, startling, or uncomfortable.

### Body Impact Pain Schema

```yaml
id: schema.body_impact_pain
age_status: active
structure:
  body impact/pressure/bump -> pain
  pain -> cry/withdrawal
  caregiver voice/touch -> comfort repair
```

This is a foundation for danger, injury, caution, and later empathy.

### Push-Roll Schema

```yaml
id: schema.push_roll
age_status: emerging
structure:
  round object on surface
  push/release/caregiver action
  object changes position by rolling
```

This makes ball rolling explicit rather than leaving it inside the `round`
property alone.

### Face Proximity Attention Schema

```yaml
id: schema.face_proximity_attention
age_status: active
structure:
  familiar face moves close
  eyes/mouth/expression become salient
  baby attention shifts to face
  voice or expression can change comfort/arousal
```

This supports caregiver face closeness as its own encounter family.

### Imitation Schema

```yaml
id: schema.imitation
age_status: emerging
structure:
  caregiver sound/facial movement/gesture -> baby attention
  baby attempts similar sound/movement
  caregiver responds
```

This is one foundation for language and social learning.

### Joint Attention Schema

```yaml
id: schema.joint_attention
age_status: emerging
structure:
  caregiver gaze/pointing/voice -> baby attention shift
  baby attends to object
  word/action/object co-occur
```

This is central for later word learning. It lets a word bind to a relation
cluster because caregiver attention selects the object/event.

### Rhythm and Song Comfort Schema

```yaml
id: schema.rhythm_song_comfort
age_status: active
structure:
  repeated rhythm + familiar soft voice -> attention stabilization
  comfort increases
  sleep transition may become easier
```

This covers lullabies, rhymes, repeated syllables, and soothing speech.

### Novelty and Habituation Schema

```yaml
id: schema.novelty_habituation
age_status: active
structure:
  new stimulus -> attention increases
  repeated same stimulus -> prediction strengthens
  attention decreases unless pattern changes
  happiness from connection_gain decreases as the relation saturates
```

This is important for learning because it controls what becomes salient.

### Mouth Aversion Schema

```yaml
id: schema.mouth_aversion
age_status: active
structure:
  unpleasant taste / hard pressure / discomfort in mouth -> aversion
  aversion -> turn away / grimace / cry
  caregiver removes or changes object/food
```

This complements mouth exploration with safety and dislike.

### Open-Close Boundary Schema

```yaml
id: schema.open_close_boundary
age_status: emerging
structure:
  door/curtain/boundary changes open/closed state
  sound may occur
  person/object/room may appear or disappear
  attention shifts toward boundary
```

This covers doors, knocking, bells, and visible boundary changes.

### Caregiver Safety Blocking and Blocked Action Schemas

```yaml
id: schema.caregiver_safety_block
age_status: emerging
structure:
  baby reaches/mouths/moves toward object or place
  caregiver blocks, removes object, or changes baby position
  action stops or redirects

id: schema.blocked_action_frustration
age_status: emerging
structure:
  intended action is blocked
  effort or fussing may increase
```

This is not morality yet. It is a precursor to danger, permission, rule,
prohibition, and later social norm learning.

### Caregiver Emotional Tone Schema

```yaml
id: schema.caregiver_emotional_tone
age_status: active
structure:
  soft voice / smiling face -> comfort or approach
  sharp voice / angry face -> discomfort or uncertainty
```

This is not morality yet. It is an affective precursor to approval,
disapproval, shame, pride, and social prediction.

### Medical, Illness, and Comfort-Exploration Schemas

```yaml
id: schema.medical_pain_care
age_status: emerging
structure:
  clinic/doctor/medicine/vaccination context
  unfamiliar adult may touch/examine/administer medicine
  discomfort or pain may occur
  primary caregiver repairs comfort

id: schema.illness_discomfort
age_status: emerging
structure:
  feverishness / blocked nose / tiredness / unusual fussiness
  exploration decreases
  care need increases

id: schema.comfort_exploration_readiness
age_status: active
structure:
  hunger/sleep/wetness/temperature/pain are regulated
  baby is calmer and more alert
  play and exploration become easier
```

The last schema is important for the happiness theory: comfort is not happiness,
but comfort supports exploration and new relation gain.

### Wake, Stimulation, Feeding Delay, and Internal Discomfort Schemas

```yaml
id: schema.wake_transition
age_status: active
structure:
  sleep state changes toward waking
  sound/light/movement/temperature/hunger/internal discomfort may trigger waking
  familiar place or caregiver can stabilize the transition

id: schema.stimulation_regulation
age_status: active
structure:
  sound/light/visitor/activity intensity changes arousal
  too much stimulation can increase discomfort
  reduced sound/light/movement can support calming or sleep

id: schema.feeding_interruption_delay
age_status: active
structure:
  expected feeding relief has started or is anticipated
  milk/food pauses or is delayed before satiety
  discomfort or frustration may increase

id: schema.internal_discomfort_gas
age_status: active
structure:
  gas/burping/stomach pressure changes internal comfort
  crying or body movement may increase
  upright holding, burping, or time may change discomfort
```

These are still bodily and regulatory, not abstract frustration or patience.
They provide lower structure for later ideas such as waiting, interruption,
illness, and environmental regulation.

### Orienting, Carrying, Light, and Mirror Schemas

```yaml
id: schema.orienting_to_sound_motion
age_status: active
structure:
  salient sound/motion/face/object occurs
  head/eyes/attention turn toward source
  attention stabilizes briefly on source

id: schema.light_change
age_status: active
structure:
  light switches on/off
  brightness/darkness changes
  attention, wakefulness, or comfort may change

id: schema.carry_context_transition
age_status: active
structure:
  caregiver holds or carries baby
  body orientation and visual scene change
  place/room context changes without direct baby control

id: schema.mirror_reflection
age_status: emerging
structure:
  mirror shows baby/caregiver image
  image moves with visual similarity
  no direct touch/proprioception comes from the image itself
```

The mirror schema should not be treated as adult self-recognition. It is a
visual contingency and same/different relation that can later support self/other
distinctions.

### Wider Social and Early Language Exposure Schemas

```yaml
id: schema.unfamiliar_agent_approach
age_status: emerging
structure:
  less familiar face/voice/body approaches
  prediction confidence is lower than with primary caregiver
  attention, uncertainty, or comfort need may change

id: schema.other_cry_arousal
age_status: emerging
structure:
  another baby/child cry is heard
  sound is distress-like but not self-produced
  arousal or uncertainty may increase

id: schema.routine_word_action
age_status: emerging
structure:
  repeated household words co-occur with feeding/bathing/dressing/play
  action sequence gives the word a weak temporal anchor

id: schema.picture_word_exposure
age_status: emerging
structure:
  caregiver shows picture or flat image
  caregiver speech names or comments on it
  joint attention gives the sound a weak object/event anchor

id: schema.object_removal_frustration
age_status: emerging
structure:
  expected toy/object access stops
  caregiver removes or redirects object for safety/cleaning/end of play
  blocked access can increase fussing
```

Routine words and picture naming are not full language yet. They are repeated
co-occurrence structures that prepare later word binding.

## Layer 2: Early Property Relations

Properties are behavior summaries, not labels.

### Soft

```yaml
id: property.soft
age_status: active
built_from:
  - touch.pressure -> deformation
  - contact -> comfort usually higher
examples:
  - cloth
  - blanket
  - soft toy
  - caregiver body
```

### Hard

```yaml
id: property.hard
age_status: active
built_from:
  - pressure -> low_deformation
  - impact -> stronger sound
  - body_impact -> possible pain
examples:
  - floor
  - steel plate/bowl
  - wooden toy
```

### Loud

```yaml
id: property.loud
age_status: active
built_from:
  - sound_intensity high
  - startle likely if sudden
examples:
  - pressure cooker whistle
  - dropped steel utensil
  - traffic horn
```

### Quiet/Soft Sound

```yaml
id: property.soft_sound
age_status: active
built_from:
  - sound_intensity low
  - low startle
examples:
  - cloth drop
  - soft toy movement
```

### Warm

```yaml
id: property.warm
age_status: active
built_from:
  - touch temperature moderate/high
  - comfort or discomfort depending intensity
examples:
  - caregiver body
  - bath water
  - milk/food
```

### Round

```yaml
id: property.round
age_status: emerging
built_from:
  - visual curved outline
  - orientation changes but outline remains similar
  - push may cause rolling
examples:
  - ball
  - bangle if present
  - bowl rim
```

### Familiar

```yaml
id: property.familiar
age_status: active
built_from:
  - repeated face/voice/smell/touch
  - predicts comfort
  - reduces uncertainty
```

### Unfamiliar

```yaml
id: property.unfamiliar
age_status: emerging
built_from:
  - face/voice pattern not matching known caregivers
  - prediction confidence lower
  - may increase vigilance/discomfort
```

### Regulation and Attention Properties

```yaml
property.sleepy:
  age_status: active
  built_from:
    - fatigue / low regulation
    - fussiness or low attention
    - sleep transition likely

property.wet:
  age_status: active
  built_from:
    - touch wetness
    - body discomfort
    - caregiver change can relieve

property.wet_body:
  age_status: active
  built_from:
    - bath / cleaning / spill / sweating wetness
    - valence depends on temperature and context

property.water_temperature:
  age_status: active
  built_from:
    - water touch temperature
    - comfort/discomfort changes with intensity

property.too_hot / property.too_cold:
  age_status: active
  built_from:
    - temperature discomfort
    - comfort changes after clothing/fan/bath/holding

property.novel:
  age_status: active
  built_from:
    - unexpected or changed stimulus
    - attention increases

property.repeated:
  age_status: active
  built_from:
    - same pattern occurs again and again
    - expectation strengthens
    - attention may decrease

property.full:
  age_status: active
  built_from:
    - satiety after feeding
    - reduced feeding interest
    - turning away or closing mouth

property.food_texture:
  age_status: emerging
  built_from:
    - mouth touch
    - taste/smell
    - smooth/lumpy/sticky/warm/cool input

property.food_familiarity:
  age_status: emerging
  built_from:
    - repeated food taste/smell/texture
    - feeding context
    - expectation
```

### Mouth and Tone Properties

```yaml
property.unpleasant_taste:
  age_status: active
  built_from:
    - bitter/sour/irritating mouth input
    - aversion or turning away

property.familiar_face:
  age_status: active
  built_from:
    - repeated caregiver face pattern
    - eyes/mouth/expression
    - comfort/attention

property.soft_voice:
  age_status: active
  built_from:
    - familiar low-intensity voice
    - comfort/approach

property.sharp_voice:
  age_status: active
  built_from:
    - abrupt or high-intensity voice
    - discomfort/uncertainty

property.unsafe_object:
  age_status: emerging
  built_from:
    - caregiver blocks access
    - possible choking/pain/contamination/break risk

property.feverish:
  age_status: emerging
  built_from:
    - unusual body heat
    - discomfort/low energy

property.blocked_breathing:
  age_status: emerging
  built_from:
    - blocked nose or breathing discomfort
    - sleep/play disruption

property.gas_discomfort:
  age_status: active
  built_from:
    - internal pressure/discomfort
    - cry/fuss/body movement
    - caregiver holding or burping may change state

property.bright_light:
  age_status: active
  built_from:
    - high visual brightness
    - attention or wakefulness may increase
    - discomfort may increase if intensity is too high

property.darkness:
  age_status: active
  built_from:
    - low visual brightness
    - sleep context or uncertainty depending on other cues

property.overstimulating:
  age_status: emerging
  built_from:
    - too much sound/light/motion/touch/visitor activity
    - current regulation capacity is exceeded
    - comfort decreases

property.smiling_face:
  age_status: active
  built_from:
    - familiar caregiver eyes/mouth expression
    - friendly attention/play/comfort often follows
```

## Layer 3: Early Object Concepts

Object concepts at 6 months should be weak, prototype-like, and heavily linked
to action and sensation.

### Own Hand

```yaml
id: object.self_hand
kind: body_part
age_status: active
relations:
  - type: directly_controlled
    target: action.move_hand
    strength: 0.90
  - type: causes_direct_sensation
    target: touch.hand_contact
    strength: 0.85
  - type: can_contact
    target: object.mouth
    strength: 0.85
  - type: can_grasp
    target: object.near_small_object
    strength: 0.60
  - type: built_from
    target: schema.self_motion
    strength: 0.95
```

### Mouth

```yaml
id: object.self_mouth
kind: body_part
age_status: active
relations:
  - type: direct_sensation
    target: taste_touch_temperature
    strength: 0.95
  - type: used_for
    target: feeding
    strength: 0.95
  - type: exploration
    target: object.grasped_object
    strength: 0.75
```

### Mother / Primary Caregiver

Use "mother" here as a role. In a real graph this should be configurable as
`caregiver.primary`.

```yaml
id: agent.primary_caregiver
kind: familiar_agent
age_status: active
relations:
  - type: predicts
    target: valence.comfort
    strength: 0.92
  - type: predicts
    target: feeding_relief
    strength: 0.90
  - type: has_signal
    target: sound.familiar_voice
    strength: 0.88
  - type: has_signal
    target: visual.familiar_face
    strength: 0.86
  - type: has_signal
    target: smell.familiar_body
    strength: 0.70
  - type: responds_to
    target: cry
    strength: 0.82
  - type: not_directly_controlled
    target: self.motor_command
    strength: 0.90
```

This is the first strong "other agent" concept.

### Secondary Caregivers

```yaml
id: agent.secondary_caregivers
examples:
  - father
  - grandmother
  - grandfather
  - sibling
  - nanny/relative if present
age_status: active_or_emerging
relations:
  - type: familiar_agent
    strength: variable
  - type: play
    target: comfort/pleasure
    strength: variable
  - type: voice_face_touch_cluster
    strength: variable
```

Kinship categories are not mature at 6 months. The relation is with recurring
individuals, not yet with the abstract family role.

### Rattle

```yaml
id: object.rattle
kind: manipulable_object
age_status: active_if_present
relations:
  - type: graspable
    target: action.grasp
    strength: 0.75
  - type: action_effect
    action: action.shake
    target: sound.rattle
    strength: 0.90
  - type: action_effect
    action: action.drop
    target: sound.impact
    strength: 0.55
  - type: mouth_explorable
    target: touch_mouth.texture
    strength: 0.70
  - type: built_from
    target: schema.shake_sound
    strength: 0.85
```

### Ball

```yaml
id: object.ball
kind: manipulable_object
age_status: emerging
relations:
  - type: has_property
    target: property.round
    strength: 0.70
  - type: action_effect
    action: action.push
    target: event.roll
    strength: 0.65
  - type: action_effect
    action: action.drop
    target: event.bounce_or_sound
    strength: 0.50
  - type: graspable
    target: action.grasp
    strength: depends_on_size
```

At 6 months, "ball" is not yet a full concept. It is a cluster of round visual
shape, touch, grasp difficulty, rolling, caregiver naming, and repeated play.

### Spoon and Bottle

```yaml
id: object.spoon
kind: feeding_object
age_status: emerging
relations:
  - type: caregiver_controlled
    target: schema.spoon_approach_mouth
  - type: can_bring
    target: food_texture/taste

id: object.bottle
kind: feeding_object
age_status: active_if_present
relations:
  - type: predicts
    target: feeding_relief
  - type: mouth_contact
    target: liquid_flow
```

These are configurable because households differ.

### Steel Bowl / Spoon

```yaml
id: object.steel_bowl_spoon
kind: household_object
age_status: active_if_present
relations:
  - type: has_property
    target: property.hard
    strength: 0.85
  - type: action_effect
    action: action.hit_or_drop
    target: sound.loud_metal
    strength: 0.85
  - type: associated_with
    target: feeding
    strength: 0.60
```

This is a common Indian household sound/object cluster.

### Cloth / Blanket

```yaml
id: object.cloth_blanket
kind: household_object
age_status: active
relations:
  - type: has_property
    target: property.soft
    strength: 0.90
  - type: action_effect
    action: action.drop
    target: sound.soft_or_none
    strength: 0.85
  - type: comfort
    target: valence.comfort
    strength: 0.55
  - type: can_hide
    target: object.small_object
    strength: 0.60
```

### Ceiling Fan

```yaml
id: object.ceiling_fan
kind: distant_object
age_status: active
relations:
  - type: visual_motion
    target: event.rotation
    strength: 0.90
  - type: not_reachable
    target: action.reach
    strength: 0.95
  - type: sound
    target: sound.hum
    strength: variable
  - type: visual_attention
    target: gaze
    strength: high_if_visible
```

The fan is useful because it teaches motion without self-control.

### Door and Doorbell / Knock

```yaml
id: object.door
kind: household_boundary_object
age_status: emerging
relations:
  - type: open_close
    target: event.door_open_close
  - type: may_hide_or_reveal
    target: person/room/object

id: context.doorbell_or_knock
kind: household_sound
age_status: emerging
relations:
  - type: can_precede
    target: door_open_close
```

Door events are useful because they combine sound, boundary change,
appearance/disappearance, and social arrival.

### Medical Context and Unfamiliar Care Agent

```yaml
id: context.clinic
kind: care_context
age_status: emerging

id: agent.unfamiliar_caregiver_or_doctor
kind: unfamiliar_agent
age_status: emerging
relations:
  - type: can_touch_or_examine
    target: body
  - type: associated_with
    target: medicine/vaccination/health_check
```

This should remain a care/safety context, not a generalized fear concept.

### Maybe-Layer Household, Social, and Language Handles

These handles were added after the maybe-42 encounter audit. They are still
weak and configurable, but they prevent common six-month encounters from being
forced through unrelated objects.

```yaml
id: agent.other_child
kind: other_agent
age_status: emerging
relations:
  - type: can_emit
    target: cry/laugh/play_sound
  - type: affects
    target: arousal

id: object.book_picture
kind: flat_visual_object
age_status: emerging
relations:
  - type: supports
    target: schema.picture_word_exposure

id: object.mirror
kind: reflective_surface
age_status: emerging
relations:
  - type: supports
    target: schema.mirror_reflection

id: context.feeding_setup
kind: routine_context
age_status: active
relations:
  - type: predicts
    target: schema.feeding_relief

id: context.kitchen_appliance_sound
kind: household_sound
age_status: emerging
relations:
  - type: has_property
    target: property.loud
  - type: can_cause
    target: event.loud_sound_startle

id: context.room_place
kind: place_context
age_status: active
relations:
  - type: supports
    target: schema.carry_context_transition

id: language.routine_word
kind: early_sound_pattern
age_status: emerging
relations:
  - type: co_occurs_with
    target: schema.routine_word_action

id: language.object_name_sound
kind: early_sound_pattern
age_status: emerging
relations:
  - type: co_occurs_with
    target: schema.joint_attention
```

## Layer 4: Early Event Concepts

### Cry -> Caregiver Response

```yaml
id: event.cry_caregiver_response
age_status: active
relations:
  - type: starts_with
    target: discomfort.hunger_pain_wet_sleepy
    strength: 0.85
  - type: action_signal
    target: cry
    strength: 0.95
  - type: predicts
    target: caregiver_approach
    strength: household_dependent
  - type: effect
    target: comfort_or_relief
    strength: 0.75
```

This relation is central to early agency: internal state changes external agent
behavior.

### Reach -> Grasp / Fail

```yaml
id: event.reach_grasp
age_status: active
relations:
  - type: precondition
    target: object.near
    strength: 0.80
  - type: action
    target: move_hand_toward_object
    strength: 0.90
  - type: success_if
    target: distance_close_and_hand_alignment
    strength: 0.60
  - type: failure_effect
    target: frustration
    strength: 0.50
```

### Object Drop -> Sound

```yaml
id: event.object_drop_sound
age_status: emerging
relations:
  - type: precondition
    target: object_held_or_supported
    strength: 0.70
  - type: effect
    target: object_moves_down
    strength: 0.80
  - type: effect
    target: impact_sound
    strength: depends_on_material
  - type: contrast
    target: cloth_drop_vs_steel_drop
    strength: 0.75
```

### Loud Sound -> Startle -> Comfort

```yaml
id: event.loud_sound_startle
age_status: active
relations:
  - type: cause
    target: startle
    strength: 0.80
  - type: effect
    target: cry_or_freeze
    strength: variable
  - type: repaired_by
    target: caregiver_voice_touch
    strength: 0.75
```

### Peekaboo / Hide-Reappear

```yaml
id: event.peekaboo
age_status: emerging
relations:
  - type: visual_disappear
    target: caregiver_face_hidden
    strength: 0.85
  - type: visual_reappear
    target: caregiver_face_visible
    strength: 0.85
  - type: repetition
    target: expectation
    strength: 0.70
  - type: effect
    target: laughter_or_surprise
    strength: 0.60
```

This is a bridge from object permanence to social play.

## Layer 5: Self and Other at 6 Months

### Self

At 6 months, self is not an abstract identity. It is a control/sensation cluster.

```yaml
id: concept.self_proto
age_status: active
built_from:
  - schema.self_motion
  - direct_touch_sensation
  - hunger/pain/comfort internal signals
relations:
  - type: directly_controls
    target: body_parts.hand_foot_head_mouth
    strength: high
  - type: directly_feels
    target: body_contact_pain_hunger
    strength: high
  - type: indirectly_affects
    target: external_objects
    strength: emerging
```

### Other Agent

```yaml
id: concept.other_agent_proto
age_status: active
built_from:
  - recurring_face_voice_touch
  - self_not_controlled
  - responds_to_cry
  - initiates_movement
relations:
  - type: can_affect_self
    target: comfort_food_movement
    strength: high
  - type: not_directly_controlled
    target: self_motor_command
    strength: high
  - type: predictable_if_familiar
    target: comfort
    strength: medium_high
```

### Familiar vs Stranger

```yaml
id: concept.familiar_vs_unfamiliar_agent
age_status: emerging
relations:
  - type: familiar_agent
    target: comfort_prediction
    strength: medium_high
  - type: unfamiliar_agent
    target: uncertainty_or_vigilance
    strength: emerging
```

This is a precursor to stranger anxiety, trust, family, and social identity.

## Layer 6: Early Social Precursors

Do not introduce adult social abstractions yet. Use precursors.

### Attention

```yaml
id: social_precursor.attention
age_status: active
relations:
  - type: caregiver_face_or_voice_directed_to_self
    target: arousal_comfort
    strength: 0.75
  - type: gaze_following
    target: shared_attention
    strength: emerging
```

### Turn-Taking

```yaml
id: social_precursor.turn_taking
age_status: emerging
relations:
  - type: baby_sound
    target: caregiver_sound_response
    strength: 0.65
  - type: caregiver_sound
    target: baby_sound_or_smile
    strength: 0.55
```

This later supports conversation.

### Approval / Disapproval Precursors

At 6 months these should be weak and affective, not moral.

```yaml
id: social_precursor.approval_disapproval
age_status: latent_or_emerging
relations:
  - type: smiling_voice
    target: comfort/approach
    strength: medium
  - type: sharp_voice_or_angry_face
    target: discomfort/uncertainty
    strength: low_medium
```

Do not yet create concepts such as shame, pride, status, or discipline.

## Layer 7: Language Binding at 6 Months

At 6 months, language is mostly sound-pattern binding, rhythm, emotional tone,
and a few repeated handles. Words are not yet full symbolic concepts.

### Configurable Language Context

```yaml
language_context:
  home_language.primary: configurable
  home_language.secondary: optional
  english_exposure: optional
  kinship_words:
    mother: configurable  # amma, mummy, maa, aai, etc.
    father: configurable  # appa, papa, baba, etc.
```

Avoid hard-coding one Indian language.

### Name-Like Sound

```yaml
id: language.sound_own_name
age_status: emerging
relations:
  - type: repeated_sound_pattern
    target: caregiver_attention_to_self
    strength: 0.65
  - type: predicts
    target: caregiver_face_voice
    strength: 0.55
```

### Caregiver Word Handles

```yaml
id: language.word_mother_handle
age_status: emerging
relations:
  - type: sound_pattern
    target: agent.primary_caregiver
    strength: 0.50
  - type: co_occurs_with
    target: feeding_comfort_voice_face
    strength: 0.70
```

### Object Word Handles

```yaml
id: language.word_ball_handle
age_status: latent_or_emerging
relations:
  - type: sound_pattern
    target: object.ball
    strength: low
  - type: co_occurs_with
    target: caregiver_pointing_showing_play
    strength: medium_if_repeated
```

Language should initially attach through repeated co-occurrence:

```text
caregiver says word + shows object + object interaction repeats
```

## Early Indian Context Nodes

These are optional environment nodes. They should be configured by household,
region, language, class, urban/rural setting, and family structure.

### Household Sound: Pressure Cooker

```yaml
id: context.india.pressure_cooker_whistle
kind: household_sound
age_status: active_if_present
relations:
  - type: has_property
    target: property.loud
    strength: 0.80
  - type: can_cause
    target: startle
    strength: 0.70
  - type: repeats
    target: mealtime_context
    strength: 0.45
```

### Household Object: Steel Utensil

```yaml
id: context.india.steel_utensil
kind: household_object
age_status: active_if_present
relations:
  - type: has_property
    target: property.hard
    strength: 0.85
  - type: action_effect
    action: drop_or_hit
    target: loud_metal_sound
    strength: 0.85
  - type: associated_with
    target: feeding_kitchen
    strength: 0.55
```

### Environment: Floor Mat

```yaml
id: context.india.floor_mat
kind: support_surface
age_status: active_if_present
relations:
  - type: supports
    target: body.lying_sitting_playing
    strength: 0.80
  - type: has_property
    target: soft_or_firm_surface
    strength: variable
  - type: enables
    target: rolling_reaching_play
    strength: 0.70
```

### Social Environment: Multi-Caregiver Household

```yaml
id: context.india.multi_caregiver_household
kind: social_context
age_status: active_if_present
relations:
  - type: provides
    target: multiple_familiar_faces_voices
    strength: variable
  - type: increases
    target: familiar_agent_set
    strength: variable
  - type: supports
    target: turn_taking_voice_variation
    strength: variable
```

This can include grandparents, relatives, siblings, domestic help, or neighbors,
depending on the actual household.

## Core Micro-Experience Records

These are training examples that build the seed graph.

### Hunger Relief

```text
STATE hunger high
BABY cries
CAREGIVER approaches
BABY is held
BABY receives milk/food
STATE hunger decreases
STATE comfort increases
RELATION cry -> caregiver_response
RELATION feeding -> relief
```

### Hand Self-Motion

```text
BABY sends motor command to hand
HAND moves visually
PROPRIOCEPTION changes
HAND touches mouth
MOUTH feels contact
RELATION motor_command -> body_motion
RELATION hand -> self_body
```

### Rattle Cause-Effect

```text
BABY grasps rattle
BABY moves hand
RATTLE makes sound
BABY stops moving hand
SOUND stops
RELATION hand_motion + rattle -> sound
RELATION stopping_motion -> sound_stops
```

### Steel Bowl Drop

```text
STEEL_BOWL held by caregiver
STEEL_BOWL falls to floor
LOUD metal sound occurs
BABY startles
CAREGIVER speaks softly / holds baby
COMFORT increases
RELATION hard_metal_object + drop -> loud_sound
RELATION loud_sudden_sound -> startle
RELATION caregiver_touch_voice -> comfort
```

### Cloth Drop Contrast

```text
CLOTH falls to mat
SOFT or no sound occurs
BABY does not startle
RELATION soft_object + drop -> low_sound
CONTRAST steel_bowl_drop vs cloth_drop
```

### Ball Roll

```text
BALL near baby
CAREGIVER pushes ball
BALL rolls away
BABY watches movement
CAREGIVER brings ball back
RELATION round_object + push -> roll
RELATION object_far -> reach_fails
RELATION caregiver_action -> object_returns
```

### Peekaboo

```text
CAREGIVER face visible
CAREGIVER covers face
FACE disappears
CAREGIVER uncovers face
FACE reappears
BABY smiles/laughs
RELATION hidden -> reappears
RELATION repeated_pattern -> expectation
RELATION familiar_face_reappears -> pleasure
```

### Spoon Feeding

```text
SPOON approaches mouth
FOOD taste occurs
HUNGER decreases
SPOON disappears
SPOON returns
RELATION spoon -> feeding_context
RELATION repeated_approach -> expectation
```

### Sleep and Lullaby

```text
STATE sleepiness high
BABY fusses
CAREGIVER holds or rocks baby
CAREGIVER uses soft repeated voice / lullaby
STIMULATION decreases
COMFORT increases
SLEEP transition begins
RELATION sleepy_state -> discomfort
RELATION rhythm + soft_voice + holding -> comfort
```

### Wetness and Changing

```text
STATE wetness high
DISCOMFORT rises
BABY cries or fusses
CAREGIVER cleans/changes diaper or cloth
WETNESS decreases
COMFORT increases
RELATION wetness -> discomfort
RELATION caregiver_change -> relief
```

### Temperature Adjustment

```text
STATE too_hot or too_cold
DISCOMFORT rises
CAREGIVER changes fan/clothing/bath/holding
TEMPERATURE discomfort decreases
RELATION temperature_extreme -> discomfort
RELATION environment_adjustment -> comfort
```

### Body Bump and Pain

```text
BODY impact or pressure occurs
PAIN rises
BABY cries
CAREGIVER approaches with voice/touch
COMFORT gradually increases
RELATION body_impact -> pain
RELATION caregiver_tone_touch -> comfort_repair
```

### Imitation and Turn-Taking

```text
CAREGIVER makes repeated sound or facial movement
BABY watches/listens
BABY attempts similar sound or movement
CAREGIVER responds
RELATION caregiver_pattern -> baby_attempt
RELATION alternating_response -> turn_taking
```

### Joint Attention to Object

```text
CAREGIVER looks/points/speaks toward ball
BABY shifts attention
BABY attends to ball
WORD/action/object co-occur
RELATION caregiver_attention -> baby_attention
RELATION word_sound -> object_relation_cluster
```

### Novelty and Habituation

```text
NEW rattle sound occurs
ATTENTION increases
SAME sound repeats many times
EXPECTATION strengthens
ATTENTION decreases unless pattern changes
RELATION novelty -> attention
RELATION repetition -> expectation
```

### Mouth Aversion

```text
OBJECT or food contacts mouth
UNPLEASANT taste or pressure occurs
BABY turns away / grimaces / cries
CAREGIVER removes or changes object/food
RELATION unpleasant_mouth_input -> aversion
```

### Familiar Soft Voice and Happiness

```text
CAREGIVER appears or speaks softly
FAMILIAR voice/face activates prior comfort relations
BABY smiles, relaxes, or approaches
RELATION familiar_positive_cue -> positive_activation
RELATION existing_connection_activation -> happiness
```

### New Rattle Relation and Happiness

```text
BABY moves hand while holding rattle
SOUND occurs unexpectedly
BABY repeats movement
SOUND repeats predictably
NEW relation hand_motion -> rattle_sound strengthens
RELATION new_useful_connection -> happiness
```

### Caregiver Absence and Connection-Loss Distress

```text
BABY expects caregiver response
CAREGIVER response is delayed or absent
EXPECTED comfort relation does not activate
DISTRESS increases
CAREGIVER returns
COMFORT relation reactivates
RELATION blocked_expected_connection -> distress/sadness precursor
```

## Concept Growth Paths From 6 Months

This seed is meant to support later growth. Some examples:

### From Sound to Cause

```text
rattle sound when shaken
steel sound when dropped
cloth low sound when dropped
-> object/action/material influence sound
```

### From Body to Self

```text
hand moves with command
caregiver hand does not move with command
object moves only after contact
-> self body vs external object vs other agent
```

### From Caregiver to Trust

```text
cry -> caregiver response
caregiver voice -> comfort
feeding -> relief
repeated reliability
-> familiar agent / trust precursor
```

### From Object Interaction to Property

```text
cloth drop -> soft/no sound
steel drop -> loud sound
ball push -> roll
rattle shake -> sound
-> soft, hard, round, sound-making
```

### From Repetition to Prediction

```text
peekaboo repeats
spoon returns
rattle sound follows shake
-> expectation
-> surprise when violated
```

## What Should Not Be Added Yet

Do not add these as active concepts at 6 months:

```text
status
laziness
responsibility
fairness
ownership
religion
country
caste
gender identity
mathematics
school
money
career
morality
```

However, their lower components may already exist:

```text
attention
comfort
discomfort
familiarity
prediction
control
effort
agent response
approval-like affect
loss/return
```

For example, status later grows from attention, compliance, resource access,
approval, and social prediction. It is not present as status in this seed.

## First Dataset Generator Target

The first generator should create micro-experiences, not encyclopedic facts.

### Input Fields

```yaml
scene:
  agents: []
  objects: []
  body_state: []
  action:
  sensory_before:
  sensory_after:
  valence_before:
  valence_after:
  relations_observed: []
  language_overlay: optional
```

### Example Generated Item

```yaml
scene_id: baby_6mo_steel_bowl_drop_001
agents:
  - caregiver.primary
  - baby.self
objects:
  - object.steel_bowl
  - surface.floor
action:
  actor: caregiver.primary
  type: drop
  object: object.steel_bowl
sensory_before:
  sound: quiet
  visual: bowl_in_hand
sensory_after:
  visual: bowl_on_floor
  sound: loud_metal_impact
valence_after:
  baby: startle
relations_observed:
  - hard_metal_object + drop -> loud_sound
  - sudden_loud_sound -> startle
  - caregiver_voice_touch -> comfort
language_overlay:
  caregiver_says:
    - "Oh! The bowl fell."
    - "{home_language.primary equivalent if available}"
```

## Evaluation Questions for This Seed

A model trained on this seed should answer or complete simple relation tasks:

```text
If the baby moves his hand, what changes?
If the caregiver moves her hand, is that directly controlled by the baby?
Which makes a louder sound when dropped: steel bowl or cloth?
What usually happens after the baby cries from hunger?
Why is the primary caregiver familiar?
What happens when the rattle is shaken?
Is the ceiling fan part of the baby's body?
Does a ball roll when pushed?
What relation makes the hand part of self?
```

It should also answer contrast questions:

```text
Steel bowl fell. Cloth fell. Which sound was louder?
Baby's hand moved. Ball moved. Which was directly controlled?
Mother disappeared behind cloth and returned. Did she stop existing?
```

The last question should be answered carefully: at 6 months object permanence is
emerging, so the model should represent partial expectation, not adult certainty.

## Roadmap Toward a 5-Year-Old

This file only defines the 6-month seed. A 5-year-old graph should grow through
intermediate stages rather than being written directly.

Suggested stages:

```text
6-12 months:
  crawling, stronger object permanence, first word bindings, intentional dropping

1-2 years:
  walking, object naming, simple commands, "mine" precursor, imitation

2-3 years:
  pretend play, simple causality, basic emotions, toilet/body routines, two-word language

3-4 years:
  why questions, rules, sharing/fairness precursor, counting, stories

4-5 years:
  school readiness, stronger language, social roles, simple morality, early math
```

Each stage should only add concepts that can be built from earlier relation
structures.

## One-Sentence Summary

The 6-month Indian child seed graph begins with body control, caregiver response,
feeding relief, household sensory patterns, object interaction, and pre-word
language bindings, while leaving adult abstractions for later growth from these
lower relational foundations.
