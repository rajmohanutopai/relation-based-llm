# Simple Social-World First-Set Relation Audit

Status: derived relation audit.

Source inventory: `docs/social-world-200-situations.md`

Related plan: `docs/core-relation-curriculum-plan.md`

## Purpose

This file reviews the 56 social-world situations currently marked:

```text
Include in first social set = yes
```

This is intentionally separate from the raw situation inventory. The raw file
should remain observational. This file is where relation interpretation and
graph coverage checking belongs.

The goal is not to model the full social world. The goal is to identify compact,
reusable relation families that can support later concepts such as trust,
fairness, rule following, group belonging, ethics, law, politics, and meaning in
life.

## Selection Criteria

The first set was prioritised in `docs/social-world-200-situations.md` using:

```text
frequency in everyday social life
importance for child and adult social understanding
coverage of attention, response, permission, sharing, trust, rules, and care
usefulness for later domains such as ethics, law, economics, and politics
counterfactual usefulness for held-out evaluation
```

The selection is not final. It is a first executable social-world slice.

## First-Set Situation IDs

```text
S001 S002 S003 S005 S006 S007 S011 S012 S016 S017
S018 S020 S021 S022 S025 S041 S042 S044 S045 S046
S047 S048 S050 S053 S054 S056 S061 S062 S063 S064
S066 S068 S069 S071 S077 S080 S081 S082 S088 S089
S091 S092 S093 S101 S102 S121 S122 S123 S132 S135
S136 S137 S164 S167 S169 S171
```

## Summary

The existing six-month child seed graph already covers some early social motifs:

```text
caregiver presence/absence/return
caregiver soft or sharp tone
caregiver response to crying
imitation and turn-taking precursor
joint attention
blocked action for safety
name/object sound binding precursor
comfort after distress
```

But the social-world curriculum needs a broader social graph. The main missing
or underdeveloped relation families are:

```text
familiar versus unfamiliar agent prediction
social signal valence
contingent response and non-response
turn-taking with waiting
joint attention and reference
permission, blocking, and allowance
giving, taking, refusing, and returning
resource conflict and unequal allocation
fairness precursor
imitation and observational learning
joining, invitation, ignoring, and exclusion
help request, help given, and help refused
promise, future expectation, keeping, and breaking
trust gain and trust loss across repeated reliability
rule compliance, violation, correction, and enforcement
comforting another person's distress
```

## Coverage Table

Coverage values:

```text
covered = already represented well enough in the current child/physical graph
partial = represented indirectly, but needs refinement
missing = not yet represented clearly enough
```

