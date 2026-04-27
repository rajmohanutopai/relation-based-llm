# Language-Binding First-Set Relation Audit

Status: derived relation audit.

Source inventory: `docs/language-binding-400-situations.md`

Related plan: `docs/core-relation-curriculum-plan.md`

## Purpose

This file reviews the 179 language-binding situations currently marked:

```text
Include in first language set = yes
```

This is intentionally separate from the raw situation inventory. The raw file
should remain observational. This file is where relation interpretation and
graph coverage checking belongs.

The goal is not to teach language as isolated word meanings. The goal is to
bind words, gestures, marks, sentence forms, questions, stories, tone, and
context to already available relation structures.

In this theory, a word is not the meaning. A word is a handle into a relation
cluster. A strong meaning is a cluster with many strong relations and many
weaker context-sensitive relations.

## Selection Criteria

The first set was prioritised in `docs/language-binding-400-situations.md`
using:

```text
coverage of root language-binding mechanisms
connection to child, physical, social, and math seed graphs
usefulness for ordinary text understanding
counterfactual usefulness for held-out evaluation
avoidance of very narrow vocabulary, rare idioms, and advanced discourse in pass one
```

The selection is not final. It is a first executable language-binding slice.

## First-Set Situation IDs

```text
LB001 LB002 LB003 LB008 LB009 LB010 LB011 LB012 LB015 LB016
LB017 LB018 LB019 LB020 LB022 LB024 LB025 LB030 LB032 LB033
LB034 LB035 LB036 LB038 LB039 LB040 LB041 LB042 LB044 LB045
LB046 LB050 LB051 LB052 LB054 LB055 LB056 LB057 LB058 LB059
LB060 LB061 LB062 LB063 LB064 LB067 LB068 LB073 LB074 LB075
LB076 LB077 LB078 LB083 LB084 LB085 LB089 LB090 LB091 LB092
LB093 LB099 LB100 LB101 LB102 LB103 LB104 LB105 LB109 LB110
LB111 LB112 LB115 LB121 LB122 LB123 LB124 LB125 LB127 LB128
LB129 LB130 LB131 LB132 LB133 LB134 LB135 LB137 LB139 LB140
LB141 LB142 LB143 LB144 LB145 LB146 LB147 LB154 LB155 LB156
LB159 LB160 LB164 LB167 LB173 LB174 LB175 LB176 LB177 LB178
LB179 LB180 LB181 LB182 LB183 LB184 LB185 LB186 LB187 LB188
LB189 LB195 LB199 LB200 LB203 LB204 LB221 LB222 LB225 LB236
LB247 LB250 LB255 LB256 LB261 LB263 LB264 LB265 LB266 LB267
LB269 LB271 LB273 LB275 LB277 LB281 LB283 LB285 LB287 LB293
LB294 LB295 LB301 LB302 LB304 LB307 LB308 LB311 LB313 LB315
LB316 LB317 LB319 LB321 LB322 LB323 LB331 LB332 LB334 LB351
LB359 LB361 LB363 LB364 LB391 LB394 LB398 LB399 LB400
```

## Summary

The existing child, physical, social, and math graphs already contain many
meaning roots:

```text
familiar caregiver and self/other
joint attention and pointing
object, action, property, quantity, and spatial relations
comfort/discomfort and social signal valence
giving, taking, helping, promise, trust, rule, and turn-taking
same/different, more/less, ordering, grouping, and conditional rules
```

But the language-binding curriculum needs those roots represented as explicit
language attachment schemas. The main missing or underdeveloped relation
families are:

