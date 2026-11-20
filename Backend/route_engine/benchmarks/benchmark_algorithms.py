import csv
import statistics
import time
from pathlib import Path

from route_engine.graph.graph import Graph
from route_engine.graph.node import Node
from route_engine.graph.edge import Edge
from route_engine.algorithms.dijkstra import dijkstra
from route_engine.algorithms.astar import astar, haversine_distance


def generate_road_graph(size: int) -> Graph:
    """Generate a grid-shaped road graph for benchmarking."""

    if size < 2:
        raise ValueError("Grid size must be at least 2")

    graph = Graph()

    base_latitude = 20.2961
    base_longitude = 85.8245
    coordinate_step = 0.001

    # Create grid nodes.
    for row in range(size):
        for col in range(size):
            node_id = f"N_{row}_{col}"

            graph.add_node(
                Node(
                    id=node_id,
                    latitude=base_latitude + row * coordinate_step,
                    longitude=base_longitude + col * coordinate_step,
                )
            )

    # Connect neighboring nodes in both directions.
    for row in range(size):
        for col in range(size):
            source = f"N_{row}_{col}"

            neighbors = []

            if col + 1 < size:
                neighbors.append(f"N_{row}_{col + 1}")

            if row + 1 < size:
                neighbors.append(f"N_{row + 1}_{col}")

            for destination in neighbors:
                source_node = graph.get_node(source)
                destination_node = graph.get_node(destination)

                distance = haversine_distance(
                    source_node,
                    destination_node,
                )

                # Approximate travel time at 5 metres per second.
                travel_time = distance / 5.0

                # Forward directed edge.
                graph.add_edge(
                    source,
                    Edge(
                        segment_id=f"segment_{source}_{destination}",
                        destination=destination,
                        distance_m=distance,
                        travel_time_s=travel_time,
                    ),
                )

                # Reverse directed edge.
                graph.add_edge(
                    destination,
                    Edge(
                        segment_id=f"segment_{destination}_{source}",
                        destination=source,
                        distance_m=distance,
                        travel_time_s=travel_time,
                    ),
                )

    return graph


def benchmark_algorithm(
    algorithm,
    graph: Graph,
    source: str,
    destination: str,
    repetitions: int = 7,
) -> dict:
    """Run an algorithm repeatedly and calculate median execution time."""

    if repetitions < 1:
        raise ValueError("Repetitions must be at least 1")

    execution_times = []
    result = None

    for _ in range(repetitions):
        start_time = time.perf_counter()

        result = algorithm(graph, source, destination)

        end_time = time.perf_counter()

        execution_times.append(
            (end_time - start_time) * 1000
        )

    return {
        "execution_time_ms": statistics.median(execution_times),
        "distance_m": result["distance_m"],
        "explored_nodes": result["explored_nodes"],
        "path": result["path"],
    }


def run_benchmark() -> list[dict]:
    """Compare Dijkstra and A* on grids of different sizes."""

    grid_sizes = [10, 25, 50]
    repetitions = 7

    results = []

    for size in grid_sizes:
        print(f"\nBenchmarking {size}x{size} grid...")

        graph = generate_road_graph(size)

        source = "N_0_0"
        destination = f"N_{size - 1}_{size - 1}"

        dijkstra_result = benchmark_algorithm(
            dijkstra,
            graph,
            source,
            destination,
            repetitions,
        )

        astar_result = benchmark_algorithm(
            astar,
            graph,
            source,
            destination,
            repetitions,
        )

        # Ensure both algorithms find a route.
        if dijkstra_result["distance_m"] is None:
            raise RuntimeError(
                f"Dijkstra could not find a route for grid size {size}"
            )

        if astar_result["distance_m"] is None:
            raise RuntimeError(
                f"A* could not find a route for grid size {size}"
            )

        # Verify both algorithms return the same shortest distance.
        if abs(
            dijkstra_result["distance_m"]
            - astar_result["distance_m"]
        ) > 1e-6:
            raise AssertionError(
                f"Shortest-distance mismatch for grid size {size}: "
                f"Dijkstra={dijkstra_result['distance_m']}, "
                f"A*={astar_result['distance_m']}"
            )

        results.append(
            {
                "grid_size": f"{size}x{size}",
                "nodes": len(graph),
                "algorithm": "Dijkstra",
                "execution_time_ms": round(
                    dijkstra_result["execution_time_ms"], 4
                ),
                "distance_m": round(
                    dijkstra_result["distance_m"], 4
                ),
                "explored_nodes": dijkstra_result["explored_nodes"],
                "repetitions": repetitions,
            }
        )

        results.append(
            {
                "grid_size": f"{size}x{size}",
                "nodes": len(graph),
                "algorithm": "A*",
                "execution_time_ms": round(
                    astar_result["execution_time_ms"], 4
                ),
                "distance_m": round(
                    astar_result["distance_m"], 4
                ),
                "explored_nodes": astar_result["explored_nodes"],
                "repetitions": repetitions,
            }
        )

        print(
            f"Dijkstra: {dijkstra_result['execution_time_ms']:.4f} ms | "
            f"Explored nodes: {dijkstra_result['explored_nodes']}"
        )

        print(
            f"A*:       {astar_result['execution_time_ms']:.4f} ms | "
            f"Explored nodes: {astar_result['explored_nodes']}"
        )

        print(
            f"Shortest distance: "
            f"{dijkstra_result['distance_m']:.4f} m"
        )

    # Save the benchmark results beside this script.
    output_path = (
        Path(__file__).resolve().parent / "benchmark_results.csv"
    )

    fieldnames = [
        "grid_size",
        "nodes",
        "algorithm",
        "execution_time_ms",
        "distance_m",
        "explored_nodes",
        "repetitions",
    ]

    with output_path.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)

    print(f"\nBenchmark results saved to: {output_path}")

    return results


if __name__ == "__main__":
    run_benchmark()