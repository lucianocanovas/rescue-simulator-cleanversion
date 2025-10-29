from assets import load_sprite
from classes.Item import Item, Person
from classes.Player import Player
from pathfinding import find_nearest_item, find_path_to_column
from classes.Mine import Mine

class Vehicle:
    def __init__(self, team: Player, position: tuple[int, int], capacity: int, sprite: str, load: list[Item] = [], only_persons: bool = False):
        self.team = team
        self.position = position
        self.capacity = capacity
        self.load = load
        # path is a list of (x,y) positions vehicle will follow (including current start)
        self.path: list[tuple[int, int]] = []
        # state: 'idle', 'collecting', 'returning'
        self.state: str = 'idle'
        self.only_persons = only_persons
        try:
            self.sprite = load_sprite(sprite)
        except Exception as e:
            print(f"Error loading sprite: {e}")
            self.sprite = None

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
        if self.path:
            return
        # If not full, find nearest safe item
        if len(self.load) < self.capacity:
            path = find_nearest_item(map_manager.grid, self.position, map_manager.danger_zones)
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
        # If destination occupied by non-item, abort
        if dest_obj is not None and not isinstance(dest_obj, Item):
            self.path = []
            return

        old_x, old_y = self.position
        if 0 <= old_x < map_manager.width and 0 <= old_y < map_manager.height:
            if map_manager.grid[old_x][old_y] is self:
                map_manager.grid[old_x][old_y] = None

        # Pick item if present
        if isinstance(dest_obj, Item):
            picked = self.pick_item(dest_obj)
            if picked:
                map_manager.grid[nx][ny] = None
            else:
                self.path = []
                map_manager.grid[old_x][old_y] = self
                return

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
                self.load = []
                self.state = 'idle'
                self.path = []

    def pick_item(self, item: Item):
        if len(self.load) >= self.capacity:
            return False
        if self.only_persons and not isinstance(item, Person):
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
    def __init__(self, team: Player, position: tuple[int, int]):
        super().__init__(team, position, capacity=3, sprite="truck.png", load=[], only_persons=False)

class Jeep(Vehicle):
    def __init__(self, team: Player, position: tuple[int, int]):
        super().__init__(team ,position, capacity=2, sprite="jeep.png", load=[], only_persons=False)

class Car(Vehicle):
    def __init__(self, team: Player, position: tuple[int, int]):
        super().__init__(team, position, capacity=1, sprite="car.png", load=[], only_persons=False)

class Motorcycle(Vehicle):
    def __init__(self, team: Player, position: tuple[int, int]):
        super().__init__(team, position, capacity=1, sprite="car.png", load=[], only_persons=True)