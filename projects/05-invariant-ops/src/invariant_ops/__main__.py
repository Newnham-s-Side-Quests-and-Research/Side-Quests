import argparse
import json
from pathlib import Path
import sqlite3
import sys
from .store import WorkflowError, WorkflowStore


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise WorkflowError(f'Duplicate field: {key}')
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description='Apply an order workflow command')
    parser.add_argument('database')
    parser.add_argument('command')
    args = parser.parse_args()
    try:
        command_path = Path(args.command)
        if command_path.stat().st_size > 1_000_000:
            raise WorkflowError('Command exceeds the size limit')
        command = json.loads(command_path.read_text(encoding='utf-8'), object_pairs_hook=unique)
        result = WorkflowStore(args.database).apply(command)
        print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
