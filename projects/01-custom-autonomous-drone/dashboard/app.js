'use strict';
const find = id => document.getElementById(id);
let scenarios = [];
let current = null;
let trace = [];
let position = 0;
let timer = null;
const format = (value, unit, decimals = 2) => value === null || value === undefined ? 'Unavailable' : `${Number(value).toFixed(decimals)} ${unit}`;

function updateLabel(update, available, scheduled = true) {
  if (!scheduled) return 'Not scheduled';
  if (!available || update === null) return 'Unavailable';
  return update.accepted ? 'Accepted' : 'Rejected';
}

function render() {
  const row = trace[position];
  if (!row) return;
  find('mode').textContent = row.control.state === 'tracking' ? 'Tracking in simulation' : 'Degraded in simulation';
  find('time').textContent = `${row.time_s.toFixed(2)} seconds`;
  find('altitude').textContent = format(row.truth.altitude_m, 'm');
  find('estimated-altitude').textContent = format(row.estimate.altitude_m, 'm');
  find('velocity').textContent = format(row.estimate.velocity_m_s, 'm/s');
  find('thrust').textContent = format(row.control.thrust_n, 'N');
  find('pressure').textContent = format(row.sensors.pressure_pa, 'Pa', 0);
  find('pressure-update').textContent = updateLabel(row.updates.pressure, row.sensors.pressure_pa !== null);
  find('gps').textContent = format(row.sensors.gps_altitude_m, 'm');
  find('gps-update').textContent = updateLabel(row.updates.gps, row.sensors.gps_altitude_m !== null, row.step % current.report.configuration.gps_interval_steps === 0);
  find('acceleration').textContent = format(row.sensors.imu_acceleration_m_s2, 'm/s²');
  find('variance').textContent = format(row.estimate.covariance[0][0], 'm²', 4);
  find('stale').textContent = String(row.estimate.unobserved_steps);
  find('step').value = position;
  find('step-label').textContent = `${position + 1} / ${trace.length}`;
  const x = trace.length > 1 ? position * 800 / (trace.length - 1) : 0;
  find('cursor').setAttribute('x1', x); find('cursor').setAttribute('x2', x);
}

function stop() {
  if (timer !== null) clearInterval(timer);
  timer = null;
  find('play').textContent = 'Play';
}

function drawChart() {
  let low = Infinity; let high = -Infinity;
  for (const row of trace) {
    low = Math.min(low, row.truth.altitude_m, row.estimate.altitude_m);
    high = Math.max(high, row.truth.altitude_m, row.estimate.altitude_m);
  }
  const spread = Math.max(high - low, 0.1);
  const points = key => trace.map((row, index) => {
    const x = trace.length > 1 ? index * 800 / (trace.length - 1) : 0;
    const value = key === 'truth' ? row.truth.altitude_m : row.estimate.altitude_m;
    return `${x.toFixed(2)},${(220 - (value - low) * 200 / spread).toFixed(2)}`;
  }).join(' ');
  find('truth-line').setAttribute('points', points('truth'));
  find('estimate-line').setAttribute('points', points('estimate'));
  find('chart-min').textContent = `${low.toFixed(2)} m`;
  find('chart-max').textContent = `${high.toFixed(2)} m`;
  const fault = current.fault_interval;
  const factor = trace.length > 1 ? 800 / (trace.length - 1) : 0;
  const x = fault ? fault.start * factor : 0;
  const end = fault ? Math.min(800, fault.end * factor) : 0;
  find('fault-region').setAttribute('x', x.toFixed(2));
  find('fault-region').setAttribute('width', Math.max(0, end - x).toFixed(2));
}

function showScenario(id) {
  stop();
  current = scenarios.find(scenario => scenario.id === id);
  if (!current) return;
  trace = current.report.trace;
  position = 0;
  find('scenario-description').textContent = current.description;
  find('fault-window').textContent = current.fault_interval ? `Fault applied from sample ${current.fault_interval.start + 1} to ${current.fault_interval.end}.` : 'No fault is injected in this scenario.';
  const metric = current.metrics;
  find('tracking-rms').textContent = format(metric.tracking_rmse_m, 'm');
  find('estimation-rms').textContent = format(metric.estimation_rmse_m, 'm');
  find('peak-error').textContent = format(metric.maximum_absolute_tracking_error_m, 'm');
  find('degraded-count').textContent = `${metric.degraded_steps} / ${metric.sample_count}`;
  find('pressure-summary').textContent = `${metric.pressure_accepted} accepted / ${metric.pressure_rejected} rejected / ${metric.pressure_missing} missing`;
  find('gps-summary').textContent = `${metric.gps_accepted} accepted / ${metric.gps_rejected} rejected / ${metric.gps_missing_on_schedule} missing of ${metric.gps_scheduled} scheduled`;
  find('imu-summary').textContent = `${metric.imu_missing} / ${metric.sample_count}`;
  find('max-thrust').textContent = format(metric.maximum_thrust_n, 'N');
  find('step').max = trace.length - 1;
  find('step').disabled = false;
  find('play').disabled = false;
  find('download').disabled = false;
  drawChart(); render();
}

find('play').addEventListener('click', () => {
  if (timer !== null) { stop(); return; }
  if (position >= trace.length - 1) position = 0;
  find('play').textContent = 'Pause';
  render();
  timer = setInterval(() => {
    if (position >= trace.length - 1) { stop(); return; }
    position += 1; render();
  }, 100);
});
find('step').addEventListener('input', event => { stop(); position = Number(event.target.value); render(); });
find('scenario').addEventListener('change', event => showScenario(event.target.value));
find('download').addEventListener('click', () => {
  if (!current) return;
  const blob = new Blob([JSON.stringify(current, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = `${current.id}.json`; document.body.appendChild(link); link.click(); link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
});
fetch('/api/scenarios').then(response => {
  if (!response.ok) throw Error('Unable to load the simulation');
  return response.json();
}).then(data => {
  if (!Array.isArray(data) || !data.length || data.some(item => !Array.isArray(item.report?.trace) || !item.report.trace.length)) throw Error('A scenario has no samples');
  scenarios = data;
  const select = find('scenario'); select.replaceChildren();
  for (const scenario of scenarios) {
    const option = document.createElement('option'); option.value = scenario.id; option.textContent = scenario.title; select.appendChild(option);
  }
  select.disabled = false;
  showScenario(scenarios[0].id);
}).catch(() => {
  find('mode').textContent = 'Unavailable';
  find('error').textContent = 'The simulation could not be loaded. Check the local server and try again.';
  find('error').hidden = false;
});
