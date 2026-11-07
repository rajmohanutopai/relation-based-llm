# Acting Agent V4: Design

Date: 2026-11-05

Status: run complete (2026-11-05); noise rule passed, learning rule failed

Experiment ID: `acting_agent_v4`

## Why v4

v3.1 (`docs/acting-agent-v3-design.md`) left the agent drawn to noise: 26% of
its time on the same gadgets, against 16% for random. The user called this the
biggest danger and proposed two rules:

1. **Attach:** start with a few concepts. A new connection gives happiness
   only if it connects to existing ones or grows out of them.
2. **Spike:** a new link fades quickly unless it recurs, and the second or
   third confirmation gives a high spike, since many connections firing
   together strengthen far more than one.

## World and shared parts

The same as v3.1: v2 "big" world, 3,000 actions, 10% flips, fixed gadgets (A)
and fresh gadgets (B), same predictor and same sadness rule. Specific links
keep the v3.1 happiness formula in every version. Only general links change.

## Versions

| Version | Rule |
|---|---|
| current | v3.1 |
| attach | general links form only if they touch the frontier |
| spike_naive | fading and S-curve; any confirmation counts |
| spike | fading and S-curve; each thing can confirm a link once |
| both | attach + spike |

**Attach.** The frontier starts as four seeds: light, round, hard, noisy.
A general link can form only if one of its features is in the frontier, and
forming adds its features to the frontier. A specific link gives happiness
only if its thing has a frontier feature. Evidence is still collected, so a
link can form later.

**Spike.** Each formed general link has a confirmation count c.

- Felt strength = c³ / (c³ + 8).
- Happiness on a confirmation = rise in felt strength × (1 − felt strength
  before). Forming counts as the first confirmation and pays only 0.11.
- A confirmation is an outcome on the side the link predicts. A contradiction
  takes 1 off c.
- Until c reaches 3, c halves every 300 actions. At 3 it is consolidated and
  stops fading.
- An unconsolidated link with c below 0.25 dissolves: it stops predicting and
  must form again from scratch. This can cost knowledge, and the tests measure
  that.
- Expected happiness uses max(p, 1 − p) as the chance of confirmation.

## Arms

Each new version runs with the happiness arm and with a random arm, since the
store itself now differs by version. The other rivals (surprise, novelty,
learning progress) are the v3.1 runs.

100 runs: 5 versions × 2 arms × 2 conditions × 5 seeds. The current version is rerun too, because the false-link measure is new; its scores should match v3.1.

## New measure: false links

A formed general link is **false** if it is sure (estimate at least 0.7 or at
most 0.3) while the truth for the things it covers is on the other side of
one half, or within 0.4–0.6. Truth comes from the rules without flips, with
gadgets at 0.5, weighted by how often things appear in rooms. Reported as a
share of sure links.

## Gate (random arm, seed 1, condition A)

G1: for each new version, room accuracy ≥ 0.75 and never-met accuracy ≥ 0.65.
G2: a happiness run takes under 4 minutes.

A version that fails G1 stays in the report but can't pass the rules below.

## Pass rules (5 seeds, each in at least 4 of 5 seeds, in both conditions unless stated)

- **N1 noise:** the version's happiness arm spends less time on gadgets than
  the random arm on the same store.
- **N2 learning:** its curve area beats both the random arm on the same store
  and the current happiness arm.
- **N3 false links:** its share of false links is below the current happiness
  arm's.
- **N4 main rival:** `both` beats surprise on curve area.
- **N5 slot machine (condition A):** spike_naive spends more time on gadgets
  than spike.

**Built in, so not evidence:** that happiness peaks on the second confirmation.
The S-curve sets that. It is reported as a check only.

## Prediction (written before running)

- Gate: attach passes. Spike and both are at risk, because dissolving removes
  rarely touched true links.
- attach: little change. Pair links carry features into the frontier fast, and
  gadgets share light, hard and noisy with the seeds.
- spike_naive: more time on gadgets than current.
- N5: pass.
- spike and both: N1 passes in B and is even odds in A.
- N2: fail for every version.
- N3: pass for spike and both.
- N4: fail.

## Gate result (2026-11-05): passed

| version | room accuracy | never-met | general links | dissolved | frontier size at end |
|---|---:|---:|---:|---:|---:|
| attach | 0.794 | 0.783 | 18,979 | 0 | 36 of 36 |
| spike_naive | 0.772 | 0.772 | 13,128 | 9,474 | not used |
| spike | 0.773 | 0.772 | 12,251 | 10,915 | not used |
| both | 0.773 | 0.772 | 12,223 | 10,918 | 36 of 36 |

A `both` happiness run took 156 s (area 0.743, gadget time 14%, seed 1 only).

## Correction (2026-11-07)

Bug SM-3 (`docs/state-machines.md`) wrongly discounted promised links under attach. The
`attach` and `both` happiness rows below are from before the fix. Fixed values: attach A 0.721,
B 0.708; both A 0.708, B 0.684; gadget times about the same. No verdict flips, but both arms
learn slightly less than shown here. `both` beats surprise 0 / 0 seeds, not 0 / 1.