```text
name and social-role word binding
gesture-word binding for yes, no, stop, come, wait, and bye
object-label binding with category generalization
property-label and modifier binding
quantity, order, and set-word binding
spatial and temporal word binding
action and event-word binding
pronoun, possession, and perspective binding
sentence-to-event binding
instruction-to-action binding
question-to-relation-query binding
child utterance, correction, and repair
written sign, symbol, and number binding
story, promise, rule, and discourse binding
conditional, causal, and logical sentence binding
polysemy and context-sensitive word sense
tone/prosody and affective meaning shift
multilingual label equivalence
sound-form contrast and approximate word recognition
negation, absence, tense, aspect, and modality
epistemic and mental-state language
indirect requests, jokes, promises, and unfamiliar-word negotiation
```

## Grouped Coverage Table

Coverage values:

```text
covered = already represented well enough in the current child/physical/social/math graph
partial = represented indirectly, but needs a language-binding schema
missing = not yet represented clearly enough
```

This table covers all 179 first-set IDs exactly once.

| Group | IDs | Situation pattern | Relation families visible | Coverage | Gap or action |
|---|---|---|---|---|---|
| Name, gesture, permission, and early social commands | LB001 LB002 LB003 LB008 LB009 LB010 LB011 LB012 LB015 LB016 LB017 LB225 | Names, caregiver roles, come/stop/no/yes/wait/bye/okay with gesture or action | social handle, gesture-word binding, permission, prohibition, allowance, delay | partial | Add language handles for familiar agents and permission states; connect word, gesture, action, and social response. |
| Object and category labels | LB018 LB019 LB020 LB022 LB024 LB025 LB030 LB032 LB033 LB034 LB035 LB036 | Cup, spoon, ball, dog, banana, water, picture labels, category extension across size/color/instance | object-label binding, reference, category generalization, picture-object mapping | partial | Add label-as-handle into object category clusters; test extension beyond one object instance. |
| Property and modifier labels | LB038 LB039 LB040 LB041 LB042 LB044 LB045 LB046 LB050 LB051 LB052 LB056 LB057 LB121 LB122 | Color, size, temperature, softness, hardness, wetness, weight, shape, same/different, empty | property-label binding, modifier binding, attribute contrast, predicate sentence | partial | Add property words as relation handles, not object names; preserve selected-attribute meaning. |
| Quantity, order, and set words | LB054 LB055 LB058 LB059 LB060 LB061 LB062 LB063 LB064 LB146 LB147 LB301 LB302 LB304 LB307 LB308 | More/less, one/two/counting, all/none/some, first, how many, bigger, every/some/only/either/both | quantity word, count word, set quantifier, ordinal, comparison, disjunction, conjunction | partial | Reuse math roots but add language forms that query or constrain quantity and set membership. |
| Spatial, temporal, and state words | LB067 LB068 LB073 LB074 LB075 LB076 LB077 LB078 LB083 LB084 LB139 LB140 LB315 LB316 | Before/after, here/there, inside/outside, on/under, open/closed, ordered instruction timing | deictic reference, spatial preposition, temporal ordering, state word, instruction sequence | partial | Add portable language handles for physical and temporal relations. |
| Action and event words | LB085 LB089 LB090 LB091 LB092 LB093 LB099 LB100 LB101 LB102 LB103 LB104 LB105 LB127 LB128 | Push, roll, bounce, fall, break, spill, eat, drink, give, take, share, help, hurt, event result clauses | action-label binding, event word, cause/effect event, result state | partial | Bind verbs to object-action-effect schemas and event transitions. |
| Self, pronoun, possession, and transfer perspective | LB109 LB110 LB111 LB112 LB115 LB129 LB130 LB133 | Mine/yours, I/you/we, gave/took, give to grandma | speaker perspective, addressee perspective, possessive relation, transfer roles | missing | Add role-sensitive binding so meaning changes with speaker, listener, giver, receiver, and owner. |
| Sentence roles, grammar, and event composition | LB123 LB124 LB125 LB131 LB132 LB134 LB135 LB137 LB261 LB263 LB264 LB265 LB266 LB267 LB269 LB271 LB273 LB275 LB277 | The box is open, toy under chair, dog running, put/take/give/bring, subject-object reversals, modifiers, relative clauses, attachment ambiguity | sentence-event binding, agent-patient role, preposition phrase, modifier scope, role reversal | missing | Add sentence templates that bind word order and grammar roles to relation structure. |
| Questions, child utterance, correction, and repair | LB141 LB142 LB143 LB144 LB145 LB154 LB155 LB156 LB159 LB160 LB400 | Where/what/who/what happened/why, wrong word corrected, one-word requests, two-word utterances, gone, unfamiliar word question | question-as-relation-query, answer target, repair, partial utterance, pragmatic intent | missing | Add query forms that ask for missing relation slots; add correction and approximate utterance repair. |
| Written sign and symbol binding | LB164 LB167 | Stop sign, written number 3 with three dots | sign-action binding, symbol-quantity binding | partial | Reuse math symbol roots but add public sign and text-mark binding. |
| Story, rule, promise, and discourse structure | LB173 LB174 LB175 LB176 LB177 LB178 LB179 LB180 LB195 LB199 LB351 LB359 LB361 LB363 LB364 LB398 LB399 | Promise kept/broken, help/exclusion/rules in stories, retelling, trust, beginning-middle-end, prediction, problem/solution | narrative sequence, commitment, rule compliance, rule violation, discourse relation, story problem/solution | partial | Add story events as compressed relation chains, not as isolated text examples. |
| Conditional, causal, and logical instructions | LB181 LB182 LB183 LB184 LB185 LB186 LB187 LB188 LB189 LB311 LB313 LB317 LB319 | If/then, and/or selection, do not, because, when, before/after, permission by condition | conditional action, causal explanation, logical filter, prohibition, trigger condition | partial | Reuse math logic and physical cause roots; add natural-language operators and clause binding. |
| Polysemy, context, and pragmatics | LB200 LB203 LB204 LB391 LB394 | Same word in different sentences, light as weight/light source, joking versus serious, indirect request | context-sensitive sense, word-sense split, pragmatic force | missing | Add context as an active relation selector; the same surface string must route to different relation clusters. |
| Tone, multilingual labels, and sound form | LB221 LB222 LB236 LB247 LB250 LB255 LB256 | Same word happy/angry, same object in English and home language, cat/bat, syllables, mispronunciation, ba for ball | prosody-affect binding, cross-language label equivalence, phonemic contrast, syllable structure, approximate recognition | missing | Add surface-form layer separate from meaning layer; pronunciation variation should not destroy relation binding. |
| Negation, absence, tense, and aspect | LB281 LB283 LB285 LB287 LB293 LB294 LB295 | Not red, do not put, nothing inside, did not spill, eating/ate/will eat | negation, absence, prohibited action, event polarity, tense, aspect | partial | Add temporal and polarity operators over relation structures. |
| Epistemic and mental-state language | LB321 LB322 LB323 LB331 LB332 LB334 | Think/know/maybe/want/believe/expected | belief strength, uncertainty, desire, expectation, mental-state attribution | missing | Add language handles for internal-state relation models without making them primitive word labels. |

