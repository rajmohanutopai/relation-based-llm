# Everyday Physical-World Held-Out Evaluation

Status: held-out evaluation design.

Parseable file:

```text
data/developmental_graph/evaluations/everyday_physical_world_heldout.json
```

Source inventory:

```text
docs/everyday-physical-world-200-situations.md
```

Source seed:

```text
data/developmental_graph/seeds/everyday_physical_world.json
```

## Purpose

This evaluation set uses `maybe` rows from the everyday physical-world inventory
to test whether the physical seed generalizes beyond the 50 selected first-set
situations.

It should not be used as first-pass training data.

The split has two case types:

```text
transfer_probe:
  should be mostly answerable from existing physical seed motifs

gap_probe:
  intentionally reveals a relation family that may need later expansion
```

## Summary

Current held-out set:

```text
cases: 33
transfer_probe: 12
gap_probe: 21
```

All `graph_anchors` in the JSON point to existing relations in:

```text
data/developmental_graph/seeds/everyday_physical_world.json
```

## Case Map

| Case | Source rows | Type | Focus |
|---|---|---|---|
| `heldout.physical.ceramic_slip_fall` | P008 | transfer | brittle fall plus wet/slip context |
| `heldout.physical.spoon_bowl_sound_contrast` | P009, P010 | transfer | material-specific impact sound |
| `heldout.physical.ball_wall_material_contrast` | P016, P017 | transfer | hardness/elasticity under impact |
| `heldout.physical.balloon_pressure_limit` | P018, P019 | transfer | elastic deformation vs limit failure |
| `heldout.physical.heavy_light_lift` | P027, P028, P030 | transfer | load and effort |
| `heldout.physical.pull_box_string` | P032 | gap | tension or attached-pull relation |
| `heldout.physical.ladder_support` | P037, P038 | transfer | support and stability |
| `heldout.physical.door_slow_slam` | P041, P042 | gap | hinge rotation and wind force |
| `heldout.physical.lid_tight_loose` | P045, P046, P047 | gap | fit, attachment, twist open/close |
| `heldout.physical.tilt_water_rate` | P057, P058 | transfer/gap | flow rate and spill likelihood |
| `heldout.physical.drip_spray` | P061, P062 | gap | pressure-shaped flow pattern |
| `heldout.physical.mixing_material_contrast` | P067-P070 | gap | suspension, foam, thickening mixtures |
| `heldout.physical.paper_towel_absorb` | P075 | transfer | absorbent material |
| `heldout.physical.freezing_water` | P079 | gap | freezing as phase-change counterpart |
| `heldout.physical.sunlight_heating` | P083, P085 | gap | radiant heat and color absorption |
| `heldout.physical.candle_covered` | P089 | gap | combustion air requirement |
| `heldout.physical.condensation_bottle` | P093 | gap | condensation |
| `heldout.physical.drying_clothes` | P094, P095 | gap | evaporation/drying and airflow |
| `heldout.physical.scissors_cut_material` | P105, P106 | transfer | sharp-edge cutting |
| `heldout.physical.paper_tear` | P108 | gap | tearing vs cutting |
| `heldout.physical.glue_joining` | P120 | gap | adhesion/joining |
| `heldout.physical.nail_screw_wood` | P123, P124 | gap | insertion and threaded fastening |
| `heldout.physical.lever_pulley` | P135, P137, P138 | gap | pulley and rope tension |
| `heldout.physical.magnet_polarity` | P151, P152 | gap | magnetic polarity and orientation |
| `heldout.physical.light_reflection_transmission` | P155, P156, P158 | gap | light transmission and reflection |
| `heldout.physical.refraction_shadow` | P160-P162 | gap | refraction and shadow geometry |
| `heldout.physical.sound_echo_damping` | P168, P173-P176 | gap | sound propagation, echo, damping |
| `heldout.physical.sieve_filtering` | P183, P184 | gap | particle-size filtering |
| `heldout.physical.visibility_containment` | P185, P187, P188 | gap | containment vs visibility |
| `heldout.physical.torn_basket_container` | P190 | transfer/gap | solid contents through openings |
| `heldout.physical.rain_soil_mud` | P191, P195 | transfer | water-soil absorption and mud state |
| `heldout.physical.wind_curtain` | P193 | gap | wind force on flexible object |
| `heldout.physical.loose_gravel_walk` | P199 | transfer/gap | traction plus loose granular support |

## Use In Experiments

The first training experiment should train on generated examples from:

```text
data/developmental_graph/seeds/everyday_physical_world.json
```

Then evaluate on:

```text
data/developmental_graph/evaluations/everyday_physical_world_heldout.json
```

Passing the `transfer_probe` cases suggests useful generalization from the seed.
Failing the `gap_probe` cases is acceptable at first; those failures tell us
which relation motifs to add next.
