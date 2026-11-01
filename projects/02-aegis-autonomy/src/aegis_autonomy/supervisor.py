"""Track a state transition policy for monitor outcomes."""
from .monitor import MonitoringError, number


def _count(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100000:
        raise MonitoringError(f'{name} must be a positive integer')
    return value


class Supervisor:
    def __init__(self, alarms_to_degrade, clears_to_recover, max_gap_seconds):
        self.alarms_to_degrade = _count(alarms_to_degrade, 'Alarm count')
        self.clears_to_recover = _count(clears_to_recover, 'Clear count')
        self.max_gap = number(max_gap_seconds, 'Maximum gap', positive=True)
        self.state = 'unknown'
        self.last_time = None
        self.alarm_count = 0
        self.clear_count = 0

    def update(self, timestamp, decision):
        timestamp = number(timestamp, 'Timestamp', minimum=0)
        if decision not in ('clear', 'alarm', 'unavailable'):
            raise MonitoringError('Invalid monitor decision')
        if self.last_time is not None and timestamp <= self.last_time:
            raise MonitoringError('Timestamps must increase strictly')
        gap = self.last_time is not None and timestamp - self.last_time > self.max_gap
        previous = self.state
        if gap or decision == 'unavailable':
            self.state = 'degraded'
            self.alarm_count = self.clear_count = 0
            reason = 'observation gap' if gap else 'measurement unavailable'
        elif decision == 'alarm':
            self.alarm_count += 1
            self.clear_count = 0
            if self.alarm_count >= self.alarms_to_degrade:
                self.state = 'degraded'
            reason = 'alarm threshold reached' if self.state == 'degraded' else 'alarm pending'
        else:
            self.alarm_count = 0
            self.clear_count += 1
            if self.state == 'unknown' or (self.state == 'degraded' and self.clear_count >= self.clears_to_recover):
                self.state = 'nominal'
            reason = 'clear measurements' if self.state == 'nominal' else 'recovery pending'
        self.last_time = timestamp
        return {'state': self.state, 'previous_state': previous, 'changed': self.state != previous,
                'reason': reason, 'alarm_count': self.alarm_count, 'clear_count': self.clear_count}
