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

The original held-out test was close to the training format. To check whether
the model was learning robust relations or just matching prompt surfaces, I
created a paraphrase stress test.

The stress test used:

- the same held-out examples
- the same target answers
- only words that appeared in training
- different question wording

Answer accuracy dropped sharply, but reason accuracy stayed high.

That means the model often recovered the right relation, but did not reliably
put it into the expected answer format.

Example:

```text
Question:
Give the meaning for audible.

Expected:
answer: audible can be heard.
reason: audible can be heard.

Model:
answer: yes.
reason: audible can be heard.
```

## Conclusion

The current implementation does not support the claim that root relation
training makes later relation learning faster.

The broader idea that meaning is relational may still be interesting, but this
specific curriculum-learning approach did not beat direct scratch training.

The next useful test, if this resumes, should focus on unseen recombinations and
relation-content scoring rather than exact answer formatting.

