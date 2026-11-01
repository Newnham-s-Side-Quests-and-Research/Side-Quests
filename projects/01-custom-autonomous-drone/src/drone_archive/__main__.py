"""Command line entry point for local evidence and simulation checks."""
import argparse
import json
import platform
import sys
from pathlib import Path
from .evidence import EvidenceError, hash_file, publication_manifest, verify_files
from .simulation import SimulationError, simulate

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
        else:
            config = json.loads(Path(args.config).read_text(encoding='utf-8'))
            result = simulate(config)
            result['python_version'] = platform.python_version()
            destination = Path(args.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
            print(f"Wrote {len(result['trace'])} simulated steps to {destination}")
    except (OSError, ValueError, EvidenceError, SimulationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
