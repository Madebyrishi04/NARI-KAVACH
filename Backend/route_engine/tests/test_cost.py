import unittest

from route_engine.routing.cost import (
    RoutingWeights,
    calculate_edge_cost,
)


class TestRoutingCost(unittest.TestCase):

    def setUp(self):
        self.weights = RoutingWeights(
            distance=0.5,
            current_risk=0.3,
            predicted_risk=0.2,
        )

    def test_cost_calculation(self):
        cost = calculate_edge_cost(
            normalized_distance=0.4,
            current_risk=0.2,
            predicted_risk=0.6,
            weights=self.weights,
        )

        expected = 0.5 * 0.4 + 0.3 * 0.2 + 0.2 * 0.6

        self.assertAlmostEqual(cost, expected)

    def test_zero_risk(self):
        cost = calculate_edge_cost(
            normalized_distance=0.5,
            current_risk=0.0,
            predicted_risk=0.0,
            weights=self.weights,
        )

        self.assertAlmostEqual(cost, 0.25)

    def test_missing_risk_rejected(self):
        with self.assertRaises(ValueError):
            calculate_edge_cost(
                normalized_distance=0.5,
                current_risk=None,
                predicted_risk=0.2,
                weights=self.weights,
            )

    def test_invalid_risk_rejected(self):
        with self.assertRaises(ValueError):
            calculate_edge_cost(
                normalized_distance=0.5,
                current_risk=1.5,
                predicted_risk=0.2,
                weights=self.weights,
            )

    def test_negative_weight_rejected(self):
        with self.assertRaises(ValueError):
            RoutingWeights(
                distance=-0.1,
                current_risk=0.6,
                predicted_risk=0.5,
            )


if __name__ == "__main__":
    unittest.main()