"""Regression tests for deterministic analysis post-processing (IMP-2)."""

import unittest
from types import SimpleNamespace

from analysis import SEED, TEMPERATURE, _generate, _postprocess
from prompts import ClauseFlag


def flag(text: str, level: str, explanation: str = "Review this term.") -> ClauseFlag:
    return ClauseFlag(clause_text=text, risk_level=level, explanation=explanation)


class PostprocessTests(unittest.TestCase):
    def test_same_findings_have_same_order_independent_of_model_order(self):
        source = "First clause. Second clause. Third clause."
        findings = [
            flag("Third clause.", "Low"),
            flag("First clause.", "High"),
            flag("Second clause.", "Medium"),
        ]

        forward = _postprocess(findings, source)
        reversed_order = _postprocess(list(reversed(findings)), source)

        self.assertEqual(forward, reversed_order)
        self.assertEqual(
            [(item.clause_text, item.risk_level) for item in forward],
            [
                ("First clause.", "High"),
                ("Second clause.", "Medium"),
                ("Third clause.", "Low"),
            ],
        )

    def test_duplicate_excerpt_keeps_highest_risk(self):
        result = _postprocess(
            [
                flag("CLIENT may terminate at any time.", "Low"),
                flag("client MAY terminate at any time.", "High"),
            ],
            "Client may terminate at any time.",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].risk_level, "High")

    def test_model_call_uses_zero_temperature_and_fixed_seed(self):
        captured = {}

        class FakeModels:
            def generate_content(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(text='{"flags": []}', parsed=None)

        client = SimpleNamespace(models=FakeModels())
        response, error = _generate(client, "test-model", "Sample contract")

        self.assertIsNone(error)
        self.assertIsNotNone(response)
        self.assertEqual(captured["config"].temperature, TEMPERATURE)
        self.assertEqual(captured["config"].temperature, 0.0)
        self.assertEqual(captured["config"].seed, SEED)
        self.assertIsInstance(captured["config"].seed, int)


if __name__ == "__main__":
    unittest.main()
