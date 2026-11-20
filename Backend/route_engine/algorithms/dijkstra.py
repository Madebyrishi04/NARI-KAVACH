import heapq
from math import inf

from route_engine.graph.graph import Graph


def dijkstra(graph: Graph, source: str, destination: str) -> dict:
    """
    Find the shortest-distance path between two nodes.

    Returns the path, total distance, and number of explored nodes.
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

    priority_queue = [(0.0, source)]
    explored_nodes = 0

    while priority_queue:
        current_distance, current_node = heapq.heappop(
            priority_queue
        )

        # Ignore outdated priority-queue entries.
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

                heapq.heappush(
                    priority_queue,
                    (new_distance, neighbor)
                )

    if distances[destination] == inf:
        return {
            "path": [],
            "distance_m": None,
            "explored_nodes": explored_nodes,
        }

    # Reconstruct the path from destination to source.
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