#!/usr/bin/env python3
"""The scaffold test must train on the answers it says it does, and must feed the model's own answers back in.

Run with: .venv/bin/python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)

try:
    import torch
    import train_language_scaffold_v0 as S
    READY = S.W.WORLD.exists() and S.W.ANSWERS.exists()  # the physics outcomes are built locally, not checked in
except ImportError:  # torch not installed
    S, READY = None, False


@unittest.skipUnless(READY, "needs torch and the locally built physics outcomes")
class RowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.truth, cls.names, facts, cls.vocab = S.prepare(True)
        cls.real, cls.fake = facts["measured"]
        cls.name = cls.names[17]

    def text(self, ids):
        return " ".join(self.vocab.itos[i] for i in ids)

    def test_fact_row_trains_each_answer_at_its_question(self):
        ids, targets = S.fact_row(self.vocab, self.name, self.real[self.name])
        self.assertEqual(len(targets), 12)
        self.assertEqual(self.text(ids[:3]), "obj17 : long_over_15")
        self.assertEqual(self.vocab.itos[ids[-1]], "weight_over_2000")
        self.assertEqual(len(ids), 2 + 24 - 1)
        for (pos, target), key in zip(targets, S.FACT_KEYS):
            self.assertEqual(self.vocab.itos[ids[pos]], S.ASK[key])
            self.assertEqual(self.vocab.itos[target], self.real[self.name][key])
        # every earlier answer is in the row, right after its question mark, for the next fact to read
        for (pos, target) in targets[:-1]:
            self.assertEqual(ids[pos + 1], target)

    def test_outcome_rows(self):
        case = (self.name, "push_gentle", "slippery")
        direct, target = S.outcome_row(self.vocab, "direct", case, 0, "yes", self.real)
        self.assertEqual(self.text(direct), "obj17 : pushed gently on a slippery table . did it move ?")
        self.assertEqual(target, [(len(direct) - 1, self.vocab.stoi["yes"])])
        scaffold, target = S.outcome_row(self.vocab, "scaffold", case, 0, "no", self.real)
        listed = " ".join(f"{S.ASK[k]} {self.real[self.name][k]}" for k in S.FACT_KEYS)
        self.assertEqual(self.text(scaffold), f"obj17 : {listed} . pushed gently on a slippery table . did it move ?")
        self.assertEqual(target, [(len(scaffold) - 1, self.vocab.stoi["no"])])  # only the last answer is trained
        self.assertLessEqual(len(scaffold), S.context_length(self.vocab, self.names, self.real))

    def test_each_row_counts_once_in_the_loss(self):
        torch.manual_seed(0)
        model = S.GPT(len(self.vocab.itos), 16, 1, 2, S.context_length(self.vocab, self.names, self.real))
        fact = S.fact_row(self.vocab, self.name, self.real[self.name])
        one = S.outcome_row(self.vocab, "direct", (self.name, "push_hard", "grippy"), 1, "yes", self.real)
        both = S.rows_loss(model, [fact, one]).item()
        self.assertAlmostEqual(both, S.rows_loss(model, [fact]).item() + S.rows_loss(model, [one]).item(), places=4)
        # a 12-answer row weighs about what a 1-answer row does at the start: both are near log(vocabulary size)
        self.assertLess(S.rows_loss(model, [fact]).item() / S.rows_loss(model, [one]).item(), 2.0)

    def test_stated_facts_are_the_models_own_answers(self):
        yes, no = self.vocab.stoi["yes"], self.vocab.stoi["no"]
        calls = []

        def always_no(model, seqs):  # a stand-in model that answers no to everything
            calls.append([list(s) for s in seqs])
            logits = torch.zeros(len(seqs), len(self.vocab.itos))
            logits[:, no] = 1.0
            return logits

        original, S.last_logits = S.last_logits, always_no
        try:
            stated, said = S.state_facts(None, self.vocab, [self.name, self.names[3]])
        finally:
            S.last_logits = original
        all_no = {k: "no" for k in S.FACT_KEYS}
        self.assertEqual(said[self.name], ["no"] * 12)
        self.assertEqual(stated[self.name], S.scaffold_prefix(self.vocab, self.name, all_no))
        self.assertEqual(len(calls), 12)
        # the second question is asked with the first answer already written in
        self.assertEqual(calls[1][0][len(calls[0][0])], no)
        self.assertNotIn(yes, stated[self.name])

    def test_balanced_accuracy_from_rows(self):
        cases = [c for c in self.truth if c[0] in set(self.names[:40])]
        right = [[c[0], c[1], c[2], [1.0 if t else -1.0 for t in self.truth[c]]] for c in cases]
        self.assertEqual(S.balanced(right, self.truth), 1.0)
        all_yes = [[c[0], c[1], c[2], [1.0, 1.0, 1.0]] for c in cases]
        self.assertAlmostEqual(S.balanced(all_yes, self.truth), 0.5)


if __name__ == "__main__":
    unittest.main()
