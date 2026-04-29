# Procedural Foundation V4 Word Surface

Date: 2026-04-29

V4 keeps the same underlying world as V3, but changes the training surface. The
main change is that the first training language no longer uses shorthand labels
such as `s:`, `q:`, `a:`, `f:`, `r:`, or `n:`.

The goal is to teach the model with proper words first, then add acronyms or
compact notations only in a later phase.

## Why

The V3 result showed a positive relation-scaffold signal, but the natural-input
evaluation also showed heavy dependence on the `s:/q:/a:` protocol.

V4 tests a better question:

```text
Can relation scaffolding still help when the base training surface uses normal
words such as scene, question, answer, reason, because, and relation?
```

## Source

V4 reuses V3 source units and split logic:

```text
source units: 5712
train base units: 4536
dev base units: 553
curriculum_test base units: 623
entities: 208
```

Each base unit is rendered into five word-surface records.

## Variants

```text
word_plain_text
word_relation_scaffolded
word_relation_first_then_text
```

The primary comparison should be:

```text
word_plain_text vs word_relation_scaffolded
```

The `word_relation_first_then_text` arm is kept only for continuity with the V3
experiment.

## Surface Types

Each source unit is rendered five ways:

```text
labeled_words
simple_lines
because_answer
answer_reason_bridge
event_continuation
```

Example plain surfaces:

```text
scene: Ball is on bed near baby. Baby reaches hand.
question: Is touch ok?
answer:

answer: yes.
reason: ball is ok to touch.
```

```text
Ball is on bed near baby. Baby reaches hand.
Is touch ok?

yes, because ball is ok to touch.
```

```text
Ball is on bed near baby. Baby reaches hand.

hand touches ball.
```

Example scaffolded target:

```text
yes, because ball is ok to touch.
known relation: baby can move hand.
known relation: ball is near.
known relation: ball is middle.
known relation: ball is on bed.
known relation: ball is soft.
known relation: ball is small.
known relation: ball is light.
known relation: ball is ok to touch.
known relation: ball can move.
known relation: hand touches ball.
known relation: baby feels ball.
known relation: hand can make ball move.
```

## Dataset Size

Per variant:

| Split | Records | Base Units | Surfaces Per Unit |
| --- | ---: | ---: | ---: |
| train | 22680 | 4536 | 5 |
| dev | 2765 | 553 | 5 |
| curriculum_test | 3115 | 623 | 5 |

Vocabulary:

| Variant | Train Words | Unique Train Words |
| --- | ---: | ---: |
| word_plain_text | 445928 | 304 |
| word_relation_scaffolded | 1475183 | 336 |
| word_relation_first_then_text | 1475183 | 336 |

The scaffolded variants contain more words because each record includes the
full-word relation scaffold. Later training should still use a matched token
budget per arm.

## Validation

Generated files:

```text
data/developmental_graph/experiments/procedural_foundation_v4_word_surface/
```

Shorthand protocol check:

```text
all dataset files: 0 hits for ^s: ^q: ^a: ^f: ^r: ^n:
```

## Next Step

Prepare a local nanochat comparison:

```text
word_plain_text
word_relation_scaffolded
```

Use one shared tokenizer and the same training token budget per arm. The first
evaluation should test:

```text
scene/question/answer/reason prompts
simple natural question prompts
because-answer prompts
event continuation prompts
```

The important question is whether the scaffolded arm still improves factual
relation answers without relying on shorthand protocol tokens.
