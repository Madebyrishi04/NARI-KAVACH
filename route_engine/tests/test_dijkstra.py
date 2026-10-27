import unittest

from route_engine.graph.graph import Graph
from route_engine.graph.node import Node
from route_engine.graph.edge import Edge
from route_engine.algorithms.dijkstra import dijkstra


class TestDijkstra(unittest.TestCase):

    def setUp(self):
        self.graph = Graph()

        self.graph.add_node(Node("A", 20.2961, 85.8245))
        self.graph.add_node(Node("B", 20.2970, 85.8250))
        self.graph.add_node(Node("C", 20.2980, 85.8260))
        self.graph.add_node(Node("D", 20.2990, 85.8270))

        self.graph.add_edge(
            "A",
            Edge(
                segment_id="segment_A_B",
                destination="B",
                distance_m=100,
                travel_time_s=20,
            ),
        )

        self.graph.add_edge(
            "A",
            Edge(
                segment_id="segment_A_C",
                destination="C",
                distance_m=300,
                travel_time_s=40,
            ),
        )

        self.graph.add_edge(
            "C",
            Edge(
                segment_id="segment_C_D",
                destination="D",
                distance_m=100,
                travel_time_s=20,
            ),
        )

        self.graph.add_edge(
            "B",
            Edge(
                segment_id="segment_B_D",
                destination="D",
                distance_m=200,
                travel_time_s=30,
            ),
        )

    def test_shortest_path(self):
        result = dijkstra(self.graph, "A", "D")

        self.assertEqual(result["path"], ["A", "B", "D"])
        self.assertEqual(result["distance_m"], 300)

    def test_source_equals_destination(self):
        result = dijkstra(self.graph, "A", "A")

        self.assertEqual(result["path"], ["A"])
        self.assertEqual(result["distance_m"], 0.0)

    def test_unreachable_destination(self):
        self.graph.add_node(Node("E", 20.3000, 85.8280))

        result = dijkstra(self.graph, "A", "E")

        self.assertEqual(result["path"], [])
        self.assertIsNone(result["distance_m"])

    def test_invalid_source(self):
        with self.assertRaises(ValueError):
            dijkstra(self.graph, "X", "D")

    def test_invalid_destination(self):
        with self.assertRaises(ValueError):
            dijkstra(self.graph, "A", "X")


if __name__ == "__main__":
    unittest.main()