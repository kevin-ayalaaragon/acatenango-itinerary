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

  const map = L.map('map', { zoomControl: true, attributionControl: true })
    .setView([14.52, -90.80], 11);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19,
  }).addTo(map);

  // Route polyline — split into done (grey) and upcoming (ember)
  const doneLatLngs     = [];
  const upcomingLatLngs = [];
  let hitToday = false;

  STOPS.forEach(s => {
    if (s.status === 'done') {
      doneLatLngs.push([s.lat, s.lng]);
    } else {
      if (!hitToday && s.status === 'today') {
        // Bridge the gap between done and today
        const last = doneLatLngs[doneLatLngs.length - 1];
        if (last) upcomingLatLngs.push(last);
        hitToday = true;
      }
      upcomingLatLngs.push([s.lat, s.lng]);
    }
  });

  if (doneLatLngs.length > 1) {
    L.polyline(doneLatLngs, { color: '#555', weight: 2, opacity: 0.4 }).addTo(map);
  }
  if (upcomingLatLngs.length > 1) {
    L.polyline(upcomingLatLngs, { color: '#e8500a', weight: 2.5, opacity: 0.7 }).addTo(map);
  }
  // Fallback if no status data
  if (doneLatLngs.length <= 1 && upcomingLatLngs.length <= 1) {
    L.polyline(STOPS.map(s => [s.lat, s.lng]), { color: '#e8500a', weight: 2.5, opacity: 0.7 }).addTo(map);
  }

  // Marker styles per status
  function makeIcon(stop) {
    const status   = stop.status || 'upcoming';
    const isSummit = stop.id === 'summit';

    let color, size, shadow, pulse = '';

    if (status === 'done') {
      color  = '#555555';
      size   = 10;
      shadow = '0 0 4px #33333388';
    } else if (status === 'today') {
      color  = '#c9a84c';
      size   = 18;
      shadow = `0 0 16px #c9a84caa`;
      pulse  = `animation: markerPulse 1.8s ease-in-out infinite;`;
    } else {
      // upcoming
      color  = isSummit ? '#c9a84c' : '#e8500a';
      size   = isSummit ? 16 : 13;
      shadow = `0 0 ${isSummit ? 14 : 8}px ${color}88`;
    }

    return L.divIcon({
      className: '',
      html: `<div style="
        width:${size}px;height:${size}px;border-radius:50%;
        background:${color};border:2px solid #1a1814;
        box-shadow:${shadow};${pulse}
      "></div>`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    });
  }

  // Inject pulse keyframe once
  if (!document.getElementById('marker-pulse-style')) {
    const style = document.createElement('style');
    style.id = 'marker-pulse-style';
    style.textContent = `
      @keyframes markerPulse {
        0%,100% { transform: scale(1);   opacity: 1;   }
        50%      { transform: scale(1.4); opacity: 0.8; }
      }
    `;
    document.head.appendChild(style);
  }

  const stopEls = document.querySelectorAll('.stop-item');

  const markers = STOPS.map((stop, i) => {
    const marker = L.marker([stop.lat, stop.lng], { icon: makeIcon(stop) })
      .addTo(map)
      .on('click', () => activateStop(i));
    return marker;
  });

  // Auto-fly to today's stop on load
  const todayIdx = STOPS.findIndex(s => s.status === 'today');
  if (todayIdx !== -1) {
    map.setView([STOPS[todayIdx].lat, STOPS[todayIdx].lng], 12);
  }

  stopEls.forEach((el, i) => {
    el.addEventListener('click', () => {
      activateStop(i);
      map.flyTo([STOPS[i].lat, STOPS[i].lng], 13, { duration: 0.8 });
    });
  });

  function activateStop(idx) {
    stopEls.forEach(el => el.classList.remove('active'));
    stopEls[idx]?.classList.add('active');
    const el = markers[idx]?.getElement();
    if (el) {
      el.style.transition = 'transform .15s';
      el.style.transform  = 'scale(1.7)';
      setTimeout(() => { el.style.transform = 'scale(1)'; }, 300);
    }
  }

  activateStop(todayIdx !== -1 ? todayIdx : 0);
})();
