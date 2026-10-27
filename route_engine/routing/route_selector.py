import heapq
from enum import Enum
from math import inf, isfinite
from typing import Optional

from route_engine.graph.graph import Graph
from route_engine.routing.cost import (
    RoutingWeights,
    calculate_edge_cost,
)


class RoutingMode(str, Enum):
    SHORTEST = "shortest"
    FASTEST = "fastest"
    SAFEST = "safest"


def select_route(
    graph: Graph,
    source: str,
    destination: str,
    mode: RoutingMode = RoutingMode.SHORTEST,
    weights: Optional[RoutingWeights] = None,
    distance_scale_m: float = 1000.0,
) -> dict:
    """
    Find a route using the selected optimization mode.

    SHORTEST:
        Minimize distance in meters.

    FASTEST:
        Minimize travel time in seconds.

    SAFEST:
        Minimize weighted normalized distance and available risk scores.

        If only one risk score is available, use that risk component
        and report that the route used incomplete risk data.

        If neither risk score is available for an edge, that edge is
        excluded from SAFEST routing.

    Risk scores must be normalized to the range [0, 1].
    """

    if not graph.has_node(source):
        raise ValueError(
            f"Source node '{source}' does not exist"
        )

    if not graph.has_node(destination):
        raise ValueError(
            f"Destination node '{destination}' does not exist"
        )

    if not isinstance(mode, RoutingMode):
        try:
            mode = RoutingMode(mode)
        except (ValueError, TypeError):
            raise ValueError(
                f"Unsupported routing mode: {mode!r}"
            ) from None

    if mode == RoutingMode.SAFEST:
        if not isinstance(weights, RoutingWeights):
            raise ValueError(
                "SAFEST mode requires valid RoutingWeights"
            )

        if (
            isinstance(distance_scale_m, bool)
            or not isinstance(distance_scale_m, (int, float))
            or not isfinite(distance_scale_m)
            or distance_scale_m <= 0
        ):
            raise ValueError(
                "distance_scale_m must be a finite, positive number"
            )

    distances = {
        node_id: inf
        for node_id in graph.nodes
    }

    previous = {
        node_id: None
        for node_id in graph.nodes
    }

    distances[source] = 0.0
    priority_queue = [(0.0, source)]
    explored_nodes = 0

    # Track the completeness of risk data used during exploration.
    incomplete_risk_data_encountered = False

    # Track whether the selected path itself used incomplete data.
    incomplete_risk_edges = set()

    while priority_queue:
        current_cost, current_node = heapq.heappop(
            priority_queue
        )

        if current_cost > distances[current_node]:
            continue

        explored_nodes += 1

        if current_node == destination:
            break

        for edge in graph.get_neighbors(current_node):

            edge_used_incomplete_risk = False

            if mode == RoutingMode.SHORTEST:
                edge_cost = edge.distance_m

            elif mode == RoutingMode.FASTEST:
                edge_cost = edge.travel_time_s

            else:
                normalized_distance = (
                    edge.distance_m / distance_scale_m
                )

                current_risk = edge.current_risk
                predicted_risk = edge.predicted_risk

                if current_risk is None and predicted_risk is None:
                    incomplete_risk_data_encountered = True
                    continue

                # If only one score is available, use its weight
                # and ignore the unavailable component.
                if current_risk is None:
                    incomplete_risk_data_encountered = True
                    edge_used_incomplete_risk = True

                    edge_cost = (
                        weights.distance * normalized_distance
                        + weights.predicted_risk * predicted_risk
                    )

                elif predicted_risk is None:
                    incomplete_risk_data_encountered = True
                    edge_used_incomplete_risk = True

                    edge_cost = (
                        weights.distance * normalized_distance
                        + weights.current_risk * current_risk
                    )

                else:
                    edge_cost = calculate_edge_cost(
                        normalized_distance=normalized_distance,
                        current_risk=current_risk,
                        predicted_risk=predicted_risk,
                        weights=weights,
                    )

            new_cost = current_cost + edge_cost
            neighbor = edge.destination

            if new_cost < distances[neighbor]:
                distances[neighbor] = new_cost
                previous[neighbor] = current_node

                if edge_used_incomplete_risk:
                    incomplete_risk_edges.add(
                        (current_node, neighbor)
                    )
                else:
                    incomplete_risk_edges.discard(
                        (current_node, neighbor)
                    )

                heapq.heappush(
                    priority_queue,
                    (new_cost, neighbor),
                )

    if distances[destination] == inf:
        return {
            "path": [],
            "total_cost": None,
            "mode": mode.value,
            "explored_nodes": explored_nodes,
            "risk_data_status": (
                "incomplete"
                if mode == RoutingMode.SAFEST
                and incomplete_risk_data_encountered
                else "not_applicable"
                if mode != RoutingMode.SAFEST
                else "unavailable"
            ),
            "used_risk_fallback": False,
        }

    path = []
    current_node = destination

    while current_node is not None:
        path.append(current_node)
        current_node = previous[current_node]

    path.reverse()

    # Determine whether any selected path edge has incomplete risk data.
    selected_path_incomplete = any(
        (path[index], path[index + 1]) in incomplete_risk_edges
        for index in range(len(path) - 1)
    )

    return {
        "path": path,
        "total_cost": distances[destination],
        "mode": mode.value,
        "explored_nodes": explored_nodes,
        "risk_data_status": (
            "incomplete"
            if mode == RoutingMode.SAFEST
            and selected_path_incomplete
            else "complete"
            if mode == RoutingMode.SAFEST
            else "not_applicable"
        ),
        "used_risk_fallback": (
            mode == RoutingMode.SAFEST
            and selected_path_incomplete
        ),
    }