## Results (5 seeds, `runs/acting_agent_v4/seed*/`)

The current version reproduces v3.1's scores exactly. v3.1 rivals: A random
0.718, surprise 0.751, learning progress 0.735, novelty 0.706; B random 0.696,
surprise 0.732, learning progress 0.692, novelty 0.643.

| version | arm | A area | A final | A gadget time | A false | B area | B final | B gadget time | B false |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| current | happiness | 0.728 | 0.791 | 25.3% | 1.5% | 0.734 | 0.801 | 15.6% | 1.3% |
| current | random | 0.718 | 0.803 | 17.0% | 0.7% | 0.696 | 0.819 | 18.7% | 0.6% |
| attach | happiness | 0.731 | 0.807 | 24.2% | 1.4% | 0.710 | 0.780 | 15.6% | 1.6% |
| attach | random | 0.717 | 0.804 | 17.0% | 0.7% | 0.696 | 0.819 | 18.7% | 0.6% |
| spike_naive | happiness | 0.713 | 0.788 | 17.5% | 0.9% | 0.690 | 0.779 | 15.4% | 1.0% |
| spike_naive | random | 0.712 | 0.796 | 17.0% | 0.7% | 0.690 | 0.810 | 18.7% | 0.5% |
| spike | happiness | 0.731 | 0.802 | **14.7%** | 0.9% | 0.693 | 0.779 | 15.7% | 0.6% |
| spike | random | 0.712 | 0.795 | 17.0% | 0.7% | 0.690 | 0.810 | 18.7% | 0.5% |
| both | happiness | 0.720 | 0.810 | **14.4%** | 0.8% | 0.702 | 0.796 | 15.8% | 0.6% |
| both | random | 0.712 | 0.795 | 17.0% | 0.7% | 0.690 | 0.810 | 18.7% | 0.5% |

Seeds won out of 5 (A / B):

| version | N1 less gadget time than own random | beats own random | beats current | N3 fewer false links | beats surprise |
|---|---:|---:|---:|---:|---:|
| attach | 0 / 5 | 3 / 4 | 3 / 1 | 3 / 1 | 1 / 1 |
| spike_naive | 2 / 5 | 2 / 1 | 2 / 0 | 5 / 4 | 0 / 1 |
| spike | **5 / 5** | 4 / 3 | 3 / 0 | 4 / 5 | 1 / 0 |
| both | **5 / 5** | 4 / 3 | 2 / 1 | 5 / 5 | 0 / 1 |

N5: spike_naive spent more time on gadgets than spike in 5 of 5 seeds in A
(1 of 5 in B, where the rule didn't apply).

**Against the rules:**

| rule | result | predicted |
|---|---|---|
| N1 noise | spike and both **pass**; attach and spike_naive fail | spike, both pass in B; even odds in A |
| N2 learning | **fail** for every version | fail |
| N3 false links | spike_naive, spike and both pass; attach fails | spike, both pass |
| N4 beats surprise | **fail** (0/5, 1/5) | fail |
| N5 slot machine | **pass** in A, by a small margin | pass |
| spike_naive more gadget time than current | **wrong**: 17.5% vs 25.3% | yes |
| attach changes little | right on gadget time; it cost B learning | little change |

**Reading:**

1. **Fading plus the S-curve removes the pull toward noise.** With the same
   gadgets, gadget time fell from 25% to about 14–15%, below random's 17%. This
   is the first rule to fix the trap in both conditions.
2. **The effect can't yet be split into parts.** The spike versions also cut
   the payment for forming a link from about 0.7 to 0.11, which shrinks the
   "promised grok". The fall from 25.3% to 17.5% came with spike_naive, and
   counting only different things took it to 14.7%. Which part of the S-curve
   does the work is untested.
3. **Attach alone did not stop noise**, and it never stayed narrow: the frontier
   reached all 36 features, because pair links carry new features in, and
   gadgets share light, hard and noisy with the seeds. This tests one weak
   form of attach, not the idea in general.
4. **Fixing noise didn't improve learning.** In B, the spike versions gave up
   the old lead: area fell from 0.734 to 0.693–0.702, about level with random.
   Final accuracy in A rose slightly for `both` (0.810 vs 0.791), but surprise
   stays ahead (0.847).
5. **False links were never common.** They are about 1% of sure links in every
   version, and my guess that chance links were widespread was wrong. The
   happiness arms have more of them than the random arms. Differences of a few
   tenths of a point are real across seeds but small in size.
6. **The peak on the second confirmation is built in** (the top 1% of tries
   hit it 90–99% of the time, against a base rate of about 70%). It's a code
   check only.
7. **Dissolving costs a little knowledge:** random arms fall from 0.718 to
   0.712 in A and from 0.696 to 0.690 in B.
