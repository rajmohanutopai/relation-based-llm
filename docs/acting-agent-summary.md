# The Pretend Baby Experiments: Summary

Date: 2026-11-07, updated 2026-11-10

Covers acting agents v0 to v4.3, the object-property tests and the language tests.
The numbers and methods are in each experiment's own report, listed at the end.

## The question

Rajmohan's theory is that happiness is the strengthening of connections, and that
it counts for most when connections are new and weak. A second hunch is that a
relation graph helps a small learner learn faster.

These experiments ask whether a learner that chases that feeling, with no teacher,
comes to understand its world. The theory had to be written down as exact rules
to run at all, and that has been as useful as the scores.

## The world

A pretend baby sits in a pretend room with no language. Each turn it picks an
object and an action, such as pushing or dropping, and sees what happens. Rules
decide the outcome: light things move, round things roll, hard things make a
noise when dropped. One outcome in ten is flipped at random.

Each room also holds gadgets, like a TV or a flashing toy, which act at random.
They hold nothing to learn, but they keep producing new sights. They test whether
a learner can be fooled by noise. Some worlds keep the same gadgets in every room
(A), and others bring new ones each time (B).

We then quiz the baby on what happens next, including on objects it has never
met. A score of 0.5 means guessing. "Area" measures how fast its score rises.

## The babies

| Baby | Plays with what... |
|---|---|
| Random | it happens to pick |
| Novelty | it has tried least |
| Surprise | it is least sure about |
| Learning progress | it has lately got better at |
| Happiness | it expects will strengthen the most connections |

## What happened, in order

**1. First tries failed (v0–v2).** Happiness was measured from changes in a neural
network's error. Four different measures all failed to tell useful learning from
noise, so I stopped tuning and changed the model.

**2. Connections made explicit (v3).** The baby now keeps actual links, first
"this ball rolled" and then general ones like "round things roll". General links
form only when at least three things agree. This matched the theory better, and
happiness beat random, novelty and learning progress in world B.

**3. The slot machine (v3, v3.1).** The baby got hooked on gadgets, because it kept
expecting a big insight from them that never came. Lowering that promise each
time it failed brought gadget time down from 38% to about 26%. Random's was 17%.

**4. Grief (v3.1).** A big loss did not cause more total sadness than a small one,
in 0 of 5 seeds. Moments that met a loss were 1.5 to 3.3 times sadder. The theory
of grief remains unshown here.

**5. Rajmohan's two rules (v4).** "Attach" allowed happiness only from links that
grow out of known concepts. It didn't help, but it also wasn't a fair trial, since
the known concepts soon spread to everything. "Spike" made new links fade unless
confirmed, with the biggest payoff on the second confirmation. It cut gadget time
to 15%, below random.

**6. Which part of the spike worked (v4.1).** v4 changed three things at once, so
I tested all 8 combinations.

| Part | Effect on gadget time |
|---|---:|
| S-curve (the second confirmation pays most; each thing counts once) | −8 points |
| Lower pay for forming a link | −4.5 points |
| Fading | +3 points |

The S-curve alone took the baby below random. Fading made noise worse. I had
predicted that low pay would do most of the work and the S-curve little, and I was
wrong on both.

**7. New seeds (v4.2).** The noise fix held in 5 of 5 new seeds. But a flat payment
over the same three confirmations did just as well, so the peak isn't the active
part: payment that runs out is. Paying only the first forming removed 57–86% of
fading's harm, so re-forming was most of the cause. The S-curve baby did not keep its
speed lead, though it did end higher than the older rule.

**8. A room that is half noise (v4.3).** Until now gadgets were 4 of the 24 things in a
room. With 4 gadgets and 4 ordinary things, the order turned over. On new seeds, the
happiness baby beat surprise and random on speed, final score and new objects, in 5 of 5
seeds and in both conditions.

| | Happiness `--S` | Surprise | Random |
|---|---:|---:|---:|
| A: speed (area) | 0.743 | 0.690 | 0.686 |
| A: final score | 0.815 | 0.753 | 0.774 |
| A: time on gadgets | 29% | 77% | 52% |
| B: speed (area) | 0.726 | 0.691 | 0.683 |
| B: final score | 0.798 | 0.755 | 0.740 |
| B: time on gadgets | 40% | 70% | 54% |

