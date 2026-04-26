# Physical V0.2 Candidate Selection

Status: preliminary run completed locally.

## Goal

`physical_v0_1` failed because the model invented plausible graph IDs during
free-form generation. `physical_v0_2` changes the task:

```text
prompt + candidate relation IDs -> selected candidate keys
prompt + candidate graph anchors -> selected candidate keys
```

The model still sees the real IDs and anchors, but the answer is an option key
such as `F03` or `A07`. This makes the task a closed-vocabulary selection test
rather than graph-ID memorization.

## Generated Data

```text
train:           1041
dev:              123
curriculum_test:  142
held-out:          33
```

Task mix:

```text
node_candidate_selection:                 329 train
relation_family_candidate_selection:      250 train
graph_anchor_candidate_selection:         231 train
relation_and_anchor_candidate_selection:  231 train
```

Candidates include deterministic hard negatives from nearby graph layers,
relation types, node kinds, or related families.

## Training Notes

Initial runs at `max_seq_length=768` and `640` hit MPS out-of-memory. The stable
run used the same 512-token context as earlier v0/v0.1 runs.

The trainer was also fixed to preserve target tokens when truncating long
prompts. Without that, long candidate prompts could consume the full context and
produce `nan` eval loss.

Final preliminary run:

```text
run: runs/physical_v0_2/smollm2_135m/candidate_selection_options_outputmarker_512_s160
model: HuggingFaceTB/SmolLM2-135M
max_seq_length: 512
max_steps: 160
train loss: 0.610
dev loss:   0.337
```

## Held-Out Candidate Score

```text
case pass:          0.000
family precision:   0.247
family recall:      0.407
anchor precision:   0.168
anchor recall:      0.596
gap precision:      0.200
gap recall:         0.026
non-candidate IDs:  0
```

## Interpretation

The result is mixed but useful.

Positive signal:

```text
The model stopped inventing non-candidate IDs.
Relation-family recall and anchor recall are much higher than v0/v0.1.
```

Failure:

```text
The model over-selects. Many outputs choose all anchor options, so recall rises
but precision is poor and exact case pass stays zero.
```

This means candidate selection is a better test shape than free-form generation,
but the current generative formatting is still too loose.

## Next Change

Do not expand domains yet.

Next experiment should reduce over-selection:

```text
1. Split held-out prompts into relation-family-only and anchor-only tasks.
2. Add expected selection count, e.g. "select exactly 3 options".
3. Consider binary candidate scoring: one prompt per candidate -> YES/NO.
4. Score precision, recall, and exact set match separately.
5. Only then run a longer full checkpoint.
```
