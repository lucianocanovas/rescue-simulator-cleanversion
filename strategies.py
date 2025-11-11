from pathfinding import find_nearest, find_farthest, find_path_to_column, bfs

class Strategy:
    def plan(self, vehicle, map_manager):
        raise NotImplementedError("Strategy.plan must be implemented by subclasses")
    
class PickNearest(Strategy):
    """Estrategia: Recoger el objeto más cercano y llevarlo a la base."""
    def plan(self, vehicle, map_manager):
        # Si ya tiene un plan, no hacer nada
        if vehicle.path:
            return
        
        # Si no está lleno, buscar el objeto más cercano
        if len(vehicle.load) < vehicle.capacity:
            path = find_nearest(map_manager.grid, vehicle.position, map_manager.danger_zones, 
                              only_persons=vehicle.only_persons, exclude_persons=vehicle.exclude_persons)
            if path:
                vehicle.path = path[1:]  # Excluir posición actual
                vehicle.state = 'collecting'
                return
        
        # Si está lleno o no hay objetos, volver a la base
        base_x = 0 if map_manager.player1 is vehicle.team else map_manager.width - 1
        path = find_path_to_column(map_manager.grid, vehicle.position, base_x, map_manager.danger_zones)
        if path:
            vehicle.path = path[1:]
            vehicle.state = 'returning'
    
class Kamikaze(Strategy):
    """Estrategia: Buscar vehículos enemigos cercanos y chocar contra ellos."""
    def plan(self, vehicle, map_manager):
        # Si ya tiene un plan, no hacer nada
        if vehicle.path:
            return
        
        # Buscar vehículos enemigos
        enemy_vehicles = map_manager.player2.vehicles if vehicle.team == map_manager.player1 else map_manager.player1.vehicles
        
        # Encontrar el vehículo enemigo más cercano usando BFS
        closest_enemy = None
        closest_path = None
        min_distance = float('inf')
        
        for enemy in enemy_vehicles:
            try:
                path = bfs(map_manager.grid, vehicle.position, enemy.position)
                if path and len(path) < min_distance:
                    min_distance = len(path)
                    closest_path = path
                    closest_enemy = enemy
            except Exception:
                continue
        
        # Si hay un enemigo cercano, ir hacia él
        if closest_path and len(closest_path) > 1:
            vehicle.path = closest_path[1:]  # Excluir posición actual
            vehicle.state = 'attacking'
            return
        
        # Si no hay enemigos o no se puede alcanzar, comportarse como PickNearest
        PickNearest().plan(vehicle, map_manager)

class Escort(Strategy):
    """Estrategia: Proteger vehículos aliados cercanos moviéndose cerca de ellos."""
    def plan(self, vehicle, map_manager):
        # Si ya tiene un plan, no hacer nada
        if vehicle.path:
            return
        
        # Obtener vehículos aliados
        allied_vehicles = [v for v in vehicle.team.vehicles if v is not vehicle]
        
        if not allied_vehicles:
            # Si no hay aliados, comportarse como PickNearest
            PickNearest().plan(vehicle, map_manager)
            return
        
        # Encontrar el aliado más cercano que esté recolectando
        closest_ally = None
        closest_path = None
        min_distance = float('inf')
        
        for ally in allied_vehicles:
            # Priorizar aliados que están en estado 'collecting'
            if ally.state == 'collecting' or len(ally.load) > 0:
                try:
                    path = bfs(map_manager.grid, vehicle.position, ally.position)
                    if path and len(path) < min_distance:
                        min_distance = len(path)
                        closest_path = path
                        closest_ally = ally
                except Exception:
                    continue
        
        # Si está muy cerca del aliado (distancia <= 3), recoger objetos cercanos
        if closest_ally and min_distance <= 3:
            PickNearest().plan(vehicle, map_manager)
            return
        
        # Si hay un aliado para proteger y está lejos, moverse hacia él
        if closest_path and len(closest_path) > 1:
            # Moverse hacia el aliado pero no demasiado cerca
            target_distance = min(len(closest_path) - 1, 5)
            if target_distance > 0:
                vehicle.path = closest_path[1:target_distance]
                vehicle.state = 'escorting'
                return
        
        # Si no hay aliados para proteger, comportarse como PickNearest
        PickNearest().plan(vehicle, map_manager)

class Invader(Strategy):
    """Estrategia: Recoger objetos más lejanos para explorar más el mapa."""
    def plan(self, vehicle, map_manager):
        # Si ya tiene un plan, no hacer nada
        if vehicle.path:
            return
        
        # Si no está lleno, buscar el objeto más lejano
        if len(vehicle.load) < vehicle.capacity:
            path = find_farthest(map_manager.grid, vehicle.position, map_manager.danger_zones, 
                               only_persons=vehicle.only_persons, exclude_persons=vehicle.exclude_persons)
            if path:
                vehicle.path = path[1:]  # Excluir posición actual
                vehicle.state = 'collecting'
                return
        
        # Si está lleno o no hay objetos, volver a la base
        base_x = 0 if map_manager.player1 is vehicle.team else map_manager.width - 1
        path = find_path_to_column(map_manager.grid, vehicle.position, base_x, map_manager.danger_zones)
        if path:
            vehicle.path = path[1:]
            vehicle.state = 'returning'