class Connection:
    """Represents a link between two zones in the network.

    A Connection tracks the two zone names it connects, the maximum
    number of drones allowed to traverse it simultaneously
    (max_link_capacity), and how many drones are currently in transit
    on it (current_drones).
    """

    def __init__(
        self,
        zone1: str,
        zone2: str,
        max_link_capacity: int = 1
    ) -> None:
        """Initialize a Connection between zone1 and zone2 with an
        optional max_link_capacity (default 1). current_drones starts
        at 0.
        """
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_capacity = max_link_capacity
        self.current_drones = 0

    def __repr__(self) -> str:
        """Return a string representation of the connection showing the
        two zone names and its max link capacity.
        """
        return (
            f"{self.zone1}-{self.zone2} "
            f"[max_link_capacity={self.max_link_capacity}]"
        )
