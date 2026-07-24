from graph import Graph


class Dijkstra:
    """Computes shortest and alternative paths through a Graph, taking
    zone type into account as a movement cost (e.g. restricted zones
    cost more, priority zones cost less, blocked zones are
    impassable).
    """

    def __init__(self, graph: Graph) -> None:
        """Initialize the pathfinder with the Graph to search over."""
        self.graph = graph
        self.all_paths: list[list[str]] = []

    def find_path(self, start: str, end: str) -> list[str]:
        """Find the lowest-cost path from start to end using Dijkstra's
        algorithm, weighting each step by zone type via
        _weighted_cost.

        Returns the path as a list of zone names (including start and
        end), or an empty list if no path exists.
        """
        distances: dict[str, float] = {}
        previous: dict[str, str | None] = {}
        queue: list[tuple[float, str]] = []
        visited: set[str] = set()

        for zone in self.graph.zones:
            distances[zone] = float("inf")
            previous[zone] = None

        distances[start] = 0.0
        queue.append((0.0, start))

        while queue:
            cost_node = queue[0]
            for item in queue:
                if item[0] < cost_node[0]:
                    cost_node = item
            current_cost, current_zone = cost_node
            queue.remove(cost_node)

            if current_zone in visited:
                continue
            visited.add(current_zone)

            if current_zone == end:
                break

            for neighbor in self.graph.get_neighbors(current_zone):
                if neighbor in visited:
                    continue
                move_cost = self._weighted_cost(neighbor)
                if move_cost == float("inf"):
                    continue
                new_cost = current_cost + move_cost
                if new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    previous[neighbor] = current_zone
                    queue.append((new_cost, neighbor))

        return self._reconstruct_path(previous, start, end)

    def _weighted_cost(self, zone_name: str) -> float:
        """Return the Dijkstra traversal cost for entering zone_name:
        infinity for blocked, 2.0 for restricted, 0.9 for priority,
        and 1.0 for normal zones.
        """
        zone = self.graph.zones[zone_name]
        if zone.zone_type == "blocked" or zone.max_drones == 0:
            return float("inf")
        elif zone.zone_type == "restricted":
            return 2.0
        elif zone.zone_type == "priority":
            return 0.9
        else:
            return 1.0

    def _reconstruct_path(
        self,
        previous: dict[str, str | None],
        start: str,
        end: str
    ) -> list[str]:
        """Rebuild the path from start to end by walking the previous-
        node map backwards from end, then reversing it.

        Returns an empty list if no valid path was found (i.e. the
        reconstructed path doesn't begin at start).
        """
        path: list[str] = []
        current: str | None = end

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()

        if not path or path[0] != start:
            return []

        return path

    def find_all_paths(self, start: str, end: str) -> list[list[str]]:
        """Find every simple path (no repeated zones) from start to end
        via depth-first search, avoiding blocked zones.

        Returns a list of paths, each a list of zone names.
        """
        self.all_paths = []
        self._dfs(current=start, goal=end, visited=set(), path=[])
        return self.all_paths

    def _dfs(
        self,
        current: str,
        goal: str,
        visited: set[str],
        path: list[str]
    ) -> None:
        """Recursively explore all simple paths from current to goal,
        appending complete paths to self.all_paths. Skips blocked
        zones and never revisits a zone already in the current path.
        """
        zone = self.graph.zones[current]
        if zone.zone_type == "blocked":
            return

        path.append(current)
        visited.add(current)

        if current == goal:
            self.all_paths.append(path.copy())
        else:
            for neighbor in self.graph.get_neighbors(current):
                if neighbor not in visited:
                    self._dfs(
                        current=neighbor,
                        goal=goal,
                        visited=visited,
                        path=path
                    )

        path.pop()
        visited.remove(current)

    def path_cost(self, path: list[str]) -> float:
        """Return the total movement cost of traversing path, summing
        Graph.movement_cost for every zone after the first.
        """
        cost = 0.0
        for zone_name in path[1:]:
            cost += self.graph.movement_cost(zone_name)
        return cost

    def get_best_paths(self, start: str, end: str) -> list[list[str]]:
        """Find all valid simple paths from start to end and sort them
        from cheapest to most expensive using path_cost.
        """
        all_paths = self.find_all_paths(start, end)
        valid: list[list[str]] = [
            p for p in all_paths if p and p[-1] == end
        ]
        valid.sort(key=self.path_cost)
        return valid
