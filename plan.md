# Adi LLM Plan

Status: working plan. This file is meant to change as the theory and experiments
become clearer.

## Project Aim

Build and test a relation-first small language model approach.

The central hypothesis:

```text
Small models can learn more efficiently if training makes relational structure
explicit: primitive input relations first, object/event relations next, social
and abstract relations later, then language as labels over those structures.
```

The transformer remains the learner. The relation graph is the supporting hand:
curriculum, auxiliary supervision, and evaluation.

## Core Theory

The current working theory:

```text
information = relation
concept = weighted cluster of relations
learning = relation formation, strengthening, weakening, and pruning
abstraction = compression of repeated relation patterns
context = partial/sub-threshold activation of relation networks
language = handles into relation clusters
```

The model should not treat words as the first source of meaning. Words should
bind to structures that already have relational content.

## Affect Theory

Primitive valence exists below comfort and happiness.

```text
primitive valence:
  pain / relief
  discomfort / comfort
  instability / stability
  approach / avoid
```

Comfort and happiness are related but not identical:

```text
comfort = body-state relief or stabilization
happiness = positive relation activation or useful new relation gain
sadness = valued relation loss or blocked expected positive activation
```

Current happiness model:

```text
happiness_delta =
  positive_relation_activation
  + useful_connection_gain * (1 - current_relation_strength)
  - connection_loss
  - harmful_shortcut_penalty
```

This captures three important cases:

- Familiar caregiver tone can activate existing happiness-linked relations.
- Discovery/play/insight can create happiness by forming new useful relations.
- Repeated activation saturates, so the same reward gives less new happiness.

Hard drug use and similar failures are modeled as direct positive activation
without useful relation growth. That is a shortcut through the affect system,
not genuine long-horizon relational growth.

## Current Artifacts

- `docs/information-cognition-abstraction-theory.md`
  Stores the core theory from the novel chapter on mind, information,
  cognition, abstraction, beauty, grief, and happiness.

- `docs/developmental-relation-graph.md`
  Defines the layered graph structure and the intended transformer-training
  role.

- `docs/execution-roadmap.md`
  Detailed execution order for the project: first physical-world vertical slice,
  then social world and math, then composite domains like geography and history.

- `docs/core-relation-curriculum-plan.md`
  Defines the first serious five-domain nanochat curriculum: six-month root
  world, everyday physical world, simple social world, math/abstraction roots,
  and language binding. It fixes the matched representation variants:
  `plain_text`, `relation_scaffolded`, and `relation_first_then_text`.

- `data/developmental_graph/core_curriculum_plan.json`
  Parseable manifest for the five-domain curriculum. It records which domains
  are ready, which files are missing, and which gates must pass before serious
  nanochat training.

- `data/developmental_graph/experiments/core5_v0/`
  First generated five-domain model-ready curriculum. It contains 3055 source
  examples across the 6mo root world, everyday physical world, social world,
  math/abstraction roots, and language binding. It renders matched
  `plain_text`, `relation_scaffolded`, and `relation_first_then_text` variants
  with 2428 train, 296 dev, and 331 curriculum-test examples per variant.

- `docs/core5-v0-curriculum-variants.md`
  Report for the core5_v0 curriculum-generation milestone, including counts,
  commands, validation, and the next shared-tokenizer step.

- `data/developmental_graph/experiments/core5_v0_controlled/`
  Controlled-vocabulary rendering of the same core5 examples. It keeps the same
  splits but uses lower-case fixed templates and compact relation packets.
  Current train vocabulary is 1367-1370 alpha words depending on variant.

- `docs/core5-v0-controlled-vocabulary.md`
  Report for the controlled-vocabulary dataset, including vocabulary counts and
  validation commands.

- `data/developmental_graph/experiments/core5_v0_childlang/`
  Child-language rendering of the same core5 examples. It keeps colon-delimited
  fields, removes JSON, and rewrites technical words where possible. Current
  train vocabulary is 1342-1343 alpha words depending on variant.

