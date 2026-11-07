# Acting Agent V0: Design

Date: 2026-11-03

Status: design, not built

Experiment ID (planned): `acting_agent_v0`

## Why this test

The sampler runs (`docs/sampler-v1-experiment.md`,
`docs/sampler-v2-experiment.md`) showed two things:

- The plan.md rule tells learnable from unlearnable. Surprise chased the
  coin-flip rows, and happiness avoided them.
- That skill didn't pay, because the data was fixed. Random sampling only
  wasted 9% of its steps on noise, and every other task could be learned.

An acting agent differs on both counts. What it does decides what it sees,
and a real baby's room holds things that are bright, loud and endlessly
surprising but teach nothing: a TV, a toy that blinks at random. A learner
drawn to surprise can spend most of its time there. This is the "noisy TV"
problem (Schmidhuber 1991; Oudeyer et al. 2007; Burda et al. 2018), and it is
the "drug" case in plan.md.

## Question

An agent explores a simulated room. It learns a world model from what it
does. Its only reward is its own feeling. If that reward is the plan.md
happiness rule, does the agent's world model end up better, sooner, than one
whose reward is surprise, novelty, plain pleasure, or chance?

## World

The world reuses the rules from `scripts/create_world_sim_v0.py` and
`scripts/create_world_sim_v1.py`, without the text.

**Each episode:** one room. The baby sits on one surface. The room holds 8
things placed on random surfaces:

- 6 ordinary things drawn from `OBJECTS` (train objects only)
- 2 gadgets drawn from a gadget list: a TV, a toy that blinks at random, a
  music box with a random tune

The baby takes 20 actions. Then a new episode starts with a new room.

**Actions** (the agent picks a thing and an action):

| Action | Outcome bits | Rule |
|---|---|---|
| push gently / push hard | moves, rolls, falls | `push_outcome_v1` (weight × strength, shape × smooth surface, high surface) |
| drop | loud, bounce, breaks | `drop_outcome` (hard × hard surface, bouncy, breakable) |
| shake | sound | the v1 shake rule (solid noisy thing, or closed container with something hard inside) |
| watch | change | ordinary things: no change. Gadgets: a random light/sound pattern |

Gadgets answer every action with random bits, drawn fresh each time. Nothing
about them can be learned past the base rate.

**What the agent knows:** the thing's name, the surface it sits on, and the
action. It does not see weight, shape or hardness. It has to learn those from
outcomes.

**Regions.** A region is one (thing, action) pair. With about 45 train
objects (the simulator has 55, some held out), 5 actions and 3 gadgets, that
gives about 240 regions. They differ in
difficulty:

- easy: drop a hard thing (two cases per surface type)
- hard: push (weight × strength × shape × surface, so many cases)
- saturating: once the world model knows a region, there is nothing left to
  learn there
- impossible: every gadget region

With 2 of 8 things being gadgets, a random agent spends about 25% of its
actions on them.

## Learner

**World model:** a small network. It takes in embeddings for thing, action
and surface, plus push strength, and outputs one probability per outcome bit.
It trains online from a replay buffer, with one update per action. It is
kept separate from the language model on purpose. Phase 2 links the two.

**Prequential loss:** before the world model trains on a new outcome, we
score its prediction for that outcome. The model hasn't seen it yet, so this
gives the "unseen" loss for free, with no probe set needed.

**Policy:** the agent picks a region using a softmax over its region scores
(temperature 0.3) plus a 10% even share, the same as the sampler. Region
scores update after every action in that region.

## Arms (only the reward differs)

| Arm | Reward for a region | Expected weakness |
|---|---|---|
| random | none, uniform over the room's (thing, action) pairs | wastes 25% on gadgets |
| surprise | recent prequential loss | stuck on gadgets (noisy TV) |
| novelty | 1 / sqrt(times tried) | ignores how hard a region is |
| pleasure | mean activation of the outcomes: lights, sounds, motion | hooked on gadgets (the "drug" case) |
| happiness | plan.md: activation + gain − loss − shortcut | the test arm |
| happiness_no_shortcut | the same, without the shortcut term | ablation |

