// PROTOTYP: Strandkarte (OpenStreetMap über Leaflet) und Google-Karte erst nach Klick
const initBeaches = () => {
  const data = document.getElementById('beach-data');
  const B = data ? JSON.parse(data.textContent) : [];
  const mapEl = document.getElementById('beach-map');
  const list = document.getElementById('beach-list');
  if (!B.length || !mapEl || !list) return;

  list.classList.add('js-beach');
  let current = 0;
  let gframe = null;
  const gsrc = (b) => `https://www.google.com/maps?q=${b.lat},${b.lon}&z=14&output=embed`;

  const markers = [];
  let map = null;
  if (window.L) {
    mapEl.innerHTML = '';
    map = L.map(mapEl, { scrollWheelZoom: false, zoomControl: true }).setView([54.46, 11.16], 11);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);
    B.forEach((b, i) => {
      const icon = L.divIcon({ className: 'bpin', html: `<span>${i + 1}</span>`, iconSize: [30, 30], iconAnchor: [15, 15] });
      const m = L.marker([b.lat, b.lon], { icon, title: b.name }).addTo(map);
      m.bindPopup(`<div class="bpop">${b.img ? `<img src="${b.img}" alt="${b.name}">` : ''}<strong>${b.name}</strong><br>${b.text || ''}</div>`, { maxWidth: 240 });
      m.on('click', () => select(i, false));
      markers.push(m);
    });
    map.invalidateSize();
    map.fitBounds(L.latLngBounds(B.map((b) => [b.lat, b.lon])).pad(0.3));
  }

  function select(i, fly = true) {
    current = i;
    list.querySelectorAll('.bitem').forEach((li) => li.classList.toggle('is-active', +li.dataset.i === i));
    list.querySelectorAll('.bitem-btn').forEach((b) => b.setAttribute('aria-pressed', String(+b.dataset.i === i)));
    if (map && fly) { map.flyTo([B[i].lat, B[i].lon], 13, { duration: 0.6 }); markers[i].openPopup(); }
    if (gframe) gframe.src = gsrc(B[i]);
  }

  const showThumb = (t) => {
    const li = t.closest('.bitem'); const big = li.querySelector('.bbig');
    big.src = t.dataset.src;
    li.querySelectorAll('.bthumb').forEach((x) => x.setAttribute('aria-pressed', String(x === t)));
  };
  list.addEventListener('keydown', (e) => {
    const t = e.target.closest('.bthumb'); if (t && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); showThumb(t); }
  });
  list.addEventListener('click', (e) => {
    const t = e.target.closest('.bthumb'); if (t) { showThumb(t); return; }
    const b = e.target.closest('.bitem-btn'); if (!b) return;
    select(+b.dataset.i);
  });

  // Eine Karte, zwei Ansichten: Übersicht (OpenStreetMap) oder Google Maps nach Zustimmung
  const gbox = document.getElementById('gmap');
  const tabs = document.querySelectorAll('.map-tabs button');
  const show = (view) => {
    tabs.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.view === view)));
    mapEl.hidden = view !== 'osm';
    gbox.hidden = view !== 'google';
    if (view === 'osm' && map) map.invalidateSize();
  };
  tabs.forEach((b) => b.addEventListener('click', () => show(b.dataset.view)));
  document.getElementById('gmap-load').addEventListener('click', () => {
    gframe = document.createElement('iframe');
    gframe.title = 'Google Maps: gewählter Strand';
    gframe.referrerPolicy = 'no-referrer-when-downgrade';
    gframe.src = gsrc(B[current]);
    gbox.replaceChildren(gframe);
    gbox.classList.add('is-loaded');
  });

  select(0, false);
};
if (document.readyState === 'complete') initBeaches(); else window.addEventListener('load', initBeaches);