Surprise spent most of its turns on gadgets and learned no faster than random. I chose
this noise level to suit the theory, and said so before the run.

## Where the theory stands

| Claim | Status | How sure |
|---|---|---|
| Happiness is large early and fades with age | Happens | Proves little: I built it in |
| Grokking gives the largest joy | Happens | Proves little: I built it in |
| A learner can chase connection-strengthening without being trapped by noise | **Supported here** | Confirmed on new seeds |
| The second or third confirmation matters most | **Not needed here** | A flat payment that runs out as fast did as well; this says nothing about what people feel |
| Links fade unless confirmed | **Doesn't help here** | Most of its harm came from paying again for re-forming; without that it still gave no gain |
| Chasing happiness makes the best learner | **Yes when noise is common, no when it's rare** | Beat surprise and random in 5 of 5 new seeds with half the room noise (v4.3); trailed surprise with 17% noise (v4.2). Where the order turns over isn't mapped |
| Grief scales with connections lost | **Not shown** | The test may need a better design |
| Happiness only from attached connections | **Open** | No fair test yet |

**The best happiness baby against surprise in the 17%-noise world (`--S`, picked after seeing the data, seeds 1–5):**

| | Happiness `--S` | Surprise | Random |
|---|---:|---:|---:|
| A: speed (area) | 0.745 | 0.751 | 0.718 |
| A: final score | 0.811 | 0.847 | 0.803 |
| A: time on gadgets | 15% | up to 39% by the end | 17% |
| B: speed (area) | 0.725 | 0.732 | 0.696 |
| B: final score | 0.811 | 0.854 | 0.819 |

So happiness nearly keeps up on speed while staying away from noise, but it ends
lower. On new seeds 6–10 surprise led by more (area 0.775 against 0.750 in A). Surprise
wins here partly because this world punishes noise so little: time on gadgets costs
only lost turns, and there are few gadgets. With half the room noise the order changes
(step 8).

## The relation graph

| What the baby was given | Score on new objects | Actions to 85% |
|---|---:|---:|
| Names only | 0.648 | ~1,420 |
| Rajmohan's hand-written graph (8% of the facts) | 0.625 | ~1,590 |
| Facts from ConceptNet and Visual Genome (14%) | 0.623 | ~1,620 |
| Answers from a blind Claude agent (94%, 96% agreeing) | **0.779** | **~1,160** |
| A complete, true table | **0.830** | **~760** |

The table above is the toy world, scored on 11 new objects. A filled graph helps a lot
there, and a thin one doesn't help at all. These fields are also the simulator's own
rule inputs, so part of the win is circular. The Claude answers aren't fully independent
either: Claude helped build this world, and I worded the questions knowing what the
simulator means.

**In a world Claude didn't write** (MuJoCo physics, 150 scanned objects; `docs/independent-world-v0.md`), the
first report gave 0.569 for blind answers on new objects against 0.498 for the same answers on the wrong objects.
That rested on one set of 30 test objects, which a check on 2026-11-10 found to be an unlucky choice. Over 60 other
choices:

| What the world model was given | Score on new objects |
|---|---:|
| Names only | 0.516 |
| Blind answers on the wrong objects | 0.516 |
| Blind answers | **0.674** (won 60 of 60) |
| Measured size and mass | **0.829** |

Most of the answers' gain comes from one fact, whether the object is large. In this world size decides most
outcomes.

**In a small language model** (`docs/language-transfer-cv-v0.md`, every object held out once), facts and outcomes
arrive only as text, and the model reads facts about a new object without ever seeing what it does:

| Fact rows in training | One opaque token per object | Real names of several words |
|---|---:|---:|
| None | 0.506 | 0.536 |
| Claude's answers | **0.564** | 0.545 |
| Claude's answers on the wrong objects | 0.491 | 0.540 |
| Measured facts | **0.688** | 0.518 |
| Measured facts on the wrong objects | 0.478 | 0.505 |

