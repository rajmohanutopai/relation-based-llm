# 200 Math-Abstraction Situation Families

Status: raw situation inventory.

Related files:

- `plan.md`
- `docs/developmental-relation-graph.md`
- `docs/core-relation-curriculum-plan.md`
- `data/developmental_graph/core_curriculum_plan.json`

## Purpose

This file lists 200 broad everyday math-abstraction situations that can later
become the grounded entry layer for a math/abstraction relation curriculum.

This is intentionally a raw observation file. It should not explain what each
situation means, what relation the model should learn, or what abstraction it
supports. Interpretation belongs in a later relation-audit file.

The domain here is not formal mathematics first. It starts with concrete
human-scale encounters: matching, comparing, counting, arranging, grouping,
sharing, measuring, patterning, symbol use, simple rules, and small problem
changes. Formal arithmetic, algebra, geometry, logic, and probability should
later grow from these grounded situations.

The list is intentionally overcomplete. Later we should run a prioritisation
pass and choose the highest-value situation families for the first
math-abstraction dataset.

## Workflow Fields

These fields are operational only. They do not describe what the situation
means.

```text
priority:
  unscored | high | medium | low | exclude

include in first math set:
  undecided | yes | no | maybe

include in relation conversion:
  undecided | yes | no | defer

status:
  candidate | keep | needs_split | needs_merge | remove
```

## Current Summary

First independent prioritisation pass. Counts:

```text
priority high: 117
priority medium: 73
priority low: 10
include in first math set yes: 66
include in first math set maybe: 124
include in first math set no: 10
include in relation conversion yes: 66
include in relation conversion defer: 124
include in relation conversion no: 10
status keep: 190
status candidate: 10
```

The `yes` rows are the first executable math-abstraction relation-audit
candidates. Some high-priority rows are still marked `maybe` because they are
better as second-pass extensions after the first seed graph exists. The `no`
rows are not rejected permanently; they are deferred to keep the first
experiment small and grounded.

## The 200 Situations

