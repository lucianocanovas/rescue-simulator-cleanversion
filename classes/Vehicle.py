from assets import load_sprite, load_sound
from classes.Item import Item, Person
from classes.Player import Player
from pathfinding import find_nearest, find_path_to_column
from classes.Mine import Mine

class Vehicle:
    def __init__(self, team: Player, position: tuple[int, int], capacity: int, sprite: str, load: list[Item] = [], only_persons: bool = False, exclude_persons: bool = False, strategy=None):
        self.team = team
        self.position = position
        self.capacity = capacity
        self.load = load
        # If a vehicle is standing on top of an item without picking it,
        # we store that item here so it can be restored to the grid when
        # the vehicle moves away or is destroyed.
        self.under_item = None
        # path is a list of (x,y) positions vehicle will follow (including current start)
        self.path: list[tuple[int, int]] = []
        # state: 'idle', 'collecting', 'returning'
        self.state: str = 'idle'
        self.only_persons = only_persons  # Motocicletas: solo personas
        self.exclude_persons = exclude_persons  # Camiones y Jeeps: no personas
        self.strategy = strategy  # Estrategia del vehículo
        try:
            self.sprite = load_sprite(sprite)
        except Exception as e:
            # Mensaje de error uniforme en español
            print(f"[ERROR] Error al cargar sprite: {e}")
            self.sprite = None
        # Cargar el sonido de descarga una sola vez (variable de clase)
        try:
            self.unload_sound = load_sound('unload.mp3')
        except Exception:
            self.unload_sound = None

    def move(self, map_manager):
        # Backwards-compatible single-vehicle move: plan then execute one step
        self.plan(map_manager)
        next_pos = self.peek_next()
        if next_pos:
            self.execute_move(map_manager, next_pos)
        return

    def plan(self, map_manager):
        """Plan a path if none exists: find nearest safe item or path to base.
        Sets self.path (list of positions excluding current) and self.state.
        Does not modify the map.
        """
        # Si el vehículo tiene una estrategia, usarla
        if self.strategy is not None:
            try:
                self.strategy.plan(self, map_manager)
                return
            except Exception as e:
                print(f"[WARNING] Error al ejecutar estrategia: {e}. Usando estrategia por defecto.")
        
        # Estrategia por defecto (PickNearest)
        if self.path:
            return
        # If not full, find nearest safe item
        if len(self.load) < self.capacity:
            path = find_nearest(map_manager.grid, self.position, map_manager.danger_zones, 
                              only_persons=self.only_persons, exclude_persons=self.exclude_persons)
            if path:
                self.path = path[1:]
                self.state = 'collecting'
                return
        # Otherwise, plan path to base
        base_x = 0 if map_manager.player1 is self.team else map_manager.width - 1
        path = find_path_to_column(map_manager.grid, self.position, base_x, map_manager.danger_zones)
        if path:
            self.path = path[1:]
            self.state = 'returning'

    def peek_next(self):
        """Return next planned position or None (does not modify path)."""
        return self.path[0] if self.path else None

    def execute_move(self, map_manager, target_pos: tuple[int, int]):
        """Execute a single step to target_pos. Assumes MapManager approved the move.
        Updates grid, position, picks items and handles unloading at base.
        """
        nx, ny = target_pos
        if not (0 <= nx < map_manager.width and 0 <= ny < map_manager.height):
            self.path = []
            return

        dest_obj = map_manager.grid[nx][ny]
        # If destination occupied by a Mine, abort the move
        if dest_obj is not None and isinstance(dest_obj, Mine):
            self.path = []
            return
        # If destination occupied by another Vehicle, allow the move.
        # Collisions are handled centrally by MapManager.check_collisions()
        # Items are handled below (picked up if possible).

        old_x, old_y = self.position
        # When leaving the old cell, restore any item that was under this vehicle
        if 0 <= old_x < map_manager.width and 0 <= old_y < map_manager.height:
            if map_manager.grid[old_x][old_y] is self:
                map_manager.grid[old_x][old_y] = None
            # If we were carrying an item 'under' us, put it back on the grid
            if getattr(self, 'under_item', None) is not None:
                item = self.under_item
                try:
                    item.position = (old_x, old_y)
                    map_manager.grid[old_x][old_y] = item
                except Exception:
                    pass
                self.under_item = None

        # Handle item at destination.
        if isinstance(dest_obj, Item):
            picked = self.pick_item(dest_obj)
            if picked:
                # Remove item from ground since it was picked
                map_manager.grid[nx][ny] = None
            else:
                # Vehicle cannot pick this item (e.g., motorcycle vs non-person).
                # Allow vehicle to pass over the item: temporarily remove the
                # item from the grid and keep it in `under_item` so it can be
                # restored when the vehicle leaves that cell or is destroyed.
                try:
                    # detach item from grid and store reference
                    self.under_item = dest_obj
                    map_manager.grid[nx][ny] = None
                except Exception:
                    self.under_item = None

        # Move
        self.position = (nx, ny)
        map_manager.grid[nx][ny] = self

        # consume step
        if self.path and self.path[0] == target_pos:
            self.path.pop(0)

        if len(self.load) >= self.capacity:
            self.path = []
            self.state = 'returning'

        if self.state == 'returning':
            base_x = 0 if map_manager.player1 is self.team else map_manager.width - 1
            if self.position[0] == base_x:
                total = 0
                for it in list(self.load):
                    try:
                        total += getattr(it, 'value', 0)
                    except Exception:
                        pass
                try:
                    self.team.add_points(total)
                except Exception:
                    pass
                # Reproducir sonido de descarga si hay items y el sonido está disponible
                if self.load and self.unload_sound is not None:
                    try:
                        self.unload_sound.play()
                    except Exception:
                        pass
                self.load = []
                self.state = 'idle'
                self.path = []

    def unload_if_at_base(self, map_manager):
        """If the vehicle is at its team's base, unload all items, award points
        to the team, and clear the load. Returns True if unload occurred."""
        if not self.load:
            return False
        base_x = 0 if map_manager.player1 is self.team else map_manager.width - 1
        if self.position[0] != base_x:
            return False

        total = 0
        for it in list(self.load):
            try:
                total += getattr(it, 'value', 0)
            except Exception:
                pass
        try:
            self.team.add_points(total)
        except Exception:
            pass
        
        # Reproducir sonido de descarga si el sonido está disponible
        if self.unload_sound is not None:
            try:
                self.unload_sound.play()
            except Exception:
                pass
        
        # clear load
        self.load = []
        self.state = 'idle'
        self.path = []
        return True

    def pick_item(self, item: Item):
        if len(self.load) >= self.capacity:
            return False
        if self.only_persons and not isinstance(item, Person):
            return False
        if self.exclude_persons and isinstance(item, Person):
            return False
        self.load.append(item)
        return True
    
    def drop_item(self, item: Item):
        if item in self.load:
            self.load.remove(item)
            return True
        return False
    
    def return_to_base(self):
        # Implement return to base logic here
        pass

class Truck(Vehicle):
    def __init__(self, team: Player, position: tuple[int, int], strategy=None):
        super().__init__(team, position, capacity=3, sprite="truck.png", load=[], only_persons=False, exclude_persons=True, strategy=strategy)

class Jeep(Vehicle):
    def __init__(self, team: Player, position: tuple[int, int], strategy=None):
        super().__init__(team ,position, capacity=2, sprite="jeep.png", load=[], only_persons=False, exclude_persons=True, strategy=strategy)

class Car(Vehicle):
    def __init__(self, team: Player, position: tuple[int, int], strategy=None):
        super().__init__(team, position, capacity=1, sprite="car.png", load=[], only_persons=False, exclude_persons=False, strategy=strategy)

class Motorcycle(Vehicle):
    def __init__(self, team: Player, position: tuple[int, int], strategy=None):
        super().__init__(team, position, capacity=1, sprite="motorcycle.png", load=[], only_persons=True, exclude_persons=False, strategy=strategy)