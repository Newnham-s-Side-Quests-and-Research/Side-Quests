"""Return source passages only after checking caller supplied access roles.

Roles must be supplied by an authenticated application. This module does not
authenticate users, persist records or connect to external systems.
"""
import hashlib
import re


class RetrievalError(ValueError):
    pass


def _id(value, name):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', value, re.ASCII):
        raise RetrievalError(f'Invalid {name}')
    return value


def _roles(value):
    if not isinstance(value, (list, tuple, set, frozenset)) or len(value) > 1000:
        raise RetrievalError('Roles must be a bounded collection')
    return {_id(item, 'role') for item in value}


class SourceIndex:
    def __init__(self, sources):
        if not isinstance(sources, list) or len(sources) > 10000:
            raise RetrievalError('Sources must be a bounded list')
        self._sources = {}
        for source in sources:
            if not isinstance(source, dict) or set(source) != {'source_id','version','text','roles'}:
                raise RetrievalError('Invalid source fields')
            source_id = _id(source['source_id'], 'source ID')
            version = _id(source['version'], 'source version')
            key = (source_id, version)
            if key in self._sources: raise RetrievalError('Duplicate source version')
            text = source['text']
            if not isinstance(text, str) or not 1 <= len(text) <= 1_000_000:
                raise RetrievalError('Source text must be nonempty and bounded')
            roles = _roles(source['roles'])
            if not roles: raise RetrievalError('Each source must have an access role')
            self._sources[key] = {'text':text, 'roles':roles,
                                  'sha256':hashlib.sha256(text.encode('utf-8')).hexdigest()}

    def search(self, query, roles, limit=20):
        if not isinstance(query, str) or not 1 <= len(query) <= 256:
            raise RetrievalError('Query must be nonempty and bounded')
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise RetrievalError('Invalid result limit')
        allowed = _roles(roles)
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        results = []
        for (source_id, version), source in sorted(self._sources.items()):
            if not allowed.intersection(source['roles']):
                continue
            for found in pattern.finditer(source['text']):
                results.append({'source_id':source_id, 'version':version, 'sha256':source['sha256'],
                                'start':found.start(), 'end':found.end(), 'text':found.group()})
                if len(results) >= limit: return results
        return results

    def resolve(self, reference, roles):
        if not isinstance(reference, dict) or set(reference) != {'source_id','version','sha256','start','end'}:
            raise RetrievalError('Invalid source reference')
        key = (_id(reference['source_id'],'source ID'), _id(reference['version'],'source version'))
        allowed = _roles(roles)
        source = self._sources.get(key)
        if source is None or not allowed.intersection(source['roles']):
            raise RetrievalError('Source is unavailable')
        start, end = reference['start'], reference['end']
        if (reference['sha256'] != source['sha256'] or type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(source['text'])):
            raise RetrievalError('Source reference is invalid or stale')
        return source['text'][start:end]
