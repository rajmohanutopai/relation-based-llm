# Age 6mo Root World 500

Date: 2026-05-01

Seed:

```text
data/developmental_graph/seeds/age_6mo_root_world_500.json
```

Generator:

```text
scripts/create_age_6mo_root_world_500.py
```

Generated curriculum:

```text
data/developmental_graph/experiments/age_6mo_root_world_500/curriculum.jsonl
```

## Purpose

This is the first full 500-concept seed for the 6-month root world.

These are not spoken words that a 6-month-old child knows. They are concept
handles for embodied relations that a word-trained model needs to represent as
tokens:

```text
touch, reach, near, far, hunger, comfort, caregiver gone, object appears,
object falls, familiar voice, blocked reach, new link, strong link
```

## Counts

```text
concepts: 500
relations: 1092
curriculum rows: 3155
```

Category allocation:

```text
core_relation:              45
body_part:                  35
body_action_control:        40
sensory_input:              55
body_state_valence:         50
space_motion_physics:       55
object_property:            40
common_object:              55
caregiver_social:           35
routine_event:              45
sound_language_precursor:   25
learning_memory:            20
```

Status allocation:

```text
active:                     407
emerging:                    69
latent:                      14
internal:                    10
```

## Design Logic

The 6-month root world is not organized as school subjects. It is organized
around what can be behaviorally grounded:

```text
body and control
sensory input
space and contact
needs and valence
objects and properties
caregiver/social regulation
routine event patterns
sound/language precursors
learning and relation-strength primitives
```

This is why the count is much larger than spoken vocabulary. A 6-month child may
not know the word `far`, but the relation is behaviorally active when reaching
fails.

The current revision makes the root anchors explicit concepts instead of
permissive validation exceptions. Handles such as `sound`, `see`, `move`,
`attention`, `need`, `support`, `surface`, `boundary`, `part`, and `whole` are
now part of the concept graph. More advanced handles are marked as `emerging`,
`latent`, or `internal` rather than treated as fully active.

Sensory coverage now includes smell, inner-body feel, and balance/proprioceptive
feel. Object entries also carry richer relation bundles for feeding, comfort,
play, rolling, sound, open/closed state, living movement, and discomfort.

The concept inventory is US-first. Earlier India-specific handles were replaced:

```text
dal -> oatmeal
ragi -> applesauce
nappy -> wipes
pressure cooker whistle -> vacuum sound
```

The 0.3 revision makes the graph stricter and cleans up the concept inventory:

```text
closed relation vocabulary: 18 relation types
unknown relation targets:   0
unknown relation types:     0
forward prerequisites:      0
one-relation concepts:      0
scene relation rows:        1063
```

It adds `internal` status for ontology handles such as `relation`, `state`,
`event`, `action`, `input`, `time now`, `cause`, and `effect`. It also adds
missing root handles for desire/control/social regulation:

```text
wanted, not wanted, too much, enough, can control, cannot control,
alone, with caregiver, not held, safe touch, start, stop, again,
gone, back again, body limit
```

The latest cleanup also moved several abstract but useful handles from `active`
to `emerging`, including:

```text
support, boundary, physical support, contact, no contact, waiting,
sound pattern, repetition comfort, success feeling, blocked feeling
```

Relation targets now point either to another concept in this file or to a small
declared external-anchor list:

```text
world, word, new, access, feeding
```

## Examples

```text
far
  summary: large distance from body or thing
  relations:
    far prevents touch
    far can cause reach fail
    far contrasts with near
```

```text
reach fail
  summary: hand moves but touch does not happen
  prerequisites: reach, far
  relations:
    reach fail can be caused by far
```

```text
caregiver gone
  summary: familiar caregiver not visible or near
  relations:
    caregiver gone is linked to person relation
    caregiver gone can cause discomfort
```

```text
new link
  summary: new relation is created
  relations:
    new link updates strong link
    new link can cause happy
    new link is linked to curiosity
```

Scene-style curriculum example:

```text
Scene: far is present. The baby tries touch. touch does not happen.
Question: What relation is shown?
Answer: far prevents touch.
```

## Validation

Commands run:

```text
python -m py_compile scripts/create_age_6mo_root_world_500.py
python scripts/create_age_6mo_root_world_500.py --overwrite
python -m json.tool data/developmental_graph/seeds/age_6mo_root_world_500.json
python -m json.tool data/developmental_graph/experiments/age_6mo_root_world_500/manifest.json
```

Validation result:

```text
expected_total: 500
actual_total: 500
duplicate_words: 0
missing_prerequisites: 0
forward_prerequisites: 0
unknown_relation_targets: 0
unknown_relation_types: 0
empty_relation_bundles: 0
category_count_mismatches: 0
passes: true
```

## Important Limit

This is now a stricter root graph plus a first scene renderer. It is still not
the final model curriculum. The generated scenes are template-based and should
be followed by a richer scenario renderer that combines multiple relations into
natural episodes.
