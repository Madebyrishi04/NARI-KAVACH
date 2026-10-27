from dataclasses import dataclass
from math import isfinite
from typing import Optional


@dataclass(frozen=True)
class RoutingWeights:
    distance: float
    current_risk: float
    predicted_risk: float

    def __post_init__(self):
        weights = (
            self.distance,
            self.current_risk,
            self.predicted_risk,
        )

        if any(
            not isfinite(weight) or weight < 0
            for weight in weights
        ):
            raise ValueError(
                "Routing weights must be finite and non-negative"
            )

        if sum(weights) == 0:
            raise ValueError("At least one routing weight must be positive")


def calculate_edge_cost(
    normalized_distance: float,
    current_risk: Optional[float],
    predicted_risk: Optional[float],
    weights: RoutingWeights,
) -> float:
    """
    Calculate the weighted cost of a road segment.

    Missing risk values are rejected rather than silently treated as zero.
    """

    if (
        not isfinite(normalized_distance)
        or normalized_distance < 0
    ):
        raise ValueError(
            "Normalized distance must be finite and non-negative"
        )

    if current_risk is None or predicted_risk is None:
        raise ValueError(
            "Current and predicted risk must be provided"
        )

    for name, risk in (
        ("current_risk", current_risk),
        ("predicted_risk", predicted_risk),
    ):
        if (
            isinstance(risk, bool)
            or not isinstance(risk, (int, float))
            or not isfinite(risk)
            or not 0 <= risk <= 1
        ):
            raise ValueError(
                f"{name} must be a finite number between 0 and 1"
            )

    return (
        weights.distance * normalized_distance
        + weights.current_risk * current_risk
        + weights.predicted_risk * predicted_risk
    )