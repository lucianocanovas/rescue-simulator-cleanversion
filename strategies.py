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

class FullSafe(Strategy):
    """Estrategia ultra-cautelosa e inteligente que:
    - Evita zonas de peligro con buffer de seguridad
    - Calcula cuándo las minas G1 se activarán/desactivarán
    - Puede atravesar zonas de mina G1 desactivada si tiene tiempo suficiente
    - Replanifica constantemente para adaptarse a cambios en el mapa
    """
    
    def _get_turns_until_g1_toggle(self, map_manager):
        """Calcula cuántos turnos faltan hasta el próximo toggle de minas G1.
        Las minas G1 se activan/desactivan cada 5 turnos (en turnos 4, 9, 14, 19, etc.)
        """
        current_turn = getattr(map_manager, 'current_turn', 0)
        # El toggle ocurre cuando (current_turn + 1) % 5 == 0
        # Es decir, en los turnos 4, 9, 14, 19, etc.
        turns_until_toggle = (5 - ((current_turn + 1) % 5)) % 5
        if turns_until_toggle == 0:
            turns_until_toggle = 5  # Si es ahora, el próximo es en 5 turnos
        return turns_until_toggle
    
    def _create_danger_zones_with_timing(self, map_manager, path_length):
        """Crea un mapa de zonas peligrosas considerando:
        1. Zonas de peligro actuales
        2. Minas G1 que podrían activarse durante el recorrido
        3. Buffer de seguridad alrededor de otras minas
        
        Args:
            map_manager: Gestor del mapa
            path_length: Longitud estimada del camino (en turnos)
        
        Returns:
            Array 2D de zonas peligrosas
        """
        from classes.Mine import Mine_G1
        
        # Copiar las zonas de peligro actuales
        danger_zones = [[False for _ in range(map_manager.height)] for _ in range(map_manager.width)]
        
        # Copiar zonas de peligro existentes
        for x in range(map_manager.width):
            for y in range(map_manager.height):
                danger_zones[x][y] = map_manager.danger_zones[x][y]
        
        # Calcular turnos hasta el próximo toggle de G1
        turns_until_toggle = self._get_turns_until_g1_toggle(map_manager)
        
        # Procesar cada mina
        for mine in map_manager.mines:
            mx, my = mine.position
            
            if isinstance(mine, Mine_G1):
                # Para minas G1, ser inteligente según el tiempo disponible
                is_currently_active = (mine.x_radius > 0 and mine.y_radius > 0)
                
                if is_currently_active:
                    # La mina está activa: NUNCA atravesar + buffer de seguridad
                    safety_buffer = 2
                    for dx in range(-mine.x_radius - safety_buffer, mine.x_radius + safety_buffer + 1):
                        for dy in range(-mine.y_radius - safety_buffer, mine.y_radius + safety_buffer + 1):
                            nx, ny = mx + dx, my + dy
                            if 0 <= nx < map_manager.width and 0 <= ny < map_manager.height:
                                danger_zones[nx][ny] = True
                else:
                    # La mina está desactivada: calcular si podemos atravesarla
                    # Si tenemos tiempo suficiente (con margen de seguridad de 2 turnos), 
                    # NO marcar como peligrosa en el mapa inicial
                    # La verificación temporal en _is_path_safe_with_timing se encargará de validar
                    if path_length + 2 >= turns_until_toggle:
                        # NO hay tiempo suficiente para caminos largos, marcar como peligrosa
                        max_radius = 7
                        safety_buffer = 2
                        for dx in range(-max_radius - safety_buffer, max_radius + safety_buffer + 1):
                            for dy in range(-max_radius - safety_buffer, max_radius + safety_buffer + 1):
                                nx, ny = mx + dx, my + dy
                                if 0 <= nx < map_manager.width and 0 <= ny < map_manager.height:
                                    danger_zones[nx][ny] = True
                    # Si hay tiempo suficiente, NO marcar (permitir paso)
                    # La verificación paso a paso validará la seguridad real
            else:
                # Para otras minas, agregar un pequeño buffer de seguridad
                safety_buffer = 1
                for dx in range(-mine.x_radius - safety_buffer, mine.x_radius + safety_buffer + 1):
                    for dy in range(-mine.y_radius - safety_buffer, mine.y_radius + safety_buffer + 1):
                        nx, ny = mx + dx, my + dy
                        if 0 <= nx < map_manager.width and 0 <= ny < map_manager.height:
                            danger_zones[nx][ny] = True
        
        return danger_zones
    
    def _is_path_safe_with_timing(self, path, map_manager):
        """Verifica si un camino es seguro considerando el tiempo de recorrido
        y cuándo se activarán las minas G1.
        """
        if not path or len(path) < 2:
            return True
        
        from classes.Mine import Mine_G1
        
        turns_until_toggle = self._get_turns_until_g1_toggle(map_manager)
        path_length = len(path) - 1  # Excluir posición actual
        
        # Verificar cada posición del camino
        for step, pos in enumerate(path[1:], 1):  # Empezar desde el paso 1
            x, y = pos
            
            # Verificar límites
            if not (0 <= x < map_manager.width and 0 <= y < map_manager.height):
                return False
            
            # Verificar si hay una mina en esta posición o cerca
            for mine in map_manager.mines:
                mx, my = mine.position
                
                if isinstance(mine, Mine_G1):
                    is_active = (mine.x_radius > 0 and mine.y_radius > 0)
                    
                    # Calcular si la mina estará activa cuando lleguemos a este paso
                    turn_when_at_position = step
                    will_toggle_before = (turn_when_at_position >= turns_until_toggle)
                    
                    # Estado de la mina cuando estemos en esa posición
                    mine_state_then = not is_active if will_toggle_before else is_active
                    
                    # Si la mina estará activa, verificar si estamos en rango
                    if mine_state_then:
                        max_radius = 7
                        if abs(x - mx) <= max_radius and abs(y - my) <= max_radius:
                            return False  # Peligro!
                else:
                    # Otras minas siempre están activas
                    if abs(x - mx) <= mine.x_radius and abs(y - my) <= mine.y_radius:
                        return False
        
        return True
    
    def plan(self, vehicle, map_manager):
        # Verificar si la ruta actual sigue siendo segura con cálculo temporal
        if vehicle.path:
            full_path = [vehicle.position] + vehicle.path
            if not self._is_path_safe_with_timing(full_path, map_manager):
                vehicle.path = []
                vehicle.state = 'idle'
        
        # Si ya tiene un plan seguro, mantenerlo
        if vehicle.path:
            return
        
        # Estimar longitud máxima de camino (para cálculo de zonas peligrosas)
        # Usamos la diagonal del mapa como estimación conservadora
        max_path_estimate = int((map_manager.width**2 + map_manager.height**2)**0.5)
        
        # Si no está lleno, buscar el objeto más cercano
        if len(vehicle.load) < vehicle.capacity:
            # Primero intentar con zonas de peligro optimizadas (permite atravesar G1 si hay tiempo)
            danger_zones_optimized = self._create_danger_zones_with_timing(map_manager, max_path_estimate // 2)
            path = find_nearest(map_manager.grid, vehicle.position, danger_zones_optimized,
                              only_persons=vehicle.only_persons, exclude_persons=vehicle.exclude_persons)
            
            if path and len(path) > 1:
                # Verificar que el camino sea seguro considerando el tiempo
                if self._is_path_safe_with_timing(path, map_manager):
                    vehicle.path = path[1:]
                    vehicle.state = 'collecting'
                    return
            
            # Si no hay rutas seguras y el vehículo tiene carga, volver a la base
            if len(vehicle.load) > 0:
                base_x = 0 if map_manager.player1 is vehicle.team else map_manager.width - 1
                danger_zones_base = self._create_danger_zones_with_timing(map_manager, max_path_estimate)
                path = find_path_to_column(map_manager.grid, vehicle.position, base_x, danger_zones_base)
                
                if path and len(path) > 1:
                    if self._is_path_safe_with_timing(path, map_manager):
                        vehicle.path = path[1:]
                        vehicle.state = 'returning'
                        return
            
            # No hay rutas seguras, esperar
            vehicle.path = []
            vehicle.state = 'waiting'
            return
        
        # Si está lleno, volver a la base
        base_x = 0 if map_manager.player1 is vehicle.team else map_manager.width - 1
        danger_zones_base = self._create_danger_zones_with_timing(map_manager, max_path_estimate)
        path = find_path_to_column(map_manager.grid, vehicle.position, base_x, danger_zones_base)
        
        if path and len(path) > 1:
            if self._is_path_safe_with_timing(path, map_manager):
                vehicle.path = path[1:]
                vehicle.state = 'returning'
                return
        
        # No hay camino seguro a la base, esperar
        vehicle.path = []
        vehicle.state = 'waiting'
