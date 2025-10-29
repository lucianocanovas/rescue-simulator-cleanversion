from strategies import Strategy

class Player:
    def __init__(self, strategy: Strategy):
        self.points = 0
        self.vehicles = []

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)

    def add_points(self, points):
        self.points += points