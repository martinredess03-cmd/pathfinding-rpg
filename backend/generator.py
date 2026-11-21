"""Generación procedimental de mapas: dos campos de ruido suavizado (altura y humedad)."""
from __future__ import annotations

import random
from typing import List, Optional, Tuple

from .grid import BLOCKED, FOREST, GRASS, SWAMP, GameMap

WATER_THRESHOLD = 0.36   # altura menor a este valor -> agua
FOREST_THRESHOLD = 0.66  # humedad mayor -> bosque
SWAMP_THRESHOLD = 0.28   # humedad menor -> pantano
BLUR_PASSES = 4


def _blur(field: List[float], width: int, height: int) -> List[float]:
    """Filtro de promedio 3 x 3."""
    out = [0.0] * len(field)
    for y in range(height):
        for x in range(width):
            total, count = 0.0, 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        total += field[ny * width + nx]
                        count += 1
            out[y * width + x] = total / count
    return out


def _noise_field(rng: random.Random, width: int, height: int) -> List[float]:
    field = [rng.random() for _ in range(width * height)]
    for _ in range(BLUR_PASSES):
        field = _blur(field, width, height)
    low, high = min(field), max(field)
    span = (high - low) or 1.0
    return [(v - low) / span for v in field]


def default_endpoints(width: int, height: int) -> Tuple[int, int]:
    """Inicio a la izquierda y cofre a la derecha, a media altura."""
    row = height // 2
    return row * width + 2, row * width + (width - 3)


def generate_map(width: int = 40, height: int = 24, seed: Optional[int] = None) -> GameMap:
    """Crea un mapa. Con la misma semilla se obtiene siempre el mismo mapa."""
    rng = random.Random(seed)
    altitude = _noise_field(rng, width, height)
    moisture = _noise_field(rng, width, height)
    costs = []
    for a, m in zip(altitude, moisture):
        if a < WATER_THRESHOLD:
            costs.append(BLOCKED)
        elif m > FOREST_THRESHOLD:
            costs.append(FOREST)
        elif m < SWAMP_THRESHOLD:
            costs.append(SWAMP)
        else:
            costs.append(GRASS)
    start, goal = default_endpoints(width, height)
    costs[start] = costs[goal] = GRASS  # inicio y cofre siempre transitables
    return GameMap(width, height, costs)


def random_endpoints(game_map: GameMap, rng: random.Random, min_distance: int = 20) -> Optional[Tuple[int, int]]:
    """Par inicio-meta aleatorio sobre casillas transitables, separados `min_distance` o más."""
    free = [i for i in range(game_map.size) if game_map.passable(i)]
    if len(free) < 2:
        return None
    for _ in range(50):
        start, goal = rng.choice(free), rng.choice(free)
        if game_map.manhattan(start, goal) >= min_distance:
            return start, goal
    return None
