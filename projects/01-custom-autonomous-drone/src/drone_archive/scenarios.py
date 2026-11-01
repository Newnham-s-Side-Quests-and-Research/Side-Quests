"""Define reproducible scenarios for the local demonstration."""
from copy import deepcopy
from .closed_loop import simulate_closed_loop
from .metrics import summarise
from .battery import power_example
from .simulation import SimulationError

def build_scenarios(config):
    steps = config.get('steps') if isinstance(config, dict) else None
    if isinstance(steps, bool) or not isinstance(steps, int) or not 20 <= steps <= 5000:
        raise SimulationError('Dashboard scenarios require between 20 and 5000 steps')
    start = steps // 3
    end = min(steps, start + max(2, steps // 10))
    specs = [
        ('baseline', 'Normal signals', 'Run with the configured synthetic sensor noise.', {}),
        ('position_outage', 'Position observations lost', 'Pressure and GPS altitude readings are unavailable during the marked interval.',
         {'pressure_dropout': {'start': start, 'end': end}, 'gps_dropout': {'start': start, 'end': end}}),
        ('imu_outage', 'Motion signal lost', 'The synthetic motion signal is unavailable during the marked interval.',
         {'imu_dropout': {'start': start, 'end': end}}),
        ('pressure_bias', 'Pressure reading biased', 'A large pressure offset is introduced while GPS altitude readings continue.',
         {'pressure_bias': {'start': start, 'end': end, 'amount': 1000.0}}),
    ]
    scenarios = []
    for identity, title, description, overrides in specs:
        settings = deepcopy(config)
        for key in ('pressure_dropout', 'gps_dropout', 'imu_dropout', 'pressure_bias', 'gps_bias'):
            settings[key] = None
        settings.update(overrides)
        report = simulate_closed_loop(settings)
        battery = power_example(voltage_v=11.1, current_a=8.0, capacity_mah=1500.0,
                                dt_seconds=settings['dt_seconds'], samples=steps)
        scenarios.append({'id': identity, 'title': title, 'description': description, 'battery_example': battery,
                          'fault_interval': None if identity == 'baseline' else {'start': start, 'end': end},
                          'metrics': summarise(report), 'report': report})
    return scenarios
