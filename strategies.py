from pathfinding import find_nearest, find_farthest, find_path_to_column, bfs

class Strategy:
    def plan(self, vehicle, map_manager):
        raise NotImplementedError("Strategy.plan must be implemented by subclasses")
    
class PickNearest(Strategy):
    def plan(self, vehicle, map_manager):
        if vehicle.path:
            return
        
        if len(vehicle.load) < vehicle.capacity:
            path = find_nearest(map_manager.grid, vehicle.position, map_manager.danger_zones, 
                              only_persons=vehicle.only_persons, exclude_persons=vehicle.exclude_persons)
            if path:
                vehicle.path = path[1:]
                vehicle.state = 'collecting'
                return
            else:
                base_x = 0 if map_manager.player1 is vehicle.team else map_manager.width - 1
                path = find_path_to_column(map_manager.grid, vehicle.position, base_x, map_manager.danger_zones)
                if path:
                    vehicle.path = path[1:]
                    vehicle.state = 'returning'
                return
        
        base_x = 0 if map_manager.player1 is vehicle.team else map_manager.width - 1
        path = find_path_to_column(map_manager.grid, vehicle.position, base_x, map_manager.danger_zones)
        if path:
            vehicle.path = path[1:]
            vehicle.state = 'returning'
    
class Kamikaze(Strategy):
    def plan(self, vehicle, map_manager):
        if vehicle.path:
            return
        
        enemy_vehicles = map_manager.player2.vehicles if vehicle.team == map_manager.player1 else map_manager.player1.vehicles
        
        closest_enemy = None
        closest_path = None
        minimum_distance = float('inf')
        
        for enemy in enemy_vehicles:
            try:
                path = bfs(map_manager.grid, vehicle.position, enemy.position)
                if path and len(path) < minimum_distance:
                    minimum_distance = len(path)
                    closest_path = path
                    closest_enemy = enemy
            except Exception:
                continue
        
        if closest_path and len(closest_path) > 1:
            vehicle.path = closest_path[1:]
            vehicle.state = 'attacking'
            return
        
        PickNearest().plan(vehicle, map_manager)

class Escort(Strategy):
    def plan(self, vehicle, map_manager):
        if vehicle.path:
            return
        
        allied_vehicles = [ally for ally in vehicle.team.vehicles if ally is not vehicle]
        
        if not allied_vehicles:
            PickNearest().plan(vehicle, map_manager)
            return
        
        closest_ally = None
        closest_path = None
        minimum_distance = float('inf')
        
        for ally in allied_vehicles:
            if ally.state == 'collecting' or len(ally.load) > 0:
                try:
                    path = bfs(map_manager.grid, vehicle.position, ally.position)
                    if path and len(path) < minimum_distance:
                        minimum_distance = len(path)
                        closest_path = path
                        closest_ally = ally
                except Exception:
                    continue
        
        if closest_ally and minimum_distance <= 3:
            PickNearest().plan(vehicle, map_manager)
            return
        
        if closest_path and len(closest_path) > 1:
            target_distance = min(len(closest_path) - 1, 5)
            if target_distance > 0:
                vehicle.path = closest_path[1:target_distance]
                vehicle.state = 'escorting'
                return
        
        PickNearest().plan(vehicle, map_manager)

class Invader(Strategy):
    def plan(self, vehicle, map_manager):
        if vehicle.path:
            return
        
        if len(vehicle.load) < vehicle.capacity:
            path = find_farthest(map_manager.grid, vehicle.position, map_manager.danger_zones, 
                               only_persons=vehicle.only_persons, exclude_persons=vehicle.exclude_persons)
            if path:
                vehicle.path = path[1:]
                vehicle.state = 'collecting'
                return
            else:
                base_x = 0 if map_manager.player1 is vehicle.team else map_manager.width - 1
                path = find_path_to_column(map_manager.grid, vehicle.position, base_x, map_manager.danger_zones)
                if path:
                    vehicle.path = path[1:]
                    vehicle.state = 'returning'
                return
        
        base_x = 0 if map_manager.player1 is vehicle.team else map_manager.width - 1
        path = find_path_to_column(map_manager.grid, vehicle.position, base_x, map_manager.danger_zones)
        if path:
            vehicle.path = path[1:]
            vehicle.state = 'returning'

