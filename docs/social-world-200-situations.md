# 200 Simple Social-World Situation Families

Status: raw situation inventory.

Related files:

- `plan.md`
- `docs/developmental-relation-graph.md`
- `docs/core-relation-curriculum-plan.md`
- `data/developmental_graph/core_curriculum_plan.json`

## Purpose

This file lists 200 broad everyday social-world situations that can later
become the grounded entry layer for a social-domain relation curriculum.

This is intentionally a raw observation file. It should not explain what each
situation means, what relation the model should learn, or what abstraction it
supports. Interpretation belongs in a later relation-audit file.

The social world here means ordinary human interaction before formal adult
domains such as law, politics, economics, history, or institutional ethics. It
includes caregiver interaction, attention, imitation, turn-taking, sharing,
helping, refusal, approval, disapproval, trust, belonging, exclusion,
cooperation, conflict, and simple role behavior.

The list is intentionally overcomplete. Later we should run a prioritisation
pass and choose the highest-value 30-50 situation families for the first
social-world dataset.

## Workflow Fields

These fields are operational only. They do not describe what the situation
means.

```text
priority:
  unscored | high | medium | low | exclude

include in first social set:
  undecided | yes | no | maybe

include in relation conversion:
  undecided | yes | no | defer

status:
  candidate | keep | needs_split | needs_merge | remove
```

## Current Summary

Independent first pass, not forced to exactly 50. Counts:

```text
priority high: 134
priority medium: 30
priority low: 36
include in first social set yes: 56
include in first social set maybe: 108
include in first social set no: 36
include in relation conversion yes: 56
include in relation conversion defer: 108
include in relation conversion no: 36
status keep: 164
status candidate: 36
```

The `yes` rows are the first executable social-world relation-audit candidates.
Some high-priority rows are still marked `maybe` because they are better as
second-pass extensions after the first seed graph exists. The `no` rows are not
rejected permanently; they are deferred to keep the first experiment small.

## The 200 Situations

