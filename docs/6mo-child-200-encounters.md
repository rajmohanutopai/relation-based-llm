# 200 Encounter Families for a 6-Month-Old Child

Status: raw encounter inventory.

Related files:

- `plan.md`
- `docs/developmental-relation-graph.md`
- `docs/seed-agent-6mo-indian-child.md`
- `data/developmental_graph/seeds/agent_6mo_indian_child.json`

## Purpose

This file lists 200 broad things a 6-month-old child may encounter or
experience.

This is intentionally a raw observation file. It does not interpret what each
event means. Interpretation should happen later in a separate annotation pass,
so the raw experience data does not get polluted by our theory.

This is not medical advice or a milestone checklist. It is a modeling scaffold.
Real children vary by health, temperament, family routine, culture, household,
and environment.

The list is intentionally overcomplete. Later we should run a prioritisation
pass and choose the highest-value 30 encounter families for the first executable
dataset.

## Workflow Fields

These fields are operational only. They do not describe what the event means.

```text
priority:
  unscored | high | medium | low | exclude

include in top 30:
  undecided | yes | no | maybe

include in relation conversion:
  undecided | yes | no | defer

status:
  candidate | keep | needs_split | needs_merge | remove
```

## Prioritisation Criteria

This first pass used operational criteria only:

```text
frequency in daily life
importance for routine care
coverage of body, object, caregiver, language, and environment experience
usefulness for producing varied later episodes
safety or health relevance
whether the row is too broad and should be split before conversion
```


## Prioritisation Summary

First pass, intentionally not forced to exactly 30. Counts:

```text
priority high: 86
priority medium: 98
priority low: 16
include in top 30 yes: 44
include in top 30 maybe: 42
include in top 30 no: 114
include in relation conversion yes: 84
include in relation conversion defer: 100
include in relation conversion no: 16
status keep: 173
status needs_split: 11
status candidate: 16
```

Interpretation should still happen outside this raw file. This section only
records workflow priority.

## The 200 Encounters

