# Acting Agent V4.1: Design

Date: 2026-11-07

Status: run complete (2026-11-07); the S-curve does the most, and fading makes noise worse

Experiment ID: `acting_agent_v4_1`

## Why v4.1

In v4 the spike rule cut time on the same gadgets from 25% to about 15%. But it
changed three things at once, so we can't say which one did it:

1. **Low pay:** forming a general link pays 0.11 instead of about 0.7.
2. **Fading:** links fade and dissolve unless confirmed.
3. **S-curve:** the second confirmation pays most, and each thing can confirm a
   link once.

The user's proposal is parts 2 and 3. Part 1 came with my way of writing it. If
part 1 alone does the work, v4 gave the user's rule credit it didn't earn.

v4 also lost the lead in fresh-gadget learning: area fell from 0.734 to 0.693.
This run asks which part cost that too.

## Versions

Each switch is on or off, which gives 8 versions, named by the switches that
are on: `---` is v3.1 and `LFS` is v4 spike.

- **L off:** forming pays the link's strength. **L on:** it pays 0.11.
- **F off:** links never fade. **F on:** c halves every 300 actions until 3, and
  a link with c below 0.25 dissolves. Confirmations count once per thing.
- **S off:** a touched link pays the v3 rise in strength × (1 − strength).
  **S on:** confirmations pay the S-curve, once per thing.

Everything else stays as in v4: world, 3,000 actions, 10% flips, condition A
(same gadgets), condition B (fresh gadgets), seeds 1–5.

**Note on dissolving.** With F on and L off, a dissolved link can form again and
pay about 0.7 again. That may reward forming, losing and re-forming links. It
comes from combining the parts, so the report will count dissolved links.

## Runs

80 happiness runs: 8 versions × 2 conditions × 5 seeds. Random arms are reused
from v4, since a random chooser doesn't read payments: `current` random for F
off, `spike` random for F on.

## Gate

`---` must match v4 `current` and `LFS` must match v4 `spike`, curve for curve,
on seed 1, condition A. Any difference means the switches changed something else.

## Pass rules (written before running; condition A, in at least 4 of 5 seeds)

"Below random" means less gadget time than the random arm on the same store.

- **Enough alone:** a switch is enough if the version with only that switch on
  is below random.
- **Needed:** a switch is needed if `LFS` with that switch turned off is no
  longer below random.
- **Credit to the user's rule:** the user's rule earns the credit if `-FS` (no
  low pay) is below random. If only versions with L on pass, the low payment did
  the work and the user's rule has not been shown to.
- **Learning cost (condition B):** a switch carries the cost if turning it off
  in `LFS` restores at least half of the fall in area (0.734 to 0.693), on
  average across seeds.

## Prediction (written before running)

- Low pay is enough alone in A, and is the main cause.
- Fading alone is not enough. With high pay it may raise gadget time.
- S-curve alone is not enough, since forming still pays about 0.7.
- `-FS` is not below random, so the user's rule does not earn the credit.
- Low pay also carries the learning cost in B.

My confidence is moderate on low pay and low on the rest.

## Gate result (2026-11-07): passed

`---` and `LFS` matched v4 `current` and `spike` curve for curve on seed 1,
condition A. In the full run they matched on all 5 seeds in both conditions.

## Results (5 seeds, `runs/acting_agent_v4_1/seed*/`)

Random spent 17.0% of its time on gadgets in A and 18.7% in B.

