import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .monitor import MonitoringError
from .runner import evaluate_run


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MonitoringError(f'Duplicate field: {key}')
        result[key] = value
    return result


def _invalid_constant(value):
    raise MonitoringError(f'Invalid numeric constant: {value}')


def main():
    parser = argparse.ArgumentParser(description='Evaluate a sequence of state trust observations')
    parser.add_argument('input')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    temporary = None
    try:
        source = Path(args.input)
        if source.stat().st_size > 10_000_000:
            raise MonitoringError('Input exceeds the size limit')
        data = json.loads(source.read_text(encoding='utf-8'), object_pairs_hook=_object, parse_constant=_invalid_constant)
        result = evaluate_run(data)
        destination = Path(args.output).resolve()
        if destination == source.resolve():
            raise MonitoringError('Output must not overwrite the input')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, destination)
        temporary = None
        print(f"Processed {result['observations_processed']} observations")
    except (OSError, ValueError, OverflowError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
