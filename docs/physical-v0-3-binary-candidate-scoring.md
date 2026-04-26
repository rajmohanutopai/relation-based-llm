# Physical V0.3 Binary Candidate Scoring

Status: preliminary run completed locally.

## Goal

`physical_v0_2` removed invented graph IDs, but the model over-selected
candidates. `physical_v0_3` changes the task again:

```text
prompt + one candidate relation family -> YES/NO
prompt + one candidate graph anchor -> YES/NO
```

This tests whether independent binary judgments reduce multi-select
over-selection.

## Generated Data

```text
train:           2376
dev:              283
curriculum_test:  343
held-out prompts: 794
```

Training label balance:

```text
train YES:  891
train NO:  1485
```

Task mix:

```text
relation_family_binary_judgment: 1453 train
graph_anchor_binary_judgment:     923 train
```

Training negatives were capped at roughly two negatives per positive so the
model would not learn an all-NO shortcut.

## Training Run

```text
run: runs/physical_v0_3/smollm2_135m/binary_candidate_scoring_s300
model: HuggingFaceTB/SmolLM2-135M
max_seq_length: 512
max_steps: 300
epoch: 1.01
train runtime: 688.2 seconds
train loss: 0.218
dev loss: 0.101
```

## Held-Out Score

Task-matched greedy YES/NO generation:

```text
case pass:          0.000
family precision:   0.750
family recall:      0.066
anchor precision:   0.400
anchor recall:      0.038
gap precision:      0.287
gap recall:         0.868
```

YES/NO logit threshold:

```text
case pass:          0.000
family precision:   1.000
family recall:      0.022
anchor precision:   n/a
anchor recall:      0.000
gap precision:      0.299
gap recall:         0.763
```

YES/NO logit top-k diagnostic, using the expected number of positives per
candidate type:

```text
case pass:          0.000
family precision:   0.407
family recall:      0.407
anchor precision:   0.288
anchor recall:      0.288
gap precision:      0.289
gap recall:         0.289
```

## Interpretation

The result is useful but not successful.

Positive signal:

```text
The binary format is parseable.
Local dev loss is low.
Logit top-k scoring shows weak relation-family and anchor ranking signal.
```

Failure:

```text
Greedy binary generation under-selects known relation families and graph
anchors. It over-selects missing-gap candidates. Exact held-out case pass stays
zero.
```

This means binary candidate scoring solved the v0.2 "select everything" failure
only by creating the opposite calibration problem. The model can learn the local
YES/NO format, but the current small bridge data is not enough for robust
held-out graph transfer.

## Next Change

Do not expand domains yet.

The next experiment should improve transfer data, not merely the answer format:

```text
1. Add held-out-style bridge prompts for every seed relation family.
2. Include many paraphrased transfer questions per relation, not only direct
   graph-ID prompts.
3. Train pairwise or listwise ranking: positive candidate must outrank hard
   negative candidates.
4. Evaluate relation ranking before exact set generation.
5. Only after ranking improves, return to set selection.
```
