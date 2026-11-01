"""Idealised sensor functions for the illustrative vertical model."""
import math

SEA_LEVEL_PRESSURE_PA = 101325.0
SCALE_HEIGHT_M = 8434.5

def pressure_from_altitude(altitude_m):
    if not math.isfinite(altitude_m):
        raise ValueError('Altitude must be finite')
    try:
        pressure = SEA_LEVEL_PRESSURE_PA * math.exp(-altitude_m / SCALE_HEIGHT_M)
    except OverflowError as exc:
        raise ValueError('Altitude is outside the pressure model range') from exc
    if not math.isfinite(pressure) or pressure <= 0:
        raise ValueError('Altitude is outside the pressure model range')
    return pressure

def altitude_from_pressure(pressure_pa):
    if not math.isfinite(pressure_pa) or pressure_pa <= 0:
        raise ValueError('Pressure must be finite and positive')
    return -SCALE_HEIGHT_M * math.log(pressure_pa / SEA_LEVEL_PRESSURE_PA)

def ideal_imu(vertical_acceleration_m_s2, gravity_m_s2):
    if not all(math.isfinite(v) for v in (vertical_acceleration_m_s2, gravity_m_s2)) or gravity_m_s2 < 0:
        raise ValueError('IMU inputs must be finite and gravity must not be negative')
    return {'specific_force_z_m_s2': vertical_acceleration_m_s2 + gravity_m_s2,
            'angular_rate_x_rad_s': 0.0, 'angular_rate_y_rad_s': 0.0, 'angular_rate_z_rad_s': 0.0}
