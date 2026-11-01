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
    args = parser.parse_args(argv)
    try:
        if args.command == 'hash':
            print(hash_file(args.file))
        elif args.command == 'validate':
            data = json.loads(Path(args.register).read_text(encoding='utf-8'))
            print(json.dumps(publication_manifest(data), indent=2))
        elif args.command == 'verify':
            data = json.loads(Path(args.register).read_text(encoding='utf-8'))
            results = verify_files(data, args.root)
            print(json.dumps(results, indent=2))
            return 0 if results and all(item['status'] == 'matched' for item in results) else 1
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
            if args.command == 'estimate':
                result = estimate_scenario(config)
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
    except (OSError, ValueError, EvidenceError, SimulationError, EstimationError, PlanningError, TelemetryError, VisionError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
