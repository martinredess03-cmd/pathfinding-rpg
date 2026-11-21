"""API REST y servidor de archivos estáticos, solo con la biblioteca estándar de Python.

Rutas:
    GET  /api/map?seed=N        genera un mapa (con semilla opcional)
    POST /api/search            ejecuta un algoritmo sobre un mapa
    POST /api/compare           ejecuta los cuatro algoritmos sobre un mapa
    GET  /api/experiment?maps=200&seed=42   promedios en mapas aleatorios
    GET  /                      sirve el frontend
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .algorithms import ALGORITHMS, search
from .experiment import run_experiment
from .generator import default_endpoints, generate_map
from .grid import GameMap

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
MAX_BODY_BYTES = 1_000_000
MAX_DIMENSION = 100
MAX_EXPERIMENT_MAPS = 500


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def parse_problem(payload: dict):
    """Valida el cuerpo de una petición y devuelve (mapa, inicio, meta)."""
    try:
        width, height = int(payload["width"]), int(payload["height"])
        if not (0 < width <= MAX_DIMENSION and 0 < height <= MAX_DIMENSION):
            raise ApiError(f"width y height deben estar entre 1 y {MAX_DIMENSION}")
        game_map = GameMap.from_dict(payload)
        start, goal = int(payload["start"]), int(payload["goal"])
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ApiError):
            raise
        raise ApiError(f"Petición inválida: {exc}") from exc
    for name, idx in (("start", start), ("goal", goal)):
        if not 0 <= idx < game_map.size:
            raise ApiError(f"{name} fuera del mapa")
        if not game_map.passable(idx):
            raise ApiError(f"{name} está sobre una casilla bloqueada")
    return game_map, start, goal


def handle_map(query: dict) -> dict:
    seed = int(query["seed"][0]) if "seed" in query else random.randrange(2**32)
    width = int(query.get("width", [40])[0])
    height = int(query.get("height", [24])[0])
    if not (5 <= width <= MAX_DIMENSION and 5 <= height <= MAX_DIMENSION):
        raise ApiError(f"width y height deben estar entre 5 y {MAX_DIMENSION}")
    game_map = generate_map(width, height, seed)
    start, goal = default_endpoints(width, height)
    return {**game_map.to_dict(), "start": start, "goal": goal, "seed": seed}


def handle_search(payload: dict) -> dict:
    game_map, start, goal = parse_problem(payload)
    algorithm = payload.get("algorithm", "astar")
    if algorithm not in ALGORITHMS:
        raise ApiError(f"Algoritmo desconocido. Opciones: {sorted(ALGORITHMS)}")
    return search(algorithm, game_map, start, goal).to_dict()


def handle_compare(payload: dict) -> dict:
    game_map, start, goal = parse_problem(payload)
    results = []
    for name in ALGORITHMS:
        r = search(name, game_map, start, goal).to_dict()
        r.pop("expanded_order")  # la comparación solo necesita las métricas
        r.pop("path")
        results.append(r)
    return {"results": results}


def handle_experiment(query: dict) -> dict:
    maps = min(int(query.get("maps", [200])[0]), MAX_EXPERIMENT_MAPS)
    seed = int(query.get("seed", [42])[0])
    return run_experiment(maps=max(maps, 1), seed=seed)


class Handler(BaseHTTPRequestHandler):
    server_version = "PathfindingRPG/1.0"

    # ---- utilidades ----
    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_BODY_BYTES:
            raise ApiError("Cuerpo demasiado grande", 413)
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as exc:
            raise ApiError(f"JSON inválido: {exc}") from exc

    def _serve_static(self, path: str) -> None:
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        target = (FRONTEND_DIR / relative).resolve()
        if FRONTEND_DIR not in target.parents or not target.is_file():
            self._send_json({"error": "No encontrado"}, 404)
            return
        body = target.read_bytes()
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8" if ctype.startswith("text") or ctype.endswith("javascript") else ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---- métodos HTTP ----
    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        query = parse_qs(url.query)
        try:
            if url.path == "/api/map":
                self._send_json(handle_map(query))
            elif url.path == "/api/experiment":
                self._send_json(handle_experiment(query))
            elif url.path.startswith("/api/"):
                raise ApiError("Ruta no encontrada", 404)
            else:
                self._serve_static(url.path)
        except ApiError as exc:
            self._send_json({"error": str(exc)}, exc.status)
        except ValueError as exc:
            self._send_json({"error": f"Parámetro inválido: {exc}"}, 400)

    def do_POST(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        try:
            payload = self._read_json()
            if url.path == "/api/search":
                self._send_json(handle_search(payload))
            elif url.path == "/api/compare":
                self._send_json(handle_compare(payload))
            else:
                raise ApiError("Ruta no encontrada", 404)
        except ApiError as exc:
            self._send_json({"error": str(exc)}, exc.status)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor del proyecto Pathfinding RPG")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = create_server(args.host, args.port)
    print(f"Servidor en http://{args.host}:{args.port}  (Ctrl+C para detener)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")
        server.server_close()


if __name__ == "__main__":
    main()