| ID | Situation | Relation families visible | Coverage | Gap or action |
|---:|---|---|---|---|
| S001 | A caregiver enters the room and the child notices them | agent presence, familiar person, attention shift | covered | Reuse caregiver presence and familiar-agent activation. |
| S002 | A caregiver leaves the room while the child is awake | agent absence, expected presence, possible distress | covered | Reuse caregiver absence but keep social-agent context explicit. |
| S003 | A caregiver returns after a short absence | return, expectation repair, comfort reactivation | partial | Add return-after-absence as social repair/reactivation. |
| S005 | A caregiver speaks in a gentle tone | voice tone, familiarity, comfort prediction | covered | Reuse soft-tone comfort relation. |
| S006 | A caregiver speaks in a hurried or tense tone | tense tone, uncertainty, discomfort prediction | partial | Add non-angry tension/urgency signal distinct from sharp tone. |
| S007 | A caregiver smiles at the child | facial signal, positive affect, attention | partial | Add smile/face signal as social-valence cue. |
| S011 | A caregiver picks up the child after crying | distress signal, caregiver response, comfort action | partial | Add contingent care response to distress signal. |
| S012 | A caregiver does not immediately respond to crying | distress signal, non-response, expectation violation | missing | Add non-response and waiting/blocked comfort expectation. |
| S016 | A caregiver repeats a sound made by the child | imitation, response, social turn | covered | Reuse babbling/turn-taking; generalize to imitation response. |
| S017 | A caregiver waits after making a playful sound | turn-taking, pause, expectation of response | partial | Add wait-window in social turn-taking. |
| S018 | A caregiver stops a game when the child turns away | attention withdrawal, consent-like stop, sensitivity | partial | Add attention/avoidance as stop signal. |
| S020 | A caregiver comforts the child after a startling sound | distress, reassurance, safety cue | covered | Reuse comfort after distress; social graph should encode caregiver as comfort source. |
| S021 | A familiar family member greets the child | familiar agent, greeting, positive attention | partial | Add greeting as social approach signal. |
| S022 | An unfamiliar visitor greets the child | unfamiliar agent, greeting, uncertainty | partial | Add familiar/unfamiliar agent contrast. |
| S025 | The child looks back toward a caregiver while near a stranger | social reference, familiar safety base, uncertainty | missing | Add social referencing and safety-base relation. |
| S041 | A child points at an object and an adult looks at it | pointing, shared attention, reference | covered | Reuse joint attention but make child-initiated reference explicit. |
| S042 | An adult points at an object and the child looks toward it | pointing, attention following, reference | covered | Reuse joint attention but make adult-initiated reference explicit. |
| S044 | An adult names an object while holding it | word label, object reference, shared attention | partial | Bridge to language binding; add social naming event. |
| S045 | An adult names an action while doing it | word label, action reference, demonstration | partial | Add action naming distinct from object naming. |
| S046 | An adult says no while blocking an action | prohibition, blocked action, authority signal | partial | Safety blocking exists; add social permission/prohibition. |
| S047 | An adult says yes or okay before allowing an action | allowance, permission, blocked/unblocked action | missing | Add allowance as contrast to prohibition. |
| S048 | An adult claps after the child does something | approval signal, reinforcement, repeated action | partial | Add praise/approval as social reinforcement. |
| S050 | An adult stops smiling after the child throws something | approval withdrawal, action consequence | missing | Add disapproval or approval-loss as social feedback. |
| S053 | An adult gently removes the child's hand from something | physical intervention, blocked access, caregiver control | partial | Safety blocking exists; add gentle intervention as social action. |
| S054 | An adult moves a dangerous object away from the child | safety intervention, object removal, harm prevention | partial | Add caregiver prevention without punishment. |
| S056 | A child cries when an object is removed | blocked access, loss response, caregiver interpretation | partial | Add object-removal distress and possible substitution/repair. |
| S061 | Two children reach for the same toy | shared object, competing access, conflict precursor | missing | Add resource conflict and simultaneous desire. |
| S062 | One child grabs a toy another child is holding | taking, possession disruption, distress risk | missing | Add possession/holding and unpermitted taking. |
| S063 | One child gives a toy to another child | giving, transfer, positive social action | missing | Add object transfer between agents. |
| S064 | One child refuses to give a toy | refusal, possession retention, blocked request | missing | Add refusal as social action. |
| S066 | An adult asks one child to give the toy back | correction, return, restoration | missing | Add repair/return after taking. |
| S068 | An adult gives one child a bigger share than another | unequal allocation, comparison, fairness precursor | missing | Add allocation and unequal-share relation. |
| S069 | An adult asks children to wait for their turn | turn order, waiting, delayed access | missing | Add turn allocation and waiting. |
| S071 | A child pushes ahead before their turn | turn violation, priority conflict | missing | Add turn violation and correction candidate. |
| S077 | A child copies another child's action | imitation, peer model, social learning | partial | Add peer imitation separate from caregiver imitation. |
| S080 | A child tries to join play and is ignored | entry bid, non-response, exclusion precursor | missing | Add group entry bid and ignored bid. |
| S081 | A child is invited into a game | invitation, inclusion, access granted | missing | Add invitation and inclusion. |
| S082 | A child is told they cannot join a game | refusal, exclusion, blocked group access | missing | Add exclusion and denied entry. |
| S088 | A child changes behavior after seeing another child corrected | observational learning, correction, prediction | missing | Add learning from others' consequences. |
| S089 | A child changes behavior after seeing another child praised | observational learning, praise, imitation shift | missing | Add praise-observation relation. |
| S091 | A person asks for help carrying or moving something | help request, need, effort | missing | Add request-for-help relation. |
| S092 | A person helps without being asked | noticed need, voluntary help | missing | Add spontaneous helping. |
| S093 | A person asks for help and is refused | help request, refusal, unmet need | missing | Add refused help contrast. |
| S101 | A person asks permission before using another person's object | ownership, permission request, access | missing | Add permission request and owned object. |
| S102 | A person uses another person's object without asking | ownership violation, unpermitted use | missing | Add unauthorized use. |
| S121 | A person promises to do something later | future action, commitment, expectation | missing | Add promise/commitment relation. |
| S122 | A person does what they promised | commitment fulfilled, trust support | missing | Add promise-kept outcome. |
| S123 | A person does not do what they promised | commitment violation, trust damage | missing | Add promise-broken outcome. |
| S132 | A person trusts a familiar person with a task | familiarity, reliability expectation, delegation | missing | Add trust as predicted reliable future action. |
| S135 | A person loses trust after repeated unreliable behavior | repeated failure, weakened trust | missing | Add trust update across repeated evidence. |
| S136 | A person follows a household rule | rule, compliance, expected behavior | missing | Add rule compliance. |
| S137 | A person breaks a household rule | rule, violation, consequence candidate | missing | Add rule violation. |
| S164 | A person comforts someone who is crying | other distress, care response, empathy precursor | partial | Comfort exists for self; add response to another's distress. |
| S167 | A person checks whether someone is hurt after they fall | observed harm, concern, care check | missing | Add harm-checking as response to possible injury. |
| S169 | A person waits for another person to finish speaking | conversational turn, restraint, respect precursor | missing | Add speech-turn waiting. |
| S171 | A person listens and then responds to what was said | listening, relevance, responsive communication | missing | Add response-to-content relation. |