| ID | Priority | Include in top 30 | Include in relation conversion | Status | What the child may encounter or experience |
|---:|---|---|---|---|---|
| E001 | high | maybe | yes | keep | Waking from sleep in a familiar sleeping place |
| E002 | high | yes | yes | keep | Waking and finding no caregiver immediately visible |
| E003 | high | yes | yes | keep | Being picked up after waking |
| E004 | medium | no | defer | keep | Being greeted after waking |
| E005 | low | no | no | candidate | Stretching, yawning, or rubbing face after sleep |
| E006 | high | maybe | yes | keep | Crying or fussing after waking |
| E007 | medium | no | defer | keep | Falling asleep while being held |
| E008 | medium | no | defer | keep | Falling asleep while being rocked |
| E009 | medium | no | defer | keep | Falling asleep during or after feeding |
| E010 | medium | no | defer | keep | Briefly waking and going back to sleep |
| E011 | medium | no | defer | keep | Being moved while asleep |
| E012 | medium | no | defer | keep | Being placed down after being asleep in arms |
| E013 | high | maybe | yes | keep | Waking because of sound, light, temperature, or movement |
| E014 | low | no | no | candidate | Short nap ending earlier than usual |
| E015 | low | no | no | candidate | Long nap ending with hunger or wetness |
| E016 | medium | no | defer | keep | Night waking in a dark or dim room |
| E017 | medium | no | defer | keep | Daytime waking with household activity nearby |
| E018 | high | maybe | yes | keep | Sleepy fussing before a nap |
| E019 | high | maybe | yes | keep | Being soothed with reduced sound and light |
| E020 | medium | no | defer | keep | Regular bedtime or nap routine |
| E021 | high | yes | yes | keep | Feeling hungry before a feed |
| E022 | high | yes | yes | keep | Feeding from breast |
| E023 | high | yes | yes | keep | Feeding from bottle |
| E024 | high | maybe | yes | keep | Feeding pausing before the child is done |
| E025 | medium | no | defer | keep | Milk flow being faster or slower than usual |
| E026 | high | yes | yes | keep | Turning away or closing the mouth when full |
| E027 | high | maybe | yes | keep | Gas, burping, or stomach discomfort |
| E028 | medium | no | defer | keep | Being held upright after feeding |
| E029 | medium | no | defer | keep | Spitting up or reflux-like discomfort |
| E030 | low | no | no | candidate | Bib, cloth, or caregiver hand wiping mouth |
| E031 | high | yes | yes | keep | Tasting a new puree or soft food |
| E032 | medium | no | defer | keep | Tasting a familiar puree or soft food |
| E033 | high | yes | yes | keep | Rejecting a bitter, sour, or unpleasant taste |
| E034 | medium | no | defer | keep | Showing interest in food others are eating |
| E035 | medium | no | defer | keep | Touching soft or sticky food with fingers |
| E036 | medium | no | defer | keep | Smearing food on face, hand, tray, or cloth |
| E037 | high | yes | yes | keep | A spoon approaching the mouth |
| E038 | medium | no | defer | keep | Biting or mouthing a spoon |
| E039 | medium | no | defer | keep | Drinking a small amount from a cup with help |
| E040 | medium | no | defer | keep | Liquid spilling on face, body, cloth, or floor |
| E041 | medium | no | defer | keep | Drooling, swallowing, or wetness around the mouth |
| E042 | medium | no | defer | keep | Coughing or gagging lightly during a texture change |
| E043 | high | maybe | yes | keep | Seeing a food bowl, spoon, bottle, or feeding cloth |
| E044 | medium | no | defer | keep | Seeing the usual feeding setup before feeding begins |
| E045 | medium | no | defer | needs_split | Medicine, vitamin drops, or unfamiliar liquid taste |
| E046 | low | no | no | candidate | Smelling food being prepared |
| E047 | medium | no | defer | keep | Sitting near family while others eat |
| E048 | high | maybe | yes | keep | Food being delayed after the child shows hunger |
| E049 | medium | no | defer | keep | Feeding being interrupted by sound, visitor, or movement |
| E050 | low | no | no | candidate | Mouth being cleaned after feeding |
| E051 | high | yes | yes | keep | Moving hands while lying down |
| E052 | high | yes | yes | keep | Watching own hand move |
| E053 | medium | no | defer | keep | Kicking feet and touching a surface |
| E054 | medium | no | defer | keep | Touching feet or bringing feet toward hands |
| E055 | high | yes | yes | keep | Rolling from back toward side |
| E056 | high | maybe | yes | keep | Rolling from back toward tummy |
| E057 | high | maybe | yes | keep | Rolling from tummy toward back |
| E058 | medium | no | defer | keep | Getting stuck halfway while rolling |
| E059 | high | yes | yes | keep | Pushing up during tummy time |
| E060 | medium | no | defer | keep | Resting head down during tummy time |
| E061 | high | maybe | yes | keep | Turning head toward sound or movement |
| E062 | medium | no | defer | keep | Looking around from caregiver arms |
| E063 | high | yes | yes | keep | Leaning on hands while sitting with support |
| E064 | high | maybe | yes | keep | Sitting briefly with support from cushions, lap, or hands |
| E065 | high | yes | yes | keep | Losing balance while sitting |
| E066 | medium | no | defer | keep | Supported standing on a caregiver's lap |
| E067 | medium | no | defer | keep | Bouncing while held upright |
| E068 | high | yes | yes | keep | Reaching toward a visible toy |
| E069 | high | maybe | yes | keep | Reaching toward something too far away |
| E070 | high | yes | yes | keep | Grasping a toy or household object |
| E071 | medium | no | defer | keep | Failing to grasp a slippery, large, or awkward object |
| E072 | high | yes | yes | keep | Dropping a held object |
| E073 | medium | no | defer | keep | Releasing an object intentionally or accidentally |
| E074 | high | yes | yes | keep | Bringing an object to the mouth |
| E075 | medium | no | defer | keep | Passing an object between hands |
| E076 | medium | no | defer | keep | Hand, foot, or toy getting stuck under cloth or body |
| E077 | medium | no | defer | keep | Pulling cloth, hair, necklace, spectacles, or caregiver clothing |
| E078 | medium | no | defer | keep | Scratching, rubbing, or patting a surface |
| E079 | medium | no | defer | keep | Hitting hand repeatedly on floor, bed, body, or object |
| E080 | high | maybe | yes | keep | Being helped into a new position by caregiver |
| E081 | high | maybe | yes | keep | Soft cloth, blanket, or caregiver clothing touching skin |
| E082 | medium | no | defer | keep | Hard floor, mat, cot, or furniture pressing against the body |
| E083 | high | yes | yes | keep | Wet diaper, nappy, cloth, or clothing |
| E084 | high | yes | yes | keep | Diaper, nappy, or clothing change |
| E085 | medium | no | defer | keep | Being cleaned with cloth, wipes, water, or towel |
| E086 | high | yes | yes | keep | Bath water touching the body |
| E087 | medium | no | defer | keep | Water poured over body or head during bath |
| E088 | low | no | no | candidate | Hair or scalp being washed or wiped |
| E089 | medium | no | defer | keep | Oil massage, lotion, or powder if used in the household |
| E090 | medium | no | defer | keep | Clothes being put on or removed |
| E091 | low | no | no | candidate | Sleeves, buttons, zips, socks, mittens, or caps being adjusted |
| E092 | high | yes | yes | keep | Feeling too hot in clothing, bedding, or room |
| E093 | high | maybe | yes | keep | Feeling too cold after bath, fan, weather, or clothing change |
| E094 | medium | no | defer | keep | Fan, blanket, clothing, bath, or holding changing body temperature |
| E095 | high | yes | yes | keep | Minor bump while moving, rolling, or being carried |
| E096 | medium | no | defer | keep | Scratchy label, rough cloth, or uncomfortable fabric |
| E097 | medium | no | defer | needs_split | Itching, rash, mosquito bite, or skin irritation |
| E098 | low | no | no | candidate | Nail cutting or hair grooming |
| E099 | medium | no | defer | keep | Teeth or gum discomfort if teething has started |
| E100 | low | no | no | candidate | Nose wiping, face wiping, or eye cleaning |
| E101 | medium | no | defer | keep | Holding a soft toy |
| E102 | medium | no | defer | keep | Squeezing a soft toy |
| E103 | medium | no | defer | keep | Holding a hard toy |
| E104 | medium | no | defer | keep | Hitting a hard toy against a surface |
| E105 | medium | no | defer | keep | Chewing or squeezing a rubber or plastic toy |
| E106 | high | yes | yes | keep | Holding and shaking a rattle |
| E107 | high | yes | yes | keep | Hearing the same rattle sound many times |
| E108 | high | maybe | yes | keep | Hearing a changed rattle rhythm or changed play pattern |
| E109 | high | yes | yes | keep | Watching a ball roll nearby |
| E110 | medium | no | defer | keep | Holding or squeezing a soft ball |
| E111 | high | maybe | yes | keep | Watching cloth, blanket, or soft toy fall |
| E112 | high | maybe | yes | keep | Watching a spoon, bowl, or hard toy fall |
| E113 | high | maybe | yes | keep | Touching or banging a steel bowl, plate, spoon, or cup |
| E114 | medium | no | defer | keep | Touching wooden, plastic, rubber, metal, or fabric objects |
| E115 | medium | no | defer | keep | Seeing a toy partly hidden behind another object |
| E116 | high | yes | yes | keep | Toy or face being hidden under cloth |
| E117 | high | yes | yes | keep | Hidden toy or face appearing again |
| E118 | medium | no | defer | keep | Seeing an object inside a bowl, box, cup, or bag |
| E119 | medium | no | defer | keep | Seeing an object removed from a container |
| E120 | medium | no | defer | keep | Seeing multiple toys together and reaching for one |
| E121 | medium | no | defer | keep | Toy being exchanged for another toy |
| E122 | medium | no | defer | keep | Toy being placed just out of reach |
| E123 | low | no | no | candidate | Toy being attached to stroller, cot, or play gym |
| E124 | medium | no | defer | keep | Toy swinging, dangling, or rotating overhead |
| E125 | medium | no | defer | needs_split | Toy making light, music, vibration, or mechanical movement |
| E126 | medium | no | defer | keep | Paper, book page, plastic wrapper, or cloth making crinkle sound |
| E127 | medium | no | defer | keep | Looking at a picture, pattern, face drawing, or high-contrast image |
| E128 | low | no | no | candidate | Seeing bright color, shiny object, shadow, reflection, or sparkle |
| E129 | medium | no | defer | needs_split | Watching water, food, cloth, or small object move unpredictably |
| E130 | high | maybe | yes | keep | Caregiver moving a fragile or unsafe object away |
| E131 | high | yes | yes | keep | Caregiver face close to the child |
| E132 | high | maybe | yes | keep | Caregiver smiling |
| E133 | medium | no | defer | keep | Caregiver laughing |
| E134 | high | yes | yes | keep | Caregiver speaking softly |
| E135 | high | yes | yes | keep | Caregiver speaking sharply, loudly, or with visible tension |
| E136 | high | maybe | yes | keep | Caregiver copying the child's sound or facial movement |
| E137 | medium | no | defer | keep | Child trying to copy caregiver sound, face, or movement |
| E138 | high | maybe | yes | keep | Peekaboo with caregiver face or cloth |
| E139 | high | yes | yes | keep | Caregiver looking at, pointing at, or holding up an object |
| E140 | medium | no | defer | keep | Caregiver singing, humming, chanting, or reciting |
| E141 | high | yes | yes | keep | Primary caregiver leaving the room briefly |
| E142 | high | yes | yes | keep | Primary caregiver returning after an absence |
| E143 | high | maybe | yes | keep | Father, grandparent, sibling, or familiar relative holding the child |
| E144 | medium | no | defer | keep | Familiar person greeting or playing from a distance |
| E145 | high | maybe | yes | keep | Stranger or less familiar person approaching |
| E146 | medium | no | defer | keep | Stranger or less familiar person holding the child |
| E147 | medium | no | defer | needs_split | Another child moving, touching, shouting, laughing, or crying nearby |
| E148 | medium | no | defer | keep | Family members laughing or talking together |
| E149 | high | maybe | yes | keep | Hearing another baby or child cry |
| E150 | high | maybe | yes | keep | Being comforted by someone other than the primary caregiver |
| E151 | medium | no | defer | keep | Being transferred from one person to another |
| E152 | medium | no | defer | keep | Caregiver being busy with phone, cooking, work, or another person |
| E153 | medium | no | defer | keep | Caregiver wearing mask, glasses, helmet, towel, or changed appearance |
| E154 | medium | no | defer | keep | Caregiver changing voice, expression, distance, or play style |
| E155 | low | no | no | candidate | Being photographed or video recorded by family |
| E156 | high | yes | yes | keep | Hearing the child's name or name-like sounds repeatedly |
| E157 | high | yes | yes | keep | Hearing a lullaby, rhyme, chant, or repeated song |
| E158 | high | maybe | yes | keep | Hearing repeated syllables from caregiver speech |
| E159 | high | maybe | yes | keep | Hearing home-language words during feeding, bathing, dressing, or play |
| E160 | medium | no | defer | keep | Hearing two or more languages or accents in the household |
| E161 | high | maybe | yes | keep | Seeing book pictures while someone speaks |
| E162 | high | maybe | yes | keep | Seeing an animal, vehicle, person, or object while someone names it |
| E163 | high | maybe | yes | keep | Hearing yes/no, come, give, take, eat, sleep, or similar routine words |
| E164 | medium | no | defer | keep | Hearing affectionate words, kinship terms, or nicknames |
| E165 | medium | no | defer | keep | Hearing warning words, stopping words, or changed tone near danger |
| E166 | medium | no | defer | keep | Babbling alone while lying, sitting, or being carried |
| E167 | high | yes | yes | keep | Babbling and receiving caregiver response |
| E168 | medium | no | defer | keep | Making squeals, raspberries, cough-like sounds, or laughter sounds |
| E169 | low | no | no | candidate | Hearing recorded music, television, radio, or online video speech |
| E170 | medium | no | defer | keep | Hearing phone or video-call voice from a distant familiar person |
| E171 | high | yes | yes | keep | Watching a ceiling fan or moving fan |
| E172 | high | maybe | yes | keep | Light being switched on or off |
| E173 | high | yes | yes | keep | Door opening, closing, knocking, or bell ringing |
| E174 | medium | no | defer | keep | Curtain, cloth, leaf, or paper moving in wind |
| E175 | high | maybe | yes | keep | Pressure cooker whistle, mixer, grinder, or kitchen appliance sound |
| E176 | medium | no | defer | keep | Utensils clanging in the kitchen |
| E177 | medium | no | defer | keep | Traffic horn, vehicle sound, construction sound, or street noise |
| E178 | low | no | no | candidate | Phone ringtone, notification sound, alarm, or video-call sound |
| E179 | medium | no | defer | needs_split | Prayer, festival, music, television, or loudspeaker sound if present |
| E180 | medium | no | defer | keep | Dog, bird, cow, cat, or other animal sound nearby |
| E181 | medium | no | defer | needs_split | Rain, thunder, wind, water pump, tap, or bucket sound |
| E182 | low | no | no | candidate | Sweeping, mopping, washing machine, vacuum, or cleaning sound |
| E183 | medium | no | defer | keep | Doorbell, visitor arrival, delivery, or gate sound |
| E184 | medium | no | defer | needs_split | Lift/elevator, staircase, corridor, balcony, terrace, or outdoor transition |
| E185 | high | maybe | yes | keep | Being carried from one room to another |
| E186 | high | maybe | yes | keep | Being placed on a floor mat, cot, bed, or play area |
| E187 | medium | no | defer | keep | Being put in a stroller, car seat, high chair, sling, or carrier |
| E188 | medium | no | defer | keep | Sitting near window, balcony, doorway, courtyard, garden, or street view |
| E189 | medium | no | defer | keep | Going outside briefly in arms, stroller, carrier, or vehicle |
| E190 | medium | no | defer | needs_split | Being in a shop, clinic, relative's house, temple/church/mosque, or public place |
| E191 | high | maybe | yes | keep | Seeing own image and caregiver image in a mirror |
| E192 | medium | no | defer | keep | Seeing shadow of self, caregiver, toy, curtain, or fan |
| E193 | high | yes | yes | keep | Caregiver preventing mouthing, touching, crawling, or reaching |
| E194 | high | maybe | yes | keep | Toy being taken away for cleaning, safety, or end of play |
| E195 | medium | no | defer | keep | Toy or object being washed, wiped, dried, or returned |
| E196 | high | yes | defer | needs_split | Vaccination, doctor visit, medicine, or health check |
| E197 | high | yes | yes | keep | Illness, blocked nose, fever, tiredness, or unusual fussiness |
| E198 | high | maybe | defer | needs_split | Many visitors, loud sounds, bright lights, or too much activity |
| E199 | high | yes | yes | keep | Calm play after feeding, sleep, changing, and basic needs are met |
| E200 | high | maybe | yes | keep | Quiet time alone while awake, looking around or self-playing briefly |

