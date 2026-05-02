# Age 6mo Handwritten Relation Authoring Spec

This document is the handoff prompt/spec for generating the full relation set for
the 6-month-old root-world curriculum.

The project is moving away from pure procedural generation for this layer. The
goal is to hand-author high-quality relation bundles concept by concept, while
still keeping the work machine-trackable through a status file.

## Current Working Files

Seed concept list:

```text
data/developmental_graph/seeds/age_6mo_root_world_wordbank_v1.json
```

Authoring status file:

```text
data/developmental_graph/relation_authoring/age_6mo_relation_authoring_status_v0.json
```

Recommended relation output directory:

```text
data/developmental_graph/relation_authoring/age_6mo_handwritten_relations_v0/
```

Recommended batch relation files:

```text
data/developmental_graph/relation_authoring/age_6mo_handwritten_relations_v0/batch_0001.jsonl
data/developmental_graph/relation_authoring/age_6mo_handwritten_relations_v0/batch_0002.jsonl
...
```

The original target was a 500-concept age-6mo seed. The current working seed is
520 concepts because 20 early Wordbank/CDI concepts were added. Use the current
520-concept status file as the source of truth.

## Core Theory

Meaning is relation.

A word is not only a dictionary definition. A word is a handle to a relation
bundle:

- what kind of thing it is
- what parts it has
- what properties it has
- what it can do
- what can be done to it
- where it can be
- what states it can enter
- what causes those states
- what it allows or blocks
- how it relates to body, senses, caregiver, comfort, pain, and action

The model should learn that meaning comes from usable relation structure.

## Target World

Use a neutral US household from the perspective of a 6-month-old baby.

Do not include:

- Indian-specific objects or situations
- school concepts
- politics
- religion
- money
- adult work concepts
- complex morality
- history
- geography
- technical AI terms
- abstract philosophy

## Workflow

1. Read the status file.
2. Pick the next 10 concepts where `authoring_status` is `pending`.
3. Mark those 10 concepts as `in_progress`.
4. Generate high-quality relation rows for only those 10 concepts.
5. Write the rows to one batch JSONL file.
6. Update each concept in the status file:
   - `authoring_status`: `relations_done`
   - `included_in_training_export`: `true`
   - `batch_id`: the batch number
   - `relation_output_file`: the JSONL batch file path
   - `relation_rows_written`: count of relation rows for that concept
   - `qa_rows_written`: count of QA rows for that concept
   - `review_status`: `not_reviewed`
7. Do not mark concepts as `approved`. Approval is a separate human review step.

Status is workflow state only. A concept marked `relations_done` can still be
used by other systems. Status does not mean "locked" or "unavailable."

Allowed `authoring_status` values:

```text
pending
in_progress
relations_done
needs_revision
approved
skipped
```

Allowed `review_status` values:

```text
not_reviewed
reviewed_pass
reviewed_needs_fix
```

## Relation Row Schema

Write JSONL, one JSON object per line.

Every relation row must have:

```json
{
  "id": "age6mo.rel.000001",
  "age_level": "age_6mo",
  "batch_id": "batch_0001",
  "domain": "visibility",
  "subject": "toy",
  "relation": "can_be_hidden",
  "object": "yes",
  "polarity": "positive",
  "confidence": "high",
  "source_type": "hand_authored",
  "supporting_relations": [
    "toy is object",
    "object can be hidden"
  ],
  "plain_text": "A toy can be hidden."
}
```

Required fields:

- `id`
- `age_level`
- `batch_id`
- `domain`
- `subject`
- `relation`
- `object`
- `polarity`
- `confidence`
- `source_type`
- `supporting_relations`
- `plain_text`

Field rules:

- `id` must be unique and sequential across the whole dataset.
- `age_level` must always be `age_6mo`.
- `source_type` must always be `hand_authored`.
- `polarity` must be `positive` or `negative`.
- `confidence` must be `high`, `medium`, or `low`.
- `plain_text` must be short, natural, and simple.
- `supporting_relations` may be empty only for primitive/root relations.
- Each row must be one atomic relation.
- Do not put long explanations in `plain_text`.
- Avoid complex vocabulary.

## Optional QA Row Schema

Most rows should be relation rows. Some rows can be QA rows when useful for
training or evaluation.

```json
{
  "id": "age6mo.qa.000001",
  "age_level": "age_6mo",
  "batch_id": "batch_0001",
  "domain": "visibility",
  "row_type": "qa",
  "question": "Can the baby see a toy under a blanket?",
  "answer": "No.",
  "expected_relation": "toy under blanket cannot_be_seen baby",
  "supporting_relations": [
    "blanket can cover toy",
    "cover hides object",
    "hidden object cannot be seen"
  ],
  "source_type": "hand_authored"
}
```

QA rows should be no more than 20 percent of a batch.

## Relation Vocabulary

Use these relation names unless a new one is clearly required.

Hard rule:

The `relation` field must exactly match one of the allowed relation names in
this section. Do not invent relation names. Do not use spaces in relation names.

