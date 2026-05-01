# Root Concept Foundation V0

Date: 2026-04-30

Experiment ID:

```text
root_concept_foundation_v0
```

## Purpose

This starts the TinyStories relation-first path.

The goal is not to define every future word by repeating all its facts. The
goal is to train root anchors and inheritance behavior first, so later words
can attach compactly.

Example:

```text
animal can move
animal can feel pain
animal can make sound
```

should live in the root foundation. Later, TinyStories does not need:

```text
puppy can move
puppy can feel pain
puppy can make sound
```

as flat repeated facts. Instead, the later word-attachment stage can say:

```text
dog is animal
puppy is young dog
puppy can be pet
```

Then the model should learn to reuse the animal, young-animal, and pet anchors.

## Current Scope

The generated root graph contains:

```text
layers: 12
nodes: 95
relations: 112
micro experiences: 10
evaluation questions: 10
```

Root areas:

```text
root concepts: thing, relation, event, state, object, place
sensory: touch, see, hear, taste, smell, body feel
body/self: body, hand, mouth, eye, ear, nose, skin, leg, self
space: near, far, up, down, inside, outside, on, under
physical: move, touch, fall, hit, block, push, pull, open, closed, hold
properties: hard, soft, hot, cold, wet, dry, big, small, heavy, light, sharp, round
living: living thing, person, animal, plant, child, adult, young animal
needs/valence: food, water, sleep, air, pain, comfort, good, bad
emotion: happy, sad, afraid, angry, want
social: caregiver, mom, dad, help, hurt, give, take, share, role, pet
language: word, name, say, hear word, story, question, answer
time/change: before, after, cause, effect, again, start, stop
```

## Dataset Variants

Generator:

```text
scripts/create_root_concept_foundation_v0.py
```

Seed graph:

```text
data/developmental_graph/seeds/root_concept_foundation_v0.json
```

Generated dataset:

```text
data/developmental_graph/experiments/root_concept_foundation_v0/
```

Variants:

```text
root_prose   normal prose only
root_qa      QA/probe format only
root_mixed   prose + QA together
```

Counts:

```text
root_prose: 100 train, 18 dev, 14 curriculum_test
root_qa:    108 train,  8 dev, 16 curriculum_test
root_mixed: 208 train, 26 dev, 30 curriculum_test
```

## Example Records

Prose:

```text
The baby feels pain. The caregiver helps the baby. Help can reduce pain and bring comfort.
```

QA:

```text
Scene: An animal is a living thing. A living thing needs food.
Question: What follows by inheritance?
Answer:
```

Target:

```text
answer: animal needs food because animal is living thing.
reason: relation passes through the middle concept.
```

Root relation:

```text
Question: What relation connects place and thing?
Answer:
```

Target:

```text
answer: place is thing.
reason: this is a root relation.
```

## Validation

Completed:

```text
python -m py_compile scripts/create_root_concept_foundation_v0.py
python scripts/create_root_concept_foundation_v0.py --overwrite
python scripts/validate_developmental_graph.py data/developmental_graph/seeds/root_concept_foundation_v0.json --stats
python -m json.tool data/developmental_graph/experiments/root_concept_foundation_v0/manifest.json
python -m json.tool data/developmental_graph/experiments/root_concept_foundation_v0/datasets/manifest.json
python -m json.tool data/developmental_graph/experiments/root_concept_foundation_v0/training_config.json
```

Graph validation passes with no warnings.

## Next Stage

The next artifact should be:

```text
tinystories_word_attachment_v0
```

Process:

```text
1. Extract frequent TinyStories content words.
2. Group forms where obvious: dogs/dog, runs/run, smiled/smile.
3. Select a small first batch, probably 200-500 words.
4. Attach each word to root anchors.
5. Generate compact relation records.
6. Train from root_mixed checkpoint into word_attachment.
7. Continue into raw TinyStories text.
```

Important comparison:

```text
A. raw TinyStories from scratch
B. root_concept_foundation -> raw TinyStories
C. word_attachment only -> raw TinyStories
D. root_concept_foundation -> word_attachment -> raw TinyStories
E. corrupt/shuffled word_attachment -> raw TinyStories
```

The main theory test is `A` versus `D` with the same model size and total token
budget.
