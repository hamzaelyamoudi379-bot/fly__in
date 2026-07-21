from typing import Optional


class Zone:
    """Represents a single zone (hub) in the delivery network.

    A Zone holds its identity (name), its position (x, y), optional
    display color, its maximum drone capacity, its type (normal,
    blocked, restricted, priority), and how many drones currently
    occupy it.
    """

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        color: Optional[str],
        max_drones: int,
        zone_type: str
    ) -> None:
        """Initialize a Zone with its name, coordinates, color, capacity
        and type. current_drones starts at 0.
        """
        self.name = name
        self.x = x
        self.y = y
        self.color = color
        self.max_drones = max_drones
        self.zone_type = zone_type
        self.current_drones = 0

    def __repr__(self) -> str:
        """Return a comma-separated string representation of the zone's
        attributes, useful for debugging and logging.
        """
        return (
            f"{self.name}, "
            f"{self.x}, "
            f"{self.y}, "
            f"{self.color}, "
            f"{self.max_drones}, "
            f"{self.zone_type}, "
            f"{self.current_drones}"
        )
