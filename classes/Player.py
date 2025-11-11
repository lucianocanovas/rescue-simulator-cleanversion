from strategies import Strategy
from typing import Any


class Player:
    def __init__(self, name: str, strategy: Strategy):
        self.name: str = name
        self.points: int = 0
        self.vehicles: list[Any] = []
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
        if item_type in self.items_collected:
            self.items_collected[item_type] += 1