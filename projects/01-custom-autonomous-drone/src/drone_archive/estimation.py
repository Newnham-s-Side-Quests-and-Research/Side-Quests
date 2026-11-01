"""Vertical state estimation for synthetic pressure and position measurements.

This two state filter does not estimate attitude or replace a flight estimator.
"""
import math
from .sensors import pressure_from_altitude, SCALE_HEIGHT_M

class EstimationError(ValueError):
    pass

def _finite_number(value, name, positive=False, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise EstimationError(f'{name} must be finite')
    if positive and value <= 0:
        raise EstimationError(f'{name} must be positive')
    if nonnegative and value < 0:
        raise EstimationError(f'{name} must not be negative')
    return float(value)

class VerticalFilter:
    def __init__(self, altitude_m, velocity_m_s, altitude_variance, velocity_variance):
        self.altitude_m = _finite_number(altitude_m, 'altitude')
        self.velocity_m_s = _finite_number(velocity_m_s, 'velocity')
        a = _finite_number(altitude_variance, 'altitude variance', positive=True)
        v = _finite_number(velocity_variance, 'velocity variance', positive=True)
        self.covariance = ((a, 0.0), (0.0, v))

    def predict(self, acceleration_m_s2, dt_seconds, acceleration_variance):
        acceleration = _finite_number(acceleration_m_s2, 'acceleration')
        dt = _finite_number(dt_seconds, 'timestep', positive=True)
        q = _finite_number(acceleration_variance, 'acceleration variance', nonnegative=True)
        p00, p01 = self.covariance[0]; _, p11 = self.covariance[1]
        g0, g1 = 0.5 * dt * dt, dt
        altitude = self.altitude_m + self.velocity_m_s * dt + g0 * acceleration
        velocity = self.velocity_m_s + dt * acceleration
        a = p00 + 2 * dt * p01 + dt * dt * p11 + g0 * g0 * q
        b = p01 + dt * p11 + g0 * g1 * q
        d = p11 + g1 * g1 * q
        self._commit(altitude, velocity, a, b, d)

    def update_altitude(self, altitude_m, variance, innovation_limit=None):
        observation = _finite_number(altitude_m, 'altitude observation')
        return self._update(observation, self.altitude_m, 1.0, variance, innovation_limit)

    def update_pressure(self, pressure_pa, variance, innovation_limit=None):
        observation = _finite_number(pressure_pa, 'pressure observation', positive=True)
        try:
            prediction = pressure_from_altitude(self.altitude_m)
        except ValueError as exc:
            raise EstimationError(str(exc)) from exc
        return self._update(observation, prediction, -prediction / SCALE_HEIGHT_M, variance, innovation_limit)

    def _update(self, observation, prediction, h0, variance, innovation_limit):
        r = _finite_number(variance, 'observation variance', positive=True)
        limit = None if innovation_limit is None else _finite_number(innovation_limit, 'innovation limit', positive=True)
        p00, p01 = self.covariance[0]; _, p11 = self.covariance[1]
        innovation = observation - prediction
        innovation_variance = h0 * h0 * p00 + r
        if not math.isfinite(innovation_variance) or innovation_variance <= 0:
            raise EstimationError('Invalid innovation variance')
        nis = innovation * innovation / innovation_variance
        if not math.isfinite(nis):
            raise EstimationError('Nonfinite innovation')
        if limit is not None and nis > limit:
            return {'accepted': False, 'innovation': innovation, 'normalised_innovation_squared': nis}
        k0, k1 = p00 * h0 / innovation_variance, p01 * h0 / innovation_variance
        # Joseph form keeps observation noise in the covariance calculation.
        m00, m10 = 1.0 - k0 * h0, -k1 * h0
        a = m00 * m00 * p00 + k0 * k0 * r
        b = m00 * (m10 * p00 + p01) + k0 * k1 * r
        d = m10 * m10 * p00 + 2.0 * m10 * p01 + p11 + k1 * k1 * r
        self._commit(self.altitude_m + k0 * innovation, self.velocity_m_s + k1 * innovation, a, b, d)
        return {'accepted': True, 'innovation': innovation, 'normalised_innovation_squared': nis}

    def _commit(self, altitude, velocity, a, b, d):
        if not all(math.isfinite(x) for x in (altitude, velocity, a, b, d)):
            raise EstimationError('Nonfinite estimator state')
        if a < 0 or d < 0:
            raise EstimationError('Covariance is not positive semidefinite')
        boundary = math.sqrt(a) * math.sqrt(d)
        if abs(b) > boundary and abs(b) - boundary > 1e-12 * boundary:
            raise EstimationError('Covariance is not positive semidefinite')
        self.altitude_m, self.velocity_m_s = altitude, velocity
        self.covariance = ((a, b), (b, d))
