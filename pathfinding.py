from typing import Any
from collections import deque
from classes.Item import Item, Person
from classes.Mine import Mine

def in_bounds(grid: list[list[Any]], position: tuple[int, int]):
    """Comprueba si una posición (x,y) está dentro de los límites de la cuadrícula.

    Args:
        grid: la matriz que representa el mapa (indexación [x][y]).
        position: tupla (x, y) a verificar.

    Returns:
        True si la posición está dentro del rango; False en caso contrario.
    """
    x, y = position
    return 0 <= x < len(grid) and 0 <= y < len(grid[0])

def neighbors(grid: list[list[Any]], position: tuple[int, int]):
    """Devuelve las posiciones vecinas (4-direcciones) válidas desde la posición dada."""
    x, y = position
    results = []
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        neighbor = (x + dx, y + dy)
        if in_bounds(grid, neighbor):
            results.append(neighbor)
    return results

def bfs(grid: list[list[Any]], start: tuple[int, int], goal: tuple[int, int]):
    # BFS simple que devuelve la ruta desde start hasta goal como lista de posiciones
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

def find_nearest(grid: list[list[Any]], start: tuple[int, int], danger_zones: list[list[bool]], only_persons: bool = False, exclude_persons: bool = False):
    """BFS from start over safe cells (danger_zones False) until an Item (or Person if only_persons=True) is found.
    
    Args:
        grid: La matriz que representa el mapa.
        start: Posición inicial (x, y).
        danger_zones: Matriz booleana indicando zonas peligrosas.
        only_persons: Si True, busca solo Person. Si False, busca cualquier Item.
        exclude_persons: Si True, excluye Person (busca solo Items no-Person).
    
    Returns:
        Path to the item/person (including start and goal) or None if none reachable.
    """
    q = deque([start])
    came_from = {start: None}

    # Función auxiliar: comprueba si una celda es transitable (segura y no es mina)
    def walkable(pos):
        x, y = pos
        # El tratamiento de fuera de límites lo realiza `neighbors`/`in_bounds`.
        if danger_zones and danger_zones[x][y]:
            return False
        obj = grid[x][y]
        # No permitir entrar en minas; los items son objetivos transitables.
        if Mine is not None and isinstance(obj, Mine):
            return False
        # Permitir celdas vacías o con items
        return True
    
    # Función auxiliar: comprueba si un objeto es el objetivo buscado
    def is_target(obj):
        if only_persons:
            # Solo personas
            return Person is not None and isinstance(obj, Person)
        elif exclude_persons:
            # Items pero NO personas
            return Item is not None and isinstance(obj, Item) and not isinstance(obj, Person)
        else:
            # Cualquier Item
            return Item is not None and isinstance(obj, Item)

    # If start cell contains the target, return it immediately
    sx, sy = start
    if is_target(grid[sx][sy]):
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
            if is_target(grid[x][y]):
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

def find_farthest(grid: list[list[Any]], start: tuple[int, int], danger_zones: list[list[bool]], only_persons: bool = False, exclude_persons: bool = False):
    """BFS over walkable cells and return the path to the farthest reachable Item/Person.
    If the start cell is a target, it's considered but the search continues to find a farther one.
    """
    q = deque([start])
    came_from = {start: None}

    def walkable(pos):
        x, y = pos
        if danger_zones and danger_zones[x][y]:
            return False
        obj = grid[x][y]
        if Mine is not None and isinstance(obj, Mine):
            return False
        return True

    def is_target(obj):
        if only_persons:
            # Solo personas
            return Person is not None and isinstance(obj, Person)
        elif exclude_persons:
            # Items pero NO personas
            return Item is not None and isinstance(obj, Item) and not isinstance(obj, Person)
        else:
            # Cualquier Item
            return Item is not None and isinstance(obj, Item)

    last_target = None
    sx, sy = start
    if is_target(grid[sx][sy]):
        last_target = start

    while q:
        current = q.popleft()
        for nbr in neighbors(grid, current):
            if nbr in came_from:
                continue
            if not walkable(nbr):
                continue
            came_from[nbr] = current
            x, y = nbr
            if is_target(grid[x][y]):
                last_target = nbr
            q.append(nbr)

    if last_target is None:
        return None

    # reconstruct path to the farthest found target
    path = [last_target]
    cur = came_from[last_target]
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path

def find_path_to_column(grid: list[list[Any]], start: tuple[int, int], target_x: int, danger_zones: list[list[bool]]):
    """BFS to the nearest cell whose x coordinate == target_x and is walkable.
    Returns path or None.
    """
    q = deque([start])
    came_from = {start: None}

    def walkable(pos):
        x, y = pos
        if danger_zones and danger_zones[x][y]:
            return False
        obj = grid[x][y]
        if Mine is not None and isinstance(obj, Mine):
            return False
        # Permitir celdas vacías, con items o incluso la propia celda del vehículo
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