Bad relation names:

```text
can hold
can_hold
can cover
can contain
cannot contain
supports
helps_baby
can_be
can_have
can_change
can_show
can_apply_to
can_relate_to
can_create
can_support
describes
relates
marks
enables
improves
helps
```

If no exact relation fits, use the closest concrete fallback:

```text
is_a
has_part
part_of
has_state
has_property
can_do
cannot_do
can_be_done_to
cannot_be_done_to
causes
prevents
allows
blocks
reduces
increases
changes_state_to
contrasts_with
can_control
cannot_control
creates_new_relation
strengthens_relation
weakens_relation
breaks_relation
```

Examples:

```text
Bad:  "relation": "can cover"
Good: "relation": "covers"

Bad:  "relation": "can_hold"
Good: "relation": "can_do", "object": "hold one object"

Bad:  "relation": "can contain"
Good: "relation": "allows", "object": "object inside"

Bad:  "relation": "marks"
Good: "relation": "body_boundary"
```

Identity/kind:

```text
is_a
same_as
different_from
contrasts_with
```

Parts:

```text
part_of
has_part
```

Properties:

```text
has_property
has_state
usually_has_state
can_have_state
```

Ability/action:

```text
can_do
cannot_do
can_be_done_to
cannot_be_done_to
can_move
cannot_move
can_be_moved
causes_movement
stops_movement
```

Sense:

```text
can_be_seen
cannot_be_seen
can_be_heard
cannot_be_heard
can_be_touched
cannot_be_touched
can_be_tasted
cannot_be_tasted
can_be_smelled
cannot_be_smelled
```

Space:

```text
near_to
far_from
inside
outside
under
over
on
off
in_front_of
behind
above
below
next_to
```

Access/blocking:

```text
allows
blocks
prevents
opens_access_to
closes_access_to
hides
reveals
covers
uncovers
```

Cause/effect:

```text
causes
can_cause
reduces
increases
changes_state_to
changes_relation_to
depends_on
```

Body/self:

```text
body_part_of
self_controlled
not_self_controlled
can_control
cannot_control
body_boundary
touched_by_body
not_touched_by_body
```

Caregiver/social:

```text
caregiver_action
responds_to
helps
soothes
feeds
holds
cleans
protects
plays_with
```

Comfort/affect:

```text
causes_comfort
causes_discomfort
causes_pain
reduces_pain
causes_hunger
reduces_hunger
causes_tiredness
reduces_tiredness
causes_happiness
causes_distress
reduces_distress
causes_sadness
creates_new_relation
strengthens_relation
weakens_relation
breaks_relation
```

Developmental cognition:

```text
supports_object_permanence
supports_prediction
supports_attention
supports_memory
supports_expectation
supports_relation_learning
```

## Core Domains

Every concept does not need every domain, but the full dataset should cover:

1. root primitives
2. body
3. senses
4. caregiver
5. comfort and pain
6. hunger and feeding
7. sleep and tiredness
8. touch and reach
9. visibility and hiding
10. sound
11. movement
12. near and far
13. inside and outside
14. open and closed
15. support and falling
16. containment
17. blockage and access
18. common objects
19. common rooms and places
20. simple social response
21. simple emotion
22. object permanence
23. simple causality
24. relation learning and happiness

## Required Coverage Patterns

### Root Primitives

Include relations such as:

- object `is_a` thing
- body `is_a` thing
- body `has_part` hand
- event `changes` state
- action `can_cause` change
- relation `links` things
- state `describes` thing
- cause `can_make` effect
- same `contrasts_with` different
- yes `confirms` relation
- no `denies` relation

### Body/Self Boundary

Include relations such as:

- baby has body
- hand body_part_of baby
- foot body_part_of baby
- baby can_control hand
- baby can_control foot
- baby cannot_control toy
- baby cannot_control caregiver
- hand movement is self_controlled
- toy movement is not_self_controlled unless caused by body
- touch by hand marks body boundary
- pain in body belongs to baby
- caregiver touch is not self-controlled but affects baby

### Touch/Reach

Include relations such as:

- hand can touch near object
- hand cannot touch far object
- hand can reach near toy
- hand cannot reach high toy
- hand can hold small object
- hand cannot hold object inside closed box
- open box allows hand reach
- closed box blocks hand reach
- reachable object can be touched
- unreachable object cannot be touched

### Visibility/Hiding

Include relations such as:

- visible object can be seen
- hidden object cannot be seen
- cover hides object
- blanket can cover toy
- closed box can hide toy
- open box can reveal toy
- toy under blanket may be hidden
- removing blanket can reveal toy
- dark room reduces seeing
- bright light helps seeing
- object behind caregiver may be hidden
- hidden object can still exist

### Sound

Include relations such as:

- loud sound can be heard
- quiet sound may be hard to hear
- rattle can make sound
- caregiver voice can be heard
- closed door can reduce sound
- sound can draw baby attention
- sudden sound can startle baby
- soft voice can soothe baby

