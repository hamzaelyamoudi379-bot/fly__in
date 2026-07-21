import sys
from parser import Parser
from graph import Graph
from dijkstra import Dijkstra
from simulation import Simulation


def main() -> None:
    """Entry point: parse command-line args, read and parse the map
    file, build the Graph, compute the best paths from start to end
    via Dijkstra, and (when enabled) run the drone delivery
    simulation.
    """
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)
    if len(sys.argv) > 3:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)
    map_file = sys.argv[1]

    try:
        parser = Parser(map_file)
        parser.read_file()
    except FileNotFoundError:
        print(f"Error: file '{map_file}' not found")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    graph = Graph(parser)
    # for conn in graph.connections:
    #     print("         ", conn.zone1, conn.zone2)
        
    # print(graph.connections)
    dijkstra = Dijkstra(graph)

    paths = dijkstra.get_best_paths(graph.start.name, graph.end.name)

    if not paths:
        print("Error: no valid path found from start to end")
        sys.exit(1)

    simulation = Simulation(graph, paths)
    simulation.simulate()


if __name__ == "__main__":
    main()
