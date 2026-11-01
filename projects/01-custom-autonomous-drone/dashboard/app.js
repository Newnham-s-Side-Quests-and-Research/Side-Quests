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
  const battery = current.battery_example;
  const power = battery.trace[position];
  const config = current.report.configuration;
  const fixed = (value, digits = 2) => Number(value).toFixed(digits);
  find('battery-voltage').textContent = format(power.voltage_v, 'V');
  find('battery-current').textContent = format(power.current_a, 'A');
  find('battery-power').textContent = format(power.power_w, 'W');
  find('battery-used').textContent = format(power.charge_used_mah, 'mAh');
  find('battery-remaining').textContent = format(power.remaining_capacity_mah, 'mAh');
  find('battery-energy').textContent = format(power.energy_used_wh, 'Wh', 4);
  find('formula-nominal').textContent = `Nominal voltage = cells times nominal voltage per cell = ${battery.cells_in_series} times 3.7 V = ${fixed(battery.nominal_voltage_v)} V.`;
  find('formula-full').textContent = `Full charge reference = cells times full charge voltage per cell = ${battery.cells_in_series} times 4.2 V = ${fixed(battery.full_charge_voltage_v)} V.`;
  find('formula-power').textContent = `Power = voltage times current = ${fixed(power.voltage_v)} V times ${fixed(power.current_a)} A = ${fixed(power.power_w)} W.`;
  find('formula-charge').textContent = `Charge used = current times elapsed seconds times 1000 divided by 3600 = ${fixed(power.current_a)} times ${fixed(row.time_s)} times 1000 divided by 3600 = ${fixed(power.charge_used_mah)} mAh.`;
  find('formula-remaining').textContent = `Estimated charge remaining = maximum of zero and capacity minus charge used = max(0, ${fixed(battery.capacity_mah)} minus ${fixed(power.charge_used_mah)}) = ${fixed(power.remaining_capacity_mah)} mAh.`;
  find('formula-energy').textContent = `Energy used = power times elapsed seconds divided by 3600 = ${fixed(power.power_w)} times ${fixed(row.time_s)} divided by 3600 = ${fixed(power.energy_used_wh, 4)} Wh.`;
  const control = row.control;
  if (control.state === 'tracking') {
    const held = control.integral_error_m_s !== control.proposed_integral_m_s;
    find('formula-error').textContent = `Altitude error = target minus estimated altitude = ${fixed(config.target_altitude_m)} minus ${fixed(row.estimate.altitude_m)} = ${fixed(control.error_m)} m.`;
    find('formula-integral').textContent = `Proposed integral = previous integral plus error times time step = ${fixed(control.integral_before_m_s, 4)} plus ${fixed(control.error_m, 4)} times ${fixed(config.dt_seconds, 4)} = ${fixed(control.proposed_integral_m_s, 4)} m s. ${held ? 'The stored integral was held because the command was saturated.' : 'The proposed integral was stored.'}`;
    find('formula-thrust').textContent = `Unbounded thrust = mass times gravity plus proportional gain times error plus integral gain times proposed integral minus velocity gain times estimated velocity = (${fixed(config.mass_kg)} times ${fixed(config.gravity_m_s2)}) plus (${fixed(config.kp_n_per_m)} times ${fixed(control.error_m)}) plus (${fixed(config.ki_n_per_m_second)} times ${fixed(control.proposed_integral_m_s, 4)}) minus (${fixed(config.kd_n_per_m_s)} times ${fixed(row.estimate.velocity_m_s)}) = ${fixed(control.unclamped_thrust_n)} N.`;
    find('formula-clamp').textContent = `Simulated thrust = unbounded thrust limited to 0 through ${fixed(config.max_thrust_n)} N = ${fixed(control.thrust_n)} N.`;
  } else {
    find('formula-error').textContent = 'The model is in its degraded state so the controller does not calculate a tracking error for this sample.';
    find('formula-integral').textContent = `The integral is held at ${fixed(control.integral_error_m_s, 4)} m s.`;
    find('formula-thrust').textContent = 'No tracking command is calculated in the degraded state.';
    find('formula-clamp').textContent = 'The model sets simulated thrust to 0 N as a test convention. This is not a flight safety procedure.';
  }
  const update = row.updates.pressure;
  if (update) {
    find('formula-innovation').textContent = `Pressure innovation = measured pressure minus predicted pressure = ${fixed(row.sensors.pressure_pa)} minus ${fixed(update.predicted_observation)} = ${fixed(update.innovation)} Pa.`;
    find('formula-variance').textContent = `Innovation variance = pressure derivative squared times prior altitude variance plus observation variance = ${fixed(update.measurement_derivative, 4)} squared times ${fixed(update.prior_altitude_variance, 6)} plus ${fixed(update.observation_variance, 2)} = ${fixed(update.innovation_variance, 4)} Pa squared.`;
    find('formula-gain').textContent = `Normalised innovation squared = innovation squared divided by innovation variance = ${fixed(update.innovation, 4)} squared divided by ${fixed(update.innovation_variance, 4)} = ${fixed(update.normalised_innovation_squared, 4)}. The limit is ${fixed(config.innovation_limit)}. The observation was ${update.accepted ? `accepted with altitude gain ${fixed(update.altitude_gain, 6)}` : 'rejected and no gain was applied'}.`;
  } else {
    find('formula-innovation').textContent = 'There is no pressure observation to calculate for this sample.';
    find('formula-variance').textContent = 'No pressure innovation variance was calculated.';
    find('formula-gain').textContent = 'No pressure update was applied.';
  }
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

