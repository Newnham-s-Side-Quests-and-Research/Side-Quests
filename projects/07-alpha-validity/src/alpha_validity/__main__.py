import argparse
import json
from pathlib import Path
import sys
from .evaluation import EvaluationError,evaluate


def unique(pairs):
    output={}
    for key,value in pairs:
        if key in output: raise EvaluationError(f'Duplicate field: {key}')
        output[key]=value
    return output


def main():
    parser=argparse.ArgumentParser(description='Evaluate supplied time ordered strategy observations')
    parser.add_argument('input');args=parser.parse_args()
    try:
        source=Path(args.input)
        if source.stat().st_size>10_000_000: raise EvaluationError('Input exceeds the size limit')
        data=json.loads(source.read_text(encoding='utf-8'),object_pairs_hook=unique)
        print(json.dumps(evaluate(data),indent=2,allow_nan=False))
    except (OSError,ValueError,OverflowError) as exc:
        print(str(exc),file=sys.stderr);return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
