# Everyday Physical-World Top-50 Relation Audit

Status: derived relation audit.

Source inventory: `docs/everyday-physical-world-200-situations.md`

Related map: `docs/physical-world-domain-map.md`

## Purpose

This file reviews the 50 everyday physical-world situations currently marked:

```text
Include in first physical set = yes
```

This is intentionally separate from the raw situation inventory. The raw file
should remain observational. This file is where relation interpretation and
graph coverage checking belongs.

## Summary

The current 6-month seed graph already covers a few low-level physical motifs:

```text
drop -> impact -> sound
round object + push -> rolling
hard/soft contrast
supported/unsupported
body balance
temperature comfort
light change
sound intensity
```

But it is still a child-world seed, not a physical-domain graph. The top-50
physical situations show that the first physical extension should add reusable
external-world relation families rather than one node per situation.

Implementation status:

```text
Added to data/developmental_graph/seeds/everyday_physical_world.json
```

The main missing physical relation families are:

```text
material-specific fall/impact outcomes
surface friction and traction
object stability and support geometry
container fill, overflow, leak, and blocked flow
absorption and porosity
immiscible separation and dissolving
thermal phase change and heat transfer
combustion
edge-pressure cutting and blunt contrast
elasticity, elastic limit, spring release, and plastic deformation
wheel/axle, braking, load, and lever balance
air resistance during fall
magnetic material selectivity
switch/circuit/light activation
sound intensity from impact force
wet-surface slipping risk
```

## Coverage Table

Coverage values:

```text
covered = already represented well enough in the seed graph
partial = represented indirectly, but needs refinement
missing = not yet represented clearly enough
```