let mission = null;
let missionPosition = 0;
let missionTimer = null;
let projectPoint = null;
function stopMission() {
  if (missionTimer !== null) clearInterval(missionTimer);
  missionTimer = null;
  find('mission-play').textContent = 'Play';
}
function renderMission() {
  if (!mission || !mission.trace.length) return;
  const sample = mission.trace[missionPosition];
  const completed = missionPosition === mission.trace.length - 1 && mission.status === 'complete';
  find('mission-state').textContent = completed ? 'Complete in model' : sample.state === 'moving' ? 'Moving in model' : 'Paused in model';
  find('mission-signal').textContent = sample.position_available ? 'Available' : 'Unavailable';
  find('mission-coordinates').textContent = sample.position_after_m.map(value => value.toFixed(2)).join(', ') + ' m';
  find('mission-distance').textContent = `${((mission.route.length - 1) * mission.configuration.cell_size_m).toFixed(2)} m`;
  find('mission-step').value = missionPosition;
  find('mission-step-label').textContent = `${missionPosition + 1} / ${mission.trace.length}`;
  const point = projectPoint(sample.position_after_m.map(value => value / mission.configuration.cell_size_m));
  find('mission-position').setAttribute('cx', point[0]); find('mission-position').setAttribute('cy', point[1]);
}
function drawMission() {
  const size = mission.configuration.grid.size;
  const raw = point => [point[0] - point[1], (point[0] + point[1]) / 2 - point[2]];
  const corners = [];
  for (const x of [0, size[0] - 1]) for (const y of [0, size[1] - 1]) for (const z of [0, size[2] - 1]) corners.push(raw([x,y,z]));
  const xs = corners.map(point => point[0]); const ys = corners.map(point => point[1]);
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const scale = Math.min(680 / Math.max(1, maxX - minX), 240 / Math.max(1, maxY - minY));
  projectPoint = point => { const projected = raw(point); return [400 + (projected[0] - (minX + maxX) / 2) * scale, 160 + (projected[1] - (minY + maxY) / 2) * scale]; };
  const spanX = (maxX - minX) * scale; const spanY = (maxY - minY) * scale;
  find('mission-chart').setAttribute('viewBox', `${400 - spanX / 2 - 25} ${160 - spanY / 2 - 25} ${Math.max(50, spanX + 50)} ${Math.max(50, spanY + 50)}`);
  const obstacleLayer = find('mission-obstacles'); obstacleLayer.replaceChildren();
  for (const obstacle of mission.configuration.grid.blocked) {
    const point = projectPoint(obstacle); const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', point[0]); circle.setAttribute('cy', point[1]); circle.setAttribute('r', '7'); obstacleLayer.appendChild(circle);
  }
  find('mission-route').setAttribute('points', mission.route.map(point => projectPoint(point).join(',')).join(' '));
  const goal = projectPoint(mission.route[mission.route.length - 1]);
  find('mission-goal').setAttribute('cx', goal[0]); find('mission-goal').setAttribute('cy', goal[1]);
}
find('mission-play').addEventListener('click', () => {
  if (missionTimer !== null) { stopMission(); return; }
  if (missionPosition >= mission.trace.length - 1) missionPosition = 0;
  find('mission-play').textContent = 'Pause'; renderMission();
  missionTimer = setInterval(() => {
    if (missionPosition >= mission.trace.length - 1) { stopMission(); return; }
    missionPosition += 1; renderMission();
  }, 150);
});
find('mission-step').addEventListener('input', event => { stopMission(); missionPosition = Number(event.target.value); renderMission(); });
fetch('/api/mission').then(response => {
  if (!response.ok) throw Error('Unable to load mission');
  return response.json();
}).then(report => {
  if (!Array.isArray(report.route) || !report.route.length || !Array.isArray(report.trace) || !report.trace.length) {
    find('mission-state').textContent = report.status === 'no route' ? 'No route in model' : 'No movement to replay'; return;
  }
  mission = report;
  find('mission-step').max = mission.trace.length - 1;
  find('mission-step').disabled = false; find('mission-play').disabled = false;
  drawMission(); renderMission();
}).catch(() => { find('mission-state').textContent = 'Unable to load'; });
