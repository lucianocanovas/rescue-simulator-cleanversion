import random
import pickle      # Biblioteca para guardar partidas
import os          # Para operaciones con archivos y directorios
from datetime import datetime  # Para agregar timestamp a los archivos guardados
from classes.Mine import Mine, Mine_O1, Mine_O2, Mine_T1, Mine_T2, Mine_G1
from classes.Item import Person, Weapon, Clothing, Food, Heal
from classes.Vehicle import Vehicle, Car, Jeep, Motorcycle, Truck
from classes.Player import Player
from strategies import Strategy

class MapManager:
    def __init__(self, player1_strategy: Strategy, player2_strategy: Strategy, width=50, height=50):
        # Player expects (name, strategy)
        self.player1 = Player("Player 1", player1_strategy)
        self.player2 = Player("Player 2", player2_strategy)
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(self.height)] for _ in range(self.width)]
        self.mines = []
        self.danger_zones = [[False for _ in range(self.height)] for _ in range(self.width)]
        self.collision_policy = 'prefer_move'
        self.current_game_folder = self._get_next_game_folder()  # Carpeta para la partida actual
                
    def get_empty_cell(self, margin_x=1, margin_y=0):
        x = random.randint(margin_x, self.width - 1 - margin_x)
        y = random.randint(margin_y, self.height - 1 - margin_y)
        while self.grid[x][y] is not None:
            x = random.randint(margin_x, self.width - 1 - margin_x)
            y = random.randint(margin_y, self.height - 1 - margin_y)
        return (x, y)

    def clear(self):
        """Vacía la grilla y resetea todas las estructuras relacionadas"""
        # Vaciamos la grilla
        for x in range(self.width):
            for y in range(self.height):
                self.grid[x][y] = None
        
        # Limpiamos minas y zonas de peligro
        self.mines = []
        self.danger_zones = [[False for _ in range(self.height)] for _ in range(self.width)]
        
        # Intentamos vaciar las listas de vehículos de los jugadores (si existen)
        try:
            self.player1.vehicles = []
        except Exception:
            pass
        try:
            self.player2.vehicles = []
        except Exception:
            pass
    
    def _get_next_game_folder(self):
        """Obtiene el número de la siguiente partida"""
        # Aseguramos que exista el directorio principal saved_games
        base_dir = "saved_games"
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        # Buscar todas las carpetas de partidas existentes dentro de saved_games
        partidas = []
        try:
            partidas = [d for d in os.listdir(base_dir) if d.startswith('Partida_')]
        except:
            pass
            
        if not partidas:
            # Si no hay partidas, creamos la primera
            new_path = os.path.join(base_dir, "Partida_1")
            os.makedirs(new_path)
            return new_path
        
        # Obtener el último número de partida y sumar 1
        nums = [int(p.split('_')[1]) for p in partidas]
        next_num = max(nums) + 1
        new_path = os.path.join(base_dir, f"Partida_{next_num}")
        os.makedirs(new_path)
        return new_path

    def save_game(self, turn_number):
        # Creamos un diccionario con todo el estado del juego
        game_state = {
            'turn': turn_number,            # Número del turno actual
            'width': self.width,            # Ancho del tablero
            'height': self.height,          # Alto del tablero
            'danger_zones': self.danger_zones,  # Zonas de peligro actuales
            
            # Guardamos solo las posiciones y tipos de objetos en la grilla
            # Convertimos cada objeto a su nombre de clase para evitar problemas de serialización
            'grid_state': [
                [(type(obj).__name__ if obj is not None else None) for obj in row]
                for row in self.grid
            ],
            
            # Guardamos la información esencial de los vehículos de cada jugador
            'vehicles': {
                'player1': [
                    {
                        'type': type(v).__name__,        # Tipo de vehículo (Car, Truck, etc)
                        'position': v.position,           # Posición actual del vehículo
                        'items': [(type(item).__name__, item.position) for item in v.load]  # Items que lleva el vehículo
                    } for v in self.player1.vehicles
                ],
                'player2': [
                    {
                        'type': type(v).__name__,        # Tipo de vehículo (Car, Truck, etc)
                        'position': v.position,           # Posición actual del vehículo
                        'items': [(type(item).__name__, item.position) for item in v.load]  # Items que lleva el vehículo
                    } for v in self.player2.vehicles
                ]
            },
            
            # Guardamos la información de las minas
            'mines': [
                {
                    'type': type(mine).__name__,     # Tipo de mina
                    'position': mine.position,        # Posición de la mina
                    'x_radius': mine.x_radius,       # Radio de explosión en X
                    'y_radius': mine.y_radius        # Radio de explosión en Y
                } for mine in self.mines
            ],
            
            # Guardamos los items que están en el mapa (no dentro de vehículos)
            'items': [
                {
                    'type': type(obj).__name__,
                    'position': (x, y)
                }
                for x in range(self.width)
                for y in range(self.height)
                for obj in [self.grid[x][y]]
                if obj is not None and not any(obj in v.load for v in (self.player1.vehicles + self.player2.vehicles)) and not isinstance(obj, (Vehicle, Mine))
            ],

            # Guardamos los puntos de los jugadores
            'scores': {
                'player1': getattr(self.player1, 'points', 0),  # Puntos del jugador 1
                'player2': getattr(self.player2, 'points', 0)   # Puntos del jugador 2
            }
        }
        
        # Creamos la carpeta de la partida si no existe
        if not os.path.exists(self.current_game_folder):
            os.makedirs(self.current_game_folder)
            
        # Guardamos el turno con número secuencial
        filename = f"{self.current_game_folder}/turno_{turn_number}.pkl"
        
        # Guardamos el estado del juego usando pickle en modo binario
        with open(filename, 'wb') as f:  # 'wb' = write binary
            pickle.dump(game_state, f)    # Serializamos el estado del juego
        
        return filename

    def load_game(self, filename: str, turn: int):
        try:
            # Primero intentamos cargar el archivo para asegurarnos que existe y es válido
            with open(filename, 'rb') as f:  # 'rb' = read binary
                game_state = pickle.load(f)  # Deserializamos el estado del juego
            
            # Si la carga fue exitosa, ahora sí limpiamos y restauramos
            self.clear()  # Limpiamos el estado actual del juego solo si pudimos cargar
            # Ajustamos la carpeta de la partida actual al directorio donde está el archivo
            try:
                self.current_game_folder = os.path.dirname(os.path.abspath(filename))
            except Exception:
                pass
            # Aseguramos listas vacías de vehículos para reconstruir desde el guardado
            try:
                self.player1.vehicles = []
            except Exception:
                pass
            try:
                self.player2.vehicles = []
            except Exception:
                pass
            
            # Restauramos las dimensiones del tablero
            self.width = game_state['width']     # Restauramos ancho
            self.height = game_state['height']    # Restauramos alto
            
            # Restauramos las zonas de peligro
            self.danger_zones = game_state['danger_zones']  # Restauramos matriz de zonas peligrosas
            
            # Recreamos los vehículos del jugador 1
            for vehicle_data in game_state['vehicles']['player1']:

                # Obtenemos la clase del vehículo por su nombre y lo creamos
                vehicle_class = globals()[vehicle_data['type']]
                vehicle = vehicle_class(self.player1, vehicle_data['position'])
                # Restauramos los items que llevaba el vehículo
                for item_type, item_pos in vehicle_data['items']:
                    item_class = globals().get(item_type)
                    if item_class is None:
                        continue
                    item = item_class(item_pos)
                    vehicle.load.append(item)
                self.player1.add_vehicle(vehicle)
                self.grid[vehicle.position[0]][vehicle.position[1]] = vehicle
            
            # Recreamos los vehículos del jugador 2
            for vehicle_data in game_state['vehicles']['player2']:
                # Obtenemos la clase del vehículo por su nombre y lo creamos
                vehicle_class = globals()[vehicle_data['type']]
                vehicle = vehicle_class(self.player2, vehicle_data['position'])
                # Restauramos los items que llevaba el vehículo
                for item_type, item_pos in vehicle_data['items']:
                    item_class = globals().get(item_type)
                    if item_class is None:
                        continue
                    item = item_class(item_pos)
                    vehicle.load.append(item)
                self.player2.add_vehicle(vehicle)
                self.grid[vehicle.position[0]][vehicle.position[1]] = vehicle
            
            # Recreamos las minas en el tablero
            self.mines = []
            for mine_data in game_state['mines']:
                # Creamos cada mina con su tipo y posición correctos
                mine_class = globals()[mine_data['type']]
                mine = mine_class(mine_data['position'])
                mine.x_radius = mine_data['x_radius']
                mine.y_radius = mine_data['y_radius']
                self.mines.append(mine)
                self.grid[mine.position[0]][mine.position[1]] = mine

            # Recreamos los items sueltos en el mapa (los que no estaban dentro de vehículos)
            for item_data in game_state.get('items', []):
                item_type = item_data.get('type')
                pos = item_data.get('position')
                item_class = globals().get(item_type)
                if item_class is None or pos is None:
                    continue
                obj = item_class(pos)
                x, y = pos
                # Solo colocamos el item si la casilla está vacía (no sobreescribimos vehículos/minas)
                if 0 <= x < self.width and 0 <= y < self.height and self.grid[x][y] is None:
                    self.grid[x][y] = obj

            # Actualizamos las zonas de peligro ahora que minas están cargadas
            self.update_danger_zones()
            
            # Restauramos los puntos de cada jugador
            self.player1.points = game_state['scores']['player1']  # Puntos jugador 1
            self.player2.points = game_state['scores']['player2']  # Puntos jugador 2
            
            return True
        except Exception as e:
            print(f"Error al cargar el juego: {e}")
            return False

    def new_game(self):
        # Inicializa un nuevo tablero y coloca vehículos, minas y items
        self.clear()

        # Setup Player 1 Vehicles
        self.player1.add_vehicle(Truck(self.player1, (0, 2)))
        self.player1.add_vehicle(Truck(self.player1, (0, 7)))
        self.player1.add_vehicle(Jeep(self.player1, (0, 12)))
        self.player1.add_vehicle(Jeep(self.player1, (0, 17)))
        self.player1.add_vehicle(Jeep(self.player1, (0, 22)))
        self.player1.add_vehicle(Car(self.player1, (0, 27)))
        self.player1.add_vehicle(Car(self.player1, (0, 32)))
        self.player1.add_vehicle(Car(self.player1, (0, 37)))
        self.player1.add_vehicle(Motorcycle(self.player1, (0, 42)))
        self.player1.add_vehicle(Motorcycle(self.player1, (0, 47)))
        for vehicle in self.player1.vehicles:
            x, y = vehicle.position
            self.grid[x][y] = vehicle

        # Setup Player 2 Vehicles
        self.player2.add_vehicle(Truck(self.player2, (self.width - 1, 2)))
        self.player2.add_vehicle(Truck(self.player2, (self.width - 1, 7)))
        self.player2.add_vehicle(Jeep(self.player2, (self.width - 1, 12)))
        self.player2.add_vehicle(Jeep(self.player2, (self.width - 1, 17)))
        self.player2.add_vehicle(Jeep(self.player2, (self.width - 1, 22)))
        self.player2.add_vehicle(Car(self.player2, (self.width - 1, 27)))
        self.player2.add_vehicle(Car(self.player2, (self.width - 1, 32)))
        self.player2.add_vehicle(Car(self.player2, (self.width - 1, 37)))
        self.player2.add_vehicle(Motorcycle(self.player2, (self.width - 1, 42)))
        self.player2.add_vehicle(Motorcycle(self.player2, (self.width - 1, 47)))
        for vehicle in self.player2.vehicles:
            x, y = vehicle.position
            self.grid[x][y] = vehicle

        # Setup Mines
        self.mines.append(Mine_O1(self.get_empty_cell(11, 10)))
        self.mines.append(Mine_O2(self.get_empty_cell(6, 5)))
        self.mines.append(Mine_T1(self.get_empty_cell(11)))
        self.mines.append(Mine_T2(self.get_empty_cell(2, 5)))
        self.mines.append(Mine_G1(self.get_empty_cell(8)))
        for mine in self.mines:
            x, y = mine.position
            self.grid[x][y] = mine

        # Update danger zones after placing mines
        self.update_danger_zones()

        # Setup Items
        items = []
        for _ in range(10):
            items.append(Person(self.get_empty_cell()))
        choices = [Weapon, Clothing, Food, Heal]
        for _ in range(50):
            item_class = random.choice(choices)
            items.append(item_class(self.get_empty_cell()))
        for item in items:
            x, y = item.position
            self.grid[x][y] = item
        return

    def update_danger_zones(self):
        # Reset all to False using same indexing as grid (x major, y minor)
        self.danger_zones = [[False for _ in range(self.height)] for _ in range(self.width)]

        for x in range(self.width):
            for y in range(self.height):
                obj = self.grid[x][y]
                if isinstance(obj, Mine):
                    mx, my = obj.position
                    # mark rectangle area covered by the mine
                    for dx in range(-obj.x_radius, obj.x_radius + 1):
                        for dy in range(-obj.y_radius, obj.y_radius + 1):
                            nx = mx + dx
                            ny = my + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                self.danger_zones[nx][ny] = True
                if isinstance(obj, Vehicle):
                    vehicle_x, vehicle_y = obj.position
                    self.danger_zones[vehicle_x][vehicle_y] = True
    
    def next_turn(self, current_turn: int):

        # DEBUG: registrar estado de minas antes de ejecutar el turno
        try:
            mine_positions_before = [m.position for m in self.mines]
            mine_radii_before = [(m.position, getattr(m, 'x_radius', None), getattr(m, 'y_radius', None)) for m in self.mines]
            print(f"[DEBUG] next_turn start: turn={current_turn}, mines_before={len(self.mines)} positions={mine_positions_before} radii={mine_radii_before}")
        except Exception:
            pass

        # Alternador de minas tipo G1: no queremos que ocurra en el turno inicial (0).
        # Aplicamos el toggle cuando el siguiente turno vaya a ser múltiplo de 7,
        # es decir, al avanzar hacia un turno 7,14,21,...
        if (current_turn + 1) % 7 == 0:
            for mine in self.mines:
                if isinstance(mine, Mine_G1):
                    mine.toggle()

        # PLAN PHASE: ask every vehicle to plan its path (does not modify grid)
        vehicles = list(self.player1.vehicles) + list(self.player2.vehicles)
        for v in vehicles:
            try:
                v.plan(self)
            except Exception:
                # fall back to move() if plan not available
                try:
                    v.move(self)
                except Exception:
                    pass

        # COLLECT INTENDED MOVES
        target_map: dict[tuple[int, int], list] = {}
        intent_by_vehicle = {}
        for v in vehicles:
            nxt = None
            try:
                nxt = v.peek_next()
            except Exception:
                nxt = None
            if nxt is not None:
                target_map.setdefault(nxt, []).append(v)
                intent_by_vehicle[v] = nxt

        # RESOLVE CONFLICTS
        for target, vs in list(target_map.items()):
            if len(vs) <= 1:
                continue
            # If policy is allow_crash, let them all move and let post-collision handle it
            if self.collision_policy == 'allow_crash':
                continue

            # prefer_move: pick one vehicle to move (highest capacity), others yield
            winner = max(vs, key=lambda v: getattr(v, 'capacity', 0))
            for v in vs:
                if v is not winner:
                    # make loser abandon planned step this turn
                    v.path = []
                    try:
                        del intent_by_vehicle[v]
                    except Exception:
                        pass

        # EXECUTE PHASE: perform approved moves
        for v, target in list(intent_by_vehicle.items()):
            try:
                v.execute_move(self, target)
            except Exception:
                # fallback to move (backwards compatibility)
                try:
                    v.move(self)
                except Exception:
                    pass

        # Recompute danger zones in case mines moved/teleported
        self.update_danger_zones()

        # DEBUG: registrar estado de minas despues de ejecutar el turno
        try:
            mine_positions_after = [m.position for m in self.mines]
            mine_radii_after = [(m.position, getattr(m, 'x_radius', None), getattr(m, 'y_radius', None)) for m in self.mines]
            print(f"[DEBUG] next_turn end: turn={current_turn}, mines_after={len(self.mines)} positions={mine_positions_after} radii={mine_radii_after}")
        except Exception:
            pass

        # After movement, handle collisions
        self.check_collisions()

        # Unload at base
        for vehicle in list(self.player1.vehicles) + list(self.player2.vehicles):
            vehicle.unload_if_at_base(self)
        return
    
    def check_collisions(self):
        # Build a mapping from positions to vehicles occupying them
        vehicles = list(self.player1.vehicles) + list(self.player2.vehicles)
        pos_map = {}
        for v in vehicles:
            pos_map.setdefault(v.position, []).append(v)

        # Remove vehicles that collided (more than one vehicle in same cell)
        for pos, vs in list(pos_map.items()):
            if len(vs) > 1:
                x, y = pos
                for v in vs:
                    if v in v.team.vehicles:
                        v.team.vehicles.remove(v)
                self.grid[x][y] = None

        # Collect all mines on the grid
        mines = []
        for x in range(self.width):
            for y in range(self.height):
                object = self.grid[x][y]
                try:
                    from classes.Mine import Mine as _Mine
                except Exception:
                    _Mine = None
                if _Mine is not None and isinstance(object, _Mine):
                    mines.append(object)

        # Remove vehicles that are inside a mine radius
        for vehicle in list(self.player1.vehicles) + list(self.player2.vehicles):
            vehicle_x, vehicle_y = vehicle.position
            for mine in mines:
                mine_x, mine_y = mine.position
                if abs(vehicle_x - mine_x) <= mine.x_radius and abs(vehicle_y - mine_y) <= mine.y_radius:
                    try:
                        if vehicle in vehicle.team.vehicles:
                            vehicle.team.vehicles.remove(vehicle)
                    except Exception:
                        pass
                    try:
                        self.grid[vehicle_x][vehicle_y] = None
                    except Exception:
                        pass
                    break