- `docs/core5-v0-child-language.md`
  Report for the child-language dataset. It remains a core5 candidate after the
  smaller procedural/foundation smoke tests.

- `data/developmental_graph/experiments/core5_v0_foundation/`
  Staged foundation ladder for introducing high relation-load handles only after
  supporting facts. It has F0 simple facts, F1 handle introduction, F2 handle
  questions, and F3 later-name attachment. Current train vocabulary is 92-93
  alpha words depending on variant.

- `docs/core5-v0-foundation-ladder.md`
  Report for the foundation ladder. This is now the recommended prelude before
  child-language nanochat training.

- `data/developmental_graph/experiments/procedural_foundation_v0/`
  First procedural relation-world dataset. It generates touch/reach/move
  outcomes from object, height, distance, action, and support-surface state.
  Current count: 2994 train, 302 dev, 592 curriculum-test examples.

- `docs/procedural-foundation-v0.md`
  Report for the procedural generator and validation results.

- `data/developmental_graph/experiments/procedural_foundation_v1/`
  Coherent-scenario procedural dataset replacing the rough V0 generator. It has
  reach/touch, push/move, drop/fall, shake/sound, hide/see,
  container/open-closed, and hot/cold touch rule families. Current count: 542
  train, 66 dev, 81 curriculum-test examples.

- `docs/procedural-foundation-v1.md`
  Report for the coherent procedural generator. This is the quality base to
  expand before nanochat training.

- `data/developmental_graph/experiments/procedural_foundation_v2/`
  Expanded coherent procedural dataset. It keeps V1's scenario grammars, adds
  derived question views, and adds support/edge/fall, same/different,
  more/less, path open/closed, caregiver comfort, and word-name binding rule
  families. Current count: 2477 train, 302 dev, 378 curriculum-test examples.

- `docs/procedural-foundation-v2.md`
  Report for the expanded procedural foundation generator. This is the current
  historical step before V3.

- `data/developmental_graph/experiments/procedural_foundation_v3/`
  Larger baby + physical + simple-social procedural dataset. It expands the
  base world to 208 entities before generating rows. Current count: 4536 train,
  553 dev, 623 curriculum-test examples.

- `docs/procedural-foundation-v3.md`
  Report for the larger base-world procedural generator. This is now the
  current active procedural arm for the local nanochat smoke test.

- `data/developmental_graph/experiments/tinystories_v0/`
  Normal simple-text baseline streamed from `roneneldan/TinyStories`. It is
  matched to the V3 relation variants by approximate word budget: 270421 train
  words, 33008 dev words, and 36695 curriculum-test words.

- `docs/tinystories-v0-baseline.md`
  Report for the TinyStories baseline. This makes the next nanochat test a
  four-arm comparison: normal simple text, relation-designed plain text,
  relation-scaffolded text, and relation-first text.

- `docs/seed-agent-6mo-indian-child.md`
  Human-readable seed graph for a 6-month-old boy child in an Indian context.

- `docs/6mo-child-200-encounters.md`
  Raw, non-annotated inventory of 200 encounter families for a 6-month-old
  child. This should stay separate from later relation annotations.

- `docs/physical-world-domain-map.md`
  Broad scaffold for the full physical-world domain: everyday grounding,
  material behavior, mechanics, flow, heat, waves, tools, environment, scale,
  and scientific formalization.

- `docs/everyday-physical-world-200-situations.md`
  Raw, non-annotated inventory of 200 everyday physical-world situation
  families. This starts the grounded entry layer without adding relation
  interpretation yet.

- `docs/social-world-200-situations.md`
  Raw, non-annotated inventory of 200 simple social-world situation families.
  This starts the social-domain entry layer without adding relation
  interpretation yet.