| ID | Priority | Include in first social set | Include in relation conversion | Status | Social-world situation |
|---:|---|---|---|---|---|
| S001 | high | yes | yes | keep | A caregiver enters the room and the child notices them |
| S002 | high | yes | yes | keep | A caregiver leaves the room while the child is awake |
| S003 | high | yes | yes | keep | A caregiver returns after a short absence |
| S004 | medium | maybe | defer | keep | A caregiver calls the child by name |
| S005 | high | yes | yes | keep | A caregiver speaks in a gentle tone |
| S006 | high | yes | yes | keep | A caregiver speaks in a hurried or tense tone |
| S007 | high | yes | yes | keep | A caregiver smiles at the child |
| S008 | medium | maybe | defer | keep | A caregiver frowns or looks worried near the child |
| S009 | medium | maybe | defer | keep | A caregiver laughs during play |
| S010 | low | no | no | candidate | A caregiver is quiet while doing routine care |
| S011 | high | yes | yes | keep | A caregiver picks up the child after crying |
| S012 | high | yes | yes | keep | A caregiver does not immediately respond to crying |
| S013 | high | maybe | defer | keep | A caregiver rocks or pats the child to calm them |
| S014 | low | no | no | candidate | A caregiver changes voice or face to amuse the child |
| S015 | medium | maybe | defer | keep | A caregiver sings a familiar song |
| S016 | high | yes | yes | keep | A caregiver repeats a sound made by the child |
| S017 | high | yes | yes | keep | A caregiver waits after making a playful sound |
| S018 | high | yes | yes | keep | A caregiver stops a game when the child turns away |
| S019 | low | no | no | candidate | A caregiver continues a game even after the child fusses |
| S020 | high | yes | yes | keep | A caregiver comforts the child after a startling sound |
| S021 | high | yes | yes | keep | A familiar family member greets the child |
| S022 | high | yes | yes | keep | An unfamiliar visitor greets the child |
| S023 | medium | maybe | defer | keep | The child is passed from one familiar adult to another |
| S024 | medium | maybe | defer | keep | The child is offered to an unfamiliar adult to hold |
| S025 | high | yes | yes | keep | The child looks back toward a caregiver while near a stranger |
| S026 | high | maybe | defer | keep | A stranger speaks loudly near the child |
| S027 | high | maybe | defer | keep | A stranger smiles and waits before approaching |
| S028 | medium | maybe | defer | keep | A family member plays peekaboo with the child |
| S029 | medium | maybe | defer | keep | A sibling tries to make the child laugh |
| S030 | medium | maybe | defer | keep | A sibling takes a toy from near the child |
| S031 | medium | maybe | defer | keep | A sibling gives a toy to the child |
| S032 | medium | maybe | defer | keep | A sibling shows a toy but keeps it out of reach |
| S033 | medium | maybe | defer | keep | A sibling imitates the child's sound |
| S034 | high | maybe | defer | keep | The child watches two adults talk to each other |
| S035 | high | maybe | defer | keep | The child hears adults argue nearby |
| S036 | high | maybe | defer | keep | The child hears adults laugh together nearby |
| S037 | medium | maybe | defer | keep | The child is present during a family meal |
| S038 | low | no | no | candidate | The child is present during a household prayer or ritual |
| S039 | medium | maybe | defer | keep | Multiple family members speak to the child at once |
| S040 | medium | maybe | defer | keep | One family member tells another what the child needs |
| S041 | high | yes | yes | keep | A child points at an object and an adult looks at it |
| S042 | high | yes | yes | keep | An adult points at an object and the child looks toward it |
| S043 | high | maybe | defer | keep | A child looks between an adult and a toy |
| S044 | high | yes | yes | keep | An adult names an object while holding it |
| S045 | high | yes | yes | keep | An adult names an action while doing it |
| S046 | high | yes | yes | keep | An adult says no while blocking an action |
| S047 | high | yes | yes | keep | An adult says yes or okay before allowing an action |
| S048 | high | yes | yes | keep | An adult claps after the child does something |
| S049 | high | maybe | defer | keep | An adult says good after the child repeats an action |
| S050 | high | yes | yes | keep | An adult stops smiling after the child throws something |
| S051 | medium | maybe | defer | keep | A child reaches for an adult's face |
| S052 | medium | maybe | defer | keep | A child pulls an adult's hair or clothing |
| S053 | high | yes | yes | keep | An adult gently removes the child's hand from something |
| S054 | high | yes | yes | keep | An adult moves a dangerous object away from the child |
| S055 | low | no | no | candidate | An adult takes a messy object from the child |
| S056 | high | yes | yes | keep | A child cries when an object is removed |
| S057 | low | no | no | candidate | A child receives another object after one is removed |
| S058 | high | maybe | defer | keep | An adult distracts the child from a forbidden object |
| S059 | high | maybe | defer | keep | An adult warns the child before touching a hot or sharp item |
| S060 | medium | maybe | defer | keep | An adult guides the child's hand during a simple action |
| S061 | high | yes | yes | keep | Two children reach for the same toy |
| S062 | high | yes | yes | keep | One child grabs a toy another child is holding |
| S063 | high | yes | yes | keep | One child gives a toy to another child |
| S064 | high | yes | yes | keep | One child refuses to give a toy |
| S065 | high | maybe | defer | keep | One child cries after losing a toy |
| S066 | high | yes | yes | keep | An adult asks one child to give the toy back |
| S067 | high | maybe | defer | keep | An adult gives each child a similar toy |
| S068 | high | yes | yes | keep | An adult gives one child a bigger share than another |
| S069 | high | yes | yes | keep | An adult asks children to wait for their turn |
| S070 | high | maybe | defer | keep | A child waits while another child uses an object |
| S071 | high | yes | yes | keep | A child pushes ahead before their turn |
| S072 | medium | maybe | defer | keep | Children pass an object back and forth |
| S073 | low | no | no | candidate | Children roll a ball to each other |
| S074 | medium | maybe | defer | keep | Children build a small stack together |
| S075 | medium | maybe | defer | keep | One child knocks down another child's stack |
| S076 | medium | maybe | defer | keep | One child helps rebuild after knocking something down |
| S077 | high | yes | yes | keep | A child copies another child's action |
| S078 | high | maybe | defer | keep | A child copies an adult's action |
| S079 | medium | maybe | defer | keep | A child watches others before joining play |
| S080 | high | yes | yes | keep | A child tries to join play and is ignored |
| S081 | high | yes | yes | keep | A child is invited into a game |
| S082 | high | yes | yes | keep | A child is told they cannot join a game |
| S083 | low | no | no | candidate | A child follows a simple group action such as clapping |
| S084 | low | no | no | candidate | A child stops when the group stops |
| S085 | low | no | no | candidate | A child continues after others stop |
| S086 | medium | maybe | defer | keep | One child leads a game and others follow |
| S087 | medium | maybe | defer | keep | Two children want to lead the same game |
| S088 | high | yes | yes | keep | A child changes behavior after seeing another child corrected |
| S089 | high | yes | yes | keep | A child changes behavior after seeing another child praised |
| S090 | low | no | no | candidate | A child repeats a behavior that made others laugh |
| S091 | high | yes | yes | keep | A person asks for help carrying or moving something |
| S092 | high | yes | yes | keep | A person helps without being asked |
| S093 | high | yes | yes | keep | A person asks for help and is refused |
| S094 | high | maybe | defer | keep | A person drops something and another person picks it up |
| S095 | high | maybe | defer | keep | A person struggles with a task while another person watches |
| S096 | high | maybe | defer | keep | A person explains how to do a task |
| S097 | high | maybe | defer | keep | A person demonstrates a task instead of explaining it |
| S098 | high | maybe | defer | keep | A person takes over a task from someone struggling |
| S099 | high | maybe | defer | keep | A person thanks someone for help |
| S100 | low | no | no | candidate | A person does not thank someone after help |
| S101 | high | yes | yes | keep | A person asks permission before using another person's object |
| S102 | high | yes | yes | keep | A person uses another person's object without asking |
| S103 | high | maybe | defer | keep | A person returns a borrowed object |
| S104 | high | maybe | defer | keep | A person does not return a borrowed object |
| S105 | high | maybe | defer | keep | A person says an object belongs to them |
| S106 | high | maybe | defer | keep | Two people claim the same object |
| S107 | low | no | no | candidate | A person labels an object with a name or mark |
| S108 | medium | maybe | defer | keep | A person moves another person's object to a safe place |
| S109 | low | no | no | candidate | A person hides another person's object as a joke |
| S110 | high | maybe | defer | keep | A person becomes upset when their object is damaged |
| S111 | high | maybe | defer | keep | A person apologizes after damaging something |
| S112 | low | no | no | candidate | A person refuses to apologize after damaging something |
| S113 | medium | maybe | defer | keep | A person repairs or replaces something they damaged |
| S114 | low | no | no | candidate | A person blames someone else for damage |
| S115 | high | maybe | defer | keep | A person admits they caused a problem |
| S116 | high | maybe | defer | keep | A person denies causing a problem |
| S117 | high | maybe | defer | keep | A person is believed after explaining what happened |
| S118 | high | maybe | defer | keep | A person is doubted after explaining what happened |
| S119 | low | no | no | candidate | A person changes their story after being questioned |
| S120 | medium | maybe | defer | keep | A person tells another person what they saw happen |
| S121 | high | yes | yes | keep | A person promises to do something later |
| S122 | high | yes | yes | keep | A person does what they promised |
| S123 | high | yes | yes | keep | A person does not do what they promised |
| S124 | high | maybe | defer | keep | A person explains why they could not keep a promise |
| S125 | high | maybe | defer | keep | A person waits because they expect someone to return |
| S126 | high | maybe | defer | keep | A person stops waiting after someone is late |
| S127 | high | maybe | defer | keep | A person lends something because they expect it back |
| S128 | low | no | no | candidate | A person shares information because they expect privacy |
| S129 | low | no | no | candidate | A person repeats private information to others |
| S130 | medium | maybe | defer | keep | A person keeps private information secret |
| S131 | low | no | no | candidate | A person asks another person not to tell |
| S132 | high | yes | yes | keep | A person trusts a familiar person with a task |
| S133 | high | maybe | defer | keep | A person hesitates to trust an unfamiliar person with a task |
| S134 | high | maybe | defer | keep | A person regains trust after repeated reliable behavior |
| S135 | high | yes | yes | keep | A person loses trust after repeated unreliable behavior |
| S136 | high | yes | yes | keep | A person follows a household rule |
| S137 | high | yes | yes | keep | A person breaks a household rule |
| S138 | high | maybe | defer | keep | An adult reminds a child of a rule |
| S139 | high | maybe | defer | keep | An adult explains a rule before enforcing it |
| S140 | high | maybe | defer | keep | An adult enforces a rule without explaining it |
| S141 | high | maybe | defer | keep | A person asks why a rule exists |
| S142 | high | maybe | defer | keep | A person follows a rule only while watched |
| S143 | high | maybe | defer | keep | A person follows a rule when no one is watching |
| S144 | high | maybe | defer | keep | A person is corrected for breaking a rule |
| S145 | high | maybe | defer | keep | A person is praised for following a rule |
| S146 | high | maybe | defer | keep | Two people disagree about whether a rule was broken |
| S147 | low | no | no | candidate | A person asks for an exception to a rule |
| S148 | low | no | no | candidate | A person is allowed an exception because of a special situation |
| S149 | low | no | no | candidate | A person is refused an exception to keep the rule consistent |
| S150 | medium | maybe | defer | keep | A person copies a rule-following behavior from others |
| S151 | high | maybe | defer | keep | A person receives praise in front of others |
| S152 | high | maybe | defer | keep | A person receives criticism in front of others |
| S153 | high | maybe | defer | keep | A person receives quiet correction away from others |
| S154 | low | no | no | candidate | A person feels shy when many people look at them |
| S155 | high | maybe | defer | keep | A person performs better when encouraged |
| S156 | high | maybe | defer | keep | A person stops trying after repeated criticism |
| S157 | high | maybe | defer | keep | A person tries again after being reassured |
| S158 | low | no | no | candidate | A person becomes excited when others cheer |
| S159 | low | no | no | candidate | A person becomes embarrassed after making a mistake |
| S160 | low | no | no | candidate | A person hides a mistake from others |
| S161 | high | maybe | defer | keep | A person asks forgiveness after hurting someone |
| S162 | high | maybe | defer | keep | A hurt person accepts an apology |
| S163 | high | maybe | defer | keep | A hurt person does not accept an apology immediately |
| S164 | high | yes | yes | keep | A person comforts someone who is crying |
| S165 | high | maybe | defer | keep | A person ignores someone who is crying |
| S166 | low | no | no | candidate | A person laughs when someone else falls |
| S167 | high | yes | yes | keep | A person checks whether someone is hurt after they fall |
| S168 | high | maybe | defer | keep | A person becomes angry when interrupted |
| S169 | high | yes | yes | keep | A person waits for another person to finish speaking |
| S170 | high | maybe | defer | keep | Two people speak over each other |
| S171 | high | yes | yes | keep | A person listens and then responds to what was said |
| S172 | low | no | no | candidate | A person answers a different question than the one asked |
| S173 | high | maybe | defer | keep | A person changes their mind after hearing another view |
| S174 | low | no | no | candidate | A person refuses to change their mind after hearing another view |
| S175 | high | maybe | defer | keep | A person asks another person to repeat something |
| S176 | high | maybe | defer | keep | A person misunderstands an instruction |
| S177 | high | maybe | defer | keep | A person clarifies an instruction |
| S178 | low | no | no | candidate | A person gives an instruction that is too vague |
| S179 | high | maybe | defer | keep | A person follows a clear step-by-step instruction |
| S180 | high | maybe | defer | keep | A person refuses an instruction they think is wrong |
| S181 | high | maybe | defer | keep | A guest arrives at home and is welcomed |
| S182 | low | no | no | candidate | A guest arrives and the host is busy |
| S183 | high | maybe | defer | keep | A guest is offered water, tea, or food |
| S184 | high | maybe | defer | keep | A guest refuses food politely |
| S185 | high | maybe | defer | keep | A guest accepts food after being offered |
| S186 | low | no | no | candidate | A guest touches or moves household objects |
| S187 | low | no | no | candidate | A host asks a guest to sit in a particular place |
| S188 | high | maybe | defer | keep | A younger person greets an elder respectfully |
| S189 | high | maybe | defer | keep | An elder gives advice to a younger person |
| S190 | high | maybe | defer | keep | A younger person disagrees with an elder |
| S191 | high | maybe | defer | keep | Family members decide who will do a household task |
| S192 | high | maybe | defer | keep | One person does more household work than others |
| S193 | high | maybe | defer | keep | A person notices someone else doing work and offers help |
| S194 | high | maybe | defer | keep | A person leaves shared work for others to finish |
| S195 | low | no | no | candidate | A family discusses spending money on something |
| S196 | low | no | no | candidate | A child asks for something and is told it is too expensive |
| S197 | high | maybe | defer | keep | A group chooses one activity from several options |
| S198 | high | maybe | defer | keep | A person accepts a group decision they did not prefer |
| S199 | high | maybe | defer | keep | A person leaves a group after feeling excluded |
| S200 | high | maybe | defer | keep | A person returns to a group after being invited back |
