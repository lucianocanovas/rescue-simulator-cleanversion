class Strategy:
    def plan(self, vehicle, map_manager):
        raise NotImplementedError("Strategy.plan must be implemented by subclasses")
    
class PickNearest(Strategy):
    def plan(self, vehicle, map_manager):
        pass
    
class Kamikaze(Strategy):
    def plan(self, vehicle, map_manager):
        pass

class Escort(Strategy):
    def plan(self, vehicle, map_manager):
        pass

class Invader(Strategy):
    def plan(self, vehicle, map_manager):
        pass