| version | A gadget time | below random, A | A area | A final | B gadget time | B area | B final | links dissolved, A |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `---` (v3.1) | 25.3% | 0 / 5 | 0.728 | 0.791 | 15.6% | 0.734 | 0.801 | 0 |
| `L--` | 18.9% | 1 / 5 | 0.742 | 0.820 | 15.0% | 0.714 | 0.780 | 0 |
| `-F-` | 27.8% | 0 / 5 | 0.726 | 0.795 | 15.7% | 0.714 | 0.786 | 17,850 |
| `--S` | **15.3%** | **4 / 5** | **0.745** | 0.811 | 16.5% | 0.725 | 0.811 | 0 |
| `LF-` | 22.9% | 0 / 5 | 0.716 | 0.793 | 15.1% | 0.708 | 0.774 | 15,417 |
| `L-S` | **12.9%** | **5 / 5** | 0.743 | 0.827 | 16.2% | 0.707 | 0.801 | 0 |
| `-FS` | 19.3% | 0 / 5 | 0.729 | 0.791 | 15.3% | 0.708 | 0.777 | 13,351 |
| `LFS` (v4 spike) | **14.7%** | **5 / 5** | 0.731 | 0.802 | 15.7% | 0.693 | 0.779 | 10,968 |

Surprise, for comparison: A area 0.751, final 0.847; B area 0.732, final 0.854.

Average effect of each switch on A gadget time, across the other switches. Each
one held in all 4 pairings, in all 5 seeds:

| switch | effect on A gadget time |
|---|---:|
| S-curve | −8.2 points |
| Low pay | −4.5 points |
| Fading | **+3.1 points** |

**Against the rules:**

| rule | result | predicted |
|---|---|---|
| S-curve enough alone | **pass** (4 / 5) | **fail (wrong)** |
| Low pay enough alone | fail (1 / 5), though it cut 6 points | **pass (wrong)** |
| Fading enough alone | fail (0 / 5); it raises gadget time | fail, may raise (right) |
| S-curve needed in `LFS` | **yes** (`LF-` 0 / 5) | |
| Low pay needed in `LFS` | yes (`-FS` 0 / 5) | |
| Fading needed in `LFS` | **no** (`L-S` 5 / 5, and lower than `LFS`) | |
| The user's rule earns the credit (`-FS` below random) | **fail** (0 / 5) | fail (right, for the wrong reason) |
| One switch carries the B learning cost | **none does**: turning any one off restores about 0.015 of the 0.041 fall, and half was required | low pay (wrong) |

**Reading:**

1. **The S-curve is the strongest part, and it's the user's idea.** On its own,
   it cut gadget time from 25.3% to 15.3%, below random. I expected it to do
   little and expected low pay to do most. I had that backwards.
2. **The other half of the user's rule made noise worse.** Fading raised gadget
   time in every pairing. So the pair as proposed, fading plus spike with the
   higher pay (`-FS`), fails my pre-set rule. A likely cause, unchecked: links
   dissolve and form again, and each new forming pays again. Fading raised links
   formed in A from 21,613 to 30,191.
3. **v4 gave low pay and fading a free ride.** The best noise result is `L-S`, at
   12.9%, with fading removed.
4. **`--S` is the best all-round version here.** It has the highest A area
   (0.745), gadget time below random in A, and the smallest learning cost in B
   among versions that fix noise (0.725 against 0.734). I picked it after seeing
   the data, so it needs fresh seeds before anyone relies on it.
5. **Surprise still leads.** `--S` beats its area in 1 of 5 seeds in A and 2 of 5
   in B, and surprise ends higher (0.847 against 0.811 in A). The gap in area is
   now small (0.745 against 0.751), and `--S` spends far less time on gadgets,
   where surprise reaches 39% by the end.

**What this can't say:**

- **S bundles two things:** the S-curve shape and the rule that each thing
  confirms a link once. v4's comparison suggests both help (`spike_naive` 17.5%,
  `spike` 14.7%), but this run doesn't split them.
- **The peak may not be the active part.** The S-curve also stops paying soon, so
  a plain payment that runs out as fast might do as well. Nobody has tested that.
- **B can't test noise.** Fresh gadgets leave little to chase, and every version
  was below random there, including v3.1.
- **Fading, as tested, pays for re-forming.** A fading rule that pays only the
  first forming hasn't been tried, so this result doesn't rule out fading itself.
