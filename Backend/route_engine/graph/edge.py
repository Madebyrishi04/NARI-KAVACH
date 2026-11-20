from dataclasses import dataclass
from math import isfinite
from typing import Optional


@dataclass(frozen=True)
class Edge:
    segment_id: str
    destination: str
    distance_m: float
    travel_time_s: float
    current_risk: Optional[float] = None
    predicted_risk: Optional[float] = None
    geometry: tuple[tuple[float, float], ...] = ()

    def __post_init__(self):
        # Validate road-segment identity.
        if not isinstance(self.segment_id, str) or not self.segment_id.strip():
            raise ValueError("Segment ID cannot be empty")

        # Validate destination.
        if not isinstance(self.destination, str) or not self.destination.strip():
            raise ValueError("Destination cannot be empty")

        # Validate distance.
        if (
            isinstance(self.distance_m, bool)
            or not isinstance(self.distance_m, (int, float))
            or not isfinite(self.distance_m)
            or self.distance_m < 0
        ):
            raise ValueError(
                "Distance must be a finite, non-negative number"
            )

        # Validate travel time.
        if (
            isinstance(self.travel_time_s, bool)
            or not isinstance(self.travel_time_s, (int, float))
            or not isfinite(self.travel_time_s)
            or self.travel_time_s < 0
        ):
            raise ValueError(
                "Travel time must be a finite, non-negative number"
            )

        # Validate optional risk scores.
        for name, risk in (
            ("current_risk", self.current_risk),
            ("predicted_risk", self.predicted_risk),
        ):
            if risk is not None and (
                isinstance(risk, bool)
                or not isinstance(risk, (int, float))
                or not isfinite(risk)
                or not 0.0 <= risk <= 1.0
            ):
                raise ValueError(
                    f"{name} must be between 0 and 1, or None"
                )