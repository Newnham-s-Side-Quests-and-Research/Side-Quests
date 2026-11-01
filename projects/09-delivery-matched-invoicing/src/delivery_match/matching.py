"""Calculate reviewable discrepancies without making a financial adjustment."""
import re


class MatchError(ValueError):
    pass


def _fields(value, expected, name):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise MatchError(f'Invalid {name} fields')


def _id(value, name):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', value, re.ASCII):
        raise MatchError(f'Invalid {name}')
    return value


def _count(value, name, positive=False):
    if type(value) is not int or not (1 if positive else 0) <= value <= 1_000_000_000:
        raise MatchError(f'Invalid {name}')
    return value


def match(order, receipts, invoice, previous_invoices):
    _fields(order, ('order_id','supplier_id','product_id','unit','ordered_quantity','currency','unit_price_minor'), 'order')
    for key in ('order_id','supplier_id','product_id','unit'): _id(order[key], key)
    quantity = _count(order['ordered_quantity'], 'ordered quantity', positive=True)
    unit_price = _count(order['unit_price_minor'], 'unit price')
    if not isinstance(order['currency'], str) or not re.fullmatch('[A-Z]{3}', order['currency'], re.ASCII):
        raise MatchError('Invalid currency')
    _fields(invoice, ('invoice_id','order_id','supplier_id','product_id','unit','quantity','currency','unit_price_minor'), 'invoice')
    _id(invoice['invoice_id'], 'invoice ID')
    invoiced = _count(invoice['quantity'], 'invoice quantity', positive=True)
    _count(invoice['unit_price_minor'], 'invoice unit price')
    if not isinstance(receipts, list) or len(receipts) > 100000:
        raise MatchError('Receipts must be a bounded list')
    if not isinstance(previous_invoices, list) or len(previous_invoices) > 100000:
        raise MatchError('Previous invoices must be a bounded list')
    seen, accepted, delivered = set(), 0, 0
    for receipt in receipts:
        _fields(receipt, ('receipt_id','order_id','product_id','unit','delivered_quantity','accepted_quantity'), 'receipt')
        receipt_id = _id(receipt['receipt_id'], 'receipt ID')
        if receipt_id in seen: raise MatchError('Duplicate receipt ID')
        seen.add(receipt_id)
        delivered_quantity = _count(receipt['delivered_quantity'], 'delivered quantity')
        accepted_quantity = _count(receipt['accepted_quantity'], 'accepted quantity')
        if accepted_quantity > delivered_quantity: raise MatchError('Accepted quantity exceeds delivered quantity')
        if any(receipt[key] != order[key] for key in ('order_id','product_id','unit')):
            return {'status':'unresolved','reason':'receipt identity or unit mismatch'}
        accepted += accepted_quantity; delivered += delivered_quantity
    if not receipts:
        return {'status':'unresolved','reason':'no delivery records'}
    if any(invoice[key] != order[key] for key in ('order_id','supplier_id','product_id','unit','currency','unit_price_minor')):
        return {'status':'unresolved','reason':'invoice does not match order terms'}
    seen_invoices = {invoice['invoice_id']}
    previous_quantity = 0
    for previous in previous_invoices:
        _fields(previous, ('invoice_id','order_id','supplier_id','product_id','unit','quantity','currency','unit_price_minor'), 'previous invoice')
        previous_id = _id(previous['invoice_id'], 'previous invoice ID')
        if previous_id in seen_invoices:
            raise MatchError('Duplicate invoice ID')
        seen_invoices.add(previous_id)
        previous_amount = _count(previous['quantity'], 'previous invoice quantity', positive=True)
        _count(previous['unit_price_minor'], 'previous invoice unit price')
        if any(previous[key] != order[key] for key in ('order_id','supplier_id','product_id','unit','currency','unit_price_minor')):
            return {'status':'unresolved','reason':'previous invoice does not match order terms'}
        previous_quantity += previous_amount
    if delivered > quantity or invoiced + previous_quantity > quantity:
        return {'status':'unresolved','reason':'quantity exceeds the order'}
    if previous_quantity > accepted:
        return {'status':'unresolved','reason':'previous invoices exceed accepted quantity'}
    available = accepted - previous_quantity
    excess = max(0, invoiced - available)
    return {'status':'matched' if excess == 0 else 'review', 'order_id':order['order_id'],
            'invoice_id':invoice['invoice_id'], 'receipt_ids':sorted(seen),
            'accepted_quantity':accepted, 'previously_invoiced_quantity':previous_quantity,
            'available_quantity':available, 'invoiced_quantity':invoiced,
            'proposed_credit_quantity':excess, 'proposed_credit_minor':excess * unit_price,
            'currency':order['currency'],
            'limitations':['The proposal depends on a complete and accurate supplied invoice history',
                            'No supplier contact, credit approval or payment adjustment is performed']}
