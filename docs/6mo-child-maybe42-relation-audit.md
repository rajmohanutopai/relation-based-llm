# 6-Month Maybe-42 Encounter Relation Audit

Status: derived relation audit.

Source inventory: `docs/6mo-child-200-encounters.md`

## Purpose

This file reviews the 42 encounters currently marked:

```text
Include in top 30 = maybe
```

This is separate from the raw encounter inventory. The raw file remains
observational; this file is where relation interpretation and graph coverage
checking belongs.

## Summary

After the top-44 additions, most of the maybe-42 encounters are partially or
fully covered. The remaining gaps were practical experience families rather
than new theory, and are now added as a second seed-graph layer:

```text
wake transition and waking from stimulus
stimulation reduction / overstimulation
feeding pause or delayed relief
gas/burping/internal discomfort
orienting head toward sound or motion
smiling face as social visual cue
unfamiliar person approach
other child crying / social arousal
routine words and early action-word exposure
book/picture + speech exposure
light/dark switching
carried room-to-room context transition
mirror/reflection
object removal / end of play
```

## Coverage Table

Coverage values:

```text
covered = already represented well enough in the seed graph
partial = represented indirectly, but needs refinement
missing = not yet represented clearly enough
```

The table records the audit state before the maybe-layer implementation. The
implemented additions are listed after the table.

| ID | Encounter | Relation families visible | Coverage | Gap or action |
|---:|---|---|---|---|
| E001 | Waking from sleep in a familiar sleeping place | sleep/wake transition, familiar place | partial | Add wake transition. |
| E006 | Crying or fussing after waking | cry, discomfort, caregiver response | covered | Covered by cry-caregiver response and comfort repair. |
| E013 | Waking because of sound, light, temperature, or movement | stimulus wakes baby, arousal change | partial | Add waking-from-stimulus and stimulation regulation. |
| E018 | Sleepy fussing before a nap | sleepy, fussing, sleep transition | covered | Covered by sleep transition. |
| E019 | Being soothed with reduced sound and light | stimulation reduction, comfort repair | partial | Add stimulation regulation. |
| E024 | Feeding pausing before the child is done | interrupted feeding, expected relief delay | partial | Add feeding interruption/delay. |
| E027 | Gas, burping, or stomach discomfort | internal pressure/discomfort, caregiver handling | missing | Add internal gas/discomfort schema. |
| E043 | Seeing a food bowl, spoon, bottle, or feeding cloth | routine feeding cues | partial | Add feeding setup cue prediction. |
| E048 | Food being delayed after the child shows hunger | delayed relief, frustration | partial | Add expected relief delay. |
| E056 | Rolling from back toward tummy | body orientation change | covered | Covered by body orientation change. |
| E057 | Rolling from tummy toward back | body orientation change | covered | Covered by body orientation change. |
| E061 | Turning head toward sound or movement | orienting response, head movement, attention | missing | Add orienting-to-sound/motion schema. |
| E064 | Sitting briefly with support from cushions, lap, or hands | posture support | covered | Covered by posture support. |
| E069 | Reaching toward something too far away | reach limit, frustration | covered | Covered by reach-grasp and blocked action frustration. |
| E080 | Being helped into a new position by caregiver | assisted movement, context/body transition | partial | Add caregiver-assisted carry/context transition. |
| E081 | Soft cloth, blanket, or caregiver clothing touching skin | soft contact | covered | Covered by soft property and cloth/blanket. |
| E093 | Feeling too cold after bath, fan, weather, or clothing change | cold discomfort, regulation | covered | Covered by temperature comfort. |
| E108 | Hearing a changed rattle rhythm or changed play pattern | changed pattern, novelty after repetition | covered | Covered by novelty and happiness saturation. |
| E111 | Watching cloth, blanket, or soft toy fall | soft object fall | covered | Covered by cloth drop contrast. |
| E112 | Watching a spoon, bowl, or hard toy fall | hard object fall and sound | covered | Covered by drop-sound and steel bowl/spoon family. |
| E113 | Touching or banging a steel bowl, plate, spoon, or cup | hard metal object, touch, loud sound | covered | Covered by steel bowl and loud property. |
| E130 | Caregiver moving a fragile or unsafe object away | unsafe object, safety blocking | covered | Covered by caregiver safety block. |
| E132 | Caregiver smiling | smiling face, positive social cue | partial | Add smiling-face property. |
| E136 | Caregiver copying the child's sound or facial movement | imitation, turn-taking | covered | Covered by imitation/turn-taking. |
| E138 | Peekaboo with caregiver face or cloth | hide/reappear, social play | covered | Covered by peekaboo. |
| E143 | Father, grandparent, sibling, or familiar relative holding the child | secondary caregiver comfort | partial | Add secondary caregiver comfort relation. |
| E145 | Stranger or less familiar person approaching | unfamiliar approach, distance change | partial | Add unfamiliar-agent approach schema. |
| E149 | Hearing another baby or child cry | other distress sound, arousal | missing | Add other-child cry/arousal schema. |
| E150 | Being comforted by someone other than the primary caregiver | secondary caregiver comfort | partial | Add secondary caregiver comfort relation. |
| E158 | Hearing repeated syllables from caregiver speech | repeated speech sound | covered | Covered by rhythm, imitation, and turn-taking. |
| E159 | Hearing home-language words during feeding, bathing, dressing, or play | routine-word exposure | partial | Add routine-word/action exposure. |
| E161 | Seeing book pictures while someone speaks | picture + speech | missing | Add book/picture word exposure. |
| E162 | Seeing an animal, vehicle, person, or object while someone names it | joint attention + naming | partial | Add generic object-name sound handle. |
| E163 | Hearing yes/no, come, give, take, eat, sleep, or similar routine words | routine action words | missing | Add routine-word/action exposure. |
| E172 | Light being switched on or off | brightness/darkness change | missing | Add light-change schema. |
| E175 | Pressure cooker whistle, mixer, grinder, or kitchen appliance sound | kitchen appliance loud sound | partial | Add generic kitchen appliance sound context. |
| E185 | Being carried from one room to another | caregiver-carried context transition | missing | Add carried room-to-room transition. |
| E186 | Being placed on a floor mat, cot, bed, or play area | support surface and play context | covered | Covered by support surface and comfort exploration readiness. |
| E191 | Seeing own image and caregiver image in a mirror | reflection, visual similarity | missing | Add mirror/reflection schema. |
| E194 | Toy being taken away for cleaning, safety, or end of play | object removal, blocked play | partial | Add object removal/end-of-play schema. |
| E198 | Many visitors, loud sounds, bright lights, or too much activity | overstimulation | missing | Add overstimulation/stimulation regulation. |
| E200 | Quiet time alone while awake, looking around or self-playing briefly | calm alert self-play | covered | Covered by comfort exploration readiness. |

