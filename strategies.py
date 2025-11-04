class Strategy:
    def plan(self, vehicle, map_manager):
        raise NotImplementedError("Strategy.plan must be implemented by subclasses")
    
class PickNearest(Strategy):
    def plan(self, vehicle, map_manager):
        pass
    
# HAY QUE HACER QUE LOS AUTOS DE DISTINTOS EQUIPOS EXPLOTEN AL CHOCAR
class Kamikaze(Strategy):
    def plan(self, vehicle, map_manager):
        pass

class Escort(Strategy):
    def plan(self, vehicle, map_manager):
        pass

class Invader(Strategy):
    def plan(self, vehicle, map_manager):
        pass