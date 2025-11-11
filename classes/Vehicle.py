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
        self.only_persons = only_persons  # Motorcycles: only persons
        self.exclude_persons = exclude_persons  # Trucks and Jeeps: no persons
        self.strategy = strategy
        try:
            self.sprite = load_sprite(sprite)
        except Exception as error:
            print(f"❌ - ERROR LOADING THE VEHICLE SPRITE: {error}")
            self.sprite = None
        # Load the unload sound once (class variable)
        try:
            self.unload_sound = load_sound('unload.mp3')
        except Exception:
            self.unload_sound = None

    def move(self, map_manager):
        self.plan(map_manager)
        next_position = self.peek_next()
        if next_position:
            self.execute_move(map_manager, next_position)
        return

    def plan(self, map_manager):
        # If the vehicle has a strategy, use it
        if self.strategy is not None:
            try:
                self.strategy.plan(self, map_manager)
                return
            except Exception as error:
                print(f"❌ - ERROR IN VEHICLE STRATEGY PLAN: {error}, USING DEFAULT BEHAVIOR")
        
        # Default strategy (PickNearest)
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
            # If no available items, return to base to avoid blocking
            else:
                base_x = 0 if map_manager.player1 is self.team else map_manager.width - 1
                path = find_path_to_column(map_manager.grid, self.position, base_x, map_manager.danger_zones)
                if path:
                    self.path = path[1:]
                    self.state = 'returning'
                return
        # Otherwise, plan path to base
        base_x = 0 if map_manager.player1 is self.team else map_manager.width - 1
        path = find_path_to_column(map_manager.grid, self.position, base_x, map_manager.danger_zones)
        if path:
            self.path = path[1:]
            self.state = 'returning'

    def peek_next(self):
        return self.path[0] if self.path else None

    def execute_move(self, map_manager, target_position: tuple[int, int]):
        next_x, next_y = target_position
        if not (0 <= next_x < map_manager.width and 0 <= next_y < map_manager.height):
            self.path = []
            return

        destination_object = map_manager.grid[next_x][next_y]
        # If destination occupied by a Mine, abort the move
        if destination_object is not None and isinstance(destination_object, Mine):
            self.path = []
            return
        # If destination occupied by another Vehicle, allow the move.
        # Collisions are handled centrally by MapManager.check_collisions()

        old_x, old_y = self.position
        # When leaving the old cell, restore any item that was under this vehicle
        if 0 <= old_x < map_manager.width and 0 <= old_y < map_manager.height:
            if map_manager.grid[old_x][old_y] is self:
                map_manager.grid[old_x][old_y] = None
            # If we were carrying an item 'under' us, put it back on the grid
            if getattr(self, 'under_item', None) is not None:
                item_under = self.under_item
                try:
                    item_under.position = (old_x, old_y)
                    map_manager.grid[old_x][old_y] = item_under
                except Exception:
                    pass
                self.under_item = None

        # Handle item at destination.
        if isinstance(destination_object, Item):
            picked = self.pick_item(destination_object)
            if picked:
                # Remove item from ground since it was picked
                map_manager.grid[next_x][next_y] = None
            else:
                # Vehicle cannot pick this item (e.g., motorcycle vs non-person).
                # Allow vehicle to pass over the item: temporarily remove the
                # item from the grid and keep it in `under_item`.
                try:
                    self.under_item = destination_object
                    map_manager.grid[next_x][next_y] = None
                except Exception:
                    self.under_item = None

        # Move
        self.position = (next_x, next_y)
        map_manager.grid[next_x][next_y] = self

        # Consume step
        if self.path and self.path[0] == target_position:
            self.path.pop(0)

        if len(self.load) >= self.capacity:
            self.path = []
            self.state = 'returning'

        if self.state == 'returning':
            base_x = 0 if map_manager.player1 is self.team else map_manager.width - 1
            if self.position[0] == base_x:
                total_points = 0
                for item in list(self.load):
                    try:
                        total_points += getattr(item, 'value', 0)
                        # Register the type of collected item
                        item_type = item.__class__.__name__
                        self.team.register_item(item_type)
                    except Exception:
                        pass
                try:
                    self.team.add_points(total_points)
                except Exception:
                    pass
                # Play unload sound if items exist and sound is available
                if self.load and self.unload_sound is not None:
                    try:
                        self.unload_sound.play()
                    except Exception:
                        pass
                self.load = []
                self.state = 'idle'
                self.path = []

    def unload_if_at_base(self, map_manager):
        if not self.load:
            return False
        base_x = 0 if map_manager.player1 is self.team else map_manager.width - 1
        if self.position[0] != base_x:
            return False

        total_points = 0
        for item in list(self.load):
            try:
                total_points += getattr(item, 'value', 0)
                # Register the type of collected item
                item_type = item.__class__.__name__
                self.team.register_item(item_type)
            except Exception:
                pass
        try:
            self.team.add_points(total_points)
        except Exception:
            pass
        
        # Play unload sound if available
        if self.unload_sound is not None:
            try:
                self.unload_sound.play()
            except Exception:
                pass
        
        # Clear load
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