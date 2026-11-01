"""Load and validate versioned synthetic test cases."""
import hashlib
import json
from pathlib import Path

class CaseError(ValueError):
    pass

def load_cases(path):
    try:
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise CaseError(f'Cannot read case set: {exc}') from exc
    if not isinstance(raw, dict) or raw.get('schema_version') != 1:
        raise CaseError('Case set must use schema version 1')
    cases = raw.get('cases')
    if not isinstance(cases, list) or not cases:
        raise CaseError('Case set must contain at least one case')
    ids = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise CaseError(f'Case {index} must be an object')
        if not isinstance(case.get('id'), str) or not case['id'].strip() or case['id'] in ids:
            raise CaseError(f'Case {index} has a missing or duplicate ID')
        ids.add(case['id'])
        if not isinstance(case.get('input'), dict) or not isinstance(case.get('expected'), dict):
            raise CaseError(f"Case {case['id']} needs input and expected objects")
        expected = case['expected']
        if not isinstance(expected.get('fields'), dict) or not isinstance(expected.get('abstain'), bool):
            raise CaseError(f"Case {case['id']} needs expected fields and abstention")
        for name in ('category', 'split', 'rights'):
            if not isinstance(case.get(name), str) or not case[name].strip():
                raise CaseError(f"Case {case['id']} needs {name}")
    try:
        canonical = json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError) as exc:
        raise CaseError(f'Case set contains a nonstandard value: {exc}') from exc
    return raw, hashlib.sha256(canonical).hexdigest()
