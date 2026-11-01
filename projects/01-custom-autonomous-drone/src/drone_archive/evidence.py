"""Validate evidence records without inferring historical facts."""
from datetime import date
from hashlib import sha256
from pathlib import Path
import re

RIGHTS = frozenset({'unknown', 'cleared', 'restricted'})
STATUSES = frozenset({'flown', 'bench', 'simulated', 'conceptual', 'unsupported'})

class EvidenceError(ValueError):
    pass

def hash_file(path):
    path = Path(path)
    if not path.is_file():
        raise EvidenceError('Artefact must be an existing file')
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f'{name} must be a nonempty string')
    return value

def validate_register(register):
    if not isinstance(register, dict) or register.get('schema_version') != 1:
        raise EvidenceError('Register must use schema version 1')
    artefacts = register.get('artefacts')
    claims = register.get('claims')
    if not isinstance(artefacts, list) or not isinstance(claims, list):
        raise EvidenceError('Register needs artefact and claim lists')
    by_id = {}
    for item in artefacts:
        if not isinstance(item, dict):
            raise EvidenceError('Artefact must be an object')
        identity = _text(item.get('id'), 'Artefact ID')
        if identity in by_id:
            raise EvidenceError(f'Duplicate artefact ID: {identity}')
        if not isinstance(item.get('sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', item['sha256']):
            raise EvidenceError(f'Invalid SHA256 for artefact {identity}')
        _text(item.get('source'), 'Artefact source')
        if item.get('rights') not in RIGHTS:
            raise EvidenceError(f'Invalid rights state for artefact {identity}')
        by_id[identity] = item
    ids = set()
    for claim in claims:
        if not isinstance(claim, dict):
            raise EvidenceError('Claim must be an object')
        identity = _text(claim.get('id'), 'Claim ID')
        if identity in ids:
            raise EvidenceError(f'Duplicate claim ID: {identity}')
        ids.add(identity)
        _text(claim.get('text'), 'Claim text')
        if claim.get('status') not in STATUSES:
            raise EvidenceError(f'Invalid claim status for {identity}')
        references = claim.get('evidence')
        if not isinstance(references, list) or any(not isinstance(x, str) for x in references):
            raise EvidenceError(f'Invalid evidence list for {identity}')
        if len(set(references)) != len(references):
            raise EvidenceError(f'Duplicate evidence reference for {identity}')
        if any(x not in by_id for x in references):
            raise EvidenceError(f'Unknown evidence reference for {identity}')
        if claim['status'] != 'unsupported' and not references:
            raise EvidenceError(f'Claim {identity} needs evidence or unsupported status')
        _text(claim.get('reviewer'), 'Claim reviewer')
        _text(claim.get('rationale'), 'Claim rationale')
        try:
            date.fromisoformat(_text(claim.get('review_date'), 'Claim review date'))
        except ValueError as exc:
            raise EvidenceError(f'Invalid review date for {identity}') from exc
    return by_id


def verify_files(register, root):
    """Compare stored artefacts with recorded hashes within an explicit root."""
    artefacts = validate_register(register)
    root = Path(root).resolve()
    if not root.is_dir():
        raise EvidenceError('Artefact root must be an existing directory')
    results = []
    for identity, item in sorted(artefacts.items()):
        storage = item.get('storage')
        if not isinstance(storage, str) or not storage.strip():
            results.append({'id': identity, 'status': 'storage not recorded'})
            continue
        relative = Path(storage)
        target = (root / relative).resolve()
        if relative.is_absolute() or not target.is_relative_to(root):
            results.append({'id': identity, 'status': 'invalid path'})
            continue
        if not target.is_file():
            results.append({'id': identity, 'status': 'missing'})
            continue
        try:
            actual = hash_file(target)
        except OSError:
            results.append({'id': identity, 'status': 'unreadable'})
            continue
        results.append({'id': identity, 'status': 'matched' if actual == item['sha256'] else 'changed'})
    return results

def publication_manifest(register):
    """List cleared artefacts and identify claims requiring further review."""
    artefacts = validate_register(register)
    cleared = sorted(a['id'] for a in artefacts.values() if a['rights'] == 'cleared')
    blockers = []
    for claim in register['claims']:
        if claim['status'] == 'unsupported':
            blockers.append({'claim_id': claim['id'], 'reason': 'Unsupported claim'})
        elif any(artefacts[x]['rights'] != 'cleared' for x in claim['evidence']):
            blockers.append({'claim_id': claim['id'], 'reason': 'Evidence rights not cleared'})
    return {'cleared_artefacts': cleared, 'claim_blockers': blockers,
            'decision': 'Human approval is required before publication.'}