- `docs/social-world-firstset-relation-audit.md`
  Derived relation audit for the first-set simple social situations. It identifies
  reusable social relation families such as presence/absence, social signals,
  turn-taking, joint attention, permission, sharing, fairness, imitation,
  inclusion, help, promise, trust, rules, and comfort response.

- `docs/math-abstraction-200-situations.md`
  Raw, non-annotated inventory of 200 math-abstraction situation families,
  with operational prioritisation complete. This starts the abstraction-domain
  entry layer without adding relation interpretation yet.

- `docs/math-abstraction-firstset-relation-audit.md`
  Derived relation audit for the 66 first-set math-abstraction situations. It
  identifies reusable relation families such as same/different, count,
  comparison, one-to-one assignment, order, grouping, containment, measurement,
  pattern, symbol mapping, and simple logical filters.

- `data/developmental_graph/seeds/math_abstraction.json`
  Parseable math-abstraction seed graph with compact relation motifs from the
  first-set audit. Current count: 109 nodes, 81 relations, 9 micro-experiences,
  and 11 evaluation questions.

- `data/developmental_graph/evaluations/math_abstraction_heldout.json`
  Parseable held-out evaluation set for testing math-abstraction transfer and
  identifying abstraction relation gaps. Current count: 27 cases, 83 graph
  anchors, and 61 gap indicators.

- `docs/language-binding-400-situations.md`
  Prioritised raw inventory of 400 language-binding situation families.
  Current first-set counts: 179 `yes`, 78 `maybe`, 143 `no`. This starts the
  language-binding entry layer without adding relation interpretation yet.

- `docs/language-binding-firstset-relation-audit.md`
  Derived relation audit for the 179 first-set language-binding situations. It
  identifies reusable binding families such as word handles, object labels,
  property labels, quantity words, sentence-event binding, questions, negation,
  tense, polysemy, tone, multilingual equivalence, and story/discourse binding.

- `data/developmental_graph/seeds/language_binding.json`
  Parseable language-binding seed graph with compact relation motifs from the
  first-set audit. Current count: 121 nodes, 230 relations, 12
  micro-experiences, and 10 evaluation questions.

- `data/developmental_graph/evaluations/language_binding_heldout.json`
  Parseable held-out evaluation set for testing language-binding transfer and
  identifying language relation gaps. Current count: 23 cases, 57 graph anchors,
  and 10 gap indicators.

- `docs/everyday-physical-world-top50-relation-audit.md`
  Derived relation audit for the 50 everyday physical situations marked as the
  first physical set. This identifies compact physical relation families rather
  than one graph node per situation.

- `docs/everyday-physical-world-heldout-evaluation.md`
  Human-readable summary of held-out physical evaluation cases from the `maybe`
  rows.

- `docs/curriculum-generation.md`
  Explains how graph seeds become supervised JSONL training examples.

- `docs/physical-v0-training.md`
  Freezes the first tiny transformer baseline, dependency install command,
  training commands, and overfit sanity-check command.

- `docs/physical-v0-overfit-sanity.md`
  Records the first local relation-scaffolded overfit sanity run. The run
  completed, loss decreased, and artifacts loaded, but it is not a model-quality
  result.

- `docs/physical-v0-heldout-comparison.md`
  Records the first full physical-v0 comparison across plain text, flat triples,
  and relation-scaffolded variants. The relation-scaffolded variant fit train/dev
  best, but no variant passed held-out graph-transfer scoring.

- `docs/physical-v0-1-bridge-curriculum.md`
  Records the `physical_v0_1` bridge curriculum added after the first failure.
  It teaches natural-language prompts to recover graph node IDs, relation
  families, anchors, and explanations with explicit relation names.

- `docs/physical-v0-1-heldout-comparison.md`
  Records the second comparison. The bridge curriculum improved train/dev loss,
  but free-form held-out generation still invented IDs and failed graph-transfer
  scoring.

- `docs/physical-experiment-report.md`
  Single running report for the physical-world experiment sequence. It records
  the `physical_v0` and `physical_v0_1` goals, results, decisions, and current
  next step.

