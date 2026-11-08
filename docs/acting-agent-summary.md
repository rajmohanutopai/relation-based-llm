# The Pretend Baby Experiments: Summary

Date: 2026-11-07

Covers acting agents v0 to v4.1 and the object-property test. The numbers and
methods are in each experiment's own report, listed at the end.

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

## Where the theory stands

| Claim | Status | How sure |
|---|---|---|
| Happiness is large early and fades with age | Happens | Proves little: I built it in |
| Grokking gives the largest joy | Happens | Proves little: I built it in |
| A learner can chase connection-strengthening without being trapped by noise | **Supported here** | Confirmed on new seeds |
| The second or third confirmation matters most | **Not needed here** | A flat payment that runs out as fast did as well; this says nothing about what people feel |
| Links fade unless confirmed | **Doesn't help here** | Most of its harm came from paying again for re-forming; without that it still gave no gain |
| Chasing happiness makes the best learner | **Not shown** | Surprise still leads |
| Grief scales with connections lost | **Not shown** | The test may need a better design |
| Happiness only from attached connections | **Open** | No fair test yet |

**The best happiness baby against surprise (`--S`, picked after seeing the data):**

| | Happiness `--S` | Surprise | Random |
|---|---:|---:|---:|
| A: speed (area) | 0.745 | 0.751 | 0.718 |
| A: final score | 0.811 | 0.847 | 0.803 |
| A: time on gadgets | 15% | up to 39% by the end | 17% |
| B: speed (area) | 0.725 | 0.732 | 0.696 |
| B: final score | 0.811 | 0.854 | 0.819 |

So happiness nearly keeps up on speed while staying away from noise, but it ends
lower. Surprise may win here partly because this world punishes noise so little:
time on gadgets costs only lost turns. In a world where noise did harm, the order
might change. I haven't tested that.

## The relation graph

| What the baby was given | Score on new objects | Actions to 85% |
|---|---:|---:|
| Names only | 0.648 | ~1,420 |
| Rajmohan's hand-written graph (8% of the facts) | 0.625 | ~1,590 |
| Facts from ConceptNet and Visual Genome (14%) | 0.623 | ~1,620 |
| Answers from a blind Claude agent (94%, 96% agreeing) | **0.779** | **~1,160** |
| A complete, true table | **0.830** | **~760** |

**In a world Claude didn't write** (MuJoCo physics, 150 scanned objects; `docs/independent-world-v0.md`),
blind answers scored 0.569 on new objects against 0.504 for names, 0.498 for the same answers on the
wrong objects, and 0.815 for measured geometry. So the content helps, but modestly.

**In a small language model** (`docs/language-transfer-v0.md`), the same facts showed no clear gain: 0.616 on
new objects against 0.605 for wrong facts and 0.600 for plain text. Words in the names may already carry much of it.

A filled graph helps a lot, and a thin one doesn't help at all. These fields are also
the simulator's own rule inputs, so part of the win is circular. The Claude answers
aren't fully independent either: Claude helped build this world, and I worded the
questions knowing what the simulator means.

## Limits on all of this

- I designed this toy world, so nothing here proves or disproves anything about
  people. It shows only whether the theory works once written as exact rules.
- Five seeds per setting show direction and little about size.
- Several things that look like confirmation are built into the rules. The reports
  mark them.
- Only one templated language test has been run, and it showed no clear gain. The project's main aim
  is a small language model with relation structure, and this line is a side branch.

## Open next steps

1. Done (v4.2).
2. **A world where noise does harm,** to see whether surprise's lead survives.
3. **A fairer attach test,** with a frontier that stays narrow.
4. **The 385-question worksheet,** still blank for Rajmohan's own answers, and a test
   on properties chosen independently of the world.
5. **A phrase-to-concept step** for the 9,253 rows, 82% of whose phrases appear
   only once (`docs/age-6mo-relation-audit-v0.md`).

## Reports

- `docs/acting-agent-v0-design.md`, `v1`, `v2`: first world, graph tests, failed measures
- `docs/acting-agent-v3-design.md`: explicit links, grokking, grief
- `docs/acting-agent-v4-design.md`: attach and spike
- `docs/acting-agent-v4-1-design.md`: which part of the spike worked
- `docs/acting-agent-v4-2-design.md`: new seeds, the peak and re-forming
- `docs/object-properties-v0.md`: facts from external sources, and the worksheet
- `docs/age-6mo-relation-audit-v0.md`: audit of the 9,253 rows
