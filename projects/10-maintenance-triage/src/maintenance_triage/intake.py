"""Persist reports and flag configured phrases for priority human review.

This is not an emergency service and does not notify a recipient. All reports
require human review. Callers must arrange access control and secure storage.
"""
import hashlib
import json
import re
import sqlite3
from datetime import datetime,timezone


class IntakeError(ValueError):
    pass


def _id(value,name):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',value,re.ASCII):
        raise IntakeError(f'Invalid {name}')
    return value


class IntakeQueue:
    def __init__(self,path,priority_phrases):
        if not isinstance(priority_phrases,list) or not priority_phrases or len(priority_phrases)>1000:
            raise IntakeError('Priority phrases must be a nonempty bounded list')
        if any(not isinstance(phrase,str) or not phrase.strip() or len(phrase)>128 for phrase in priority_phrases):
            raise IntakeError('Invalid priority phrase')
        self.patterns=[(phrase,re.compile(r'(?<!\w)'+re.escape(phrase.strip())+r'(?!\w)',re.IGNORECASE)) for phrase in priority_phrases]
        self.policy_hash=hashlib.sha256(json.dumps(priority_phrases,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
        self.path=str(path)
        connection=sqlite3.connect(self.path,timeout=10)
        try:
            connection.execute('CREATE TABLE IF NOT EXISTS reports (report_id TEXT PRIMARY KEY, request_hash TEXT NOT NULL, payload TEXT NOT NULL, route TEXT NOT NULL, reasons TEXT NOT NULL, policy_hash TEXT NOT NULL)')
            connection.commit()
        finally:connection.close()

    def submit(self,report):
        if not isinstance(report,dict) or set(report)!={'report_id','unit_id','timestamp','text'}:
            raise IntakeError('Invalid report fields')
        report_id=_id(report['report_id'],'report ID');_id(report['unit_id'],'unit ID')
        timestamp=report['timestamp']
        if not isinstance(timestamp,str):raise IntakeError('Invalid timestamp')
        try: parsed=datetime.fromisoformat(timestamp.replace('Z','+00:00'))
        except ValueError as exc:raise IntakeError('Invalid timestamp') from exc
        if parsed.tzinfo is None or parsed.utcoffset()!=timezone.utc.utcoffset(parsed):
            raise IntakeError('Timestamp must include UTC offset')
        text=report['text']
        if not isinstance(text,str) or not text.strip() or len(text)>20000:
            raise IntakeError('Report text must be nonempty and bounded')
        payload=json.dumps(report,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        digest=hashlib.sha256(payload.encode('utf-8')).hexdigest()
        reasons=[phrase for phrase,pattern in self.patterns if pattern.search(text)]
        route='priority_human_review' if reasons else 'human_review'
        connection=sqlite3.connect(self.path,timeout=10,isolation_level=None)
        try:
            connection.execute('BEGIN IMMEDIATE')
            previous=connection.execute('SELECT request_hash,route,reasons,policy_hash FROM reports WHERE report_id=?',(report_id,)).fetchone()
            if previous:
                if previous[0]!=digest:raise IntakeError('Report ID was used for different data')
                connection.commit()
                return {'report_id':report_id,'route':previous[1],'reasons':json.loads(previous[2]),'policy_hash':previous[3]}
            connection.execute('INSERT INTO reports VALUES (?,?,?,?,?,?)',(report_id,digest,payload,route,json.dumps(reasons),self.policy_hash))
            connection.commit()
            return {'report_id':report_id,'route':route,'reasons':reasons,'policy_hash':self.policy_hash}
        except Exception:
            connection.rollback();raise
        finally:connection.close()
