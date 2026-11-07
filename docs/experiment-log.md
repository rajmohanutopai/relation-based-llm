# Experiment Log

This is the running chronological log for experiments. New entries go at the
top so the latest result is always visible first.

## 2026-11-07: State Machine Audit

Experiment ID:

```text
state_machines_v0
```

Purpose:

```text
Map the repo's state machines, reproduce invalid states, fix them with regression tests.
Document: docs/state-machines.md. Tests: tests/test_state_machines.py (32 pass).
```

Result:

```text
10 confirmed bugs fixed. Highest: a failed paid Gemini rerun lost results; a wrong
--output-dir deleted input splits; two runs on one --out lost half their results. One changes
reported numbers: v4 attach and both learn up to 0.018 less in area than reported, with no
verdict flipped. Training reruns remain unconfirmed; the model isn't cached here.
```

Decision:

```text
v4 report corrected. Issue groups are in the document, not filed on GitHub.
```

## 2026-11-07: Acting Agent V4.2 (new seeds; peak and re-forming)

Experiment ID:

```text
acting_agent_v4_2
```

Purpose:

```text
Confirm v4.1 on new seeds 6-10, test S-curve against a flat payment of equal total, and
test whether paying only the first forming removes fading's harm. 110 runs.
```

Result:

```text
Noise fix confirmed (5/5). The peak doesn't matter: flat matches the S-curve (13.2% vs
12.9% on gadgets; 16.1% vs 16.0%). Re-forming explains fading's harm (86% and 57% of the
rise). S-curve-only did not beat v3.1 on speed in A (2/5), though it ends higher. Surprise
leads (0.775 vs 0.750).
```

Decision:

```text
Saturating payment is what fixes noise. No evidence yet for a needed peak or for a better
learner. Report: docs/acting-agent-v4-2-design.md
```

## 2026-11-07: Object Properties V0, LLM answers

Experiment ID:

```text
object_properties_llm_v0
```

Purpose:

```text
The user waived the no-bulk-LLM-rows rule for the 385-question worksheet. A fresh
subagent with no repository access answered, blind to simulator values. Same graph test.
```

Result:

```text
Passes, 5/5 seeds. Names 0.648 on new objects, hand 0.625, sourced 0.623, llm 0.779,
table7 0.830; actions to 85% about 1,420 for names, 1,160 for llm. 94% coverage; 96.4%
agreement against a 77.9% all-"no" baseline. Limits: Claude helped build this project's
world, I worded the questions knowing the simulator, and the fields are its rule inputs.
```

Decision:

```text
Filled, mostly true graphs help, and coverage was the gap. Not proof for language. Next:
a test on properties chosen independently of the world. Report: docs/object-properties-v0.md
```

## 2026-11-07: Age 6mo Relation Audit V0

Experiment ID:

```text
age_6mo_relation_audit_v0
```

Purpose:

```text
First check of the 9,253 hand-written rows: machine checks on all, and one reader
(Claude) on a fixed random sample of 200. No row or status changed.
```

Result:

```text
Form is clean: no missing fields, repeated IDs or opposite-relation clashes; 106
repeated triples and 2 polarity conflicts. In the sample, 171 of 200 had no fault;
1 doubtful fact, 2 garbled, 7 with the wrong relation, 18 in adult or theory
language, 1 empty. Rows join up poorly on exact phrases: 82% of 8,415 nodes appear
in one row, and 14% of rows have both ends in the concept list.
```

Decision:

```text
Don't review row by row first. Decide on theory-language rows, then design a
phrase-to-concept step. User's call. Report: docs/age-6mo-relation-audit-v0.md
```

## 2026-11-07: Object Properties V0 (facts from external sources)

Experiment ID:

```text
object_properties_v0
```

Purpose:

```text
Fill the graph's physical-fact gap from ConceptNet and Visual Genome through a
mapper, with no LLM rows and no simulator values, then rerun the v1 graph test.
```

Result:

```text
Fails both rules. 54 of 385 cells (14%), 61% agreeing with the simulator, with many
disagreements a clash of meaning. Sourced beat names on both measures in 0/5 seeds
and hand on new objects in 2/5. New objects: names 0.648, hand 0.625, sourced 0.623,
table7 0.830. I predicted 25-40% coverage, about 75% agreement, and a win over hand;
all three were wrong.
```

Decision:

```text
These sources can't supply the table. Wrote a blank 385-question worksheet for the
user, blind to simulator values. Report: docs/object-properties-v0.md
```

## 2026-11-07: Acting Agent V4.1 (which part of the spike worked)

Experiment ID:

```text
acting_agent_v4_1
```

Purpose:

```text
Split v4's spike rule into low pay, fading and S-curve, in all 8 combinations, to
see which removes the pull to noise. 80 runs; corners reproduce v4 exactly.
```

Result:

```text
The S-curve alone is enough: same-gadget time 25.3% -> 15.3%, below random's 17% in
4/5 seeds. Low pay helps less (18.9%, 1/5). Fading makes noise worse (+3 points, in
every pairing and seed), so fading plus S-curve without low pay fails (19.3%, 0/5).
No one switch carries the learning cost in fresh-gadget rooms. I predicted low pay
would be the main cause, and it isn't. Surprise still leads.
```

Decision:

```text
S-curve only is the best version so far, but I picked it after seeing the data; it
needs fresh seeds. Report: docs/acting-agent-v4-1-design.md. Whole line summarised
in docs/acting-agent-summary.md
```

## 2026-11-05: Acting Agent V4 (attach and spike)

Experiment ID:

```text
acting_agent_v4
```

Purpose:

```text
Test the user's two rules against happiness from noise. Attach: links must
connect to seed concepts or grow from them. Spike: unconfirmed links fade
fast, strength follows an S-curve, and each thing can confirm a link once.
```

Result:

```text
Noise rule passed: spike and both spent less time on gadgets than random in
5/5 seeds in both conditions (same gadgets: 25% -> 14-15%, random 17%). Attach
alone failed; its frontier reached all 36 features. Learning rule failed for
every version: in fresh-gadget rooms spike gave up the old lead (0.734 ->
0.693-0.702, random 0.696), and surprise stays ahead. False links were about 1%
everywhere, so my guess that they were widespread was wrong.
```

Decision:

```text
Spike fixes the noise trap but doesn't yet build better knowledge. Report:
docs/acting-agent-v4-design.md
```

## 2026-11-04: Acting Agent V3 (explicit connections)

Experiment ID:

```text
acting_agent_v3
```

Purpose:

```text
Compute happiness and sadness as the user's theory states them: an explicit
store of specific and general links (general links form only from specific
ones), happiness = sum of strength gain x (1 - strength), sadness = sum of
strength x miss.
```

Result:

```text
Mixed. Gate failed once (single-feature links polluted by gadgets); fixed
with paired-feature links and a strongest-link predictor before any arm
comparison. Grokking held: all top-1% happiest tries formed a general link
(base rate 22%), and happiness per try fell about 90% with age. With fresh
gadgets, happiness beat random, novelty and learning progress in 5/5 seeds
(area 0.737 vs 0.696 random). With fixed gadgets it spent 38% of its time on
them and lost (0.714 vs 0.718 random, 0.751 surprise). Sadness was swamped by
everyday noise; the big world change was no sadder than the small one.
```

Decision:

```text
Main and grief rules failed. Next candidate: sadness from repeated failure
of strong links, and find why fixed gadgets keep paying. Report:
docs/acting-agent-v3-design.md
```

v3.1 (2026-11-04):

```text
Fixed gadgets trapped the agent through a promised grok that never came
(gadget feature links always "about to form"). Fix: expected chance of
forming = 1/(2 + past failures). Sadness now needs repeated failure above a
link's usual rate. Gadget time in A fell 38% -> 26% (random 16%); area 0.728
(random 0.718, surprise 0.751). B unchanged: beats random, novelty, LP 5/5.
Everyday sadness fell ~20x. Grief test still flat: the "big" change touched
only 29 tries in 1,000, so it was too small to test.
```

Fair grief test (2026-11-04):

