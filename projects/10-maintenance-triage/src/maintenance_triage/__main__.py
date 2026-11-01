import argparse
import json
from pathlib import Path
import sqlite3
import sys
from .intake import IntakeError,IntakeQueue


def unique(pairs):
    output={}
    for key,value in pairs:
        if key in output: raise IntakeError(f'Duplicate field: {key}')
        output[key]=value
    return output


def main():
    parser=argparse.ArgumentParser(description='Save a maintenance report for human review')
    parser.add_argument('database');parser.add_argument('input');args=parser.parse_args()
    try:
        source=Path(args.input)
        if source.stat().st_size>1_000_000:raise IntakeError('Input exceeds the size limit')
        data=json.loads(source.read_text(encoding='utf-8'),object_pairs_hook=unique)
        if not isinstance(data,dict) or set(data)!={'priority_phrases','report'}:raise IntakeError('Invalid input fields')
        print(json.dumps(IntakeQueue(args.database,data['priority_phrases']).submit(data['report']),allow_nan=False))
    except (OSError,ValueError,sqlite3.Error) as exc:
        print(str(exc),file=sys.stderr);return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
