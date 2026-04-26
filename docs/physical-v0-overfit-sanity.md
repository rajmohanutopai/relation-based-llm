# Physical V0 Overfit Sanity Check

Status: completed locally. This is a pipeline sanity check, not a model-quality
claim.

## Command

```bash
python3 scripts/train_tiny_causal_lm.py \
  --config data/developmental_graph/experiments/physical_v0/training_config.json \
  --variant relation_scaffolded \
  --overfit-limit 8 \
  --max-steps 30 \
  --output-dir runs/physical_v0/overfit_relation_scaffolded
```

## Environment

```text
torch: 2.11.0
transformers: 5.6.2
accelerate: 1.13.0
mps_available: true
cuda_available: false
```

## Result

The run completed and wrote checkpoints plus a final model under:

```text
runs/physical_v0/overfit_relation_scaffolded/
```

Observed loss:

```text
train loss at step 5:  1.712
train loss at step 10: 1.406
train loss at step 15: 1.183
train loss at step 20: 1.078
train loss at step 25: 1.024
train loss at step 30: 1.007

eval loss at step 1:  1.864
eval loss at step 30: 1.048
```

The final checkpoint also loaded successfully and generated text from a training
prompt.

## Interpretation

This passes the infrastructure sanity check:

```text
dependencies install
model downloads and loads
dataset formatting works
training loop runs
loss decreases
checkpoints are saved
final checkpoint loads
generation path works
```

It does not prove the model has learned the relation theory. The 30-step run did
not memorize the exact JSON target, so this should be treated as a training-loop
sanity check only.

The next meaningful step is to train all three variants with the frozen command
shape and compare them on curriculum-test and held-out transfer.
