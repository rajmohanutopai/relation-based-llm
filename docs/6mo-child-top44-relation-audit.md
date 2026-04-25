# 6-Month Top-44 Encounter Relation Audit

Status: derived relation audit.

Source inventory: `docs/6mo-child-200-encounters.md`

## Purpose

This file looks only at the 44 encounters currently marked:

```text
Include in top 30 = yes
```

This is intentionally separate from the raw encounter inventory. The raw file
should remain observational. This file is where we derive relation families and
check whether the current seed graph has enough coverage.

## Summary

The current seed graph covers the main foundation well:

```text
caregiver presence/absence/return
hunger -> feeding -> relief
self-motion and own hand
reach/grasp/mouth exploration
drop -> sound
rattle shake/repetition/saturation
wetness -> changing
temperature discomfort
body bump/pain/comfort repair
hide/reappear
caregiver soft/sharp tone
joint attention
own-name sound
lullaby/rhythm
babbling/turn-taking
ceiling fan as moving non-self object
```

The audit shows that we have not missed the core theory, but we have missed
some practical relation families needed for the first child-world dataset.

Implementation status:

```text
Added to docs/developmental-relation-graph.md
Added to docs/seed-agent-6mo-indian-child.md
Added to data/developmental_graph/seeds/agent_6mo_indian_child.json
```

## Coverage Table

Coverage values:

```text
covered = already represented well enough in the seed graph
partial = represented indirectly, but needs refinement
missing = not yet represented clearly enough
```

| ID | Encounter | Relation families visible | Coverage | Gap or action |
|---:|---|---|---|---|
| E002 | Waking and finding no caregiver immediately visible | caregiver absence, wake state, expected presence | partial | Add wake-context variant to caregiver absence/distress. |
| E003 | Being picked up after waking | caregiver holding, lift, body position change | partial | Holding exists; lift/carry/vestibular change is not explicit. |
| E021 | Feeling hungry before a feed | hunger, discomfort, care need | covered | Already covered by feeding relief. |
| E022 | Feeding from breast | feeding, mouth contact, satiety, caregiver closeness | partial | Generic feeding exists; breast-specific source can remain configurable. |
| E023 | Feeding from bottle | feeding, mouth contact, flow, satiety | partial | Generic feeding exists; bottle/nipple/flow variant is not explicit. |
| E026 | Turning away or closing the mouth when full | satiety, refusal, stop signal | partial | Add satiety/fullness/refusal as feeding completion. |
| E031 | Tasting a new puree or soft food | new taste, texture, mouth exploration | partial | Food texture/acceptance is weaker than aversion. |
| E033 | Rejecting a bitter, sour, or unpleasant taste | unpleasant taste, mouth aversion | covered | Covered by mouth aversion. |
| E037 | A spoon approaching the mouth | approaching object, caregiver feeding action, mouth contact | missing | Add object-approach-to-mouth / spoon feeding schema. |
| E051 | Moving hands while lying down | self-motion, direct control | covered | Covered by self-motion. |
| E052 | Watching own hand move | visual-proprioceptive match, self-motion | covered | Covered by self-motion, but can use a visual-match example. |
| E055 | Rolling from back toward side | body orientation, self-motion, effort | partial | Add body-orientation/rolling schema. |
| E059 | Pushing up during tummy time | support, pressure, effort, head/body posture | partial | Add posture-support/effort schema. |
| E063 | Leaning on hands while sitting with support | balance, support, posture | missing | Add supported-sitting/balance schema. |
| E065 | Losing balance while sitting | instability, fall/tilt, possible catch | missing | Add balance-loss/fall-risk schema. |
| E068 | Reaching toward a visible toy | reach, distance, attention | covered | Covered by reach-grasp-mouth. |
| E070 | Grasping a toy or household object | hand contact, grasp, control of object | covered | Covered by reach-grasp-mouth. |
| E072 | Dropping a held object | release, fall, impact, sound | covered | Covered by drop-sound. |
| E074 | Bringing an object to the mouth | hand-to-mouth, mouth exploration | covered | Covered by reach-grasp-mouth. |
| E083 | Wet diaper, nappy, cloth, or clothing | wetness, discomfort | covered | Covered by wetness relief. |
| E084 | Diaper, nappy, or clothing change | caregiver cleaning/changing, relief | covered | Covered by wetness relief. |
| E086 | Bath water touching the body | water contact, temperature, caregiver support | partial | Add bath/water-contact schema distinct from wet diaper. |
| E092 | Feeling too hot in clothing, bedding, or room | heat discomfort, regulation | covered | Covered by temperature comfort. |
| E095 | Minor bump while moving, rolling, or being carried | impact, pain, caregiver repair | covered | Covered by body impact pain. |
| E106 | Holding and shaking a rattle | grasp, hand motion, sound | covered | Covered by shake-sound. |
| E107 | Hearing the same rattle sound many times | repetition, habituation, saturation | covered | Covered by novelty/habituation and happiness saturation. |
| E109 | Watching a ball roll nearby | round object, motion, rolling | partial | Ball exists; push/roll event should be explicit in seed JSON. |
| E116 | Toy or face being hidden under cloth | hiding, disappearance | covered | Covered by hide-reappear. |
| E117 | Hidden toy or face appearing again | reappearance, surprise/play | covered | Covered by hide-reappear and peekaboo. |
| E131 | Caregiver face close to the child | face proximity, familiar visual cue | partial | Familiar caregiver exists; face-proximity signal is not explicit. |
| E134 | Caregiver speaking softly | familiar voice, comfort, positive activation | covered | Covered by caregiver emotional tone and soft voice. |
| E135 | Caregiver speaking sharply, loudly, or with visible tension | sharp tone, uncertainty, discomfort | covered | Covered by caregiver emotional tone, but can use a sharper example. |
| E139 | Caregiver looking at, pointing at, or holding up an object | joint attention, attention shift | covered | Covered by joint attention. |
| E141 | Primary caregiver leaving the room briefly | caregiver absence, blocked expected relation | covered | Covered by sadness/connection-loss precursor. |
| E142 | Primary caregiver returning after an absence | return, repair, reactivation | partial | Absence exists; return/reactivation should be explicit. |
| E156 | Hearing the child's name or name-like sounds repeatedly | own-name sound, attention-to-self | covered | Covered by own-name sound pattern. |
| E157 | Hearing a lullaby, rhyme, chant, or repeated song | rhythm, repeated voice, soothing | covered | Covered by rhythm/song comfort. |
| E167 | Babbling and receiving caregiver response | turn-taking, imitation, social response | covered | Covered by imitation and turn-taking. |
| E171 | Watching a ceiling fan or moving fan | moving distant object, non-self motion | covered | Covered by ceiling fan non-self motion. |
| E173 | Door opening, closing, knocking, or bell ringing | boundary change, household sound, appearance/disappearance | missing | Add door/open-close/bell schema or context object. |
| E193 | Caregiver preventing mouthing, touching, crawling, or reaching | blocked action, safety intervention | missing | Add caregiver safety-blocking schema. |
| E196 | Vaccination, doctor visit, medicine, or health check | unfamiliar place/agent, pain/medicine, caregiver repair | partial | Needs split; pain and medicine are partial, doctor/clinic missing. |
| E197 | Illness, blocked nose, fever, tiredness, or unusual fussiness | internal body discomfort, low energy, care need | missing | Add illness/fatigue body-state schema. |
| E199 | Calm play after feeding, sleep, changing, and basic needs are met | regulated state, exploration readiness | partial | Add comfort-supported exploration/readiness schema. |

