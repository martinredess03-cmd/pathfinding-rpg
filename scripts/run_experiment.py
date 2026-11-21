"""Ejecuta el experimento desde la terminal.

Uso:  python scripts/run_experiment.py --maps 200 --seed 42 [--csv resultados.csv]
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.experiment import run_experiment  # noqa: E402

NAMES = {"bfs": "BFS (ciega)", "dijkstra": "Costo uniforme (ciega)",
         "greedy": "Voraz (heurística)", "astar": "A* (heurística)"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara BFS, costo uniforme, voraz y A*")
    parser.add_argument("--maps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--csv", help="archivo CSV de salida (opcional)")
    args = parser.parse_args()

    data = run_experiment(maps=args.maps, seed=args.seed)
    print(f"\n{data['maps']} mapas resolubles (semilla {data['seed']}, separación mínima {data['min_distance']})\n")
    print(f"{'Algoritmo':<26}{'Expandidos':>11}{'Costo':>9}{'Óptima':>9}{'ms':>9}")
    for r in data["rows"]:
        print(f"{NAMES[r['algorithm']]:<26}{r['avg_expanded']:>11}{r['avg_cost']:>9}{r['optimal_pct']:>8}%{r['avg_ms']:>9}")
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(data["rows"][0]))
            writer.writeheader()
            writer.writerows(data["rows"])
        print(f"\nResultados guardados en {args.csv}")


if __name__ == "__main__":
    main()
