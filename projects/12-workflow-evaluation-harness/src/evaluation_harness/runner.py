"""Run both adapters against the same cases and score observable outcomes."""
from copy import deepcopy

def _run(adapter, case, settings):
    try:
        value = adapter.run(deepcopy(case['input']), deepcopy(settings))
        if not isinstance(value, dict) or not isinstance(value.get('fields'), dict) or not isinstance(value.get('abstain'), bool):
            raise ValueError('Adapter returned an invalid output')
        return {'output': value, 'error': None}
    except Exception as exc:
        return {'output': None, 'error': {'type': type(exc).__name__, 'message': str(exc)}}

def _score(cases, outcomes):
    field_total = field_correct = abstention_correct = 0
    errors = 0
    details = []
    for case, outcome in zip(cases, outcomes):
        expected = case['expected']; value = outcome['output']
        errors += int(outcome['error'] is not None)
        abstention_ok = value is not None and value['abstain'] == expected['abstain']
        abstention_correct += int(abstention_ok)
        checks = []
        if not expected['abstain']:
            for key, target in expected['fields'].items():
                field_total += 1
                # An abstention is not an accepted field even if a value was returned.
                correct = value is not None and not value['abstain'] and key in value['fields'] and type(value['fields'][key]) is type(target) and value['fields'][key] == target
                field_correct += int(correct)
                checks.append({'field': key, 'expected': target, 'correct': correct})
        details.append({'case_id': case['id'], 'category': case['category'], 'result': outcome,
                        'abstention_correct': abstention_ok, 'field_checks': checks})
    return {'cases': len(cases), 'errors': errors,
            'field_accuracy': field_correct / field_total if field_total else None,
            'field_correct': field_correct, 'field_total': field_total,
            'abstention_accuracy': abstention_correct / len(cases) if cases else None,
            'abstention_correct': abstention_correct, 'details': details}

def compare(cases, baseline, candidate, settings):
    baseline_results = [_run(baseline, c, settings) for c in cases]
    candidate_results = [_run(candidate, c, settings) for c in cases]
    return {'baseline': _score(cases, baseline_results), 'candidate': _score(cases, candidate_results)}