## Relation Families To Add

The following should become the first language-binding graph extension. Names
are proposed IDs, not final commitments.

### 1. Word Handle and Relation Cluster

Needed for nearly every selected row.

Proposed additions:

```text
schema.word_handle
schema.relation_cluster_binding
schema.contextual_relation_activation
relation.word_points_to_cluster
relation.cluster_has_strong_relation
relation.cluster_has_weak_relation
relation.context_selects_relation_subset
```

This is the core theory link. A word does not contain meaning by itself. It
activates a relation cluster. Context controls which subset becomes active.

### 2. Name, Gesture, Permission, and Social Command Binding

Needed for:

```text
LB001 LB002 LB003 LB008 LB009 LB010 LB011 LB012 LB015 LB016 LB017 LB225
```

Proposed additions:

```text
schema.name_binding
schema.social_role_word_binding
schema.gesture_word_pairing
schema.permission_word_binding
schema.prohibition_word_binding
schema.delay_word_binding
relation.names_agent
relation.gesture_confirms_word
relation.word_allows_action
relation.word_blocks_action
```

This is the first language layer over the social graph.

### 3. Object Label, Category Extension, and Picture Reference

Needed for:

```text
LB018 LB019 LB020 LB022 LB024 LB025 LB030 LB032 LB033 LB034 LB035 LB036
```

