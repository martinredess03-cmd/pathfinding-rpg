"""Representación del mapa del juego como una cuadrícula con costos de terreno."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

# Costo de entrada de cada terreno. El agua es infranqueable (costo 0 = bloqueado).
BLOCKED = 0
GRASS = 1
FOREST = 3
SWAMP = 6

TERRAIN_NAMES: Dict[int, str] = {BLOCKED: "agua", GRASS: "pasto", FOREST: "bosque", SWAMP: "pantano"}
VALID_COSTS = frozenset(TERRAIN_NAMES)


@dataclass
class GameMap:
    """Cuadrícula de `width` x `height` casillas guardada como arreglo plano.

    La casilla (x, y) ocupa el índice ``y * width + x``.
    """

    width: int
    height: int
    costs: List[int]

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("El mapa debe tener dimensiones positivas")
        if len(self.costs) != self.width * self.height:
            raise ValueError("El número de costos no coincide con width * height")
        if any(c not in VALID_COSTS for c in self.costs):
            raise ValueError("Hay costos de terreno no válidos")

    @property
    def size(self) -> int:
        return self.width * self.height

    def coords(self, index: int) -> tuple[int, int]:
        return index % self.width, index // self.width

    def passable(self, index: int) -> bool:
        return self.costs[index] != BLOCKED

    def neighbors(self, index: int) -> List[int]:
        """Vecinas en 4 direcciones dentro del mapa (sin filtrar el agua)."""
        x, y = self.coords(index)
        result = []
        if x > 0:
            result.append(index - 1)
        if x < self.width - 1:
            result.append(index + 1)
        if y > 0:
            result.append(index - self.width)
        if y < self.height - 1:
            result.append(index + self.width)
        return result

    def manhattan(self, a: int, b: int) -> int:
        """Distancia de Manhattan: heurística admisible y consistente (costo mínimo = 1)."""
        ax, ay = self.coords(a)
        bx, by = self.coords(b)
        return abs(ax - bx) + abs(ay - by)

    def to_dict(self) -> dict:
        return {"width": self.width, "height": self.height, "costs": self.costs}

    @classmethod
    def from_dict(cls, data: dict) -> "GameMap":
        return cls(int(data["width"]), int(data["height"]), [int(c) for c in data["costs"]])
