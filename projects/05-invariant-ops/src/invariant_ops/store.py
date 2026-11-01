"""Local transactional order processing with idempotency and an outbox.

Actor names are supplied by the caller and are not authenticated. This module
does not transmit events, make payments or connect to an external ledger.
"""
import hashlib
import json
import re
import sqlite3


class WorkflowError(ValueError):
    pass


IDENTIFIER = re.compile(r'^[A-Za-z0-9_.-]{1,128}$', re.ASCII)


def _id(value, name):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise WorkflowError(f'Invalid {name}')
    return value


def _quantity(value, name, minimum=1):
    if type(value) is not int or not minimum <= value <= 1_000_000_000:
        raise WorkflowError(f'Invalid {name}')
    return value


class WorkflowStore:
    def __init__(self, path):
        self.path = str(path)
        connection = self._connection()
        try:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY, supplier_id TEXT NOT NULL, currency TEXT NOT NULL,
                    quantity INTEGER NOT NULL, unit_price_minor INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS receipts (
                    receipt_id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES orders(order_id),
                    quantity INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS invoices (
                    invoice_id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES orders(order_id),
                    quantity INTEGER NOT NULL, amount_minor INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS commands (
                    command_id TEXT PRIMARY KEY, request_hash TEXT NOT NULL, response TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS outbox (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, command_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL, payload TEXT NOT NULL
                );
            ''')
        finally:
            connection.close()

    def _connection(self):
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.execute('PRAGMA foreign_keys = ON')
        return connection

    def apply(self, command):
        if not isinstance(command, dict) or set(command) != {'command_id', 'actor', 'operation', 'payload'}:
            raise WorkflowError('Invalid command')
        command_id = _id(command['command_id'], 'command ID')
        actor = _id(command['actor'], 'actor')
        operation = command['operation']
        payload = command['payload']
        if operation not in ('create_order', 'record_receipt', 'post_invoice') or not isinstance(payload, dict):
            raise WorkflowError('Invalid operation or payload')
        try:
            request = json.dumps({'actor': actor, 'operation': operation, 'payload': payload},
                                 sort_keys=True, separators=(',', ':'), allow_nan=False)
        except (ValueError, TypeError) as exc:
            raise WorkflowError('Invalid command data') from exc
        digest = hashlib.sha256(request.encode('utf-8')).hexdigest()
        connection = self._connection()
        try:
            connection.execute('BEGIN IMMEDIATE')
            prior = connection.execute('SELECT request_hash, response FROM commands WHERE command_id = ?', (command_id,)).fetchone()
            if prior:
                if prior[0] != digest:
                    raise WorkflowError('Command ID was already used for different data')
                connection.commit()
                return json.loads(prior[1])
            if operation == 'create_order':
                result = self._create_order(connection, payload)
            elif operation == 'record_receipt':
                result = self._record_receipt(connection, payload)
            else:
                result = self._post_invoice(connection, payload)
            response = json.dumps(result, sort_keys=True, separators=(',', ':'))
            event = json.dumps({'actor': actor, 'result': result}, sort_keys=True, separators=(',', ':'))
            connection.execute('INSERT INTO commands VALUES (?, ?, ?)', (command_id, digest, response))
            connection.execute('INSERT INTO outbox (command_id, event_type, payload) VALUES (?, ?, ?)', (command_id, operation, event))
            connection.commit()
            return result
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise WorkflowError('Duplicate identifier or missing referenced record') from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _create_order(self, connection, payload):
        if set(payload) != {'order_id', 'supplier_id', 'currency', 'quantity', 'unit_price_minor'}:
            raise WorkflowError('Invalid order fields')
        order = _id(payload['order_id'], 'order ID')
        supplier = _id(payload['supplier_id'], 'supplier ID')
        currency = payload['currency']
        if not isinstance(currency, str) or not re.fullmatch('[A-Z]{3}', currency, re.ASCII):
            raise WorkflowError('Invalid currency')
        quantity = _quantity(payload['quantity'], 'quantity')
        price = _quantity(payload['unit_price_minor'], 'unit price', minimum=0)
        connection.execute('INSERT INTO orders VALUES (?, ?, ?, ?, ?)', (order, supplier, currency, quantity, price))
        return {'order_id': order, 'status': 'created'}

    def _record_receipt(self, connection, payload):
        if set(payload) != {'receipt_id', 'order_id', 'quantity'}:
            raise WorkflowError('Invalid receipt fields')
        receipt = _id(payload['receipt_id'], 'receipt ID')
        order = _id(payload['order_id'], 'order ID')
        quantity = _quantity(payload['quantity'], 'quantity')
        row = connection.execute('SELECT quantity FROM orders WHERE order_id = ?', (order,)).fetchone()
        if row is None:
            raise WorkflowError('Order does not exist')
        received = connection.execute('SELECT COALESCE(SUM(quantity), 0) FROM receipts WHERE order_id = ?', (order,)).fetchone()[0]
        if received + quantity > row[0]:
            raise WorkflowError('Receipt would exceed the order quantity')
        connection.execute('INSERT INTO receipts VALUES (?, ?, ?)', (receipt, order, quantity))
        return {'receipt_id': receipt, 'order_id': order, 'status': 'recorded'}

    def _post_invoice(self, connection, payload):
        if set(payload) != {'invoice_id', 'order_id', 'supplier_id', 'currency', 'quantity', 'amount_minor'}:
            raise WorkflowError('Invalid invoice fields')
        invoice = _id(payload['invoice_id'], 'invoice ID')
        order = _id(payload['order_id'], 'order ID')
        supplier = _id(payload['supplier_id'], 'supplier ID')
        quantity = _quantity(payload['quantity'], 'quantity')
        amount = _quantity(payload['amount_minor'], 'amount', minimum=0)
        row = connection.execute('SELECT supplier_id, currency, unit_price_minor FROM orders WHERE order_id = ?', (order,)).fetchone()
        if row is None:
            raise WorkflowError('Order does not exist')
        if row[0] != supplier or row[1] != payload['currency'] or amount != quantity * row[2]:
            raise WorkflowError('Invoice does not match order terms')
        received = connection.execute('SELECT COALESCE(SUM(quantity), 0) FROM receipts WHERE order_id = ?', (order,)).fetchone()[0]
        invoiced = connection.execute('SELECT COALESCE(SUM(quantity), 0) FROM invoices WHERE order_id = ?', (order,)).fetchone()[0]
        if invoiced + quantity > received:
            raise WorkflowError('Invoice quantity exceeds recorded receipts')
        connection.execute('INSERT INTO invoices VALUES (?, ?, ?, ?)', (invoice, order, quantity, amount))
        return {'invoice_id': invoice, 'order_id': order, 'status': 'posted'}

    def outbox(self):
        connection = self._connection()
        try:
            rows = connection.execute('SELECT sequence, command_id, event_type, payload FROM outbox ORDER BY sequence').fetchall()
            return [{'sequence': row[0], 'command_id': row[1], 'event_type': row[2], 'payload': json.loads(row[3])} for row in rows]
        finally:
            connection.close()
