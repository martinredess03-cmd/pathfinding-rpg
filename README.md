# El camino del héroe: búsqueda de rutas en un videojuego

**Universidad Tecnológica de Puebla** · Producto II · Martin Romero Velez

Proyecto de Inteligencia Artificial que compara algoritmos de **búsqueda ciega** (anchura y costo uniforme) y **búsqueda heurística** (voraz y A*) para resolver un problema típico de videojuegos: llevar a un personaje hasta un cofre a través de un mapa con terrenos de distinto costo.

Los algoritmos están programados en el **backend (Python)** y se exponen mediante una **API REST**; el **frontend** (HTML, CSS y JavaScript) dibuja el mapa, anima la búsqueda y muestra las métricas.

## El problema

Mapa de 40 × 24 casillas. El héroe se mueve en 4 direcciones y paga el costo de la casilla a la que entra:

| Terreno | Costo |
|---|---|
| Pasto | 1 |
| Bosque | 3 |
| Pantano | 6 |
| Agua | bloqueado |

Objetivo: encontrar la ruta de **menor costo** entre el inicio y el cofre explorando el menor número de casillas.

## Algoritmos

| Algoritmo | Tipo | Criterio | ¿Óptimo? |
|---|---|---|---|
| BFS (`bfs`) | Ciega | Menor número de pasos | No, ignora los costos |
| Costo uniforme (`dijkstra`) | Ciega | Menor costo acumulado g(n) | Sí |
| Voraz (`greedy`) | Heurística | Menor h(n) | No |
| A* (`astar`) | Heurística | Menor f(n) = g(n) + h(n) | Sí |

La heurística es la **distancia de Manhattan**, admisible y consistente porque el costo mínimo de una casilla es 1.

## Estructura del proyecto

```
pathfinding-rpg/
├── backend/
│   ├── grid.py          # Mapa: costos de terreno, vecindad y heurística
│   ├── generator.py     # Generación procedimental de mapas (ruido suavizado)
│   ├── algorithms.py    # BFS, costo uniforme, voraz y A*
│   ├── experiment.py    # Comparación en cientos de mapas aleatorios
│   └── server.py        # API REST + servidor del frontend (biblioteca estándar)
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js           # Dibujo, animación y consumo de la API
├── scripts/
│   └── run_experiment.py  # Experimento desde la terminal
├── tests/
│   └── test_algorithms.py # Pruebas de algoritmos, generador y API
└── docs/                  # Informe en PDF (agregar aquí)
```

## Requisitos

- Python 3.9 o superior.
- No hay dependencias externas.

## Cómo ejecutarlo

```bash
git clone <url-del-repositorio>
cd pathfinding-rpg
python -m backend.server            # http://127.0.0.1:8000
```

Abre `http://127.0.0.1:8000` en el navegador. Para cambiar el puerto: `python -m backend.server --port 9000`.

**Experimento desde la terminal**

```bash
python scripts/run_experiment.py --maps 200 --seed 42
python scripts/run_experiment.py --maps 200 --seed 42 --csv resultados.csv
```

**Pruebas**

```bash
python -m unittest discover -s tests -v
```

## API REST

| Método y ruta | Descripción |
|---|---|
| `GET /api/map?seed=N` | Genera un mapa y devuelve `width`, `height`, `costs`, `start`, `goal` y `seed` |
| `POST /api/search` | Ejecuta un algoritmo. Cuerpo: el mapa más `algorithm` (`bfs`, `dijkstra`, `greedy` o `astar`) |
| `POST /api/compare` | Ejecuta los cuatro algoritmos sobre el mismo mapa |
| `GET /api/experiment?maps=200&seed=42` | Promedios en mapas aleatorios (máximo 500 mapas) |

Ejemplo:

```bash
curl -s "http://127.0.0.1:8000/api/map?seed=5" > mapa.json
curl -s -X POST http://127.0.0.1:8000/api/compare \
     -H "Content-Type: application/json" -d @mapa.json
```

Respuesta de `/api/search`: `found`, `path`, `expanded_order`, `cost`, `steps`, `expanded` y `elapsed_ms`. El servidor valida el cuerpo (dimensiones, costos, inicio y meta) y responde `400` con un mensaje de error si algo no es válido.

## Resultados

Promedios en 200 mapas aleatorios con semilla 42 (`python scripts/run_experiment.py`):

| Algoritmo | Nodos expandidos | Costo de la ruta | Rutas óptimas |
|---|---|---|---|
| BFS (ciega) | 546.6 | 61.88 | 10.0 % |
| Costo uniforme (ciega) | 517.0 | 40.59 | 100 % |
| Voraz (heurística) | 42.5 | 66.06 | 9.0 % |
| A* (heurística) | 175.5 | 40.59 | 100 % |

- A* obtiene siempre la ruta óptima, igual que costo uniforme, pero expande cerca de **66 % menos casillas**.
- BFS y la búsqueda voraz producen rutas entre 52 % y 63 % más caras que la óptima.
- La búsqueda voraz es la que menos explora, a costa de la calidad de la ruta.

Los tiempos dependen del equipo. Con otra semilla los valores cambian ligeramente, pero el orden entre algoritmos se mantiene. Los valores del informe en PDF provienen de una versión previa del experimento hecha en JavaScript, con otro generador de números aleatorios, por eso difieren un poco de esta tabla.

## Correspondencia con el informe

| Punto de la actividad | Dónde verlo en el proyecto |
|---|---|
| Descripción del problema | Secciones «El problema» y «Algoritmos» de este archivo |
| Metodología | `backend/algorithms.py` y `backend/experiment.py` |
| Justificación del algoritmo | Tabla de algoritmos y sección «Resultados» |
| Producto de la implementación | Todo el repositorio: backend, API REST y frontend |
| Adquisición y preparación de datos | `backend/generator.py` (generación de mapas) y `backend/grid.py` (validación) |
| Interpretación de resultados | Sección «Resultados» y el informe en `docs/` |
| Conclusiones | Informe en `docs/` |

## Autor

Martin Romero Velez · Universidad Tecnológica de Puebla · Producto II
