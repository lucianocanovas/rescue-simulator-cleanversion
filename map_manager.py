import random
import pickle      # Biblioteca para serializar/guardar objetos Python
import os         # Para operaciones con archivos y directorios
from datetime import datetime  # Para agregar timestamp a los archivos guardados
from classes.Mine import Mine, Mine_O1, Mine_O2, Mine_T1, Mine_T2, Mine_G1
from classes.Item import Person, Weapon, Clothing, Food, Heal
from classes.Vehicle import Car, Jeep, Motorcycle, Truck
from classes.Player import Player
from strategies import Strategy

class MapManager:
    def __init__(self, player1_strategy: Strategy, player2_strategy: Strategy, width=50, height=50):
        self.player1 = Player(player1_strategy)
        self.player2 = Player(player2_strategy)
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(self.height)] for _ in range(self.width)]
        self.danger_zones = [[False for _ in range(self.height)] for _ in range(self.width)]
        # collision policy: 'prefer_move' picks one vehicle to move on conflicts
        # 'allow_crash' lets all vehicles move and collisions are resolved after
        self.collision_policy = 'prefer_move'
                
    def get_empty_cell(self, margin_x=1, margin_y=0):
        x = random.randint(margin_x, self.width - 1 - margin_x)
        y = random.randint(margin_y, self.height - 1 - margin_y)
        while self.grid[x][y] is not None:
            x = random.randint(margin_x, self.width - 1 - margin_x)
            y = random.randint(margin_y, self.height - 1 - margin_y)
        return (x, y)

    def clear(self):
        for x in range(self.width):
            for y in range(self.height):
                self.grid[x][y] = None
        return
    
    def save_game(self, turn_number):
        # Creamos un diccionario con todo el estado del juego
        game_state = {
            'turn': turn_number,            # Número del turno actual
            'grid': self.grid,              # Estado actual del tablero
            'danger_zones': self.danger_zones,  # Zonas de peligro actuales
            'player1': self.player1,        # Estado del jugador 1 (vehículos, estrategia, etc)
            'player2': self.player2,        # Estado del jugador 2
            'width': self.width,            # Ancho del tablero
            'height': self.height           # Alto del tablero
        }
        
        # Creamos la carpeta saved_games si no existe
        if not os.path.exists('saved_games'):
            os.makedirs('saved_games')
            
        # Generamos el nombre del archivo con fecha y hora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Formato: AñoMesDía_HoraMinutoSegundo
        filename = f"saved_games/game_{timestamp}_turn_{turn_number}.pkl"
        
        # Guardamos el estado del juego usando pickle
        with open(filename, 'wb') as f:  # 'wb' = write binary
            pickle.dump(game_state, f)    # Serializamos el estado del juego
        
        return filename

    def load_game(self, filename: str, turn: int):
        self.clear()  # Limpiamos el estado actual del juego
        try:
            # Abrimos y cargamos el archivo guardado
            with open(filename, 'rb') as f:  # 'rb' = read binary
                game_state = pickle.load(f)  # Deserializamos el estado del juego
                
            # Restauramos cada componente del estado del juego
            self.grid = game_state['grid']           # Restauramos el tablero
            self.danger_zones = game_state['danger_zones']  # Restauramos zonas de peligro
            self.player1 = game_state['player1']     # Restauramos jugador 1
            self.player2 = game_state['player2']     # Restauramos jugador 2
            self.width = game_state['width']         # Restauramos dimensiones
            self.height = game_state['height']
            
            return True
        except Exception as e:
            print(f"Error al cargar el juego: {e}")
            return False

    def new_game(self):
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
        mines = []
        mines.append(Mine_O1(self.get_empty_cell(11, 10)))
        mines.append(Mine_O2(self.get_empty_cell(6, 5)))
        mines.append(Mine_T1(self.get_empty_cell(11)))
        mines.append(Mine_T2(self.get_empty_cell(2, 5)))
        mines.append(Mine_G1(self.get_empty_cell(8)))
        for mine in mines:
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
    
    def next_turn(self):
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

        # After movement, handle collisions and mine triggers
        self.check_collisions()
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
                    try:
                        if v in v.team.vehicles:
                            v.team.vehicles.remove(v)
                    except Exception:
                        pass
                # clear grid cell
                try:
                    self.grid[x][y] = None
                except Exception:
                    pass

        # Collect all mines currently on the grid
        mines = []
        for x in range(self.width):
            for y in range(self.height):
                obj = self.grid[x][y]
                try:
                    from classes.Mine import Mine as _Mine
                except Exception:
                    _Mine = None
                if _Mine is not None and isinstance(obj, _Mine):
                    mines.append(obj)

        # Remove vehicles that are inside any mine radius
        for v in list(self.player1.vehicles) + list(self.player2.vehicles):
            vx, vy = v.position
            for mine in mines:
                mx, my = mine.position
                if abs(vx - mx) <= mine.x_radius and abs(vy - my) <= mine.y_radius:
                    try:
                        if v in v.team.vehicles:
                            v.team.vehicles.remove(v)
                    except Exception:
                        pass
                    try:
                        self.grid[vx][vy] = None
                    except Exception:
                        pass
                    break