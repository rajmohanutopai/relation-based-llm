# Relation Curriculum Experiment Summary

Date: 2026-05-03

## Question

Does root relation training help a small transformer learn later relation data
faster than direct scratch training?

## Setup

The experiment used small nanochat transformer models with about 5M parameters.

The compared training paths were:

- bridge-only from scratch
- root first, then bridge
- root and bridge mixed together
- 25% root / 75% bridge

The bridge dataset contained relation-style examples for later concepts. The
root dataset contained earlier physical, sensory, body, and simple social
relations.

## Main 500-Step Result

| Model | Normal test answer | Normal test reason | Reworded test answer | Reworded test reason |
| --- | ---: | ---: | ---: | ---: |
| Bridge-only from scratch | 98.5% | 99.5% | 69.9% | 99.2% |
| 25% root / 75% bridge | 97.0% | 98.6% | 61.8% | 97.0% |

Direct bridge-only scratch training was better in this setup.

## Paraphrase Stress Test

The original held-out test was close to the training format. I created a
paraphrase stress test to ask the same relation questions in different ways,
while still using only words that appeared in training.

The stress test showed that the model learned many relation patterns, even when
the prompt wording changed.

Example:

```text
Question:
The box is loose. The child opens the box. The toy is inside.
The hand reaches in. What does loose tell us in this case?

Model:
answer: loose enables move and open lets the hand reach inside.
reason: loose enables move and open lets the hand reach inside.
```

Example:

```text
Question:
The child sees a toy. The toy is interesting in this moment.
The child looks longer or changes attention. What does interesting show?

Model:
answer: interesting can make new link.
reason: interesting can make new link.
```

Answer accuracy dropped sharply, but reason accuracy stayed high.

That means the model often recovered the right relation, but did not reliably
put it into the expected answer format.

## Conclusion

The current implementation does not support the claim that root relation
training makes later relation learning faster.

The broader idea that meaning is relational may still be interesting, but this
specific curriculum-learning approach did not beat direct scratch training.

The next useful test, if this resumes, should focus on unseen recombinations and
relation-content scoring rather than exact answer formatting.