**Happiness terms, per region, from its recent tries:**

- strength = exp(−mean prequential loss over the last 10 tries)
- gain = fall in prequential loss (last 10 tries vs. the 10 before) × (1 − strength)
- loss = rise in prequential loss × strength before
- shortcut = how much the replay-buffer loss for the region fell, minus how
  much the prequential loss fell. A large gap means memorized, not learned.
- activation = 0.02 × the outcome's raw pleasure (lights, sound, motion)

**Warm-up:** every adaptive arm takes its first 200 actions at random. In
sampler v2, most of the loss came from starving tasks early, before the
scores meant anything. This rule is set now, before any results.

## Measures

1. **World-model accuracy** on a fixed test set: every (train object, action,
   surface, strength) case, weighted equally. Gadgets are left out, since
   they can't be learned. The score is mean bit accuracy, recorded every 250
   actions.
2. **Learning speed:** area under that curve, plus actions to reach 90%.
3. **Time on gadgets:** share of actions.
4. **Moving on:** share of actions spent on regions the model already knows
   (prequential loss under 0.05). This tests the saturation part of the rule.
5. **New objects:** accuracy on held-out objects after a few tries each. This
   only works if the world model gets object features (see open questions),
   so it isn't part of the pass rule.

## Phase 2: link to the language model

Render each arm's action log to text with the world_sim renderer, so each
action becomes a story with a question and an answer. Then train the same
3.48M GPT from the sampler runs on an equal token budget from each arm's log,
and score it on the world_sim_v1 test splits.

This asks the Track A question: does experience the agent chose by happiness
make better training data than experience chosen at random?

## Pass rules (set before any run)

- **Phase 1:** happiness beats random and surprise on learning speed in all 5
  seeds, and spends less time on gadgets than random, surprise and pleasure.
- **Phase 2** (run only if phase 1 passes): text from happiness logs beats
  text from random logs on test_iid and new-object curve area, in all 3
  seeds.
- **Gadget share sweep:** also run 0, 1 and 4 gadgets per room. We expect
  happiness to tie or lose at 0 gadgets, the same as sampler v2. The question
  is where it starts to win. This is reported as a result, not as a pass rule.

## Prior work

This is close to Intelligent Adaptive Curiosity (Oudeyer, Kaplan and Hafner
2007), where an agent seeks learning progress per region. What plan.md adds:

- the saturation weight (1 − strength)
- the shortcut penalty (memorized vs. learned)
- the loss term for forgetting
- the plain-pleasure arm as an explicit "drug" control
- phase 2: using the agent's experience as language-model data

## Open questions

1. **Object features for new objects.** As designed, the world model only
   knows a thing by its name, so it can't transfer to an object it has never
   seen. One option is to give it the MiniLM word vector for each name, which
   `Closeness` in world_sim_v0 already caches. That would let a melon borrow
   from a watermelon, and would also test whether word meaning helps.
   Recommendation: leave it out of v0 and add it in v1.
2. **Per-region vs. per-action-type regions.** About 240 regions means about
   12 tries each over 3,000 actions, which may be too few for the gain term to
   settle. A fallback is to group regions by action type × object kind, about
   25 groups. Decide after a one-seed signal check, as in v2.
3. **Gadget pleasure strength.** Gadget pleasure has to be high enough that
   the pleasure arm really gets hooked. Fix it at 0.8, the value
   `feel_shortcut` uses in world_sim_v1.

## Cost

- Phase 1: 6 arms × 5 seeds × 3,000 actions, with a small world model. A few
  minutes per run on CPU, about 1 hour in all with the sweep.
- Phase 2: like sampler v2, about 30 minutes.

## Build plan

1. `scripts/acting_agent_v0.py`: the environment (reusing the world_sim
   rules), world model, policies, logging, and a `--check` mode that runs one
   seed and prints region scores.
