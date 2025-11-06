"""Clase que representa a un jugador (equipo).

Contiene nombre, puntos y lista de vehículos asociados.
"""

from strategies import Strategy
from typing import Any


class Player:
    """Representa a un jugador.

    Atributos:
        name: nombre del jugador.
        points: puntos acumulados.
        vehicles: lista de vehículos propiedad del jugador.
    """

    def __init__(self, name: str, strategy: Strategy):
        self.name: str = name
        self.points: int = 0
        self.vehicles: list[Any] = []

    def add_vehicle(self, vehicle: Any) -> None:
        """Añade un vehículo al jugador."""
        self.vehicles.append(vehicle)

    def add_points(self, points: int) -> None:
        """Suma puntos al total del jugador."""
        self.points += points