"""Gestor del mapa y estado del juego.

Contiene la lógica para crear nuevas partidas, guardar/cargar estados por turno,
gestionar minas, vehículos y la resolución de colisiones.
"""

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
        self.collision_policy = 'allow_crash'
        self.current_game_folder = self._get_next_game_folder()  # Carpeta para la partida actual
        self.explosions = []
                
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
        if not os.path.exists(self.current_game_folder):
            os.makedirs(self.current_game_folder, exist_ok=True)

        # Save with a deterministic per-turn filename so visualization can load it
        filename = os.path.join(self.current_game_folder, f"turno_{turn_number}.pkl")
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
            print(f"[ERROR] No se pudo abrir el archivo de guardado: {e}")
            return False

        try:
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
            print(f"[ERROR] Error al reconstruir el estado de la partida: {e}")
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

    # RESOLVER CONFLICTOS ENTRE VEHÍCULOS QUE QUIEREN LA MISMA CASILLA
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
                print(f"[COLISIÓN] Posición: {pos} — Vehículos eliminados: {len(vs)}")
                detalle_vehiculos = [f"{v.__class__.__name__} (equipo: {v.team.name})" for v in vs]
                print(f"[COLISIÓN] Vehículos involucrados: {detalle_vehiculos}")

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
        """Return (True, reason) if the game should end.

        Reasons:
          - 'no_vehicles': no vehicles remain for either player
          - 'no_items': there are no items anywhere (on grid or in vehicles)
          - 'no_reachable_items': there are items on the grid but no available
            vehicle can find a safe path to any of them
        """
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
        vehicles = list(getattr(self.player1, 'vehicles', [])) + list(getattr(self.player2, 'vehicles', []))
        for v in vehicles:
            try:
                items_in_vehicles += len(getattr(v, 'load', []))
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
        # If there are no items on the grid (all are inside vehicles), the game is not over.
        if not items_on_grid:
            return False, None

        # Use pathfinding utilities to check reachability from each vehicle that
        # is able to pick items (not full).
        try:
            from pathfinding import find_nearest_item, find_nearest_person
        except Exception:
            find_nearest_item = None
            find_nearest_person = None

        for v in vehicles:
            try:
                # skip vehicles that are full
                if len(getattr(v, 'load', [])) >= getattr(v, 'capacity', 0):
                    continue
                # choose pathfinder according to vehicle's capabilities
                if getattr(v, 'only_persons', False):
                    if find_nearest_person is None:
                        continue
                    path = find_nearest_person(self.grid, v.position, self.danger_zones)
                else:
                    if find_nearest_item is None:
                        continue
                    path = find_nearest_item(self.grid, v.position, self.danger_zones)
                if path is not None:
                    # at least one vehicle can reach an on-grid item => not over
                    return False, None
            except Exception:
                continue

        # No vehicle can reach any on-grid item
        return True, 'no_reachable_items'