Proposed additions:

```text
schema.object_label_binding
schema.category_extension
schema.picture_object_reference
schema.instance_to_category_binding
relation.labels_object_instance
relation.labels_object_category
relation.same_label_across_instances
relation.picture_represents_object
```

This should prevent the model from treating `ball` as one object instance. The
word should bind to a cluster that survives size, color, picture, and instance
changes.

### 4. Property, Modifier, and Predicate Binding

Needed for:

```text
LB038 LB039 LB040 LB041 LB042 LB044 LB045 LB046 LB050 LB051 LB052
LB056 LB057 LB121 LB122
```

Proposed additions:

```text
schema.property_label_binding
schema.modifier_property_binding
schema.attribute_specific_contrast
schema.predicate_property_sentence
relation.word_labels_property
relation.modifier_selects_attribute
relation.predicate_assigns_property
```

This is important for the user's ball example: `round`, `bouncy`, `squishy`,
`soft`, and `hard` are not independent labels. They are relation handles into
property dimensions and threshold ranges.

### 5. Quantity, Set, Comparison, and Logical Word Binding

Needed for:

```text
LB054 LB055 LB058 LB059 LB060 LB061 LB062 LB063 LB064 LB146 LB147
LB301 LB302 LB304 LB307 LB308
```

Proposed additions:

```text
schema.quantity_word_binding
schema.count_word_binding
schema.set_quantifier_binding
schema.comparison_question_binding
schema.logical_connector_binding
relation.word_labels_count
relation.word_labels_set_scope
relation.word_queries_quantity
relation.word_connects_alternatives
```

This should reuse the math graph but expose natural-language handles for count,
set, comparison, and logical selection.

### 6. Spatial, Temporal, and State Word Binding

Needed for:

```text
LB067 LB068 LB073 LB074 LB075 LB076 LB077 LB078 LB083 LB084
LB139 LB140 LB315 LB316
```

Proposed additions:

```text
schema.spatial_word_binding
schema.temporal_word_binding
schema.state_word_binding
schema.ordered_instruction_binding
relation.word_labels_spatial_relation
relation.word_labels_temporal_relation
relation.word_labels_state
relation.instruction_orders_actions
```

This binds natural words to portable relation structures like inside/outside,
before/after, open/closed, and on/under.

### 7. Verb, Event, and Result-State Binding

Needed for:

```text
LB085 LB089 LB090 LB091 LB092 LB093 LB099 LB100 LB101 LB102
LB103 LB104 LB105 LB127 LB128
```

Proposed additions:

```text
schema.action_word_binding
schema.event_transition_binding
schema.result_state_binding
schema.social_action_word_binding
relation.word_labels_action
relation.word_labels_event_change
relation.action_creates_result_state
```

Verbs should bind to action-effect structure: push creates motion, spill creates
liquid-out-of-container, break creates damaged state, hurt links action/event to
pain or distress.

### 8. Pronoun, Possession, and Role Perspective

Needed for:

```text
LB109 LB110 LB111 LB112 LB115 LB129 LB130 LB133
```

Proposed additions:

```text
schema.speaker_addressee_binding
schema.pronoun_perspective_binding
schema.possessive_relation_binding
schema.transfer_role_binding
relation.word_refers_to_speaker
relation.word_refers_to_addressee
relation.word_refers_to_joint_group
relation.word_labels_possession
relation.sentence_marks_giver_receiver
```

