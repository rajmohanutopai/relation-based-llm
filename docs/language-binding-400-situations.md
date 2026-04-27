# 400 Language-Binding Situation Families

Status: prioritised situation inventory.

Related files:

- `plan.md`
- `docs/developmental-relation-graph.md`
- `docs/core-relation-curriculum-plan.md`
- `data/developmental_graph/core_curriculum_plan.json`

## Purpose

This file lists 400 broad everyday language-binding situations that can later
become the grounded entry layer for a language-binding relation curriculum.

This is intentionally a raw observation file. It should not explain what each
situation means, what relation the model should learn, or what abstraction it
supports. Interpretation belongs in a later relation-audit file.

Language binding here means ordinary encounters where sounds, gestures, written
marks, words, phrases, sentences, questions, instructions, and stories become
attached to already available experience. The aim is not to treat language as
the first source of meaning. The aim is to capture situations where language is
used with objects, actions, properties, quantities, social events, time,
causality, rules, stories, and figurative speech.

The list is intentionally overcomplete. It now has a first independent
prioritisation pass that chooses the highest-value situation families for the
first language-binding dataset without adding relation interpretation.

## Workflow Fields

These fields are operational only. They do not describe what the situation
means.

```text
priority:
  unscored | high | medium | low | exclude

include in first language set:
  undecided | yes | no | maybe

include in relation conversion:
  undecided | yes | no | defer

status:
  candidate | keep | needs_split | needs_merge | remove
```

## Current Summary

First independent prioritisation pass. Counts:

```text
priority high: 254
priority medium: 3
priority low: 143
include in first language set yes: 179
include in first language set maybe: 78
include in first language set no: 143
include in relation conversion yes: 179
include in relation conversion defer: 78
include in relation conversion no: 143
status keep: 257
status candidate: 143
```

The `yes` rows are the first executable language-binding relation-audit candidates.
Some high-priority rows are still marked `maybe` because they are better as
second-pass extensions after the first seed graph exists. The `no` rows are not
rejected permanently; they are deferred to keep the first experiment small enough
to audit and implement.

## The 400 Situations

