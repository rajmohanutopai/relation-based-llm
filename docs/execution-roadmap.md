# Execution Roadmap

This roadmap exists to keep the project from spreading sideways into every
knowledge domain before the core claim is tested.

The project should move as an evidence ladder:

```text
theory -> graph -> curriculum -> held-out evaluation -> tiny model comparison
       -> failure analysis -> graph/curriculum revision -> next domain
```

The central rule is:

```text
Do not expand broadly until one narrow vertical slice has measurable signal.
```

## Current Position

Already present:

- Canonical theory notes.
- Six-month child seed graph.
- Raw 200 six-month child encounter inventory.
- Relation audits for first-core and maybe child encounters.
- Everyday physical-world domain map.
- Raw 200 everyday physical-world situation inventory.
- Relation audit for the first 50 physical situations.
- Parseable physical-world seed graph.
- Held-out physical-world evaluation set from maybe rows.
- Deterministic curriculum generator.
- First generated physical-world curriculum.

Current physical-world curriculum:

```text
relation_completion: 114
state_action_effect: 10
counterfactual_contrast: 10
explanation_path: 14
total: 148
```

The immediate problem is not lack of domains. The immediate problem is proving
that this structure gives a smaller model useful transfer.

## Phase 0: Repository And Data Discipline

Goal: make every artifact reproducible and parseable.

Do first:

1. Keep `.env`, local virtualenvs, downloaded PDFs, and machine-specific files
   out of git.
2. Commit graph, curriculum, evaluation, and docs in stable chunks.
3. Keep raw inventories separate from relation audits.
4. Keep generated curriculum separate from hand-authored graph data.
5. Add validators before adding more generated data.

Outputs:

```text
data/developmental_graph/schemas/
data/developmental_graph/seeds/
data/developmental_graph/curricula/
data/developmental_graph/evaluations/
scripts/validate_*.py
scripts/generate_*.py
```

Stop condition:

```text
Any graph or generated file can be regenerated or validated from command line.
```

## Phase 1: Finish The First Vertical Slice

Goal: test one complete pipeline before expanding into more domains.

Use the physical-world seed because it is concrete, easy to evaluate, and less
ambiguous than social or historical concepts.

Order:

1. Freeze the current physical-world seed as experiment version `physical_v0`.
2. Freeze the current generated curriculum as `physical_v0_train`.
3. Freeze the held-out evaluation as `physical_v0_heldout`.
4. Build an evaluation runner.
5. Build model-ready train/dev/test splits.
6. Create a plain-text baseline dataset from the same underlying examples.
7. Create a flat-triple baseline dataset.
8. Train or fine-tune the same tiny transformer on each dataset.
9. Compare on the held-out evaluation set.
10. Write a failure report.

Required comparison:

```text
same model + plain text
same model + flat triples
same model + relation-scaffolded curriculum
```

Measure:

```text
relation family recall
graph anchor recall
counterfactual correctness
explanation path correctness
transfer to new objects
gap detection accuracy
```

Decision gate:

```text
If relation scaffolding does not beat plain text or flat triples on at least one
important held-out measure, do not expand domains yet. Revise the graph format,
curriculum tasks, or evaluation method first.
```

## Phase 2: Add Data Contracts

Goal: prevent silent drift as the project grows.

Add schemas or validators for:

1. Curriculum JSONL examples.
2. Held-out evaluation files.
3. Experiment manifests.
4. Model output records.
5. Evaluation result reports.

Each generated example should have:

```text
id
source graph
task type
input
target
text target
metadata
```

Each evaluation case should have:

```text
id
case type
prompt
expected answer
expected relation families
graph anchors
gap indicators, if any
scoring rubric
```

Decision gate:

```text
No new domain gets generated curriculum until its raw inventory, relation audit,
seed graph, curriculum, and evaluation all validate.
```

## Phase 3: Integrate Root Child Graph With Physical World

Goal: make sure the six-month child graph and the physical-world graph share the
same relation grammar.

Order:

1. Map overlapping root relations:
   `same/different`, `before/after`, `more/less`, `touching`, `moves/stops`,
   `inside/outside`, `support`, `threshold`, `state change`.
