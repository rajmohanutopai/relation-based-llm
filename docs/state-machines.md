# State Machines

Date: 2026-11-07

This repo is a set of research scripts with no server, database or queue. Its state
lives in files that later scripts trust, and in the memory of long experiment runs.
This document lists those machines, the rules each must keep, and the invalid states
the code could reach. Each bug below was reproduced on the unfixed code before being
fixed, except two parts found by reading the code: SM-9, and the same delete-then-build
order in the 24 older generators under SM-2.

Regression tests: `.venv/bin/python -m unittest discover -s tests`
(`tests/test_state_machines.py`). Shared safe-output code: `scripts/output_state.py`.

## Bugs by impact

"Fixed" means the change is in and a regression test passes. See Verification for which
tests also ran on the old code.

| ID | Impact | Invalid state | Reached through | Status |
|---|---|---|---|---|
| SM-1 | **High:** paid results lost; files disagree | A rerun empties earlier results, then one failed call leaves new rows beside the old manifest | Failure, no retry, two processes | Fixed |
| SM-2 | **High:** input data deleted | `--output-dir` equal to the experiment deletes the input splits; any failed rebuild deletes the old output | Failure, user flag | Fixed |
| SM-8 | **High:** results lost silently | Two runs sharing `--out` overwrite each other; 20 of 40 runs were lost in the test | Concurrency, rerun | Fixed |
| SM-7 | **Medium:** a model can train on a mismatched pair | New train shard beside old val shard and old manifest | Failure | Fixed |
| SM-6 | **Medium:** stale data looks current | After a re-split, the old `heldout.json` and old `datasets/` remain | Rerun | Fixed |
| SM-3 | **Medium:** biased experiment arm | Blocked agreement counted as a failed promise | Normal run of `attach`, `both` | Fixed; see numbers below |
| SM-4 | **Medium:** results depend on run order | Same seed and setting give different logs in one process | Sequential runs | Fixed; see numbers below |
| SM-5 | **Low:** reported counts wrong | Dead links stored and counted as live | Normal run | Fixed; no score affected |
| SM-9 | **Low:** a wrong file can go unnoticed | Outputs matching no case are dropped without a word | Wrong input file | Fixed |
| SM-10 | **Low:** a short run crashes at the end | Division by zero in reporting at 200 actions or fewer | Short run | Fixed |

### Issue groups

No GitHub issues were opened, since that needs the user's go-ahead. These groups are
ready to file.

- **Issue A: derived data can be lost or mixed.** SM-1, SM-2, SM-6, SM-7. Common cause:
  destroying or overwriting the old state before the new state is complete. Common fix:
  build aside, publish last, write the manifest last.
- **Issue B: experiment numbers can be silently wrong or lost.** SM-3, SM-4, SM-5, SM-8.
  Common cause: state shared or conflated across runs or across link states.
- **Issue C: small reporting gaps.** SM-9, SM-10.

## Machine 1: paid generation run

`scripts/generate_age_6mo_gemini_episodes.py`. A run makes one paid API call per concept.

**States:** Idle; Locked; Collecting (rows in `*.partial`, `run_state.json` present);
Interrupted (partial files, no lock or a dead lock); Publishing; Complete (published
files and manifest agree, no partial files).

**Rules:**

1. Published files and the manifest always describe one whole run.
2. No manifest while the published files change.
3. Only one live writer per output directory.
4. Finished rows from an unfinished run are never dropped without a flag.
5. `--resume` only continues a run with the same model, concepts and settings.
6. A concept appears once across accepted and rejected.

| From | Event | To | Guard or action |
|---|---|---|---|
| Idle | start | Locked | `.lock` created exclusively |
| Locked | another live process holds the lock | exit | Before any paid call |
| Locked | the lock's process is dead | Locked | Takes over |
| Locked | no unfinished run | Collecting | Writes `run_state.json` |
| Locked | unfinished run, no flag | exit | Before any paid call |
| Locked | `--resume`, same settings | Collecting | Torn last line dropped; finished concepts skipped |
| Locked | `--resume`, other settings | exit | |
| Locked | `--discard-partial` | Collecting | Partial files removed |
| Collecting | response | Collecting | Row appended; a blocked or unparseable response is a rejected row |
| Collecting | transient error | Collecting | Up to 4 retries with backoff |
| Collecting | other error, or retries used up | Interrupted | Exit non-zero; published files untouched |
| Collecting | all concepts done | Publishing | Manifest removed first |
| Publishing | files moved, manifest written | Complete | Partial files removed; lock released |

