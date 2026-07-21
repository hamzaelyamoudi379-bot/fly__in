from typing import Optional
from zone import Zone
from connection import Connection
from parser import Parser


class Graph:
    """Represents the drone delivery network built from parsed data.

    Wraps the zones, connections, start/end hubs and drone count
    produced by a Parser, and provides helper methods to query
    neighbors, connections, and to track/update zone and link
    capacity as drones move through the network.
    """

    def __init__(self, parser: Parser) -> None:
        """Initialize the Graph from an already-parsed Parser instance,
        copying over its zones, connections, start, end and nb_drons.
        """
        self.zones: dict[str, Zone] = parser.zone
        self.connections: list[Connection] = parser.connections
        self.start: Zone = parser.start  # type: ignore[assignment]
        self.end: Zone = parser.end  # type: ignore[assignment]
        self.nb_drons: int = parser.nb_drons

    def __str__(self) -> str:
        """Return a human-readable string showing zones, connections,
        start, end and nb_drons, mainly for debugging.
        """
        return (
            f"{self.zones}\n"
            f"{self.connections}\n"
            f"{self.start}\n"
            f"{self.end}\n"
            f"{self.nb_drons}"
        )

    def get_neighbors(self, zone_name: str) -> list[str]:
        """Return the list of zone names directly connected to
        zone_name via any connection, regardless of direction.
        """
        neighbors: list[str] = []
        for conn in self.connections:
            if zone_name == conn.zone1:
                neighbors.append(conn.zone2)
            elif zone_name == conn.zone2:
                neighbors.append(conn.zone1)
        return neighbors

    def get_connection(self, zone1: str, zone2: str) -> Optional[Connection]:
        """Return the Connection object linking zone1 and zone2 in
        either direction, or None if no such connection exists.
        """
        for conn in self.connections:
            if (conn.zone1 == zone1 and conn.zone2 == zone2) or \
               (conn.zone1 == zone2 and conn.zone2 == zone1):
                return conn
        return None

    def check_zone_capacity(self, zone_name: str) -> bool:
        """Return True if zone_name currently has room for another
        drone (current_drones < max_drones).
        """
        zone = self.zones[zone_name]
        return zone.current_drones < zone.max_drones

    def check_link_capacity(self, zone1: str, zone2: str) -> bool:
        """Return True if the connection between zone1 and zone2 exists
        and currently has room for another drone in transit.
        """
        conn = self.get_connection(zone1, zone2)
        if conn is None:
            return False
        return conn.current_drones < conn.max_link_capacity

    def add_drone_to_zone(self, zone_name: str) -> bool:
        """Increment the drone count of zone_name if it has capacity.

        Returns True if the drone was added, False if the zone is full.
        """
        if self.check_zone_capacity(zone_name):
            self.zones[zone_name].current_drones += 1
            return True
        return False

    def remove_drone_from_zone(self, zone_name: str) -> bool:
        """Decrement the drone count of zone_name if it is above zero.

        Returns True if a drone was removed, False if the zone was
        already empty.
        """
        if self.zones[zone_name].current_drones > 0:
            self.zones[zone_name].current_drones -= 1
            return True
        return False

    def add_drone_to_link(self, zone1: str, zone2: str) -> bool:
        """Increment the in-transit drone count of the connection
        between zone1 and zone2 if it has capacity.

        Returns True if the drone was added, False if the connection
        doesn't exist or is already at max capacity.
        """
        conn = self.get_connection(zone1, zone2)
        if conn is None:
            return False
        if conn.current_drones < conn.max_link_capacity:
            conn.current_drones += 1
            return True
        return False

    def remove_drone_from_link(self, zone1: str, zone2: str) -> bool:
        """Decrement the in-transit drone count of the connection
        between zone1 and zone2 if it is above zero.

        Returns True if a drone was removed, False if the connection
        doesn't exist or was already empty.
        """
        conn = self.get_connection(zone1, zone2)
        if conn is None:
            return False
        if conn.current_drones > 0:
            conn.current_drones -= 1
            return True
        return False

    def movement_cost(self, zone_name: str) -> float:
        """Return the cost of moving into zone_name based on its type:
        infinity for blocked zones, 2.0 for restricted zones, and 1.0
        for all other zone types.
        """
        zone = self.zones[zone_name]
        if zone.zone_type == "blocked":
            return float("inf")
        elif zone.zone_type == "restricted":
            return 2.0
        else:
            return 1.0
