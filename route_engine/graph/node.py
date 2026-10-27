from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    id: str
    latitude: float
    longitude: float