2. Signal check on one seed: region shares should move away from even,
   gadget share should fall under happiness, and surprise should rise.
3. Full run plus sweep, then a report in `docs/` and a log entry.
4. Phase 2, if phase 1 passes.

## Signal check (2026-11-03): not passed

Built `scripts/acting_agent_v0.py`. Fixes made during the check:

- A hard push used strength 3, so even the heaviest things moved. It now
  uses 2, as world_sim_v1 does.
- Plain bit accuracy started at 66%, because guessing "nothing happens" is
  usually right. The score is now balanced accuracy per outcome bit (hit rate
  on true and on false cases, averaged), so a guess scores 0.5. "Watch" is
  left out, since it never has a true case.

Results over 3 seeds, 2 gadgets per room (`runs/acting_agent_v0_check_region/`):

| Arm | curve area | to 90% | gadget share |
|---|---:|---:|---:|
| random | 0.908 | 983 | 24% |
| surprise | 0.927 | 717 | 58% |
| novelty | **0.930** | 817 | 13% |
| pleasure | 0.900 | 1050 | 66% |
| happiness | 0.910 | 917 | 23% |
| happiness_no_shortcut | 0.915 | 867 | 26% |
| happiness_pleasure (shortcut = activation × (1 − strength)) | 0.918 | 833 | 25% |
| happiness_noact (gain − loss only) | 0.921 | 800 | 25% |

Pooling scores by (kind, action) made every adaptive arm worse
(`runs/acting_agent_v0_check_kind/`).

What it shows:

1. **The traps work.** Surprise spends 58% of its time on gadgets and
   pleasure 66%.
2. **Happiness does not avoid gadgets** (23–26%, the same as random).
3. **The world is too easy.** Each (thing, action) pair is learned in 2–3
   tries. After that no region shows any gain, so happiness scores are noise.
   Surprise wins despite its gadget habit: about 1,200 well-chosen actions are
   enough. Novelty wins because the only thing worth knowing is "which pairs
   haven't I tried".
4. **The memorization shortcut can't fire on gadgets.** A gadget gives
   random outputs for the same input, so the model can't memorize it, and
   seen and unseen loss stay level.

The happiness variants were added after looking at results, so these runs
are exploratory. A confirmatory run must fix one happiness version
beforehand.

