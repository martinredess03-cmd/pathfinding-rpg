"""Pruebas unitarias y de la API. Ejecutar con:  python -m unittest discover -s tests -v"""
import json
import random
import threading
import unittest
import urllib.error
import urllib.request

from backend.algorithms import ALGORITHMS, a_star, bfs, greedy, search, uniform_cost
from backend.generator import default_endpoints, generate_map, random_endpoints
from backend.grid import BLOCKED, FOREST, GRASS, GameMap
from backend.server import create_server


def valid_path(game_map, path, start, goal):
    """La ruta empieza y termina donde debe, avanza de casilla en casilla y no cruza agua."""
    if path[0] != start or path[-1] != goal:
        return False
    return all(game_map.passable(b) and b in game_map.neighbors(a) for a, b in zip(path, path[1:]))


class AlgorithmTests(unittest.TestCase):
    def test_bfs_minimiza_pasos_en_mapa_uniforme(self):
        m = GameMap(5, 5, [GRASS] * 25)
        r = bfs(m, 0, 24)
        self.assertTrue(r.found)
        self.assertEqual(r.steps, 8)  # distancia de Manhattan en cuadrícula libre

    def test_costo_uniforme_prefiere_pasto_a_bosque(self):
        # Fila de arriba: pasto largo. Fila de abajo: bosque corto pero caro.
        costs = [GRASS] * 5 + [FOREST] * 5
        m = GameMap(5, 2, costs)
        r = uniform_cost(m, 5, 9)
        # Por el bosque costaría 4 x 3 = 12; subiendo al pasto: 1 + 4 x 1 + 3 = 8
        self.assertEqual(r.cost, 8)

    def test_a_star_y_costo_uniforme_dan_el_mismo_costo(self):
        rng = random.Random(7)
        comparados = 0
        for seed in range(60):
            m = generate_map(seed=seed)
            ends = random_endpoints(m, rng)
            if not ends:
                continue
            ref, astar = uniform_cost(m, *ends), a_star(m, *ends)
            self.assertEqual(ref.found, astar.found)
            if ref.found:
                comparados += 1
                self.assertEqual(ref.cost, astar.cost)
                self.assertTrue(valid_path(m, astar.path, *ends))
                self.assertLessEqual(astar.expanded, m.size)
        self.assertGreater(comparados, 30)

    def test_todas_las_rutas_son_validas_y_ninguna_supera_el_optimo(self):
        m = generate_map(seed=3)
        start, goal = default_endpoints(m.width, m.height)
        best = uniform_cost(m, start, goal)
        if not best.found:
            self.skipTest("mapa sin solución")
        for name, fn in ALGORITHMS.items():
            r = fn(m, start, goal)
            self.assertTrue(valid_path(m, r.path, start, goal), name)
            self.assertGreaterEqual(r.cost, best.cost, name)

    def test_sin_camino_cuando_el_agua_aisla_la_meta(self):
        costs = [GRASS] * 25
        for y in range(5):
            costs[y * 5 + 2] = BLOCKED  # muro de agua vertical
        m = GameMap(5, 5, costs)
        for name in ALGORITHMS:
            r = search(name, m, 0, 4)
            self.assertFalse(r.found, name)
            self.assertEqual(r.path, [])

    def test_voraz_expande_menos_que_costo_uniforme_en_campo_abierto(self):
        m = GameMap(20, 20, [GRASS] * 400)
        self.assertLess(greedy(m, 0, 399).expanded, uniform_cost(m, 0, 399).expanded)

    def test_algoritmo_desconocido(self):
        with self.assertRaises(ValueError):
            search("dfs", GameMap(2, 2, [1] * 4), 0, 3)


class GeneratorTests(unittest.TestCase):
    def test_misma_semilla_mismo_mapa(self):
        self.assertEqual(generate_map(seed=11).costs, generate_map(seed=11).costs)

    def test_inicio_y_cofre_transitables(self):
        for seed in range(20):
            m = generate_map(seed=seed)
            s, g = default_endpoints(m.width, m.height)
            self.assertTrue(m.passable(s) and m.passable(g))

    def test_mapa_invalido(self):
        with self.assertRaises(ValueError):
            GameMap(3, 3, [1] * 8)
        with self.assertRaises(ValueError):
            GameMap(2, 2, [1, 1, 1, 9])


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server("127.0.0.1", 0)  # puerto libre
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def post(self, path, body):
        req = urllib.request.Request(self.base + path, json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.load(resp)
        except urllib.error.HTTPError as err:
            return err.code, json.load(err)

    def test_mapa_search_y_compare(self):
        with urllib.request.urlopen(self.base + "/api/map?seed=5") as resp:
            problem = json.load(resp)
        self.assertEqual(len(problem["costs"]), problem["width"] * problem["height"])
        status, data = self.post("/api/search", {**problem, "algorithm": "astar"})
        self.assertEqual(status, 200)
        self.assertIn("expanded", data)
        status, data = self.post("/api/compare", problem)
        self.assertEqual(status, 200)
        self.assertEqual([r["algorithm"] for r in data["results"]], list(ALGORITHMS))

    def test_errores_de_validacion(self):
        status, data = self.post("/api/search", {"width": 2, "height": 2, "costs": [1, 1, 1, 1], "start": 0, "goal": 9})
        self.assertEqual(status, 400)
        self.assertIn("error", data)
        status, _ = self.post("/api/search", {"hola": 1})
        self.assertEqual(status, 400)

    def test_sirve_el_frontend(self):
        with urllib.request.urlopen(self.base + "/") as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn(b"<html", resp.read().lower())


if __name__ == "__main__":
    unittest.main()
