from math import isfinite

import osmnx as ox

from route_engine.graph.edge import Edge
from route_engine.graph.graph import Graph
from route_engine.graph.node import Node


def build_road_graph(
    latitude: float,
    longitude: float,
    dist_m: float = 1000.0,
    network_type: str = "drive",
) -> Graph:
    """Download an OSM road network and convert it to the project's Graph."""

    for name, value, lower, upper in (
        ("latitude", latitude, -90.0, 90.0),
        ("longitude", longitude, -180.0, 180.0),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or not lower <= value <= upper
        ):
            raise ValueError(
                f"{name} must be a finite value between {lower} and {upper}"
            )

    if (
        isinstance(dist_m, bool)
        or not isinstance(dist_m, (int, float))
        or not isfinite(dist_m)
        or dist_m <= 0
    ):
        raise ValueError("dist_m must be a finite positive number")

    allowed_network_types = {
        "drive",
        "drive_service",
        "walk",
        "bike",
        "all",
    }

    if network_type not in allowed_network_types:
        raise ValueError(
            f"Unsupported network_type: {network_type!r}"
        )

    osm_graph = ox.graph.graph_from_point(
        (latitude, longitude),
        dist=dist_m,
        network_type=network_type,
        simplify=True,
        retain_all=False,
        truncate_by_edge=True,
    )

    osm_graph = ox.routing.add_edge_speeds(osm_graph)
    osm_graph = ox.routing.add_edge_travel_times(osm_graph)

    graph = Graph()

    for osm_node_id, data in osm_graph.nodes(data=True):
        graph.add_node(
            Node(
                id=str(osm_node_id),
                latitude=float(data["y"]),
                longitude=float(data["x"]),
            )
        )

    for source, destination, key, data in osm_graph.edges(
        keys=True,
        data=True,
    ):
        distance_m = float(data["length"])
        travel_time_s = float(data["travel_time"])

        if not isfinite(distance_m) or distance_m < 0:
            raise ValueError("OSM road edge has an invalid length")

        if not isfinite(travel_time_s) or travel_time_s < 0:
            raise ValueError("OSM road edge has an invalid travel time")

        geometry = data.get("geometry")

        if geometry is not None:
            coordinates = tuple(
                (float(lat), float(lon))
                for lon, lat in geometry.coords
            )
        else:
            source_data = osm_graph.nodes[source]
            destination_data = osm_graph.nodes[destination]

            coordinates = (
                (float(source_data["y"]), float(source_data["x"])),
                (
                    float(destination_data["y"]),
                    float(destination_data["x"]),
                ),
            )

        graph.add_edge(
            str(source),
            Edge(
                segment_id=f"osm:{source}:{destination}:{key}",
                destination=str(destination),
                distance_m=distance_m,
                travel_time_s=travel_time_s,
                current_risk=None,
                predicted_risk=None,
                geometry=coordinates,
            ),
        )

    return graph