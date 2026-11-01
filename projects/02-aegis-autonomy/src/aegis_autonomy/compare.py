import argparse
import json
from pathlib import Path
import sys
from .__main__ import _invalid_constant,_object
from .comparison import compare
from .monitor import MonitoringError


def main():
    parser=argparse.ArgumentParser(description='Compare monitors on labelled observations')
    parser.add_argument('input');args=parser.parse_args()
    try:
        source=Path(args.input)
        if source.stat().st_size>10_000_000:raise MonitoringError('Input exceeds the size limit')
        data=json.loads(source.read_text(encoding='utf-8'),object_pairs_hook=_object,parse_constant=_invalid_constant)
        print(json.dumps(compare(data),indent=2,allow_nan=False))
    except (OSError,ValueError,OverflowError) as exc:
        print(str(exc),file=sys.stderr);return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