This is a critical part of self/non-self in language: `I`, `you`, `mine`, and
`yours` change meaning depending on who speaks.

### 9. Sentence-to-Event and Grammar-Role Binding

Needed for:

```text
LB123 LB124 LB125 LB131 LB132 LB134 LB135 LB137 LB261 LB263
LB264 LB265 LB266 LB267 LB269 LB271 LB273 LB275 LB277
```

Proposed additions:

```text
schema.sentence_event_binding
schema.agent_patient_role_binding
schema.preposition_phrase_binding
schema.modifier_scope_binding
schema.relative_clause_binding
schema.attachment_ambiguity_binding
relation.word_order_marks_role
relation.phrase_modifies_entity
relation.phrase_modifies_event
```

This is the first place where ordinary language becomes more than labels. Word
order and phrase attachment decide who did what to whom, where, and under what
description.

### 10. Questions, Answers, Repair, and Partial Utterances

Needed for:

```text
LB141 LB142 LB143 LB144 LB145 LB154 LB155 LB156 LB159 LB160 LB400
```

Proposed additions:

```text
schema.question_relation_query
schema.answer_slot_binding
schema.word_correction_repair
schema.partial_utterance_resolution
schema.unfamiliar_word_negotiation
relation.question_requests_missing_slot
relation.answer_fills_requested_slot
relation.context_recovers_partial_word
```

Questions should be represented as requests for missing relation slots: where
asks for location, who asks for agent, why asks for cause, what happened asks
for event transition.

### 11. Written Sign and Symbol Binding

Needed for:

```text
LB164 LB167
```

Proposed additions:

```text
schema.public_sign_binding
schema.written_symbol_binding
schema.symbol_to_action_binding
schema.symbol_to_quantity_binding
relation.sign_triggers_action_rule
relation.symbol_represents_quantity_relation
```

This is deliberately small in the first pass. Writing should enter as a public
symbol system attached to already learned action and quantity relations.

### 12. Story, Promise, Rule, and Discourse Binding

Needed for:

```text
LB173 LB174 LB175 LB176 LB177 LB178 LB179 LB180 LB195 LB199
LB351 LB359 LB361 LB363 LB364 LB398 LB399
```

Proposed additions:

```text
schema.story_event_chain
schema.narrative_order_binding
schema.promise_language_binding
schema.rule_story_binding
schema.problem_solution_discourse
schema.prediction_from_story_state
relation.story_has_beginning_middle_end
relation.sentence_explains_previous_sentence
relation.promise_creates_future_expectation
relation.promise_outcome_updates_trust
```

Stories should be compressed relation chains. This lets the same graph support
retelling, prediction, problem detection, solution detection, and trust update.

### 13. Conditional, Causal, and Logical Sentence Binding

Needed for:

```text
LB181 LB182 LB183 LB184 LB185 LB186 LB187 LB188 LB189
LB311 LB313 LB317 LB319
```

Proposed additions:

```text
schema.conditional_clause_binding
schema.causal_clause_binding
schema.prohibition_clause_binding
schema.and_or_filter_binding
schema.when_trigger_binding
relation.if_clause_sets_condition
relation.because_clause_links_cause
relation.do_not_blocks_action
relation.condition_grants_permission
```

This is where the language graph should connect strongly to math and physical
world roots: condition, cause, filter, trigger, and permission.

### 14. Polysemy, Context Selection, and Pragmatic Force

Needed for:

```text
LB200 LB203 LB204 LB391 LB394
```

Proposed additions:

```text
schema.polysemy_context_selection
schema.word_sense_split
schema.pragmatic_force_binding
schema.indirect_request_binding
relation.context_selects_word_sense
relation.same_surface_different_cluster
relation.sentence_form_implies_request
```

This is an important test for the relation theory. The same word can point to
different clusters depending on the active relation context.

### 15. Tone, Multilingual Equivalence, and Sound-Form Binding

Needed for:

