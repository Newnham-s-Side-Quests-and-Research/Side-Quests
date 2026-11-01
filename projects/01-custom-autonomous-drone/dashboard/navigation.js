'use strict';
(() => {
  const get = id => document.getElementById(id);
  const svg = 'http://www.w3.org/2000/svg';
  let examples = [];
  let current = null;
  let index = 0;
  let timer = null;
  const project = point => [80 + (point[0] - current.origin_m[0]) * 130,
                            250 - (point[2] - current.origin_m[2]) * 80];
  function stop() {
    if (timer !== null) clearInterval(timer);
    timer = null;
    get('navigation-play').textContent = 'Play';
  }
  function render() {
    const row = current.samples[index];
    const point = project(row.position_m);
    get('navigation-position').setAttribute('cx', point[0]);
    get('navigation-position').setAttribute('cy', point[1]);
    get('navigation-position-text').textContent = row.position_m.map(n => n.toFixed(2)).join(', ') + ' m';
    get('navigation-time').textContent = `${row.time_s.toFixed(2)} s`;
    get('navigation-estimate').textContent = `${row.estimated_altitude_m.toFixed(2)} m`;
    get('navigation-voltage').textContent = row.power ? `${row.power.loaded_voltage_v.toFixed(2)} V` : 'Unavailable';
    get('navigation-charge').textContent = row.power ? `${row.power.start_charge_mah.toFixed(1)} mAh` : 'Unavailable';
    get('navigation-current').textContent = row.power ? `${row.power.current_a.toFixed(2)} A` : 'Unavailable';
    for (let motor = 0; motor < 4; motor += 1) {
      get(`navigation-motor-${motor + 1}`).textContent = `${row.motor_thrust_n[motor].toFixed(2)} N`;
    }
    get('navigation-progress').textContent = `${current.waypoint_events.filter(event => event.time_s <= row.time_s).length} / ${current.route.length - 1}`;
    get('navigation-step').value = index;
    get('navigation-label').textContent = `${index + 1} / ${current.samples.length}`;
  }
  function select(id) {
    stop();
    current = examples.find(item => item.id === id);
    if (!current || !current.samples.length) return;
    index = 0;
    get('navigation-outcome').textContent = current.status === 'complete'
      ? 'This synthetic run reaches its planned goal in still air.'
      : `This synthetic run stops after ${current.terminal_event.time_s.toFixed(2)} seconds when the point model reaches a blocked cell. Wind is an assumed ${current.wind_m_s} m/s.`;
    const layer = get('navigation-obstacles');
    layer.replaceChildren();
    const seen = new Set();
    for (const cell of current.grid.blocked) {
      const key = `${cell[0]},${cell[2]}`;
      if (seen.has(key)) continue;
      seen.add(key);
      const centre = project(cell.map((v, i) => current.origin_m[i] + v * current.cell_size_m));
      const rectangle = document.createElementNS(svg, 'rect');
      rectangle.setAttribute('x', centre[0] - 65 * current.cell_size_m);
      rectangle.setAttribute('y', centre[1] - 40 * current.cell_size_m);
      rectangle.setAttribute('width', 130 * current.cell_size_m);
      rectangle.setAttribute('height', 80 * current.cell_size_m);
      layer.appendChild(rectangle);
    }
    get('navigation-route').setAttribute('points', current.waypoints_m.map(p => project(p).join(',')).join(' '));
    get('navigation-path').setAttribute('points', current.samples.map(row => project(row.position_m).join(',')).join(' '));
    get('navigation-step').max = current.samples.length - 1;
    get('navigation-step').disabled = false;
    get('navigation-play').disabled = false;
    render();
  }
  get('navigation-scenario').addEventListener('change', event => select(event.target.value));
  get('navigation-step').addEventListener('input', event => { stop(); index = Number(event.target.value); render(); });
  get('navigation-play').addEventListener('click', () => {
    if (timer !== null) { stop(); return; }
    if (index >= current.samples.length - 1) index = 0;
    get('navigation-play').textContent = 'Pause';
    render();
    timer = setInterval(() => {
      if (index >= current.samples.length - 1) { stop(); return; }
      index += 1;
      render();
    }, 100);
  });
  fetch('/api/navigation').then(response => {
    if (!response.ok) throw Error('Unable to load navigation');
    return response.json();
  }).then(data => {
    examples = data;
    const menu = get('navigation-scenario');
    menu.replaceChildren();
    for (const item of examples) {
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = item.id === 'calm' ? 'Still air' : 'Wind towards an obstacle';
      menu.appendChild(option);
    }
    if (!examples.length) throw Error('No navigation scenarios');
    menu.disabled = false;
    select(examples[0].id);
  }).catch(() => { get('navigation-outcome').textContent = 'The controlled mission could not be loaded.'; });
})();
