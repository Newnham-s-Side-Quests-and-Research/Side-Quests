"""Command line entry point for a local synthetic comparison."""
import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from .adapters import FixtureAdapter
from .cases import CaseError, load_cases
from .gates import evaluate
from .runner import compare

RULES = {'version': 1, 'minimum_cases': 3, 'minimum_field_delta': 0.0, 'minimum_abstention_accuracy': 1.0}

def main(argv=None):
    parser = argparse.ArgumentParser(description='Compare deterministic workflow fixtures')
    parser.add_argument('--cases', required=True, help='Path to a versioned JSON case set')
    parser.add_argument('--candidate', choices=('sound', 'wrong_field', 'false_accept', 'false_abstain'), default='sound')
    parser.add_argument('--output', required=True, help='Directory for JSON and text reports')
    args = parser.parse_args(argv)
    try:
        case_set, digest = load_cases(args.cases)
    except (CaseError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 3
    baseline = FixtureAdapter('sound'); candidate = FixtureAdapter(args.candidate)
    settings = {}
    scores = compare(case_set['cases'], baseline, candidate, settings)
    gate = evaluate(scores, RULES.copy())
    try:
        revision = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True, timeout=3).stdout.strip()
        dirty = bool(subprocess.run(['git', 'status', '--porcelain', '--', '.'], capture_output=True, text=True, check=True, timeout=3).stdout.strip())
    except (OSError, subprocess.SubprocessError):
        revision = None
        dirty = None
    report = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(), 'case_set_sha256': digest,
              'case_set_path': str(Path(args.cases)), 'baseline_version': baseline.version, 'candidate_version': candidate.version,
              'settings': settings, 'python_version': platform.python_version(), 'code_revision': revision, 'working_tree_dirty': dirty,
              'scores': scores, 'gate': gate, 'release_decision': 'Not made. A person must review the result.'}
    output = Path(args.output)
    try:
        output.mkdir(parents=True, exist_ok=True)
        (output / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
        lines = [f"Gate: {gate['status']}", f"Cases: {scores['candidate']['cases']}",
                 f"Field accuracy: {scores['candidate']['field_correct']}/{scores['candidate']['field_total']}",
                 f"Abstention accuracy: {scores['candidate']['abstention_correct']}/{scores['candidate']['cases']}",
                 'Review required. No release decision has been made.']
        lines.extend('Reason: ' + reason for reason in gate['reasons'])
        (output / 'report.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    except OSError as exc:
        print(f'Cannot write report: {exc}', file=sys.stderr)
        return 3
    print('\n'.join(lines))
    return {'pass': 0, 'fail': 1, 'incomplete': 2}[gate['status']]

if __name__ == '__main__':
    raise SystemExit(main())