| ID | Priority | Include in first language set | Include in relation conversion | Status | Language-binding situation |
|---:|---|---|---|---|---|
| LB001 | high | yes | yes | keep | A caregiver says the child's name while looking at the child |
| LB002 | high | yes | yes | keep | A caregiver says mama while pointing to herself |
| LB003 | high | yes | yes | keep | A caregiver says papa while pointing to another familiar adult |
| LB004 | high | maybe | defer | keep | A child hears the same name said by different family members |
| LB005 | low | no | no | candidate | A child hears a name called from another room |
| LB006 | low | no | no | candidate | A child hears a nickname used for the same person |
| LB007 | low | no | no | candidate | A child hears two people use different names for the same caregiver |
| LB008 | high | yes | yes | keep | A caregiver says come while opening arms toward the child |
| LB009 | high | yes | yes | keep | A caregiver says stop while blocking the child's hand |
| LB010 | high | yes | yes | keep | A caregiver says no while moving an unsafe object away |
| LB011 | high | yes | yes | keep | A caregiver says yes while allowing the child to take a toy |
| LB012 | high | yes | yes | keep | A caregiver says wait while holding a toy just out of reach |
| LB013 | high | maybe | defer | keep | A caregiver says bye-bye while leaving the room |
| LB014 | low | no | no | candidate | A caregiver says hello when entering the room |
| LB015 | high | yes | yes | keep | A caregiver waves while saying bye-bye |
| LB016 | high | yes | yes | keep | A caregiver shakes head while saying no |
| LB017 | high | yes | yes | keep | A caregiver nods while saying yes |
| LB018 | high | yes | yes | keep | A caregiver points to a cup and says cup |
| LB019 | high | yes | yes | keep | A caregiver holds a spoon and says spoon |
| LB020 | high | yes | yes | keep | A caregiver touches a ball and says ball |
| LB021 | high | maybe | defer | keep | A caregiver points to a toy car and says car |
| LB022 | high | yes | yes | keep | A caregiver points to a dog and says dog |
| LB023 | low | no | no | candidate | A caregiver points to a cow in a picture and says cow |
| LB024 | high | yes | yes | keep | A caregiver names a banana before giving it to the child |
| LB025 | high | yes | yes | keep | A caregiver names water before offering a cup |
| LB026 | low | no | no | candidate | A caregiver says milk while holding a milk bottle |
| LB027 | low | no | no | candidate | A caregiver says shoe while putting a shoe on the child |
| LB028 | low | no | no | candidate | A caregiver says shirt while holding a shirt |
| LB029 | low | no | no | candidate | A caregiver says book while opening a picture book |
| LB030 | high | yes | yes | keep | A caregiver names the same object when it appears in a picture |
| LB031 | low | no | no | candidate | A caregiver names the same object when it is partly hidden |
| LB032 | high | yes | yes | keep | A child hears ball used for balls of different sizes |
| LB033 | high | yes | yes | keep | A child hears cup used for cups of different colors |
| LB034 | high | yes | yes | keep | A child hears dog used for different dogs in the street |
| LB035 | high | yes | yes | keep | A child hears toy used for many different play objects |
| LB036 | high | yes | yes | keep | A child hears food used for rice, fruit, and snacks |
| LB037 | low | no | no | candidate | A child hears animal used for dog, cow, and cat pictures |
| LB038 | high | yes | yes | keep | A caregiver says red while showing a red block |
| LB039 | high | yes | yes | keep | A caregiver says blue while showing a blue block |
| LB040 | high | yes | yes | keep | A caregiver says big while holding a large cup |
| LB041 | high | yes | yes | keep | A caregiver says small while holding a small cup |
| LB042 | high | yes | yes | keep | A caregiver says hot before touching a cup of tea |
| LB043 | low | no | no | candidate | A caregiver says cold before touching a cold bottle |
| LB044 | high | yes | yes | keep | A caregiver says soft while pressing a cloth |
| LB045 | high | yes | yes | keep | A caregiver says hard while tapping a wooden block |
| LB046 | high | yes | yes | keep | A caregiver says wet while touching a wet towel |
| LB047 | low | no | no | candidate | A caregiver says dry while touching a dry towel |
| LB048 | low | no | no | candidate | A caregiver says loud after a steel bowl falls |
| LB049 | low | no | no | candidate | A caregiver says quiet while speaking softly |
| LB050 | high | yes | yes | keep | A caregiver says heavy while lifting a full bag |
| LB051 | high | yes | yes | keep | A caregiver says light while lifting an empty box |
| LB052 | high | yes | yes | keep | A caregiver says round while rolling a ball |
| LB053 | low | no | no | candidate | A caregiver says square while showing a square block |
| LB054 | high | yes | yes | keep | A caregiver says more while adding food to a plate |
| LB055 | high | yes | yes | keep | A caregiver says less while taking food away |
| LB056 | high | yes | yes | keep | A caregiver says same while showing two matching objects |
| LB057 | high | yes | yes | keep | A caregiver says different while showing two unlike objects |
| LB058 | high | yes | yes | keep | A caregiver says one while giving one biscuit |
| LB059 | high | yes | yes | keep | A caregiver says two while giving two biscuits |
| LB060 | high | yes | yes | keep | A caregiver counts toys while pointing to them one by one |
| LB061 | high | yes | yes | keep | A caregiver says all while putting every block in a box |
| LB062 | high | yes | yes | keep | A caregiver says none while showing an empty plate |
| LB063 | high | yes | yes | keep | A caregiver says some while leaving a few grapes in a bowl |
| LB064 | high | yes | yes | keep | A caregiver says first while pointing to the first child in a line |
| LB065 | low | no | no | candidate | A caregiver says last while pointing to the last child in a line |
| LB066 | low | no | no | candidate | A caregiver says next while turning a book page |
| LB067 | high | yes | yes | keep | A caregiver says before while talking about washing hands before eating |
| LB068 | high | yes | yes | keep | A caregiver says after while talking about sleeping after dinner |
| LB069 | low | no | no | candidate | A caregiver says now during a current action |
| LB070 | low | no | no | candidate | A caregiver says later while delaying a requested toy |
| LB071 | low | no | no | candidate | A caregiver says yesterday while showing an old photo |
| LB072 | low | no | no | candidate | A caregiver says tomorrow while talking about a future visit |
| LB073 | high | yes | yes | keep | A caregiver says here while pointing near the child |
| LB074 | high | yes | yes | keep | A caregiver says there while pointing across the room |
| LB075 | high | yes | yes | keep | A caregiver says inside while putting a toy in a box |
| LB076 | high | yes | yes | keep | A caregiver says outside while taking a toy out of a box |
| LB077 | high | yes | yes | keep | A caregiver says on while placing a cup on a table |
| LB078 | high | yes | yes | keep | A caregiver says under while placing a ball under a chair |
| LB079 | low | no | no | candidate | A caregiver says behind while hiding a toy behind a pillow |
| LB080 | low | no | no | candidate | A caregiver says between while placing a block between two blocks |
| LB081 | low | no | no | candidate | A caregiver says near while moving a toy close to another toy |
| LB082 | low | no | no | candidate | A caregiver says far while moving a toy away from another toy |
| LB083 | high | yes | yes | keep | A caregiver says open while opening a box |
| LB084 | high | yes | yes | keep | A caregiver says closed while closing a box |
| LB085 | high | yes | yes | keep | A caregiver says push while pushing a toy car |
| LB086 | low | no | no | candidate | A caregiver says pull while pulling a drawer |
| LB087 | low | no | no | candidate | A caregiver says throw while throwing a ball |
| LB088 | low | no | no | candidate | A caregiver says catch while catching a ball |
| LB089 | high | yes | yes | keep | A caregiver says roll while rolling a ball |
| LB090 | high | yes | yes | keep | A caregiver says bounce while bouncing a ball |
| LB091 | high | yes | yes | keep | A caregiver says fall after a toy falls from a table |
| LB092 | high | yes | yes | keep | A caregiver says break after a cup breaks |
| LB093 | high | yes | yes | keep | A caregiver says spill after water falls from a cup |
| LB094 | low | no | no | candidate | A caregiver says cut while cutting fruit |
| LB095 | low | no | no | candidate | A caregiver says mix while stirring sugar into tea |
| LB096 | low | no | no | candidate | A caregiver says melt while ice disappears in water |
| LB097 | low | no | no | candidate | A caregiver says burn while pointing to a flame from a distance |
| LB098 | low | no | no | candidate | A caregiver says sleep while pointing to a sleeping child |
| LB099 | high | yes | yes | keep | A caregiver says eat while feeding the child |
| LB100 | high | yes | yes | keep | A caregiver says drink while offering water |
| LB101 | high | yes | yes | keep | A caregiver says give while handing a toy to the child |
| LB102 | high | yes | yes | keep | A caregiver says take while accepting a toy from the child |
| LB103 | high | yes | yes | keep | A caregiver says share while giving pieces to two children |
| LB104 | high | yes | yes | keep | A caregiver says help while lifting a heavy object with another person |
| LB105 | high | yes | yes | keep | A caregiver says hurt after someone falls |
| LB106 | low | no | no | candidate | A caregiver says sorry after bumping into someone |
| LB107 | low | no | no | candidate | A caregiver says thank you after receiving help |
| LB108 | low | no | no | candidate | A caregiver says please while asking for an object |
| LB109 | high | yes | yes | keep | A caregiver says mine while holding their own object |
| LB110 | high | yes | yes | keep | A caregiver says yours while giving an object back to the child |
| LB111 | high | yes | yes | keep | A child hears I while a speaker talks about their own action |
| LB112 | high | yes | yes | keep | A child hears you while a speaker talks to the child |
| LB113 | low | no | no | candidate | A child hears he while someone points to a boy |
| LB114 | low | no | no | candidate | A child hears she while someone points to a girl |
| LB115 | high | yes | yes | keep | A child hears we while two people act together |
| LB116 | low | no | no | candidate | A child hears they while watching a group of people |
| LB117 | low | no | no | candidate | A caregiver says my cup while holding their own cup |
| LB118 | low | no | no | candidate | A caregiver says your cup while pointing to the child's cup |
| LB119 | low | no | no | candidate | A caregiver says his toy while pointing to another child's toy |
| LB120 | low | no | no | candidate | A caregiver says our house while standing with family members |
| LB121 | high | yes | yes | keep | A caregiver says the ball is red while showing a red ball |
| LB122 | high | yes | yes | keep | A caregiver says the cup is empty while showing an empty cup |
| LB123 | high | yes | yes | keep | A caregiver says the box is open after opening a box |
| LB124 | high | yes | yes | keep | A caregiver says the toy is under the chair |
| LB125 | high | yes | yes | keep | A caregiver says the dog is running while a dog runs |
| LB126 | high | maybe | defer | keep | A caregiver says the baby is sleeping while the baby sleeps |
| LB127 | high | yes | yes | keep | A caregiver says the glass broke after a glass falls |
| LB128 | high | yes | yes | keep | A caregiver says the floor is wet after water spills |
| LB129 | high | yes | yes | keep | A caregiver says the child gave the toy to the sibling |
| LB130 | high | yes | yes | keep | A caregiver says the sibling took the toy from the child |
| LB131 | high | yes | yes | keep | A caregiver says put the ball in the box |
| LB132 | high | yes | yes | keep | A caregiver says take the ball out of the box |
| LB133 | high | yes | yes | keep | A caregiver says give the cup to grandma |
| LB134 | high | yes | yes | keep | A caregiver says bring the red block |
| LB135 | high | yes | yes | keep | A caregiver says bring two spoons |
| LB136 | low | no | no | candidate | A caregiver says pick the big ball |
| LB137 | high | yes | yes | keep | A caregiver says put the small cup inside the big cup |
| LB138 | low | no | no | candidate | A caregiver says touch your nose |
| LB139 | high | yes | yes | keep | A caregiver says wash your hands before eating |
| LB140 | high | yes | yes | keep | A caregiver says first wear shoes, then go outside |
| LB141 | high | yes | yes | keep | A caregiver asks where is the ball |
| LB142 | high | yes | yes | keep | A caregiver asks what is this while holding a cup |
| LB143 | high | yes | yes | keep | A caregiver asks who came home |
| LB144 | high | yes | yes | keep | A caregiver asks what happened after a toy falls |
| LB145 | high | yes | yes | keep | A caregiver asks why is the floor wet |
| LB146 | high | yes | yes | keep | A caregiver asks how many biscuits are on the plate |
| LB147 | high | yes | yes | keep | A caregiver asks which cup is bigger |
| LB148 | low | no | no | candidate | A caregiver asks do you want water |
| LB149 | low | no | no | candidate | A caregiver asks can I take this toy |
| LB150 | low | no | no | candidate | A caregiver asks did you give the toy back |
| LB151 | low | no | no | candidate | A child answers yes after being offered water |
| LB152 | low | no | no | candidate | A child answers no after being offered food |
| LB153 | low | no | no | candidate | A child points instead of saying the object name |
| LB154 | high | yes | yes | keep | A child says the wrong object name and an adult corrects it |
| LB155 | high | yes | yes | keep | A child uses one word to request a whole action |
| LB156 | high | yes | yes | keep | A child uses two words such as more milk |
| LB157 | low | no | no | candidate | A child says no bath while resisting bath time |
| LB158 | low | no | no | candidate | A child says my toy while holding a toy |
| LB159 | high | yes | yes | keep | A child says want ball while reaching for a ball |
| LB160 | high | yes | yes | keep | A child says gone after a toy is hidden |
| LB161 | low | no | no | candidate | A child sees the written letter A while an adult says A |
| LB162 | low | no | no | candidate | A child sees the written word cat under a cat picture |
| LB163 | low | no | no | candidate | A child sees the written word ball on a flashcard with a ball picture |
| LB164 | high | yes | yes | keep | A child sees a stop sign while an adult says stop |
| LB165 | low | no | no | candidate | A child sees an arrow sign while walking in that direction |
| LB166 | low | no | no | candidate | A child sees a red color swatch labelled red |
| LB167 | high | yes | yes | keep | A child sees number 3 written beside three dots |
| LB168 | low | no | no | candidate | A child sees a label on a storage box and opens that box |
| LB169 | low | no | no | candidate | A child sees a name written on a school notebook |
| LB170 | low | no | no | candidate | A child sees a picture schedule with words below each picture |
| LB171 | high | maybe | defer | keep | A caregiver reads a story about a child losing a toy |
| LB172 | high | maybe | defer | keep | A caregiver reads a story about a child finding a toy |
| LB173 | high | yes | yes | keep | A caregiver reads a story where someone promises to return |
| LB174 | high | yes | yes | keep | A caregiver reads a story where someone breaks a promise |
| LB175 | high | yes | yes | keep | A caregiver reads a story where a character helps another character |
| LB176 | high | yes | yes | keep | A caregiver reads a story where a character is left out of a game |
| LB177 | high | yes | yes | keep | A caregiver reads a story where a rule is followed |
| LB178 | high | yes | yes | keep | A caregiver reads a story where a rule is broken |
| LB179 | high | yes | yes | keep | A caregiver retells an event that happened earlier in the day |
| LB180 | high | yes | yes | keep | A child retells that a cup fell and water spilled |
| LB181 | high | yes | yes | keep | A caregiver says if it rains, take the umbrella |
| LB182 | high | yes | yes | keep | A caregiver says if the light is red, stop |
| LB183 | high | yes | yes | keep | A caregiver says choose the red and soft toy |
| LB184 | high | yes | yes | keep | A caregiver says choose the red or soft toy |
| LB185 | high | yes | yes | keep | A caregiver says do not touch the hot cup |
| LB186 | high | yes | yes | keep | A caregiver says the cup fell because it was near the edge |
| LB187 | high | yes | yes | keep | A caregiver says the floor is wet because water spilled |
| LB188 | high | yes | yes | keep | A caregiver says the child cried because the toy was taken |
| LB189 | high | yes | yes | keep | A caregiver says the ball rolled because it was pushed |
| LB190 | high | maybe | defer | keep | A caregiver says the plant grew because it got water |
| LB191 | high | maybe | defer | keep | A caregiver says time flies during a fun game |
| LB192 | high | maybe | defer | keep | A caregiver says the child has a warm heart after helping |
| LB193 | high | maybe | defer | keep | A caregiver says a room is cold after people stop talking |
| LB194 | high | maybe | defer | keep | A caregiver says a problem is heavy during a serious talk |
| LB195 | high | yes | yes | keep | A caregiver says a person broke trust after breaking a promise |
| LB196 | high | maybe | defer | keep | A caregiver says a child is in trouble after breaking a rule |
| LB197 | high | maybe | defer | keep | A caregiver says a friend is close even when living far away |
| LB198 | high | maybe | defer | keep | A caregiver says an idea is clear after explaining it |
| LB199 | high | yes | yes | keep | A caregiver says a story has a beginning, middle, and end |
| LB200 | high | yes | yes | keep | A caregiver says the same word can mean different things in different sentences |
| LB201 | low | no | no | candidate | A caregiver says bank while pointing to a river bank in a picture |
| LB202 | low | no | no | candidate | A caregiver says bank while pointing to a building where money is kept |
| LB203 | high | yes | yes | keep | A caregiver says light while lifting a small empty box |
| LB204 | high | yes | yes | keep | A caregiver says light while switching on a lamp |
| LB205 | high | maybe | defer | keep | A caregiver says right while pointing to the right side |
| LB206 | high | maybe | defer | keep | A caregiver says right after a child answers correctly |
| LB207 | medium | maybe | defer | keep | A caregiver says match while pairing socks |
| LB208 | low | no | no | candidate | A caregiver says match while showing a matchstick from a safe distance |
| LB209 | low | no | no | candidate | A caregiver says bark while pointing to a dog making sound |
| LB210 | low | no | no | candidate | A caregiver says bark while pointing to the outside of a tree |
| LB211 | high | maybe | defer | keep | A caregiver says orange while showing an orange fruit |
| LB212 | high | maybe | defer | keep | A caregiver says orange while showing an orange color swatch |
| LB213 | low | no | no | candidate | A caregiver says watch while looking at a wristwatch |
| LB214 | low | no | no | candidate | A caregiver says watch while asking the child to look carefully |
| LB215 | high | maybe | defer | keep | A caregiver says clean while wiping a table |
| LB216 | high | maybe | defer | keep | A caregiver says clean while describing a washed shirt |
| LB217 | high | maybe | defer | keep | A caregiver says run while a child runs |
| LB218 | high | maybe | defer | keep | A caregiver says run while water runs from a tap |
| LB219 | low | no | no | candidate | A caregiver says charge while plugging in a phone |
| LB220 | low | no | no | candidate | A caregiver says charge while talking about paying money |
| LB221 | high | yes | yes | keep | A caregiver speaks the same word in a happy tone |
| LB222 | high | yes | yes | keep | A caregiver speaks the same word in an angry tone |
| LB223 | high | maybe | defer | keep | A caregiver says really in a surprised tone |
| LB224 | high | maybe | defer | keep | A caregiver says really in a doubtful tone |
| LB225 | high | yes | yes | keep | A caregiver says okay as permission |
| LB226 | high | maybe | defer | keep | A caregiver says okay as reluctant agreement |
| LB227 | low | no | no | candidate | A caregiver says fine while meaning the situation is acceptable |
| LB228 | low | no | no | candidate | A caregiver says fine while sounding upset |
| LB229 | high | maybe | defer | keep | A caregiver says come here gently |
| LB230 | high | maybe | defer | keep | A caregiver says come here sharply |
| LB231 | low | no | no | candidate | A caregiver whispers a secret to another adult |
| LB232 | low | no | no | candidate | A caregiver shouts a warning across the room |
| LB233 | medium | maybe | defer | keep | A caregiver repeats a sentence slowly for clarity |
| LB234 | low | no | no | candidate | A caregiver says a familiar sentence quickly during routine care |
| LB235 | high | maybe | defer | keep | A child hears the same word spoken with an Indian accent and a foreign accent |
| LB236 | high | yes | yes | keep | A child hears the same object named in English and a home language |
| LB237 | high | maybe | defer | keep | A caregiver uses a Hindi word for water and later uses the English word water |
| LB238 | high | maybe | defer | keep | A caregiver uses a Tamil or Malayalam word for food and later uses the English word food |
| LB239 | high | maybe | defer | keep | A child hears code-switching within one sentence |
| LB240 | high | maybe | defer | keep | A child hears an English noun inside a home-language sentence |
| LB241 | low | no | no | candidate | A child hears a polite form used with an elder |
| LB242 | low | no | no | candidate | A child hears a casual form used with a sibling |
| LB243 | high | maybe | defer | keep | A child hears the same request phrased as a command and as a polite question |
| LB244 | low | no | no | candidate | A child hears a short command from a parent and a longer explanation from a teacher |
| LB245 | high | maybe | defer | keep | A child hears the same story told in two languages |
| LB246 | low | no | no | candidate | A child hears a song line in one language and its meaning explained in another |
| LB247 | high | yes | yes | keep | A caregiver says cat and the child hears bat as a similar sound |
| LB248 | high | maybe | defer | keep | A caregiver says pin and bin to show a sound difference |
| LB249 | low | no | no | candidate | A caregiver says sip and ship to show a sound difference |
| LB250 | high | yes | yes | keep | A caregiver claps the syllables in banana |
| LB251 | high | maybe | defer | keep | A caregiver breaks a long word into smaller sounds |
| LB252 | low | no | no | candidate | A caregiver joins small sounds to say a word |
| LB253 | high | maybe | defer | keep | A child hears rhyming words in a nursery rhyme |
| LB254 | high | maybe | defer | keep | A child hears two words that start with the same sound |
| LB255 | high | yes | yes | keep | A child hears a word mispronounced and then corrected |
| LB256 | high | yes | yes | keep | A child says ba for ball and an adult understands from context |
| LB257 | high | maybe | defer | keep | A child says a partial word while pointing to the desired object |
| LB258 | low | no | no | candidate | A caregiver exaggerates a word sound during play |
| LB259 | low | no | no | candidate | A caregiver sings a word with a changed tune |
| LB260 | high | maybe | defer | keep | A child hears the same word spoken by a child and by an adult |
| LB261 | high | yes | yes | keep | A caregiver says feed the dog |
| LB262 | high | maybe | defer | keep | A caregiver says the dog feeds the puppy |
| LB263 | high | yes | yes | keep | A caregiver says the child chased the dog |
| LB264 | high | yes | yes | keep | A caregiver says the dog chased the child |
| LB265 | high | yes | yes | keep | A caregiver says the ball hit the cup |
| LB266 | high | yes | yes | keep | A caregiver says the cup hit the ball |
| LB267 | high | yes | yes | keep | A caregiver says put the spoon in the cup |
| LB268 | high | maybe | defer | keep | A caregiver says put the cup in the bowl |
| LB269 | high | yes | yes | keep | A caregiver says give the toy to the child |
| LB270 | high | maybe | defer | keep | A caregiver says give the child the toy |
| LB271 | high | yes | yes | keep | A caregiver says the boy with the red cap is running |
| LB272 | low | no | no | candidate | A caregiver says the red cap with the boy is on the table |
| LB273 | high | yes | yes | keep | A caregiver says the small red ball rolled under the chair |
| LB274 | low | no | no | candidate | A caregiver says the red small ball rolled under the chair |
| LB275 | high | yes | yes | keep | A caregiver says the child who was crying got the toy back |
| LB276 | high | maybe | defer | keep | A caregiver says the toy that fell under the chair was found |
| LB277 | high | yes | yes | keep | A caregiver says I saw the child with the telescope |
| LB278 | low | no | no | candidate | A caregiver says the child saw the dog with the collar |
| LB279 | low | no | no | candidate | A caregiver says the old photo album is heavy |
| LB280 | low | no | no | candidate | A caregiver says the old family friend is visiting |
| LB281 | high | yes | yes | keep | A caregiver says the cup is not red |
| LB282 | high | maybe | defer | keep | A caregiver says the cup is not on the table |
| LB283 | high | yes | yes | keep | A caregiver says do not put the toy in the box |
| LB284 | high | maybe | defer | keep | A caregiver says nobody came to the door |
| LB285 | high | yes | yes | keep | A caregiver says nothing is inside the box |
| LB286 | low | no | no | candidate | A caregiver says no one took the toy |
| LB287 | high | yes | yes | keep | A caregiver says the child did not spill the water |
| LB288 | low | no | no | candidate | A caregiver says the child almost spilled the water |
| LB289 | high | maybe | defer | keep | A caregiver says the child has not yet eaten |
| LB290 | high | maybe | defer | keep | A caregiver says the child has already eaten |
| LB291 | high | maybe | defer | keep | A caregiver says the toy is still under the chair |
| LB292 | high | maybe | defer | keep | A caregiver says the toy is no longer under the chair |
| LB293 | high | yes | yes | keep | A caregiver says the child is eating |
| LB294 | high | yes | yes | keep | A caregiver says the child ate |
| LB295 | high | yes | yes | keep | A caregiver says the child will eat |
| LB296 | high | maybe | defer | keep | A caregiver says the child was eating when the bell rang |
| LB297 | low | no | no | candidate | A caregiver says the child had eaten before sleeping |
| LB298 | low | no | no | candidate | A caregiver says the child has been waiting for a long time |
| LB299 | low | no | no | candidate | A caregiver says the child used to play with that toy |
| LB300 | high | maybe | defer | keep | A caregiver says the child is going to visit grandma |
| LB301 | high | yes | yes | keep | A caregiver says every child got a sweet |
| LB302 | high | yes | yes | keep | A caregiver says some children got sweets |
| LB303 | high | maybe | defer | keep | A caregiver says most children got sweets |
| LB304 | high | yes | yes | keep | A caregiver says only one child got a sweet |
| LB305 | high | maybe | defer | keep | A caregiver says at least two spoons are needed |
| LB306 | low | no | no | candidate | A caregiver says no more than two spoons are needed |
| LB307 | high | yes | yes | keep | A caregiver says either the red cup or the blue cup can be used |
| LB308 | high | yes | yes | keep | A caregiver says both the red cup and the blue spoon are needed |
| LB309 | low | no | no | candidate | A caregiver says neither cup is clean |
| LB310 | low | no | no | candidate | A caregiver says all the cups except one are clean |
| LB311 | high | yes | yes | keep | A caregiver says if the toy is broken, do not use it |
| LB312 | high | maybe | defer | keep | A caregiver says unless it rains, we will go outside |
| LB313 | high | yes | yes | keep | A caregiver says when the bell rings, come inside |
| LB314 | low | no | no | candidate | A caregiver says while the water boils, wait near the table |
| LB315 | high | yes | yes | keep | A caregiver says after you wash your hands, sit down |
| LB316 | high | yes | yes | keep | A caregiver says before you touch the book, dry your hands |
| LB317 | high | yes | yes | keep | A caregiver says because the cup is hot, hold the handle |
| LB318 | low | no | no | candidate | A caregiver says although the toy is old, it still works |
| LB319 | high | yes | yes | keep | A caregiver says the child can play if homework is done |
| LB320 | low | no | no | candidate | A caregiver says the child may play but must put toys back |
| LB321 | high | yes | yes | keep | A caregiver says I think the toy is in the box |
| LB322 | high | yes | yes | keep | A caregiver says I know the toy is in the box |
| LB323 | high | yes | yes | keep | A caregiver says maybe the toy is under the bed |
| LB324 | low | no | no | candidate | A caregiver says the toy must be under the bed |
| LB325 | low | no | no | candidate | A caregiver says the toy might be outside |
| LB326 | high | maybe | defer | keep | A caregiver says the toy cannot be in the box because the box is empty |
| LB327 | high | maybe | defer | keep | A caregiver says I remember the toy was on the table |
| LB328 | low | no | no | candidate | A caregiver says I forgot where the toy is |
| LB329 | low | no | no | candidate | A caregiver says the child seems tired |
| LB330 | low | no | no | candidate | A caregiver says the child pretended to sleep |
| LB331 | high | yes | yes | keep | A caregiver says the child wants the toy |
| LB332 | high | yes | yes | keep | A caregiver says the child believes the toy is in the box |
| LB333 | high | maybe | defer | keep | A caregiver says the child knows the toy was moved |
| LB334 | high | yes | yes | keep | A caregiver says the child expected the caregiver to return |
| LB335 | high | maybe | defer | keep | A caregiver says the child was surprised that the toy disappeared |
| LB336 | high | maybe | defer | keep | A caregiver says the child felt sad when the friend left |
| LB337 | high | maybe | defer | keep | A caregiver says the child felt happy when the friend returned |
| LB338 | high | maybe | defer | keep | A caregiver says the child is angry because the turn was skipped |
| LB339 | high | maybe | defer | keep | A caregiver says the child is proud after building a tall tower |
| LB340 | high | maybe | defer | keep | A caregiver says the child is embarrassed after spilling water |
| LB341 | low | no | no | candidate | A caregiver says Riya told Aman that the toy was lost |
| LB342 | low | no | no | candidate | A caregiver says Riya told Aman to bring the toy |
| LB343 | medium | maybe | defer | keep | A caregiver says Aman promised Riya that he would return the toy |
| LB344 | low | no | no | candidate | A caregiver says Riya thought Aman had returned the toy |
| LB345 | low | no | no | candidate | A caregiver says Aman knew Riya was waiting |
| LB346 | low | no | no | candidate | A caregiver says the teacher asked the child who took the toy |
| LB347 | low | no | no | candidate | A caregiver says the child asked where the toy went |
| LB348 | low | no | no | candidate | A caregiver says the child asked why the game stopped |
| LB349 | low | no | no | candidate | A caregiver says the child asked whether the visitor will come tomorrow |
| LB350 | low | no | no | candidate | A caregiver says the child said that the cup broke |
| LB351 | high | yes | yes | keep | A caregiver reads a two-sentence story where the second sentence explains the first |
| LB352 | low | no | no | candidate | A caregiver reads a story where a character changes their mind |
| LB353 | low | no | no | candidate | A caregiver reads a story with a surprise ending |
| LB354 | low | no | no | candidate | A caregiver reads a story where the same event is shown from two people's views |
| LB355 | low | no | no | candidate | A caregiver reads a story where a character lies |
| LB356 | low | no | no | candidate | A caregiver reads a story where a character tells the truth |
| LB357 | low | no | no | candidate | A caregiver reads a story where a misunderstanding is corrected |
| LB358 | low | no | no | candidate | A caregiver reads a story where a missing object is found by following clues |
| LB359 | high | yes | yes | keep | A caregiver asks the child to predict what will happen next in a story |
| LB360 | high | maybe | defer | keep | A caregiver asks the child to explain why a character acted |
| LB361 | high | yes | yes | keep | A caregiver asks the child to retell a story in order |
| LB362 | low | no | no | candidate | A caregiver asks the child to describe the main character |
| LB363 | high | yes | yes | keep | A caregiver asks the child to find the problem in a story |
| LB364 | high | yes | yes | keep | A caregiver asks the child to find how the problem was solved |
| LB365 | low | no | no | candidate | A caregiver asks what the story title means |
| LB366 | low | no | no | candidate | A caregiver changes a story ending and asks whether it still makes sense |
| LB367 | high | maybe | defer | keep | A caregiver says the word head while pointing to a body part |
| LB368 | high | maybe | defer | keep | A caregiver says the head of the table during dinner |
| LB369 | low | no | no | candidate | A caregiver says the foot while pointing to a body part |
| LB370 | low | no | no | candidate | A caregiver says the foot of the bed while making the bed |
| LB371 | low | no | no | candidate | A caregiver says the mouth of a bottle |
| LB372 | low | no | no | candidate | A caregiver says the mouth of a person |
| LB373 | low | no | no | candidate | A caregiver says the leg of a chair |
| LB374 | low | no | no | candidate | A caregiver says the leg of a person |
| LB375 | high | maybe | defer | keep | A caregiver says a sharp idea during a conversation |
| LB376 | high | maybe | defer | keep | A caregiver says a sharp knife while cutting fruit |
| LB377 | low | no | no | candidate | A caregiver says a sweet child after kind behavior |
| LB378 | low | no | no | candidate | A caregiver says sweet mango while tasting fruit |
| LB379 | high | maybe | defer | keep | A caregiver says the plan fell apart |
| LB380 | high | maybe | defer | keep | A caregiver says the tower fell apart |
| LB381 | low | no | no | candidate | A caregiver says the argument was heated |
| LB382 | low | no | no | candidate | A caregiver says the tea was heated |
| LB383 | low | no | no | candidate | A caregiver says the child crossed a line after breaking a rule |
| LB384 | low | no | no | candidate | A caregiver says the child crossed a line on the floor |
| LB385 | high | maybe | defer | keep | A caregiver says the idea grew from a small question |
| LB386 | high | maybe | defer | keep | A caregiver says the plant grew from a seed |
| LB387 | low | no | no | candidate | A caregiver says the relationship became stronger |
| LB388 | low | no | no | candidate | A caregiver says the rope became stronger |
| LB389 | high | maybe | defer | keep | A caregiver says the child carries responsibility |
| LB390 | high | maybe | defer | keep | A caregiver says the child carries a bag |
| LB391 | high | yes | yes | keep | A caregiver says the same sentence can be serious or joking depending on context |
| LB392 | low | no | no | candidate | A caregiver says a joke and waits for laughter |
| LB393 | low | no | no | candidate | A caregiver says a sarcastic sentence that sounds positive but means criticism |
| LB394 | high | yes | yes | keep | A caregiver says an indirect request such as can you open the door |
| LB395 | low | no | no | candidate | A caregiver says it is cold here to suggest closing a window |
| LB396 | low | no | no | candidate | A caregiver says maybe later to refuse a request politely |
| LB397 | low | no | no | candidate | A caregiver says we will see while avoiding a clear promise |
| LB398 | high | yes | yes | keep | A caregiver says I promise and later follows through |
| LB399 | high | yes | yes | keep | A caregiver says I promise and later does not follow through |
| LB400 | high | yes | yes | keep | A caregiver asks what does that mean after hearing an unfamiliar word |