```text
LB221 LB222 LB236 LB247 LB250 LB255 LB256
```

Proposed additions:

```text
schema.prosody_affect_binding
schema.cross_language_label_equivalence
schema.phoneme_contrast_binding
schema.syllable_structure_binding
schema.approximate_word_recognition
relation.tone_changes_affective_prediction
relation.two_surface_forms_share_cluster
relation.sound_difference_changes_word_candidate
relation.context_resolves_partial_surface_form
```

This keeps surface form separate from meaning while still letting sound, accent,
tone, and language affect interpretation.

### 16. Negation, Absence, Tense, Aspect, and Mental-State Language

Needed for:

```text
LB281 LB283 LB285 LB287 LB293 LB294 LB295 LB321 LB322 LB323
LB331 LB332 LB334
```

Proposed additions:

```text
schema.negation_operator_binding
schema.absence_word_binding
schema.tense_event_time_binding
schema.epistemic_strength_binding
schema.desire_belief_expectation_binding
relation.negates_property
relation.negates_action_event
relation.word_marks_event_time
relation.word_marks_uncertainty
relation.word_marks_belief_or_desire
```

This lets language modify an existing relation rather than creating a separate
fact. `The cup is red` and `The cup is not red` share a target relation but
differ in polarity.

## Proposed First Graph Shape

The first language graph should not create one node per sentence. It should
create reusable binding motifs:

```text
surface_form
spoken_word
gesture
written_mark
sign
symbol
word_handle
relation_cluster
context
speaker
listener
referent
property
event
sentence
question
story
tone
language_variant
```

Core language schemas:

```text
word_handle
relation_cluster_binding
name_binding
gesture_word_pairing
object_label_binding
category_extension
property_label_binding
quantity_word_binding
spatial_word_binding
temporal_word_binding
action_word_binding
pronoun_perspective_binding
sentence_event_binding
question_relation_query
written_symbol_binding
story_event_chain
conditional_clause_binding
causal_clause_binding
polysemy_context_selection
prosody_affect_binding
cross_language_label_equivalence
negation_operator_binding
tense_event_time_binding
epistemic_strength_binding
```

## Held-Out Evaluation Ideas

The held-out language evaluation should test transfer rather than exact labels.

Example:

```text
The model sees: "The cup is not under the table."
It has learned: cup, under, table, not.
Question: Which relation is blocked?
```

Expected relation path:

```text
cup-location-under-table candidate -> negation operator -> relation not asserted
```

Example:

```text
The model sees: "The light box is easy to lift" and "Turn on the light."
Question: Are both uses of light the same relation?
```

Expected relation path:

```text
same surface form -> different context -> weight cluster versus illumination cluster
```

Example:

```text
The model sees: "Riya promised to bring the toy" and later "Riya did not bring it."
Question: What changed?
```

Expected relation path:

```text
promise creates future expectation -> expected action absent -> trust/reliability decreases
```

## Seed Graph Requirements

The parseable `language_binding.json` seed should include:

```text
nodes for surface forms, words, gestures, signs, symbols, speakers, listeners,
referents, relation clusters, contexts, questions, sentences, and stories

relations for labels, refers_to, modifies, queries, negates, conditions,
causes, permits, prohibits, predicts, promises, fulfills, violates, and
context_selects

micro_experiences that render the same underlying relation in plain_text,
relation_scaffolded, and relation_first_then_text formats

evaluation_questions that force transfer across word order, context, negation,
polysemy, and story state
```

The seed graph should be compact. The purpose is to create high-density relation
motifs, not to encode a dictionary.

## Do Not Do In First Pass

Do not add:

```text
a full grammar ontology
a full dictionary
rare idioms
large multilingual vocabulary
advanced literary interpretation
full conversational pragmatics
one node per row from the raw inventory
```

Those are later domains. The first pass should prove that language can attach to
relation structures and improve transfer efficiency in a small model.