## Missing Relation Families

### 1. Waking and Stimulation Regulation

```text
schema.wake_transition
schema.stimulation_regulation
property.bright_light
property.darkness
property.overstimulating
```

### 2. Feeding Delay, Gas, and Feeding Cues

```text
schema.feeding_interruption_delay
schema.internal_discomfort_gas
context.feeding_setup
property.gas_discomfort
```

### 3. Orienting and Assisted Context Change

```text
schema.orienting_to_sound_motion
schema.carry_context_transition
```

### 4. Social Signals Beyond Primary Caregiver

```text
property.smiling_face
schema.unfamiliar_agent_approach
schema.other_cry_arousal
agent.other_child
```

Also add a stronger relation from `agent.secondary_caregiver` to comfort/holding.

### 5. Routine Words, Pictures, and Naming

```text
schema.routine_word_action
schema.picture_word_exposure
language.routine_word
language.object_name_sound
object.book_picture
```

### 6. Light, Mirror, Object Removal, and Household Sound

```text
schema.light_change
schema.mirror_reflection
schema.object_removal_frustration
object.mirror
context.kitchen_appliance_sound
```

## Implemented Additions

Implementation status:

```text
Added to docs/developmental-relation-graph.md
Added to docs/seed-agent-6mo-indian-child.md
Added to data/developmental_graph/seeds/agent_6mo_indian_child.json
```

Added schema families:

```text
schema.wake_transition
schema.stimulation_regulation
schema.feeding_interruption_delay
schema.internal_discomfort_gas
schema.orienting_to_sound_motion
schema.object_removal_frustration
schema.unfamiliar_agent_approach
schema.other_cry_arousal
schema.routine_word_action
schema.picture_word_exposure
schema.light_change
schema.carry_context_transition
schema.mirror_reflection
```

Added supporting nodes:

```text
property.gas_discomfort
property.bright_light
property.darkness
property.overstimulating
property.smiling_face
agent.other_child
object.book_picture
object.mirror
context.feeding_setup
context.kitchen_appliance_sound
context.room_place
language.routine_word
language.object_name_sound
```

Added micro-experience probes:

```text
experience.wake_stimulation_regulation_001
experience.feeding_delay_gas_001
experience.orienting_carry_light_001
experience.social_smile_stranger_other_cry_001
experience.routine_words_picture_naming_001
experience.mirror_reflection_001
experience.object_removed_overstimulation_001
```

Added evaluation probes:

```text
eval.wake_stimulation_regulation
eval.feeding_delay_gas
eval.orienting_to_sound_motion
eval.social_smile_stranger_other_cry
eval.routine_words_picture_naming
eval.light_carry_transition
eval.mirror_reflection
eval.object_removal_overstimulation
```
