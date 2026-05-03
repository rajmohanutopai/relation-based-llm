# Relation Based LLM Experiments

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

## Example Outputs

The model did learn many of the relation patterns. Some examples from the
reworded test set:

```text
Question:
The box is loose. The child opens the box. The toy is inside.
The hand reaches in. What does loose tell us in this case?

Model:
answer: loose enables move and open lets the hand reach inside.
reason: loose enables move and open lets the hand reach inside.
```

```text
Question:
The child sees a toy. The toy is interesting in this moment.
The child looks longer or changes attention. What does interesting show?

Model:
answer: interesting can make new link.
reason: interesting can make new link.
```

```text
Question:
The child sees crawl. A thing changes after the event.
The child watches the result. What does crawl show?

Model:
answer: crawl is body move.
reason: crawl is body move.
```

```text
Question:
The child compares filled with inside. Filled means something is inside.
What state link is right for filled?

Model:
answer: filled has inside thing.
reason: filled has inside thing.
```

The reworded test was useful because it showed both sides of the result. The
model often recovered the right relation, especially in the reason field, but it
was still weaker at handling different answer formats. That is why I treat this
as a useful experiment rather than a successful replacement for ordinary
training.

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
