"""Tests de la aritmética de la Fase 1. No necesitan el modelo.

Se ejecutan con:  uv run --python 3.12 test_enrich.py
"""

import unittest

from enrich import CASE, compute_facts, render_enriched, render_narrative

DAILY = CASE["daily_demand_units"]


def case_with(**overrides):
    """El caso de la fase, con los cambios puntuales que pida cada test."""
    return {**CASE, **overrides}


class ArithmeticTest(unittest.TestCase):
    """Los tres hechos calculados sobre el caso real de la fase."""

    def test_coverage_is_stock_over_daily_demand(self):
        facts = compute_facts(CASE)
        self.assertAlmostEqual(facts["coverage_days"], 5.0)

    def test_shortage_is_delay_minus_coverage(self):
        facts = compute_facts(CASE)
        self.assertAlmostEqual(facts["shortage_days"], 7.0)

    def test_missing_units_is_shortage_times_daily_demand(self):
        facts = compute_facts(CASE)
        self.assertAlmostEqual(facts["missing_units"], 7.0 * DAILY)


class EdgeCaseTest(unittest.TestCase):
    """Los bordes que un caso real puede traer."""

    def test_without_stock_the_whole_delay_is_a_shortage(self):
        facts = compute_facts(case_with(stock_units=0))
        self.assertAlmostEqual(facts["coverage_days"], 0.0)
        self.assertAlmostEqual(facts["shortage_days"], 12.0)
        self.assertAlmostEqual(facts["missing_units"], 12.0 * DAILY)

    def test_when_stock_covers_the_delay_there_is_no_shortage(self):
        facts = compute_facts(case_with(stock_units=20 * DAILY))
        self.assertAlmostEqual(facts["coverage_days"], 20.0)
        self.assertAlmostEqual(facts["shortage_days"], 0.0)
        self.assertAlmostEqual(facts["missing_units"], 0.0)


class ValidationTest(unittest.TestCase):
    """Datos que no representan una operación real se rechazan, no se calculan."""

    def test_daily_demand_must_be_positive(self):
        with self.assertRaises(ValueError):
            compute_facts(case_with(daily_demand_units=0))
        with self.assertRaises(ValueError):
            compute_facts(case_with(daily_demand_units=-5))

    def test_negative_stock_or_delay_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_facts(case_with(stock_units=-1))
        with self.assertRaises(ValueError):
            compute_facts(case_with(supplier_delay_days=-3))


class FactBoundaryTest(unittest.TestCase):
    """La frontera de la fase: hechos calculados, nunca veredictos."""

    def test_facts_contain_exactly_the_three_computed_quantities(self):
        facts = compute_facts(CASE)
        self.assertEqual(set(facts), {"coverage_days", "shortage_days", "missing_units"})

    def test_enriched_state_keeps_the_whole_narrative(self):
        facts = compute_facts(CASE)
        narrative = render_narrative(CASE)
        enriched = render_enriched(CASE, facts)
        self.assertTrue(enriched.startswith(narrative))
        self.assertGreater(len(enriched), len(narrative))

    def test_enriched_state_shows_the_computed_numbers(self):
        facts = compute_facts(CASE)
        enriched = render_enriched(CASE, facts)
        self.assertIn("5.0 días", enriched)     # cobertura
        self.assertIn("7.0 días", enriched)     # días sin cobertura
        self.assertIn("700.0 unidades", enriched)


if __name__ == "__main__":
    unittest.main(verbosity=2)
