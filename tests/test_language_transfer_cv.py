#!/usr/bin/env python3
"""The cross-validated language test must hold every object out exactly once, and score as it says.

Run with: .venv/bin/python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)

try:
    import numpy as np
    import train_language_transfer_cv_v0 as CV
except ImportError:  # torch or numpy not installed
    CV = None


@unittest.skipIf(CV is None, "needs torch and numpy")
class FoldTest(unittest.TestCase):
    def setUp(self):
        self.names = sorted(f"thing_{i:03d}" for i in range(150))
        self.folds = CV.fold_sets(self.names)

    def test_every_object_is_held_out_exactly_once(self):
        self.assertEqual([len(f) for f in self.folds], [30] * 5)
        joined = [n for f in self.folds for n in f]
        self.assertEqual(sorted(joined), self.names)

    def test_fold_zero_is_the_earlier_experiments_test_set(self):
        old = sorted(random.Random(CV.W.SPLIT_SEED).sample(self.names, CV.W.HELD_OUT))
        self.assertEqual(self.folds[0], old)

    def test_folds_do_not_change_between_calls(self):
        self.assertEqual(self.folds, CV.fold_sets(self.names))


@unittest.skipIf(CV is None, "needs torch and numpy")
class ScoreTest(unittest.TestCase):
    def test_measured_facts_follow_the_cut_offs(self):
        world = [{"name": "a", "size": [0.30, 0.10, 0.06], "mass": 0.8}]
        facts = CV.measured_facts(world)["a"]
        self.assertEqual(len(facts), 12)
        self.assertEqual([facts[f"long_{c}"] for c in (15, 24, 29)], ["yes", "yes", "yes"])
        self.assertEqual([facts[f"wide_{c}"] for c in (9, 13, 20)], ["yes", "no", "no"])
        self.assertEqual([facts[f"thick_{c}"] for c in (5, 8, 11)], ["yes", "no", "no"])
        self.assertEqual([facts[f"weight_{c}"] for c in (350, 750, 2000)], ["yes", "yes", "no"])

    def test_pooled_balanced_accuracy(self):
        # 4 objects, 1 action, 2 surfaces, 1 bit: perfect on yes cases, half right on no cases
        y = np.array([[[[True], [True]]], [[[True], [True]]], [[[False], [False]]], [[[False], [False]]]])
        pred = np.array([[[[True], [True]]], [[[True], [True]]], [[[False], [False]]], [[[True], [True]]]])
        counts = CV.object_counts(pred, y)
        self.assertAlmostEqual(float(CV.pooled_balanced(counts, np.ones((1, 4)))[0]), 0.75)
        # counting the wrong object twice lowers the score: no cases are then right 1 time in 3
        self.assertAlmostEqual(float(CV.pooled_balanced(counts, np.array([[1.0, 1.0, 1.0, 2.0]]))[0]), (1 + 1 / 3) / 2)


if __name__ == "__main__":
    unittest.main()