Proposed change: make ordinary outcomes slightly noisy (for example, 10% of
bits flipped, since a baby's push varies), so a region takes many tries to
learn. Gadgets then differ from ordinary things in degree (50% vs. 10%), and
learning progress has time to show.

## Confirmatory run: fixed before running (2026-11-03)

**World:** each bit of an ordinary thing's outcome is flipped with chance 0.1
(`--flip 0.1`). Gadgets stay at 50%. The test set holds the true rule, with
no flips. A random-arm-only sanity check reached 90% at step 2,600 of 3,000,
so the budget is not at ceiling. No adaptive arm was run in this world before
these rules were written down.

**Conditions:**
- A: the same 3 gadgets in every room (2 per room)
- B: fresh gadgets (`--fresh-gadgets`): every room's gadgets are new to the
  agent

**Arms:** random, surprise, novelty, pleasure, learning_progress, happiness.

- happiness = activation + gain − loss − shortcut, with shortcut =
  activation × (1 − strength). This reads plan.md's "direct positive
  activation without useful relation growth" literally, and it is
  `happiness_pleasure` in the code. The memorization shortcut was dropped,
  because it can't fire on a source that gives random outputs for the same
  input.
- learning_progress = max(fall in prequential loss, 0), with no saturation
  weight, loss term, shortcut or activation. It stands for the prior work
  (Oudeyer et al. 2007).

**Settings:** 3,000 actions, 5 seeds, region-level scores, 200 random warm-up
actions, temperature 0.3, epsilon 0.1, activation weight 0.02.

**Pass rule:** in both conditions, happiness beats random, surprise and
novelty on curve area in all 5 seeds.

**Secondary:**
- Does happiness beat learning_progress? If so, the saturation weight and
  shortcut term add something.
- Gadget share.

## Confirmatory run: results (5 seeds)

Output: `runs/acting_agent_v0_noisy_A/`, `runs/acting_agent_v0_noisy_B/`

**A: same gadgets in every room**

| Arm | curve area | gadget share | happiness wins (seeds) |
|---|---:|---:|---:|
| random | 0.820 | 24% | 2/5 |
| surprise | **0.839** | 32% | 0/5 |
| novelty | **0.839** | 13% | 0/5 |
| pleasure | 0.791 | 65% | |
| learning_progress | 0.823 | 19% | 2/5 |
| happiness | 0.823 | 26% | |

**B: fresh gadgets in every room**

| Arm | curve area | gadget share | happiness wins (seeds) |
|---|---:|---:|---:|
| random | **0.813** | 24% | 2/5 |
| surprise | 0.812 | 52% | 2/5 |
| novelty | 0.802 | 50% | 4/5 |
| pleasure | 0.795 | 59% | |
| learning_progress | 0.789 | 59% | 5/5 |
| happiness | 0.806 | 38% | |

**Fails the pass rule** in both conditions.

What it shows:

1. **Fresh gadgets trap novelty and plain learning progress**, as predicted.
   Both spend 50–59% of their time on gadgets. Happiness spends 38% and beats
   learning_progress in all 5 seeds and novelty in 4 of 5. So the saturation
   weight and pleasure-shortcut term do add something over plain learning
   progress.
2. **Random is still hard to beat.** It never gets hooked, and in B nothing
   beats it.
3. **Why happiness doesn't avoid gadgets in A.** Its term breakdown on seed 1
   shows the "loss" (sadness) term firing hard on ordinary things: a mean of
   0.39, against 0.02 for gadgets. Once the model is sure what a toy does, one
   flipped outcome gives a large error, and the rule reads that as a
   connection weakening. Gadgets never make the model sure, so they never
   cause these spikes. The rule ends up preferring gadgets to known toys
   (mean score +0.04 vs −0.32).

**Next fix (exploratory, not yet run):** measure connection loss as
forgetting. That would be a rise in loss on the region's earlier cases, which
the model has already learned, not one unlucky new outcome. This is closer
to plan.md's "valued relation loss". Any rerun with this change needs a new
pre-set rule.

## Rerun with sadness as forgetting: fixed before running (2026-11-03)

**Change:** `happiness_forget` = activation + gain − forget − activation ×
(1 − strength).
- forget = rise in the model's mean loss on the region's last 10 earlier
  cases (already trained on), measured before each try, × exp(−that loss
  before).
- gain, activation and the shortcut term are unchanged from
  `happiness_pleasure`.

**World, conditions, settings and arms:** the same as the confirmatory run.
`happiness_pleasure` is kept for comparison.

**Pass rule (unchanged):** in both A and B, happiness_forget beats random,
surprise and novelty on curve area in all 5 seeds.

**Note:** this is the second confirmatory try at this rule. Any further
change to the rule counts as exploratory.

## Rerun with sadness as forgetting: results (5 seeds)

Output: `runs/acting_agent_v0_forget_A/`, `runs/acting_agent_v0_forget_B/`

| Condition | happiness_forget area | best other arm | gadget share | wins vs random / surprise / novelty |
|---|---:|---:|---:|---|
| A (same gadgets) | 0.829 | surprise, novelty 0.839 | 21% | 4/5, 1/5, 1/5 |
| B (fresh gadgets) | 0.790 | random 0.813 | 60% | 1/5, 1/5, 1/5 |

**Fails the pass rule.**

- In A the fix worked as meant. Known toys no longer cause sadness spikes,
  gadget time fell from 26% to 21%, and happiness now beats random in 4 of 5
  seeds. It still trails surprise and novelty.
- In B it made things worse: 60% of time on fresh gadgets, the same as plain
  learning progress. The old sadness term had been pushing the agent away
  from gadgets by accident: a gadget's random answers raised its new-outcome
  loss.
- **Root cause:** a new gadget does give real learning progress in its first
  few tries, as the model learns "this thing is 50/50". The rule counts that
  as useful gain, so each new room's gadgets pay again. plan.md's term is
  *useful* connection gain, and none of the versions so far measure
  usefulness.

**Idea for next (exploratory):** count gain as useful only to the extent it
improves prediction elsewhere. Learning about one ball should help predict
other round things. Learning that tv#17 is random helps nothing else. That
transfer can be measured as the fall in loss on other regions' recent cases
after the update.

## Useful gain via transfer: results (exploratory, 5 seeds)

Output: `runs/acting_agent_v0_useful_A/`, `runs/acting_agent_v0_useful_B/`

`happiness_useful` = activation + gain × useful − forget − activation ×
(1 − strength). Here useful = the mean over the last 10 tries of the cosine
between the gradient of the new case and the gradient of 64 recent cases
from other regions (floored at 0).

| Condition | happiness_useful | random | surprise | novelty | gadget share | wins vs random |
|---|---:|---:|---:|---:|---:|---:|
| A | 0.834 | 0.820 | 0.839 | 0.839 | 19% | 4/5 |
| B | **0.816** | 0.813 | 0.812 | 0.802 | 31% | 2/5 |

These are the best happiness numbers so far, but **the mechanism did not
work.** The mean cosine was about 0.002 for ordinary things and 0.002 for
gadgets in A (0.003 vs −0.001 in B). Leaving the thing's own embedding out of
the gradient gave the same near-zero values. Since useful ≈ 0, the gain term
nearly vanished. The arm became "random with a mild tilt" (small activation ×
strength, minus forgetting), which explains why it sits close to random. This
is not evidence for the usefulness idea.

A single case's gradient is too noisy to show transfer. A direct measure
would take one step on the new case alone, on a copy of the model, and
measure the fall in loss on other regions' cases. It costs more per action.

## Direct transfer test (exploratory, seed 1): does not separate

`transfer_direct`: one plain gradient step (size 0.05) on the new case alone,
on a copy of the weights, then the fall in mean loss on 64 recent cases from
other regions. Arm: `happiness_transfer` (useful gain = mean transfer over the
last 10 tries, floored at 0, × (1 − strength)).

Mean transfer per try (whole run; first third; last third):

| Condition | ordinary things | gadgets |
|---|---|---|
| A | −0.0023; −0.0031; −0.0015 | −0.0021; −0.0034; −0.0003 |
| B | −0.0025; −0.0035; −0.0019 | −0.0052; −0.0128; −0.0012 |

On average, one step on a single case makes the other cases slightly worse,
for toys and gadgets alike. In B, new gadgets hurt more early on (−0.013 vs
−0.0035), but that one-seed gap is too small to steer by. With the floor at
0, useful gain is again about zero.

Per the stopping rule set before this try, the agent work pauses here. The
"useful gain" idea is still untested: neither measure tried here can see
usefulness in this world model.

## Where acting agent v0 leaves the theory

- **The traps are real.** Surprise and pleasure get hooked on gadgets.
  Novelty and plain learning progress get hooked when gadgets are new each
  time.
- **The plan.md terms beat plain learning progress** with fresh gadgets: 5/5
  seeds in the pre-set run, at 38% gadget time vs 59%.
- **No happiness version beat random, surprise and novelty in every seed.**
  Two pre-set runs failed, and two exploratory variants were close to random.
- **Measurement drove most of the result.** One unlucky outcome read as
  sadness, and a new gadget's "it's 50/50" read as gain. A direct measure of
  useful gain is the open problem. It would need a world model whose parts
  are shared in a way that shows transfer: object features, or a model of
  relations instead of names.
