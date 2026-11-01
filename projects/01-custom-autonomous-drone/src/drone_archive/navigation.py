"""Connect a voxel route to the synthetic controlled rigid body model."""
import math
from .flight3d import run_controlled_flight
from .mission3d import plan_voxels
from .point_mass import _finite, _vector
from .simulation import SimulationError


def _intersects_box(start, end, low, high):
    enter, leave = 0.0, 1.0
    for axis in range(3):
        direction = end[axis] - start[axis]
        if direction == 0:
            if start[axis] < low[axis] or start[axis] > high[axis]:
                return False
            continue
        first = (low[axis] - start[axis]) / direction
        second = (high[axis] - start[axis]) / direction
        enter = max(enter, min(first, second))
        leave = min(leave, max(first, second))
        if enter > leave:
            return False
    return True


def run_navigation(config, position_controller=None):
    if not isinstance(config, dict) or config.get('schema_version') != 1:
        raise SimulationError('Navigation configuration must use schema version 1')
    grid, flight = config.get('grid'), config.get('flight')
    if not isinstance(grid, dict) or not isinstance(flight, dict):
        raise SimulationError('Grid and flight configurations are required')
    route = plan_voxels(grid.get('size'), grid.get('blocked'), grid.get('start'), grid.get('goal'))
    spacing = _finite(config.get('cell_size_m'), 'cell_size_m', 0)
    origin = _vector(config.get('origin_m'), 'origin_m')
    tolerance = _finite(config.get('waypoint_tolerance_m'), 'waypoint_tolerance_m', 0)
    speed_limit = _finite(config.get('waypoint_speed_m_s'), 'waypoint_speed_m_s', 0)
    dwell = config.get('waypoint_dwell_steps')
    if spacing <= 0 or tolerance <= 0 or tolerance >= spacing / 2 or speed_limit <= 0:
        raise SimulationError('Spacing, tolerance and speed must be positive and tolerance less than half a cell')
    if isinstance(dwell, bool) or not isinstance(dwell, int) or dwell < 1 or dwell > 10000:
        raise SimulationError('Waypoint dwell must be between 1 and 10000 steps')
    limitations = ['Synthetic static voxel map and point vehicle only',
                   'Obstacle checks use swept point segments and do not include the aircraft footprint',
                   'Horizontal state and attitude are ideal model values',
                   'Waypoint arrival uses ideal simulated position and velocity',
                   'A final ground contact segment is not separately checked for blocked cells',
                   'No camera perception, changing obstacles, battery or physical aircraft validation',
                   'A simulated route is not a safe flight trajectory']
    if route is None:
        return {'model': 'synthetic controlled voxel mission', 'status': 'no route', 'route': None,
                'waypoint_events': [], 'flight': None, 'limitations': limitations}
    points = [[origin[i] + spacing * cell[i] for i in range(3)] for cell in route]
    if any(point[2] <= 0 for point in points):
        raise SimulationError('All waypoints must be above ground')
    plant = flight.get('plant')
    if not isinstance(plant, dict):
        raise SimulationError('Flight plant is required')
    initial = _vector(plant.get('initial_position_m'), 'initial_position_m')
    if math.dist(initial, points[0]) > 1e-9:
        raise SimulationError('Initial position must match the start cell centre')
    low_bound = [origin[i] - spacing / 2 for i in range(3)]
    high_bound = [origin[i] + spacing * (grid['size'][i] - 0.5) for i in range(3)]
    boxes = []
    for cell in grid['blocked']:
        centre = [origin[i] + spacing * cell[i] for i in range(3)]
        boxes.append((list(cell), [x - spacing / 2 for x in centre], [x + spacing / 2 for x in centre]))
    index = 0 if len(points) == 1 else 1
    consecutive = 0
    completed = False
    events = []

    def target(state):
        nonlocal index, consecutive, completed
        point = points[index]
        within = math.dist(state['position_m'], point) <= tolerance
        slow = math.sqrt(sum(item * item for item in state['velocity_m_s'])) <= speed_limit
        consecutive = consecutive + 1 if within and slow else 0
        if consecutive >= dwell and not completed:
            events.append({'waypoint_index': index, 'cell': list(route[index]),
                           'time_s': state['time_s'], 'position_m': state['position_m'].copy()})
            consecutive = 0
            if index == len(points) - 1:
                completed = True
            else:
                index += 1
        return points[index]

    def check_segment(start, end):
        if any(end[i] < low_bound[i] or end[i] > high_bound[i] for i in range(3)):
            return {'type': 'geofence_exit'}
        for cell, low, high in boxes:
            if _intersects_box(start, end, low, high):
                return {'type': 'obstacle_contact', 'cell': cell}
        return None

    def stop(state):
        previous = state['previous_position_m'] or state['position_m']
        return check_segment(previous, state['position_m'])

    report = run_controlled_flight(flight, position_controller=position_controller,
                                   target_provider=target, stop_condition=stop)
    event = report['terminal_event']
    if event is None and report['trace']:
        event = check_segment(report['trace'][-1]['position_m'], report['final']['position_m'])
        if event:
            event['time_s'] = len(report['trace']) * flight['plant']['dt_seconds']
            report['terminal_event'] = event
    status = event['type'] if event else ('complete' if completed else 'incomplete')
    report['limitations'].remove('No route planner, collision avoidance or physical aircraft is connected')
    report['limitations'].append('A static route is connected but collision avoidance is not implemented')
    return {'model': 'synthetic controlled voxel mission', 'status': status, 'route': [list(cell) for cell in route],
            'waypoints_m': points, 'waypoint_events': events, 'flight': report, 'limitations': limitations}