| ID | Situation | Relation families visible | Coverage | Gap or action |
|---:|---|---|---|---|
| P003 | A glass cup falls from a table onto a hard floor | unsupported object, falling, impact, brittleness, sound, possible break | partial | Drop-sound exists; add material-specific impact/break outcomes. |
| P004 | A plastic cup falls from a table onto a hard floor | falling, impact, plastic deformation or bounce, lower break risk | partial | Add material contrast under same fall event. |
| P005 | A steel tumbler falls from a table onto a hard floor | falling, hard metal impact, loud sound, low break risk | partial | Existing steel bowl sound helps; generalize to metal material outcome. |
| P012 | A rubber ball is pushed across a smooth floor | push, rolling, low friction, elastic round object | partial | Push-roll exists; add surface friction as modifier. |
| P013 | A rubber ball is pushed across a rough mat | push, rolling, rough surface, friction, slower motion | partial | Need rough/smooth contrast and friction effect. |
| P015 | A sponge ball is squeezed by hand | pressure, deformation, softness, shape recovery or partial recovery | partial | Soft exists; add deformation and porous/sponge behavior. |
| P023 | A tall stack of blocks is nudged sideways | stacked support, height, instability, tipping | partial | Body balance exists; add object-stack stability. |
| P024 | A wide stack of blocks is nudged sideways | stacked support, wider base, stability under nudge | partial | Add support-base contrast. |
| P026 | A book is balanced halfway over a table edge | partial support, overhang, tipping/falling risk | partial | Add object center-of-support relation. |
| P031 | A cardboard box is pushed on the floor | push, sliding, friction, mass/load if present | missing | Add generic push-slide and effort relation. |
| P033 | A chair is pushed on a tiled floor | push, sliding, low friction, sound/resistance | missing | Add surface-dependent sliding. |
| P034 | A chair is pushed on a carpet | push, high friction, higher resistance, lower sliding | missing | Add carpet/rough-surface resistance contrast. |
| P036 | A table stands with one leg shorter than the others | support inequality, wobble, instability | partial | Add uneven support and wobble schema. |
| P051 | Water is poured into an empty glass | liquid flow, container, fill level | missing | Add pour/fill/container schema. |
| P052 | Water is poured into a glass that is already full | liquid flow, capacity, overflow, spill | missing | Add capacity/overflow relation. |
| P054 | Water is poured onto a cloth | liquid contact, absorption, wetness spread | partial | Wetness exists; add absorption/porosity. |
| P055 | Water is poured onto dry soil | liquid contact, absorption, mud/soil change | missing | Add porous/granular absorption and state change. |
| P059 | Water flows through a pipe | flow path, containment, direction, pressure | missing | Add constrained flow/path schema. |
| P060 | A pipe is blocked by a plug | blockage, stopped flow, obstacle in path | missing | Add blocked-flow relation. |
| P064 | A bucket with a hole leaks water | container failure, opening, leak, lowering fill | missing | Add leak-through-opening schema. |
| P065 | Oil is poured into water | liquid-liquid contact, non-mixing, separation | missing | Add immiscibility/separation relation. |
| P066 | Salt is stirred into water | solid-liquid contact, dissolving, mixing | missing | Add dissolving relation. |
| P071 | A dry sponge is placed in water | porous material, absorption, water uptake | missing | Add sponge/porous absorption. |
| P072 | A wet sponge is squeezed | pressure, water release, deformation, recovery | missing | Add squeeze-release for absorbed liquid. |
| P078 | Ice is placed in a glass of water | solid water, temperature difference, melting | missing | Add phase-change/heat exchange. |
| P080 | Steam rises from boiling water | heat, boiling, phase change, upward vapor motion | missing | Add boiling/evaporation relation. |
| P081 | A metal spoon is placed in hot tea | heat transfer, conduction, material difference | missing | Add thermal conduction for metal. |
| P082 | A wooden spoon is placed in hot tea | heat transfer, insulation, material contrast | missing | Add conductor/insulator contrast. |
| P088 | A candle flame touches paper | flame, heat, flammable material, burning | missing | Add combustion/burn transformation. |
| P101 | A knife presses into a tomato | sharp edge, pressure, soft target, cutting | missing | Add edge-pressure-cut schema. |
| P102 | A spoon presses into a tomato | blunt object, pressure, deformation without clean cut | missing | Add blunt-pressure contrast. |
| P104 | A blunt knife presses into a tomato | weak sharpness, higher force needed, poor cutting | missing | Add degree of sharpness and threshold. |
| P111 | A rubber band is stretched | tension, elastic deformation, stored energy | missing | Add elastic stretch relation. |
| P112 | A rubber band is stretched too far | elastic limit, breaking or permanent damage | missing | Add elastic-limit failure. |
| P113 | A spring is compressed | compression, stored elastic energy | missing | Add spring compression. |
| P114 | A spring is released after compression | release, elastic return, motion | missing | Add elastic release/action effect. |
| P115 | Clay is pressed into a new shape | pressure, plastic deformation, shape retention | missing | Add non-elastic deformation. |
| P118 | A pencil tip presses against paper | pointed tip, pressure, mark formation | missing | Add marking/trace relation. |
| P129 | A wheel rolls on an axle | rotation, axle constraint, rolling support | missing | Add wheel/axle rotation schema. |
| P132 | Brakes are pressed on a moving bicycle wheel | friction, motion reduction, stopping | missing | Add braking/friction-to-stop schema. |
| P133 | A cart is pushed with heavy items inside | load, effort, inertia, rolling resistance | missing | Add load-effort relation. |
| P134 | An empty cart is pushed | lower load, lower effort, easier motion | missing | Add load contrast with P133. |
| P136 | A seesaw has more weight on one side | unequal load, rotation around pivot, tilt | missing | Add lever/pivot balance. |
| P145 | A feather falls through still air | falling, air resistance, low mass/large surface, slow descent | missing | Add air-resistance fall contrast. |
| P146 | A stone falls through still air | falling, low air-resistance effect, faster descent | missing | Add mass/drag contrast with feather. |
| P149 | A magnet is brought near iron pins | magnetic attraction, material selectivity | missing | Add magnetism/material-selective attraction. |
| P150 | A magnet is brought near a wooden pencil | magnet near non-magnetic material, no attraction | missing | Add non-magnetic contrast. |
| P153 | A switch is turned on for a light | switch state, circuit/device activation, light output | partial | Light-change exists; add circuit/switch causation. |
| P167 | A drum is hit softly | impact, vibration, sound, lower amplitude | partial | Sound intensity exists; add force-to-amplitude relation. |
| P198 | A person walks on wet floor tiles | wet surface, reduced traction, slipping risk | missing | Add wet-surface traction/slip relation. |

## Relation Families To Add

The following should become the first physical-domain graph extension. Names are
proposed IDs, not final commitments.

### 1. Fall, Impact, and Material Outcome

Needed for:

```text
P003 glass cup falls
P004 plastic cup falls
P005 steel tumbler falls
```

Proposed additions:

```text
schema.object_fall_impact
schema.material_impact_outcome
property.fragile
property.brittle
property.metallic_resonance
property.plastic_deformable
event.break_fragment
```

This should generalize the child seed's `schema.drop_sound` into a richer
physical relation: same fall event, different material outcome.

### 2. Surface Friction, Rolling, Sliding, and Traction

Needed for:

```text
P012 rubber ball on smooth floor
P013 rubber ball on rough mat
P031 cardboard box pushed
P033 chair on tiled floor
P034 chair on carpet
P198 person on wet floor tiles
```

Proposed additions:

```text
schema.surface_friction_motion
schema.push_slide_resistance
schema.slippery_surface_traction
property.smooth_surface
property.rough_surface
property.slippery_wet_surface
property.high_friction
property.low_friction
```

### 3. Object Support, Balance, and Stability

Needed for:

```text
P023 tall stack nudged
P024 wide stack nudged
P026 book halfway over edge
P036 table with short leg
```

Proposed additions:

