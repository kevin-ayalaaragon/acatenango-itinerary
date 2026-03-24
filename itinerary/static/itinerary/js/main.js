/* ── SCROLL REVEAL ── */
const observer = new IntersectionObserver(
  entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
  { threshold: 0.1 }
);
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

/* ── LEAFLET MAP (free, no API key) ── */
(function initLeafletMap() {
  const STOPS = window.STOPS_DATA || [];
  if (!STOPS.length || typeof L === 'undefined') return;

  // Dark OSM tile layer via CartoDB Dark Matter (free, no key)
  const map = L.map('map', { zoomControl: true, attributionControl: true })
    .setView([14.52, -90.80], 11);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19,
  }).addTo(map);

  // Route polyline
  const latlngs = STOPS.map(s => [s.lat, s.lng]);
  L.polyline(latlngs, { color: '#e8500a', weight: 2.5, opacity: 0.7 }).addTo(map);

  // Custom circular marker using divIcon
  function makeIcon(stop) {
    const isSummit = stop.id === 'summit';
    const size = isSummit ? 18 : 14;
    const color = isSummit ? '#c9a84c' : '#e8500a';
    return L.divIcon({
      className: '',
      html: `<div style="
        width:${size}px;height:${size}px;border-radius:50%;
        background:${color};border:2px solid #1a1814;
        box-shadow:0 0 ${isSummit ? 14 : 8}px ${color}88;
      "></div>`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    });
  }

  const stopEls = document.querySelectorAll('.stop-item');

  const markers = STOPS.map((stop, i) => {
    const marker = L.marker([stop.lat, stop.lng], { icon: makeIcon(stop) })
      .addTo(map)
      .on('click', () => activateStop(i));
    return marker;
  });

  stopEls.forEach((el, i) => {
    el.addEventListener('click', () => {
      activateStop(i);
      map.flyTo([STOPS[i].lat, STOPS[i].lng], 13, { duration: 0.8 });
    });
  });

  function activateStop(idx) {
    stopEls.forEach(el => el.classList.remove('active'));
    stopEls[idx]?.classList.add('active');
    // Pulse effect: briefly scale the marker
    const el = markers[idx]?.getElement();
    if (el) {
      el.style.transition = 'transform .15s';
      el.style.transform = 'scale(1.7)';
      setTimeout(() => { el.style.transform = 'scale(1)'; }, 300);
    }
  }

  activateStop(0);
})();

/* ── WEATHER TOGGLE ── */
(function () {
  const toggle   = document.getElementById('weather-toggle');
  const panel    = document.getElementById('weather-panel');
  const refreshBtn = document.getElementById('weather-refresh');

  if (!toggle) return;

  // Persist preference in localStorage
  const PREF_KEY = 'acatenango_weather_on';
  const saved = localStorage.getItem(PREF_KEY);
  if (saved === 'false') {
    toggle.checked = false;
    showOff();
  }

  toggle.addEventListener('change', () => {
    localStorage.setItem(PREF_KEY, toggle.checked);
    if (toggle.checked) {
      fetchWeather();
    } else {
      showOff();
    }
  });

  if (refreshBtn) {
    refreshBtn.addEventListener('click', fetchWeather);
  }

  function fetchWeather() {
    panel.innerHTML = '<span class="weather-loading">Fetching summit conditions…</span>';
    fetch('/api/weather/')
      .then(r => r.json())
      .then(data => {
        if (!data.enabled) { showOff(); return; }
        if (data.error)    { showError(data.error); return; }
        renderWeather(data.weather);
      })
      .catch(() => showError('Could not reach weather service'));
  }

  function renderWeather(w) {
    const advisoryClass = {
      good: 'advisory-good', ok: 'advisory-ok', warn: 'advisory-warn'
    }[w.hiking_advisory?.level] || 'advisory-ok';

    panel.innerHTML = `
      <div class="weather-content">
        <span class="weather-emoji">${w.emoji}</span>
        <div>
          <div class="weather-temp">${w.temp_c}°C</div>
          <div class="weather-desc">${w.description}</div>
        </div>
        <div class="weather-meta">
          <span>Feels ${w.apparent_c}°C</span>
          <span>Wind ${w.wind_kmh} km/h</span>
          <span>Gusts ${w.gusts_kmh} km/h</span>
          <span>Cloud ${w.cloud_pct}%</span>
          <span>Visibility ${w.visibility_km} km</span>
          <span>Precip ${w.precip_mm} mm</span>
        </div>
        ${w.hiking_advisory ? `<div class="weather-advisory ${advisoryClass}">${w.hiking_advisory.text}</div>` : ''}
        <div style="margin-top:.5rem">
          <span style="font-family:'Space Mono',monospace;font-size:.58rem;color:var(--mist)">
            Updated ${w.fetched_at} local time
          </span>
          <button class="weather-refresh-btn" id="weather-refresh" style="margin-left:1rem">↻ Refresh</button>
        </div>
      </div>
    `;
    // Re-bind the new refresh button
    document.getElementById('weather-refresh')?.addEventListener('click', fetchWeather);
  }

  function showOff() {
    panel.innerHTML = '<span class="weather-off">Live weather is off</span>';
  }
  function showError(msg) {
    panel.innerHTML = `<span class="weather-error">⚠ ${msg}</span>`;
  }
})();
