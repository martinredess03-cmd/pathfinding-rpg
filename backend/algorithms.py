"""Algoritmos de búsqueda de rutas.

Búsqueda ciega:       bfs, uniform_cost
Búsqueda heurística:  greedy, a_star (heurística: distancia de Manhattan)
"""
from __future__ import annotations

import heapq
import time
from collections import deque
from dataclasses import asdict, dataclass
from typing import Callable, Dict, List

from .grid import GameMap


@dataclass
class SearchResult:
    algorithm: str
    found: bool
    path: List[int]            # índices de casillas desde el inicio hasta la meta
    expanded_order: List[int]  # orden en que se expandieron las casillas (para animar)
    cost: int                  # suma de los costos de las casillas en las que se entra
    steps: int
    expanded: int              # nodos expandidos: medida del esfuerzo de búsqueda
    elapsed_ms: float

    def to_dict(self) -> dict:
        return asdict(self)


def _reconstruct(parent: Dict[int, int], goal: int) -> List[int]:
    path = [goal]
    while parent[path[-1]] != -1:
        path.append(parent[path[-1]])
    path.reverse()
    return path


def _finish(name: str, game_map: GameMap, parent, goal: int, order: List[int], t0: float, found: bool) -> SearchResult:
    path = _reconstruct(parent, goal) if found else []
    cost = sum(game_map.costs[i] for i in path[1:])
    return SearchResult(name, found, path, order, cost, max(len(path) - 1, 0), len(order),
                        (time.perf_counter() - t0) * 1000)


def bfs(game_map: GameMap, start: int, goal: int) -> SearchResult:
    """Búsqueda en anchura (ciega): minimiza el número de pasos e ignora los costos."""
    t0 = time.perf_counter()
    parent = {start: -1}
    queue = deque([start])
    order: List[int] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        if node == goal:
            return _finish("bfs", game_map, parent, goal, order, t0, True)
        for nxt in game_map.neighbors(node):
            if game_map.passable(nxt) and nxt not in parent:
                parent[nxt] = node
                queue.append(nxt)
    return _finish("bfs", game_map, parent, goal, order, t0, False)


def _best_first(name: str, game_map: GameMap, start: int, goal: int, use_g: bool, use_h: bool) -> SearchResult:
    """Núcleo común de costo uniforme (g), voraz (h) y A* (g + h)."""
    t0 = time.perf_counter()
    g_cost = {start: 0}
    parent = {start: -1}
    closed = set()
    order: List[int] = []

    def priority(node: int) -> tuple:
        h = game_map.manhattan(node, goal)
        f = (g_cost[node] if use_g else 0) + (h if use_h else 0)
        return (f, h, node)  # empates: se prefiere la casilla más cercana a la meta

    frontier = [(priority(start), start)]
    while frontier:
        _, node = heapq.heappop(frontier)
        if node in closed:
            continue  # entrada obsoleta de la cola
        closed.add(node)
        order.append(node)
        if node == goal:
            return _finish(name, game_map, parent, goal, order, t0, True)
        for nxt in game_map.neighbors(node):
            if not game_map.passable(nxt) or nxt in closed:
                continue
            if use_g:
                new_g = g_cost[node] + game_map.costs[nxt]
                if new_g < g_cost.get(nxt, float("inf")):
                    g_cost[nxt] = new_g
                    parent[nxt] = node
                    heapq.heappush(frontier, (priority(nxt), nxt))
            elif nxt not in parent:  # voraz: no revisa costos acumulados
                g_cost[nxt] = g_cost[node] + game_map.costs[nxt]
                parent[nxt] = node
                heapq.heappush(frontier, (priority(nxt), nxt))
    return _finish(name, game_map, parent, goal, order, t0, False)


def uniform_cost(game_map: GameMap, start: int, goal: int) -> SearchResult:
    """Costo uniforme / Dijkstra (ciega): siempre encuentra la ruta de menor costo."""
    return _best_first("dijkstra", game_map, start, goal, use_g=True, use_h=False)


def greedy(game_map: GameMap, start: int, goal: int) -> SearchResult:
    """Voraz primero el mejor (heurística): rápido pero no garantiza la ruta óptima."""
    return _best_first("greedy", game_map, start, goal, use_g=False, use_h=True)


def a_star(game_map: GameMap, start: int, goal: int) -> SearchResult:
    """A*: f(n) = g(n) + h(n). Óptimo porque Manhattan es admisible y consistente."""
    return _best_first("astar", game_map, start, goal, use_g=True, use_h=True)


ALGORITHMS: Dict[str, Callable[[GameMap, int, int], SearchResult]] = {
    "bfs": bfs,
    "dijkstra": uniform_cost,
    "greedy": greedy,
    "astar": a_star,
}


def search(algorithm: str, game_map: GameMap, start: int, goal: int) -> SearchResult:
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Algoritmo desconocido: {algorithm!r}. Opciones: {sorted(ALGORITHMS)}")
    return ALGORITHMS[algorithm](game_map, start, goal)