| ID | Priority | Include in first math set | Include in relation conversion | Status | Math-abstraction situation |
|---:|---|---|---|---|---|
| M001 | high | yes | yes | keep | A child is shown two identical red blocks side by side |
| M002 | high | yes | yes | keep | A child is shown a red block and a blue block side by side |
| M003 | medium | maybe | defer | keep | A child is shown two round balls of different colors |
| M004 | high | yes | yes | keep | A child is shown a round ball and a square block |
| M005 | high | yes | yes | keep | A child picks the matching sock from a small pile |
| M006 | high | yes | yes | keep | A child picks the odd sock from a set of matching socks |
| M007 | medium | maybe | defer | keep | A child matches two cups that have the same shape but different colors |
| M008 | medium | maybe | defer | keep | A child matches two cups that have the same color but different sizes |
| M009 | medium | maybe | defer | keep | A child sees two pictures of the same animal in different poses |
| M010 | medium | maybe | defer | keep | A child sees pictures of two different animals in the same pose |
| M011 | medium | maybe | defer | keep | A child places a spoon beside another spoon from the kitchen drawer |
| M012 | medium | maybe | defer | keep | A child places a spoon away from a fork and a knife |
| M013 | medium | maybe | defer | keep | A child sees two toy cars that differ only in size |
| M014 | medium | maybe | defer | keep | A child sees two toy cars that differ only in color |
| M015 | medium | maybe | defer | keep | A child sees two toy cars that differ in both color and shape |
| M016 | high | yes | yes | keep | A child finds another triangle among circles and squares |
| M017 | high | yes | yes | keep | A child finds the one shape that is not like the others |
| M018 | medium | maybe | defer | keep | A child hears two repeated claps and then a different sound |
| M019 | medium | maybe | defer | keep | A child sees two written letters that look the same |
| M020 | medium | maybe | defer | keep | A child sees two written letters that look similar but not identical |
| M021 | high | yes | yes | keep | One biscuit is placed on a plate |
| M022 | high | yes | yes | keep | Two biscuits are placed on a plate |
| M023 | high | maybe | defer | keep | Three biscuits are placed on a plate |
| M024 | high | yes | yes | keep | A plate with no biscuits is placed beside a plate with biscuits |
| M025 | high | yes | yes | keep | A child points to each toy while an adult says number words |
| M026 | high | yes | yes | keep | A child touches the same toy twice while counting toys |
| M027 | high | yes | yes | keep | A child skips one toy while counting a row of toys |
| M028 | high | maybe | defer | keep | A child counts three toys arranged in a straight line |
| M029 | high | maybe | defer | keep | A child counts the same three toys after they are spread out |
| M030 | medium | maybe | defer | keep | A child counts the same three toys after they are gathered close together |
| M031 | high | yes | yes | keep | A child sees three toys in a row and then one more toy is added |
| M032 | high | yes | yes | keep | A child sees four toys in a row and then one toy is removed |
| M033 | medium | maybe | defer | keep | A child sees two toys under one cup and one toy under another cup |
| M034 | medium | maybe | defer | keep | A child sees one toy moved from one cup to another cup |
| M035 | high | maybe | defer | keep | A child is asked to bring one spoon from a drawer |
| M036 | high | maybe | defer | keep | A child is asked to bring two spoons from a drawer |
| M037 | medium | maybe | defer | keep | A child has one block in each hand |
| M038 | medium | maybe | defer | keep | A child has two blocks in one hand and none in the other |
| M039 | medium | maybe | defer | keep | A child sees many small beads scattered on a tray |
| M040 | medium | maybe | defer | keep | A child sees a few large blocks on a tray |
| M041 | high | yes | yes | keep | A child sees a bowl with more grapes than another bowl |
| M042 | high | yes | yes | keep | A child sees two bowls with the same number of grapes |
| M043 | high | maybe | defer | keep | A child sees one tall stack of blocks and one short stack of blocks |
| M044 | high | maybe | defer | keep | A child sees one long row of blocks and one short row of blocks |
| M045 | medium | maybe | defer | keep | A child sees five tiny buttons beside two large buttons |
| M046 | high | yes | yes | keep | A child gives one cup to each person at a table |
| M047 | high | yes | yes | keep | A child gives two cups to one person and none to another |
| M048 | high | yes | yes | keep | A child pairs each shoe with a matching foot |
| M049 | high | yes | yes | keep | A child sees one shoe left after making pairs |
| M050 | high | maybe | defer | keep | A child puts one lid on each container |
| M051 | high | maybe | defer | keep | A child sees more containers than lids |
| M052 | medium | maybe | defer | keep | A child places one crayon beside each sheet of paper |
| M053 | medium | maybe | defer | keep | A child sees one sheet of paper without a crayon |
| M054 | high | yes | yes | keep | A child gives one sweet to each child in a group |
| M055 | high | yes | yes | keep | A child sees one child get an extra sweet |
| M056 | high | maybe | defer | keep | A child divides six blocks between two bowls |
| M057 | high | maybe | defer | keep | A child divides seven blocks between two bowls |
| M058 | medium | maybe | defer | keep | A child places two socks into each drawer section |
| M059 | high | maybe | defer | keep | A child arranges chairs so each child has a place to sit |
| M060 | high | maybe | defer | keep | A child notices one person standing when all chairs are filled |
| M061 | medium | maybe | defer | keep | A child puts buttons into egg-carton holes one by one |
| M062 | medium | maybe | defer | keep | A child sees empty egg-carton holes after all buttons are placed |
| M063 | medium | maybe | defer | keep | A child sees buttons left over after all egg-carton holes are filled |
| M064 | medium | maybe | defer | keep | A child pairs small plates with small cups and large plates with large cups |
| M065 | medium | maybe | defer | keep | A child gives each toy animal one pretend food item |
| M066 | high | yes | yes | keep | Three blocks are placed from smallest to largest |
| M067 | high | yes | yes | keep | Three blocks are placed from largest to smallest |
| M068 | high | yes | yes | keep | A child arranges sticks from shortest to longest |
| M069 | medium | maybe | defer | keep | A child arranges cups from emptiest to fullest |
| M070 | high | yes | yes | keep | A child stands first in a line |
| M071 | high | maybe | defer | keep | A child stands last in a line |
| M072 | high | maybe | defer | keep | A child moves from last place to first place in a line |
| M073 | high | yes | yes | keep | A child places picture cards in the order of a daily routine |
| M074 | medium | maybe | defer | keep | A child places a bedtime picture before a breakfast picture |
| M075 | high | maybe | defer | keep | A child sees a seed, a plant, and a fruit picture out of order |
| M076 | high | maybe | defer | keep | A child arranges nesting cups from inside to outside |
| M077 | medium | maybe | defer | keep | A child places puzzle pieces in a left-to-right row |
| M078 | medium | maybe | defer | keep | A child reverses the order of colored beads on a string |
| M079 | high | yes | yes | keep | A child follows a two-step instruction with the steps swapped |
| M080 | high | yes | yes | keep | A child follows a three-step instruction in the spoken order |
| M081 | high | maybe | defer | keep | A child puts the smallest cup inside the next larger cup |
| M082 | high | maybe | defer | keep | A child puts a large cup where only a small cup fits |
| M083 | high | maybe | defer | keep | A child places a missing middle block between a small and a large block |
| M084 | low | no | no | candidate | A child sees Monday, Wednesday, and Thursday on a calendar strip |
| M085 | medium | maybe | defer | keep | A child steps on numbered floor tiles in order |
| M086 | high | yes | yes | keep | A child puts all red objects into one basket |
| M087 | high | yes | yes | keep | A child puts all round objects into one basket |
| M088 | high | yes | yes | keep | A child puts red round objects into one basket and red square objects into another |
| M089 | high | yes | yes | keep | A child sorts spoons, forks, and plates into separate piles |
| M090 | medium | maybe | defer | keep | A child sorts toy animals by animal type |
| M091 | medium | maybe | defer | keep | A child sorts toy animals by size |
| M092 | medium | maybe | defer | keep | A child sorts toy animals by where they are usually seen |
| M093 | high | maybe | defer | keep | A child puts fruits and vegetables into separate baskets |
| M094 | medium | maybe | defer | keep | A child sees a tomato placed with fruit in one setting and vegetables in another |
| M095 | medium | maybe | defer | keep | A child groups school items separately from kitchen items |
| M096 | high | yes | yes | keep | A child groups things that can be worn separately from things that cannot |
| M097 | high | maybe | defer | keep | A child groups things that can roll separately from things that cannot |
| M098 | medium | maybe | defer | keep | A child groups things that make sound separately from things that do not |
| M099 | high | maybe | defer | keep | A child sees one object that belongs in two different piles |
| M100 | high | yes | yes | keep | A child changes the sorting rule after half the objects are sorted |
| M101 | high | yes | yes | keep | A child makes a pile of all things that are not red |
| M102 | medium | maybe | defer | keep | A child makes a pile of all things that are not toys |
| M103 | medium | maybe | defer | keep | A child finds the missing object type in a set of kitchen items |
| M104 | high | maybe | defer | keep | A child names a broad group that includes dogs, cats, and cows |
| M105 | high | maybe | defer | keep | A child names a smaller group inside a broader group of animals |
| M106 | high | yes | yes | keep | A child puts a small toy inside a box |
| M107 | high | yes | yes | keep | A child puts a large toy beside a box because it does not fit inside |
| M108 | high | yes | yes | keep | A child places a ball under a chair |
| M109 | high | yes | yes | keep | A child places a ball on top of a chair |
| M110 | medium | maybe | defer | keep | A child places one block between two other blocks |
| M111 | medium | maybe | defer | keep | A child places one cup next to another cup |
| M112 | medium | maybe | defer | keep | A child places one toy far away from another toy |
| M113 | high | yes | yes | keep | A child follows arrows through a simple floor path |
| M114 | high | yes | yes | keep | A child reaches a blocked part of a floor path |
| M115 | medium | maybe | defer | keep | A child turns left at a marker and right at another marker |
| M116 | high | maybe | defer | keep | A child sees a triangle rotated on a page |
| M117 | medium | maybe | defer | keep | A child sees a square rotated on a page |
| M118 | high | maybe | defer | keep | A child sees a shape reflected in a mirror |
| M119 | high | yes | yes | keep | A child joins two half-circle pieces into a circle |
| M120 | high | maybe | defer | keep | A child breaks a square cracker into two pieces |
| M121 | high | maybe | defer | keep | A child covers a picture with matching puzzle pieces |
| M122 | high | maybe | defer | keep | A child leaves a gap while covering a picture with puzzle pieces |
| M123 | medium | maybe | defer | keep | A child fills a rectangular tray with square tiles |
| M124 | medium | maybe | defer | keep | A child fills part of a rectangular tray and leaves one corner empty |
| M125 | medium | maybe | defer | keep | A child draws a path from home to school on a simple map |
| M126 | high | yes | yes | keep | A child compares a full glass and a half-full glass |
| M127 | high | yes | yes | keep | A child compares a tall thin glass and a short wide glass with the same water |
| M128 | high | yes | yes | keep | A child compares two ropes by placing their ends together |
| M129 | high | maybe | defer | keep | A child compares two sticks without lining up their ends |
| M130 | high | yes | yes | keep | A child uses hand spans to measure a table |
| M131 | high | maybe | defer | keep | Two children use different hand spans to measure the same table |
| M132 | high | yes | yes | keep | A child uses the same block repeatedly to measure a shelf |
| M133 | high | yes | yes | keep | A child leaves gaps while using blocks to measure a shelf |
| M134 | high | maybe | defer | keep | A child weighs two bags by holding one in each hand |
| M135 | high | yes | yes | keep | A child sees a heavy small stone and a light large sponge |
| M136 | medium | maybe | defer | keep | A child pours water from one cup into a measuring cup |
| M137 | medium | maybe | defer | keep | A child fills a spoon, a cup, and a bucket with sand |
| M138 | medium | maybe | defer | keep | A child compares two sounds, one quiet and one loud |
| M139 | high | maybe | defer | keep | A child compares two waits, one short and one long |
| M140 | high | maybe | defer | keep | A child checks whether a pencil fits inside a pencil box |
| M141 | low | no | no | candidate | A child sees a thermometer reading before and after fever medicine |
| M142 | low | no | no | candidate | A child sees a clock before school and after school |
| M143 | medium | maybe | defer | keep | A child estimates whether a pile has enough cups for all guests |
| M144 | medium | maybe | defer | keep | A child checks an estimate by handing out the cups |
| M145 | low | no | no | candidate | A child compares the price tags of two small items |
| M146 | high | yes | yes | keep | A child arranges beads red, blue, red, blue |
| M147 | high | yes | yes | keep | A child arranges beads red, blue, green, red, blue, green |
| M148 | high | yes | yes | keep | A child continues a clap, clap, pause rhythm |
| M149 | medium | maybe | defer | keep | A child continues a step, jump, step, jump movement game |
| M150 | high | yes | yes | keep | A child sees one missing bead in the middle of a color pattern |
| M151 | high | maybe | defer | keep | A child notices a pattern changes after several repetitions |
| M152 | high | maybe | defer | keep | A child repeats a tower pattern of one large block and two small blocks |
| M153 | high | maybe | defer | keep | A child copies a tile pattern from a picture |
| M154 | medium | maybe | defer | keep | A child makes a border pattern around a drawing |
| M155 | medium | maybe | defer | keep | A child hears a song line repeated with one word changed |
| M156 | high | maybe | defer | keep | A child sees days on a weekly calendar repeat after Sunday |
| M157 | medium | maybe | defer | keep | A child sees morning, afternoon, night, and morning again |
| M158 | medium | maybe | defer | keep | A child sees a rotating fan blade return to the same position |
| M159 | medium | maybe | defer | keep | A child watches a traffic light change through a repeated cycle |
| M160 | high | yes | yes | keep | A child predicts the next picture in a repeated story sequence |
| M161 | high | yes | yes | keep | A child sees the spoken word three linked with the written symbol 3 |
| M162 | high | yes | yes | keep | A child sees three dots linked with the written symbol 3 |
| M163 | high | maybe | defer | keep | A child matches a picture of an apple with the written word apple |
| M164 | medium | maybe | defer | keep | A child matches a red mark on a chart with a red object |
| M165 | medium | maybe | defer | keep | A child follows a picture card that means wash hands |
| M166 | medium | maybe | defer | keep | A child follows an arrow sign toward a classroom |
| M167 | low | no | no | candidate | A child sees a map symbol for home placed on a map |
| M168 | high | yes | yes | keep | A child uses tally marks to record children entering a room |
| M169 | high | yes | yes | keep | A child sees a bar chart showing favorite fruits in a class |
| M170 | high | maybe | defer | keep | A child points to the tallest bar in a chart |
| M171 | low | no | no | candidate | A child uses a calendar square to mark a birthday |
| M172 | low | no | no | candidate | A child reads a bus number before getting on a bus |
| M173 | high | maybe | defer | keep | A child sees the same number used as a count and as a bus label |
| M174 | medium | maybe | defer | keep | A child follows a recipe picture that shows two spoons of sugar |
| M175 | medium | maybe | defer | keep | A child sees a score change on a game board |
| M176 | high | yes | yes | keep | A child is told that if shoes are wet, they should stay outside |
| M177 | high | yes | yes | keep | A child is told that if the light is red, they should stop |
| M178 | high | maybe | defer | keep | A child is told to take an umbrella only if it is raining |
| M179 | high | yes | yes | keep | A child is told to pick a snack that is not spicy |
| M180 | high | yes | yes | keep | A child is told to choose a toy that is both red and soft |
| M181 | high | yes | yes | keep | A child is told to choose a toy that is red or soft |
| M182 | medium | maybe | defer | keep | A child sees a closed box and is told there may be a toy inside |
| M183 | medium | maybe | defer | keep | A child opens a box and finds it empty |
| M184 | high | maybe | defer | keep | A child sees a covered cup moved after a ball is hidden under it |
| M185 | medium | maybe | defer | keep | A child sees two possible hiding places and one is checked |
| M186 | low | no | no | candidate | A child guesses which hand holds a coin |
| M187 | high | maybe | defer | keep | A child sees a bag with mostly red beads and a few blue beads |
| M188 | medium | maybe | defer | keep | A child picks one bead from a bag without looking |
| M189 | low | no | no | candidate | A child sees a spinner land on the same color several times |
| M190 | low | no | no | candidate | A child chooses between a sure small sweet and a chance of a larger sweet |
| M191 | high | maybe | defer | keep | A child pours the same water between differently shaped cups |
| M192 | high | maybe | defer | keep | A child flattens a clay ball into a pancake shape |
| M193 | high | maybe | defer | keep | A child cuts a paper square into two rectangles |
| M194 | medium | maybe | defer | keep | A child folds a paper sheet and then unfolds it |
| M195 | high | maybe | defer | keep | A child moves a toy car forward the same distance several times |
| M196 | medium | maybe | defer | keep | A child doubles a tower by adding the same number of blocks again |
| M197 | medium | maybe | defer | keep | A child halves a row of blocks by giving every second block away |
| M198 | high | maybe | defer | keep | A child changes one part of a drawing while keeping the rest the same |
| M199 | high | maybe | defer | keep | A child sees two different routes reach the same room |
| M200 | high | yes | yes | keep | A child uses the same rule on a new set of objects |
