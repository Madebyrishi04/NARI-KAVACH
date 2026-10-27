from dataclasses import dataclass
from math import isfinite
from typing import Any, Optional

from route_engine.graph.edge import Edge
from route_engine.graph.graph import Graph


class RiskDataError(ValueError):
    """Raised when risk data does not match the expected contract."""


@dataclass(frozen=True)
class SegmentRisk:
    """Risk scores associated with a road segment."""

    current_risk: Optional[float]
    predicted_risk: Optional[float]
    current_status: str
    predicted_status: str


class RiskDataAdapter:
    """
    Validate incoming ML risk data and associate it with road segments.

    Expected structure:
    {
        "risk_data_version": "0.1",
        "source": "demo",
        "model_version": None,
        "generated_at": None,
        "segments": {
            "segment_A_B": {
                "current_risk": {
                    "score": 0.2,
                    "category": None,
                    "status": "available"
                },
                "predicted_risk": {
                    "score": None,
                    "category": None,
                    "status": "unavailable"
                }
            }
        }
    }
    """

    def __init__(self, payload: dict[str, Any]):
        if not isinstance(payload, dict):
            raise RiskDataError("Risk payload must be a dictionary")

        version = payload.get("risk_data_version")
        source = payload.get("source")
        segments = payload.get("segments")

        if not isinstance(version, str) or not version.strip():
            raise RiskDataError(
                "risk_data_version must be a non-empty string"
            )

        if not isinstance(source, str) or not source.strip():
            raise RiskDataError("source must be a non-empty string")

        if not isinstance(segments, dict):
            raise RiskDataError("segments must be a dictionary")

        self.risk_data_version = version
        self.source = source
        self.model_version = payload.get("model_version")
        self.generated_at = payload.get("generated_at")

        self._segments: dict[str, SegmentRisk] = {}

        for segment_id, segment_data in segments.items():
            if (
                not isinstance(segment_id, str)
                or not segment_id.strip()
            ):
                raise RiskDataError(
                    "Every segment must have a non-empty segment ID"
                )

            if not isinstance(segment_data, dict):
                raise RiskDataError(
                    f"Risk data for '{segment_id}' must be a dictionary"
                )

            current = self._parse_risk_component(
                segment_id,
                "current_risk",
                segment_data.get("current_risk"),
            )

            predicted = self._parse_risk_component(
                segment_id,
                "predicted_risk",
                segment_data.get("predicted_risk"),
            )

            self._segments[segment_id] = SegmentRisk(
                current_risk=current[0],
                current_status=current[1],
                predicted_risk=predicted[0],
                predicted_status=predicted[1],
            )

    @staticmethod
    def _parse_risk_component(
        segment_id: str,
        component_name: str,
        component: Any,
    ) -> tuple[Optional[float], str]:
        """Validate a current or predicted risk component."""

        if not isinstance(component, dict):
            raise RiskDataError(
                f"{component_name} for '{segment_id}' must be a dictionary"
            )

        score = component.get("score")
        status = component.get("status")

        if status not in ("available", "unavailable"):
            raise RiskDataError(
                f"Invalid status for {component_name} on '{segment_id}'"
            )

        if status == "unavailable":
            if score is not None:
                raise RiskDataError(
                    f"Unavailable {component_name} for '{segment_id}' "
                    "must have a null score"
                )

            return None, status

        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not isfinite(score)
            or not 0.0 <= score <= 1.0
        ):
            raise RiskDataError(
                f"Available {component_name} for '{segment_id}' "
                "must have a finite score between 0 and 1"
            )

        return float(score), status

    def get_segment_risk(
        self,
        segment_id: str,
    ) -> Optional[SegmentRisk]:
        """Return risk information for a segment, or None if absent."""

        return self._segments.get(segment_id)

    def apply_to_graph(self, graph: Graph) -> Graph:
        """
        Return a new graph with risk scores applied to matching edges.

        Original graph and edge objects are not modified.
        Unavailable or absent scores remain None.
        """
        updated_graph = Graph()

        for node in graph.nodes.values():
            updated_graph.add_node(node)

        for source, edges in graph.adjacency_list.items():
            for edge in edges:
                risk = self.get_segment_risk(edge.segment_id)

                if risk is None:
                    current_risk = None
                    predicted_risk = None
                else:
                    current_risk = risk.current_risk
                    predicted_risk = risk.predicted_risk

                updated_edge = Edge(
                    segment_id=edge.segment_id,
                    destination=edge.destination,
                    distance_m=edge.distance_m,
                    travel_time_s=edge.travel_time_s,
                    current_risk=current_risk,
                    predicted_risk=predicted_risk,
                    geometry=edge.geometry,
                )

                updated_graph.add_edge(source, updated_edge)

        return updated_graph