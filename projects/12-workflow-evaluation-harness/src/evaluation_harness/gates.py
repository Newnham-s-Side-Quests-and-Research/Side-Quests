"""Apply explicit comparison rules without authorising a release."""
def evaluate(scores, rules):
    baseline, candidate = scores['baseline'], scores['candidate']
    minimum = rules['minimum_cases']
    if baseline['errors'] or candidate['errors'] or candidate['cases'] < minimum:
        return {'status': 'incomplete', 'reasons': ['Execution errors or insufficient cases'], 'rules': rules}
    if any(x is None for x in (baseline['field_accuracy'], candidate['field_accuracy'], candidate['abstention_accuracy'])):
        return {'status': 'incomplete', 'reasons': ['A required score is unavailable'], 'rules': rules}
    reasons = []
    if candidate['field_accuracy'] - baseline['field_accuracy'] < rules['minimum_field_delta']:
        reasons.append('Field accuracy fell below the allowed comparison')
    if candidate['abstention_accuracy'] < rules['minimum_abstention_accuracy']:
        reasons.append('Abstention accuracy fell below the threshold')
    return {'status': 'fail' if reasons else 'pass', 'reasons': reasons, 'rules': rules}
