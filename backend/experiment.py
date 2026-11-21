"""Experimento: compara los cuatro algoritmos en muchos mapas aleatorios."""
from __future__ import annotations

import random
from typing import Dict, List

from .algorithms import ALGORITHMS, search
from .generator import generate_map, random_endpoints


def run_experiment(maps: int = 200, seed: int = 42, min_distance: int = 20,
                   width: int = 40, height: int = 24) -> Dict:
    """Devuelve promedios por algoritmo sobre `maps` mapas resolubles.

    La ruta de costo uniforme se toma como referencia óptima.
    """
    rng = random.Random(seed)
    names = list(ALGORITHMS)
    totals = {n: {"expanded": 0, "cost": 0, "optimal": 0, "ms": 0.0} for n in names}
    solved, attempts = 0, 0
    while solved < maps and attempts < maps * 5:
        attempts += 1
        game_map = generate_map(width, height, seed=rng.randrange(2**32))
        endpoints = random_endpoints(game_map, rng, min_distance)
        if endpoints is None:
            continue
        results = {n: search(n, game_map, *endpoints) for n in names}
        if not results["dijkstra"].found:
            continue  # mapa sin solución: se descarta
        solved += 1
        best = results["dijkstra"].cost
        for n, r in results.items():
            totals[n]["expanded"] += r.expanded
            totals[n]["cost"] += r.cost
            totals[n]["optimal"] += int(r.cost == best)
            totals[n]["ms"] += r.elapsed_ms
    rows: List[Dict] = []
    for n in names:
        t = totals[n]
        rows.append({
            "algorithm": n,
            "avg_expanded": round(t["expanded"] / solved, 1) if solved else None,
            "avg_cost": round(t["cost"] / solved, 2) if solved else None,
            "optimal_pct": round(100 * t["optimal"] / solved, 1) if solved else None,
            "avg_ms": round(t["ms"] / solved, 3) if solved else None,
        })
    return {"maps": solved, "seed": seed, "min_distance": min_distance, "rows": rows}
