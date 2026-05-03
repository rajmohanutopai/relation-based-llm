# Adi LLM Experiments

This project started with a simple question:

Can a small language model learn faster if we teach it meaning as relations?

The idea was that a word is not just a token. A word is a bundle of relations.
For example, a ball is round, can roll, can bounce, can be touched, can be near
or far, and is not alive. If a model first learns these basic relation patterns,
maybe it can understand later words with less training.

That was the hypothesis.

## What I Tried

I built small synthetic curricula around basic relations.

There were two main kinds of data:

- root relation data: early physical, sensory, body, and simple social relations
- bridge relation data: later concepts that attach to those earlier relations

Then I trained small nanochat transformer models in a few ways:

- train directly on the bridge data from scratch
- train on root first, then bridge
- train on a mix of root and bridge
- train on 25% root and 75% bridge

The hope was that the root-trained model would learn the bridge data faster.

## What Happened

It did not.

In the current experiments, direct scratch training on the bridge data worked
better than root-plus-bridge training.

At 500 training steps, the clearest comparison was:

| Model | Normal test answer | Normal test reason | Reworded test answer | Reworded test reason |
| --- | ---: | ---: | ---: | ---: |
| Bridge-only from scratch | 98.5% | 99.5% | 69.9% | 99.2% |
| 25% root / 75% bridge | 97.0% | 98.6% | 61.8% | 97.0% |

So the relation-root curriculum did not give an advantage.

## The Important Caveat

The first test was too easy.

The model scored very high when the test questions looked like the training
questions. When I asked the same things in a different way, while still using
only words seen during training, answer accuracy dropped a lot.

But the model often still put the correct relation in the reason field.

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

So the model learned many relation strings, but it did not learn a robust way to
answer across different question forms.

## Current Conclusion

I am pausing this line of work.

The broader idea that meaning is relational may still be useful, but the
specific training claim tested here was not supported:

> Teaching root relations first did not make the model learn later relation data
> faster in these experiments.

That is still a useful result. It narrows the path.

If this project continues, the next version should test something sharper:

- unseen relation recombinations
- relation scoring instead of exact answer format
- normal text learning after relation preparation
- much cleaner separation between memorized templates and real generalization

## Useful Reports

- `docs/relation-curriculum-experiment-summary.md`

## Note

This is not a benchmark. It is a small research experiment to test an idea.
