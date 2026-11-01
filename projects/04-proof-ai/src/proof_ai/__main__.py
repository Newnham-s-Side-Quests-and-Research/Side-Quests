import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .verification import VerificationError, verify_invoice


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f'Duplicate field: {key}')
        result[key] = value
    return result


def invalid_constant(value):
    raise VerificationError(f'Invalid numeric constant: {value}')


def main():
    parser = argparse.ArgumentParser(description='Check extracted invoice fields')
    parser.add_argument('input')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    temporary = None
    try:
        source = Path(args.input)
        if source.stat().st_size > 10_000_000:
            raise VerificationError('Input exceeds the size limit')
        data = json.loads(source.read_text(encoding='utf-8'), object_pairs_hook=unique_object, parse_constant=invalid_constant)
        if not isinstance(data, dict) or set(data) != {'schema_version', 'extraction', 'policy'} or type(data['schema_version']) is not int or data['schema_version'] != 1:
            raise VerificationError('Input schema is invalid')
        result = verify_invoice(data['extraction'], data['policy'])
        destination = Path(args.output).resolve()
        if destination == source.resolve():
            raise VerificationError('Output must not overwrite the input')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, destination)
        temporary = None
        print('Decision:', result['decision'])
    except (OSError, ValueError, OverflowError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