2. Identify duplicate or inconsistent relation names.
3. Decide which relations are canonical root relations and which are
   domain-specific specializations.
4. Add crosswalk documentation.
5. Only then generate mixed child-plus-physical curriculum examples.

Important rule:

```text
The child graph is not the only training source. It is the root grammar of
meaning. Other domains grow from the same grammar.
```

Decision gate:

```text
A model should be able to answer simple physical questions using relation
families that can be traced back to root relations.
```

## Phase 4: Social World Domain

Goal: add people, agency, attention, roles, cooperation, conflict, trust, and
group behavior.

Do this before history, law, economics, and politics because those depend on
social relations.

Raw inventory should include:

```text
caregiver attention
imitation
sharing
turn-taking
helping
refusal
approval
disapproval
rule following
rule breaking
ownership
fairness
status
promise
trust
lying
group belonging
exclusion
cooperation
conflict
```

Expected relation families:

```text
self/other
agent/action/effect
attention/absence
intention/outcome
help/harm
approval/disapproval
rule/compliance/consequence
role/permission/expectation
trust/prediction/violation
group/member/non-member
```

Outputs:

```text
docs/social-world-200-situations.md
docs/social-world-top50-relation-audit.md
data/developmental_graph/seeds/social_world.json
data/developmental_graph/evaluations/social_world_heldout.json
data/developmental_graph/curricula/seed_social_world_curriculum.jsonl
```

Decision gate:

```text
The model should transfer from simple social relations to unseen cases such as
promise breaking, exclusion, or unfair sharing without memorizing definitions.
```

## Phase 5: Math And Abstraction Domain

Goal: test whether abstractions can be built from relation patterns.

Do this before geography/history expansion because it tests the core claim that
higher abstractions are compressed relation structures.

Start with:

```text
same/different
grouping
one/many
more/less/equal
order
before/after sequence
matching
mapping
containment
part/whole
repetition
pattern
invariance
composition
if/then
negation
```

Do not start with formal algebra. Start with the relation roots that later make
algebra meaningful.

Outputs:

```text
docs/math-abstraction-200-situations.md
docs/math-abstraction-top50-relation-audit.md
data/developmental_graph/seeds/math_abstraction.json
data/developmental_graph/evaluations/math_abstraction_heldout.json
data/developmental_graph/curricula/seed_math_abstraction_curriculum.jsonl
```

Decision gate:

```text
The model should explain a new abstraction through relation paths, not only
produce the word's memorized definition.
```

## Phase 6: Body, Health, And Medicine

Goal: connect bodily state, discomfort, function, failure, cause, symptom,
treatment, risk, and recovery.

This comes after physical and social basics because health reasoning combines
body mechanics, sensation, social care, and causal prediction.

Core relation families:

```text
body part/function
comfort/discomfort
pain/location
symptom/cause
injury/repair
contamination/illness
treatment/effect
risk/probability
recovery/time
normal/abnormal range
```

Decision gate:

```text
The model should distinguish symptom, cause, treatment, and risk rather than
collapsing them into loose medical association.
```

## Phase 7: Language And Reading

Goal: attach words, symbols, grammar, and reading to already-built relation
structures.

This should not be treated as the first source of meaning.

Order:

1. Sound pattern to word handle.
2. Written symbol to sound or word handle.
3. Word handle to relation cluster.
4. Phrase to relation composition.
5. Sentence to event or state relation.
6. Story to temporal and causal relation chain.

Core relation families:

```text
symbol/meaning
word/object
word/action
modifier/property
subject/action/object
before/after narrative
cause/effect narrative
metaphor as relation transfer
```

Decision gate:

```text
Language examples should improve access to relation structures, not replace
those structures with word co-occurrence alone.
```

## Phase 8: Geography

Goal: build place knowledge from physical space plus human settlement.

Do geography after physical, social, and basic abstraction.

Core relation families:

```text
location
distance
direction
boundary
inside/outside
near/far
terrain
water path
climate
resource
settlement
route
trade
region/category
scale: room/city/state/country/continent/world
```

A place should be represented as:

```text
place =
  location + boundary + terrain + climate + resources + people + routes
```

Outputs:

```text
docs/geography-200-situations.md
docs/geography-top50-relation-audit.md
data/developmental_graph/seeds/geography.json
data/developmental_graph/evaluations/geography_heldout.json
```