```text
schema.object_stack_stability
schema.partial_support_tipping
schema.uneven_support_wobble
invariant.support_base
invariant.center_of_support
property.tall_narrow
property.wide_stable
```

This should reuse the infant graph's support/balance ideas, but extend them to
external objects rather than body posture.

### 4. Containers, Flow, Overflow, Leak, and Blockage

Needed for:

```text
P051 water into empty glass
P052 water into full glass
P059 water through pipe
P060 pipe blocked
P064 bucket with hole leaks
```

Proposed additions:

```text
schema.pour_fill_container
schema.capacity_overflow
schema.constrained_flow_path
schema.blocked_flow
schema.leak_through_opening
property.container_capacity
property.opening
property.blockage
```

### 5. Absorption, Porosity, Mixing, and Separation

Needed for:

```text
P054 water onto cloth
P055 water onto dry soil
P065 oil into water
P066 salt into water
P071 dry sponge in water
P072 wet sponge squeezed
```

Proposed additions:

```text
schema.absorption_porosity
schema.squeeze_release_liquid
schema.immiscible_separation
schema.dissolution_mixing
property.porous
property.absorbent
property.immiscible
property.soluble
```

### 6. Heat, Phase Change, Conduction, and Combustion

Needed for:

```text
P078 ice in water
P080 steam from boiling water
P081 metal spoon in hot tea
P082 wooden spoon in hot tea
P088 flame touches paper
```

Proposed additions:

```text
schema.heat_transfer
schema.phase_change_melting
schema.boiling_vapor_rise
schema.thermal_conduction_material
schema.combustion_flammable_material
property.thermal_conductor
property.thermal_insulator
property.flammable
```

### 7. Cutting, Marking, and Pressure Thresholds

Needed for:

```text
P101 knife presses tomato
P102 spoon presses tomato
P104 blunt knife presses tomato
P118 pencil tip presses paper
```

Proposed additions:

```text
schema.edge_pressure_cut
schema.blunt_pressure_deform
schema.point_pressure_mark
property.sharp_edge
property.blunt_edge
property.pointed_tip
property.soft_target
```

This is central for later tool understanding: same pressure action, different
edge geometry and target material.

### 8. Elasticity, Spring Behavior, and Plastic Deformation

Needed for:

```text
P111 rubber band stretched
P112 rubber band stretched too far
P113 spring compressed
P114 spring released
P115 clay pressed
```

Proposed additions:

```text
schema.elastic_stretch_return
schema.elastic_limit_failure
schema.spring_compress_release
schema.plastic_deformation_retains_shape
property.elastic
property.elastic_limit
property.plastic_deformable
```

### 9. Wheels, Brakes, Load, and Levers

Needed for:

```text
P129 wheel on axle
P132 brakes on moving bicycle wheel
P133 cart with heavy items
P134 empty cart
P136 seesaw more weight on one side
```

Proposed additions:

```text
schema.wheel_axle_rotation
schema.brake_friction_slow_stop
schema.load_inertia_effort
schema.lever_pivot_balance
property.heavy_load
property.light_load
property.pivot
```

### 10. Air Resistance, Magnetism, Switches, and Sound Amplitude

Needed for:

```text
P145 feather falls
P146 stone falls
P149 magnet near iron pins
P150 magnet near wooden pencil
P153 switch on light
P167 drum hit softly
```

Proposed additions:

```text
schema.air_resistance_fall
schema.magnet_material_selectivity
schema.switch_circuit_activation
schema.impact_force_sound_amplitude
property.magnetic_material
property.non_magnetic_material
property.low_sound_amplitude
property.high_sound_amplitude
```

## First Implementation Recommendation

Do not add all 50 situations as graph nodes.

Add a compact physical extension with roughly:

```text
schemas: 20-25
properties: 25-35
objects/material handles: 20-30
micro-experiences: 12-18
evaluation questions: 12-18
```

The first implementation should emphasize contrast pairs and counterfactuals:

```text
glass vs plastic vs steel under same fall
smooth floor vs rough mat under same push
tall stack vs wide stack under same nudge
empty container vs full container under same pour
cloth/soil/sponge/plastic under same water contact
metal spoon vs wooden spoon under same hot liquid
knife vs spoon vs blunt knife under same tomato pressure
rubber band/spring/clay under same force
heavy cart vs empty cart under same push
feather vs stone under same fall
magnet + iron vs magnet + wood
dry floor vs wet floor walking
```

These contrasts are high-value because they teach that the same event frame can
produce different outcomes when one relation changes.

## Implemented Seed

The first parseable implementation adds a separate physical-domain seed rather
than extending the 6-month child graph:

```text
data/developmental_graph/seeds/everyday_physical_world.json
```

Current seed size:

```text
nodes: 149
relations: 114
micro_experiences: 10
evaluation_questions: 14
```

The `maybe` rows from the raw inventory should now be used mainly as held-out
generalization tests.
