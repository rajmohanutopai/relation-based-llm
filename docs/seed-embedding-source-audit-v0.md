# Seed Embedding Source Audit V0

Status date: 2026-05-01

Purpose: sample currently uncovered 6mo seed concepts and check whether nearby
terms exist in external sources. This tests whether low coverage means
`missing in the world` or `present but not mapped by our current extractors`.

## Method

Input seed:

```text
data/developmental_graph/seeds/age_6mo_root_world_wordbank_v1.json
```

Current coverage baseline:

```text
data/developmental_graph/experiments/age_6mo_external_relations_v4_wordbank_seed/
```

Audit output:

```text
data/developmental_graph/experiments/seed_embedding_source_audit_v0/
```

Procedure:

1. Find seed concepts not covered by current external relation edges.
2. Randomly sample 30 uncovered concepts.
3. Pull lexically nearby candidate terms from ConceptNet, WordNet, Visual
   Genome, Wordbank, and existing mapped external edges.
4. Rank candidates using `sentence-transformers/all-MiniLM-L6-v2` embeddings.

This is a candidate discovery audit, not a training dataset.

## Result

Sample size:

```text
30 uncovered seed concepts
```

Candidate pool:

```text
source terms considered: 142506
embedded candidate terms: 12153
```

Top-score distribution:

```text
>= 0.75:  2 / 30
>= 0.65: 12 / 30
>= 0.55: 28 / 30
>= 0.45: 30 / 30
```

Interpretation:

```text
Most sampled concepts have source-near terms. The main issue is not that the
world has no matching knowledge. The issue is that our current source mappers
are too exact, too ontology-like, or do not convert source phrases/definitions
into our relation grammar.
```

## Examples

Strong or useful source-near matches:

```text
moving -> moving of things / act or process of moving
tip over -> tip over / tip over very easily
avoidance -> avoidance / conditioned avoidance
cause -> relation between causes and effects / cause and effect
hidden -> state of being hidden / hidden and difficult to see
wave arm -> wave arm / moving arm
curiosity -> develop curiosity / natural curiosity
bounce -> bounce / bouncing / bounce back
visible -> visible / is visible
blocked access -> blocked / is blocked / blocked against entry
```

Weak or partial matches:

```text
caregiver voice -> voice / human voice, but not the full caregiver-voice bundle
vacuum sound -> sound perception / sound effect, but not vacuum-specific sound
soap smell -> sense of smell / senses smell, but not soap-specific smell
uh oh -> sound change, but not a clean CDI-style social sound relation
strong link -> strong connection exists, but not our exact learning-memory handle
dishabituation -> term exists, but this is too technical for a root 6mo layer
```

## Conclusion

The sampled audit suggests three fixes:

1. Add a source-term mapping layer.
   Map source phrases and definitions to our seed handles before relation
   extraction. Example: `state of being hidden -> hidden`.

2. Add composite concept templates.
   Some concepts are bundles, not source terms. Example: `caregiver voice`,
   `soap smell`, `vacuum sound`.

3. Separate root handles from public-dataset handles.
   Concepts such as `thing`, `need`, `cause`, `less`, `strong link`, and
   `cause learning` exist in external sources, but the external wording is often
   adult/abstract. They need careful controlled renderings, not raw triples.

Next action: build a synonym/phrase candidate review file from
`embedding_matches.csv`, approve mappings manually, then rerun extraction with
those approved source aliases.

## All-Uncovered Candidate Layer

The full uncovered pass is now available at:

```text
data/developmental_graph/experiments/seed_embedding_source_audit_all_v0/
```

It covers every currently uncovered seed concept:

```text
uncovered seed concepts: 371
review rows: 2226
source terms considered: 337226
embedded candidate terms: 30125
```

Primary review file:

```text
source_mapping_review.csv
```

Review columns:

```text
seed_word
seed_category
candidate_phrase
sources
embedding_score
approved
approved_target
review_notes
```

To approve a mapping, set `approved` to `yes` and keep or edit
`approved_target`. The extraction scripts can now load this file through:

```text
--source-aliases data/developmental_graph/experiments/seed_embedding_source_audit_all_v0/source_mapping_review.csv
```

Only rows with `approved` equal to `yes`, `true`, `y`, or `1` are used.
