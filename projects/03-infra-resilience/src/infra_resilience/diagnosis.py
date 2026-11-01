"""Rank configured candidate causes from supplied event records."""
import re


class DiagnosisError(ValueError):
    pass


IDENTIFIER = re.compile(r'^[A-Za-z0-9_.-]{1,128}$', re.ASCII)


def identifier(value, name):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise DiagnosisError(f'{name} is invalid')
    return value


def diagnose(data):
    if not isinstance(data, dict) or set(data) != {'schema_version', 'catalogue', 'events'}:
        raise DiagnosisError('Input must contain the declared fields')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise DiagnosisError('Unsupported schema version')
    catalogue, events = data['catalogue'], data['events']
    if not isinstance(catalogue, list) or not 1 <= len(catalogue) <= 10000:
        raise DiagnosisError('Catalogue must be a nonempty bounded list')
    if not isinstance(events, list) or len(events) > 100000:
        raise DiagnosisError('Events must be a bounded list')
    causes = {}
    for candidate in catalogue:
        if not isinstance(candidate, dict) or set(candidate) != {'cause_id', 'signals'}:
            raise DiagnosisError('Invalid catalogue entry')
        cause = identifier(candidate['cause_id'], 'Cause')
        signals = candidate['signals']
        if cause in causes or not isinstance(signals, list) or not 1 <= len(signals) <= 1000:
            raise DiagnosisError('Cause IDs must be unique and signals nonempty')
        signals = [identifier(signal, 'Signal') for signal in signals]
        if len(signals) != len(set(signals)):
            raise DiagnosisError('Signals must be unique within a cause')
        causes[cause] = set(signals)
    ids = set()
    valid = []
    for event in events:
        if not isinstance(event, dict) or set(event) != {'event_id', 'timestamp_ms', 'signal', 'quality', 'alarm'}:
            raise DiagnosisError('Invalid event')
        event_id = identifier(event['event_id'], 'Event ID')
        signal = identifier(event['signal'], 'Signal')
        timestamp = event['timestamp_ms']
        if event_id in ids or type(timestamp) is not int or not 0 <= timestamp <= 2**53 - 1:
            raise DiagnosisError('Event IDs must be unique and timestamps valid')
        if event['quality'] not in ('valid', 'missing', 'stale'):
            raise DiagnosisError('Invalid event quality')
        if event['quality'] == 'valid' and type(event['alarm']) is not bool:
            raise DiagnosisError('Valid events require a boolean alarm')
        if event['quality'] != 'valid' and event['alarm'] is not None:
            raise DiagnosisError('Unavailable events must not carry an alarm value')
        ids.add(event_id)
        valid.append({'event_id': event_id, 'timestamp_ms': timestamp, 'signal': signal,
                      'quality': event['quality'], 'alarm': event['alarm']})
    ordered = sorted(valid, key=lambda event: (event['timestamp_ms'], event['event_id']))
    latest = {}
    conflicts = set()
    for event in ordered:
        previous = latest.get(event['signal'])
        if previous is None or event['timestamp_ms'] > previous['timestamp_ms']:
            latest[event['signal']] = event
            conflicts.discard(event['signal'])
        elif (event['quality'], event['alarm']) != (previous['quality'], previous['alarm']):
            conflicts.add(event['signal'])
    alarms = {signal: event for signal, event in latest.items() if signal not in conflicts and event['quality'] == 'valid' and event['alarm']}
    required_signals = set().union(*causes.values())
    unavailable = sorted((required_signals - latest.keys()) |
                         {signal for signal, event in latest.items() if event['quality'] != 'valid'} | conflicts)
    ranking = []
    for cause, signals in causes.items():
        matched = sorted(signals & alarms.keys())
        if matched:
            ranking.append({'cause_id': cause, 'score': len(matched),
                            'evidence_ids': [alarms[signal]['event_id'] for signal in matched]})
    ranking.sort(key=lambda item: (-item['score'], item['cause_id']))
    status = 'unknown' if not ranking else 'ambiguous' if len(ranking) > 1 and ranking[0]['score'] == ranking[1]['score'] else 'ranked'
    return {'schema_version': 1, 'status': status, 'ranking': ranking, 'unavailable_signals': unavailable,
            'events_processed': len(ordered),
            'limitations': ['Ranking is based on configured signal associations and is not proof of causation',
                            'Only the newest event time for each signal is used and conflicting events at that time are unavailable',
                            'No plant control or protective action is performed']}
