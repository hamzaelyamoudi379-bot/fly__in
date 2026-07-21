from typing import Optional
from graph import Graph

COLORS: dict[str, str] = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "orange": "\033[38;5;214m",
    "purple": "\033[38;5;129m",
    "brown": "\033[38;5;130m",
    "lime": "\033[38;5;154m",
    "gold": "\033[38;5;220m",
    "gray": "\033[37m",
    "white": "\033[97m",
    "black": "\033[30m",
    "maroon": "\033[38;5;88m",
    "darkred": "\033[38;5;124m",
    "crimson": "\033[38;5;196m",
    "violet": "\033[38;5;177m",
    "rainbow": "\033[38;5;201m",
}
RESET = "\033[0m"


def colorize(text: str, color: Optional[str]) -> str:
    """Wrap text in ANSI color codes matching color (case-insensitive).

    If color is None or not a recognized color name, text is returned
    unchanged.
    """
    if color and color.lower() in COLORS:
        return f"{COLORS[color.lower()]}{text}{RESET}"
    return text


class DroneState:
    """Tracks a single drone's progress along its assigned path during
    the simulation, including its current position, transit status,
    and whether it has been delivered.
    """

    def __init__(self, drone_id: str, path: list[str]) -> None:
        """Initialize a drone with its id and the full path (list of
        zone names) it will follow, starting at the first zone in the
        path.
        """
        self.drone_id = drone_id
        self.path = path
        self.position = 0
        self.in_transit = False
        self.transit_from = ""
        self.transit_to = ""
        self.delivered = False

    @property
    def current_zone(self) -> str:
        """Return the name of the zone the drone is currently at."""
        return self.path[self.position]

    def at_end(self, end_name: str) -> bool:
        """Return True if the drone's current zone matches end_name."""
        return self.current_zone == end_name

    def next_zone(self) -> Optional[str]:
        """Return the name of the next zone in the drone's path, or
        None if it is already at the last zone.
        """
        if self.position + 1 < len(self.path):
            return self.path[self.position + 1]
        return None


