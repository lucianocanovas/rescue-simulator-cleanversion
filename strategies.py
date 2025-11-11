class Strategy:
    def plan(self, vehicle, map_manager):
        raise NotImplementedError("Strategy.plan must be implemented by subclasses")
    
class PickNearest(Strategy):
    def plan(self, vehicle, map_manager):
        # RECOGER EL OBJETO MÁS CERCANO
        pass
    
class Kamikaze(Strategy):
    def plan(self, vehicle, map_manager):
        # BUSCAR VEHICULOS ENEMIGOS CERCANOS Y CHOCAR CONTRA ELLOS
        pass

class Escort(Strategy):
    def plan(self, vehicle, map_manager):
        # PROTEGER VEHÍCULOS ALIADOS CERCANOS
        pass

class Invader(Strategy):
    def plan(self, vehicle, map_manager):
        # RECOGER OBJETOS MAS LEJANOS
        pass