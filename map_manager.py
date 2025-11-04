import random
import pickle
import os
from datetime import datetime
from classes.Mine import Mine, Mine_O1, Mine_O2, Mine_T1, Mine_T2, Mine_G1
from classes.Item import Person, Weapon, Clothing, Food, Heal
from classes.Vehicle import Vehicle, Car, Jeep, Motorcycle, Truck
from classes.Player import Player
from strategies import Strategy

class MapManager:
    def __init__(self, player1_strategy: Strategy, player2_strategy: Strategy, width=50, height=50):
        self.player1 = Player("Player 1", player1_strategy)
        self.player2 = Player("Player 2", player2_strategy)
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(self.height)] for _ in range(self.width)]
        self.mines = []
        self.danger_zones = [[False for _ in range(self.height)] for _ in range(self.width)]
        # When 'allow_crash', multiple vehicles may move into the same cell
        # and will be removed afterward by `check_collisions`.
        # This makes collisions deterministic/simple: no avoidance policy.
        self.collision_policy = 'allow_crash'
                
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
        """Save a serializable snapshot of the game state.

        We avoid pickling pygame Surfaces by converting objects to simple
        dictionaries that contain only primitive types (strings, numbers,
        tuples, lists). Returns the filename written.
        """
        def serialize_item(item):
            return {
                'type': item.__class__.__name__,
                'position': item.position,
                'value': getattr(item, 'value', None)
            }

        def serialize_vehicle(v):
            return {
                'type': v.__class__.__name__,
                'position': v.position,
                'capacity': v.capacity,
                'only_persons': v.only_persons,
                'load': [serialize_item(it) for it in getattr(v, 'load', [])]
            }

        def serialize_mine(m):
            return {
                'type': m.__class__.__name__,
                'position': m.position,
                'x_radius': getattr(m, 'x_radius', None),
                'y_radius': getattr(m, 'y_radius', None)
            }

        game_state = {
            'turn': turn_number,
            'width': self.width,
            'height': self.height,
            'danger_zones': self.danger_zones,
            'player1': {
                'points': getattr(self.player1, 'points', 0),
                'vehicles': [serialize_vehicle(v) for v in self.player1.vehicles]
            },
            'player2': {
                'points': getattr(self.player2, 'points', 0),
                'vehicles': [serialize_vehicle(v) for v in self.player2.vehicles]
            },
            'mines': [serialize_mine(m) for m in self.mines],
            'items': []
        }

        # collect standalone items from the grid (not part of vehicles or mines)
        for x in range(self.width):
            for y in range(self.height):
                obj = self.grid[x][y]
                # skip vehicles and mines
                if isinstance(obj, Vehicle) or isinstance(obj, Mine):
                    continue
                if obj is not None:
                    # assume it's an Item
                    try:
                        from classes.Item import Item as _Item
                    except Exception:
                        _Item = None
                    if _Item is not None and isinstance(obj, _Item):
                        game_state['items'].append(serialize_item(obj))

        # ensure saved_games directory
        if not os.path.exists('saved_games'):
            os.makedirs('saved_games')

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saved_games/game_{timestamp}_turn_{turn_number}.pkl"

        with open(filename, 'wb') as f:
            pickle.dump(game_state, f)

        return filename

    def load_game(self, filename: str, turn: int):
        """Load a previously saved game_state created by save_game.

        This rebuilds mines, items and vehicles from the serialized data.
        """
        try:
            with open(filename, 'rb') as f:
                game_state = pickle.load(f)
        except Exception as e:
            print(f"Error al abrir el archivo de guardado: {e}")
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

        if current_turn % 7 == 0:
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
                print(f"Collision at {pos}, removed {len(vs)} vehicles.")
                print(f"Vehicles involved: {[str(v.__class__.__name__)+" from "+v.team.name for v in vs]}")

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