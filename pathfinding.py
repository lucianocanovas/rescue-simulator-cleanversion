from typing import Any
from collections import deque
from classes.Item import Item, Person
from classes.Mine import Mine

def in_bounds(grid: list[list[Any]], position: tuple[int, int]):
    x, y = position
    return 0 <= x < len(grid) and 0 <= y < len(grid[0])

def neighbors(grid: list[list[Any]], position: tuple[int, int]):
    x, y = position
    results = []
    for delta_x, delta_y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        neighbor = (x + delta_x, y + delta_y)
        if in_bounds(grid, neighbor):
            results.append(neighbor)
    return results

def bfs(grid: list[list[Any]], start: tuple[int, int], goal: tuple[int, int]):
    from collections import deque

    if start == goal:
        return [start]

    queue = deque([start])
    came_from = {start: None}

    while queue:
        current = queue.popleft()
        for neighbor in neighbors(grid, current):
            if neighbor in came_from:
                continue
            came_from[neighbor] = current
            if neighbor == goal:
                # Reconstruct path
                path = [goal]
                current_position = current
                while current_position is not None:
                    path.append(current_position)
                    current_position = came_from[current_position]
                path.reverse()
                return path
            queue.append(neighbor)
    return None

def find_nearest(grid: list[list[Any]], start: tuple[int, int], danger_zones: list[list[bool]], only_persons: bool = False, exclude_persons: bool = False):
    queue = deque([start])
    came_from = {start: None}

    # Helper function: checks if a cell is walkable (safe and not a mine)
    def walkable(position):
        cell_x, cell_y = position
        if danger_zones and danger_zones[cell_x][cell_y]:
            return False
        grid_object = grid[cell_x][cell_y]
        # Don't allow entering mines; items are traversable objectives
        if Mine is not None and isinstance(grid_object, Mine):
            return False
        # Allow empty cells or cells with items
        return True
    
    # Helper function: checks if an object is the target
    def is_target(grid_object):
        if only_persons:
            # Only persons
            return Person is not None and isinstance(grid_object, Person)
        elif exclude_persons:
            # Items but NOT persons
            return Item is not None and isinstance(grid_object, Item) and not isinstance(grid_object, Person)
        else:
            # Any Item
            return Item is not None and isinstance(grid_object, Item)

    # If start cell contains the target, return it immediately
    start_x, start_y = start
    if is_target(grid[start_x][start_y]):
        return [start]

    while queue:
        current = queue.popleft()
        for neighbor in neighbors(grid, current):
            if neighbor in came_from:
                continue
            if not walkable(neighbor):
                continue
            came_from[neighbor] = current
            neighbor_x, neighbor_y = neighbor
            if is_target(grid[neighbor_x][neighbor_y]):
                # Reconstruct path
                path = [neighbor]
                current_position = current
                while current_position is not None:
                    path.append(current_position)
                    current_position = came_from[current_position]
                path.reverse()
                return path
            queue.append(neighbor)
    return None

def find_farthest(grid: list[list[Any]], start: tuple[int, int], danger_zones: list[list[bool]], only_persons: bool = False, exclude_persons: bool = False):
    queue = deque([start])
    came_from = {start: None}

    def walkable(position):
        cell_x, cell_y = position
        if danger_zones and danger_zones[cell_x][cell_y]:
            return False
        grid_object = grid[cell_x][cell_y]
        if Mine is not None and isinstance(grid_object, Mine):
            return False
        return True

    def is_target(grid_object):
        if only_persons:
            # Only persons
            return Person is not None and isinstance(grid_object, Person)
        elif exclude_persons:
            # Items but NOT persons
            return Item is not None and isinstance(grid_object, Item) and not isinstance(grid_object, Person)
        else:
            # Any Item
            return Item is not None and isinstance(grid_object, Item)

    last_target = None
    start_x, start_y = start
    if is_target(grid[start_x][start_y]):
        last_target = start

    while queue:
        current = queue.popleft()
        for neighbor in neighbors(grid, current):
            if neighbor in came_from:
                continue
            if not walkable(neighbor):
                continue
            came_from[neighbor] = current
            neighbor_x, neighbor_y = neighbor
            if is_target(grid[neighbor_x][neighbor_y]):
                last_target = neighbor
            queue.append(neighbor)

    if last_target is None:
        return None

    # Reconstruct path to the farthest found target
    path = [last_target]
    current_position = came_from[last_target]
    while current_position is not None:
        path.append(current_position)
        current_position = came_from[current_position]
    path.reverse()
    return path

def find_path_to_column(grid: list[list[Any]], start: tuple[int, int], target_x: int, danger_zones: list[list[bool]]):
    queue = deque([start])
    came_from = {start: None}

    def walkable(position):
        cell_x, cell_y = position
        if danger_zones and danger_zones[cell_x][cell_y]:
            return False
        grid_object = grid[cell_x][cell_y]
        if Mine is not None and isinstance(grid_object, Mine):
            return False
        # Allow empty cells, cells with items, or even the vehicle's own cell
        return True

    # If already in target column and walkable, return start path
    if start[0] == target_x and walkable(start):
        return [start]

    while queue:
        current = queue.popleft()
        for neighbor in neighbors(grid, current):
            if neighbor in came_from:
                continue
            if not walkable(neighbor):
                continue
            came_from[neighbor] = current
            if neighbor[0] == target_x:
                # Reconstruct path
                path = [neighbor]
                current_position = current
                while current_position is not None:
                    path.append(current_position)
                    current_position = came_from[current_position]
                path.reverse()
                return path
            queue.append(neighbor)
    return None