**SM-1 evidence, before the fix** (fake client, real script):

```text
first run complete: requested 3 rejected 3 rejected bytes 1326
second run crashed on one transient error (no retry): transient
after crash: rejected rows 1 manifest still says rejected 3
blocked response crashes the whole run: response blocked
```

The script emptied the published files before its first call, had no retries, and read
`response.text` outside its `try`, so one blocked response ended the run. Two processes
could write the same files at once.

**Limits of the fix:** nothing has been run against the real Gemini API, which needs a
key. Retries cover connection and timeout errors and codes 408, 429 and 5xx. A call that
fails after Google has billed it would be paid twice; the script can't see that.

## Machine 2: experiment artefact chain

Curriculum → splits → datasets → shards → trained model → outputs → score.

**Splits** (`create_developmental_experiment_splits.py`). States: Absent; Incomplete
(no manifest); Current (manifest lists exactly the files present). Datasets built from
an older split count as invalid.

**Rules:** the manifest goes last; no manifest means incomplete, and the dataset step
refuses to read such a directory; a failed run changes nothing; a re-split removes
everything the old split produced.

| From | Event | To | Action |
|---|---|---|---|
| Absent | split | Current | Stage, move, write manifest |
| Current | split, no `--overwrite` | Current | Refused |
| Current | split `--overwrite`, bad input | Current | Fails before any change |
| Current | split `--overwrite`, good input | Current | Removes manifest, old held-out files and `datasets/`, moves files, writes manifest |
| any | crash during the moves | Incomplete | Rerun with `--overwrite` |

**SM-6 evidence, before the fix:**

```text
manifest lists heldout? False | heldout.json on disk? True | stale datasets/ still there? True
```

**Datasets** (`create_developmental_dataset_variants.py`). States: Absent; Staged;
Current. Rules: the inputs can't sit inside the output; a failed build keeps the old
output; manifest hashes match the final files.

| From | Event | To | Action |
|---|---|---|---|
| any | output is, or contains, the experiment directory | same | Refused, with or without `--overwrite` |
| Absent or Current | build | Staged | Written to a hidden sibling |
| Staged | failure | Absent or Current, as before | Sibling removed |
| Staged | success | Current | Swapped in by rename |

**SM-2 evidence, before the fix:**

```text
output-dir == experiment_dir: exit 1 | experiment dir now has [] | FileNotFoundError ... train.jsonl
```

The same delete-then-build order was in 24 older generators. They now call
`retire_output_dir`, which moves the old directory aside and restores it if the script
dies on an exception.

**Limit:** a generator that fails through `SystemExit` counts as finished, because
Python doesn't tell exit handlers the status. Its old output is then removed, as it
always was. Outputs of these generators are gitignored and can be regenerated.

**Shards** (`create_nanochat_pretrain_shards.py`). Rule: train, val and manifest come
from one build. Both shards are written under a non-parquet name and moved after both
succeed; the manifest goes last.

**SM-7 evidence, before the fix:** `train now NEW | val still OLD | manifest still present True`.

**Training** (`train_tiny_causal_lm.py`). States: NoRun; Training (`checkpoint-N`);
Saved (`final/`); Recorded (`run_manifest.json`). **Unconfirmed, not changed:** reading
the code, a rerun in the same directory keeps old checkpoints, and a crash would leave
an old `final/` and old manifest beside new checkpoints. The base model isn't cached
here, so I couldn't run this. `generate_heldout_outputs.py` takes an explicit
`--model-dir`, which limits the harm.

**Scoring** (`run_heldout_evaluation.py`). Each case is Answered or Missing, and a
missing one scores as an empty answer and appears in `missing_outputs`. Rows are
unique per case; a duplicate is refused. **SM-9:** outputs matching no case were
dropped silently, and now appear as `unmatched_outputs`.

