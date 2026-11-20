import unittest

from route_engine.graph.node import Node
from route_engine.graph.edge import Edge
from route_engine.graph.graph import Graph


class TestGraph(unittest.TestCase):

    def setUp(self):
        self.graph = Graph()

        self.node_a = Node("A", 20.2961, 85.8245)
        self.node_b = Node("B", 20.2970, 85.8250)
        self.node_c = Node("C", 20.2980, 85.8260)

        self.graph.add_node(self.node_a)
        self.graph.add_node(self.node_b)
        self.graph.add_node(self.node_c)

    def test_add_node(self):
        self.assertTrue(self.graph.has_node("A"))
        self.assertEqual(len(self.graph), 3)

    def test_duplicate_node(self):
        with self.assertRaises(ValueError):
            self.graph.add_node(self.node_a)

    def test_add_edge(self):
        edge = Edge(
            segment_id="segment_A_B",
            destination="B",
            distance_m=100,
            travel_time_s=20,
        )

        self.graph.add_edge("A", edge)

        self.assertEqual(
            self.graph.get_neighbors("A"),
            [edge],
        )

    def test_invalid_source(self):
        edge = Edge(
            segment_id="segment_X_B",
            destination="B",
            distance_m=100,
            travel_time_s=20,
        )

        with self.assertRaises(ValueError):
            self.graph.add_edge("X", edge)

    def test_invalid_destination(self):
        edge = Edge(
            segment_id="segment_A_X",
            destination="X",
            distance_m=100,
            travel_time_s=20,
        )

        with self.assertRaises(ValueError):
            self.graph.add_edge("A", edge)

    def test_get_node(self):
        self.assertEqual(self.graph.get_node("A"), self.node_a)

    def test_get_missing_node(self):
        with self.assertRaises(KeyError):
            self.graph.get_node("X")

    def test_get_neighbors_returns_copy(self):
        neighbors = self.graph.get_neighbors("A")

        neighbors.append(
            Edge(
                segment_id="segment_A_B_extra",
                destination="B",
                distance_m=50,
                travel_time_s=10,
            )
        )

        self.assertEqual(self.graph.get_neighbors("A"), [])

    def test_missing_neighbors(self):
        with self.assertRaises(KeyError):
            self.graph.get_neighbors("X")


if __name__ == "__main__":
    unittest.main()