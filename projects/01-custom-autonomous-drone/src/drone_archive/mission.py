"""Run a synthetic integration demonstration without aircraft control."""
from .planning import PlanningError, plan_grid
from .replay import estimate_scenario
from .simulation import simulate
from .telemetry import build_snapshot
from .vision import VisionError, detect_regions

def run_demonstration(config, grid, image):
    if not isinstance(grid, dict) or grid.get('schema_version') != 1:
        raise PlanningError('Grid must use schema version 1')
    if not isinstance(image, dict) or image.get('schema_version') != 1:
        raise VisionError('Image must use schema version 1')
    simulation = simulate(config)
    estimate = estimate_scenario(config, simulation)
    route = plan_grid(grid.get('width'), grid.get('height'), grid.get('blocked'), grid.get('start'), grid.get('goal'))
    regions = detect_regions(image.get('pixels'), image.get('threshold'), image.get('minimum_area'))
    snapshots = [build_snapshot(sample) for sample in simulation['trace']]
    return {'model': 'synthetic integration demonstration', 'configuration': config,
            'grid': grid, 'image': image, 'estimator_settings': estimate['estimator_settings'],
            'route': route, 'image_regions': regions, 'simulation_trace': simulation['trace'],
            'estimation': estimate['trace'], 'telemetry': snapshots,
            'limitations': ['Components are not connected in a closed flight control loop',
                            'Image, map and signals are synthetic and do not represent a camera or real position',
                            'No physical aircraft, networking or flight safety is verified']}
