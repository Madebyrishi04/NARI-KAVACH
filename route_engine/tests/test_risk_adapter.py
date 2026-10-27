import unittest

from route_engine.graph.edge import Edge
from route_engine.graph.graph import Graph
from route_engine.graph.node import Node
from route_engine.risk.risk_adapter import (
    RiskDataAdapter,
    RiskDataError,
)


def make_payload():
    return {
        "risk_data_version": "0.1",
        "source": "demo",
        "model_version": None,
        "generated_at": None,
        "segments": {
            "segment_A_B": {
                "current_risk": {
                    "score": 0.2,
                    "category": None,
                    "status": "available",
                },
                "predicted_risk": {
                    "score": 0.4,
                    "category": None,
                    "status": "available",
                },
            },
            "segment_B_C": {
                "current_risk": {
                    "score": 0.3,
                    "category": None,
                    "status": "available",
                },
                "predicted_risk": {
                    "score": None,
                    "category": None,
                    "status": "unavailable",
                },
            },
        },
    }


class TestRiskDataAdapter(unittest.TestCase):

    def setUp(self):
        self.payload = make_payload()
        self.adapter = RiskDataAdapter(self.payload)

    def test_metadata_is_preserved(self):
        self.assertEqual(
            self.adapter.risk_data_version,
            "0.1",
        )
        self.assertEqual(self.adapter.source, "demo")
        self.assertIsNone(self.adapter.model_version)

    def test_get_segment_risk(self):
        risk = self.adapter.get_segment_risk("segment_A_B")

        self.assertIsNotNone(risk)
        self.assertEqual(risk.current_risk, 0.2)
        self.assertEqual(risk.predicted_risk, 0.4)

    def test_missing_segment_returns_none(self):
        self.assertIsNone(
            self.adapter.get_segment_risk("unknown_segment")
        )

    def test_unavailable_risk_remains_none(self):
        risk = self.adapter.get_segment_risk("segment_B_C")

        self.assertIsNotNone(risk)
        self.assertEqual(risk.current_risk, 0.3)
        self.assertIsNone(risk.predicted_risk)
        self.assertEqual(risk.predicted_status, "unavailable")

    def test_invalid_score_is_rejected(self):
        self.payload["segments"]["segment_A_B"]["current_risk"][
            "score"
        ] = 1.5

        with self.assertRaises(RiskDataError):
            RiskDataAdapter(self.payload)

    def test_boolean_score_is_rejected(self):
        self.payload["segments"]["segment_A_B"]["current_risk"][
            "score"
        ] = True

        with self.assertRaises(RiskDataError):
            RiskDataAdapter(self.payload)

    def test_unavailable_score_cannot_be_zero(self):
        self.payload["segments"]["segment_A_B"]["current_risk"][
            "score"
        ] = 0.0

        self.payload["segments"]["segment_A_B"]["current_risk"][
            "status"
        ] = "unavailable"

        with self.assertRaises(RiskDataError):
            RiskDataAdapter(self.payload)

    def test_apply_risk_to_graph(self):
        graph = Graph()

        graph.add_node(Node("A", 20.2961, 85.8245))
        graph.add_node(Node("B", 20.2970, 85.8250))
        graph.add_node(Node("C", 20.2980, 85.8260))

        graph.add_edge(
            "A",
            Edge(
                segment_id="segment_A_B",
                destination="B",
                distance_m=100,
                travel_time_s=20,
            ),
        )

        graph.add_edge(
            "B",
            Edge(
                segment_id="segment_B_C",
                destination="C",
                distance_m=150,
                travel_time_s=30,
            ),
        )

        updated_graph = self.adapter.apply_to_graph(graph)

        edge_ab = updated_graph.get_neighbors("A")[0]
        edge_bc = updated_graph.get_neighbors("B")[0]

        self.assertEqual(edge_ab.current_risk, 0.2)
        self.assertEqual(edge_ab.predicted_risk, 0.4)

        self.assertEqual(edge_bc.current_risk, 0.3)
        self.assertIsNone(edge_bc.predicted_risk)

    def test_original_graph_is_not_modified(self):
        graph = Graph()

        graph.add_node(Node("A", 20.2961, 85.8245))
        graph.add_node(Node("B", 20.2970, 85.8250))

        graph.add_edge(
            "A",
            Edge(
                segment_id="segment_A_B",
                destination="B",
                distance_m=100,
                travel_time_s=20,
            ),
        )

        updated_graph = self.adapter.apply_to_graph(graph)

        original_edge = graph.get_neighbors("A")[0]
        updated_edge = updated_graph.get_neighbors("A")[0]

        self.assertIsNone(original_edge.current_risk)
        self.assertEqual(updated_edge.current_risk, 0.2)

    def test_missing_segment_risk_stays_unavailable(self):
        graph = Graph()

        graph.add_node(Node("A", 20.2961, 85.8245))
        graph.add_node(Node("C", 20.2980, 85.8260))

        graph.add_edge(
            "A",
            Edge(
                segment_id="segment_A_C",
                destination="C",
                distance_m=200,
                travel_time_s=40,
            ),
        )

        updated_graph = self.adapter.apply_to_graph(graph)
        edge = updated_graph.get_neighbors("A")[0]

        self.assertIsNone(edge.current_risk)
        self.assertIsNone(edge.predicted_risk)


if __name__ == "__main__":
    unittest.main()