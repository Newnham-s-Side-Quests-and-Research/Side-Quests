"""Evaluate measurement residuals against explicitly configured thresholds."""
import math


class MonitoringError(ValueError):
    pass


def number(value, name, minimum=None, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MonitoringError(f'{name} must be a finite number')
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or (minimum is not None and value < minimum) or (positive and value <= 0):
        raise MonitoringError(f'{name} is outside the supported range')
    return float(value)


class ResidualMonitor:
    def __init__(self, method, threshold):
        if method not in ('absolute', 'normalised'):
            raise MonitoringError('Monitor must be absolute or normalised')
        self.method = method
        self.threshold = number(threshold, 'Threshold', positive=True)

    def evaluate(self, residual, variance):
        if residual is None or variance is None:
            if residual is not None:
                number(residual, 'Residual')
            if variance is not None:
                number(variance, 'Variance', positive=True)
            return {'decision': 'unavailable', 'score': None, 'reason': 'measurement unavailable'}
        residual = number(residual, 'Residual')
        variance = number(variance, 'Variance', positive=True)
        try:
            score = abs(residual) if self.method == 'absolute' else (residual / math.sqrt(variance)) ** 2
        except OverflowError as exc:
            raise MonitoringError('Monitor score is not finite') from exc
        if not math.isfinite(score):
            raise MonitoringError('Monitor score is not finite')
        alarm = score > self.threshold
        return {'decision': 'alarm' if alarm else 'clear', 'score': score,
                'reason': 'threshold exceeded' if alarm else 'within threshold'}
