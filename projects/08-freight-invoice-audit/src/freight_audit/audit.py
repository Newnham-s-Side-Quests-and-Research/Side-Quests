"""Compare supplied invoice lines with an explicitly selected rate card."""
from datetime import date
import re


class AuditError(ValueError):
    pass


def _fields(value, expected, name):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise AuditError(f'Invalid {name} fields')


def _id(value, name):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', value, re.ASCII):
        raise AuditError(f'Invalid {name}')
    return value


def _integer(value, name, minimum=0, maximum=1_000_000_000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise AuditError(f'Invalid {name}')
    return value


def _date(value):
    if not isinstance(value, str):
        raise AuditError('Invalid date')
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise AuditError('Invalid date') from exc
    if parsed.isoformat() != value:
        raise AuditError('Date must use ISO format')
    return parsed


def audit(shipment, rate_cards, invoice):
    _fields(shipment, ('shipment_id','carrier','service','zone','date','weight_g','accessorials'), 'shipment')
    for name in ('shipment_id','carrier','service','zone'): _id(shipment[name], name)
    shipped = _date(shipment['date'])
    weight = _integer(shipment['weight_g'], 'weight', minimum=1)
    extras = shipment['accessorials']
    if not isinstance(extras, list) or any(not isinstance(item, str) for item in extras) or len(extras) != len(set(extras)):
        raise AuditError('Accessorials must be unique identifiers')
    for item in extras: _id(item, 'accessorial')
    _fields(invoice, ('shipment_id','currency','lines'), 'invoice')
    if invoice['shipment_id'] != shipment['shipment_id']:
        raise AuditError('Invoice does not identify the shipment')
    if not isinstance(invoice['currency'], str) or not re.fullmatch('[A-Z]{3}', invoice['currency'], re.ASCII):
        raise AuditError('Invalid invoice currency')
    lines = invoice['lines']
    if not isinstance(lines, list) or not 1 <= len(lines) <= 10000:
        raise AuditError('Invoice must contain a bounded list of lines')
    seen_ids, billed = set(), {}
    for line in lines:
        _fields(line, ('line_id','component','amount_minor'), 'invoice line')
        line_id = _id(line['line_id'], 'line ID')
        component = _id(line['component'], 'component')
        amount = _integer(line['amount_minor'], 'amount', minimum=-1_000_000_000)
        if line_id in seen_ids or component in billed:
            raise AuditError('Duplicate invoice line or component')
        seen_ids.add(line_id); billed[component] = (line_id, amount)
    if not isinstance(rate_cards, list) or len(rate_cards) > 10000:
        raise AuditError('Rate cards must be a bounded list')
    candidates = []
    card_ids = set()
    for card in rate_cards:
        _fields(card, ('tariff_id','carrier','service','zone','currency','start_date','end_date','min_weight_g','max_weight_g','base_minor','fuel_bps','accessorials'), 'rate card')
        card_id = _id(card['tariff_id'], 'tariff ID')
        if card_id in card_ids: raise AuditError('Duplicate tariff ID')
        card_ids.add(card_id)
        for name in ('carrier','service','zone'): _id(card[name], name)
        if not isinstance(card['currency'], str) or not re.fullmatch('[A-Z]{3}', card['currency'], re.ASCII):
            raise AuditError('Invalid tariff currency')
        start, end = _date(card['start_date']), _date(card['end_date'])
        low = _integer(card['min_weight_g'], 'minimum weight', minimum=1)
        high = _integer(card['max_weight_g'], 'maximum weight', minimum=1)
        _integer(card['base_minor'], 'base charge')
        _integer(card['fuel_bps'], 'fuel basis points', maximum=100000)
        if start > end or low > high: raise AuditError('Invalid tariff range')
        rates = card['accessorials']
        if not isinstance(rates, dict): raise AuditError('Invalid accessorial rates')
        for key, value in rates.items():
            _id(key, 'accessorial'); _integer(value, 'accessorial charge')
            if key in ('base', 'fuel'): raise AuditError('Reserved accessorial name')
        if all(card[key] == shipment[key] for key in ('carrier','service','zone')) and start <= shipped <= end and low <= weight <= high:
            candidates.append(card)
    if len(candidates) != 1:
        return {'status':'unresolved', 'reason':'no matching tariff' if not candidates else 'ambiguous tariffs',
                'shipment_id':shipment['shipment_id'], 'tariff_ids':sorted(card['tariff_id'] for card in candidates)}
    card = candidates[0]
    if card['currency'] != invoice['currency']:
        return {'status':'unresolved', 'reason':'currency mismatch', 'shipment_id':shipment['shipment_id'], 'tariff_ids':[card['tariff_id']]}
    if any(extra not in card['accessorials'] for extra in extras):
        return {'status':'unresolved', 'reason':'missing accessorial rate', 'shipment_id':shipment['shipment_id'], 'tariff_ids':[card['tariff_id']]}
    expected = {'base': card['base_minor'], 'fuel': (card['base_minor'] * card['fuel_bps'] + 5000) // 10000}
    expected.update({extra:card['accessorials'][extra] for extra in extras})
    if set(billed) != set(expected):
        return {'status':'unresolved', 'reason':'missing or unexpected invoice component', 'shipment_id':shipment['shipment_id'], 'tariff_ids':[card['tariff_id']]}
    results = [{'component':component,'expected_minor':amount,'billed_minor':billed[component][1],
                'difference_minor':billed[component][1]-amount,'line_id':billed[component][0],
                'shipment_id':shipment['shipment_id'],'tariff_id':card['tariff_id']} for component,amount in expected.items()]
    return {'status':'matched' if all(row['difference_minor']==0 for row in results) else 'discrepancy',
            'currency':invoice['currency'],'components':results,
            'difference_minor':sum(row['difference_minor'] for row in results),
            'limitations':['Results depend on supplied rate cards and shipment facts', 'No dispute or payment action is performed']}