```text
Big change: every light thing stops moving when pushed (~12% of tries);
small: one light object. Valid run after two test-code fixes (noise kept,
changed outcomes from their own random source so runs stay matched). Failed:
total sadness big/small 0.79-1.14, no seed above 2x. Changed moments are
1.5-3.3x sadder (waves), but total sadness doesn't rise: links measured
against their usual failure rate adapt as fast as the loss comes.
```

## 2026-11-04: Acting Agent V2 (both gates failed)

Experiment ID:

```text
acting_agent_v2
```

Purpose:

```text
Give the happiness rule a fair test: a world too big to cover at random
(800 made-up objects in 16 kinds, 20 objects + 4 gadgets per room, 15
actions per room), graph features so things share what is learned, and a
useful-gain measure (one step's effect on the 8 nearest probe objects, same
action) checked against the graph and names models first.
```

Pass rules and prediction:

```text
Fixed in the design before any run. Main rule: happiness_useful beats
learning_progress, novelty and surprise in both gadget conditions, 4 of 5
seeds. Predicted: gate passes, main rule passes, beating random fails.
Report: docs/acting-agent-v2-design.md
```

Gate result (2026-11-04):

```text
Failed. Neighbour transfer was negative for ordinary things with the graph
model (step 0.05 harms a trained model). With smaller steps it is positive
for everything, gadgets too, and the same for graph and names models: it
measures general learning, not carry-over. Sizing also failed: random tried
58% of regions, and the graph model stopped improving by about 1,600 actions
(16 kinds make 600 objects easy). Full grid not run. Third loss-based
useful-gain measure to fail.
```

Second gate (2026-11-04):

```text
Failed. Decision transfer (neighbour answers fixed minus broken by one step)
in a 100-kind, 1,200-object world: graph model -0.016 for ordinary things
(one try breaks more than it fixes), names model slightly positive. The
graph model still plateaus at about 0.80 early. Fourth single-try measure to
fail; stopped and handed back.
```

## 2026-11-03: Acting Agent V1 (gate)

Experiment ID:

```text
acting_agent_v1
```

Purpose:

```text
Give the agent's world model shared features (word vectors) so useful gain
(carry-over to other things) can be measured.
```

Result:

```text
Gate failed. One-step transfer to other cases is negative for ordinary things
(-0.003 to -0.004) with names or word vectors. Word vectors carry over a
little (zero-shot new objects 0.654 vs 0.597), too weakly to show in the
transfer test. Full grid not run.
```

Decision:

```text
Next candidate: graph-derived property features (noisy, with gaps), which
also tests the "graph speeds up a small learner" hunch. Report:
docs/acting-agent-v1-design.md
```

Graph features (exploratory; simulated graph = property table + errors/gaps):

```text
Perfect graph: actions to 85% ~700 vs ~1530 for names; new objects 0.860 vs
0.597. 2% errors 0.834, 5% 0.773, 10% 0.760 on new objects; speed gain mostly
gone at 10% errors. With a free per-thing slot, a noisy graph is ignored. The
transfer gate fails even with the perfect graph, so the one-step transfer
test is dropped as a usefulness measure.
```

Hand-written graph test (pre-set rule; random agent; 5 seeds):

```text
Fails as predicted. The 6mo rows give 23 of 294 property cells (8%) and none
for held-out objects; hand graph 0.808 / 0.625 vs names 0.826 / 0.648. True
values at the same cells score the same, so coverage, not correctness, is the
limit. A complete true 7-field table: 0.865 / 0.830, ~40% fewer actions to
85%.
```

## 2026-11-03: Acting Agent V0

Experiment ID:

```text
acting_agent_v0
```

Purpose:

```text
Test the happiness rule as the only reward of an agent that acts in a
simulated room with gadgets that teach nothing, against random, surprise,
novelty, plain pleasure and plain learning progress.
```

Setup:

```text
scripts/acting_agent_v0.py; world_sim rules without text; 6 ordinary things
+ 2 gadgets per room; 3000 actions; small MLP world model; prequential loss.
Signal check in an exact world, then a confirmatory run with 10% outcome
noise, same gadgets (A) or fresh gadgets each room (B), 5 seeds.
```

Result:

```text
Fails the pass rule. A: surprise and novelty 0.839, happiness 0.823, random
0.820. B: random 0.813, happiness 0.806; fresh gadgets trap novelty (50%) and
learning progress (59%); happiness 38%, beats learning progress in 5/5 seeds.
The sadness term fires on unlucky outcomes for known toys, so the rule
prefers gadgets to them.
```

Rerun with connection loss = forgetting (pre-set rule, same pass rule):

```text
Fails again. A: 0.829, beats random 4/5 but trails surprise and novelty
(0.839); gadget time 21%. B: 0.790 vs random 0.813; 60% on fresh gadgets.
A new gadget gives real but useless gain (learning it is 50/50); no version
measures "useful".
```

Decision:

```text
Two pre-set tries failed. Next idea, exploratory: useful gain = gain that
improves prediction in other regions (transfer). Report:
docs/acting-agent-v0-design.md
```

Exploratory useful-gain run (gradient cosine as transfer):

```text
A 0.834, B 0.816 (best happiness numbers; B edges random 0.813), but the
cosine was ~0.002 for both gadgets and toys, so the gain term vanished and the
arm acted close to random. Not evidence for the idea.
```

Direct transfer test (one step on the new case alone, loss change elsewhere):

```text
Does not separate: about -0.002 for toys and gadgets alike. Agent work
paused per the stopping rule. Useful gain remains untested; it likely needs a
world model with shared object features.
```

## 2026-11-03: Sampler Experiment V2

Experiment ID:

```text
sampler_v2
```

Purpose:

```text
Test the full plan.md happiness rule (activation + gain - loss - shortcut) as
a sampler, measured on unseen rows, against random and surprise.
```

Setup:

```text
world_sim_v1 + 1600 noise rows; 3.48M-param GPT; 1500 steps x batch 32;
3 seeds. 64 unseen + 64 seen probe rows per cluster, answer-word loss,
smoothed. Arms: random, surprise, happiness, happiness_review (+ loss).
```

Result:

```text
random wins in every seed on curve area for test_iid (0.749 vs 0.734 / 0.738)
and new objects (0.650 vs 0.598 / 0.605). Surprise chased noise (13.7% of
picks); happiness cut it to 4-5%, but avoiding 9% waste didn't pay. Most of
the loss comes early, when the sampler starves tasks. Fails the pass rule.
```

Decision:

```text
Drop the happiness sampler for choosing training rows. Next test the rule as
the reward of an acting agent in the simulator. Report:
docs/sampler-v2-experiment.md
```

## 2026-11-02: Sampler Experiment V1

Experiment ID:

```text
sampler_v1
```

Purpose:

```text
Test whether choosing what to learn by the happiness rule
(drop in loss * (1 - strength), plus replay when a strong link weakens)
beats random, fixed roots-first, and surprise-seeking sampling.
```

Setup:

```text
world_sim_v1 + 1600 noise rows; 3.48M-param GPT; word tokenizer; 3000 steps x
batch 32; 3 seeds; only the sampler differs between arms.
```

Result:

```text
test_iid / new wording / new objects (stated) / curve area:
random     0.919 / 0.620 / 0.792 / 0.821
happiness  0.907 / 0.565 / 0.764 / 0.806
surprise   0.906 / 0.605 / 0.751 / 0.804
fixed      0.859 / 0.546 / 0.690 / 0.608
Random leads at every point on the curve. The happiness sampler's picks stayed
near-even (7-10% per cluster); its signal was too noisy to steer. The noise
test was flawed (noise rows mostly learnable).
```

Decision:

```text
Fixed roots-first ordering does not help (agrees with May 3). Run one
follow-up with a stronger happiness signal, answer-only noise scoring, and
finer clusters; if happiness still loses to random, move to the acting-agent
experiment.
```

Detailed report:

```text
docs/sampler-v1-experiment.md
```

## 2026-11-02: World Simulator V1

Experiment ID:

```text
world_sim_v1
```

Purpose:

```text
Fix v0's one-word physics answers, and add the parts the happiness-sampler
test needs: shortcut ("drug") cases, a learn-more choice task, and an
unlearnable noise set.
```

Counts:

```text
train 16501, dev 1663, test_iid 1231, test_new_wording 1233,
test_new_object 3086; train_noise 1600, test_noise 400; 15 task types
```

Result:

```text
On new objects, the best single word for push_moves fell from 1.000 to 0.495
and for shake_sound from 0.910 to 0.244. Test-wording sentence overlap fell
from 29% to 18%. Lint finds no issues. The hand-written audit checked 34
relations: 32 agree, 2 differ in meaning. drop_* and push_falls still lean on
surface words (0.6-0.85).
```

Decision:

```text
Use v1 for the first happiness-sampler run (random vs fixed vs happiness,
4M, 3 seeds, tight budget, noise files in the sampler pool).
```

Detailed report:

```text
docs/world-sim-v1.md
```

## 2026-11-02: World Simulator V0

Experiment ID:

```text
world_sim_v0
```

Purpose:

```text
Replace template-first rows with rows computed from a small simulated world
(objects, containers, surfaces, baby height, caregiver, relation strengths).
Fix the root_bridge_600_v1 problems: narrow tasks, one-word giveaways, four
fixed happiness answers, and broken grammar.
```

Counts:

```text
train 14420, dev 1448, test_iid 1026, test_new_wording 1015,
test_new_object 2003; 13 task types; train vocabulary 321 words
```

Result:

```text
No test input appears in train. Lint finds no errors. Answers are balanced
(yes/no tasks at 50/50). On new objects, the best single word scores
0.24-0.63 on reach, sight, tracking and feeling tasks, close to the majority
baseline. Single-object physics tasks are still decided by the object's name.
```

Decision:

```text
Add shortcut cases, a noise cluster, and more varied physics objects in v1
before the happiness-sampler run. Do not train a comparison on v0 alone.
```

Detailed report:

```text
docs/world-sim-v0.md
```

## 2026-05-01: Age 6mo Root World 500

Experiment ID:

```text
age_6mo_root_world_500
```

Purpose:

```text
Create the full 500-concept 6-month root-world seed. These are embodied
relation handles for model training, not spoken-word milestones.
```

Counts:

```text
concepts: 500
relations: 1092
curriculum rows: 3155
```

Category allocation:

```text
core_relation:              45
body_part:                  35
body_action_control:        40
sensory_input:              55
body_state_valence:         50
space_motion_physics:       55
object_property:            40
common_object:              55
caregiver_social:           35
routine_event:              45
sound_language_precursor:   25
learning_memory:            20
```

Status allocation:

```text
active:                     407
emerging:                    69
latent:                      14
internal:                    10
```

Update:

```text
Review fixes applied: root anchors are now real concepts, advanced concepts are
marked active/emerging/latent, smell/body-balance/internal sensation coverage was
added, valence-learning hubs were strengthened, and common objects now carry
richer relation bundles.
```

Second review fixes:

```text
Relation schema normalized to a closed 18-type vocabulary.
Relation targets now resolve to concept nodes or declared external anchors.
Forward prerequisite validation added and passed.
Sparse bundles enriched; no concept has only one relation.
Status-aware scene_relation rows added for active/emerging concepts.
```

Third review fixes:

```text
Added internal status for ontology-only handles.
Moved abstract graph handles such as relation/state/event/action/input/cause/effect
out of active child-facing status.
Added missing desire/control/social-regulation handles: wanted, not wanted, too
much, enough, can control, cannot control, alone, with caregiver, not held, safe
touch, start, stop, again, gone, back again, body limit.
Removed or replaced weaker/specific handles: doctor touch, family group, arms,
kiss touch, chew gum, crawl attempt, teething discomfort, medicine discomfort,
bath comfort, transition, interruption, path, blocked path, container boundary.
```

US-first cleanup:

```text
Removed India-specific handles from the 6mo seed. Replaced dal/ragi/nappy/
pressure cooker whistle with oatmeal/applesauce/wipes/vacuum sound.
Demoted support, boundary, physical support, contact, no contact, waiting,
sound pattern, repetition comfort, success feeling, and blocked feeling from
active to emerging.
Enriched body limit, gone, back again, and safe touch with experiential relation
bundles.
```

Validation:

```text
expected_total: 500
actual_total: 500
duplicate_words: 0
missing prerequisites: 0
forward prerequisites: 0
unknown relation targets: 0
unknown relation types: 0
empty relation bundles: 0
category count mismatches: 0
JSON files parse cleanly.
```

Files:

```text
generator: scripts/create_age_6mo_root_world_500.py
seed: data/developmental_graph/seeds/age_6mo_root_world_500.json
curriculum: data/developmental_graph/experiments/age_6mo_root_world_500/curriculum.jsonl
report: docs/age-6mo-root-world-500.md
```

Decision:

```text
Use this as the age_6mo source concept set. The first scene_relation renderer is
now included; next build a richer multi-relation episode renderer before serious
training.
```

## 2026-05-01: Procedural Foundation V7 ConceptNet

Experiment ID:

```text
procedural_foundation_v7_conceptnet
```

Purpose:

```text
Create the first reusable project-specific ConceptNet layer: high-frequency
normal words mapped to a staged relation system.
```

Core design:

```text
word -> age level -> domain tags -> prerequisite earlier words -> relation bundle
```

Counts:

```text
concepts: 215
relations: 283
train rows: 713
dev rows: 279
curriculum_test rows: 156
```

Age levels:

```text
age_6mo: 39 concepts
age_1yo: 51 concepts
age_3yo: 47 concepts
age_5yo: 78 concepts
```

Validation:

```text
duplicate words: 0
missing prerequisites: 0
forward prerequisites: 0
empty relation bundles: 0
JSON manifests parse cleanly.
```

Files:

```text
generator: scripts/create_procedural_foundation_world_v7_conceptnet.py
seed: data/developmental_graph/seeds/adi_conceptnet_v7.json
generated output: data/developmental_graph/experiments/procedural_foundation_v7_conceptnet/
report: docs/procedural-foundation-v7-conceptnet.md
```

Decision:

```text
Use V7 as the curated relation-lexicon source of truth. Do not train a serious
model on V7 alone yet; next add a scene renderer that converts relation bundles
into ordinary relation-dense examples.
```

## 2026-04-30: Root Procedural Expansion V1

Experiment ID:

```text
root_procedural_expansion_v1
```

Purpose:

```text
Expand root_concept_foundation_v1 into a larger ordinary-language procedural
QA dataset with hidden root-relation metadata and dense/sparse/corrupt control
arms.
```

Data:

```text
generator: scripts/create_root_procedural_expansion_v1.py
generated output: data/developmental_graph/experiments/root_procedural_expansion_v1/
root seed: root_concept_foundation_v1
```

Source units:

```text
total: 3276
train: 1926
dev: 258
test_observation: 380
test_inference: 53
test_transfer: 375
test_counterfactual: 284
```

Rendered records per variant:

```text
train: 9630
dev: 1290
curriculum_test: 5460
```

Variants:

```text
root_dense_qa
root_sparse_qa
root_corrupt_qa
```

Validation:

```text
No train/test source-id overlap.
No train/test counterfactual-group overlap.
No selected transfer-key train overlap.
No dense-train ambiguous prompts.
No shorthand protocol leaks.
No bare visible "Question: Why?" prompts.
No visible relation-label phrases like "open lets touch happen".
```

Local nanochat training:

```text
run directory: runs/nanochat_root_procedural_v1_20260430/
model: nanochat decoder-only transformer, depth 4, 4 heads, 256 embedding dim
parameters: about 4.06M
context length: 256
tokenizer vocab: 881, padded to 896 at runtime
iterations: 1000 per variant
training tokens: 2048000 per variant
device: Apple MPS
variants trained: root_dense_qa, root_sparse_qa, root_corrupt_qa
```

Training validation bpb:

```text
root_dense_qa:   final 0.129592, min 0.115348
root_sparse_qa:  final 0.132896, min 0.121064
root_corrupt_qa: final 0.131706, min 0.120557
```

Held-out evaluation:

```text
dataset: root_dense_qa/curriculum_test.jsonl
examples: 5460
temperature: 0.0
max generated tokens: 48
summary: runs/nanochat_root_procedural_v1_20260430/evaluation/dense_curriculum_test_d4_i1000/summary.md
```

Overall exact-match results:

