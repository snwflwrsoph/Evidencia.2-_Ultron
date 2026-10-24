from __future__ import annotations

import csv
from dataclasses import dataclass
import heapq
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
BASE = "S000"
OUTLET = "OUTLET"


@dataclass
class CaseData:
    stations: list[str]
    roads: list[tuple[str, str, int, int]]
    conflict_edges: list[tuple[str, str]]
    pipes: list[tuple[str, str, int]]
    checkpoints: list[str]
    travel_graph: dict[str, list[tuple[str, int]]]
    cable_graph: dict[str, list[tuple[str, int]]]
    conflict_graph: dict[str, set[str]]
    pipe_graph: dict[str, list[tuple[str, int]]]


def read_csv(name: str) -> list[dict[str, str]]:
    """Read a file from ./data. utf-8-sig also accepts CSVs with a BOM."""
    with (DATA / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def make_undirected_graph(
    nodes: list[str], edges: list[tuple[str, str, int]]
) -> dict[str, list[tuple[str, int]]]:
    graph = {node: [] for node in nodes}
    for a, b, weight in edges:
        graph[a].append((b, weight))
        graph[b].append((a, weight))
    return graph


def make_directed_graph(
    nodes: list[str], edges: list[tuple[str, str, int]]
) -> dict[str, list[tuple[str, int]]]:
    graph = {node: [] for node in nodes}
    for a, b, capacity in edges:
        graph[a].append((b, capacity))
    return graph


def load_case() -> CaseData:
    """Load and validate all inputs, retaining distinct models for each network."""
    station_rows = read_csv("stations.csv")
    road_rows = read_csv("roads.csv")
    conflict_rows = read_csv("interference.csv")
    pipe_rows = read_csv("pipes.csv")
    checkpoint_rows = read_csv("checkpoints.csv")

    stations = [r["id"] for r in station_rows]
    assert len(stations) == 196 and len(set(stations)) == 196
    assert stations == [f"S{i:03d}" for i in range(196)]
    station_set = set(stations)

    roads = [(r["source"], r["target"], int(r["travel_minutes"]),
              int(r["cable_cost"])) for r in road_rows]
    assert len(roads) == 690
    assert all(a in station_set and b in station_set and a != b and t > 0 and c > 0
               for a, b, t, c in roads)
    assert len({tuple(sorted((a, b))) for a, b, _, _ in roads}) == len(roads)

    conflict_edges = [(r["node_a"], r["node_b"]) for r in conflict_rows]
    assert len(conflict_edges) == 1000
    assert all(a in station_set and b in station_set and a != b
               for a, b in conflict_edges)
    assert len({tuple(sorted((a, b))) for a, b in conflict_edges}) == len(conflict_edges)

    pipes = [(r["source"], r["target"], int(r["capacity_per_minute"]))
             for r in pipe_rows]
    assert len(pipes) == 689
    hydraulic_nodes = station_set | {"SOURCE", "OUTLET"}
    assert all(a in hydraulic_nodes and b in hydraulic_nodes and a != b and cap > 0
               for a, b, cap in pipes)
    assert len({(a, b) for a, b, _ in pipes}) == len(pipes)

    checkpoints = [r["station_id"] for r in checkpoint_rows]
    assert len(checkpoints) == 12 and len(set(checkpoints)) == 12
    assert all(p in station_set and p != BASE for p in checkpoints)

    travel_graph = make_undirected_graph(stations, [(a, b, t) for a, b, t, _ in roads])
    cable_graph = make_undirected_graph(stations, [(a, b, c) for a, b, _, c in roads])
    conflict_graph: dict[str, set[str]] = {s: set() for s in stations}
    for a, b in conflict_edges:
        conflict_graph[a].add(b)
        conflict_graph[b].add(a)
    pipe_graph = make_directed_graph(sorted(hydraulic_nodes), pipes)

    return CaseData(stations, roads, conflict_edges, pipes, checkpoints,
                    travel_graph, cable_graph, conflict_graph, pipe_graph)


# ------- Your work starts here. Implement the algorithms named below. -------


def times_from_one_station(graph: dict[str, list[tuple[str, int]]], start: str) -> dict[str, int]:
    """TODO (Dijkstra): shortest travel times from a single starting station."""
    dist = {v: float("inf") for v in graph}
    dist[start] = 0

    pq = [(0, start)]

    while pq:
        d, u = heapq.heappop(pq)

        if d > dist[u]:
            continue

        for v, w in graph[u]:
            newDist = d + w

            if newDist < dist[v]:
                dist[v] = newDist
                heapq.heappush(pq, (newDist, v))

    print(dist)
    for station, distance in dist.items():
        if 72 <= distance <= 96:
            print(f"Station: {station}, Distance: {distance}")
    return dist


def times_between_all_stations(graph: dict[str, list[tuple[str, int]]]) -> dict[str, dict[str, int]]:
    stations = list(graph.keys())
    V = len(stations)
    INF = int(1e8)
    index = {station: idx for idx, station in enumerate(stations)}
    dist = [[INF] * V for _ in range(V)]

    
    # for each intermediate vertex
    for i in range(V):
        dist[i][i] = 0
    for station in stations:
        i = index[station]
        for neighbor, time in graph[station]:
            j = index[neighbor]
            dist[i][j] = min(dist[i][j], time)
    for k in range(V):
        for i in range(V):
            for j in range(V):
                if dist[i][k] != INF and dist[k][j] != INF:
                    dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

    return {stations[i]: {stations[j]: dist[i][j] for j in range(V)} for i in range(V)}

def filter_part2(candidates: list[str], distances: dict[str, dict[str, int]]) -> list[str]:
    filtered = [
        station for station in candidates
        if 30 <= distances["S013"][station] <= 78
        and 83 <= distances["S182"][station] <= 107
    ]

    return filtered



def cheapest_backbone(
    stations: list[str], roads: list[tuple[str, str, int, int]], approach: str
) -> tuple[list[tuple[str, str]], int]:
    """Build a minimum spanning tree with Prim ('grow') or Kruskal ('sort')."""
    if not stations:
        return [], 0

    if approach == "sort":
        parent = {station: station for station in stations}
        rank = {station: 0 for station in stations}

        def find(station: str) -> str:
            if parent[station] != station:
                parent[station] = find(parent[station])
            return parent[station]

        backbone: list[tuple[str, str]] = []
        total_cost = 0
        for source, target, _, cable_cost in sorted(roads, key=lambda road: road[3]):
            source_root = find(source)
            target_root = find(target)
            if source_root == target_root:
                continue

            backbone.append((source, target))
            total_cost += cable_cost
            if rank[source_root] < rank[target_root]:
                parent[source_root] = target_root
            elif rank[source_root] > rank[target_root]:
                parent[target_root] = source_root
            else:
                parent[target_root] = source_root
                rank[source_root] += 1

            if len(backbone) == len(stations) - 1:
                break

        if len(backbone) != len(stations) - 1:
            raise ValueError("The road network is disconnected; no spanning tree exists.")
        return backbone, total_cost

    if approach != "grow":
        raise ValueError("approach must be 'grow' (Prim) or 'sort' (Kruskal).")

    graph: dict[str, list[tuple[str, int]]] = {station: [] for station in stations}
    for source, target, _, cable_cost in roads:
        graph[source].append((target, cable_cost))
        graph[target].append((source, cable_cost))

    visited = {stations[0]}
    candidates = [
        (cost, stations[0], target)
        for target, cost in graph[stations[0]]
    ]
    heapq.heapify(candidates)
    backbone: list[tuple[str, str]] = []
    total_cost = 0

    while candidates and len(visited) < len(stations):
        cost, source, target = heapq.heappop(candidates)
        if target in visited:
            continue

        visited.add(target)
        backbone.append((source, target))
        total_cost += cost

        for neighbor, edge_cost in graph[target]:
            if neighbor not in visited:
                heapq.heappush(candidates, (edge_cost, target, neighbor))

    if len(visited) != len(stations):
        raise ValueError("The road network is disconnected; no spanning tree exists.")

    return backbone, total_cost

def degree_one_edges(
    stations: list[str], edges: list[tuple[str, str]]
) -> list[tuple[str, tuple[str, str]]]:
    """Return each degree-one station and its incident tree edge."""
    incident_edges: dict[str, list[tuple[str, str]]] = {
        station: [] for station in stations
    }
    for edge in edges:
        source, target = edge
        incident_edges[source].append(edge)
        incident_edges[target].append(edge)

    return [
        (station, station_edges[0])
        for station, station_edges in incident_edges.items()
        if len(station_edges) == 1
    ]

def frequency_assignment(conflicts: dict[str, set[str]]) -> dict[str, int]:
   
    nodes = list(conflicts.keys())
    nodes.sort(key=lambda v: len(conflicts[v]), reverse=True)

    def can_color(k: int) -> dict[str, int]:

        color: dict[str, int] = {}

        def bt(i: int) -> bool:
            if i == len(nodes):
                return True
            v = nodes[i]
            used = {color[u] for u in conflicts[v] if u in color}
            for j in range(k):
                if j not in used:
                    color[v] = j
                    if bt(i + 1):
                        return True
                    del color[v]
            return False

        if bt(0):
            return color
    print(nodes)

    lo, hi = 1, len(nodes)
    best = None

    while lo <= hi:
        mid = (lo + hi)//2
        result = can_color(mid)
        if result:
            best = result
            hi = mid - 1
        else:
            lo = mid + 1
    return best




def inspection_loop(
    start: str, checkpoints: list[str], distances: dict[str, dict[str, int]]
) -> tuple[int, list[str]]:
    """Traveling Salesperson / Held-Karp: exact tour, ties lexicographic."""

    INF = float("inf")

    def dist(a, b):
        return distances.get(a, {}).get(b, INF)

    points = sorted(set(checkpoints) - {start})
    n = len(points)
    full = (1 << n) - 1

    remaining = [[INF] * n for _ in range(1 << n)]

    for i in range(n):
        remaining[full][i] = dist(points[i], start)

    for mask in range(full - 1, 0, -1):
        for i in range(n):
            if mask & (1 << i):
                remaining[mask][i] = min(
                    (
                        dist(points[i], points[j]) + remaining[mask | (1 << j)][j]
                        for j in range(n)
                        if not mask & (1 << j)
                    ),
                    default=INF
                )

    total = min(
        dist(start, points[j]) + remaining[1 << j][j]
        for j in range(n)
    )

    if total == INF:
        raise ValueError("No existe un recorrido valido")

    tour, mask, current, spent = [start], 0, start, 0

    for _ in range(n):
        for j in range(n):
            if mask & (1 << j):
                continue

            step = dist(current, points[j])

            if spent + step + remaining[mask | (1 << j)][j] == total:
                mask |= 1 << j
                spent += step
                current = points[j]
                tour.append(current)
                break

    tour.append(start)

    return total, tour


class Graph:

    def __init__(self, graph):
        self.graph = graph
        self.ROW = len(graph)

    def BFS(self, s, t, parent):

        visited = [False] * self.ROW
        queue = [s]
        visited[s] = True

        while queue:
            u = queue.pop(0)

            for ind, val in enumerate(self.graph[u]):
                if not visited[ind] and val > 0:
                    queue.append(ind)
                    visited[ind] = True
                    parent[ind] = u

                    if ind == t:
                        return True

        return False

    def EdmondKarp(self, source, sink):

        parent = [-1] * self.ROW
        max_flow = 0

        while self.BFS(source, sink, parent):

            path_flow = float("inf")
            s = sink

            while s != source:
                path_flow = min(
                    path_flow,
                    self.graph[parent[s]][s]
                )
                s = parent[s]

            max_flow += path_flow

            v = sink
            while v != source:
                u = parent[v]
                self.graph[u][v] -= path_flow
                self.graph[v][u] += path_flow
                v = parent[v]

        return max_flow



def maximum_delivery(
    pipes: list[tuple[str, str, int]], injection: str, outlet: str
) -> int:

    nodes = sorted(
        {node for a, b, _ in pipes for node in (a, b)}
        | {injection, outlet}
    )

    # Asignar indices numericos
    index = {node: i for i, node in enumerate(nodes)}

    V = len(nodes)

    # Crear matriz de capacidades
    graph = [[0] * V for _ in range(V)]

    # Agregar las tuberias dirigidas
    for source, target, capacity in pipes:
        i = index[source]
        j = index[target]
        graph[i][j] += capacity

    # Ejecutar Edmonds-Karp
    g = Graph(graph)

    return g.EdmondKarp(
        index[injection],
        index[outlet]
    )




def investigate(case: CaseData) -> None:

    # PARTE 1 - Dijkstra
    dijkstra = times_from_one_station(case.travel_graph, "S000")

    candidates = [
        station for station in case.stations
        if 72 <= dijkstra[station] <= 96
    ]

    print("Parte 1:", candidates)

    # PARTE 2 - Floyd-Warshall
    distances = times_between_all_stations(case.travel_graph)

    candidates = filter_part2(candidates, distances)

    print("Parte 2:", candidates)

    # PARTE 3 - Prim y Kruskal
    prim_edges, prim_cost = cheapest_backbone(
        case.stations, case.roads, "grow"
    )

    kruskal_edges, kruskal_cost = cheapest_backbone(
        case.stations, case.roads, "sort"
    )

    assert prim_cost == kruskal_cost
    assert len(prim_edges) == len(case.stations) - 1
    assert len(kruskal_edges) == len(case.stations) - 1

    # Usamos el arbol de Prim para aplicar la pista
    degree_one = degree_one_edges(case.stations, prim_edges)
    degree_one_stations = {
        station for station, edge in degree_one
    }

    candidates = [
        station for station in candidates
        if station in degree_one_stations
    ]

    print("Parte 3:", candidates)
    print("Costo MST Prim:", prim_cost)
    print("Costo MST Kruskal:", kruskal_cost)

    # PARTE 4 - Coloreo de grafos
    color = frequency_assignment(case.conflict_graph)

    posibleStations = [
        k for k, v in color.items()
        if v == color["S182"]
    ]

    candidates = [
        station for station in candidates
        if station in posibleStations
    ]

    print("Parte 4:", candidates)
    # PARTE 5 - Held-Karp


    total, route = inspection_loop(
        "S000", case.checkpoints, distances
    )

    sixth_checkpoint = route[6]

    candidates = [
        station for station in candidates
        if 27 <= distances[sixth_checkpoint][station] <= 47
    ]

    print("Parte 5:", candidates)
    print("Ruta optima:", route)
    print("Tiempo total:", total)
    print("Sexto checkpoint:", sixth_checkpoint)
        # PARTE 6 - Flujo maximo
    candidates = [
        station for station in candidates
        if maximum_delivery(case.pipes, station, "OUTLET") == 60
    ]

    print("Parte 6:", candidates)

def main() -> None:
    case = load_case()
    print("Operation Ultron Loaded")
    print(f"Stations:       {len(case.stations)}")
    print(f"Roads:          {len(case.roads)} (undirected)")
    print(f"Radio conflicts:{len(case.conflict_edges):>5} (undirected)")
    print(f"Pipes:          {len(case.pipes)} (directed)")
    print(f"Checkpoints:    {len(case.checkpoints)} (unordered)")
    print("Graphs ready. Complete the TODO functions to begin the investigation.")

    
    # When ready, uncomment the next line:
    investigate(case)


if __name__ == "__main__":
    main()
