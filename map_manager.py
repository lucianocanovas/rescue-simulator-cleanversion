import random
import pickle
import os
import csv
from datetime import datetime
from classes.Mine import Mine, Mine_O1, Mine_O2, Mine_T1, Mine_T2, Mine_G1
from classes.Item import Item, Person, Weapon, Clothing, Food, Heal
from classes.Vehicle import Vehicle, Car, Jeep, Motorcycle, Truck
from classes.Player import Player
from strategies import Strategy
from pathfinding import find_nearest

class MapManager:
    def __init__(self, player1_strategy: Strategy, player2_strategy: Strategy, width=50, height=50):
        self.player1 = Player("Player 1", player1_strategy)
        self.player2 = Player("Player 2", player2_strategy)
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(self.height)] for _ in range(self.width)]
        self.mines = []
        self.danger_zones = [[False for _ in range(self.height)] for _ in range(self.width)]
        self.current_game_folder = None
        self.explosions = []
        self.current_turn = 0
        
        # Game statistics tracking
        self.game_stats = {
            'start_time': None,
            'end_time': None,
            'total_turns': 0,
            'winner': None,
            'end_reason': None,
            'player1_stats': {
                'final_points': 0,
                'items_collected': {'Person': 0, 'Weapon': 0, 'Clothing': 0, 'Food': 0, 'Heal': 0},
                'total_items_collected': 0,
                'vehicles_lost': 0,
                'vehicles_survived': 0,
                'collisions': 0,
                'mine_deaths': 0,
                'strategies_used': {},
                'strategy_efficiency': {}
            },
            'player2_stats': {
                'final_points': 0,
                'items_collected': {'Person': 0, 'Weapon': 0, 'Clothing': 0, 'Food': 0, 'Heal': 0},
                'total_items_collected': 0,
                'vehicles_lost': 0,
                'vehicles_survived': 0,
                'collisions': 0,
                'mine_deaths': 0,
                'strategies_used': {},
                'strategy_efficiency': {}
            }
        }
        
        # Track initial vehicles for statistics
        self.initial_vehicles = {'player1': [], 'player2': []}
                
    def get_empty_cell(self, margin_x=1, margin_y=0):
        pos_x = random.randint(margin_x, self.width - 1 - margin_x)
        pos_y = random.randint(margin_y, self.height - 1 - margin_y)
        while self.grid[pos_x][pos_y] is not None:
            pos_x = random.randint(margin_x, self.width - 1 - margin_x)
            pos_y = random.randint(margin_y, self.height - 1 - margin_y)
        return (pos_x, pos_y)

    def clear(self):
        for x in range(self.width):
            for y in range(self.height):
                self.grid[x][y] = None
        
        self.mines = []
        self.danger_zones = [[False for _ in range(self.height)] for _ in range(self.width)]
        
        try:
            self.player1.vehicles = []
        except Exception:
            pass
        try:
            self.player2.vehicles = []
        except Exception:
            pass
    
    def _get_next_game_folder(self):
        base_directory = "saved_games"
        if not os.path.exists(base_directory):
            os.makedirs(base_directory)
        
        saved_games = []
        try:
            saved_games = [d for d in os.listdir(base_directory) if d.startswith('Game_')]
        except:
            pass
            
        if not saved_games:
            new_path = os.path.join(base_directory, "Game_1")
            os.makedirs(new_path)
            return new_path
        
        game_numbers = [int(game.split('_')[1]) for game in saved_games]
        next_number = max(game_numbers) + 1
        new_path = os.path.join(base_directory, f"Game_{next_number}")
        os.makedirs(new_path)
        return new_path

    def save_game(self, turn_number):
        def serialize_item(item):
            return {
                'type': item.__class__.__name__,
                'position': item.position,
                'value': getattr(item, 'value', None)
            }

        def serialize_vehicle(vehicle):
            return {
                'type': vehicle.__class__.__name__,
                'position': vehicle.position,
                'capacity': vehicle.capacity,
                'only_persons': vehicle.only_persons,
                'path': list(getattr(vehicle, 'path', [])),
                'state': getattr(vehicle, 'state', 'idle'),
                'load': [serialize_item(it) for it in getattr(vehicle, 'load', [])],
                'under_item': serialize_item(getattr(vehicle, 'under_item', None)) if getattr(vehicle, 'under_item', None) is not None else None
            }

        def serialize_mine(mine):
            return {
                'type': mine.__class__.__name__,
                'position': mine.position,
                'x_radius': getattr(mine, 'x_radius', None),
                'y_radius': getattr(mine, 'y_radius', None)
            }

        game_state = {
            'turn': turn_number,
            'width': self.width,
            'height': self.height,
            'danger_zones': self.danger_zones,
            'explosions': [ {'pos': explosion.get('pos'), 'ttl': int(explosion.get('ttl',0))} for explosion in getattr(self, 'explosions', []) ],
            'player1': {
                'points': getattr(self.player1, 'points', 0),
                'vehicles': [serialize_vehicle(vehicle) for vehicle in self.player1.vehicles]
            },
            'player2': {
                'points': getattr(self.player2, 'points', 0),
                'vehicles': [serialize_vehicle(vehicle) for vehicle in self.player2.vehicles]
            },
            'mines': [serialize_mine(mine) for mine in self.mines],
            'items': []
        }

        # Collect standalone items from the grid (not part of vehicles or mines)
        for x in range(self.width):
            for y in range(self.height):
                grid_object = self.grid[x][y]
                if isinstance(grid_object, Vehicle) or isinstance(grid_object, Mine):
                    continue
                if grid_object is not None:
                    try:
                        from classes.Item import Item as _Item
                    except Exception:
                        _Item = None
                    if _Item is not None and isinstance(grid_object, _Item):
                        game_state['items'].append(serialize_item(grid_object))

        if self.current_game_folder is None:
            self.current_game_folder = self._get_next_game_folder()
        if not os.path.exists(self.current_game_folder):
            os.makedirs(self.current_game_folder, exist_ok=True)

        filename = os.path.join(self.current_game_folder, f"turn_{turn_number}.pkl")
        with open(filename, 'wb') as file:
            pickle.dump(game_state, file)

        return filename

    def load_game(self, filename: str, turn: int):
        try:
            with open(filename, 'rb') as file:
                game_state = pickle.load(file)
        except Exception as error:
            print(f"❌ - ERROR LOADING SAVED GAME FILE: {error}")
            return False

        try:
            self.current_game_folder = os.path.dirname(os.path.abspath(filename))
            
            self.width = game_state.get('width', self.width)
            self.height = game_state.get('height', self.height)

            self.clear()
            self.danger_zones = game_state.get('danger_zones', self.danger_zones)

            def create_item(item_data):
                item_type = item_data.get('type')
                position = item_data.get('position')
                if item_type == 'Person':
                    return Person(position)
                if item_type == 'Weapon':
                    return Weapon(position)
                if item_type == 'Clothing':
                    return Clothing(position)
                if item_type == 'Food':
                    return Food(position)
                if item_type == 'Heal':
                    return Heal(position)
                return None

            def create_vehicle(vehicle_data, team):
                vehicle_type = vehicle_data.get('type')
                position = tuple(vehicle_data.get('position', (0, 0)))
                vehicle_class = None
                if vehicle_type == 'Truck':
                    vehicle_class = Truck
                elif vehicle_type == 'Jeep':
                    vehicle_class = Jeep
                elif vehicle_type == 'Car':
                    vehicle_class = Car
                elif vehicle_type == 'Motorcycle':
                    vehicle_class = Motorcycle
                if vehicle_class is None:
                    return None
                vehicle = vehicle_class(team, position)
                vehicle.load = []
                for item in vehicle_data.get('load', []):
                    item_object = create_item(item)
                    if item_object is not None:
                        vehicle.load.append(item_object)
                try:
                    vehicle.path = [tuple(point) for point in vehicle_data.get('path', [])]
                except Exception:
                    vehicle.path = []
                vehicle.state = vehicle_data.get('state', 'idle')
                try:
                    under_serialized = vehicle_data.get('under_item')
                    if under_serialized:
                        under_item = create_item(under_serialized)
                        if under_item is not None:
                            vehicle.under_item = under_item
                except Exception:
                    vehicle.under_item = None
                return vehicle

            mines_data = game_state.get('mines', [])
            for mine_data in mines_data:
                mine_type = mine_data.get('type')
                mine_position = tuple(mine_data.get('position', (0, 0)))
                mine_object = None
                if mine_type == 'Mine_O1':
                    mine_object = Mine_O1(mine_position)
                elif mine_type == 'Mine_O2':
                    mine_object = Mine_O2(mine_position)
                elif mine_type == 'Mine_T1':
                    mine_object = Mine_T1(mine_position)
                elif mine_type == 'Mine_T2':
                    mine_object = Mine_T2(mine_position)
                elif mine_type == 'Mine_G1':
                    mine_object = Mine_G1(mine_position)
                if mine_object is not None:
                    try:
                        saved_x_radius = mine_data.get('x_radius', None)
                        saved_y_radius = mine_data.get('y_radius', None)
                        if saved_x_radius is not None:
                            mine_object.x_radius = int(saved_x_radius)
                        if saved_y_radius is not None:
                            mine_object.y_radius = int(saved_y_radius)
                    except Exception:
                        pass
                    self.mines.append(mine_object)
                    x, y = mine_object.position
                    self.grid[x][y] = mine_object

            for item_data in game_state.get('items', []):
                item_object = create_item(item_data)
                if item_object is not None:
                    x, y = item_object.position
                    self.grid[x][y] = item_object

            try:
                self.explosions = []
                for explosion_data in game_state.get('explosions', []):
                    explosion_position = tuple(explosion_data.get('pos')) if explosion_data.get('pos') is not None else None
                    time_to_live = int(explosion_data.get('ttl', 0))
                    if explosion_position is not None and time_to_live > 0:
                        self.explosions.append({'pos': explosion_position, 'ttl': time_to_live})
            except Exception:
                self.explosions = []

            try:
                self.player1.points = game_state.get('player1', {}).get('points', 0)
                self.player2.points = game_state.get('player2', {}).get('points', 0)
            except Exception:
                pass

            self.player1.vehicles = []
            self.player2.vehicles = []
            for vehicle_data in game_state.get('player1', {}).get('vehicles', []):
                vehicle = create_vehicle(vehicle_data, self.player1)
                if vehicle is not None:
                    self.player1.add_vehicle(vehicle)
                    x, y = vehicle.position
                    self.grid[x][y] = vehicle
            for vehicle_data in game_state.get('player2', {}).get('vehicles', []):
                vehicle = create_vehicle(vehicle_data, self.player2)
                if vehicle is not None:
                    self.player2.add_vehicle(vehicle)
                    x, y = vehicle.position
                    self.grid[x][y] = vehicle

            self.update_danger_zones()

            return True
        except Exception as error:
            print(f"❌ - ERROR RESTORING GAME STATE FROM FILE: {error}")
            return False

    def new_game(self):
        self.clear()
        
        self.game_stats['start_time'] = datetime.now()
        self.current_turn = 0
        
        if self.current_game_folder is None:
            self.current_game_folder = self._get_next_game_folder()
        
        vehicles_player1 = []
        vehicles_player2 = []
        try:
            import json
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            with open(config_path, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
            
            from strategies import PickNearest, Kamikaze, Escort, Invader, FullSafe
            strategy_map = {
                'PickNearest': PickNearest,
                'Kamikaze': Kamikaze,
                'Escort': Escort,
                'Invader': Invader,
                'FullSafe': FullSafe
            }
            
            vehicle_type_map = {
                'Truck': Truck,
                'Car': Car,
                'Jeep': Jeep,
                'Motorcycle': Motorcycle
            }
            
            players_config = config.get('players', {})
            
            player1_config = players_config.get('player1', {}).get('vehicles', [])
            for vehicle_config in player1_config:
                vehicle_type = vehicle_config.get('type', 'Car')
                strategy_name = vehicle_config.get('strategy', 'PickNearest')
                y_position = vehicle_config.get('y_position', 0)
                
                vehicle_class = vehicle_type_map.get(vehicle_type, Car)
                strategy_class = strategy_map.get(strategy_name, PickNearest)
                strategy = strategy_class()
                
                vehicles_player1.append({
                    'class': vehicle_class,
                    'position': (0, y_position),
                    'strategy': strategy
                })
            
            player2_config = players_config.get('player2', {}).get('vehicles', [])
            for vehicle_config in player2_config:
                vehicle_type = vehicle_config.get('type', 'Car')
                strategy_name = vehicle_config.get('strategy', 'PickNearest')
                y_position = vehicle_config.get('y_position', 0)
                
                vehicle_class = vehicle_type_map.get(vehicle_type, Car)
                strategy_class = strategy_map.get(strategy_name, PickNearest)
                strategy = strategy_class()
                
                vehicles_player2.append({
                    'class': vehicle_class,
                    'position': (self.width - 1, y_position),
                    'strategy': strategy
                })
                
        except Exception as error:
            print(f"❌ - ERROR LOADING CONFIGURATION FILE: {error}, USING DEFAULT VEHICLE SETUP")
            from strategies import PickNearest
            default_vehicles = [
                (Truck, 2), (Car, 7), (Jeep, 12), (Motorcycle, 17), (Jeep, 22),
                (Car, 27), (Truck, 32), (Car, 37), (Motorcycle, 42), (Jeep, 47)
            ]
            for vehicle_class, y_position in default_vehicles:
                vehicles_player1.append({
                    'class': vehicle_class,
                    'position': (0, y_position),
                    'strategy': PickNearest()
                })
                vehicles_player2.append({
                    'class': vehicle_class,
                    'position': (self.width - 1, y_position),
                    'strategy': PickNearest()
                })
        
        if not vehicles_player1:
            from strategies import PickNearest
            vehicles_player1.append({
                'class': Car,
                'position': (0, self.height // 2),
                'strategy': PickNearest()
            })
        if not vehicles_player2:
            from strategies import PickNearest
            vehicles_player2.append({
                'class': Car,
                'position': (self.width - 1, self.height // 2),
                'strategy': PickNearest()
            })

        for vehicle_data in vehicles_player1:
            vehicle = vehicle_data['class'](
                self.player1, 
                vehicle_data['position'], 
                strategy=vehicle_data['strategy']
            )
            self.player1.add_vehicle(vehicle)
            x, y = vehicle.position
            self.grid[x][y] = vehicle

        for vehicle_data in vehicles_player2:
            vehicle = vehicle_data['class'](
                self.player2, 
                vehicle_data['position'], 
                strategy=vehicle_data['strategy']
            )
            self.player2.add_vehicle(vehicle)
            x, y = vehicle.position
            self.grid[x][y] = vehicle

        self.mines.append(Mine_O1(self.get_empty_cell(11, 10)))
        self.mines.append(Mine_O2(self.get_empty_cell(6, 5)))
        self.mines.append(Mine_T1(self.get_empty_cell(11)))
        self.mines.append(Mine_T2(self.get_empty_cell(2, 5)))
        self.mines.append(Mine_G1(self.get_empty_cell(8)))
        for mine in self.mines:
            x, y = mine.position
            self.grid[x][y] = mine

        self.update_danger_zones()

        items = []
        for _ in range(10):
            items.append(Person(self.get_empty_cell()))
        item_choices = [Weapon, Clothing, Food, Heal]
        for _ in range(50):
            item_class = random.choice(item_choices)
            items.append(item_class(self.get_empty_cell()))
        for item in items:
            x, y = item.position
            self.grid[x][y] = item
        
        self.initial_vehicles = {'player1': [], 'player2': []}
        for vehicle in self.player1.vehicles:
            strategy_name = vehicle.strategy.__class__.__name__ if hasattr(vehicle, 'strategy') else 'Unknown'
            self.initial_vehicles['player1'].append({
                'type': vehicle.__class__.__name__,
                'strategy': strategy_name
            })
            self.game_stats['player1_stats']['strategies_used'][strategy_name] = \
                self.game_stats['player1_stats']['strategies_used'].get(strategy_name, 0) + 1
        
        for vehicle in self.player2.vehicles:
            strategy_name = vehicle.strategy.__class__.__name__ if hasattr(vehicle, 'strategy') else 'Unknown'
            self.initial_vehicles['player2'].append({
                'type': vehicle.__class__.__name__,
                'strategy': strategy_name
            })
            self.game_stats['player2_stats']['strategies_used'][strategy_name] = \
                self.game_stats['player2_stats']['strategies_used'].get(strategy_name, 0) + 1
        
        return

    def update_danger_zones(self):
        self.danger_zones = [[False for _ in range(self.height)] for _ in range(self.width)]

        for x in range(self.width):
            for y in range(self.height):
                grid_object = self.grid[x][y]
                if isinstance(grid_object, Mine):
                    mine_x, mine_y = grid_object.position
                    for delta_x in range(-grid_object.x_radius, grid_object.x_radius + 1):
                        for delta_y in range(-grid_object.y_radius, grid_object.y_radius + 1):
                            new_x = mine_x + delta_x
                            new_y = mine_y + delta_y
                            if 0 <= new_x < self.width and 0 <= new_y < self.height:
                                self.danger_zones[new_x][new_y] = True
                if isinstance(grid_object, Vehicle):
                    vehicle_x, vehicle_y = grid_object.position
                    self.danger_zones[vehicle_x][vehicle_y] = True
    
    def next_turn(self, current_turn: int):
        self.current_turn = current_turn

        if (current_turn + 1) % 5 == 0:
            for mine in self.mines:
                if isinstance(mine, Mine_G1):
                    mine.toggle()

        vehicles = list(self.player1.vehicles) + list(self.player2.vehicles)
        for vehicle in vehicles:
            try:
                vehicle.plan(self)
            except Exception:
                try:
                    vehicle.move(self)
                except Exception:
                    pass

        target_map: dict[tuple[int, int], list] = {}
        intent_by_vehicle = {}
        for vehicle in vehicles:
            next_position = None
            try:
                next_position = vehicle.peek_next()
            except Exception:
                next_position = None
            if next_position is not None:
                target_map.setdefault(next_position, []).append(vehicle)
                intent_by_vehicle[vehicle] = next_position

        for vehicle, target in list(intent_by_vehicle.items()):
            try:
                vehicle.execute_move(self, target)
            except Exception:
                try:
                    vehicle.move(self)
                except Exception:
                    pass

        self.update_danger_zones()
        self.check_collisions()

        try:
            for explosion in list(self.explosions):
                try:
                    explosion['ttl'] = int(explosion.get('ttl', 0)) - 1
                except Exception:
                    explosion['ttl'] = 0
            self.explosions = [explosion for explosion in self.explosions if explosion.get('ttl', 0) > 0]
        except Exception:
            pass

        for vehicle in list(self.player1.vehicles) + list(self.player2.vehicles):
            vehicle.unload_if_at_base(self)
        return
    
    def check_collisions(self):
        # Build a mapping from positions to vehicles occupying them
        vehicles = list(self.player1.vehicles) + list(self.player2.vehicles)
        position_map = {}
        for vehicle in vehicles:
            position_map.setdefault(vehicle.position, []).append(vehicle)

        # Remove vehicles that collided (more than one vehicle in same cell)
        for position, vehicles_at_position in list(position_map.items()):
            if len(vehicles_at_position) > 1:
                cell_x, cell_y = position
                # Register a visual explosion when there's a collision (3 turns)
                try:
                    self.explosions.append({'pos': (cell_x, cell_y), 'ttl': 3})
                except Exception:
                    pass
                # Track whether any vehicle restored an item to this cell
                restored_item = False
                for vehicle in vehicles_at_position:
                    # Register collision statistics
                    player_key = 'player1_stats' if vehicle.team == self.player1 else 'player2_stats'
                    self.game_stats[player_key]['collisions'] += 1
                    self.game_stats[player_key]['vehicles_lost'] += 1
                    
                    # If a vehicle had an item stored under it, restore it to the grid
                    try:
                        if getattr(vehicle, 'under_item', None) is not None:
                            under_item = vehicle.under_item
                            try:
                                under_item.position = (cell_x, cell_y)
                                self.grid[cell_x][cell_y] = under_item
                                restored_item = True
                            except Exception:
                                pass
                            vehicle.under_item = None
                    except Exception:
                        pass
                    # Remove vehicle from its team's list
                    try:
                        if vehicle in vehicle.team.vehicles:
                            vehicle.team.vehicles.remove(vehicle)
                    except Exception:
                        pass
                # If no item was restored above, make sure the grid cell is cleared
                if not restored_item:
                    try:
                        self.grid[cell_x][cell_y] = None
                    except Exception:
                        pass
                print(f"💥 - COLLISION ({position})")
                vehicle_details = [f"{vehicle.__class__.__name__.upper()} - TEAM: {vehicle.team.name.upper()}" for vehicle in vehicles_at_position]
                print(f"💥 - COLLISION VEHICLES: {vehicle_details}")

        # Collect all mines on the grid
        mines = []
        for x in range(self.width):
            for y in range(self.height):
                grid_object = self.grid[x][y]
                try:
                    from classes.Mine import Mine as _Mine
                except Exception:
                    _Mine = None
                if _Mine is not None and isinstance(grid_object, _Mine):
                    mines.append(grid_object)

        # Remove vehicles that are inside a mine radius
        for vehicle in list(self.player1.vehicles) + list(self.player2.vehicles):
            vehicle_x, vehicle_y = vehicle.position
            for mine in mines:
                mine_x, mine_y = mine.position
                if abs(vehicle_x - mine_x) <= mine.x_radius and abs(vehicle_y - mine_y) <= mine.y_radius:
                    # Register mine death statistics
                    player_key = 'player1_stats' if vehicle.team == self.player1 else 'player2_stats'
                    self.game_stats[player_key]['mine_deaths'] += 1
                    self.game_stats[player_key]['vehicles_lost'] += 1
                    
                    # Restore any item that was under the vehicle
                    restored_item = False
                    try:
                        if getattr(vehicle, 'under_item', None) is not None:
                            under_item = vehicle.under_item
                            try:
                                under_item.position = (vehicle_x, vehicle_y)
                                self.grid[vehicle_x][vehicle_y] = under_item
                                restored_item = True
                            except Exception:
                                restored_item = False
                            vehicle.under_item = None
                    except Exception:
                        restored_item = False

                    # Register a visual explosion for mine destruction (3 turns)
                    try:
                        self.explosions.append({'pos': (vehicle_x, vehicle_y), 'ttl': 3})
                    except Exception:
                        pass

                    # Remove vehicle from its team
                    try:
                        if vehicle in vehicle.team.vehicles:
                            vehicle.team.vehicles.remove(vehicle)
                    except Exception:
                        pass

                    # If no item was restored, clear the grid cell
                    try:
                        if not restored_item:
                            self.grid[vehicle_x][vehicle_y] = None
                    except Exception:
                        pass
                    break

    def is_game_over(self):
        # 1) No vehicles
        total_vehicles = len(getattr(self.player1, 'vehicles', [])) + len(getattr(self.player2, 'vehicles', []))
        if total_vehicles == 0:
            return True, 'no_vehicles'

        # 2) No items (on grid or inside vehicles or stored under vehicles)
        items_on_grid = []
        for x in range(self.width):
            for y in range(self.height):
                grid_object = self.grid[x][y]
                try:
                    if Item is not None and isinstance(grid_object, Item):
                        items_on_grid.append((x, y))
                except Exception:
                    pass

        items_in_vehicles = 0
        vehicles_with_load = []
        vehicles = list(getattr(self.player1, 'vehicles', [])) + list(getattr(self.player2, 'vehicles', []))
        for vehicle in vehicles:
            try:
                vehicle_load = len(getattr(vehicle, 'load', []))
                items_in_vehicles += vehicle_load
                if vehicle_load > 0:
                    vehicles_with_load.append(vehicle)
            except Exception:
                pass
            try:
                if getattr(vehicle, 'under_item', None) is not None:
                    items_in_vehicles += 1
            except Exception:
                pass

        if (len(items_on_grid) + items_in_vehicles) == 0:
            return True, 'no_items'

        # 3) Items exist on the map but no available vehicle can reach any of them
        # If there are vehicles with items loaded, the game must continue
        if not items_on_grid:
            # If no items on grid but vehicles have cargo, game continues
            if vehicles_with_load:
                return False, None
            # If no items on grid and no vehicles with cargo, game ends
            return True, 'no_items'

        # Check if any vehicle can reach items on the grid
        for vehicle in vehicles:
            try:
                # Skip vehicles that are full
                if len(getattr(vehicle, 'load', [])) >= getattr(vehicle, 'capacity', 0):
                    continue
                # Choose pathfinder according to vehicle's capabilities
                if find_nearest is None:
                    continue
                only_persons = getattr(vehicle, 'only_persons', False)
                exclude_persons = getattr(vehicle, 'exclude_persons', False)
                path = find_nearest(self.grid, vehicle.position, self.danger_zones, 
                                  only_persons=only_persons, exclude_persons=exclude_persons)
                if path is not None:
                    # At least one vehicle can reach an on-grid item => not over
                    return False, None
            except Exception:
                continue

        # No vehicle can reach any on-grid item
        # BUT: if there are vehicles with items loaded, they need to deliver them first
        if vehicles_with_load:
            return False, None
        
        # No reachable items AND no vehicles with cargo
        return True, 'no_reachable_items'
    
    def generate_game_stats_csv(self, end_reason: str):
        if self.current_game_folder is None:
            print("❌ - ERROR: No active game folder to save statistics")
            return
        
        # Update final statistics
        self.game_stats['end_time'] = datetime.now()
        self.game_stats['total_turns'] = self.current_turn
        self.game_stats['end_reason'] = end_reason
        
        # Determine winner
        player1_points = self.player1.points
        player2_points = self.player2.points
        if player1_points > player2_points:
            self.game_stats['winner'] = 'Player 1'
        elif player2_points > player1_points:
            self.game_stats['winner'] = 'Player 2'
        else:
            self.game_stats['winner'] = 'Tie'
        
        # Update final points statistics
        self.game_stats['player1_stats']['final_points'] = player1_points
        self.game_stats['player2_stats']['final_points'] = player2_points
        
        # Update collected items statistics
        for item_type in self.player1.items_collected:
            self.game_stats['player1_stats']['items_collected'][item_type] = \
                self.player1.items_collected[item_type]
        for item_type in self.player2.items_collected:
            self.game_stats['player2_stats']['items_collected'][item_type] = \
                self.player2.items_collected[item_type]
        
        # Calculate total collected items
        self.game_stats['player1_stats']['total_items_collected'] = \
            sum(self.player1.items_collected.values())
        self.game_stats['player2_stats']['total_items_collected'] = \
            sum(self.player2.items_collected.values())
        
        # Calculate surviving vehicles
        self.game_stats['player1_stats']['vehicles_survived'] = len(self.player1.vehicles)
        self.game_stats['player2_stats']['vehicles_survived'] = len(self.player2.vehicles)
        
        # Calculate efficiency by strategy
        self._calculate_strategy_efficiency()
        
        # Generate CSV file
        csv_filename = os.path.join(self.current_game_folder, 'game_statistics.csv')
        
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # General information
                writer.writerow(['=== GENERAL INFORMATION ==='])
                writer.writerow(['Game start', self.game_stats['start_time']])
                writer.writerow(['Game end', self.game_stats['end_time']])
                duration = self.game_stats['end_time'] - self.game_stats['start_time']
                writer.writerow(['Duration', str(duration)])
                writer.writerow(['Total turns', self.game_stats['total_turns']])
                writer.writerow(['End reason', end_reason])
                writer.writerow(['Winner', self.game_stats['winner']])
                writer.writerow([])
                
                # Final score
                writer.writerow(['=== FINAL SCORE ==='])
                writer.writerow(['Player 1', player1_points])
                writer.writerow(['Player 2', player2_points])
                writer.writerow(['Difference', abs(player1_points - player2_points)])
                writer.writerow([])
                
                # Statistics per player
                for player_name, player_key in [('Player 1', 'player1_stats'), ('Player 2', 'player2_stats')]:
                    stats = self.game_stats[player_key]
                    writer.writerow([f'=== {player_name.upper()} STATISTICS ==='])
                    writer.writerow(['Final points', stats['final_points']])
                    writer.writerow(['Total items collected', stats['total_items_collected']])
                    writer.writerow(['Vehicles lost', stats['vehicles_lost']])
                    writer.writerow(['Vehicles survived', stats['vehicles_survived']])
                    writer.writerow(['Collision deaths', stats['collisions']])
                    writer.writerow(['Mine deaths', stats['mine_deaths']])
                    writer.writerow([])
                    
                    # Items collected by type
                    writer.writerow([f'Items collected by type - {player_name}:'])
                    writer.writerow(['Type', 'Count'])
                    for item_type, count in stats['items_collected'].items():
                        writer.writerow([item_type, count])
                    writer.writerow([])
                
                # Strategy efficiency (comparison)
                writer.writerow(['=== STRATEGY EFFICIENCY ==='])
                writer.writerow(['Strategy', 'Player 1 - Items/Vehicle', 'Player 2 - Items/Vehicle', 'Best'])
                
                all_strategies = set(
                    list(self.game_stats['player1_stats']['strategy_efficiency'].keys()) +
                    list(self.game_stats['player2_stats']['strategy_efficiency'].keys())
                )
                
                for strategy in sorted(all_strategies):
                    player1_efficiency = self.game_stats['player1_stats']['strategy_efficiency'].get(strategy, 0)
                    player2_efficiency = self.game_stats['player2_stats']['strategy_efficiency'].get(strategy, 0)
                    
                    if player1_efficiency > player2_efficiency:
                        better = 'Player 1'
                    elif player2_efficiency > player1_efficiency:
                        better = 'Player 2'
                    else:
                        better = 'Tie'
                    
                    writer.writerow([strategy, f'{player1_efficiency:.2f}', f'{player2_efficiency:.2f}', better])
                writer.writerow([])
                
                # Ranking of strategies by average efficiency
                writer.writerow(['=== STRATEGY RANKING (BY AVERAGE EFFICIENCY) ==='])
                writer.writerow(['Rank', 'Strategy', 'Average Efficiency', 'Player'])
                
                strategy_rankings = []
                for strategy in all_strategies:
                    player1_efficiency = self.game_stats['player1_stats']['strategy_efficiency'].get(strategy, 0)
                    player2_efficiency = self.game_stats['player2_stats']['strategy_efficiency'].get(strategy, 0)
                    
                    if player1_efficiency > 0:
                        strategy_rankings.append((strategy, player1_efficiency, 'Player 1'))
                    if player2_efficiency > 0:
                        strategy_rankings.append((strategy, player2_efficiency, 'Player 2'))
                
                # Sort by efficiency descending
                strategy_rankings.sort(key=lambda x: x[1], reverse=True)
                
                for rank_index, (strategy, efficiency, player) in enumerate(strategy_rankings, 1):
                    writer.writerow([rank_index, strategy, f'{efficiency:.2f}', player])
                writer.writerow([])
                
                # Strategies used
                writer.writerow(['=== STRATEGIES USED ==='])
                writer.writerow(['Strategy', 'Player 1 (vehicles)', 'Player 2 (vehicles)'])
                
                for strategy in sorted(all_strategies):
                    player1_count = self.game_stats['player1_stats']['strategies_used'].get(strategy, 0)
                    player2_count = self.game_stats['player2_stats']['strategies_used'].get(strategy, 0)
                    writer.writerow([strategy, player1_count, player2_count])
            
            print(f"✅ - STATS SAVED TO CSV: {csv_filename}")
            return csv_filename
        
        except Exception as e:
            print(f"❌ - ERROR SAVING STATS TO CSV: {e}")
            return None
    
    def _calculate_strategy_efficiency(self):
        # For efficiency calculation, we use an approximate approach:
        # divide total items proportionally by the number of vehicles of each strategy
        
        for strategy in self.game_stats['player1_stats']['strategies_used']:
            vehicle_count = self.game_stats['player1_stats']['strategies_used'][strategy]
            if vehicle_count > 0:
                # Approximation: assume proportional distribution
                total_items = self.game_stats['player1_stats']['total_items_collected']
                total_vehicles = sum(self.game_stats['player1_stats']['strategies_used'].values())
                average_items = total_items / total_vehicles if total_vehicles > 0 else 0
                self.game_stats['player1_stats']['strategy_efficiency'][strategy] = average_items
        
        for strategy in self.game_stats['player2_stats']['strategies_used']:
            vehicle_count = self.game_stats['player2_stats']['strategies_used'][strategy]
            if vehicle_count > 0:
                total_items = self.game_stats['player2_stats']['total_items_collected']
                total_vehicles = sum(self.game_stats['player2_stats']['strategies_used'].values())
                average_items = total_items / total_vehicles if total_vehicles > 0 else 0
                self.game_stats['player2_stats']['strategy_efficiency'][strategy] = average_items