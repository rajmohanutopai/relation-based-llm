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

- `scripts/run_heldout_evaluation.py`
  First held-out evaluation runner. It scores model-output JSONL against
  expected relation families, graph anchors, and gap indicators.

- `scripts/create_developmental_experiment_splits.py`
  Deterministic train/dev/curriculum-test split generator for generated
  curriculum files, with held-out prompt export.

- `scripts/create_developmental_dataset_variants.py`
  Generates matched plain-text, flat-triple, and relation-scaffolded dataset
  variants from an experiment split.

- `scripts/train_tiny_causal_lm.py`
  Minimal Hugging Face causal-LM fine-tuning script for one dataset variant.
  Supports `--dry-run` without training dependencies.

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
