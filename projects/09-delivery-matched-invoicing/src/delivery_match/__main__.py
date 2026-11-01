import argparse
import json
from pathlib import Path
import sys
from .matching import MatchError, match


def unique(pairs):
    output = {}
    for key, value in pairs:
        if key in output: raise MatchError(f'Duplicate field: {key}')
        output[key] = value
    return output


def main():
    parser=argparse.ArgumentParser(description='Compare an invoice with accepted deliveries')
    parser.add_argument('input')
    args=parser.parse_args()
    try:
        source=Path(args.input)
        if source.stat().st_size > 10_000_000: raise MatchError('Input exceeds the size limit')
        data=json.loads(source.read_text(encoding='utf-8'),object_pairs_hook=unique)
        if not isinstance(data,dict) or set(data) != {'order','receipts','invoice'}: raise MatchError('Invalid input fields')
        print(json.dumps(match(data['order'],data['receipts'],data['invoice']),indent=2,allow_nan=False))
    except (OSError,ValueError,OverflowError) as exc:
        print(str(exc),file=sys.stderr); return 2
    return 0


if __name__=='__main__': raise SystemExit(main())