With one token per object, all four rules pass with intervals clear of zero, and better facts give a bigger gain.
The model keeps about half of what the same facts give a world model as direct inputs. With real names nothing
carries over, though the model recalls 98% of the facts. The two earlier language reports
(`docs/language-transfer-v0.md`, `docs/language-transfer-opaque-v0.md`) used the unlucky test set and carry
correction notes.

**Why real names fail** (`docs/language-transfer-names-v0.md`): the carry-over is lost when names get long. With
two made-up tokens per object it holds (0.630 against 0.497). With as many tokens as the real name, all the
object's own, it is gone (0.481 against 0.476). Shared words aren't needed to explain it.

**Stating the facts first** (`docs/language-scaffold-v0.md`): the model answers the 12 fact questions about a new
object itself, then the outcome question. This is the project's relation scaffold, in a case where it has work to
do.

| Real names, measured facts | Score on new objects |
|---|---:|
| Asked directly | 0.544 |
| States the facts, then answers | **0.716** (0.83 by rank) |
| The same, taught wrong-object facts | 0.559 |

Both rules pass in every fold and both seeds. The model states 99.9% of a new object's facts correctly. With
one token per object the same procedure gives 0.772 against 0.550 asked directly. The fact questions were
supplied in a fixed order; whether a model can choose which relations to state is untested.

## Limits on all of this

- I designed this toy world, so nothing here proves or disproves anything about
  people. It shows only whether the theory works once written as exact rules.
- Five seeds per setting show direction and little about size. A "4 of 5 seeds" rule
  passes by luck about one time in five, and misses a moderate real effect about half
  the time, so single passes and fails under it carry little weight.
- New-object scores from one small test set can be off by 0.1 (30 objects in the physics
  world, 11 in the toy world). From 2026-11-10 the physics-world tests hold every object
  out once and give an interval.
- Several things that look like confirmation are built into the rules. The reports
  mark them.
- The language tests use templated text in a narrow world. The project's main aim is a
  small language model with relation structure on ordinary text, and that has not been
  tested against any outside benchmark.

## Open next steps

1. Done (v4.2).
2. Done (v4.3): with half the room noise, surprise's lead doesn't survive. Open: where
   between 17% and 50% the order turns over, and whether novelty or learning progress
   do better there.
3. **A fairer attach test,** with a frontier that stays narrow.
4. The 385-question worksheet: Rajmohan declined it on 2026-11-08, expecting his answers
   to match Claude's. The test on independently chosen properties is done
   (`docs/independent-world-v0.md`).
5. **A phrase-to-concept step** for the 9,253 rows, 82% of whose phrases appear
   only once (`docs/age-6mo-relation-audit-v0.md`).
6. Done (`docs/language-transfer-names-v0.md`): names longer than a token or two are
   the cause. Open: whether length or position does the harm.
7. Done (`docs/language-scaffold-v0.md`): stating the facts first works, 0.716 against
   0.544 with real names. Open: the same test with weaker facts (Claude's answers, the
   hand-written rows), and with the model choosing which relations to state.
8. **The main aim on public ground:** a small model on ordinary text, with and without
   a fact supplement of equal length, scored on tests the project didn't write. The
   scaffold result says how the supplement should be used: stated before the answer.

## Reports

- `docs/acting-agent-v0-design.md`, `v1`, `v2`: first world, graph tests, failed measures
- `docs/acting-agent-v3-design.md`: explicit links, grokking, grief
- `docs/acting-agent-v4-design.md`: attach and spike
- `docs/acting-agent-v4-1-design.md`: which part of the spike worked
- `docs/acting-agent-v4-2-design.md`: new seeds, the peak and re-forming
- `docs/acting-agent-v4-3-design.md`: a room that is half noise
- `docs/object-properties-v0.md`: facts from external sources, and the worksheet
- `docs/independent-world-v0.md`: the physics world, with the test-set check
- `docs/language-transfer-v0.md`, `docs/language-transfer-opaque-v0.md`: first language tests, on one test set
- `docs/language-transfer-cv-v0.md`: the language test with every object held out once
- `docs/language-transfer-names-v0.md`: why real names block the facts
- `docs/language-scaffold-v0.md`: stating the facts before answering
- `docs/age-6mo-relation-audit-v0.md`: audit of the 9,253 rows