### Movement/Physics

Include relations such as:

- ball can roll
- block does not roll easily
- dropped object can fall
- falling object moves down
- hand can push ball
- pushed ball can move
- held object may stay up
- unsupported object can fall
- floor stops falling
- heavy object is harder to move
- light object is easier to move

### Inside/Outside/Containment

Include relations such as:

- object can be inside box
- object can be outside box
- open box allows seeing inside
- closed box blocks seeing inside
- open box allows putting object inside
- closed box blocks putting object inside
- object inside container moves with container sometimes
- object inside container may be hidden

### Open/Closed/Access

Include relations such as:

- open allows access
- closed blocks access
- open door allows going through
- closed door blocks going through
- open drawer allows seeing inside
- closed drawer hides inside
- open mouth allows food
- closed mouth blocks food
- open hand can release object
- closed hand can hold object

### Hunger/Feeding

Include relations such as:

- hunger causes discomfort
- milk reduces hunger
- food reduces hunger
- bottle can contain milk
- caregiver feeds baby
- feeding can cause comfort
- full reduces hunger
- hunger can cause crying
- caregiver may respond to crying with feeding
- too hot food can hurt
- safe food helps baby

### Sleep/Tiredness

Include relations such as:

- tiredness causes discomfort
- sleep reduces tiredness
- crib supports sleep
- caregiver soothing can help sleep
- loud sound can wake baby
- dark room can help sleep
- comfort can help sleep

### Pain/Safety

Include relations such as:

- pain causes distress
- hurt body part causes crying
- soft object reduces pain risk
- hard object can hurt if hit
- hot object can hurt
- sharp object can hurt
- caregiver protects baby
- safe place reduces harm
- unsafe object should be blocked

### Comfort/Happiness Theory

Use this carefully:

- comfort causes happiness
- reducing pain causes comfort
- reducing hunger causes comfort
- caregiver smile can cause happiness
- caregiver soft voice can cause comfort
- caregiver touch can cause comfort
- new useful relation can cause happiness
- repeated known relation gives less new happiness than first relation
- broken comfort relation can cause sadness
- caregiver going away can cause distress
- caregiver returning can reduce distress

Keep `plain_text` simple:

- Milk can reduce hunger.
- Less hunger feels good.
- Pain feels bad.
- A soft voice can feel good.
- A new useful link can feel good.

### Object Permanence/Prediction

Include relations such as:

- hidden toy can still exist
- toy under blanket can come back
- repeated event supports prediction
- caregiver leaving may be followed by caregiver returning
- dropped object may be found on floor
- sound from hidden object can suggest object exists
- seeing object again strengthens memory

### Relation Learning

Include relations such as:

- touching object creates relation between hand and object
- seeing object creates relation between eye and object
- hearing sound creates relation between ear and sound
- repeated touch strengthens relation
- repeated sound strengthens relation
- new relation can cause interest
- stronger relation supports expectation
- broken expected relation can cause surprise

## Negative Rows

Negative rows are required when they are useful.

Good negative rows:

- baby cannot touch far toy
- baby cannot see hidden toy
- closed box blocks seeing inside
- closed hand cannot release object
- baby cannot control caregiver hand
- quiet sound may not be heard
- dark room makes seeing harder

Bad negative rows:

- milk cannot sing
- chair cannot feel shame
- blanket cannot do math

Avoid absurd negatives. They are not useful for this curriculum.

## Contrast Pairs

Create useful contrast pairs:

- open allows access / closed blocks access
- near allows touch / far blocks touch
- visible allows seeing / hidden blocks seeing
- soft reduces hurt / hard can hurt
- held prevents falling / let go allows falling
- caregiver near can comfort / caregiver away can distress

## Training Purpose

The dataset should help the model answer unseen questions by combining learned
relations.

Example:

Training relations:

- toy is object
- object can be hidden
- hidden object cannot be seen
- blanket can cover toy

Held-out test:

```text
Question: Can the baby see the toy under the blanket?
Expected answer: No.
Reason: the blanket can cover and hide the toy.
```

The aim is not memorization. The aim is relation bundles and inference paths.

## Batch Size

Use batches of 10 concepts.

For each concept, generate enough rows to give it a usable relation bundle.
Typical target:

- normal concept: 20 to 30 rows
- root/primitive concept: 20 to 30 rows, anchored to concrete baby-world examples
- body/sense/action concept: 25 to 45 rows
- common object: 25 to 60 rows
- important connector concept such as open, closed, near, far, hidden: 50 to 120 rows

Quality is more important than count.

The full 520-concept layer should therefore be expected to exceed 10,000 rows.
The earlier 3,000-6,000 row range is too small for this hand-authored relation
layer. The goal is dense relation coverage, not a minimal sample.

## Final Instruction For Claude

Use the status file to select the next 10 pending concepts. Generate only those
10 concepts. Write the relation rows as JSONL. Then update the status file for
those 10 concepts. Do not change the status for other concepts. Do not mark
anything as approved.