## Relation Families To Add

The following should become the first social-domain graph extension. Names are
proposed IDs, not final commitments.

### 1. Familiar Agent Presence, Absence, and Return

Needed for:

```text
S001 caregiver enters
S002 caregiver leaves
S003 caregiver returns
S021 familiar family member greets
S022 unfamiliar visitor greets
S025 child references caregiver near stranger
```

Proposed additions:

```text
schema.familiar_agent_presence
schema.agent_absence_return
schema.social_referencing_safety_base
property.familiar_agent
property.unfamiliar_agent
relation.predicts_care
relation.predicts_uncertainty
```

This generalizes the child seed's caregiver relation into a broader
familiar/unfamiliar agent model.

### 2. Social Signals and Valence

Needed for:

```text
S005 gentle tone
S006 hurried or tense tone
S007 smile
S048 clapping after action
S050 smile stops after throwing
```

Proposed additions:

```text
schema.social_affect_signal
schema.approval_feedback
schema.disapproval_or_approval_loss
property.gentle_tone
property.tense_tone
property.smile_signal
property.praise_signal
relation.increases_comfort_prediction
relation.increases_uncertainty_prediction
```

This should connect to the affect-relation model later, but the first graph only
needs the observable social signal and likely effect.

### 3. Contingent Response, Non-Response, and Comfort

Needed for:

```text
S011 picked up after crying
S012 no immediate response to crying
S020 comfort after startle
S164 comforts someone crying
```

Proposed additions:

```text
schema.distress_signal_response
schema.distress_signal_nonresponse
schema.other_distress_comfort
relation.signals_need
relation.responds_to
relation.does_not_respond_to
relation.reduces_distress
```

This is important because social meaning often depends on whether another agent
responds to a need.

### 4. Turn-Taking, Waiting, and Interaction Timing

Needed for:

```text
S016 repeated child sound
S017 caregiver waits after playful sound
S018 game stops when child turns away
S069 wait for turn
S071 pushes ahead before turn
```

Proposed additions:

```text
schema.social_turn_taking
schema.wait_window
schema.turn_order
schema.turn_violation
relation.waits_for_response
relation.takes_turn
relation.violates_turn_order
relation.stop_signal
```

This is a root for later conversation, cooperation, fairness, and respect.

### 5. Joint Attention, Reference, and Naming

Needed for:

```text
S041 child points and adult looks
S042 adult points and child looks
S044 adult names object
S045 adult names action
```

Proposed additions:

```text
schema.joint_attention_reference
schema.object_naming_event
schema.action_naming_event
relation.points_to
relation.attends_to_same_target
relation.labels_object
relation.labels_action
```

This is the bridge from social attention to language binding.

### 6. Permission, Blocking, and Allowance

Needed for:

```text
S046 no while blocking action
S047 yes/okay before allowing action
S101 permission before using another person's object
S102 using another person's object without asking
```

Proposed additions:

```text
schema.permission_request
schema.permission_granted
schema.permission_denied
schema.unauthorized_use
relation.allows_action
relation.blocks_action
relation.requires_permission
```

This is a root for later rule, ownership, rights, and law concepts.

### 7. Possession, Giving, Taking, Refusal, and Return

Needed for:

```text
S061 two children reach for same toy
S062 one child grabs held toy
S063 one child gives toy
S064 one child refuses to give toy
S066 adult asks child to give toy back
```

Proposed additions:

```text
schema.possession_and_access
schema.object_transfer_between_agents
schema.unpermitted_taking
schema.refusal_to_transfer
schema.return_or_restoration
relation.holds
relation.wants_access_to
relation.gives_to
relation.takes_from
relation.returns_to
```

