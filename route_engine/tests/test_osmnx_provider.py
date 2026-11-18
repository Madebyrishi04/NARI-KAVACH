import unittest
from unittest.mock import patch

import networkx as nx

from route_engine.road_network.osmnx_provider import build_road_graph


class TestOSMnxProvider(unittest.TestCase):

    def setUp(self):
        self.osm_graph = nx.MultiDiGraph()

        self.osm_graph.add_node(
            1,
            y=20.35,
            x=85.81,
        )
        self.osm_graph.add_node(
            2,
            y=20.36,
            x=85.82,
        )

        self.osm_graph.add_edge(
            1,
            2,
            key=0,
            length=150.0,
            travel_time=12.0,
        )

    @patch(
        "route_engine.road_network.osmnx_provider.ox.routing.add_edge_travel_times"
    )
    @patch(
        "route_engine.road_network.osmnx_provider.ox.routing.add_edge_speeds"
    )
    @patch(
        "route_engine.road_network.osmnx_provider.ox.graph.graph_from_point"
    )
    def test_builds_graph_from_osmnx_data(
        self,
        mock_graph_from_point,
        mock_add_edge_speeds,
        mock_add_edge_travel_times,
    ):
        mock_graph_from_point.return_value = self.osm_graph
        mock_add_edge_speeds.side_effect = lambda graph: graph
        mock_add_edge_travel_times.side_effect = lambda graph: graph

        graph = build_road_graph(
            latitude=20.35,
            longitude=85.81,
            dist_m=500,
            network_type="drive",
        )

        self.assertEqual(len(graph.nodes), 2)
        self.assertEqual(len(graph.adjacency_list[ "1"]), 1)

        node = graph.get_node("1")
        self.assertAlmostEqual(node.latitude, 20.35)
        self.assertAlmostEqual(node.longitude, 85.81)

        edge = graph.adjacency_list["1"][0]

        self.assertEqual(edge.destination, "2")
        self.assertEqual(edge.distance_m, 150.0)
        self.assertEqual(edge.travel_time_s, 12.0)
        self.assertIsNone(edge.current_risk)
        self.assertIsNone(edge.predicted_risk)

        mock_graph_from_point.assert_called_once_with(
            (20.35, 85.81),
            dist=500,
            network_type="drive",
            simplify=True,
            retain_all=False,
            truncate_by_edge=True,
        )

        mock_add_edge_speeds.assert_called_once_with(self.osm_graph)
        mock_add_edge_travel_times.assert_called_once_with(self.osm_graph)

    @patch(
        "route_engine.road_network.osmnx_provider.ox.routing.add_edge_travel_times"
    )
    @patch(
        "route_engine.road_network.osmnx_provider.ox.routing.add_edge_speeds"
    )
    @patch(
        "route_engine.road_network.osmnx_provider.ox.graph.graph_from_point"
    )
    def test_preserves_edge_geometry(
        self,
        mock_graph_from_point,
        mock_add_edge_speeds,
        mock_add_edge_travel_times,
    ):
        from shapely.geometry import LineString

        self.osm_graph.edges[1, 2, 0]["geometry"] = LineString(
            [
                (85.81, 20.35),
                (85.815, 20.355),
                (85.82, 20.36),
            ]
        )

        mock_graph_from_point.return_value = self.osm_graph
        mock_add_edge_speeds.side_effect = lambda graph: graph
        mock_add_edge_travel_times.side_effect = lambda graph: graph

        graph = build_road_graph(20.35, 85.81, 500)

        edge = graph.adjacency_list["1"][0]

        self.assertEqual(
            edge.geometry,
            (
                (20.35, 85.81),
                (20.355, 85.815),
                (20.36, 85.82),
            ),
        )

    def test_rejects_invalid_latitude(self):
        for latitude in (-91, 91, float("nan"), float("inf"), True):
            with self.subTest(latitude=latitude):
                with self.assertRaises(ValueError):
                    build_road_graph(latitude, 85.81)

    def test_rejects_invalid_longitude(self):
        for longitude in (-181, 181, float("nan"), float("-inf"), True):
            with self.subTest(longitude=longitude):
                with self.assertRaises(ValueError):
                    build_road_graph(20.35, longitude)

    def test_rejects_invalid_distance(self):
        for distance in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(distance=distance):
                with self.assertRaises(ValueError):
                    build_road_graph(20.35, 85.81, distance)

    def test_rejects_unsupported_network_type(self):
        with self.assertRaises(ValueError):
            build_road_graph(
                20.35,
                85.81,
                network_type="unsupported",
            )


if __name__ == "__main__":
    unittest.main()