```text
root_dense_qa:   answer 94.5% (5162/5460), reason 94.2% (5144/5460)
root_sparse_qa:  answer 52.7% (2879/5460), reason 36.9% (2016/5460)
root_corrupt_qa: answer 45.3% (2474/5460), reason 44.5% (2431/5460)
```

Dense held-out bucket results:

```text
test_observation:    answer 95.5%, reason 94.2%
test_inference:      answer 100.0%, reason 99.6%
test_transfer:       answer 92.7%, reason 93.2%
test_counterfactual: answer 94.6%, reason 94.6%
```

Known weakness:

```text
The dense model is weak on language_name examples: answer 51.1%, reason 51.1%.
It often flips word-object match/mismatch cases. The next root dataset revision
should make naming examples clearer and more numerous before TinyStories word
attachment.
```

Decision:

```text
The dense ordinary-language relation data strongly beats sparse and corrupt
controls on the same dense held-out prompts. Continue, but fix the weak naming
task before using this root model as the base for TinyStories word attachment.
```

Detailed report:

```text
docs/root-procedural-expansion-v1.md
```

## 2026-04-30: Root Concept Foundation V1

Experiment ID:

```text
root_concept_foundation_v1
```

Purpose:

```text
Replace the V0 root foundation with a cleaner relation-first seed graph that
fixes split leakage, clearer relation semantics, concrete positive/negative
scenario probes, and a first explicit encoding of the happiness mechanism.
```

Data:

```text
seed graph: data/developmental_graph/seeds/root_concept_foundation_v1.json
generator: scripts/create_root_concept_foundation_v1.py
generated output: data/developmental_graph/experiments/root_concept_foundation_v1/
```

Graph counts:

```text
layers: 11
nodes: 133
relations: 172
micro experiences: 84
evaluation questions: 34
```

Dataset variants:

```text
root_prose: 239 train,  6 dev, 11 curriculum_test
root_qa:    306 train, 12 dev, 22 curriculum_test
root_mixed: 545 train, 18 dev, 33 curriculum_test
```

Validation:

```text
Graph validation passes.
No train/dev/test canonical group overlap in root_prose, root_qa, or root_mixed.
```

Decision:

```text
Use V1 instead of V0 as the root seed. Do not treat it as enough data for a
serious model run by itself; expand it procedurally before the next training
experiment, then compare against TinyStories-only and corrupt/shuffled controls.
```

Detailed report:

```text
docs/root-concept-foundation-v1.md
```

## 2026-04-30: Root Concept Foundation V0

Experiment ID:

```text
root_concept_foundation_v0
```

Purpose:

```text
Start the TinyStories relation-first path by creating a root concept graph and
small prose/QA curriculum. Later TinyStories words should attach to these root
anchors by inheritance instead of repeating flat definitions.
```

Data:

```text
seed graph: data/developmental_graph/seeds/root_concept_foundation_v0.json
generator: scripts/create_root_concept_foundation_v0.py
generated output: data/developmental_graph/experiments/root_concept_foundation_v0/
```

Graph counts:

```text
layers: 12
nodes: 95
relations: 112
micro experiences: 10
evaluation questions: 10
```

Dataset variants:

```text
root_prose: 100 train, 18 dev, 14 curriculum_test
root_qa:    108 train,  8 dev, 16 curriculum_test
root_mixed: 208 train, 26 dev, 30 curriculum_test
```

Decision:

```text
Use root_mixed as the first Stage 1 candidate, then build
tinystories_word_attachment_v0 from frequent TinyStories vocabulary. Do not
claim performance yet; no model training has been run for this stage.
```

Detailed report:

```text
docs/root-concept-foundation-v0.md
```

## 2026-04-29: nanochat V6 Transfer QA Dense/Sparse/Corrupt Run

Experiment ID:

```text
nanochat_v6_transfer_qa_20260429
```

Purpose:

```text
Test whether relation-dense ordinary text creates reusable relation behavior
across observation, inference, transfer, and counterfactual held-out buckets.
```

Data and model:

```text
dataset: procedural_foundation_v6_transfer_qa
model variants: ordinary_dense_qa, ordinary_sparse_qa, ordinary_corrupt_qa
relations visible to model: no
train records per variant: 17720
held-out dense prompts: 8525
parameters: 4325506
iterations: 1000
training tokens per variant: 2048000
context length: 256
tokenizer vocab: 1146
```

Training validation bpb:

```text
ordinary_dense_qa:   2.448177 -> 0.121423
ordinary_sparse_qa:  2.593039 -> 0.114275
ordinary_corrupt_qa: 2.446165 -> 0.118257
```

Held-out evaluation on dense ordinary prompts:

```text
ordinary_dense_qa:   91.7% answer exact, 90.3% reason exact
ordinary_sparse_qa:  53.1% answer exact, 43.4% reason exact
ordinary_corrupt_qa: 33.9% answer exact, 31.7% reason exact
```

Dense model bucket scores:

```text
test_observation:    85.0% answer exact, 84.3% reason exact
test_inference:      98.1% answer exact, 97.0% reason exact
test_transfer:       89.0% answer exact, 87.4% reason exact
test_counterfactual: 99.4% answer exact, 96.9% reason exact
```

Decision:

```text
This is the strongest controlled result so far. Dense ordinary relation text
beats sparse and corrupt controls by a large margin, including on transfer and
counterfactual tests. Continue with learning-curve, vocabulary-transfer, and
mixed-domain tests before claiming general language improvement.
```

Detailed report:

```text
docs/procedural-foundation-v6-transfer-qa.md
runs/nanochat_v6_transfer_qa_20260429/evaluation/dense_curriculum_test_d4_i1000/summary.md
```

## 2026-04-29: Procedural Foundation V6 Transfer QA Dataset

Experiment ID:

```text
procedural_foundation_v6_transfer_qa
```

Purpose:

```text
Move beyond V5's dense-vs-sparse result and test whether relation-dense
ordinary text supports reusable relation rules across observation, inference,
transfer, and counterfactual held-out buckets.
```

Data:

```text
source world: procedural_foundation_v3
main variant: ordinary_dense_qa
control variants: ordinary_sparse_qa, ordinary_corrupt_qa
relations visible to model: no
prompt surfaces per unit: 5
```

Dense main-arm counts:

```text
train records: 17720
dev records: 2315
test_observation records: 2695
test_inference records: 1700
test_transfer records: 2380
test_counterfactual records: 1750
curriculum_test records: 8525
```

Validation:

```text
dense train ambiguous inputs: 0
dense curriculum_test ambiguous inputs: 0
visible relation tag leaks: 0
counterfactual groups with both true and false cases: 146 / 146
```

Decision:

```text
V6 is ready for the next nanochat run. Train dense, sparse, and corrupted
control models, then evaluate all of them on the dense V6 held-out buckets.
```

Detailed report:

```text
docs/procedural-foundation-v6-transfer-qa.md
```

## 2026-04-29: nanochat V5 Sparse QA Full 22K 1000-Iteration Control

Experiment ID:

```text
nanochat_v5_sparse_qa_22k_i1000_20260429
```

Purpose:

```text
Check whether the sparse-control failure at 5K / 250 disappears when the
model gets the full V5 training set and a longer 1000-iteration budget.
```

Data and model:

```text
dataset: procedural_foundation_v5_sparse_qa
variant: word_sparse_qa
train records: 22680
held-out prompts: 3115
parameters: 4391042
training tokens: 2048000
iterations: 1000
tokenizer: reused V5 full word_plain_qa tokenizer
validation bpb: 2.528003 -> 0.120677
```

Held-out evaluation:

```text
dense plain QA -> dense prompts:       86.4% answer exact, 84.8% reason exact
relation-output QA -> dense prompts:   86.1% answer exact, 83.7% reason exact
sparse QA -> dense prompts:            48.0% answer exact, 42.9% reason exact
sparse QA -> sparse prompts:           44.1% answer exact, 43.4% reason exact
```

Decision:

```text
The sparse control still fails at full size. More examples and more training
do not recover the missing relation distinctions. This strengthens the
interpretation that the high V5 score depends on relation-dense ordinary text,
not just the answer protocol or generator priors.
```

Detailed report:

```text
docs/nanochat-v5-sparse-qa-control-2026-04-29.md
```

## 2026-04-29: nanochat V5 Sparse QA Control

Experiment ID:

```text
nanochat_v5_sparse_qa_5k_i250_20260429
```

Purpose:

```text
Validate whether the strong V5 plain-QA result comes from relation-dense text,
not merely from the answer protocol, object priors, or generator distribution.
```

Data and model:

```text
dataset: procedural_foundation_v5_sparse_qa_5k
variant: word_sparse_qa
train records: 5000
held-out prompts: 3115
parameters: 4391042
training tokens: 512000
iterations: 250
tokenizer: reused V5 5K word_plain_qa tokenizer
```

Control design:

```text
Same source examples and same answer/reason targets as V5 5K plain QA, but
scene text removes discriminating cues such as near/far, open/closed, wet/dry,
edge/middle, counts, colors, and hot/cold.
```

Held-out evaluation:

```text
dense plain QA -> dense prompts: 82.2% answer exact, 70.7% reason exact
sparse QA -> dense prompts:      47.0% answer exact, 33.4% reason exact
sparse QA -> sparse prompts:     49.4% answer exact, 42.9% reason exact
```

Decision:

```text
This strongly supports the current hypothesis. The high V5 plain-QA result
depends on relation-dense ordinary text. A sparse text control with the same
protocol, tokenizer, model, and token budget falls near chance.
```

Detailed report:

```text
docs/nanochat-v5-sparse-qa-control-2026-04-29.md
```

## 2026-04-29: nanochat V5 5K Relation-As-Input 250-Iteration Run

Experiment ID:

```text
nanochat_v5_consistent_qa_5k_relation_input_i250_20260429
```

Purpose:

```text
Test the relation design that does not emit relation scaffolds. Relation facts
are prepended to the input, while the target remains answer/reason only.
```

Data and model:

```text
dataset variant: word_relation_input_qa
train records: 5000
held-out prompts: 3115
average relation input lines: about 8
ambiguous prompt inputs: 0
shorthand protocol hits: 0
parameters: 4391042
training tokens: 512000
iterations: 250
```

Sequence length:

```text
relation-input prompt+target max length: 149 tokens
context length: 256
no context truncation issue found
```

Held-out evaluation:

```text
word_relation_input_qa: 81.9% answer exact, 59.9% reason exact
```

Comparison at 5K / 250 iterations:

```text
plain QA: 82.2% answer exact, 70.7% reason exact
relation-output QA: 74.5% answer exact, 55.8% reason exact
relation-input QA: 81.9% answer exact, 59.9% reason exact
```

Decision:

```text
Relation-as-input is much better than relation-output for answer accuracy, but
it still does not beat plain QA at 250 iterations. The likely issue is noisy
relation input: about 8 relation lines are provided, and the model does not
reliably select the exact relation that should become the reason.
```

Next:

```text
Try relation-candidate-input QA: provide only 3-5 candidate relation anchors,
including the correct reason anchor, and keep output answer/reason only.
```

Detailed report:

```text
docs/nanochat-v5-consistent-qa-5k-local-run-2026-04-29.md
```

## 2026-04-29: nanochat V5 Consistent QA 5K 250-Iteration Run

Experiment ID:

```text
nanochat_v5_consistent_qa_5k_i250_20260429
```

Purpose:

```text
Run the same 5K V5 comparison with 250 iterations instead of 1000, to test
whether output relation scaffolding improves early learning speed.
```

Data and model:

```text
dataset: procedural_foundation_v5_consistent_qa_5k
train records per variant: 5000
held-out prompts: 3115
parameters: 4391042
training tokens per arm: 512000
iterations per arm: 250
```

Training:

```text
word_plain_qa validation bpb: 2.466605 -> 0.188111
word_relation_scaffolded_qa validation bpb: 2.289457 -> 0.137097
```

Held-out evaluation:

```text
word_plain_qa: 82.2% answer exact, 70.7% reason exact
word_relation_scaffolded_qa: 74.5% answer exact, 55.8% reason exact
```

Decision:

```text
At 250 iterations, output-scaffolded relations are worse despite lower BPB.
This argues against relation scaffolding as answer-time generated text for
early learning. Next test should use relation-as-input or auxiliary relation
prediction with answer-only output.
```

Detailed report:

```text
docs/nanochat-v5-consistent-qa-5k-local-run-2026-04-29.md
```

## 2026-04-29: nanochat V5 Consistent QA 5K Local Run

Experiment ID:

```text
nanochat_v5_consistent_qa_5k_20260429
```

Purpose:

```text
Repeat the V5 proper-word nanochat experiment with only 5000 matched train
records per variant, to test whether relation scaffolding helps under lower
distinct-data conditions.
```

Data:

```text
dataset: procedural_foundation_v5_consistent_qa_5k
selection: matched random sample by source_example_id + prompt_type
train records per variant: 5000
dev records per variant: 2765
curriculum_test records per variant: 3115
ambiguous prompt inputs: 0
shorthand protocol hits: 0
tokenizer: reused full V5 tokenizer to keep model size fixed
```

Model:

```text
nanochat from scratch
parameters: 4391042
layers: 4
embedding size: 256
heads: 4
context length: 256
vocab size: 1216
training tokens per arm: 2048000
iterations per arm: 1000
device: MPS
```

Training:

```text
word_plain_qa validation bpb: 2.466605 -> 0.195234
word_relation_scaffolded_qa validation bpb: 2.289457 -> 0.043949
```

Held-out evaluation:

```text
dataset: data/developmental_graph/experiments/procedural_foundation_v5_consistent_qa_5k/datasets/word_plain_qa/curriculum_test.jsonl
examples: 3115
word_plain_qa: 86.1% answer exact, 82.7% reason exact
word_relation_scaffolded_qa: 86.8% answer exact, 83.3% reason exact
```

Decision:

```text
The 5K run weakly supports the sample-efficiency hypothesis: relation
scaffolded QA slightly beats plain QA when distinct training records are
reduced from 22680 to 5000. The next test should reduce token budget too
because this run used the same 2048000 training tokens as the 22K run.
```

Detailed report:

```text
docs/nanochat-v5-consistent-qa-5k-local-run-2026-04-29.md
```

## 2026-04-29: nanochat V5 Consistent QA Local Run

Experiment ID:

```text
nanochat_v5_consistent_qa_20260429
```

Purpose:

```text
Train tiny nanochat models from scratch on a cleaned proper-word procedural
foundation dataset. V5 fixes the V4 issue where the same prompt could map to
multiple target formats.
```

Data:

```text
dataset: procedural_foundation_v5_consistent_qa
variants: word_plain_qa, word_relation_scaffolded_qa
train records per variant: 22680
dev records per variant: 2765
curriculum_test records per variant: 3115
ambiguous prompt inputs: 0
shorthand protocol hits: 0
```

Model:

```text
nanochat from scratch
parameters: 4391042
layers: 4
embedding size: 256
heads: 4
context length: 256
vocab size: 1216
training tokens per arm: 2048000
iterations per arm: 1000
device: MPS
```

Training:

```text
word_plain_qa validation bpb: 2.466605 -> 0.137033
word_relation_scaffolded_qa validation bpb: 2.289457 -> 0.040710
```

Held-out evaluation:

```text
dataset: data/developmental_graph/experiments/procedural_foundation_v5_consistent_qa/datasets/word_plain_qa/curriculum_test.jsonl
examples: 3115
prompt suffix: blank line, matching input_target training shards
word_plain_qa: 86.4% answer exact, 84.8% reason exact
word_relation_scaffolded_qa: 86.1% answer exact, 83.7% reason exact
```

Decision:

```text
The proper-word procedural dataset is viable for tiny from-scratch training.
This relation-scaffolded-output design did not beat plain QA, even though it
fit validation text better. Next relation experiment should avoid making the
model emit relation scaffolds at answer time.
```

Detailed report:

```text
docs/nanochat-v5-consistent-qa-local-run-2026-04-29.md
```

## 2026-04-29: Procedural Foundation V5 Consistent QA Dataset

Experiment ID:

```text
procedural_foundation_v5_consistent_qa
```

Purpose:

```text
Create a cleaned successor to V4 with ordinary word labels and one stable
target format. V5 removes event-continuation ambiguity and duplicate output
styles for identical prompts.
```

Data:

```text
source units: 5712
train base units: 4536
dev base units: 553
curriculum_test base units: 623
prompt phrasings per unit: 5
records per variant: 22680 train / 2765 dev / 3115 curriculum_test
```

Variants:

```text
word_plain_qa
word_relation_scaffolded_qa
```

Validation:

```text
word_plain_qa train: 22680 unique inputs, 0 ambiguous inputs, 0 shorthand hits
word_relation_scaffolded_qa train: 22680 unique inputs, 0 ambiguous inputs, 0 shorthand hits
```

Decision:

```text
Use V5 rather than V4 for the first proper-word nanochat run. V4 remains useful
as a record of the failed surface-design attempt.
```

## 2026-04-29: Procedural Foundation V4 Word Surface Dataset

Experiment ID:

```text
procedural_foundation_v4_word_surface
```

Purpose:

```text
Create the next procedural dataset without shorthand protocol labels. V4 keeps
the V3 underlying world but renders each unit with proper word surfaces:
scene, question, answer, reason, because, event continuation, and full-word
relation scaffolds.
```

Data:

```text
source units: 5712
train base units: 4536
dev base units: 553
curriculum_test base units: 623
surfaces per unit: 5
records per variant: 22680 train / 2765 dev / 3115 curriculum_test
```

Variants:

```text
word_plain_text
word_relation_scaffolded
word_relation_first_then_text
```

Validation:

```text
No shorthand protocol labels found:
^s: ^q: ^a: ^f: ^r: ^n: all 0 hits across generated datasets.
```

Decision:

```text
Use word_plain_text vs word_relation_scaffolded as the next primary local
nanochat comparison. Keep relation_first_then_text only as a continuity arm.
Do not train on acronym protocol first; compact notation can be taught later.
```

Detailed report:

```text
docs/procedural-foundation-v4-word-surface.md
```

## 2026-04-29: nanochat Core4 Natural-Input Held-Out Evaluation

Experiment ID:

```text
nanochat_core4_natural_input_eval_2026_04_29
```

Purpose:

```text
Test whether the held-out relation result survives when s:/q: input tags are
removed and replaced with simple natural-language situation/question lines.
```

Run:

```text
script: scripts/run_nanochat_relation_eval.py --prompt-style natural_a
checkpoints: runs/nanochat_core4_20260429
dataset: procedural_foundation_v3 procedural_plain_text curriculum_test
examples: 623
device: mps
max generated tokens: 32
temperature: 0.0
```

Result:

```text
tinystories_plain_text:                 answer 0.0%,  fact 0.0%
procedural_plain_text:                  answer 54.6%, fact 13.3%
procedural_relation_scaffolded:         answer 61.6%, fact 39.0%
procedural_relation_first_then_text:    answer 38.4%, fact 19.1%
```

Decision:

```text
The relation-scaffolded model still beats the plain procedural model under
naturalized inputs, especially on fact exactness. But performance drops sharply
from structured prompts, so the current models depend heavily on the prompt
protocol. Next training should mix structured prompts, natural prompts, natural
Q&A, and short event-continuation text.
```

Detailed report:

```text
docs/nanochat-core4-natural-heldout-evaluation-2026-04-29.md
```

## 2026-04-29: nanochat Core4 Held-Out Relation Evaluation

Experiment ID:

```text
nanochat_core4_heldout_relation_eval_2026_04_29
```

Purpose:

```text
Evaluate the depth-4 local nanochat checkpoints on held-out procedural V3
relation questions, using the same plain prompt surface for every trained arm.
```

Run:

```text
script: scripts/run_nanochat_relation_eval.py
checkpoints: runs/nanochat_core4_20260429
dataset: procedural_foundation_v3 procedural_plain_text curriculum_test
examples: 623
device: mps
max generated tokens: 32
temperature: 0.0
```

Result:

```text
tinystories_plain_text:                 answer 0.0%,  fact 0.0%
procedural_plain_text:                  answer 74.6%, fact 39.3%
procedural_relation_scaffolded:         answer 82.2%, fact 73.4%
procedural_relation_first_then_text:    answer 50.7%, fact 19.4%
```

Decision:

```text
This is the first positive held-out signal for explicit relation scaffolding.
The scaffolded model beat the plain procedural model on the same plain prompts.
It is still same-generator transfer, not broad language transfer. Next control:
train/evaluate a plain procedural model with answer-protocol exposure but no
explicit relation lines, then compare again at matched token budget.
```

Detailed report:

```text
docs/nanochat-core4-heldout-evaluation-2026-04-29.md
```

## 2026-04-29: nanochat Core4 Depth-4 Local Run

Experiment ID:

```text
nanochat_core4_depth4_local_2026_04_29
```

Purpose:

```text
After the four-arm smoke passed, run a larger local from-scratch comparison
with the same shared tokenizer and equal token budget.
```

Run:

```text
run root: /tmp/adi_nanochat_core4_20260429_smoke
workspace copy: runs/nanochat_core4_20260429
model: nanochat depth 4
parameters: 7340162
device: mps
tokenizer: shared 4096-vocab BPE
training tokens per arm: 1024000
iterations per arm: 500
```

Validation BPB:

```text
tinystories_plain_text:                 2.967028 -> 1.221640
procedural_plain_text:                  3.621244 -> 0.150843
procedural_relation_scaffolded:         3.769814 -> 0.057640
procedural_relation_first_then_text:    3.777705 -> 0.062668
```

Decision:

```text
The longer local training path works. The procedural arms fit much faster than
TinyStories, and explicit relation variants fit the procedural validation split
best. This is not yet a theory result because BPB on same-generator dev data can
reward format/corpus simplicity. Next step is held-out relation transfer
evaluation using the saved checkpoints.
```

Detailed report:

```text
docs/nanochat-core4-local-smoke-2026-04-29.md
```

## 2026-04-29: nanochat Core4 Local Smoke

Experiment ID:

```text
nanochat_core4_local_smoke_2026_04_29
```

Purpose:

```text
Verify the full four-arm nanochat training path with a shared tokenizer:
normal simple text, relation-designed plain text, relation-scaffolded text,
and relation-first text.
```

Run:

```text
run root: /tmp/adi_nanochat_core4_20260429_smoke
model: nanochat depth 2
parameters: 1966134
device: mps
tokenizer: shared 4096-vocab BPE trained on mixed four-arm corpus
training tokens per arm: 40960
iterations per arm: 20
```

Validation BPB:

```text
tinystories_plain_text:                 3.014457 -> 2.894597
procedural_plain_text:                  3.546736 -> 3.223261
procedural_relation_scaffolded:         3.805675 -> 3.434072
procedural_relation_first_then_text:    3.842853 -> 3.461918
```

Decision:

```text
The local training path works end to end. This is a pipeline result, not a
relation-theory result. The next useful run should be longer and scored on
held-out relation transfer, not validation BPB alone.
```

Detailed report:

```text
docs/nanochat-core4-local-smoke-2026-04-29.md
```

## 2026-04-29: TinyStories V0 Baseline

Experiment ID:

```text
tinystories_v0
```

Purpose:

```text
Create a normal simple-text control for the procedural V3 relation experiment.
```

Data:

```text
train stories: 1607
dev stories: 208
curriculum_test stories: 225
```

Word budget:

```text
train: 270421 words
dev: 33008 words
curriculum_test: 36695 words
```

Interpretation:

```text
This is the fourth arm needed for the real comparison: normal simple text vs
relation-designed plain text vs relation-scaffolded text vs relation-first text.
It is matched to the V3 relation variants by approximate word budget.
```

Decision:

```text
Use tinystories_v0 as the normal-simple-text baseline for the next local
nanochat smoke test. No model training has been run yet.
```

Detailed report:

```text
docs/tinystories-v0-baseline.md
```

## 2026-04-28: Procedural Foundation V3

Experiment ID:

```text
procedural_foundation_v3
```

Purpose:

```text
Expand the base procedural world before generating more examples. V3 combines
baby body, everyday physical objects, food/liquid, places/surfaces, simple
social agents, and simple social signals.
```

Data:

```text
base entities: 208
total units: 5712
train: 4536
dev: 553
curriculum_test: 623
```

Rule families:

```text
reach_touch
push_pull_move
body_control
drop_fall
support_edge_fall
container_open_closed
hide_see
shake_sound
temperature_touch
wet_dry
safe_unsafe_touch
same_different_match
more_less_count
path_open_closed
caregiver_comfort
familiar_agent
social_signal_response
give_take
word_name_binding
```

Result:

```text
positive train cases: 2449
negative train cases: 2087
train vocabulary: 302-334 alpha words depending on variant
```

Interpretation:

```text
V3 is the current active procedural corpus. It is much less toy-like than V2
because the base world has 208 entities rather than a few dozen objects.
```

Decision:

```text
Use procedural_foundation_v3 for the next shared-tokenizer nanochat smoke test.
No V3 model training has been run yet.
```

Detailed report:

```text
docs/procedural-foundation-v3.md
```

## 2026-04-28: Procedural Foundation V2

Experiment ID:

```text
procedural_foundation_v2
```

Purpose:

```text
Expand procedural_foundation_v1 with derived questions and additional coherent
rule families while keeping a small noun world and controlled vocabulary.
```

Data:

```text
total units: 3157
train: 2477
dev: 302
curriculum_test: 378
```

Rule families:

```text
reach_touch
push_move
drop_fall
shake_sound
hide_see
container_open_closed
hot_cold_touch
support_edge_fall
same_different_match
more_less_count
path_open_closed
caregiver_comfort
word_name_binding
```

Result:

```text
positive train cases: 1136
negative train cases: 1341
train vocabulary: 133-155 alpha words depending on variant
```

Interpretation:

```text
V2 is the best current procedural foundation corpus. It asks multiple questions
over the same coherent scenarios, which tests whether relation structure can
support different answer views without simply memorizing one prompt shape.
```

Decision:

```text
V2 was the next local nanochat smoke-test candidate at this point. It was later
superseded by procedural_foundation_v3 before model training.
```

Detailed report:

```text
docs/procedural-foundation-v2.md
```

## 2026-04-28: Procedural Foundation V1

Experiment ID:

```text
procedural_foundation_v1
```

Purpose:

```text
Replace procedural_foundation_v0 with coherent scenario grammars.
```

Data:

```text
total units: 689
train: 542
dev: 66
curriculum_test: 81
```

Rule families:

```text
reach_touch
push_move
drop_fall
shake_sound
hide_see
container_open_closed
hot_cold_touch
```

Result:

```text
positive train cases: 251
negative train cases: 291
train vocabulary: 79-106 alpha words depending on variant
```

Interpretation:

```text
V1 is qualitatively better than V0 because layouts are coherent and rule-family
specific. It is still a seed dataset, not enough for serious training.
```

Decision:

```text
Use procedural_foundation_v1 as the quality base and expand it with more
derived questions and rule families before training.
```

Detailed report:

```text
docs/procedural-foundation-v1.md
```

## 2026-04-28: Procedural Foundation V0

Experiment ID:

```text
procedural_foundation_v0
```

Purpose:

```text
Generate relation-composed foundation scenarios rather than paraphrases.
```

Data:

```text
total units: 3888
train: 2994
dev: 302
curriculum_test: 592
```

Rules:

```text
near + reachable height + action -> touch
far or very high -> no touch
touch -> baby feels thing
touch + movable thing -> thing may move
unsafe thing -> not ok
heavy or big thing -> movement resistance
```

Result:

```text
positive touch/reach train cases: 835
negative touch/reach train cases: 2159
train vocabulary: 59-73 alpha words depending on variant
```

Interpretation:

```text
This is the right direction for data expansion: generate new scenarios from
world state plus relation rules, not by repeating one fact in many word forms.
```

Decision:

```text
Expand procedural rule families before serious nanochat training.
```

Detailed report:

```text
docs/procedural-foundation-v0.md
```

## 2026-04-28: Core5 V0 Foundation Ladder

Experiment ID:

```text
core5_v0_foundation
```

Purpose:

```text
Create a staged foundation ladder where high relation-load words are introduced
only after supporting simple facts.
```

Data:

```text
train: 403
dev: 60
curriculum_test: 53
held-out cases: 108
```

Train stages:

```text
f0 simple facts: 353
f1 introduce handle: 28
f2 ask using handle: 14
f3 later name: 8
```

Variants:

```text
foundation_plain_text
foundation_relation_scaffolded
foundation_relation_first_then_text
```

Vocabulary result, train split:

```text
foundation_plain_text:                92 alpha words, 96 raw tokens
foundation_relation_scaffolded:       93 alpha words, 97 raw tokens
foundation_relation_first_then_text:  93 alpha words, 97 raw tokens
```

Interpretation:

```text
The correct first rung is not merely non-technical language. It is staged
meaning: facts first, then handles, then questions using handles, then later
names like own body.
```

Decision:

```text
Use core5_v0_foundation as the prelude before core5_v0_childlang.
```

Detailed report:

```text
docs/core5-v0-foundation-ladder.md
```

## 2026-04-28: Core5 V0 Child Language

Experiment ID:

```text
core5_v0_childlang
```

Purpose:

```text
Create a child-language version of core5_v0 before nanochat from-scratch
training.
```

Data:

```text
train: 2428
dev: 296
curriculum_test: 331
held-out cases: 108
```

Variants:

```text
child_plain_text
child_relation_scaffolded
child_relation_first_then_text
```

Vocabulary result, train split:

```text
child_plain_text:                1342 alpha words, 1349 raw tokens
child_relation_scaffolded:       1342 alpha words, 1350 raw tokens
child_relation_first_then_text:  1343 alpha words, 1351 raw tokens
```

Interpretation:

```text
This is simpler than core5_v0_controlled. It keeps colon-delimited fields and
relation structure, but removes JSON and rewrites technical words like relation,
schema, graph, proto, concept, and binding.
```

Decision:

```text
Use core5_v0_childlang as the first nanochat shared-tokenizer training input.
```

Detailed report:

```text
docs/core5-v0-child-language.md
```

## 2026-04-28: Core5 V0 Controlled Vocabulary

Experiment ID:

```text
core5_v0_controlled
```

Purpose:

```text
Create a controlled-vocabulary version of core5_v0 before nanochat from-scratch
training.
```

Data:

```text
train: 2428
dev: 296
curriculum_test: 331
held-out cases: 108
```

Variants:

```text
controlled_plain_text
controlled_relation_scaffolded
controlled_relation_first_then_text
```

Vocabulary result, train split:

```text
controlled_plain_text:                1367 alpha words, 1832 raw tokens
controlled_relation_scaffolded:       1369 alpha words, 1838 raw tokens
controlled_relation_first_then_text:  1370 alpha words, 1840 raw tokens
```

Interpretation:

```text
The controlled variants remove most JSON/schema token noise and reduce the
surface vocabulary while preserving concept words needed for the word-to-relation
test.
```

Decision:

```text
Use core5_v0_controlled, not raw core5_v0, as the first nanochat shared-tokenizer
training input.
```

Detailed report:

```text
docs/core5-v0-controlled-vocabulary.md
```

## 2026-04-28: Core5 V0 Curriculum Variants

Experiment ID:

```text
core5_v0
```

Purpose:

```text
Generate the first model-ready five-domain curriculum with matched plain text,
relation-scaffolded, and relation-first representations.
```

Data:

```text
domains: 5
total examples: 3055
train: 2428
dev: 296
curriculum_test: 331
held-out cases: 108
```

Variants:

```text
plain_text
relation_scaffolded
relation_first_then_text
```

Validation:

```text
generator compiled
all three variants passed training dry-run
JSON manifests validated
held-out evaluation validated with expected merged-source warning
source examples match across variants for every split
```

Interpretation:

```text
The core5 data surface is now ready for shared-tokenizer nanochat conversion.
This is a curriculum-generation result, not a model-quality result.
```

Decision:

```text
Next step is shared-tokenizer conversion for nanochat, then Level 1 local sanity.
```

Detailed report:

```text
docs/core5-v0-curriculum-variants.md
```

## 2026-04-27: nanochat Level 0 Local Smoke

Experiment ID:

```text
nanochat_level0_local_smoke
```

Purpose:

```text
Verify that project JSONL data can be converted into nanochat pretraining
Parquet shards and that nanochat can train a tiny from-scratch model locally on
Mac/MPS.
```

Data:

```text
plain base dir:    /tmp/adi_nanochat_plain_smoke
relation base dir: /tmp/adi_nanochat_relation_smoke
train docs:        11800 per variant
val docs:          280 per variant
source split:      physical_v0 train/dev
```

Model/run:

```text
nanochat repo: /tmp/nanochat-read
device:        mps
depth:         2
max_seq_len:   256
iterations:    20
tokens:        40960 per run
```

Plain-text smoke result:

```text
model tag:              adi_plain_d2_smoke20
parameters:             983094
initial validation bpb: 2.379064
final validation bpb:   1.992483
checkpoint:             /tmp/adi_nanochat_plain_smoke/base_checkpoints/adi_plain_d2_smoke20
```

Relation-scaffolded smoke result:

```text
model tag:              adi_relation_d2_smoke20
parameters:             1179702
initial validation bpb: 2.412748
final validation bpb:   2.027082
checkpoint:             /tmp/adi_nanochat_relation_smoke/base_checkpoints/adi_relation_d2_smoke20
```

Interpretation:

```text
The nanochat path works locally: Parquet conversion, tokenizer training,
base pretraining, validation, and checkpointing all completed for both variants.
This is not evidence for the theory yet.
```

Caveat:

```text
The two smoke runs used separately trained tokenizers. That changed the
effective vocabulary sizes and parameter counts, so these numbers must not be
used as a plain-vs-relation comparison.
```

Decision:

```text
Next step is to add a shared-tokenizer procedure and a relation_first_then_text
dataset variant before any serious comparison or GPU spend.
```

Detailed report:

```text
docs/tiny-from-scratch-relation-experiment.md
```

## 2026-04-26: Physical V0.3 Binary Candidate Scoring

Experiment ID:

```text
physical_v0_3
```

Purpose:

```text
Test whether independent YES/NO candidate judgments reduce the over-selection
seen in physical_v0_2.
```

Data:

```text
train: 2376
dev: 283
curriculum_test: 343
held-out binary prompts: 794
```

Model/run:

```text
model: HuggingFaceTB/SmolLM2-135M
run: binary_candidate_scoring_s300
max_seq_length: 512
max_steps: 300
epoch: 1.01
```

Training result:

```text
train loss: 0.218
dev loss:   0.101
```

Held-out result, task-matched greedy generation:

```text
case pass:          0.000
family precision:   0.750
family recall:      0.066
anchor precision:   0.400
anchor recall:      0.038
gap precision:      0.287
gap recall:         0.868
```

Held-out diagnostic, YES/NO logit top-k:

```text
case pass:          0.000
family precision:   0.407
family recall:      0.407
anchor precision:   0.288
anchor recall:      0.288
gap precision:      0.289
gap recall:         0.289
```

Interpretation:

```text
Binary scoring fixed the over-selection shape only by creating an
under-selection/calibration problem. The logits contain weak relation-ranking
signal, but held-out graph transfer is still not good enough.
```

Decision:

```text
Do not expand domains yet. Next step should add held-out-style transfer bridge
prompts and/or pairwise/listwise ranking, then evaluate ranking before returning
to set selection.
```

Detailed report:

```text
docs/physical-v0-3-binary-candidate-scoring.md
```

## 2026-04-26: Physical V0.2 Closed-Vocabulary Candidate Selection

Experiment ID:

```text
physical_v0_2
```

Purpose:

```text
Test whether held-out graph transfer improves when the valid relation IDs and
graph anchors are shown as candidates instead of generated from memory.
```

Data:

```text
train: 1041
dev: 123
curriculum_test: 142
held-out: 33
```

Model/run:

```text
model: HuggingFaceTB/SmolLM2-135M
run: candidate_selection_options_outputmarker_512_s160
max_seq_length: 512
max_steps: 160
```

Training result:

```text
train loss: 0.610
dev loss:   0.337
```

Held-out result:

```text
case pass:          0.000
family precision:   0.247
family recall:      0.407
anchor precision:   0.168
anchor recall:      0.596
gap precision:      0.200
gap recall:         0.026
non-candidate IDs:  0
```

Interpretation:

```text
The closed-vocabulary setup solved the invented-ID problem, but not exact
selection. The model often over-selected candidates, especially all anchor
options, so recall improved while precision stayed poor and exact case pass
remained zero.
```

Decision:

```text
The direction is useful, but the next run should make selection less generative:
separate relation-family and anchor prompts, include expected count or binary
yes/no candidate scoring, and train/evaluate a full stable run only after the
selection head stops over-selecting.
```

Detailed report:

```text
docs/physical-v0-2-candidate-selection.md
```

## 2026-04-26: Physical V0.1 Held-Out Comparison

Experiment ID:

```text
physical_v0_1
```

Purpose:

```text
Test whether adding bridge tasks improves held-out graph-transfer performance.
```

Change from previous experiment:

```text
Added bridge tasks:
- node_id_from_paraphrase
- relation_family_from_prompt
- graph_anchor_from_prompt
- explanation_with_relations
```

Model:

```text
HuggingFaceTB/SmolLM2-135M
```

Data:

```text
train: 488
dev: 58
curriculum_test: 66
held-out: 33
```

Result:

```text
variant                final dev loss  heldout pass  relation recall  anchor recall
plain_text             1.816           0.000         0.011            0.000
flat_triples           1.101           0.000         0.022            0.000
relation_scaffolded    0.491           0.000         0.000            0.000
```

Interpretation:

```text
The bridge curriculum improved local fit, but held-out graph transfer still
failed. The model produced plausible labels, invented schema IDs, or JSON-like
objects instead of recovering fixed graph vocabulary.
```

Decision:

```text
Do not expand domains.
Move to closed-vocabulary candidate selection in physical_v0_2.
```

Detailed report:

```text
docs/physical-v0-1-heldout-comparison.md
```

## 2026-04-26: Physical V0.1 Bridge Curriculum Generation

Experiment ID:

```text
physical_v0_1
```

Purpose:

```text
Create a bridge curriculum after physical_v0 showed that relation scaffolding
fit train/dev but did not transfer to held-out graph recovery.
```

Generated tasks:

```text
node_id_from_paraphrase:     298
graph_anchor_from_prompt:    128
relation_family_from_prompt:  24
explanation_with_relations:   14
```

Data:

```text
base examples:   148
bridge examples: 464
total examples:  612
```

Validation:

```text
OK: data/developmental_graph/curricula/seed_everyday_physical_world_physical_v0_1_curriculum.jsonl
```

Decision:

```text
Train the same three variants as physical_v0 and rerun held-out scoring.
```

Detailed report:

```text
docs/physical-v0-1-bridge-curriculum.md
```

## 2026-04-26: Physical V0 Held-Out Comparison

Experiment ID:

```text
physical_v0
```

Purpose:

```text
Test the first complete physical-world vertical slice.
```

Model:

```text
HuggingFaceTB/SmolLM2-135M
```

Data:

```text
train: 118
dev: 14
curriculum_test: 16
held-out: 33
```

Result:

```text
variant                final dev loss  heldout pass  relation recall  anchor recall
plain_text             3.667           0.000         0.011            0.000
flat_triples           2.282           0.000         0.000            0.000
relation_scaffolded    0.808           0.000         0.011            0.000
```

Interpretation:

```text
Relation scaffolding fit train/dev best, but did not improve held-out graph
transfer.
```

Decision:

```text
Do not expand domains.
Add bridge curriculum to connect natural prompts to graph relation vocabulary.
```

Detailed report:

```text
docs/physical-v0-heldout-comparison.md
```

## 2026-04-26: Physical V0 Overfit Sanity Check

Experiment ID:

```text
physical_v0_overfit_relation_scaffolded
```

Purpose:

```text
Verify that the local training pipeline, dependencies, data formatting,
checkpointing, and generation path work.
```

Setup:

```text
variant: relation_scaffolded
overfit_limit: 8
max_steps: 30
```

Result:

```text
train loss step 5:  1.712
train loss step 30: 1.007
eval loss step 1:   1.864
eval loss step 30:  1.048
```

Interpretation:

```text
Infrastructure sanity passed. This was not a model-quality result.
```

Decision:

```text
Proceed to full physical_v0 three-way comparison.
```

Detailed report:

```text
docs/physical-v0-overfit-sanity.md
```