This is a root for sharing, property, theft, lending, and exchange.

### 8. Allocation, Fairness, and Turn Order

Needed for:

```text
S068 bigger share for one child
S069 wait for turn
S071 pushes ahead before turn
```

Proposed additions:

```text
schema.resource_allocation
schema.unequal_allocation
schema.fairness_precursor
relation.receives_more_than
relation.receives_less_than
relation.has_turn_before
relation.has_turn_after
```

Fairness should not be primitive. It is built from comparison, expectation,
need, role, prior rule, and allocation.

### 9. Imitation and Observational Learning

Needed for:

```text
S077 peer imitation
S088 changes after seeing correction
S089 changes after seeing praise
```

Proposed additions:

```text
schema.peer_imitation
schema.observed_consequence_learning
relation.observes_action
relation.observes_feedback
relation.updates_own_action_prediction
```

This lets the model represent learning from another person's experience, not
only from direct self-experience.

### 10. Group Entry, Inclusion, and Exclusion

Needed for:

```text
S080 tries to join play and is ignored
S081 invited into game
S082 told cannot join
```

Proposed additions:

```text
schema.group_entry_bid
schema.group_invitation
schema.group_exclusion
relation.requests_group_access
relation.grants_group_access
relation.denies_group_access
relation.ignores_entry_bid
```

This is a root for belonging, loneliness, status, group identity, and social
meaning.

### 11. Help Request, Help Given, and Help Refused

Needed for:

```text
S091 asks for help
S092 helps without being asked
S093 asks for help and is refused
```

Proposed additions:

```text
schema.help_request_response
schema.spontaneous_help
schema.help_refusal
relation.needs_assistance
relation.requests_assistance
relation.provides_assistance
relation.refuses_assistance
```

This connects effort, need, care, cooperation, reciprocity, and ethics.

### 12. Promise, Reliability, and Trust Update

Needed for:

```text
S121 promises later action
S122 keeps promise
S123 breaks promise
S132 trusts familiar person with task
S135 loses trust after repeated unreliable behavior
```

Proposed additions:

```text
schema.promise_commitment
schema.promise_fulfilled
schema.promise_violated
schema.trust_update
relation.commits_to_future_action
relation.fulfills_commitment
relation.violates_commitment
relation.increases_trust
relation.decreases_trust
```

Trust should be represented as expectation over future action based on past
reliability, not as a primitive word label.

### 13. Rule Compliance and Rule Violation

Needed for:

```text
S136 follows household rule
S137 breaks household rule
```

Proposed additions:

```text
schema.rule_compliance
schema.rule_violation
relation.rule_applies_to_action
relation.action_matches_rule
relation.action_violates_rule
```

Rules should later connect to permission, harm prevention, fairness, role,
authority, and consequence.

## First Social Seed Graph Shape

The first parseable social seed should not create one node per situation. It
should create reusable motifs:

```text
agent
familiar_agent
unfamiliar_agent
attention_target
shared_object
held_object
social_signal
distress_signal
response
nonresponse
permission
prohibition
turn
group
help_request
promise
trust_state
rule
```

Core social schemas:

```text
familiar_agent_presence
distress_signal_response
social_affect_signal
social_turn_taking
joint_attention_reference
permission_request
object_transfer_between_agents
resource_allocation
peer_imitation
group_entry_bid
help_request_response
promise_commitment
trust_update
rule_compliance
```

## Held-Out Evaluation Ideas

The held-out social evaluation should test transfer rather than exact labels.

Examples:

```text
If one child gives a toy and later asks for it back, what social relation is
active?
```

Expected relation path:

```text
object_transfer -> expected return or access expectation -> cooperation/trust
```

Example:

```text
Why is ignoring a crying person different from not hearing them?
```

Expected relation path:

```text
distress signal + perceived by agent + no response -> nonresponse
distress signal + not perceived -> missing information, not refusal
```

Example:

```text
Why does breaking a promise reduce trust?
```

Expected relation path:

```text
future commitment -> expected action -> action not done -> prediction failure
-> lower reliability expectation
```

Example:

```text
Why is a bigger share sometimes unfair and sometimes acceptable?
```

Expected relation path:

```text
allocation comparison + need/role/rule/context -> fairness judgment
```

## Next Step

Create the parseable seed graph:

```text
data/developmental_graph/seeds/social_world.json
```

Then create a held-out evaluation file before generating model-ready social
curriculum.
