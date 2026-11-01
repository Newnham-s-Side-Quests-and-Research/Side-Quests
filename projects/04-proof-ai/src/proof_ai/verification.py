"""Verify supplied extraction results without processing payments."""
from decimal import Decimal, InvalidOperation
import re


class VerificationError(ValueError):
    pass


FIELDS = ('invoice_id', 'supplier_id', 'currency', 'subtotal', 'tax', 'total')
AMOUNT = re.compile(r'^(0|[1-9][0-9]{0,11})(\.[0-9]{1,2})?$', re.ASCII)


def _identifier(value, name):
    if not isinstance(value, str) or not value or len(value) > 128 or value != value.strip() or any(ord(char) < 32 for char in value):
        raise VerificationError(f'{name} must be a nonempty identifier')
    return value


def _amount(value):
    if not isinstance(value, str) or not AMOUNT.fullmatch(value):
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def verify_invoice(extraction, policy):
    if not isinstance(policy, dict) or set(policy) != {'supplier_id', 'currency', 'known_sources', 'existing_invoice_ids', 'rule_version'}:
        raise VerificationError('Policy is invalid')
    supplier = _identifier(policy['supplier_id'], 'Expected supplier')
    currency = _identifier(policy['currency'], 'Expected currency')
    version = _identifier(policy['rule_version'], 'Rule version')
    if not re.fullmatch(r'[A-Z]{3}', currency, re.ASCII):
        raise VerificationError('Expected currency must use three uppercase letters')
    for name in ('known_sources', 'existing_invoice_ids'):
        values = policy[name]
        if not isinstance(values, list) or len(values) > 100000:
            raise VerificationError(f'{name} must be a bounded list')
        for value in values:
            _identifier(value, name)
        if len(set(values)) != len(values):
            raise VerificationError(f'{name} must not contain duplicates')
    known_sources = set(policy['known_sources'])
    previous = set(policy['existing_invoice_ids'])
    if not isinstance(extraction, dict) or set(extraction) != {'status', 'fields'}:
        raise VerificationError('Extraction must contain status and fields')
    if extraction['status'] not in ('complete', 'failed'):
        raise VerificationError('Unsupported extraction status')
    values = extraction['fields']
    if not isinstance(values, dict) or values.keys() - set(FIELDS):
        raise VerificationError('Extraction fields are invalid')
    checks = []
    parsed = {}
    for field in FIELDS:
        item = values.get(field)
        if item is None:
            checks.append({'rule': 'field_present', 'field': field, 'passed': False, 'source_id': None})
            continue
        if not isinstance(item, dict) or set(item) != {'value', 'source_id'}:
            raise VerificationError(f'Invalid field object: {field}')
        source = item['source_id']
        source_ok = isinstance(source, str) and source in known_sources
        value = item['value']
        if field in ('subtotal', 'tax', 'total'):
            parsed[field] = _amount(value)
            valid = parsed[field] is not None
        else:
            try:
                parsed[field] = _identifier(value, field)
                valid = True
            except VerificationError:
                parsed[field] = None
                valid = False
        checks.append({'rule': 'field_present', 'field': field, 'passed': valid, 'source_id': source if source_ok else None})
        checks.append({'rule': 'source_known', 'field': field, 'passed': source_ok, 'source_id': source if source_ok else None})
    checks.append({'rule': 'supplier_match', 'passed': parsed.get('supplier_id') == supplier})
    checks.append({'rule': 'currency_match', 'passed': parsed.get('currency') == currency})
    invoice_id = parsed.get('invoice_id')
    checks.append({'rule': 'invoice_not_seen', 'passed': invoice_id is not None and invoice_id not in previous})
    amounts = [parsed.get(name) for name in ('subtotal', 'tax', 'total')]
    checks.append({'rule': 'total_matches', 'passed': all(value is not None for value in amounts) and amounts[0] + amounts[1] == amounts[2]})
    checks.append({'rule': 'extraction_complete', 'passed': extraction['status'] == 'complete'})
    return {'decision': 'checks_passed' if all(check['passed'] for check in checks) else 'review',
            'rule_version': version, 'checks': checks,
            'limitations': ['Consistent fields and arithmetic do not prove the document is genuine or correct',
                            'Source identifiers are checked for membership but document content is not independently read',
                            'Passing checks does not approve the invoice',
                            'No payment, model call or human approval is performed']}
