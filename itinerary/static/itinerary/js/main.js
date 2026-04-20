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
