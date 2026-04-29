# nanochat Core4 Natural-Input Held-Out Evaluation

Date: 2026-04-29

This extends the held-out procedural V3 evaluation by replacing the `s:/q:`
input tags with simple natural-language lines while keeping the `a:` answer cue.

The goal is to test whether the models learned only the exact structured input
format, or whether some relation learning transfers when the situation/question
surface changes.

## Prompt Mode

Structured prompt:

```text
s: baby tries to move back.
q: can baby move back?
a:
```

Natural-input prompt:

```text
Baby tries to move back.
Can baby move back?
a:
```

This is not fully natural chat yet. It intentionally preserves `a:` so exact
answer/fact scoring remains comparable.

## Setup

```text
checkpoints: runs/nanochat_core4_20260429
script: scripts/run_nanochat_relation_eval.py
prompt style: natural_a
dataset: data/developmental_graph/experiments/procedural_foundation_v3/datasets/procedural_plain_text/curriculum_test.jsonl
examples: 623
max generated tokens: 32
temperature: 0.0
device: mps
```

Command:

```bash
/tmp/nanochat-read/.venv/bin/python scripts/run_nanochat_relation_eval.py \
  --prompt-style natural_a \
  --models tinystories_plain_text procedural_plain_text procedural_relation_scaffolded procedural_relation_first_then_text \
  --progress-every 100
```

## Results

| Model | Answer exact | Fact exact |
| --- | ---: | ---: |
| tinystories_plain_text | 0.0% (0/623) | 0.0% (0/623) |
| procedural_plain_text | 54.6% (340/623) | 13.3% (83/623) |
| procedural_relation_scaffolded | 61.6% (384/623) | 39.0% (243/623) |
| procedural_relation_first_then_text | 38.4% (239/623) | 19.1% (119/623) |

Raw predictions and full task breakdown:

```text
runs/nanochat_core4_20260429/evaluation/procedural_v3_natural_a_prompt_d4_i500/
```

## Comparison With Structured Prompts

| Model | Structured answer | Natural-input answer | Structured fact | Natural-input fact |
| --- | ---: | ---: | ---: | ---: |
| procedural_plain_text | 74.6% | 54.6% | 39.3% | 13.3% |
| procedural_relation_scaffolded | 82.2% | 61.6% | 73.4% | 39.0% |
| procedural_relation_first_then_text | 50.7% | 38.4% | 19.4% | 19.1% |

## Interpretation

The result is mixed but useful.

Positive signal:

```text
The relation-scaffolded model still beats the plain procedural model when the
s:/q: input tags are removed.

answer exact: 61.6% vs 54.6%
fact exact:   39.0% vs 13.3%
```

Limitation:

```text
Performance drops sharply compared with structured prompts.
The current tiny models learned useful relation structure, but they also depend
heavily on the training prompt protocol.
```

This means the current experiment supports the relation-scaffold idea, but it
does not yet show that the learned structure transfers cleanly into ordinary
language use.

## Fully Natural Answer Cue Smoke

A 20-example smoke test replaced `a:` with:

```text
Scene: ...
Question: ...
Answer:
```

Strict exact-match result:

```text
all four models: 0/20 answer exact, 0/20 fact exact
```

This is expected for these tiny checkpoints because they were not trained on
instruction-following or `Answer:` output format. It confirms that the next
training run should include mixed prompt surfaces rather than only `s:/q:/a:`.

## Next Step

Create a mixed next-token curriculum from the same procedural examples:

```text
structured s:/q:/a:/f:
natural input with a:/f:
natural question/answer sentences
short event continuation text
relation scaffold lines
```

Then train the same four-arm comparison again. The important test is whether
relation scaffolding still improves held-out relation accuracy while the model
also learns ordinary text continuation surfaces.
