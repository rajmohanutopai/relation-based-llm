# 200 Everyday Physical-World Situation Families

Status: raw situation inventory.

Related files:

- `plan.md`
- `docs/developmental-relation-graph.md`
- `docs/6mo-child-200-encounters.md`

## Purpose

This file lists 200 broad everyday physical-world situations that can later
become the grounded entry layer for a physical-domain relation curriculum.

This is intentionally a raw observation file. It should not explain what each
situation means, what relation the model should learn, or what abstraction it
supports. Interpretation belongs in a later relation-audit file.

Unlike the six-month child inventory, this list is not written from a child's
first-person perspective. It is still human-scale and everyday: objects,
materials, motion, force, support, containment, fluids, heat, light, sound,
damage, tools, and environment.

This is not the whole physical world. The broader domain structure is defined
in `docs/physical-world-domain-map.md`.

The list is intentionally overcomplete. Later we should run a prioritisation
pass and choose the highest-value 30-50 situation families for the first
physical-world dataset.

## Workflow Fields

These fields are operational only. They do not describe what the situation
means.

```text
priority:
  unscored | high | medium | low | exclude

include in first physical set:
  undecided | yes | no | maybe

include in relation conversion:
  undecided | yes | no | defer

status:
  candidate | keep | needs_split | needs_merge | remove
```

## Prioritisation Criteria

This first pass used operational criteria only:

```text
coverage of reusable physical principles
frequency in ordinary text and everyday experience
counterfactual usefulness
variation potential for generated examples
importance for later domains such as medicine, tools, safety, and science
avoidance of overly narrow or duplicate first-set rows
```

Interpretation should still happen outside this raw file. This section only
records workflow priority.

## Prioritisation Summary

First pass, intentionally set to exactly 50 first-set items. Counts:

```text
priority high: 50
priority medium: 78
priority low: 72
include in first physical set yes: 50
include in first physical set maybe: 78
include in first physical set no: 72
include in relation conversion yes: 50
include in relation conversion defer: 150
include in relation conversion no: 0
status keep: 128
status candidate: 72
```

The `yes` rows are the first physical-world relation-audit candidates. The
`maybe` rows are useful second-tier contrast or extension cases. The `no` rows
are not rejected permanently; they are deferred to keep the first experiment
small.

## The 200 Situations

