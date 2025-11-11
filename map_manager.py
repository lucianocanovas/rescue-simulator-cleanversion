"""Gestor del mapa y estado del juego.

Contiene la lógica para crear nuevas partidas, guardar/cargar estados por turno,
gestionar minas, vehículos y la resolución de colisiones.
"""

import random
import pickle
import os
import csv
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
        self.current_game_folder = None  # Se asignará cuando se cree o cargue una partida
        self.explosions = []
        self.current_turn = 0  # Turno actual del juego
        
        # Estadísticas de la partida
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
                'strategies_used': {},  # {strategy_name: count}
                'strategy_efficiency': {}  # {strategy_name: items_per_vehicle}
            },
            'player2_stats': {
                'final_points': 0,
                'items_collected': {'Person': 0, 'Weapon': 0, 'Clothing': 0, 'Food': 0, 'Heal': 0},
                'total_items_collected': 0,
                'vehicles_lost': 0,
                'vehicles_survived': 0,
                'collisions': 0,
                'mine_deaths': 0,
                'strategies_used': {},  # {strategy_name: count}
                'strategy_efficiency': {}  # {strategy_name: items_per_vehicle}
            }
        }
        
        # Rastreo de vehículos iniciales para calcular estadísticas
        self.initial_vehicles = {'player1': [], 'player2': []}
                
    def get_empty_cell(self, margin_x=1, margin_y=0):
        x = random.randint(margin_x, self.width - 1 - margin_x)
        y = random.randint(margin_y, self.height - 1 - margin_y)
        while self.grid[x][y] is not None:
            x = random.randint(margin_x, self.width - 1 - margin_x)
            y = random.randint(margin_y, self.height - 1 - margin_y)
        return (x, y)

    def clear(self):
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
                # Persist planned path and state so loading returns exact state
                'path': list(getattr(v, 'path', [])),
                'state': getattr(v, 'state', 'idle'),
                'load': [serialize_item(it) for it in getattr(v, 'load', [])],
                # If a vehicle is standing on an item (not picked), serialize it
                'under_item': serialize_item(getattr(v, 'under_item', None)) if getattr(v, 'under_item', None) is not None else None
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
            # Persistir explosiones visuales para que al cargar un turno
            # previo se restaure su visibilidad correctamente.
            'explosions': [ {'pos': e.get('pos'), 'ttl': int(e.get('ttl',0))} for e in getattr(self, 'explosions', []) ],
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

        # ensure current game folder exists
        if self.current_game_folder is None:
            self.current_game_folder = self._get_next_game_folder()
        if not os.path.exists(self.current_game_folder):
            os.makedirs(self.current_game_folder, exist_ok=True)

        # Save with a deterministic per-turn filename so visualization can load it
        filename = os.path.join(self.current_game_folder, f"turno_{turn_number}.pkl")
        with open(filename, 'wb') as f:
            pickle.dump(game_state, f)

        return filename

    def load_game(self, filename: str, turn: int):
        try:
            with open(filename, 'rb') as f:
                game_state = pickle.load(f)
        except Exception as e:
            print(f"❌ - ERROR LOADING SAVED GAME FILE: {e}")
            return False

        try:
            # Actualizar current_game_folder para que apunte a la carpeta de la partida cargada
            # Extraemos la carpeta padre del archivo cargado (ej: saved_games/Partida_5)
            self.current_game_folder = os.path.dirname(os.path.abspath(filename))
            
            # Basic properties
            self.width = game_state.get('width', self.width)
            self.height = game_state.get('height', self.height)

            # Clear current state
            self.clear()

            # Restore danger zones if present
            self.danger_zones = game_state.get('danger_zones', self.danger_zones)

            # Helper to recreate items
            def create_item(item_data):
                t = item_data.get('type')
                pos = item_data.get('position')
                if t == 'Person':
                    return Person(pos)
                if t == 'Weapon':
                    return Weapon(pos)
                if t == 'Clothing':
                    return Clothing(pos)
                if t == 'Food':
                    return Food(pos)
                if t == 'Heal':
                    return Heal(pos)
                return None

            # Helper to recreate vehicles
            def create_vehicle(vdata, team):
                t = vdata.get('type')
                pos = tuple(vdata.get('position', (0, 0)))
                cls = None
                if t == 'Truck':
                    cls = Truck
                elif t == 'Jeep':
                    cls = Jeep
                elif t == 'Car':
                    cls = Car
                elif t == 'Motorcycle':
                    cls = Motorcycle
                if cls is None:
                    return None
                v = cls(team, pos)
                # restore load if present (items carried by vehicle)
                v.load = []
                for it in vdata.get('load', []):
                    obj = create_item(it)
                    if obj is not None:
                        # Items inside vehicles shouldn't be placed on the grid
                        # their position can remain as metadata.
                        v.load.append(obj)
                # restore planned path and state so the vehicle returns
                # exactly to its previous behavior
                try:
                    v.path = [tuple(p) for p in vdata.get('path', [])]
                except Exception:
                    v.path = []
                v.state = vdata.get('state', 'idle')
                # restore item that was under the vehicle (if any)
                try:
                    under_serial = vdata.get('under_item')
                    if under_serial:
                        itm = create_item(under_serial)
                        if itm is not None:
                            # don't place on grid yet; keep as under_item
                            v.under_item = itm
                except Exception:
                    v.under_item = None
                return v

            # Restore mines
            mines_data = game_state.get('mines', [])
            for m in mines_data:
                mtype = m.get('type')
                pos = tuple(m.get('position', (0, 0)))
                mine_obj = None
                if mtype == 'Mine_O1':
                    mine_obj = Mine_O1(pos)
                elif mtype == 'Mine_O2':
                    mine_obj = Mine_O2(pos)
                elif mtype == 'Mine_T1':
                    mine_obj = Mine_T1(pos)
                elif mtype == 'Mine_T2':
                    mine_obj = Mine_T2(pos)
                elif mtype == 'Mine_G1':
                    mine_obj = Mine_G1(pos)
                if mine_obj is not None:
                    # If the saved data contained explicit radii (e.g. Mine_G1 toggled
                    # to 0), restore those values so loading a previous turn keeps
                    # the mine in the same active/inactive state.
                    try:
                        saved_x = m.get('x_radius', None)
                        saved_y = m.get('y_radius', None)
                        if saved_x is not None:
                            mine_obj.x_radius = int(saved_x)
                        if saved_y is not None:
                            mine_obj.y_radius = int(saved_y)
                    except Exception:
                        # ignore and keep defaults if something goes wrong
                        pass
                    self.mines.append(mine_obj)
                    x, y = mine_obj.position
                    self.grid[x][y] = mine_obj

            # Restore standalone items
            for it in game_state.get('items', []):
                obj = create_item(it)
                if obj is not None:
                    x, y = obj.position
                    self.grid[x][y] = obj

            # Restore explosions visual state (so que al retroceder desaparezcan)
            try:
                self.explosions = []
                for ex in game_state.get('explosions', []):
                    pos = tuple(ex.get('pos')) if ex.get('pos') is not None else None
                    ttl = int(ex.get('ttl', 0))
                    if pos is not None and ttl > 0:
                        self.explosions.append({'pos': pos, 'ttl': ttl})
            except Exception:
                self.explosions = []

            # Restore player points
            try:
                self.player1.points = game_state.get('player1', {}).get('points', 0)
                self.player2.points = game_state.get('player2', {}).get('points', 0)
            except Exception:
                pass

            # Restore vehicles for each player
            self.player1.vehicles = []
            self.player2.vehicles = []
            for vdata in game_state.get('player1', {}).get('vehicles', []):
                v = create_vehicle(vdata, self.player1)
                if v is not None:
                    self.player1.add_vehicle(v)
                    x, y = v.position
                    self.grid[x][y] = v
            for vdata in game_state.get('player2', {}).get('vehicles', []):
                v = create_vehicle(vdata, self.player2)
                if v is not None:
                    self.player2.add_vehicle(v)
                    x, y = v.position
                    self.grid[x][y] = v

            # Update danger zones
            self.update_danger_zones()

            return True
        except Exception as e:
            print(f"❌ - ERROR RESTORING GAME STATE FROM FILE: {e}")
            return False

    def new_game(self):
        # Inicializa un nuevo tablero y coloca vehículos, minas y items
        self.clear()
        
        # Inicializar estadísticas del juego
        self.game_stats['start_time'] = datetime.now()
        self.current_turn = 0
        
        # Crear carpeta para la nueva partida
        if self.current_game_folder is None:
            self.current_game_folder = self._get_next_game_folder()
        
        # Cargar configuración de vehículos desde config.json
        vehicles_p1 = []
        vehicles_p2 = []
        try:
            import json
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Importar las clases de estrategia
            from strategies import PickNearest, Kamikaze, Escort, Invader, FullSafe
            strategy_map = {
                'PickNearest': PickNearest,
                'Kamikaze': Kamikaze,
                'Escort': Escort,
                'Invader': Invader,
                'FullSafe': FullSafe
            }
            
            # Mapa de tipos de vehículos
            vehicle_type_map = {
                'Truck': Truck,
                'Car': Car,
                'Jeep': Jeep,
                'Motorcycle': Motorcycle
            }
            
            # Leer configuración de jugadores
            players_config = config.get('players', {})
            
            # Configurar vehículos para player1
            p1_config = players_config.get('player1', {}).get('vehicles', [])
            for vehicle_config in p1_config:
                vehicle_type = vehicle_config.get('type', 'Car')
                strategy_name = vehicle_config.get('strategy', 'PickNearest')
                y_pos = vehicle_config.get('y_position', 0)
                
                # Crear instancia de vehículo
                vehicle_class = vehicle_type_map.get(vehicle_type, Car)
                strategy_class = strategy_map.get(strategy_name, PickNearest)
                strategy = strategy_class()
                
                vehicles_p1.append({
                    'class': vehicle_class,
                    'position': (0, y_pos),
                    'strategy': strategy
                })
            
            # Configurar vehículos para player2
            p2_config = players_config.get('player2', {}).get('vehicles', [])
            for vehicle_config in p2_config:
                vehicle_type = vehicle_config.get('type', 'Car')
                strategy_name = vehicle_config.get('strategy', 'PickNearest')
                y_pos = vehicle_config.get('y_position', 0)
                
                # Crear instancia de vehículo
                vehicle_class = vehicle_type_map.get(vehicle_type, Car)
                strategy_class = strategy_map.get(strategy_name, PickNearest)
                strategy = strategy_class()
                
                vehicles_p2.append({
                    'class': vehicle_class,
                    'position': (self.width - 1, y_pos),
                    'strategy': strategy
                })
                
        except Exception as e:
            print(f"❌ - ERROR LOADING CONFIGURATION FILE: {e}, USING DEFAULT VEHICLE SETUP")
            from strategies import PickNearest
            # Configuración por defecto (10 vehículos por jugador)
            default_vehicles = [
                (Truck, 2), (Car, 7), (Jeep, 12), (Motorcycle, 17), (Jeep, 22),
                (Car, 27), (Truck, 32), (Car, 37), (Motorcycle, 42), (Jeep, 47)
            ]
            for vehicle_class, y_pos in default_vehicles:
                vehicles_p1.append({
                    'class': vehicle_class,
                    'position': (0, y_pos),
                    'strategy': PickNearest()
                })
                vehicles_p2.append({
                    'class': vehicle_class,
                    'position': (self.width - 1, y_pos),
                    'strategy': PickNearest()
                })
        
        # Asegurar que hay al menos un vehículo
        if not vehicles_p1:
            from strategies import PickNearest
            vehicles_p1.append({
                'class': Car,
                'position': (0, self.height // 2),
                'strategy': PickNearest()
            })
        if not vehicles_p2:
            from strategies import PickNearest
            vehicles_p2.append({
                'class': Car,
                'position': (self.width - 1, self.height // 2),
                'strategy': PickNearest()
            })

        # Setup Player 1 Vehicles
        for vehicle_data in vehicles_p1:
            vehicle = vehicle_data['class'](
                self.player1, 
                vehicle_data['position'], 
                strategy=vehicle_data['strategy']
            )
            self.player1.add_vehicle(vehicle)
            x, y = vehicle.position
            self.grid[x][y] = vehicle

        # Setup Player 2 Vehicles
        for vehicle_data in vehicles_p2:
            vehicle = vehicle_data['class'](
                self.player2, 
                vehicle_data['position'], 
                strategy=vehicle_data['strategy']
            )
            self.player2.add_vehicle(vehicle)
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
        
        # Registrar vehículos iniciales y estrategias para estadísticas
        self.initial_vehicles = {'player1': [], 'player2': []}
        for v in self.player1.vehicles:
            strategy_name = v.strategy.__class__.__name__ if hasattr(v, 'strategy') else 'Unknown'
            self.initial_vehicles['player1'].append({
                'type': v.__class__.__name__,
                'strategy': strategy_name
            })
            # Contar estrategias usadas
            self.game_stats['player1_stats']['strategies_used'][strategy_name] = \
                self.game_stats['player1_stats']['strategies_used'].get(strategy_name, 0) + 1
        
        for v in self.player2.vehicles:
            strategy_name = v.strategy.__class__.__name__ if hasattr(v, 'strategy') else 'Unknown'
            self.initial_vehicles['player2'].append({
                'type': v.__class__.__name__,
                'strategy': strategy_name
            })
            # Contar estrategias usadas
            self.game_stats['player2_stats']['strategies_used'][strategy_name] = \
                self.game_stats['player2_stats']['strategies_used'].get(strategy_name, 0) + 1
        
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
        # Guardar el turno actual
        self.current_turn = current_turn

        # DEBUG: registrar estado de minas antes de ejecutar el turno
        try:
            mine_positions_before = [m.position for m in self.mines]
            mine_radii_before = [(m.position, getattr(m, 'x_radius', None), getattr(m, 'y_radius', None)) for m in self.mines]
        except Exception:
            pass

        # Alternador de minas tipo G1: no queremos que ocurra en el turno inicial (0).
        # Aplicamos el toggle cuando el siguiente turno vaya a ser múltiplo de 7,
        # es decir, al avanzar hacia un turno 7,14,21,...
        if (current_turn + 1) % 5 == 0:
            for mine in self.mines:
                if isinstance(mine, Mine_G1):
                    mine.toggle()

    # FASE DE PLANIFICACIÓN: pedir a cada vehículo que planifique su siguiente paso
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

    # RECOGIDA DE MOVIMIENTOS INTENDIDOS
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

    # FASE DE EJECUCIÓN: realizar los movimientos aprobados
        for v, target in list(intent_by_vehicle.items()):
            try:
                v.execute_move(self, target)
            except Exception:
                # fallback to move (backwards compatibility)
                try:
                    v.move(self)
                except Exception:
                    pass

    # Recalcular zonas de peligro por si alguna mina cambió de estado
        self.update_danger_zones()

        # DEBUG: registrar estado de minas despues de ejecutar el turno
        try:
            mine_positions_after = [m.position for m in self.mines]
            mine_radii_after = [(m.position, getattr(m, 'x_radius', None), getattr(m, 'y_radius', None)) for m in self.mines]
        except Exception:
            pass

    # Después del movimiento, gestionar colisiones
        self.check_collisions()

        # Reducir TTL de explosiones (aparecen N turnos)
        try:
            for ex in list(self.explosions):
                try:
                    ex['ttl'] = int(ex.get('ttl', 0)) - 1
                except Exception:
                    ex['ttl'] = 0
            self.explosions = [e for e in self.explosions if e.get('ttl', 0) > 0]
        except Exception:
            pass

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
                # Registrar una explosión visual cuando hay colisión (3 turnos)
                try:
                    self.explosions.append({'pos': (x, y), 'ttl': 3})
                except Exception:
                    pass
                # Track whether any vehicle restored an item to this cell
                restored_item = False
                for v in vs:
                    # Registrar estadísticas de colisión
                    player_key = 'player1_stats' if v.team == self.player1 else 'player2_stats'
                    self.game_stats[player_key]['collisions'] += 1
                    self.game_stats[player_key]['vehicles_lost'] += 1
                    
                    # If a vehicle had an item stored under it, restore it to the grid
                    try:
                        if getattr(v, 'under_item', None) is not None:
                            itm = v.under_item
                            try:
                                itm.position = (x, y)
                                self.grid[x][y] = itm
                                restored_item = True
                            except Exception:
                                pass
                            v.under_item = None
                    except Exception:
                        pass
                    # Remove vehicle from its team's list
                    try:
                        if v in v.team.vehicles:
                            v.team.vehicles.remove(v)
                    except Exception:
                        pass
                # If no item was restored above, make sure the grid cell is cleared
                # (previous code mistakenly checked if grid[x][y] is None before
                # clearing, which left a vehicle instance visible on the grid).
                if not restored_item:
                    try:
                        self.grid[x][y] = None
                    except Exception:
                        pass
                # Registro de colisión: imprimimos información consistente en español
                print(f"💥 - COLLISION ({pos})")
                detalle_vehiculos = [f"{v.__class__.__name__.upper()} - TEAM: {v.team.name.upper()}" for v in vs]
                print(f"💥 - COLLISION VEHICLES: {detalle_vehiculos}")

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
                    # Registrar estadísticas de muerte por mina
                    player_key = 'player1_stats' if vehicle.team == self.player1 else 'player2_stats'
                    self.game_stats[player_key]['mine_deaths'] += 1
                    self.game_stats[player_key]['vehicles_lost'] += 1
                    
                    # Restaurar cualquier item que estuviera bajo el vehículo
                    restored_item = False
                    try:
                        if getattr(vehicle, 'under_item', None) is not None:
                            itm = vehicle.under_item
                            try:
                                itm.position = (vehicle_x, vehicle_y)
                                self.grid[vehicle_x][vehicle_y] = itm
                                restored_item = True
                            except Exception:
                                restored_item = False
                            vehicle.under_item = None
                    except Exception:
                        restored_item = False

                    # Registrar una explosión visual por destrucción en mina (3 turnos)
                    try:
                        self.explosions.append({'pos': (vehicle_x, vehicle_y), 'ttl': 3})
                    except Exception:
                        pass

                    # Eliminar vehículo del equipo
                    try:
                        if vehicle in vehicle.team.vehicles:
                            vehicle.team.vehicles.remove(vehicle)
                    except Exception:
                        pass

                    # Si no se restauró un item bajo el vehículo, limpiar la celda para
                    # evitar que el vehículo permanezca visible en el grid
                    try:
                        if not restored_item:
                            self.grid[vehicle_x][vehicle_y] = None
                    except Exception:
                        pass
                    break

    def is_game_over(self):
        try:
            from classes.Item import Item, Person
        except Exception:
            Item = None
            Person = None

        # 1) No vehicles
        total_vehicles = len(getattr(self.player1, 'vehicles', [])) + len(getattr(self.player2, 'vehicles', []))
        if total_vehicles == 0:
            return True, 'no_vehicles'

        # 2) No items (on grid or inside vehicles or stored under vehicles)
        items_on_grid = []
        for x in range(self.width):
            for y in range(self.height):
                obj = self.grid[x][y]
                try:
                    if Item is not None and isinstance(obj, Item):
                        items_on_grid.append((x, y))
                except Exception:
                    pass

        items_in_vehicles = 0
        vehicles_with_load = []
        vehicles = list(getattr(self.player1, 'vehicles', [])) + list(getattr(self.player2, 'vehicles', []))
        for v in vehicles:
            try:
                vehicle_load = len(getattr(v, 'load', []))
                items_in_vehicles += vehicle_load
                if vehicle_load > 0:
                    vehicles_with_load.append(v)
            except Exception:
                pass
            try:
                if getattr(v, 'under_item', None) is not None:
                    items_in_vehicles += 1
            except Exception:
                pass

        if (len(items_on_grid) + items_in_vehicles) == 0:
            return True, 'no_items'

        # 3) Items exist on the map but no available vehicle can reach any of them
        # IMPORTANT: If there are vehicles with items loaded, the game must continue
        # so they can deliver them, even if there are no more reachable items on the grid
        if not items_on_grid:
            # Si no hay items en el grid pero hay vehículos con carga, el juego continúa
            if vehicles_with_load:
                return False, None
            # Si no hay items en el grid ni vehículos con carga, el juego termina
            return True, 'no_items'

        # Check if any vehicle can reach items on the grid
        # Use pathfinding utilities to check reachability from each vehicle that
        # is able to pick items (not full).
        try:
            from pathfinding import find_nearest
        except Exception:
            find_nearest = None

        for v in vehicles:
            try:
                # skip vehicles that are full
                if len(getattr(v, 'load', [])) >= getattr(v, 'capacity', 0):
                    continue
                # choose pathfinder according to vehicle's capabilities
                if find_nearest is None:
                    continue
                only_persons = getattr(v, 'only_persons', False)
                exclude_persons = getattr(v, 'exclude_persons', False)
                path = find_nearest(self.grid, v.position, self.danger_zones, 
                                  only_persons=only_persons, exclude_persons=exclude_persons)
                if path is not None:
                    # at least one vehicle can reach an on-grid item => not over
                    return False, None
            except Exception:
                continue

        # No vehicle can reach any on-grid item
        # BUT: if there are vehicles with items loaded, they need to deliver them first
        if vehicles_with_load:
            return False, None
        
        # No hay items alcanzables Y no hay vehículos con carga
        return True, 'no_reachable_items'
    
    def generate_game_stats_csv(self, end_reason: str):
        """Genera un archivo CSV con las estadísticas completas de la partida"""
        if self.current_game_folder is None:
            print("❌ - ERROR: No hay carpeta de juego activa para guardar estadísticas")
            return
        
        # Actualizar estadísticas finales
        self.game_stats['end_time'] = datetime.now()
        self.game_stats['total_turns'] = self.current_turn
        self.game_stats['end_reason'] = end_reason
        
        # Determinar ganador
        p1_points = self.player1.points
        p2_points = self.player2.points
        if p1_points > p2_points:
            self.game_stats['winner'] = 'Player 1'
        elif p2_points > p1_points:
            self.game_stats['winner'] = 'Player 2'
        else:
            self.game_stats['winner'] = 'Empate'
        
        # Actualizar estadísticas de puntos finales
        self.game_stats['player1_stats']['final_points'] = p1_points
        self.game_stats['player2_stats']['final_points'] = p2_points
        
        # Actualizar estadísticas de items recolectados
        for item_type in self.player1.items_collected:
            self.game_stats['player1_stats']['items_collected'][item_type] = \
                self.player1.items_collected[item_type]
        for item_type in self.player2.items_collected:
            self.game_stats['player2_stats']['items_collected'][item_type] = \
                self.player2.items_collected[item_type]
        
        # Calcular total de items recolectados
        self.game_stats['player1_stats']['total_items_collected'] = \
            sum(self.player1.items_collected.values())
        self.game_stats['player2_stats']['total_items_collected'] = \
            sum(self.player2.items_collected.values())
        
        # Calcular vehículos sobrevivientes
        self.game_stats['player1_stats']['vehicles_survived'] = len(self.player1.vehicles)
        self.game_stats['player2_stats']['vehicles_survived'] = len(self.player2.vehicles)
        
        # Calcular eficiencia por estrategia
        self._calculate_strategy_efficiency()
        
        # Generar archivo CSV
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
                writer.writerow(['Player 1', p1_points])
                writer.writerow(['Player 2', p2_points])
                writer.writerow(['Difference', abs(p1_points - p2_points)])
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
                    p1_eff = self.game_stats['player1_stats']['strategy_efficiency'].get(strategy, 0)
                    p2_eff = self.game_stats['player2_stats']['strategy_efficiency'].get(strategy, 0)
                    
                    if p1_eff > p2_eff:
                        better = 'Player 1'
                    elif p2_eff > p1_eff:
                        better = 'Player 2'
                    else:
                        better = 'Tie'
                    
                    writer.writerow([strategy, f'{p1_eff:.2f}', f'{p2_eff:.2f}', better])
                writer.writerow([])
                
                # Ranking of strategies by average efficiency
                writer.writerow(['=== STRATEGY RANKING (BY AVERAGE EFFICIENCY) ==='])
                writer.writerow(['Rank', 'Strategy', 'Average Efficiency', 'Player'])
                
                strategy_rankings = []
                for strategy in all_strategies:
                    p1_eff = self.game_stats['player1_stats']['strategy_efficiency'].get(strategy, 0)
                    p2_eff = self.game_stats['player2_stats']['strategy_efficiency'].get(strategy, 0)
                    
                    if p1_eff > 0:
                        strategy_rankings.append((strategy, p1_eff, 'Player 1'))
                    if p2_eff > 0:
                        strategy_rankings.append((strategy, p2_eff, 'Player 2'))
                
                # Sort by efficiency descending
                strategy_rankings.sort(key=lambda x: x[1], reverse=True)
                
                for idx, (strategy, efficiency, player) in enumerate(strategy_rankings, 1):
                    writer.writerow([idx, strategy, f'{efficiency:.2f}', player])
                writer.writerow([])
                
                # Strategies used
                writer.writerow(['=== STRATEGIES USED ==='])
                writer.writerow(['Strategy', 'Player 1 (vehicles)', 'Player 2 (vehicles)'])
                
                for strategy in sorted(all_strategies):
                    p1_count = self.game_stats['player1_stats']['strategies_used'].get(strategy, 0)
                    p2_count = self.game_stats['player2_stats']['strategies_used'].get(strategy, 0)
                    writer.writerow([strategy, p1_count, p2_count])
            
            print(f"✅ - STATS SAVED TO CSV: {csv_filename}")
            return csv_filename
        
        except Exception as e:
            print(f"❌ - ERROR SAVING STATS TO CSV: {e}")
            return None
    
    def _calculate_strategy_efficiency(self):
        """Calcula la eficiencia de cada estrategia (items recolectados por vehículo)"""
        # Rastrear items recolectados por estrategia
        p1_strategy_items = {}
        p2_strategy_items = {}
        
        # Para calcular eficiencia, necesitamos saber cuántos items recolectó cada vehículo
        # Como no tenemos rastreo individual, usaremos un enfoque aproximado:
        # dividir items totales proporcionalmente por el número de vehículos de cada estrategia
        
        for strategy in self.game_stats['player1_stats']['strategies_used']:
            vehicle_count = self.game_stats['player1_stats']['strategies_used'][strategy]
            if vehicle_count > 0:
                # Aproximación: asumir distribución proporcional
                total_items = self.game_stats['player1_stats']['total_items_collected']
                total_vehicles = sum(self.game_stats['player1_stats']['strategies_used'].values())
                avg_items = total_items / total_vehicles if total_vehicles > 0 else 0
                self.game_stats['player1_stats']['strategy_efficiency'][strategy] = avg_items
        
        for strategy in self.game_stats['player2_stats']['strategies_used']:
            vehicle_count = self.game_stats['player2_stats']['strategies_used'][strategy]
            if vehicle_count > 0:
                total_items = self.game_stats['player2_stats']['total_items_collected']
                total_vehicles = sum(self.game_stats['player2_stats']['strategies_used'].values())
                avg_items = total_items / total_vehicles if total_vehicles > 0 else 0
                self.game_stats['player2_stats']['strategy_efficiency'][strategy] = avg_items