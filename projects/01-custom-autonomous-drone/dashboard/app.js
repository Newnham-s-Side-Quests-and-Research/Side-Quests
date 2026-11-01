'use strict';
const find = id => document.getElementById(id);
let trace = [];
let position = 0;
let timer = null;
const format = (value, unit, decimals = 2) => value === null || value === undefined ? 'Unavailable' : `${Number(value).toFixed(decimals)} ${unit}`;

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
  find('gps').textContent = format(row.sensors.gps_altitude_m, 'm');
  find('acceleration').textContent = format(row.sensors.imu_acceleration_m_s2, 'm/s²');
  const updates = [row.updates.pressure, row.updates.gps].filter(Boolean);
  find('observation').textContent = updates.some(update => update.accepted) ? 'Yes' : 'None';
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
fetch('/api/trace').then(response => {
  if (!response.ok) throw Error('Unable to load the simulation');
  return response.json();
}).then(report => {
  if (!Array.isArray(report.trace) || !report.trace.length) throw Error('The simulation has no samples');
  trace = report.trace;
  find('step').max = trace.length - 1;
  find('step').disabled = false;
  find('play').disabled = false;
  drawChart(); render();
}).catch(() => {
  find('mode').textContent = 'Unavailable';
  find('error').textContent = 'The simulation could not be loaded. Check the local server and try again.';
  find('error').hidden = false;
});
