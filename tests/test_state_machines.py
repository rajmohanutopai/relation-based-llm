#!/usr/bin/env python3
"""Regression tests for the invalid states recorded in docs/state-machines.md.

Run with: .venv/bin/python -m unittest discover -s tests
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)
CURRICULUM = ROOT / "data/developmental_graph/curricula/seed_everyday_physical_world_curriculum.jsonl"
HELDOUT = ROOT / "data/developmental_graph/evaluations/everyday_physical_world_heldout.json"


def script(name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, f"scripts/{name}", *args], capture_output=True, text=True, cwd=ROOT)


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)


# --- Gemini generator: SM-1 ---------------------------------------------------


class FakeResponse:
    usage_metadata = None

    def __init__(self, text):
        self.text = text


class BlockedResponse:
    usage_metadata = None

    @property
    def text(self):
        raise ValueError("response blocked")


GOOD = FakeResponse(json.dumps({"scene": "s", "question": "q", "answer": "a", "hidden_relation": "h", "concepts_used": []}))


def load_generator():
    google, genai, gtypes = (types.ModuleType(n) for n in ("google", "google.genai", "google.genai.types"))
    gtypes.GenerateContentConfig = gtypes.ThinkingConfig = lambda **k: None

    class Client:
        plan: list = []

        def __init__(self, **k):
            self.models = self

        def generate_content(self, **k):
            action = Client.plan.pop(0)
            if isinstance(action, Exception):
                raise action
            return action

    genai.Client, genai.types, google.genai = Client, gtypes, genai
    with mock.patch.dict(sys.modules, {"google": google, "google.genai": genai, "google.genai.types": gtypes}):
        spec = importlib.util.spec_from_file_location("gemini_under_test", ROOT / "scripts/generate_age_6mo_gemini_episodes.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    module.validate_episode = lambda episode, item: []
    module.time.sleep = lambda s: None
    return module, Client


class GeminiRunLifecycle(TempDirTest):
    def setUp(self):
        super().setUp()
        self.G, self.Client = load_generator()
        self.out = self.tmp / "gem"
        os.environ["GEMINI_API_KEY"] = "test"
        self.addCleanup(os.environ.pop, "GEMINI_API_KEY", None)

    def go(self, plan, *extra):
        self.Client.plan = list(plan)
        argv = ["g", "--output-dir", str(self.out), "--limit", "3", "--sleep-seconds", "0", *extra]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            self.G.main()

    def rows(self, name):
        path = self.out / name
        return [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []

    def manifest(self):
        return json.loads((self.out / "manifest.json").read_text())

    def test_transient_error_is_retried(self):
        self.go([ConnectionError("blip"), GOOD, GOOD, GOOD])
        self.assertEqual(self.manifest()["accepted"], 3)

    def test_failed_rerun_keeps_previous_results_in_step(self):
        self.go([GOOD, GOOD, GOOD])
        before = (self.out / "episodes.accepted.jsonl").read_text()
        fatal = RuntimeError("bad request")
        with self.assertRaises(BaseException):
            self.go([fatal], "--discard-partial")
        self.assertEqual((self.out / "episodes.accepted.jsonl").read_text(), before)
        self.assertEqual(self.manifest()["accepted"], len(self.rows("episodes.accepted.jsonl")))
        self.assertEqual(len(self.rows("training.accepted.jsonl")), len(self.rows("episodes.accepted.jsonl")))

    def test_resume_doesnt_call_the_api_again_for_finished_concepts(self):
        with self.assertRaises(BaseException):
            self.go([GOOD, RuntimeError("bad request")])
        self.go([GOOD, GOOD], "--resume")  # only the two unfinished concepts
        self.assertEqual(self.Client.plan, [])
        self.assertEqual(self.manifest()["accepted"], 3)
        ids = [r["source_concept_id"] for r in self.rows("episodes.accepted.jsonl")]
        self.assertEqual(len(ids), len(set(ids)))

    def test_leftover_partial_isnt_discarded_silently(self):
        with self.assertRaises(BaseException):
            self.go([GOOD, RuntimeError("bad request")])
        with self.assertRaises(SystemExit):
            self.go([GOOD, GOOD, GOOD])
        self.assertEqual(len(self.Client.plan), 3, "must refuse before any paid call")

    def test_resume_with_other_settings_is_refused(self):
        with self.assertRaises(BaseException):
            self.go([GOOD, RuntimeError("bad request")])
        with self.assertRaises(SystemExit):
            self.go([GOOD], "--resume", "--temperature", "0.9")
        self.assertEqual(len(self.Client.plan), 1)

    def test_torn_last_line_is_dropped_on_resume(self):
        with self.assertRaises(BaseException):
            self.go([GOOD, RuntimeError("bad request")])
        with (self.out / "episodes.accepted.jsonl.partial").open("a") as f:
            f.write('{"torn": ')
        self.go([GOOD, GOOD], "--resume")
        self.assertEqual(self.manifest()["accepted"], 3)

    def test_blocked_response_is_a_rejected_row(self):
        self.go([BlockedResponse(), GOOD, GOOD])
        self.assertEqual(self.manifest()["rejected"], 1)
        self.assertEqual(self.manifest()["accepted"], 2)

    def test_second_process_is_locked_out(self):
        self.out.mkdir(parents=True)
        (self.out / ".lock").write_text(str(os.getppid()))  # a process that's alive
        with self.assertRaises(SystemExit):
            self.go([GOOD, GOOD, GOOD])
        self.assertEqual(len(self.Client.plan), 3)

    def test_stale_lock_from_a_dead_process_is_taken_over(self):
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        self.out.mkdir(parents=True)
        (self.out / ".lock").write_text(str(dead.pid))
        self.go([GOOD, GOOD, GOOD])
        self.assertEqual(self.manifest()["accepted"], 3)
        self.assertFalse((self.out / ".lock").exists())


# --- Dataset pipeline: SM-2 ---------------------------------------------------


class ExperimentPipeline(TempDirTest):
    def split(self, *extra):
        return script("create_developmental_experiment_splits.py", str(CURRICULUM), "--experiment-id", "t",
                      "--output-dir", str(self.exp), *extra)

    def setUp(self):
        super().setUp()
        self.exp = self.tmp / "exp"

    def variants(self, *extra):
        return script("create_developmental_dataset_variants.py", str(self.exp), *extra)

    def test_output_dir_cant_be_the_experiment_dir(self):
        self.assertEqual(self.split().returncode, 0)
        result = self.variants("--output-dir", str(self.exp), "--overwrite")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.exp / "train.jsonl").exists(), "input splits were deleted")

    def test_output_dir_cant_contain_the_experiment_dir(self):
        self.assertEqual(self.split().returncode, 0)
        result = self.variants("--output-dir", str(self.tmp), "--overwrite")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.exp / "train.jsonl").exists(), "input splits were deleted")

    def test_failed_rebuild_keeps_the_previous_datasets(self):
        self.assertEqual(self.split().returncode, 0)
        first = self.variants()
        self.assertEqual(first.returncode, 0, first.stderr)
        before = (self.exp / "datasets/manifest.json").read_text()
        (self.exp / "dev.jsonl").write_text("{broken\n")
        self.assertNotEqual(self.variants("--overwrite").returncode, 0)
        self.assertEqual((self.exp / "datasets/manifest.json").read_text(), before)
        self.assertEqual([p.name for p in self.tmp.iterdir() if "datasets" in p.name], [])
        self.assertEqual(sorted(p.name for p in self.exp.iterdir() if p.name.startswith(".")), [])

    def test_variant_manifest_hashes_match_final_files(self):
        self.assertEqual(self.split().returncode, 0)
        self.assertEqual(self.variants().returncode, 0)
        manifest = json.loads((self.exp / "datasets/manifest.json").read_text())
        import hashlib
        files = manifest["files"] if "files" in manifest else manifest["outputs"]
        self.assertTrue(files)
        for entry in files.values():
            self.assertEqual(hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest(), entry["sha256"])

    def test_resplit_removes_what_the_new_manifest_doesnt_list(self):
        self.assertEqual(self.split("--heldout", str(HELDOUT)).returncode, 0)
        self.assertEqual(self.variants().returncode, 0)
        self.assertEqual(self.split("--overwrite").returncode, 0)
        self.assertFalse((self.exp / "heldout.json").exists(), "stale held-out copy")
        self.assertFalse((self.exp / "heldout_prompts.jsonl").exists(), "stale held-out prompts")
        self.assertFalse((self.exp / "datasets").exists(), "datasets from the old split")

    def test_failed_resplit_changes_nothing(self):
        self.assertEqual(self.split().returncode, 0)
        before = (self.exp / "train.jsonl").read_text()
        bad = self.tmp / "bad.jsonl"
        bad.write_text("{broken\n")
        result = script("create_developmental_experiment_splits.py", str(bad), "--experiment-id", "t",
                        "--output-dir", str(self.exp), "--overwrite")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.exp / "train.jsonl").read_text(), before)
        self.assertTrue((self.exp / "manifest.json").exists())


@unittest.skipUnless(importlib.util.find_spec("pyarrow"), "needs pyarrow")
class ShardWrites(TempDirTest):
    def test_crash_leaves_train_and_val_from_the_same_build(self):
        import create_nanochat_pretrain_shards as N
        import pyarrow.parquet as pq
        train, val = self.tmp / "tr.jsonl", self.tmp / "va.jsonl"
        for path in (train, val):
            path.write_text(json.dumps({"id": "1", "input": "OLD", "target": "OLD"}) + "\n")
        argv = ["x", "--train-jsonl", str(train), "--val-jsonl", str(val), "--base-dir", str(self.tmp / "b"),
                "--mode", "input_target"]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            N.main()
        train.write_text(json.dumps({"id": "1", "input": "NEW", "target": "NEW"}) + "\n")
        real, calls = N.write_parquet, []

        def fail_second(texts, path):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("disk full")
            real(texts, path)

        with mock.patch.object(N, "write_parquet", fail_second), mock.patch.object(sys, "argv", argv + ["--overwrite"]):
            with self.assertRaises(OSError):
                N.main()
        data = self.tmp / "b/base_data_climbmix"
        self.assertTrue(pq.read_table(data / N.TRAIN_SHARD).to_pylist()[0]["text"].startswith("OLD"))
        self.assertTrue((data / "manifest.json").exists())
        self.assertEqual([p.name for p in data.iterdir() if ".tmp" in p.name], [])


# --- Link lifecycle and run bookkeeping: SM-3, SM-4 ---------------------------


def short_args(actions=320):
    return argparse.Namespace(actions=actions, episode_len=15, warmup=200, flip=0.1, temperature=0.3, epsilon=0.1,
                              eval_every=100)


class LinkLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import acting_agent_v4 as V4
        cls.V4, cls.V = V4, V4.V

    def tearDown(self):
        pass

    def things(self):
        return self.V.W.ROOM_OBJS[:3]

    def teach(self, store, rounds=4):
        for _ in range(rounds):
            for t in self.things():
                action = self.V.W.actions_for(t)[0]
                store.update(t, action, "floor", [False] * self.V.W.N_BITS[action])

    def test_agreeing_evidence_blocked_by_attach_isnt_a_failed_promise(self):
        store = self.V4.Store(attach=True, spike=None)
        store.frontier = set()
        self.teach(store)
        self.assertEqual(len(store.gen), 0)
        self.assertEqual(sum(store.fails.values()), 0)

    def test_disagreeing_evidence_still_counts_as_a_failure(self):
        store = self.V4.Store(attach=False, spike=None)
        a, b, c = self.things()
        for t, y in ((a, True), (b, True), (c, False)) * 3:
            action = self.V.W.actions_for(a)[0]
            if action in self.V.W.actions_for(t):
                store.update(t, action, "floor", [y] * self.V.W.N_BITS[action])
        self.assertGreater(sum(store.fails.values()), 0)

    def test_sweep_removes_dead_links_and_counts_them(self):
        store = self.V4.Store(attach=False, spike="guard")
        self.teach(store)
        formed = len(store.gen)
        self.assertGreater(formed, 0)
        self.assertEqual(set(store.gen), set(store.felt))
        store.step += 10_000
        store.sweep()
        self.assertEqual(len(store.gen), 0)
        self.assertEqual(store.dissolved, formed)
        self.assertEqual(set(store.gen), set(store.felt))

    def test_reported_link_count_excludes_dead_links(self):
        made = []

        def factory():
            made.append(self.V4.Store(False, "guard"))
            return made[-1]

        with mock.patch.object(self.V, "Store", factory):
            result = self.V.run("random", 1, short_args(), False, "none")
        store = made[-1]
        self.assertEqual(result["general_links"], sum(store.alive(k) for k in store.gen))
        self.assertEqual(result["general_links"], len(store.gen))

    def test_link_state_rules_hold_through_a_real_run(self):
        made = []

        def factory():
            made.append(self.V4.Store(False, "guard"))
            return made[-1]

        with mock.patch.object(self.V, "Store", factory):
            self.V.run("happiness", 1, short_args(500), False, "none")
        store = made[-1]
        self.assertGreater(store.dissolved + len(store.gen), 0)
        self.assertEqual(set(store.gen), set(store.felt))
        self.assertEqual(set(store.gen) & set(store.cand), set())
        for felt in store.felt.values():
            if not felt.done:
                self.assertLess(felt.c, self.V4.CONSOLIDATED)

    def test_short_run_doesnt_crash_in_reporting(self):
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.V4.run("current", "random", 1, short_args(150), False)
        self.assertEqual(result["gadget_share"], 0.0)

    def test_change_runs_repeat_exactly_in_one_process(self):
        with mock.patch.object(self.V, "Store", lambda: self.V4.Store(False, None)):
            args = short_args(2200)
            args.eval_every = 2200
            first = self.V.run("random", 1, args, False, "light_big")["log"]
            second = self.V.run("random", 1, args, False, "light_big")["log"]
        self.assertEqual(first, second)


class ResultFiles(TempDirTest):
    def test_results_file_is_claimed_once(self):
        from output_state import claim_results
        path = self.tmp / "results.json"
        claim_results(path, overwrite=False)
        with self.assertRaises(SystemExit):
            claim_results(path, overwrite=False)
        claim_results(path, overwrite=True)

    def test_atomic_write_never_exposes_a_partial_file(self):
        from output_state import atomic_write_text
        path = self.tmp / "results.json"
        path.write_text("old")
        with mock.patch("os.replace", side_effect=OSError("disk full")), self.assertRaises(OSError):
            atomic_write_text(path, "new")
        self.assertEqual(path.read_text(), "old")
        self.assertEqual([p.name for p in self.tmp.iterdir()], ["results.json"])

    def test_every_grid_script_refuses_to_overwrite_results(self):
        for name in ("acting_agent_v3.py", "acting_agent_v4.py", "acting_agent_v4_1.py", "acting_agent_v4_2.py"):
            source = (ROOT / "scripts" / name).read_text()
            self.assertIn("claim_results", source, name)
            self.assertIn("atomic_write_text", source, name)


class OlderGenerators(TempDirTest):
    SCRIPT = """
