from typing import Any

def in_bounds(grid: list[list[Any]], position: tuple[int, int]):
    x, y = position
    return 0 <= x < len(grid) and 0 <= y < len(grid[0])

def neighbors(grid: list[list[Any]], position: tuple[int, int]):
    x, y = position
    results = []
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        neighbor = (x + dx, y + dy)
        if in_bounds(grid, neighbor):
            results.append(neighbor)
    return results

def bfs(grid: list[list[Any]], start: tuple[int, int], goal: tuple[int, int]):
    # Simple BFS that returns path from start to goal as list of positions
    from collections import deque

    if start == goal:
        return [start]

    q = deque([start])
    came_from = {start: None}

    while q:
        current = q.popleft()
        for nbr in neighbors(grid, current):
            if nbr in came_from:
                continue
            came_from[nbr] = current
            if nbr == goal:
                # reconstruct path
                path = [goal]
                cur = current
                while cur is not None:
                    path.append(cur)
                    cur = came_from[cur]
                path.reverse()
                return path
            q.append(nbr)
    return None


def find_nearest_item(grid: list[list[Any]], start: tuple[int, int], danger_zones: list[list[bool]]):
    """BFS from start over safe cells (danger_zones False) until an Item is found.
    Returns path to the item (including start and goal) or None if none reachable.
    """
    from collections import deque
    try:
        from classes.Item import Item
        from classes.Mine import Mine
    except Exception:
        Item = None
        Mine = None

    q = deque([start])
    came_from = {start: None}

    # helper to check if a cell is walkable (safe and not a mine)
    def walkable(pos):
        x, y = pos
        # out of bounds handled by neighbors
        if danger_zones and danger_zones[x][y]:
            return False
        obj = grid[x][y]
        # can't walk into Mine or a Vehicle (vehicle type unknown here),
        # but items are walkable targets
        if Mine is not None and isinstance(obj, Mine):
            return False
        # allow empty or items
        return True

    # If start cell contains an item, return it immediately
    sx, sy = start
    if Item is not None and isinstance(grid[sx][sy], Item):
        return [start]

    while q:
        current = q.popleft()
        for nbr in neighbors(grid, current):
            if nbr in came_from:
                continue
            if not walkable(nbr):
                continue
            came_from[nbr] = current
            x, y = nbr
            if Item is not None and isinstance(grid[x][y], Item):
                # reconstruct path
                path = [nbr]
                cur = current
                while cur is not None:
                    path.append(cur)
                    cur = came_from[cur]
                path.reverse()
                return path
            q.append(nbr)
    return None

def find_nearest_person(grid: list[list[Any]], start: tuple[int, int], danger_zones: list[list[bool]]):
    """BFS from start over safe cells (danger_zones False) until a Person is found.
    Returns path to the person (including start and goal) or None if none reachable.
    """
    from collections import deque
    try:
        from classes.Item import Person
        from classes.Mine import Mine
    except Exception:
        Person = None
        Mine = None

    q = deque([start])
    came_from = {start: None}

    # helper to check if a cell is walkable (safe and not a mine)
    def walkable(pos):
        x, y = pos
        # out of bounds handled by neighbors
        if danger_zones and danger_zones[x][y]:
            return False
        obj = grid[x][y]
        # can't walk into Mine or a Vehicle (vehicle type unknown here),
        # but persons are walkable targets
        if Mine is not None and isinstance(obj, Mine):
            return False
        # allow empty or persons
        return True

    # If start cell contains a person, return it immediately
    sx, sy = start
    if Person is not None and isinstance(grid[sx][sy], Person):
        return [start]

    while q:
        current = q.popleft()
        for nbr in neighbors(grid, current):
            if nbr in came_from:
                continue
            if not walkable(nbr):
                continue
            came_from[nbr] = current
            x, y = nbr
            if Person is not None and isinstance(grid[x][y], Person):
                # reconstruct path
                path = [nbr]
                cur = current
                while cur is not None:
                    path.append(cur)
                    cur = came_from[cur]
                path.reverse()
                return path
            q.append(nbr)
    return None


def find_path_to_column(grid: list[list[Any]], start: tuple[int, int], target_x: int, danger_zones: list[list[bool]]):
    """BFS to the nearest cell whose x coordinate == target_x and is walkable.
    Returns path or None.
    """
    from collections import deque
    try:
        from classes.Mine import Mine
    except Exception:
        Mine = None

    q = deque([start])
    came_from = {start: None}

    def walkable(pos):
        x, y = pos
        if danger_zones and danger_zones[x][y]:
            return False
        obj = grid[x][y]
        if Mine is not None and isinstance(obj, Mine):
            return False
        # allow empty or items or even the vehicle itself
        return True

    # If already in target column and walkable, return start path
    if start[0] == target_x and walkable(start):
        return [start]

    while q:
        current = q.popleft()
        for nbr in neighbors(grid, current):
            if nbr in came_from:
                continue
            if not walkable(nbr):
                continue
            came_from[nbr] = current
            if nbr[0] == target_x:
                # reconstruct path
                path = [nbr]
                cur = current
                while cur is not None:
                    path.append(cur)
                    cur = came_from[cur]
                path.reverse()
                return path
            q.append(nbr)
    return None