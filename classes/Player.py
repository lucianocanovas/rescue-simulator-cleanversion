"""Clase que representa a un jugador (equipo).

Contiene nombre, puntos y lista de vehículos asociados.
"""

from strategies import Strategy
from typing import Any


class Player:
    def __init__(self, name: str, strategy: Strategy):
        self.name: str = name
        self.points: int = 0
        self.vehicles: list[Any] = []
        # Estadísticas de items recolectados por tipo
        self.items_collected: dict[str, int] = {
            'Person': 0,
            'Weapon': 0,
            'Clothing': 0,
            'Food': 0,
            'Heal': 0
        }

    def add_vehicle(self, vehicle: Any) -> None:
        self.vehicles.append(vehicle)

    def add_points(self, points: int) -> None:
        self.points += points
    
    def register_item(self, item_type: str) -> None:
        """Registra un item recolectado por tipo"""
        if item_type in self.items_collected:
            self.items_collected[item_type] += 1