## Machine 3: a general link

`scripts/acting_agent_v3.py`, `v4.py`, `v4_1.py`, `v4_2.py`. One link per key
(feature combination, action, surface feature, bit).

**States:** Unseen; Candidate (in `cand`); Formed-unconfirmed; Consolidated (c ≥ 3,
`done`); Dead (c below 0.25, awaiting removal). With fading off, a formed link never
dies; with no S-curve or fading (v3.1), `felt` isn't used.

**Rules:**

1. A key is never in both `cand` and `gen`.
2. Where counts are kept, `gen` and `felt` hold the same keys.
3. A Dead link doesn't predict, doesn't pay, and is not counted as formed.
4. Each thing confirms a link once when the guard is on.
5. Consolidated links don't fade and contradictions don't lower them.
6. `fails` counts only groks that were promised and refused by the evidence.

| From | Event | To | Action |
|---|---|---|---|
| Unseen | a thing is tried | Candidate | Member link added |
| Candidate | at least 3 ready things, spread at most 0.25, attach allows | Formed | Evidence merged; forming pays; `paid` records the key |
| Candidate | at least 3 ready things, spread above 0.25 | Candidate | `fails` + 1 |
| Candidate | at least 3 ready things, spread fine, attach blocks | Candidate | No change (**SM-3** counted this as a failure) |
| Formed | confirmation by a new thing | Formed | c + 1; pays under S-curve or flat |
| Formed | c reaches 3 | Consolidated | `done` |
| Formed | contradiction | Formed | c − 1, floor 0 |
| Formed | time passes, fading on | Formed | c halves every 300 actions |
| Formed | c below 0.25 | Dead | |
| Dead | touched, or `sweep()` at end of run | Unseen | Removed; `dissolved` + 1 (**SM-5** skipped the sweep) |
| Consolidated | touched | Consolidated | Strength still updates |

Re-forming goes Unseen → Candidate → Formed from no evidence, and `fails` isn't reset.
In `*-first` versions of v4.2, `paid` makes the second forming pay nothing.

**SM-3 evidence, before the fix:**

```text
general links formed 0 candidates 1050 fails recorded while evidence agreed 315
```

A later attached link's promise, `pay / (2 + fails)`, was therefore too low.

**SM-5 evidence, before the fix** (1,200 random actions):

```text
general_links reported 6526 of which dead 257 = 0.039; dissolved counted 4802
gadget links reported 207 alive 195
```

Prediction already skipped dead links, so accuracy and choices weren't affected. Only
`general_links`, `gadget_general_links` and `dissolved` were off, by about 4% here.

## Machine 4: an experiment run and its results file

**States:** Unclaimed; Claimed (empty file, created exclusively); Partial (valid JSON
with finished runs so far); Finished. **Rules:** a file holds runs from one process;
each write replaces it whole.

| From | Event | To | Action |
|---|---|---|---|
| Unclaimed | start | Claimed | Exclusive create |
| Claimed or later | another start, no `--overwrite` | same | Second run exits |
| Claimed or later | another start, `--overwrite` | Claimed | User chose this; concurrent writers aren't prevented |
| Claimed or Partial | run ends | Partial | Atomic replace |

**SM-8 evidence, before the fix** (two processes, one `--out`):

```text
runs in shared results.json 20 seeds [1] (2 processes did 20 runs each)
```

**SM-4:** `CHANGE_RNG` was module state, so a run's outcomes depended on how many change
runs came before it in the process. Evidence: `same seed, same change, identical logs? False`.
It's now reset per run.

**SM-10:** at 200 actions or fewer, `log[200:]` is empty and reporting divided by zero.

**Per-run cache** (`hcache`). Filled at warm-up's end and at each room start; only the
tried thing's entries refresh after a try. Entries for other things can be up to 15 tries
old, by design, as `docs/acting-agent-v3-design.md` records. `V.Store` is a module global
that each `run` sets; this is safe because runs in a process are sequential.

## Machine 5: authoring status

`data/developmental_graph/relation_authoring/age_6mo_relation_authoring_status_v0.json`.