class Simulation:
    """Runs the turn-by-turn drone delivery simulation over a Graph,
    moving drones along their assigned paths while respecting zone
    and link capacity constraints, and printing each turn's moves.
    """

    def __init__(self, graph: Graph, drones_paths: list[list[str]]) -> None:
        """Initialize the simulation with the Graph to run on and the
        list of candidate paths drones will be assigned from (cycled
        round-robin in _setup_drones).
        """
        self.graph = graph
        self.drones_paths = drones_paths
        self.nb_drons = self.graph.nb_drons
        self.drones: dict[str, DroneState] = {}

    def simulate(self) -> None:
        """Run the full simulation loop: set up drones, then repeatedly
        advance one turn at a time, printing the moves and zone status
        for any turn with activity, until all drones are delivered or
        the turn limit (10000) is exceeded.
        """
        self._setup_drones()
        turn = 1

        while not self._all_delivered():
            moves = self._run_turn()
            if moves:
                print(f"\nTurn {turn}:")
                print(" ".join(moves))
                self.print_zone_status()
            turn += 1

            if turn > 10000:
                print("Error: simulation exceeded turn limit")
                break

    def _setup_drones(self) -> None:
        """Create a DroneState for each of the nb_drons drones, cycling
        through drones_paths round-robin to assign each drone a path,
        and place all drones in the start zone.
        """
        nb_paths = len(self.drones_paths)
        for i in range(1, self.nb_drons + 1):
            drone_id = f"D{i}"
            path = self.drones_paths[(i - 1) % nb_paths]
            self.drones[drone_id] = DroneState(drone_id, path)
        self.graph.zones[self.graph.start.name].current_drones = self.nb_drons

    def _all_delivered(self) -> bool:
        """Return True if every drone in the simulation has reached the
        end hub.
        """
        return all(d.delivered for d in self.drones.values())

    def _zone_has_space(self, zone_name: str) -> bool:
        """Return True if zone_name can accept another drone. The end
        hub always has space; other zones defer to
        Graph.check_zone_capacity.
        """
        if zone_name == self.graph.end.name:
            return True
        return self.graph.check_zone_capacity(zone_name)

    def _run_turn(self) -> list[str]:
        """Advance the simulation by one turn.

        First completes any drones already in transit (moving them
        into their destination zone), then attempts to start new
        transits for idle, non-delivered drones whose next zone has
        available link/zone capacity, handling restricted zones as a
        two-step transit and other zones as an immediate move.

        Returns the list of formatted move strings produced this turn.
        """
        moves: list[str] = []
        end_name = self.graph.end.name

        for drone in list(self.drones.values()):
            if not drone.in_transit or drone.delivered:
                continue
            dest = drone.transit_to
            src = drone.transit_from
            self.graph.remove_drone_from_link(src, dest)
            if dest != end_name:
                self.graph.add_drone_to_zone(dest)
            drone.position += 1
            drone.in_transit = False
            drone.transit_from = ""
            drone.transit_to = ""
            moves.append(self._format_move(drone, dest))
            if drone.at_end(end_name):
                drone.delivered = True

        for drone in list(self.drones.values()):
            if drone.in_transit or drone.delivered:
                continue
            next_z = drone.next_zone()
            if next_z is None:
                continue

            current = drone.current_zone
            next_zone_obj = self.graph.zones[next_z]

            if next_zone_obj.zone_type == "blocked":
                continue

            if not self.graph.check_link_capacity(current, next_z):
                continue

            if next_zone_obj.zone_type == "restricted":
                if self.graph.add_drone_to_link(current, next_z):
                    self.graph.remove_drone_from_zone(current)
                    drone.in_transit = True
                    drone.transit_from = current
                    drone.transit_to = next_z
                    drone_colored = colorize(drone.drone_id, "cyan")
                    moves.append(f"{drone_colored}-{current}-{next_z}")
            else:
                if self._zone_has_space(next_z):
                    self.graph.remove_drone_from_zone(current)
                    if next_z != end_name:
                        self.graph.add_drone_to_zone(next_z)
                    drone.position += 1
                    moves.append(self._format_move(drone, next_z))
                    if drone.at_end(end_name):
                        drone.delivered = True

        return moves

    def _format_move(self, drone: DroneState, dest: str) -> str:
        """Build a colorized 'drone_id-zone_name' string describing a
        drone's move into dest, used for turn-by-turn output.
        """
        zone_color = self.graph.zones[dest].color
        drone_part = colorize(drone.drone_id, "cyan")
        zone_part = colorize(dest, zone_color)
        return f"{drone_part}-{zone_part}"

    def build_zone_state(self) -> dict[str, list[str]]:
        """Build a snapshot mapping each zone name to the sorted list
        of drone ids currently occupying it.

        Drones that are mid-transit (in_transit) are not counted in
        any zone. Drone ids within each zone are sorted numerically
        (e.g. D1, D2, ... D10) for stable, readable output.
        """

        zone_state: dict[str, list[str]] = {
            zone_name: [] for zone_name in self.graph.zones
        }

        for drone in self.drones.values():
            if drone.in_transit:
                continue
            zone_name = drone.current_zone
            if zone_name in zone_state:
                zone_state[zone_name].append(drone.drone_id)

        for drone_ids in zone_state.values():
            drone_ids.sort(key=lambda d: int(d[1:]))

        return zone_state

    def get_drones_in_zone(self, zone_name: str) -> list[str]:
        """Return the sorted list of drone ids currently in zone_name,
        or an empty list if the zone is empty or unknown.
        """
        return self.build_zone_state().get(zone_name, [])

    def count_drones_in_zone(self, zone_name: str) -> int:
        """Return the number of drones currently in zone_name."""
        return len(self.get_drones_in_zone(zone_name))

    def print_zone_status(self) -> None:
        """Print a 'Zone Status' report listing every zone, its current
        drone count, and the ids of the drones occupying it (or
        'empty' if none). Intended to be called once per active turn,
        after the turn's moves have been printed.
        """
        zone_state = self.build_zone_state()
        print("Zone Status:")
        for zone_name in self.graph.zones:
            drone_ids = zone_state.get(zone_name, [])
            count = len(drone_ids)
            ids_str = " ".join(drone_ids) if drone_ids else "empty"
            print(f"{zone_name} ({count}): {ids_str}")
