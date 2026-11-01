import argparse
import json
from pathlib import Path
import sys
from .retrieval import RetrievalError, SourceIndex


def unique(pairs):
    output = {}
    for key, value in pairs:
        if key in output: raise RetrievalError(f'Duplicate field: {key}')
        output[key] = value
    return output


def main():
    parser=argparse.ArgumentParser(description='Search authorised source passages')
    parser.add_argument('input')
    args=parser.parse_args()
    try:
        source=Path(args.input)
        if source.stat().st_size > 10_000_000: raise RetrievalError('Input exceeds the size limit')
        data=json.loads(source.read_text(encoding='utf-8'),object_pairs_hook=unique)
        if not isinstance(data,dict) or set(data) != {'sources','roles','query'}: raise RetrievalError('Invalid input fields')
        print(json.dumps({'matches':SourceIndex(data['sources']).search(data['query'],data['roles'])},indent=2,ensure_ascii=False,allow_nan=False))
    except (OSError,ValueError,OverflowError) as exc:
        print(str(exc),file=sys.stderr); return 2
    return 0


if __name__=='__main__': raise SystemExit(main())