- `docs/experiment-log.md`
  Concise reverse-chronological experiment ledger. Each entry records the date,
  experiment ID, purpose, data, result, interpretation, decision, and detailed
  report link.

- `docs/6mo-child-top44-relation-audit.md`
  Derived relation audit for the 44 encounters currently marked as first-core
  candidates. This is where relation interpretation belongs, not in the raw
  encounter inventory.

- `docs/6mo-child-maybe42-relation-audit.md`
  Derived relation audit for the 42 encounters marked as maybe candidates.
  This checks the second-priority encounter layer against the seed graph.

- `data/developmental_graph/seeds/agent_6mo_indian_child.json`
  Parseable seed graph.

- `data/developmental_graph/seeds/everyday_physical_world.json`
  Parseable physical-domain seed graph with compact external-world relation
  motifs from the everyday physical audit.

- `data/developmental_graph/seeds/social_world.json`
  Parseable social-domain seed graph with compact social relation motifs from
  the prioritised social first-set audit. Current count: 109 nodes, 74
  relations, 14 micro-experiences, and 10 evaluation questions.

- `data/developmental_graph/evaluations/social_world_heldout.json`
  Parseable held-out evaluation set for testing social transfer and identifying
  missing social relation families. Current count: 25 cases, 69 graph anchors,
  and 47 gap indicators.

- `data/developmental_graph/evaluations/everyday_physical_world_heldout.json`
  Parseable held-out evaluation set for testing physical transfer and identifying
  physical relation gaps.

- `data/developmental_graph/curricula/seed_everyday_physical_world_curriculum.jsonl`
  Generated supervised curriculum from the physical seed graph.

- `data/developmental_graph/curricula/seed_everyday_physical_world_curriculum.manifest.json`
  Manifest for the physical curriculum. Current count: 148 examples.

- `data/developmental_graph/experiments/physical_v0/`
  First model-ready physical-world experiment split. It contains 118 training
  examples, 14 dev examples, 16 curriculum-test examples, 33 held-out prompts,
  and a manifest.

- `data/developmental_graph/experiments/physical_v0/datasets/`
  Matched dataset variants for the first comparison: plain text, flat triples,
  and relation-scaffolded. Each variant has the same 118 train, 14 dev, and 16
  curriculum-test examples.

- `data/developmental_graph/experiments/physical_v0/training_config.json`
  Frozen baseline config using `HuggingFaceTB/SmolLM2-135M` with identical
  commands for the three dataset variants.

- `data/developmental_graph/experiments/physical_v0_1/`
  Bridge-curriculum experiment split with 488 train, 58 dev, 66 curriculum-test,
  and the same 33 held-out prompts as `physical_v0`.

- `data/developmental_graph/experiments/physical_v0_1/training_config.json`
  Frozen config for rerunning the same tiny transformer comparison after adding
  bridge tasks.

- `data/developmental_graph/schemas/graph.schema.json`
  JSON schema for graph data.

- `scripts/validate_developmental_graph.py`
  Dependency-free graph validator.

- `scripts/validate_developmental_evaluation.py`
  Dependency-free held-out evaluation validator. It checks case structure,
  expected relation families, graph anchors, and gap indicators.

- `scripts/validate_developmental_curriculum.py`
  Dependency-free generated curriculum validator. It checks JSONL structure,
  manifest counts, task contracts, and graph references.

- `scripts/generate_developmental_curriculum.py`
  Deterministic curriculum generator for relation completion, event trace,
  counterfactual contrast, and explanation-path examples.

- `scripts/generate_developmental_bridge_curriculum.py`
  Deterministic bridge generator for prompt-to-graph transfer tasks. It can
  prepend an existing base curriculum and writes the combined `physical_v0_1`
  curriculum.

- `scripts/run_heldout_evaluation.py`
  First held-out evaluation runner. It scores model-output JSONL against
  expected relation families, graph anchors, and gap indicators.