**States:** authoring: pending, in_progress, relations_done, needs_revision, approved,
skipped. Review: not_reviewed, reviewed_pass, reviewed_needs_fix. All 520 concepts sit at
relations_done and not_reviewed.

**No script writes this file**, so these transitions happen by hand and no code enforces
them. `tests/test_state_machines.py` now checks the rules: values come from the listed
sets, row counts per batch match the files, and approved implies reviewed_pass. A clean clone
showed the last commit broke one: batch 0009 has 217 rows and the file said 216. An uncommitted
edit already held the right count, and it's now committed.

| From | Event | To |
|---|---|---|
| pending | author starts | in_progress |
| in_progress | rows written | relations_done |
| relations_done | review passes | approved, reviewed_pass |
| relations_done | review finds faults | needs_revision, reviewed_needs_fix |
| needs_revision | rows fixed | relations_done, not_reviewed |
| any | concept dropped | skipped |

## Machine 6: curriculum sampler

`scripts/train_sampler_experiment.py`, `train_sampler_v2.py`. Each cluster is Inactive or
Active in the fixed arm, joining in order until all are active by 80% of training. Probe
losses move Unprobed → Probed once → Probed. No invalid state found by reading. These
scripts need the generated world data to run, and I didn't run them for this audit.
`log.jsonl` is opened with `"w"`, so a rerun replaces an arm's log, as with SM-8, in a
per-arm folder; left as it is, since nothing runs them in parallel.

## What changed for reported results

Fixes were checked by rerunning the affected arms into new folders. The earlier run
folders are unchanged.

**No change for anything without `attach`.** After all fixes, `---`, `--S` and `-FS` still
match their earlier curves exactly on seed 1, condition A. So v3.1, v4 `current`, `spike` and
`spike_naive`, all of v4.1 and all of v4.2 keep their scores.

**SM-3 changes `attach` and `both`** (`runs/acting_agent_v4_fixed_attach/`, 5 seeds):

| version | A area | A final | A gadget time | B area | B final | B gadget time |
|---|---:|---:|---:|---:|---:|---:|
| attach, reported | 0.731 | 0.807 | 24.2% | 0.710 | 0.780 | 15.6% |
| attach, fixed | 0.721 | 0.790 | 24.7% | 0.708 | 0.776 | 15.8% |
| both, reported | 0.720 | 0.810 | 14.4% | 0.702 | 0.796 | 15.8% |
| both, fixed | 0.708 | 0.793 | 15.1% | 0.684 | 0.781 | 15.6% |

No v4 verdict flips. `both` stays below random on gadgets in 5 of 5 seeds in each condition,
and attach still fails that test in A. But both arms learn less than reported, by up to
0.018 in area, so **the bug happened to help them.** I haven't shown why. `both` now beats surprise in 0 of 5 seeds in each
condition (reported: 0 and 1).

**SM-4 changes no reported number.** Rerunning grief2 with the fix gives the same big-to-small
sadness ratios as the reported run, to two decimals (1.14, 0.97, 0.95, 0.79, 0.96), and the
same first-run logs. Each seed ran in its own process, which limited the leak.

**SM-5 changes counts only:** `general_links`, `gadget_general_links` and `dissolved` in v4,
v4.1 and v4.2 reports are off by a few percent (about 4% in one test run). They were not
recomputed.

**Verification:** all 32 tests pass. 25 of them also ran on the old code first: 20 failed or
errored, as they should. The other 5 passed there: they guard behaviour that was already right,
or, for two Gemini tests, stopped on the then-unknown flag, so those two proved nothing on the
old code. The other 7 tests (older generators, scorer, status file, link rules) were written
after the fixes and never ran on the old code. All 24 edited generators start with `--help`, and
one was built twice with `--overwrite`; its outputs matched a fresh build except for the output
path in `training_config.json`.

## Known limits of these fixes

- `claim_results` stops accidents. `--overwrite` on two processes at once still conflicts.
- `directory_lock` has a small race if two processes take over the same dead lock at once.
- `staged_directory` can leave a `.retired` folder if two builds of one output race. Output
  stays complete.
- Files are moved one at a time, so a power cut mid-publish can leave a missing manifest.
  That state is detectable by design.
