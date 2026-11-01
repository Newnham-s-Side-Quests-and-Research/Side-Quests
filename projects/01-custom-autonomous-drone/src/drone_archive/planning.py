"""Deterministic four direction path planning on a synthetic occupancy grid."""
import heapq

class PlanningError(ValueError):
    pass

def _point(value, label, width, height):
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise PlanningError(f'{label} must contain two integer coordinates')
    x, y = value
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (x, y)):
        raise PlanningError(f'{label} must contain two integer coordinates')
    if not (0 <= x < width and 0 <= y < height):
        raise PlanningError(f'{label} is outside the grid')
    return (x, y)

def plan_grid(width, height, blocked, start, goal):
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in (width, height)):
        raise PlanningError('Grid dimensions must be positive integers')
    if width * height > 1000000:
        raise PlanningError('Grid exceeds the supported size')
    if not isinstance(blocked, (list, tuple, set, frozenset)):
        raise PlanningError('Blocked cells must be a collection')
    obstacles = {_point(p, 'Blocked cell', width, height) for p in blocked}
    start = _point(start, 'Start', width, height)
    goal = _point(goal, 'Goal', width, height)
    if start in obstacles or goal in obstacles:
        raise PlanningError('Start and goal must be clear')
    def heuristic(point):
        return abs(point[0] - goal[0]) + abs(point[1] - goal[1])
    queue = [(heuristic(start), 0, start)]
    costs = {start: 0}
    previous = {}
    while queue:
        _, cost, current = heapq.heappop(queue)
        if cost != costs[current]:
            continue
        if current == goal:
            route = [current]
            while current in previous:
                current = previous[current]
                route.append(current)
            return list(reversed(route))
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            neighbour = (current[0] + dx, current[1] + dy)
            if not (0 <= neighbour[0] < width and 0 <= neighbour[1] < height) or neighbour in obstacles:
                continue
            next_cost = cost + 1
            if next_cost < costs.get(neighbour, float('inf')):
                costs[neighbour] = next_cost
                previous[neighbour] = current
                heapq.heappush(queue, (next_cost + heuristic(neighbour), next_cost, neighbour))
    return None