- `scripts/generate_heldout_outputs.py`
  Loads a trained causal-LM checkpoint, runs the shared held-out prompts, and
  writes model-output JSONL for the evaluator.

- `scripts/create_developmental_experiment_splits.py`
  Deterministic train/dev/curriculum-test split generator for generated
  curriculum files, with held-out prompt export.

- `scripts/create_developmental_dataset_variants.py`
  Generates matched plain-text, flat-triple, and relation-scaffolded dataset
  variants from an experiment split.

- `scripts/train_tiny_causal_lm.py`
  Minimal Hugging Face causal-LM fine-tuning script for one dataset variant.
  Supports `--dry-run` without training dependencies.

- `scripts/create_core5_curriculum_variants.py`
  Generates the five-domain `core5_v0` curriculum, merged held-out prompts,
  matched representation variants, manifests, and local training config.

- `scripts/create_core5_controlled_vocabulary_variants.py`
  Generates the controlled-vocabulary `core5_v0_controlled` variants for the
  first nanochat from-scratch training test.

- `scripts/create_core5_child_language_variants.py`
  Generates the simpler `core5_v0_childlang` variants with colon-delimited
  child-language fields and simple relation words.

- `scripts/create_core5_foundation_variants.py`
  Generates the staged `core5_v0_foundation` ladder where complex handles are
  introduced after support facts instead of used as primitives.

- `scripts/create_procedural_foundation_world.py`
  Generates procedural scenarios from simple relation rules, currently covering
  hand action, height, distance, touch, reach, feeling, and object movement.

- `scripts/create_procedural_foundation_world_v1.py`
  Generates coherent procedural scenarios from rule-family grammars. This is the
  preferred procedural generator over V0.

## Layer Structure

Current graph layers:

```text
Layer -1: input channels
Layer  0: relational invariants
Layer  1: sensorimotor schemas
Layer  2: property relations
Layer  3: object concepts
Layer  4: event and affordance concepts
Layer  5: self, agency, and other minds
Layer  6: social concepts
Layer  7: language binding
Layer  8: logical and mathematical abstractions
Layer  9: meta-abstractions
```

Important rule:

```text
Higher concepts are not primitives.
They must be built from lower relation structures.
```

Examples:

```text
status = attention + compliance + priority + approval + future access
laziness = capability + expected action + effort cost + avoidance + consequence
ethics = action + effect on others + social prediction + long-horizon stability
```

## Training Strategy

Start simple. Do not build a custom architecture first.

Initial model structure:

```text
tokens -> transformer -> outputs
```

The difference should be in the data and tasks:

```text
plain text
structured relation examples
state/action/effect examples
relation prediction
missing-edge prediction
counterfactual prediction
valence prediction
explanation/path prediction
```

The goal is to test whether relation scaffolding improves sample efficiency and
generalization.

## Example Training Forms

### State Action Effect

```text
STATE: baby holds rattle.
ACTION: baby shakes hand.
RESULT: sound repeats.
RELATION: hand_motion causes rattle_sound.
AFFECT: new useful connection increases happiness.
```

### Saturation

```text
STATE: same rattle sound repeats many times.
RESULT: sound becomes expected.
RELATION: novelty decreases.
AFFECT: happiness gain saturates unless something changes.
```

### Object Boundary

```text
OBJECT: ball
RELATIONS:
  roundness high
  rolling likely when pushed
  bounce possible on impact
  squishiness can vary

QUESTION:
  If squishiness becomes too high and stable roundness is lost, is it still
  strongly ball-like?

EXPECTED:
  No. It shifts toward sponge/slime because core ball relations weaken.
```

## Evaluation Principle

The theory has engineering value only if it produces measurable advantage.

Compare:

```text
same model size + plain text
same model size + flat triples
same model size + developmental relation curriculum
```

Measure:

```text
sample efficiency
held-out relation generalization
counterfactual reasoning
property boundary reasoning
cause-effect transfer
valence/saturation understanding
abstraction from examples
```

Useful early tests:

- object/property transfer: rattle, cloth, steel bowl, ball, cup
- cause-effect transfer: drop, shake, push, squeeze, hide/reappear
- valence transfer: comfort, startle, relief, novelty, saturation
- category boundary: ball versus sponge/slime, knife versus spoon/razor
- social precursor: caregiver tone, absence, attention, imitation

## Execution Order

The detailed sequencing lives in `docs/execution-roadmap.md`.

The short version:

```text
1. Finish the physical-world vertical slice.
2. Add validators for curriculum and held-out evaluation files.
3. Build the evaluation runner and train/dev/test split generator.
4. Compare plain text, flat triples, and relation-scaffolded curriculum.
5. Revise from failures before expanding domains.
6. Add social world.
7. Add math and abstraction.
8. Add body/health and language binding.
9. Add geography.
10. Add history.
11. Add economics, law, politics, and formal science later.
```

The project should not create 200-item inventories for every domain immediately.
Each domain should pass through the same pipeline:

```text
raw inventory -> relation audit -> seed graph -> curriculum -> held-out eval
-> model comparison -> failure-driven revision
```

## Milestones

### Milestone 1: Stabilize Theory and Graph

- Keep refining the canonical theory documents.
- Add missing fundamental relations when found.
- Keep the seed graph parseable and validated.
- Avoid adding adult abstractions as primitives.

Success condition:

```text
The graph can explain simple infant experiences without hidden adult concepts.
```

### Milestone 2: Generate Synthetic Curriculum

Create scripts that convert graph data into training examples:

```text
relation completion
state/action/effect
cause/effect/valence
counterfactual
explanation path
language binding
```

Success condition:

```text
Given one seed graph, we can generate thousands of controlled examples.
```

### Milestone 3: Tiny Model Experiment

Train or fine-tune a very small transformer on:

```text
baseline text examples
relation-scaffolded examples
mixed text + relation curriculum
```

Success condition:

```text
The relation-scaffolded model performs better on held-out relational tasks using
similar compute.
```

### Milestone 4: Expand Developmental Ages

Add staged seed graphs:

```text
1 month
6 months
1 year
2 years
5 years
```

Each age should add only relations that can plausibly be built from earlier
layers.

Success condition:

```text
Later concepts are traceable to earlier relation structures.
```

### Milestone 5: Abstraction and Mathematics

Test whether higher abstractions can be built from relation patterns:

```text
same/different -> grouping
more/less/equal -> quantity
repetition -> counting precursor
containment/path/order -> symbolic structure
relation composition -> logic
invariant pattern -> abstraction
```

Success condition:

```text
The model can explain abstract concepts through relation paths, not memorized
definitions alone.
```

## Open Questions

- What are the minimum primitive input channels?
- Are `positive_activation`, `connection_gain`, and `positive_saturation`
  sufficient for early happiness modeling?
- How should relation strength be updated during training?
- Should the model output relation IDs, natural language explanations, or both?
- How much synthetic curriculum is useful before it becomes brittle?
- When do we add retrieval or graph adapters, if ever?
- How do we prevent raw happiness optimization from becoming reward hacking?
- How do we test whether abstractions are truly relation-built?

## Design Guardrails

- Keep raw encounter data separate from derived relation annotations.
- Do not hand-build the whole mind.
- Do not treat ConceptNet-style triples as enough.
- Do not make adult concepts primitive.
- Do not maximize immediate happiness directly.
- Do not replace the transformer until data-side scaffolding is tested.
- Prefer small measurable experiments over broad ontology expansion.

## Long-Term Data Source Roadmap

The project should not depend on paid LLM generation for large datasets. Use
external structured sources as raw relation material, then map them into our
own developmental relation grammar.

Recommended order:

1. ConceptNet + WordNet first.
   - ConceptNet gives broad commonsense assertions but is noisy.
   - WordNet should clean and strengthen `is_a`, `part_of`, synonym, and alias
     relations.
   - Use both as source material, not as the final ontology.
   - Current 6mo implementation:
     `scripts/create_age_6mo_conceptnet_relation_dataset.py`,
     `scripts/create_age_6mo_wordnet_relation_dataset.py`, and
     `scripts/create_age_6mo_external_relation_dataset.py`.
   - Current combined output:
     `data/developmental_graph/experiments/age_6mo_external_relations_v1/`.
     This is a mapped source layer, not the full training curriculum.

2. Visual Genome after the lexical layer is stable.
   - Use it for object-property-spatial relations such as object on surface,
     person holding object, object near object, color, size, and scene context.
   - Current 6mo implementation:
     `scripts/create_age_6mo_visual_genome_relation_dataset.py`.
   - Current combined external output after adding Visual Genome:
     `data/developmental_graph/experiments/age_6mo_external_relations_v3/`.
     It has 582 deduplicated mapped edges covering 134 of the 500 seed
     concepts. Visual Genome rows are rendered as `can be` / `can have`
     evidence because they are image-instance observations, not permanent
     definitions.

3. Wordbank / MacArthur-Bates CDI for age staging.
   - Use it to guide which words/concepts enter at which developmental stage.
   - It is not primarily a relation dataset.
   - Current implementation:
     `scripts/create_wordbank_age_staging_audit.py`.
   - Current output:
     `data/developmental_graph/experiments/wordbank_age_staging_v1/`.
     It matched 148 of the 520 candidate 6mo seed concepts and produced an
     `early_unmatched_wordbank_items.csv` list for vocabulary/alias review.
   - Current candidate seed:
     `data/developmental_graph/seeds/age_6mo_root_world_wordbank_v1.json`.
     This keeps the original 500 concepts unchanged, adds 20 early CDI
     concepts, and adds aliases for early Wordbank forms.

4. ATOMIC / ATOMIC 2020 for social, affective, intent, and consequence
   relations.
   - Use after the physical/body/social root layer is stable.

5. GenericsKB, TupleKB, Quasimodo, and WebChild as additional generic-fact
   sources.
   - Useful for object-property-action facts.
   - Require strict filtering and held-out audit because generic facts can be
     noisy or culturally/contextually broad.

6. FrameNet, VerbNet, and PropBank for action-role structure.
   - Use for who-does-what-to-whom, action frames, causes, recipients, objects,
     and event composition.

Policy:

- Prefer programmatic extraction and filtering over LLM-generated rows.
- Use LLMs only for small quality-audit samples, ambiguous mapping decisions,
  and answer judging where exact match is too strict.
- Keep source triples, mapped relations, generated statements, and held-out
  questions as separate artifacts.
- Never train blindly on raw external triples; every source needs a mapper,
  validator, and noise report.

## Near-Term Tasks

1. Checkpoint the current physical-world artifacts. Done in commit `c82eeab`.
2. Add a validator for held-out evaluation JSON. Done.
3. Add a validator for curriculum JSONL. Done.
4. Build an evaluation runner for the held-out physical cases. Done.
5. Generate model-ready train/dev/test splits. Done for `physical_v0`.
6. Create three matched datasets: plain text, flat triples, and
   relation-scaffolded. Done for `physical_v0`.
7. Pick one tiny transformer baseline and freeze the training command. Done.
8. Run a tiny overfit sanity check. Done for `relation_scaffolded`.
9. Run the first held-out comparison.
10. Write the first physical-world experiment report.
11. Revise the graph and generator based on failures.
12. Only then start the social-world domain or math-abstraction domain.

## Working Definition of Success

This project is working if a smaller model trained with explicit developmental
relation scaffolding can learn commonsense, abstraction, and affective
reasoning with less data or compute than a comparable plain-text baseline.