| ID | Priority | Include in first physical set | Include in relation conversion | Status | Physical-world situation |
|---:|---|---|---|---|---|
| P001 | medium | maybe | defer | keep | A glass cup rests on a table |
| P002 | medium | maybe | defer | keep | A glass cup is pushed near the edge of a table |
| P003 | high | yes | yes | keep | A glass cup falls from a table onto a hard floor |
| P004 | high | yes | yes | keep | A plastic cup falls from a table onto a hard floor |
| P005 | high | yes | yes | keep | A steel tumbler falls from a table onto a hard floor |
| P006 | low | no | defer | candidate | A paper cup is squeezed by hand |
| P007 | low | no | defer | candidate | A ceramic plate is placed flat on a table |
| P008 | medium | maybe | defer | keep | A ceramic plate slips from wet hands |
| P009 | medium | maybe | defer | keep | A metal spoon is dropped into a steel bowl |
| P010 | medium | maybe | defer | keep | A wooden spoon is dropped into a steel bowl |
| P011 | medium | maybe | defer | keep | A rubber ball is placed on a flat floor |
| P012 | high | yes | yes | keep | A rubber ball is pushed across a smooth floor |
| P013 | high | yes | yes | keep | A rubber ball is pushed across a rough mat |
| P014 | low | no | defer | candidate | A stone is pushed across a smooth floor |
| P015 | high | yes | yes | keep | A sponge ball is squeezed by hand |
| P016 | medium | maybe | defer | keep | A hard cricket ball hits a wall |
| P017 | medium | maybe | defer | keep | A tennis ball hits a wall |
| P018 | medium | maybe | defer | keep | A balloon is pressed between two hands |
| P019 | medium | maybe | defer | keep | A balloon is overfilled with air |
| P020 | low | no | defer | candidate | A balloon is released without tying its mouth |
| P021 | medium | maybe | defer | keep | A wooden block rests on another wooden block |
| P022 | medium | maybe | defer | keep | Several wooden blocks are stacked upward |
| P023 | high | yes | yes | keep | A tall stack of blocks is nudged sideways |
| P024 | high | yes | yes | keep | A wide stack of blocks is nudged sideways |
| P025 | low | no | defer | candidate | A book lies flat on a table |
| P026 | high | yes | yes | keep | A book is balanced halfway over a table edge |
| P027 | medium | maybe | defer | keep | A heavy book is lifted with one hand |
| P028 | medium | maybe | defer | keep | A thin notebook is lifted with one hand |
| P029 | low | no | defer | candidate | A cardboard box is empty |
| P030 | medium | maybe | defer | keep | A cardboard box is filled with books |
| P031 | high | yes | yes | keep | A cardboard box is pushed on the floor |
| P032 | medium | maybe | defer | keep | A cardboard box is pulled with a string |
| P033 | high | yes | yes | keep | A chair is pushed on a tiled floor |
| P034 | high | yes | yes | keep | A chair is pushed on a carpet |
| P035 | medium | maybe | defer | keep | A table with four legs stands on level ground |
| P036 | high | yes | yes | keep | A table stands with one leg shorter than the others |
| P037 | medium | maybe | defer | keep | A ladder leans against a wall |
| P038 | medium | maybe | defer | keep | A ladder is placed on uneven ground |
| P039 | medium | maybe | defer | keep | A door is pushed open |
| P040 | low | no | defer | candidate | A door is pulled open |
| P041 | medium | maybe | defer | keep | A door closes slowly on its hinge |
| P042 | medium | maybe | defer | keep | A door slams shut in wind |
| P043 | low | no | defer | candidate | A drawer is pulled out |
| P044 | low | no | defer | candidate | A drawer is pushed in |
| P045 | medium | maybe | defer | keep | A lid is placed on a jar |
| P046 | medium | maybe | defer | keep | A tight lid is twisted open |
| P047 | medium | maybe | defer | keep | A loose lid falls off a container |
| P048 | low | no | defer | candidate | A key is inserted into a lock |
| P049 | low | no | defer | candidate | A key is turned inside a lock |
| P050 | low | no | defer | candidate | A zip is pulled upward on a bag |
| P051 | high | yes | yes | keep | Water is poured into an empty glass |
| P052 | high | yes | yes | keep | Water is poured into a glass that is already full |
| P053 | low | no | defer | candidate | Water is poured onto a plate |
| P054 | high | yes | yes | keep | Water is poured onto a cloth |
| P055 | high | yes | yes | keep | Water is poured onto dry soil |
| P056 | low | no | defer | candidate | Water is poured onto a plastic sheet |
| P057 | medium | maybe | defer | keep | A glass of water is tilted slowly |
| P058 | medium | maybe | defer | keep | A glass of water is tilted quickly |
| P059 | high | yes | yes | keep | Water flows through a pipe |
| P060 | high | yes | yes | keep | A pipe is blocked by a plug |
| P061 | medium | maybe | defer | keep | Water drips from a leaking tap |
| P062 | medium | maybe | defer | keep | Water sprays from a hose nozzle |
| P063 | low | no | defer | candidate | A bucket is filled under a tap |
| P064 | high | yes | yes | keep | A bucket with a hole leaks water |
| P065 | high | yes | yes | keep | Oil is poured into water |
| P066 | high | yes | yes | keep | Salt is stirred into water |
| P067 | medium | maybe | defer | keep | Sugar is stirred into hot tea |
| P068 | medium | maybe | defer | keep | Sand is stirred into water |
| P069 | medium | maybe | defer | keep | Flour is mixed with water |
| P070 | medium | maybe | defer | keep | Soap is rubbed with water |
| P071 | high | yes | yes | keep | A dry sponge is placed in water |
| P072 | high | yes | yes | keep | A wet sponge is squeezed |
| P073 | low | no | defer | candidate | A dry towel wipes a wet table |
| P074 | low | no | defer | candidate | A wet towel wipes a dusty table |
| P075 | medium | maybe | defer | keep | A paper towel is placed on spilled water |
| P076 | low | no | defer | candidate | A plastic bag is filled with water |
| P077 | low | no | defer | candidate | A plastic bag with a small hole is filled with water |
| P078 | high | yes | yes | keep | Ice is placed in a glass of water |
| P079 | medium | maybe | defer | keep | Water is placed in a freezer |
| P080 | high | yes | yes | keep | Steam rises from boiling water |
| P081 | high | yes | yes | keep | A metal spoon is placed in hot tea |
| P082 | high | yes | yes | keep | A wooden spoon is placed in hot tea |
| P083 | medium | maybe | defer | keep | A steel plate is left in sunlight |
| P084 | low | no | defer | candidate | A white cloth is left in sunlight |
| P085 | medium | maybe | defer | keep | A black cloth is left in sunlight |
| P086 | low | no | defer | candidate | A hot pan touches a plastic handle |
| P087 | medium | maybe | defer | keep | A hot pan touches a wet cloth |
| P088 | high | yes | yes | keep | A candle flame touches paper |
| P089 | medium | maybe | defer | keep | A candle flame is covered by a glass |
| P090 | low | no | defer | candidate | A matchstick is struck on a matchbox |
| P091 | low | no | defer | candidate | A cold bottle is taken out of a refrigerator |
| P092 | low | no | defer | candidate | A cold bottle sits in warm air |
| P093 | medium | maybe | defer | keep | Water droplets appear on the outside of a cold bottle |
| P094 | medium | maybe | defer | keep | Wet clothes are hung in sunlight |
| P095 | medium | maybe | defer | keep | Wet clothes are hung in a closed room |
| P096 | medium | maybe | defer | keep | Rice is cooked in boiling water |
| P097 | low | no | defer | candidate | Milk is heated in a vessel |
| P098 | low | no | defer | candidate | Milk is left outside for many hours |
| P099 | medium | maybe | defer | keep | Dough is kneaded by hand |
| P100 | medium | maybe | defer | keep | Batter is spread on a hot pan |
| P101 | high | yes | yes | keep | A knife presses into a tomato |
| P102 | high | yes | yes | keep | A spoon presses into a tomato |
| P103 | low | no | defer | candidate | A knife presses into a wooden board |
| P104 | high | yes | yes | keep | A blunt knife presses into a tomato |
| P105 | medium | maybe | defer | keep | Scissors cut paper |
| P106 | medium | maybe | defer | keep | Scissors cut cloth |
| P107 | low | no | defer | candidate | Scissors try to cut a metal spoon |
| P108 | medium | maybe | defer | keep | Paper is torn by hand |
| P109 | low | no | defer | candidate | Cloth is torn by hand |
| P110 | low | no | defer | candidate | Plastic wrapper is torn open |
| P111 | high | yes | yes | keep | A rubber band is stretched |
| P112 | high | yes | yes | keep | A rubber band is stretched too far |
| P113 | high | yes | yes | keep | A spring is compressed |
| P114 | high | yes | yes | keep | A spring is released after compression |
| P115 | high | yes | yes | keep | Clay is pressed into a new shape |
| P116 | low | no | defer | candidate | Wet clay is left to dry |
| P117 | low | no | defer | candidate | Chalk is pressed against a blackboard |
| P118 | high | yes | yes | keep | A pencil tip presses against paper |
| P119 | low | no | defer | candidate | An eraser rubs a pencil mark |
| P120 | medium | maybe | defer | keep | Glue is applied between two paper sheets |
| P121 | low | no | defer | candidate | Tape is pressed onto a cardboard box |
| P122 | low | no | defer | candidate | Tape is pulled off paper |
| P123 | medium | maybe | defer | keep | A nail is hit into wood with a hammer |
| P124 | medium | maybe | defer | keep | A screw is turned into wood with a screwdriver |
| P125 | low | no | defer | candidate | A nut is tightened onto a bolt |
| P126 | low | no | defer | candidate | A rope is tied around a bundle |
| P127 | low | no | defer | candidate | A knot is pulled tighter |
| P128 | low | no | defer | candidate | A knot is untied |
| P129 | high | yes | yes | keep | A wheel rolls on an axle |
| P130 | low | no | defer | candidate | A bicycle wheel spins while lifted off the ground |
| P131 | low | no | defer | candidate | A bicycle wheel rolls on the road |
| P132 | high | yes | yes | keep | Brakes are pressed on a moving bicycle wheel |
| P133 | high | yes | yes | keep | A cart is pushed with heavy items inside |
| P134 | high | yes | yes | keep | An empty cart is pushed |
| P135 | medium | maybe | defer | keep | A seesaw has equal weight on both sides |
| P136 | high | yes | yes | keep | A seesaw has more weight on one side |
| P137 | medium | maybe | defer | keep | A lever lifts a stone from one end |
| P138 | medium | maybe | defer | keep | A pulley lifts a bucket with a rope |
| P139 | low | no | defer | candidate | A gear turns another gear |
| P140 | medium | maybe | defer | keep | A fan blade rotates in air |
| P141 | low | no | defer | candidate | A paper sheet is held in front of a fan |
| P142 | low | no | defer | candidate | Dust is blown by wind |
| P143 | low | no | defer | candidate | A kite is pulled by wind |
| P144 | low | no | defer | candidate | A leaf floats down from a tree |
| P145 | high | yes | yes | keep | A feather falls through still air |
| P146 | high | yes | yes | keep | A stone falls through still air |
| P147 | low | no | defer | candidate | A paper plane is thrown forward |
| P148 | low | no | defer | candidate | A paper ball is thrown forward |
| P149 | high | yes | yes | keep | A magnet is brought near iron pins |
| P150 | high | yes | yes | keep | A magnet is brought near a wooden pencil |
| P151 | medium | maybe | defer | keep | Two magnets are brought together one way |
| P152 | medium | maybe | defer | keep | Two magnets are brought together the opposite way |
| P153 | high | yes | yes | keep | A switch is turned on for a light |
| P154 | low | no | defer | candidate | A switch is turned off for a light |
| P155 | medium | maybe | defer | keep | A torch shines on a wall |
| P156 | medium | maybe | defer | keep | A torch shines through clear glass |
| P157 | low | no | defer | candidate | A torch shines through frosted glass |
| P158 | medium | maybe | defer | keep | A torch shines on a mirror |
| P159 | low | no | defer | candidate | A mirror is tilted while reflecting light |
| P160 | medium | maybe | defer | keep | A stick is partly placed in water |
| P161 | medium | maybe | defer | keep | A shadow forms when a hand blocks sunlight |
| P162 | medium | maybe | defer | keep | A shadow changes when a light source moves |
| P163 | low | no | defer | candidate | A red object is seen under white light |
| P164 | low | no | defer | candidate | A red object is seen under colored light |
| P165 | low | no | defer | candidate | A loudspeaker plays a low sound |
| P166 | low | no | defer | candidate | A loudspeaker plays a high sound |
| P167 | high | yes | yes | keep | A drum is hit softly |
| P168 | medium | maybe | defer | keep | A drum is hit hard |
| P169 | low | no | defer | candidate | A metal plate is tapped |
| P170 | low | no | defer | candidate | A wooden table is tapped |
| P171 | low | no | defer | candidate | A glass bottle is tapped when empty |
| P172 | low | no | defer | candidate | A glass bottle is tapped when filled with water |
| P173 | medium | maybe | defer | keep | A sound is heard in an empty room |
| P174 | medium | maybe | defer | keep | A sound is heard in a room with curtains and cushions |
| P175 | medium | maybe | defer | keep | A phone vibrates on a wooden table |
| P176 | medium | maybe | defer | keep | A phone vibrates on a soft bed |
| P177 | low | no | defer | candidate | Rice grains are poured into a bowl |
| P178 | low | no | defer | candidate | Rice grains are poured onto a flat plate |
| P179 | low | no | defer | candidate | Sand is poured through fingers |
| P180 | low | no | defer | candidate | Sand is packed into a cup and turned over |
| P181 | low | no | defer | candidate | Pebbles are poured into a jar |
| P182 | low | no | defer | candidate | Pebbles and sand are poured into the same jar |
| P183 | medium | maybe | defer | keep | A sieve is used with flour |
| P184 | medium | maybe | defer | keep | A sieve is used with pebbles |
| P185 | medium | maybe | defer | keep | A small object is placed inside a closed box |
| P186 | low | no | defer | candidate | A small object is placed under a cloth |
| P187 | medium | maybe | defer | keep | A transparent bottle contains a coin |
| P188 | medium | maybe | defer | keep | An opaque bottle contains a coin |
| P189 | low | no | defer | candidate | A basket holds many fruits |
| P190 | medium | maybe | defer | keep | A torn basket holds many fruits |
| P191 | medium | maybe | defer | keep | Rain falls on dry ground |
| P192 | low | no | defer | candidate | Rain falls on a metal roof |
| P193 | medium | maybe | defer | keep | Wind moves a curtain near an open window |
| P194 | low | no | defer | candidate | Wind moves a heavy wooden door slightly |
| P195 | medium | maybe | defer | keep | Mud forms where water mixes with soil |
| P196 | low | no | defer | candidate | A vehicle wheel moves through mud |
| P197 | low | no | defer | candidate | A person walks on dry floor tiles |
| P198 | high | yes | yes | keep | A person walks on wet floor tiles |
| P199 | medium | maybe | defer | keep | A person walks on loose gravel |
| P200 | low | no | defer | candidate | A person walks up a staircase |

## Coverage Areas

The list is grouped roughly across these areas:

```text
objects, shape, support, and everyday containers: P001-P050
fluids, wetness, mixing, and phase/state changes: P051-P100
cutting, deformation, joining, tools, and machines: P101-P140
air, falling, magnetism, light, and reflection: P141-P164
sound, vibration, granular materials, containment, and environment: P165-P200
```

## Separation Rule

Do not add inferred learning targets to this file.

Later passes may create separate files such as:

```text
docs/physical-world-top-relations-audit.md
docs/physical-world-micro-experiences.md
data/developmental_graph/annotations/physical_world_*.json
```

Those derived files can extract relations, counterfactuals, prediction changes,
material behavior, valence/risk where relevant, language overlays, and training
examples. This file should remain the clean situation inventory.

## Later Refinement

Later, revise scores only if the relation audit shows missing coverage or too much duplication.

Possible prioritisation dimensions:

```text
frequency in everyday life
coverage of reusable physical principles
variation potential
counterfactual usefulness
importance for later domains
safety or risk relevance
ease of generating controlled examples
```

The first executable physical dataset should start with the 50 rows currently marked `yes`.
