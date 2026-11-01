import argparse
import json
from pathlib import Path
import sys
from .audit import AuditError, audit


def unique(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise AuditError(f'Duplicate field: {key}')
        output[key] = value
    return output


def main():
    parser = argparse.ArgumentParser(description='Compare a freight invoice with a rate card')
    parser.add_argument('input')
    args = parser.parse_args()
    try:
        source = Path(args.input)
        if source.stat().st_size > 10_000_000:
            raise AuditError('Input exceeds the size limit')
        data = json.loads(source.read_text(encoding='utf-8'), object_pairs_hook=unique)
        if not isinstance(data, dict) or set(data) != {'shipment','rate_cards','invoice'}:
            raise AuditError('Invalid input fields')
        print(json.dumps(audit(data['shipment'], data['rate_cards'], data['invoice']), indent=2, allow_nan=False))
    except (OSError, ValueError, OverflowError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