Decision gate:

```text
The model should infer place relations, not merely recall labels. Example:
river delta, coastal city, desert settlement, mountain pass, monsoon region.
```

## Phase 9: History

Goal: build historical understanding from time, agency, group behavior,
resources, power, conflict, institutions, and evidence.

Do history after social world and geography. History is not just dates.

A historical event should be represented as:

```text
historical event =
  agents + groups + motives + resources + constraints + actions
  + consequences + memory/evidence
```

Core relation families:

```text
before/after
period/change
cause/consequence
agent/group action
resource pressure
power/control
conflict/cooperation
law/institution
evidence/source
interpretation/bias
continuity/discontinuity
```

Decision gate:

```text
The model should explain why an event happened and what changed afterward, not
only associate names with dates.
```

## Phase 10: Economics, Law, Politics, And Society

Goal: build institutional concepts from social relations, scarcity, incentives,
authority, rules, enforcement, and group coordination.

Core relation families:

```text
need/scarcity
ownership/exchange
value/trust
work/reward
incentive/behavior
rule/authority
violation/punishment
right/duty
representation/decision
institution/stability
```

These domains should wait until social world, abstraction, geography, and
history have usable foundations.

## Phase 11: Science Formalization

Goal: connect everyday physical concepts to formal scientific concepts.

Do not start here. Formal physics, chemistry, and biology should grow from
grounded physical, body, math, and abstraction graphs.

Examples:

```text
push/slide/resistance -> force/friction
fall/impact/rebound -> gravity/energy/momentum
mixing/dissolving/separating -> solubility/solution/suspension
heating/cooling/state change -> thermodynamics/phase transition
body function/failure -> physiology/pathology
```

Decision gate:

```text
The model should bridge from everyday explanation to formal explanation while
preserving the relation path.
```

## Standard Domain Workflow

Every new domain should use the same workflow:

1. Create a raw 200-situation inventory.
2. Add status fields: `yes`, `maybe`, `no`.
3. Prioritize the first `yes` set, usually around 30-50 items.
4. Create a relation audit for the `yes` set.
5. Create held-out evaluation cases from the `maybe` set.
6. Build a compact parseable seed graph.
7. Validate the seed graph.
8. Generate curriculum.
9. Run held-out evaluation.
10. Compare baseline versus relation-scaffolded model.
11. Write failure analysis.
12. Only then expand or revise the domain.

The raw inventory is observation data. The relation audit is interpretation.
The seed graph is machine-parseable structure. The curriculum is generated
training data. The held-out set is evidence.

## Immediate Next Ten Tasks

The next work should be done in this order:

1. Commit or otherwise checkpoint the current physical-world artifacts. Done in
   commit `c82eeab`.
2. Add a validator for held-out evaluation JSON. Done.
3. Add a validator for curriculum JSONL. Done.
4. Build the held-out evaluation runner. Done.
5. Add model-ready train/dev/test split generation. Done.
6. Create three datasets from the same examples: plain text, flat triples, and
   relation-scaffolded. Done.
7. Pick one tiny transformer baseline and freeze the training command. Done.
8. Run a tiny overfit sanity check on a few examples. Done.
9. Run the first held-out comparison.
10. Write `docs/physical-world-v0-experiment-report.md`.

Only after task 10 should the project expand into social world or math.

## What To Avoid For Now

Do not build a custom model architecture yet.

Do not create 200-item inventories for every school subject immediately.

Do not use ConceptNet or DRAGON as the main representation before the first
controlled experiment. They can be comparison sources later.

Do not turn the six-month child graph into the only learning source. It is the
root relation grammar, not the whole world.

Do not mix raw observations with derived relation labels in the same artifact.

Do not optimize happiness directly as a reward before safety and shortcut
failure modes are modeled.

## Success Definition

The roadmap is working if each domain passes through this chain:

```text
raw situations
-> relation audit
-> seed graph
-> generated curriculum
-> held-out evaluation
-> model comparison
-> failure-driven revision
```

The project itself is working if relation scaffolding gives a measurable sample
efficiency or transfer advantage over plain text and flat triples using the same
small model and similar compute.
