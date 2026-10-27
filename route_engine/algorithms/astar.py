import heapq
from math import asin, cos, inf, radians, sin, sqrt

from route_engine.graph.graph import Graph


def haversine_distance(node_a, node_b) -> float:
    """
    Calculate straight-line geographic distance between two nodes.
    Returns distance in metres.
    """
    earth_radius_m = 6_371_000

    lat1 = radians(node_a.latitude)
    lon1 = radians(node_a.longitude)
    lat2 = radians(node_b.latitude)
    lon2 = radians(node_b.longitude)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )

    # Protect against floating-point rounding errors.
    a = max(0.0, min(1.0, a))

    return 2 * earth_radius_m * asin(sqrt(a))


def astar(graph: Graph, source: str, destination: str) -> dict:
    """
    Find a shortest-distance path using A*.

    Returns the path, distance, and number of explored nodes.
    """

    if not graph.has_node(source):
        raise ValueError(f"Source node '{source}' does not exist")

    if not graph.has_node(destination):
        raise ValueError(
            f"Destination node '{destination}' does not exist"
        )

    distances = {node_id: inf for node_id in graph.nodes}
    previous = {node_id: None for node_id in graph.nodes}

    distances[source] = 0.0

    destination_node = graph.get_node(destination)

    priority_queue = [
        (
            haversine_distance(
                graph.get_node(source), destination_node
            ),
            0.0,
            source,
        )
    ]

    explored_nodes = 0

    while priority_queue:
        _, current_distance, current_node = heapq.heappop(
            priority_queue
        )

        # Ignore outdated entries.
        if current_distance > distances[current_node]:
            continue

        explored_nodes += 1

        if current_node == destination:
            break

        for edge in graph.get_neighbors(current_node):
            neighbor = edge.destination

            new_distance = current_distance + edge.distance_m

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current_node

                heuristic = haversine_distance(
                    graph.get_node(neighbor),
                    destination_node,
                )

                estimated_total = new_distance + heuristic

                heapq.heappush(
                    priority_queue,
                    (estimated_total, new_distance, neighbor),
                )

    if distances[destination] == inf:
        return {
            "path": [],
            "distance_m": None,
            "explored_nodes": explored_nodes,
        }

    path = []
    current_node = destination

    while current_node is not None:
        path.append(current_node)
        current_node = previous[current_node]

    path.reverse()

    return {
        "path": path,
        "distance_m": distances[destination],
        "explored_nodes": explored_nodes,
    }