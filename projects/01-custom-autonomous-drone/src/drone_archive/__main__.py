"""Command line entry point for local evidence and simulation checks."""
import argparse
import json
import platform
import sys
from pathlib import Path
from .evidence import EvidenceError, hash_file, publication_manifest, verify_files
from .simulation import SimulationError, simulate
from .estimation import EstimationError
from .replay import estimate_scenario
from .planning import PlanningError, plan_grid
from .telemetry import TelemetryError, build_snapshot
from .vision import VisionError, detect_regions
from .mission import run_demonstration
from .closed_loop import simulate_closed_loop
from .dashboard import LocalDashboard
from .mission3d import MissionError, run_mission
from .point_mass import simulate_point_mass
from .rigid_body import simulate_rigid_body
from .flight3d import run_controlled_flight
from .c_controller import load_position_controller

def main(argv=None):
    parser = argparse.ArgumentParser(description='Drone evidence and illustrative signal simulation')
    commands = parser.add_subparsers(dest='command', required=True)
    inventory = commands.add_parser('hash', help='Calculate an artefact hash')
    inventory.add_argument('file')
    register = commands.add_parser('validate', help='Validate an evidence register')
    register.add_argument('register')
    check = commands.add_parser('verify', help='Compare artefacts with recorded hashes')
    check.add_argument('register')
    check.add_argument('--root', required=True)
    model = commands.add_parser('simulate', help='Run the illustrative model')
    model.add_argument('config')
    model.add_argument('--output', required=True)
    estimation = commands.add_parser('estimate', help='Replay simulated sensors through the vertical filter')
    estimation.add_argument('config')
    estimation.add_argument('--output', required=True)
    planning = commands.add_parser('plan', help='Plan a route on a synthetic grid')
    planning.add_argument('grid')
    planning.add_argument('--output', required=True)
    telemetry = commands.add_parser('telemetry', help='Create simulated telemetry snapshots')
    telemetry.add_argument('config')
    telemetry.add_argument('--output', required=True)
    vision = commands.add_parser('vision', help='Detect regions in a synthetic image')
    vision.add_argument('image')
    vision.add_argument('--output', required=True)
    demo = commands.add_parser('demo', help='Run the synthetic integration demonstration')
    demo.add_argument('--scenario', required=True)
    demo.add_argument('--grid', required=True)
    demo.add_argument('--image', required=True)
    demo.add_argument('--output', required=True)
    closed = commands.add_parser('closed', help='Run the synthetic closed loop vertical model')
    closed.add_argument('config')
    closed.add_argument('--output', required=True)
    spatial = commands.add_parser('mission3d', help='Run a synthetic three dimensional kinematic mission')
    spatial.add_argument('config')
    spatial.add_argument('--output', required=True)
    point_mass = commands.add_parser('point-mass', help='Run a synthetic level point mass model')
    point_mass.add_argument('config')
    point_mass.add_argument('--output', required=True)
    rigid_body = commands.add_parser('rigid-body', help='Run a synthetic rigid body model')
    rigid_body.add_argument('config')
    rigid_body.add_argument('--output', required=True)
    controlled = commands.add_parser('controlled-flight', help='Run a synthetic controlled three dimensional flight')
    controlled.add_argument('config')
    controlled.add_argument('--output', required=True)
    controlled.add_argument('--controller-library', help='Optional shared library built from the C controller')
    dashboard = commands.add_parser('dashboard', help='Open a local synthetic telemetry dashboard')
    dashboard.add_argument('config')
    dashboard.add_argument('--port', type=int, default=8766)
    args = parser.parse_args(argv)
    try:
        if args.command == 'dashboard':
            if not 0 <= args.port <= 65535:
                raise ValueError('Port must be between 0 and 65535')
            config = json.loads(Path(args.config).read_text(encoding='utf-8'))
            with LocalDashboard(config, args.port) as server:
                print(f'Synthetic dashboard: http://127.0.0.1:{server.server_port}', flush=True)
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    pass
        elif args.command == 'hash':
            print(hash_file(args.file))
        elif args.command == 'validate':
            data = json.loads(Path(args.register).read_text(encoding='utf-8'))
            print(json.dumps(publication_manifest(data), indent=2))
        elif args.command == 'verify':
            data = json.loads(Path(args.register).read_text(encoding='utf-8'))
            results = verify_files(data, args.root)
            print(json.dumps(results, indent=2))
            return 0 if results and all(item['status'] == 'matched' for item in results) else 1
        elif args.command == 'mission3d':
            config = json.loads(Path(args.config).read_text(encoding='utf-8'))
            result = run_mission(config)
            result['python_version'] = platform.python_version()
            destination = Path(args.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
            print(f"Mission status: {result['status']}")
            return 0 if result['status'] == 'complete' else 1
        elif args.command == 'demo':
            config = json.loads(Path(args.scenario).read_text(encoding='utf-8'))
            grid = json.loads(Path(args.grid).read_text(encoding='utf-8'))
            image = json.loads(Path(args.image).read_text(encoding='utf-8'))
            result = run_demonstration(config, grid, image)
            result['python_version'] = platform.python_version()
            destination = Path(args.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
            print(f"Wrote {len(result['telemetry'])} synthetic snapshots to {destination}")
        elif args.command == 'vision':
            image = json.loads(Path(args.image).read_text(encoding='utf-8'))
            if not isinstance(image, dict) or image.get('schema_version') != 1:
                raise VisionError('Image must use schema version 1')
            regions = detect_regions(image.get('pixels'), image.get('threshold'), image.get('minimum_area'))
            result = {'model': 'synthetic grayscale regions', 'image': image, 'regions': regions, 'limitations': ['Not a camera model', 'Not a trained detector', 'Not validated on real imagery']}
            destination = Path(args.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
            print(f'Detected {len(regions)} regions')
        elif args.command == 'plan':
            grid = json.loads(Path(args.grid).read_text(encoding='utf-8'))
            if not isinstance(grid, dict) or grid.get('schema_version') != 1:
                raise PlanningError('Grid must use schema version 1')
            route = plan_grid(grid.get('width'), grid.get('height'), grid.get('blocked'), grid.get('start'), grid.get('goal'))
            result = {'model': 'synthetic two dimensional grid', 'grid': grid, 'route': route, 'limitations': ['No aircraft dynamics or geographic coordinates', 'Not a flight trajectory or safety guarantee']}
            destination = Path(args.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
            print('Route found' if route is not None else 'No route found')
            return 0 if route is not None else 1
        else:
            config = json.loads(Path(args.config).read_text(encoding='utf-8'))
            if args.command == 'controlled-flight':
                controller = load_position_controller(args.controller_library) if args.controller_library else None
                result = run_controlled_flight(config, position_controller=controller)
            elif args.command == 'rigid-body':
                result = simulate_rigid_body(config)
            elif args.command == 'point-mass':
                result = simulate_point_mass(config)
            elif args.command == 'estimate':
                result = estimate_scenario(config)
            elif args.command == 'closed':
                result = simulate_closed_loop(config)
            else:
                result = simulate(config)
                if args.command == 'telemetry':
                    result['snapshots'] = [build_snapshot(sample) for sample in result.pop('trace')]
                    result['trace'] = result.pop('snapshots')
            result['python_version'] = platform.python_version()
            destination = Path(args.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
            print(f"Wrote {len(result['trace'])} simulated steps to {destination}")
    except (OSError, ValueError, EvidenceError, SimulationError, EstimationError, PlanningError, TelemetryError, VisionError, MissionError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