import sys
sys.path.insert(0, "scripts")
from pathlib import Path
from output_state import retire_output_dir
out = Path(sys.argv[1])
retire_output_dir(out)
out.mkdir()
(out / "partial.txt").write_text("partial")
if sys.argv[2] == "fail":
    raise ValueError("generator failed")
(out / "done.txt").write_text("done")
"""

    def go(self, mode):
        self.out = self.tmp / "out"
        self.out.mkdir(exist_ok=True)
        (self.out / "old.txt").write_text("old")
        return subprocess.run([sys.executable, "-c", self.SCRIPT, str(self.out), mode], capture_output=True, text=True, cwd=ROOT)

    def names(self):
        return sorted(p.name for p in self.out.iterdir())

    def test_failure_restores_the_previous_output(self):
        self.assertNotEqual(self.go("fail").returncode, 0)
        self.assertEqual(self.names(), ["old.txt"])
        self.assertEqual([p.name for p in self.tmp.iterdir()], ["out"])

    def test_success_replaces_the_previous_output(self):
        self.assertEqual(self.go("ok").returncode, 0)
        self.assertEqual(self.names(), ["done.txt", "partial.txt"])
        self.assertEqual([p.name for p in self.tmp.iterdir()], ["out"])

    def test_no_generator_deletes_its_output_before_building(self):
        import re
        offenders = [p.name for p in (ROOT / "scripts").glob("create_*.py")
                     if re.search(r"shutil\.rmtree\((path|args\.output_dir)\)", p.read_text())]
        self.assertEqual(offenders, [])

    def test_a_real_generator_restores_output_when_its_input_is_broken(self):
        out = self.tmp / "foundation"
        first = script("create_procedural_foundation_world_v2.py", "--output-dir", str(out))
        self.assertEqual(first.returncode, 0, first.stderr[-400:])
        again = script("create_procedural_foundation_world_v2.py", "--output-dir", str(out), "--overwrite")
        self.assertEqual(again.returncode, 0, again.stderr[-400:])
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["foundation"])


class HeldoutScoring(TempDirTest):
    def test_outputs_matching_no_case_are_reported(self):
        evaluation = json.loads(HELDOUT.read_text())
        case_id = evaluation["cases"][0]["id"]
        outputs = self.tmp / "o.jsonl"
        outputs.write_text(json.dumps({"case_id": case_id, "answer": "x"}) + "\n"
                           + json.dumps({"case_id": "from_another_file", "answer": "x"}) + "\n")
        result = script("run_heldout_evaluation.py", str(HELDOUT), str(outputs))
        self.assertEqual(result.returncode, 0, result.stderr[-300:])
        summary = json.loads(result.stdout)
        self.assertEqual(summary["unmatched_outputs"], 1)
        self.assertEqual(summary["missing_outputs"], summary["cases"] - 1)


class AuthoringStatus(unittest.TestCase):
    """No script writes this file, so these are the only guard on hand edits."""

    def test_status_file_invariants(self):
        import glob
        from collections import Counter
        status = json.loads((ROOT / "data/developmental_graph/relation_authoring/age_6mo_relation_authoring_status_v0.json").read_text())
        rows = Counter()
        for path in glob.glob(str(ROOT / "data/developmental_graph/relation_authoring/age_6mo_handwritten_relations_v0/*.jsonl")):
            rows[Path(path).stem] += len(Path(path).read_text().splitlines())
        written = Counter()
        for c in status["concepts"]:
            self.assertIn(c["authoring_status"], status["status_values"])
            self.assertIn(c["review_status"], status["review_status_values"])
            written[c["batch_id"]] += c["relation_rows_written"]
            if c["review_status"] != "not_reviewed":
                self.assertIn(c["authoring_status"], ("relations_done", "needs_revision", "approved"))
            if c["authoring_status"] == "approved":
                self.assertEqual(c["review_status"], "reviewed_pass")
        self.assertEqual(+rows, +written)


if __name__ == "__main__":
    unittest.main()
