from route_engine.graph.node import Node
from route_engine.graph.edge import Edge


class Graph:
    def __init__(self):
        # Store nodes using their unique IDs
        self.nodes: dict[str, Node] = {}

        # Adjacency list: source node ID -> outgoing edges
        self.adjacency_list: dict[str, list[Edge]] = {}

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        if node.id in self.nodes:
            raise ValueError(f"Node '{node.id}' already exists")

        self.nodes[node.id] = node
        self.adjacency_list[node.id] = []

    def add_edge(self, source: str, edge: Edge) -> None:
        """Add a directed edge between existing nodes."""
        if source not in self.nodes:
            raise ValueError(f"Source node '{source}' does not exist")

        if edge.destination not in self.nodes:
            raise ValueError(
                f"Destination node '{edge.destination}' does not exist"
            )

        self.adjacency_list[source].append(edge)

    def get_node(self, node_id: str) -> Node:
        """Return a node by its ID."""
        if node_id not in self.nodes:
            raise KeyError(f"Node '{node_id}' does not exist")

        return self.nodes[node_id]

    def get_neighbors(self, node_id: str) -> list[Edge]:
        """Return all outgoing edges from a node."""
        if node_id not in self.adjacency_list:
            raise KeyError(f"Node '{node_id}' does not exist")

        return self.adjacency_list[node_id].copy()

    def has_node(self, node_id: str) -> bool:
        """Check whether a node exists."""
        return node_id in self.nodes

    def __len__(self) -> int:
        """Return the number of nodes."""
        return len(self.nodes)