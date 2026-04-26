# Physical World Domain Map

Status: domain scaffold.

Related files:

- `plan.md`
- `docs/developmental-relation-graph.md`
- `docs/everyday-physical-world-200-situations.md`

## Purpose

This file defines the broader physical-world domain so that the first everyday
physical situation list does not get mistaken for the whole physical world.

The everyday list is the grounded entry layer. It gives concrete, observable,
human-scale examples. The domain map below is the larger structure into which
later physical knowledge can attach.

This file is still a scaffold, not a physics textbook. It should define the
major relation areas that a small model must eventually connect.

## Design Principle

The physical-world curriculum should move from concrete experience to broader
abstraction:

```text
everyday situation
-> reusable physical relation
-> generalized physical principle
-> mathematical or scientific formulation
```

Example:

```text
glass cup falls on hard floor
-> unsupported object moves downward and impacts
-> fragile material may break under impact
-> force, energy transfer, material failure
```

The model should not learn physics only as equations or definitions. It should
learn equations later as compact symbolic forms over relation patterns.

## Layer P0: Everyday Grounding

Human-scale, directly observable physical situations.

Examples:

```text
cup falls
ball rolls
water pours
knife cuts
cloth absorbs
door opens
light reflects
sound echoes
wet floor slips
```

Current raw inventory:

```text
docs/everyday-physical-world-200-situations.md
```

Purpose:

```text
ground physical concepts in concrete object/action/result examples
create easy counterfactuals
connect child-world learning to external-world regularities
```

## Layer P1: Primitive Physical Descriptors

These are the lowest reusable physical handles.

```text
object
part
surface
edge
point
boundary
inside/outside
position
distance
direction
path
shape
size
state
change
time
rate
quantity
```

These should connect back to Layer 0 relational invariants in the developmental
graph: same/different, before/after, near/far, more/less, supported/unsupported,
touching/not touching, expected/unexpected.

## Layer P2: Matter and Material Behavior

This layer describes what things are like and how they respond.

```text
solid
liquid
gas
granular material
powder
foam
gel
elastic material
plastic/deformable material
brittle material
hard material
soft material
viscous material
porous material
conductive material
insulating material
magnetic material
transparent material
opaque material
reflective material
absorbent material
flammable material
```

Typical relation families:

```text
pressure -> deformation
impact -> sound / damage / bounce
heat -> expansion / melting / burning / evaporation
contact with liquid -> absorption / mixing / floating / sinking
light contact -> reflection / transmission / absorption
```

## Layer P3: Motion and Mechanics

This layer covers how objects move and interact.

```text
motion
rest
speed
acceleration
force
mass
inertia
gravity
friction
support
balance
stability
falling
sliding
rolling
spinning
collision
rebound
pressure
torque
leverage
tension
compression
elastic return
vibration
```

Typical relation families:

```text
unsupported + gravity -> falling
round + push + low friction -> rolling
force + mass -> change in motion
contact + motion difference -> friction
center of mass outside support -> tipping
impact + material properties -> sound/damage/bounce
```

## Layer P4: Containment, Flow, and Mixtures

This layer covers boundaries and substance movement.

```text
container
opening
closure
leak
flow
pouring
dripping
spraying
spreading
absorption
dissolving
mixing
separation
filtering
settling
floating
sinking
evaporation
condensation
freezing
melting
boiling
```

Typical relation families:

```text
container + closed boundary -> holds contents
hole + liquid -> leak
porous material + liquid -> absorption
solute + solvent -> dissolving
different density + fluid -> floating/sinking
filter opening size + particle size -> pass/block
```

## Layer P5: Heat, Energy, and Transformation

This layer covers thermal and energy-driven change.

```text
temperature
heat transfer
cooling
warming
conduction
convection
radiation
phase change
combustion
burning
cooking
drying
melting
freezing
expansion
contraction
energy storage
energy release
work
efficiency
```

Typical relation families:

```text
hot object + contact -> heat transfer / pain risk
heat + water -> evaporation / boiling
cooling + water -> freezing
heat + food material -> cooking transformation
flame + fuel + air -> burning
insulation -> slower heat transfer
```

## Layer P6: Waves, Sound, Light, and Fields

This layer covers propagation without direct object transport.

```text
sound
vibration
frequency
amplitude
echo
resonance
light
shadow
reflection
refraction
transmission
absorption
color
electric charge
current
voltage
circuit
magnetism
field
attraction
repulsion
electromagnetic radiation
```

Typical relation families:

```text
impact/vibration -> sound
larger vibration amplitude -> louder sound
surface/material/room -> echo or damping
light + opaque object -> shadow
light + mirror -> reflection
light + transparent medium -> transmission/refraction
closed circuit + power source -> current/device action
magnet + ferromagnetic material -> attraction
```

## Layer P7: Tools, Machines, and Human Technology

This layer connects physical relations to designed systems.

```text
tool
handle
blade
wheel
axle
lever
pulley
gear
screw
spring
hinge
lock
brake
motor
pump
pipe
valve
fan
vehicle
building
bridge
sensor
computer hardware
```

Typical relation families:

```text
tool shape + material + action -> intended effect
wheel + axle -> lower sliding friction
lever + pivot -> force/distance tradeoff
gear contact -> rotation transfer
pipe + pressure difference -> flow
building structure + load -> support/failure risk
```

## Layer P8: Earth and Environment

This layer moves from household physics to natural systems.

```text
rain
wind
cloud
river
wave
soil
mud
erosion
sediment
rock
mountain
valley
weather
climate
season
day/night
tide
earthquake
fire
flood
ecosystem physical constraints
```

Typical relation families:

```text
rain + soil -> wetness/mud/flow
wind + flexible object -> motion
water flow + soil/rock -> erosion
sunlight + earth rotation -> day/night
weather patterns -> repeated environmental states
```

## Layer P9: Scale Extensions

This layer prevents the model from treating human-scale experience as the whole
physical world.

### Microscopic

```text
molecule
atom
ion
bond
crystal
cell-scale physical constraint
diffusion
osmosis
surface tension
viscosity
chemical reaction
```

### Macroscopic and Astronomical

```text
planet
moon
orbit
gravity at scale
rotation
revolution
tide
star
solar radiation
galaxy
cosmic distance
```

Typical relation families:

```text
small particles + random motion -> diffusion
molecular bonds + energy -> reaction/change
mass + gravity -> orbit/fall/tide
large distance + light speed -> delayed observation
```

## Layer P10: Mathematical and Scientific Formalization

This is where physical relations become formal.

```text
measurement
unit
variable
law
equation
graph
model
approximation
idealization
experiment
control
prediction
error
conservation
symmetry
invariance
```

Example bridge:

```text
Everyday:
  heavier cart is harder to push

Relation:
  greater mass resists change in motion

Formal:
  F = m * a
```

The curriculum should not start here, but it must eventually connect here.

## Open Design Questions

- Which physical relations are primitive enough to enter the first executable
  graph?
- Which everyday situations best cover the full physical-domain map?
- How many counterfactual pairs are needed per physical relation?
- When should symbolic equations be introduced?
- How do we distinguish everyday approximate physics from formal physics?
- How should microscopic and astronomical concepts attach to the same relation
  grammar?

## Next Step

Prioritise `docs/everyday-physical-world-200-situations.md` against this domain
map, then convert the top 30-50 everyday situations into a physical relation
audit.