## Coverage Areas

The list is grouped roughly across these areas:

```text
sleep and waking: E001-E020
feeding and mouth: E021-E050
movement and posture: E051-E080
body care and bodily states: E081-E100
objects and play: E101-E130
caregiver and social contact: E131-E155
speech and sound exposure: E156-E170
household and outside environment: E171-E190
reflection, safety, disruption, and calm play: E191-E200
```

## Separation Rule

Do not add inferred learning targets to this file.

Later passes may create separate files such as:

```text
docs/6mo-child-encounter-relations.md
docs/6mo-child-encounter-micro-experiences.md
data/developmental_graph/annotations/...
```

Those derived files can extract relations, valence changes, prediction changes,
language overlays, and training examples. This file should remain the clean
encounter inventory.

## Prioritisation Pass Later

Later, score each encounter family without changing this raw file.

Possible prioritisation dimensions:

```text
frequency in daily life
developmental importance
coverage of input channels
variation potential
training usefulness
risk/safety importance
cultural configurability
```

The first executable dataset should probably choose about 30 high-value families
from this 200-item inventory.

## Sources Used for Developmental Grounding

- CDC, "Milestones by 6 Months" (updated Feb. 16, 2026):
  https://www.cdc.gov/act-early/milestones/6-months.html
- American Academy of Pediatrics, "Infant Food and Feeding":
  https://www.aap.org/en/patient-care/healthy-active-living-for-families/infant-food-and-feeding/
- American Academy of Pediatrics, "Health Supervision Visit, 6 Months"
  (updated Feb. 13, 2026):
  https://www.aap.org/en/patient-care/newborn-infant-and-early-childhood-nutrition/newborn-and-infant-health-assessment-and-promotion/health-supervision-visit-6-months/
- American Speech-Language-Hearing Association, "Feeding and Swallowing
  Milestones: 6 to 12 Months":
  https://www.asha.org/siteassets/public/feeding-and-swallowing-milestones-6-to-12-months.pdf