## Missed Relation Families

These are the main gaps found from the 44 core encounters.

### 1. Body Orientation, Posture, and Balance

Needed for:

```text
E055 rolling
E059 tummy-time push-up
E063 supported sitting
E065 losing balance
```

Proposed additions:

```text
schema.body_orientation_change
schema.posture_support
schema.balance_instability
invariant.supported_unsupported
invariant.body_orientation
```

### 2. Feeding Completion and Spoon Approach

Needed for:

```text
E026 turning away when full
E031 new puree
E037 spoon approaching mouth
```

Proposed additions:

```text
schema.feeding_completion
schema.spoon_approach_mouth
property.food_texture
property.food_familiarity
object.spoon
object.bottle
```

### 3. Bath and Water Contact

Needed for:

```text
E086 bath water touching the body
```

Proposed additions:

```text
schema.bath_water_contact
property.wet_body
property.water_temperature
```

This should be separate from wet diaper because bath water can be positive,
neutral, or negative depending on temperature, handling, and routine.

### 4. Ball Rolling Event

Needed for:

```text
E109 watching a ball roll nearby
```

Proposed additions:

```text
event.ball_roll
schema.push_roll
```

The graph has `object.ball` and `property.round`, but the seed JSON should make
rolling as an event relation explicit.

### 5. Face Proximity and Social Visual Signals

Needed for:

```text
E131 caregiver face close
E134 soft voice
E135 sharp voice
```

Proposed additions:

```text
property.familiar_face
schema.face_proximity_attention
```

The current caregiver node already implies this, but a baby-world dataset will
need face-specific encounters.

### 6. Door, Boundary, and Household Signal

Needed for:

```text
E173 door opening, closing, knocking, or bell ringing
```

Proposed additions:

```text
object.door
schema.open_close_boundary
context.doorbell_or_knock
```

This is useful because door opening/closing combines visual boundary change,
sound, appearance/disappearance, and visitor expectation.

### 7. Caregiver Safety Blocking

Needed for:

```text
E193 caregiver preventing mouthing, touching, crawling, or reaching
```

Proposed additions:

```text
schema.caregiver_safety_block
schema.blocked_action_frustration
property.unsafe_object
```

This is a precursor to prohibition, rule, danger, permission, and later social
norms. It should not become morality yet.

### 8. Medical/Illness Body State

Needed for:

```text
E196 vaccination, doctor visit, medicine, or health check
E197 illness, blocked nose, fever, tiredness, unusual fussiness
```

Proposed additions:

```text
schema.medical_pain_care
schema.illness_discomfort
property.feverish
property.blocked_breathing
agent.unfamiliar_caregiver_or_doctor
context.clinic
```

E196 should be split before conversion because it mixes multiple events:
vaccination, doctor visit, medicine, and health check.

### 9. Comfort-Supported Exploration

Needed for:

```text
E199 calm play after needs are met
```

Proposed additions:

```text
schema.comfort_exploration_readiness
```

This is important for the theory because comfort is not identical to happiness,
but comfort makes exploration and new relation gain easier.

## Implemented Additions

The following relation families were added to the design docs and parseable seed
graph:

```text
schema.body_orientation_change
schema.posture_support
schema.balance_instability
schema.feeding_completion
schema.spoon_approach_mouth
schema.bath_water_contact
schema.push_roll
schema.open_close_boundary
schema.caregiver_safety_block
schema.illness_discomfort
schema.comfort_exploration_readiness
```

The JSON seed also now includes supporting properties, objects/contexts, events,
micro-experiences, and evaluation questions for these families.