class FullSafe(Strategy):
    def _get_turns_until_g1_toggle(self, map_manager):
        current_turn = getattr(map_manager, 'current_turn', 0)
        turns_until_toggle = (5 - ((current_turn + 1) % 5)) % 5
        if turns_until_toggle == 0:
            turns_until_toggle = 5
        return turns_until_toggle
    
    def _create_danger_zones_with_timing(self, map_manager, path_length):
        from classes.Mine import Mine_G1
        
        danger_zones = [[False for _ in range(map_manager.height)] for _ in range(map_manager.width)]
        
        for x in range(map_manager.width):
            for y in range(map_manager.height):
                danger_zones[x][y] = map_manager.danger_zones[x][y]
        
        turns_until_toggle = self._get_turns_until_g1_toggle(map_manager)
        
        for mine in map_manager.mines:
            mine_x, mine_y = mine.position
            
            if isinstance(mine, Mine_G1):
                is_currently_active = (mine.x_radius > 0 and mine.y_radius > 0)
                
                if is_currently_active:
                    safety_buffer = 2
                    for delta_x in range(-mine.x_radius - safety_buffer, mine.x_radius + safety_buffer + 1):
                        for delta_y in range(-mine.y_radius - safety_buffer, mine.y_radius + safety_buffer + 1):
                            new_x, new_y = mine_x + delta_x, mine_y + delta_y
                            if 0 <= new_x < map_manager.width and 0 <= new_y < map_manager.height:
                                danger_zones[new_x][new_y] = True
                else:
                    if path_length + 2 >= turns_until_toggle:
                        max_radius = 7
                        safety_buffer = 2
                        for delta_x in range(-max_radius - safety_buffer, max_radius + safety_buffer + 1):
                            for delta_y in range(-max_radius - safety_buffer, max_radius + safety_buffer + 1):
                                new_x, new_y = mine_x + delta_x, mine_y + delta_y
                                if 0 <= new_x < map_manager.width and 0 <= new_y < map_manager.height:
                                    danger_zones[new_x][new_y] = True
            else:
                safety_buffer = 1
                for delta_x in range(-mine.x_radius - safety_buffer, mine.x_radius + safety_buffer + 1):
                    for delta_y in range(-mine.y_radius - safety_buffer, mine.y_radius + safety_buffer + 1):
                        new_x, new_y = mine_x + delta_x, mine_y + delta_y
                        if 0 <= new_x < map_manager.width and 0 <= new_y < map_manager.height:
                            danger_zones[new_x][new_y] = True
        
        return danger_zones
    
    def _is_path_safe_with_timing(self, path, map_manager):
        if not path or len(path) < 2:
            return True
        
        from classes.Mine import Mine_G1
        
        turns_until_toggle = self._get_turns_until_g1_toggle(map_manager)
        path_length = len(path) - 1
        
        for step, position in enumerate(path[1:], 1):
            pos_x, pos_y = position
            
            if not (0 <= pos_x < map_manager.width and 0 <= pos_y < map_manager.height):
                return False
            
            for mine in map_manager.mines:
                mine_x, mine_y = mine.position
                
                if isinstance(mine, Mine_G1):
                    is_active = (mine.x_radius > 0 and mine.y_radius > 0)
                    
                    turn_when_at_position = step
                    will_toggle_before = (turn_when_at_position >= turns_until_toggle)
                    
                    mine_state_then = not is_active if will_toggle_before else is_active
                    
                    if mine_state_then:
                        max_radius = 7
                        if abs(pos_x - mine_x) <= max_radius and abs(pos_y - mine_y) <= max_radius:
                            return False
                else:
                    if abs(pos_x - mine_x) <= mine.x_radius and abs(pos_y - mine_y) <= mine.y_radius:
                        return False
        
        return True
    
    def plan(self, vehicle, map_manager):
        if vehicle.path:
            full_path = [vehicle.position] + vehicle.path
            if not self._is_path_safe_with_timing(full_path, map_manager):
                vehicle.path = []
                vehicle.state = 'idle'
        
        if vehicle.path:
            return
        
        max_path_estimate = int((map_manager.width**2 + map_manager.height**2)**0.5)
        
        if len(vehicle.load) < vehicle.capacity:
            danger_zones_optimized = self._create_danger_zones_with_timing(map_manager, max_path_estimate // 2)
            path = find_nearest(map_manager.grid, vehicle.position, danger_zones_optimized,
                              only_persons=vehicle.only_persons, exclude_persons=vehicle.exclude_persons)
            
            if path and len(path) > 1:
                if self._is_path_safe_with_timing(path, map_manager):
                    vehicle.path = path[1:]
                    vehicle.state = 'collecting'
                    return
            
            base_x = 0 if map_manager.player1 is vehicle.team else map_manager.width - 1
            danger_zones_base = self._create_danger_zones_with_timing(map_manager, max_path_estimate)
            path = find_path_to_column(map_manager.grid, vehicle.position, base_x, danger_zones_base)
            
            if path and len(path) > 1:
                if self._is_path_safe_with_timing(path, map_manager):
                    vehicle.path = path[1:]
                    vehicle.state = 'returning'
                    return
            
            vehicle.path = []
            vehicle.state = 'waiting'
            return
        
        base_x = 0 if map_manager.player1 is vehicle.team else map_manager.width - 1
        danger_zones_base = self._create_danger_zones_with_timing(map_manager, max_path_estimate)
        path = find_path_to_column(map_manager.grid, vehicle.position, base_x, danger_zones_base)
        
        if path and len(path) > 1:
            if self._is_path_safe_with_timing(path, map_manager):
                vehicle.path = path[1:]
                vehicle.state = 'returning'
                return
        
        vehicle.path = []
        vehicle.state = 'waiting'
