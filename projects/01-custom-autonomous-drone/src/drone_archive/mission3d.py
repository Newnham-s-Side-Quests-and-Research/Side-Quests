"""Plan and replay a synthetic mission on a bounded three dimensional grid.

The vehicle moves kinematically. This module does not model attitude or motors.
"""
import heapq
import math

class MissionError(ValueError):
    pass

def _point(value, label, size):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise MissionError(f'{label} must have three integer coordinates')
    if any(isinstance(x, bool) or not isinstance(x, int) for x in value):
        raise MissionError(f'{label} must have three integer coordinates')
    point = tuple(value)
    if not all(0 <= point[i] < size[i] for i in range(3)):
        raise MissionError(f'{label} is outside the grid')
    return point

def _positive(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MissionError(f'{label} must be a finite positive number')
    try:
        valid = math.isfinite(value) and value > 0
    except OverflowError:
        valid = False
    if not valid:
        raise MissionError(f'{label} must be a finite positive number')
    return float(value)

def plan_voxels(size, blocked, start, goal):
    if not isinstance(size, (list, tuple)) or len(size) != 3:
        raise MissionError('Grid size must have three positive integer dimensions')
    if any(isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in size):
        raise MissionError('Grid size must have three positive integer dimensions')
    size = tuple(size)
    if math.prod(size) > 250000:
        raise MissionError('Grid exceeds the supported size')
    if not isinstance(blocked, (list, tuple, set, frozenset)):
        raise MissionError('Blocked cells must be a collection')
    occupied = {_point(value, 'Blocked cell', size) for value in blocked}
    start, goal = _point(start, 'Start', size), _point(goal, 'Goal', size)
    if start in occupied or goal in occupied:
        raise MissionError('Start and goal must be clear')
    def distance(point):
        return sum(abs(point[i] - goal[i]) for i in range(3))
    costs = {start: 0}
    previous = {}
    queue = [(distance(start), 0, start)]
    directions = ((-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1))
    while queue:
        _, cost, point = heapq.heappop(queue)
        if cost != costs[point]:
            continue
        if point == goal:
            route = [point]
            while point in previous:
                point = previous[point]
                route.append(point)
            return list(reversed(route))
        for delta in directions:
            neighbour = tuple(point[i] + delta[i] for i in range(3))
            if any(not 0 <= neighbour[i] < size[i] for i in range(3)) or neighbour in occupied:
                continue
            candidate = cost + 1
            if candidate < costs.get(neighbour, float('inf')):
                costs[neighbour] = candidate
                previous[neighbour] = point
                heapq.heappush(queue, (candidate + distance(neighbour), candidate, neighbour))
    return None

def run_mission(config):
    if not isinstance(config, dict) or config.get('schema_version') != 1:
        raise MissionError('Mission configuration must use schema version 1')
    grid = config.get('grid')
    if not isinstance(grid, dict):
        raise MissionError('A grid is required')
    route = plan_voxels(grid.get('size'), grid.get('blocked'), grid.get('start'), grid.get('goal'))
    spacing = _positive(config.get('cell_size_m'), 'Cell size')
    speed = _positive(config.get('speed_m_s'), 'Speed')
    timestep = _positive(config.get('dt_seconds'), 'Timestep')
    steps = config.get('max_steps')
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 100000:
        raise MissionError('max_steps must be an integer between 1 and 100000')
    dropout = config.get('position_dropout')
    if dropout is not None:
        if not isinstance(dropout, dict):
            raise MissionError('Position dropout must be an object')
        start, end = dropout.get('start'), dropout.get('end')
        if any(isinstance(x, bool) or not isinstance(x, int) for x in (start, end)) or not 0 <= start < end <= steps:
            raise MissionError('Position dropout must be a valid half open step interval')
    limitations = ['Synthetic grid and kinematic motion only',
                   'No attitude, motor, wind, battery or three dimensional flight dynamics',
                   'Position loss pauses the model and is not a flight safety procedure',
                   'No camera perception or physical aircraft has been verified']
    if route is None:
        return {'model': 'synthetic three dimensional kinematic mission', 'configuration': config,
                'status': 'no route', 'route': None, 'trace': [], 'limitations': limitations}
    position = tuple(axis * spacing for axis in route[0])
    waypoint = 1
    trace = []
    total_distance = 0.0
    for step in range(steps):
        if waypoint >= len(route):
            break
        missing = dropout is not None and dropout['start'] <= step < dropout['end']
        before = position
        target = tuple(axis * spacing for axis in route[waypoint])
        displacement = tuple(target[i] - position[i] for i in range(3))
        distance = math.sqrt(sum(x * x for x in displacement))
        if missing:
            moved = 0.0
            state = 'position unavailable'
        else:
            moved = min(distance, speed * timestep)
            if distance > 0:
                position = tuple(position[i] + displacement[i] * moved / distance for i in range(3))
            if moved >= distance:
                position = target
                waypoint += 1
            state = 'moving'
        total_distance += moved
        if not all(math.isfinite(x) for x in (*position, total_distance)):
            raise MissionError(f'Nonfinite mission state at step {step}')
        trace.append({'step': step, 'time_s': step * timestep, 'position_before_m': before,
                      'position_after_m': position, 'target_m': target,
                      'position_available': not missing, 'state': state, 'distance_m': moved})
    status = 'complete' if waypoint >= len(route) else 'incomplete'
    return {'model': 'synthetic three dimensional kinematic mission', 'configuration': config,
            'status': status, 'route': route, 'trace': trace, 'distance_m': total_distance,
            'final_position_m': position, 'limitations': limitations}
