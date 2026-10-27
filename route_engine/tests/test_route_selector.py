import unittest

from route_engine.graph.node import Node
from route_engine.graph.edge import Edge
from route_engine.graph.graph import Graph
from route_engine.routing.route_selector import (
    RoutingMode,
    select_route,
)
from route_engine.routing.cost import RoutingWeights


class TestRouteSelector(unittest.TestCase):

    def setUp(self):
        """Create a sample graph with three possible routes' nodes."""

        self.graph = Graph()

        self.graph.add_node(Node("A", 20.2961, 85.8245))
        self.graph.add_node(Node("B", 20.2970, 85.8250))
        self.graph.add_node(Node("C", 20.3000, 85.8300))
        self.graph.add_node(Node("D", 20.3050, 85.8350))

        # Route A -> B -> D:
        # Shorter and safer, but slower.
        self.graph.add_edge(
            "A",
            Edge(
                segment_id="segment_A_B",
                destination="B",
                distance_m=100,
                travel_time_s=60,
                current_risk=0.1,
                predicted_risk=0.1,
            ),
        )

        self.graph.add_edge(
            "B",
            Edge(
                segment_id="segment_B_D",
                destination="D",
                distance_m=100,
                travel_time_s=60,
                current_risk=0.1,
                predicted_risk=0.1,
            ),
        )

        # Route A -> C -> D:
        # Longer and riskier, but faster.
        self.graph.add_edge(
            "A",
            Edge(
                segment_id="segment_A_C",
                destination="C",
                distance_m=300,
                travel_time_s=20,
                current_risk=0.8,
                predicted_risk=0.8,
            ),
        )

        self.graph.add_edge(
            "C",
            Edge(
                segment_id="segment_C_D",
                destination="D",
                distance_m=300,
                travel_time_s=20,
                current_risk=0.8,
                predicted_risk=0.8,
            ),
        )

    # ---------------------------------------------------------
    # SHORTEST ROUTE TESTS
    # ---------------------------------------------------------

    def test_shortest_route(self):
        """SHORTEST mode should minimize total distance."""

        result = select_route(
            self.graph,
            "A",
            "D",
            mode=RoutingMode.SHORTEST,
        )

        self.assertEqual(result["path"], ["A", "B", "D"])
        self.assertEqual(result["total_cost"], 200)
        self.assertEqual(result["mode"], "shortest")
        self.assertEqual(result["risk_data_status"], "not_applicable")
        self.assertFalse(result["used_risk_fallback"])

    def test_shortest_route_does_not_require_risk_data(self):
        """SHORTEST mode should work when risk scores are missing."""

        graph = Graph()

        graph.add_node(Node("A", 20.2961, 85.8245))
        graph.add_node(Node("B", 20.2970, 85.8250))
        graph.add_node(Node("D", 20.3050, 85.8350))

        graph.add_edge(
            "A",
            Edge(
                segment_id="segment_A_B",
                destination="B",
                distance_m=100,
                travel_time_s=50,
            ),
        )

        graph.add_edge(
            "B",
            Edge(
                segment_id="segment_B_D",
                destination="D",
                distance_m=150,
                travel_time_s=60,
            ),
        )

        result = select_route(
            graph,
            "A",
            "D",
            mode=RoutingMode.SHORTEST,
        )

        self.assertEqual(result["path"], ["A", "B", "D"])
        self.assertEqual(result["total_cost"], 250)
        self.assertEqual(result["risk_data_status"], "not_applicable")
        self.assertFalse(result["used_risk_fallback"])

    # ---------------------------------------------------------
    # FASTEST ROUTE TESTS
    # ---------------------------------------------------------

    def test_fastest_route(self):
        """FASTEST mode should minimize total travel time."""

        result = select_route(
            self.graph,
            "A",
            "D",
            mode=RoutingMode.FASTEST,
        )

        self.assertEqual(result["path"], ["A", "C", "D"])
        self.assertEqual(result["total_cost"], 40)
        self.assertEqual(result["mode"], "fastest")
        self.assertEqual(result["risk_data_status"], "not_applicable")
        self.assertFalse(result["used_risk_fallback"])

    # ---------------------------------------------------------
    # SAFEST ROUTE TESTS
    # ---------------------------------------------------------

    def test_safest_route(self):
        """SAFEST mode should choose the lower-cost safer route."""

        weights = RoutingWeights(
            distance=0.2,
            current_risk=0.4,
            predicted_risk=0.4,
        )

        result = select_route(
            self.graph,
            "A",
            "D",
            mode=RoutingMode.SAFEST,
            weights=weights,
        )

        self.assertEqual(result["path"], ["A", "B", "D"])
        self.assertEqual(result["mode"], "safest")
        self.assertEqual(result["risk_data_status"], "complete")
        self.assertFalse(result["used_risk_fallback"])

    def test_safest_route_with_missing_predicted_risk(self):
        """
        SAFEST mode should use current risk if predicted risk is missing.
        The result should indicate incomplete risk data if that route wins.
        """

        graph = Graph()

        graph.add_node(Node("A", 20.2961, 85.8245))
        graph.add_node(Node("B", 20.2970, 85.8250))
        graph.add_node(Node("D", 20.3050, 85.8350))

        graph.add_edge(
            "A",
            Edge(
                segment_id="segment_A_B",
                destination="B",
                distance_m=100,
                travel_time_s=50,
                current_risk=0.2,
                predicted_risk=None,
            ),
        )

        graph.add_edge(
            "B",
            Edge(
                segment_id="segment_B_D",
                destination="D",
                distance_m=100,
                travel_time_s=50,
                current_risk=0.2,
                predicted_risk=None,
            ),
        )

        weights = RoutingWeights(
            distance=0.2,
            current_risk=0.8,
            predicted_risk=0.0,
        )

        result = select_route(
            graph,
            "A",
            "D",
            mode=RoutingMode.SAFEST,
            weights=weights,
        )

        self.assertEqual(result["path"], ["A", "B", "D"])
        self.assertEqual(result["mode"], "safest")
        self.assertEqual(result["risk_data_status"], "incomplete")
        self.assertTrue(result["used_risk_fallback"])

    def test_safest_route_with_missing_current_risk(self):
        """
        SAFEST mode should use predicted risk if current risk is missing.
        The result should indicate incomplete risk data if that route wins.
        """

        graph = Graph()

        graph.add_node(Node("A", 20.2961, 85.8245))
        graph.add_node(Node("B", 20.2970, 85.8250))
        graph.add_node(Node("D", 20.3050, 85.8350))

        graph.add_edge(
            "A",
            Edge(
                segment_id="segment_A_B",
                destination="B",
                distance_m=100,
                travel_time_s=50,
                current_risk=None,
                predicted_risk=0.2,
            ),
        )

        graph.add_edge(
            "B",
            Edge(
                segment_id="segment_B_D",
                destination="D",
                distance_m=100,
                travel_time_s=50,
                current_risk=None,
                predicted_risk=0.2,
            ),
        )

        weights = RoutingWeights(
            distance=0.2,
            current_risk=0.0,
            predicted_risk=0.8,
        )

        result = select_route(
            graph,
            "A",
            "D",
            mode=RoutingMode.SAFEST,
            weights=weights,
        )

        self.assertEqual(result["path"], ["A", "B", "D"])
        self.assertEqual(result["mode"], "safest")
        self.assertEqual(result["risk_data_status"], "incomplete")
        self.assertTrue(result["used_risk_fallback"])

    def test_safest_route_tracks_final_path_risk_completeness(self):
        """Risk completeness must describe the final selected path."""

        graph = Graph()

        for node_id in ("A", "B", "C", "D"):
            graph.add_node(Node(node_id, 20.0, 85.0))

        # Initially discovered route: incomplete risk data.
        graph.add_edge(
            "A",
            Edge(
                segment_id="A_B",
                destination="B",
                distance_m=100,
                travel_time_s=10,
                current_risk=0.1,
                predicted_risk=None,
            ),
        )

        graph.add_edge(
            "B",
            Edge(
                segment_id="B_D",
                destination="D",
                distance_m=100,
                travel_time_s=10,
                current_risk=0.1,
                predicted_risk=0.1,
            ),
        )

        # Alternative route: complete risk data.
        graph.add_edge(
            "A",
            Edge(
                segment_id="A_C",
                destination="C",
                distance_m=200,
                travel_time_s=10,
                current_risk=0.1,
                predicted_risk=0.1,
            ),
        )

        graph.add_edge(
            "C",
            Edge(
                segment_id="C_D",
                destination="D",
                distance_m=200,
                travel_time_s=10,
                current_risk=0.1,
                predicted_risk=0.1,
            ),
        )

        weights = RoutingWeights(
            distance=1.0,
            current_risk=0.0,
            predicted_risk=0.0,
        )

        result = select_route(
            graph,
            "A",
            "D",
            mode=RoutingMode.SAFEST,
            weights=weights,
        )

        self.assertEqual(result["path"], ["A", "B", "D"])
        self.assertEqual(result["risk_data_status"], "incomplete")
        self.assertTrue(result["used_risk_fallback"])

    # ---------------------------------------------------------
    # VALIDATION TESTS
    # ---------------------------------------------------------

    def test_invalid_source(self):
        """An unknown source node should raise ValueError."""

        with self.assertRaises(ValueError):
            select_route(
                self.graph,
                "UNKNOWN",
                "D",
                mode=RoutingMode.SHORTEST,
            )

    def test_invalid_destination(self):
        """An unknown destination node should raise ValueError."""

        with self.assertRaises(ValueError):
            select_route(
                self.graph,
                "A",
                "UNKNOWN",
                mode=RoutingMode.SHORTEST,
            )

    def test_invalid_routing_mode(self):
        """An unsupported routing mode should raise ValueError."""

        with self.assertRaises(ValueError):
            select_route(
                self.graph,
                "A",
                "D",
                mode="invalid_mode",
            )

    def test_safest_mode_requires_weights(self):
        """SAFEST mode should require RoutingWeights."""

        with self.assertRaises(ValueError):
            select_route(
                self.graph,
                "A",
                "D",
                mode=RoutingMode.SAFEST,
            )

    def test_safest_mode_rejects_invalid_distance_scale(self):
        """SAFEST mode should reject a non-positive distance scale."""

        weights = RoutingWeights(
            distance=0.2,
            current_risk=0.4,
            predicted_risk=0.4,
        )

        with self.assertRaises(ValueError):
            select_route(
                self.graph,
                "A",
                "D",
                mode=RoutingMode.SAFEST,
                weights=weights,
                distance_scale_m=0,
            )

    def test_source_equals_destination(self):
        """A route from a node to itself should have zero cost."""

        result = select_route(
            self.graph,
            "A",
            "A",
            mode=RoutingMode.SHORTEST,
        )

        self.assertEqual(result["path"], ["A"])
        self.assertEqual(result["total_cost"], 0.0)
        self.assertEqual(result["explored_nodes"], 1)


if __name__ == "__main__":
    unittest.main()