# External Source Check

Status date: 2026-05-01

Purpose: identify which public structured sources can expand the relation-first
curriculum without paying an LLM to generate every row.

## 6mo Sources Checked

| Source | Local status | Current use | Result |
| --- | --- | --- | --- |
| ConceptNet 5.7 | Downloaded at `data/external/conceptnet/` | Commonsense object/action/place triples | Cleaned strict mapper gives 162 edges over 108 seed concepts. |
| WordNet | Available through NLTK corpora | Lexical hierarchy and part-whole relations | Cleaned mapper gives 72 edges over 54 seed concepts. |
| Visual Genome | Downloaded at `data/external/visual_genome/` | Visual object-property, object-location, held/touched evidence | Cleaned high-count mapper gives 462 usable edges in the combined layer. |
| Wordbank / MacArthur-Bates CDI | Downloaded at `data/external/wordbank/` | Developmental word staging | American English WG/WS audit gives 1073 item-form rows; 121 seed concepts matched. |

Current combined output:

```text
data/developmental_graph/experiments/age_6mo_external_relations_v4_wordbank_seed/
```

Current combined counts:

```text
seed: age_6mo_root_world_wordbank_v1
seed concepts: 520
edges: 705
covered seed concepts: 149 / 520
sources:
  conceptnet: 153
  wordnet: 74
  visual_genome: 478
```

Visual Genome relations are rendered as evidence:

```text
ball can be blue.
cup can be at a hand.
book can be held.
```

They are not rendered as hard definitions like `ball is blue`.

## Wordbank/CDI Staging Audit

Current output:

```text
data/developmental_graph/experiments/wordbank_age_staging_v1/
```

Current counts:

```text
seed: age_6mo_root_world_wordbank_v1
wordbank item-form rows: 1073
matched rows: 303
matched seed concepts: 148 / 520
early unmatched rows: 118
```

The audit produces:

```text
wordbank_english_american_item_staging.csv
seed_matches.csv
unmatched_wordbank_items.csv
early_unmatched_wordbank_items.csv
```

Examples of early unmatched items that may need mapping or future inclusion:

```text
drink action
woof woof
yum yum
thank you
go
bite
brush
bring
dance
give
stroller
throw
```

Wordbank should be used to revise age staging and aliases. It should not be
used as a relation graph by itself.

The first Wordbank seed revision is:

```text
data/developmental_graph/seeds/age_6mo_root_world_wordbank_v1.json
```

It keeps the original 500 seed concepts unchanged, adds 20 early CDI concepts,
and adds aliases such as `tummy -> belly`, `teddybear -> soft toy`,
`eat -> feeding starts`, `bath -> bath water`, and `all gone -> gone`.

## Remaining Sources

| Source | Best project role | 6mo priority | Notes |
| --- | --- | --- | --- |
| ATOMIC / ATOMIC 2020 | Social, affective, intent, consequence relations | Medium-later | Valuable for comfort, pain, desire, help, harm, intention, and consequence after root physical/body relations stabilize. |
| GenericsKB / TupleKB / Quasimodo / WebChild | Generic object-property-action facts | Medium | Useful, but noisier than ConceptNet/WordNet. Should be added only with strict source-specific filters. |
| FrameNet / VerbNet / PropBank | Event frames and action roles | Later | Best for toddler-plus language/action grammar: actor, object, recipient, instrument, cause, result. Too abstract for the first 6mo source layer. |

## Recommendation

Next source to wire should be a small ATOMIC slice for affect and social
consequence, limited to root concepts such as pain, comfort, hunger, help,
touch, cry, smile, and caregiver response.

Do not train directly on raw Visual Genome, ConceptNet, ATOMIC, or generic KB
rows. Each source needs a mapper, a blocklist/allowlist, and a random sample
audit before it is merged into a model-ready curriculum.
