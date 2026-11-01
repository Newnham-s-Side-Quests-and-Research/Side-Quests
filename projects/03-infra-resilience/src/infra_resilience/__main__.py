import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .diagnosis import DiagnosisError, diagnose


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DiagnosisError(f'Duplicate field: {key}')
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description='Rank candidate causes from equipment events')
    parser.add_argument('input')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    temporary = None
    try:
        source = Path(args.input)
        if source.stat().st_size > 10_000_000:
            raise DiagnosisError('Input exceeds the size limit')
        data = json.loads(source.read_text(encoding='utf-8'), object_pairs_hook=unique)
        result = diagnose(data)
        target = Path(args.output).resolve()
        if target == source.resolve():
            raise DiagnosisError('Output must not overwrite input')
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, target)
        temporary = None
        print('Diagnosis:', result['status'])
    except (OSError, ValueError, OverflowError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
