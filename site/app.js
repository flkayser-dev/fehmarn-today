// PROTOTYP: Kalender-Logik für Fehmarn Today. Ohne JavaScript bleiben die Kacheln von heute stehen.
(() => {
  const EV = JSON.parse(document.getElementById('events-data').textContent);
  const TODAY = document.querySelector('.hero time[datetime]').getAttribute('datetime');
  const WD = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];
  const MO = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
  const CAT_ORDER = ['Märkte', 'Musik & Bühne', 'Kinder & Familie', 'Draußen & Führungen', 'Kurse & Workshops', 'Sonstiges'];
  const PAGE = 8;
  const $ = (s) => document.querySelector(s);
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  const parse = (s) => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };
  const addDays = (s, n) => { const d = parse(s); d.setDate(d.getDate() + n); return iso(d); };
  const wdIdx = (s) => (parse(s).getDay() + 6) % 7;
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const PIN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>';
  const CLOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>';

  // Auswahl: ein Tag (day) oder ein Zeitraum (range)
  const state = { day: TODAY, range: null, town: '', cat: '', free: false, shown: PAGE, month: parse(TODAY), barStart: TODAY };
  const BAR_DAYS = 7;
  const tn = (n) => `${n} ${n === 1 ? 'Termin' : 'Termine'}`;
  const satFrom = (s) => { const wd = wdIdx(s); return wd === 6 ? addDays(s, 6) : addDays(s, 5 - wd); }; // sonntags: das kommende Wochenende, wie oben in der Startkachel

  const count = (list, key) => list.reduce((m, e) => (m.set(e[key], (m.get(e[key]) || 0) + 1), m), new Map());
  const townSel = $('#f-town');
  [['Auf Fehmarn', true], ['Ostholstein und Umgebung', false]].forEach(([label, f]) => {
    const g = document.createElement('optgroup'); g.label = label;
    [...count(EV.filter((e) => e.fehmarn === f), 'town')].sort((a, b) => b[1] - a[1])
      .forEach(([v, n]) => g.insertAdjacentHTML('beforeend', `<option value="${esc(v)}">${esc(v)} (${n})</option>`));
    townSel.append(g);
  });
  const cats = count(EV, 'cat');
  $('#cats').insertAdjacentHTML('beforeend', ['', ...CAT_ORDER.filter((c) => cats.has(c))]
    .map((c) => `<button type="button" data-cat="${esc(c)}" aria-pressed="${c === ''}">${c ? esc(c) : 'Alles'}</button>`).join(''));

  function bounds() {
    if (state.day) return [state.day, state.day];
    const wd = wdIdx(TODAY);
    switch (state.range) {
      case 'weekend': { const sat = satFrom(state.barStart); return [sat < TODAY ? TODAY : sat, addDays(sat, 1)]; }
      case 'week': return [TODAY, addDays(TODAY, 6)];
      default: return [TODAY, '9999-12-31'];
    }
  }
  const matches = (e) => (!state.town || e.town === state.town) && (!state.cat || e.cat === state.cat) && (!state.free || e.free);
  const filtered = () => { const [a, b] = bounds(); return EV.filter((e) => e.date >= a && e.date <= b && matches(e)); };

  const card = (e) => `<li class="card"><a class="card-link" href="${esc(e.url)}"><span class="card-photo">`
    + `<img src="img/k/${esc(e.img)}.jpg" alt="${esc(e.alt)}" loading="lazy" width="900" height="600"><span class="card-cat">${esc(e.cat)}</span></span>`
    + `<span class="card-body"><span class="card-title">${esc(e.title)}</span><span class="card-meta">`
    + `<span>${PIN}${esc(e.town)}</span><span>${CAL}${WD[wdIdx(e.date)]}, ${parse(e.date).getDate()}. ${MO[parse(e.date).getMonth()]}</span>`
    + `<span>${CLOCK}${esc(e.time ? e.time + ' Uhr' : 'ganztags')}</span>${e.free ? '<span class="card-free">Eintritt frei</span>' : ''}</span></span></a>`
    + `<button type="button" class="card-add" data-i="${EV.indexOf(e)}">${CAL}In Kalender</button></li>`;

  // Ein Klick: Termin als .ics-Datei (Was, Wann, Wo), öffnet sich in Apple-, Google- oder Outlook-Kalender
  const CAL = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M12 14v4M10 16h4"/></svg>';
  const icsText = (s) => String(s).replace(/\\/g, '\\\\').replace(/[,;]/g, (c) => '\\' + c).replace(/\n/g, '\\n');
  function ics(e) {
    const d = e.date.replace(/-/g, '');
    const times = (e.time || '').match(/\d{1,2}[:.]\d{2}/g) || [];
    const hm = (t) => t.replace('.', ':').split(':').map((x) => x.padStart(2, '0')).join('') + '00';
    let when;
    if (times.length) {
      const start = hm(times[0]);
      let end = times[1] ? hm(times[1]) : String(Math.min(23, +start.slice(0, 2) + 2)).padStart(2, '0') + start.slice(2);
      when = [`DTSTART:${d}T${start}`, `DTEND:${d}T${end}`];
    } else {
      when = [`DTSTART;VALUE=DATE:${d}`, `DTEND;VALUE=DATE:${addDays(e.date, 1).replace(/-/g, '')}`];
    }
    const where = e.town === 'Fehmarn' || e.town === 'Ostholstein' || e.town === 'Lübeck' ? e.town : `${e.town}, ${e.fehmarn ? 'Fehmarn' : 'Ostholstein'}`;
    const uid = [...(e.date + e.title + e.town)].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7).toString(36);
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, '');
    return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Fehmarn Today//Prototyp//DE', 'CALSCALE:GREGORIAN', 'BEGIN:VEVENT',
      `UID:${d}-${uid}@fehmarn-today`, `DTSTAMP:${stamp}`, ...when,
      `SUMMARY:${icsText(e.title)}`, `LOCATION:${icsText(where)}`,
      `DESCRIPTION:${icsText(`${e.cat}. Mehr Infos: ${e.url}`)}`, `URL:${e.url}`, 'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
  }
  document.getElementById('days').addEventListener('click', (ev) => {
    const b = ev.target.closest('.card-add'); if (!b) return;
    const e = EV[+b.dataset.i];
    const blob = new Blob([ics(e)], { type: 'text/calendar;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${e.date}-${e.title.toLowerCase().replace(/[^a-z0-9äöüß]+/g, '-').replace(/^-|-$/g, '').slice(0, 40)}.ics`;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    b.innerHTML = `${CAL}Gespeichert`;
  });

  function renderList() {
    const list = filtered();
    const byDay = new Map();
    list.slice(0, state.shown).forEach((e) => byDay.set(e.date, [...(byDay.get(e.date) || []), e]));
    const total = count(list, 'date');
    $('#days').innerHTML = byDay.size
      ? [...byDay].map(([d, evs]) => {
        const dt = parse(d);
        return `<section class="day" aria-labelledby="d${d}"><h3 class="day-head" id="d${d}">${WD[wdIdx(d)]}, ${dt.getDate()}. ${MO[dt.getMonth()]}`
          + `<span class="day-n">${tn(total.get(d))}</span></h3><ul class="cards">${evs.map(card).join('')}</ul></section>`;
      }).join('')
      : '<p class="empty">An diesem Tag ist mit dieser Auswahl nichts eingetragen. Rechts im Kalender einen anderen Tag wählen.</p>';
    $('#more').hidden = list.length <= state.shown;
  }

  function renderMonth() {
    const m = state.month;
    const y = m.getFullYear(), mo = m.getMonth();
    $('#m-title').textContent = `${MO[mo]} ${y}`;
    const per = count(EV.filter(matches), 'date');
    const first = (new Date(y, mo, 1).getDay() + 6) % 7;
    const len = new Date(y, mo + 1, 0).getDate();
    let h = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'].map((d) => `<span class="wd">${d}</span>`).join('');
    h += '<span class="pad"></span>'.repeat(first);
    for (let d = 1; d <= len; d++) {
      const s = iso(new Date(y, mo, d));
      const n = per.get(s) || 0;
      const past = s < TODAY;
      h += `<button type="button" data-day="${s}" aria-pressed="${state.day === s}" class="${s === TODAY ? 'is-today' : ''}" ${past || !n ? 'disabled' : ''}`
        + ` aria-label="${d}. ${MO[mo]}, ${n} Termine">${d}${n && !past ? `<small>${n}</small>` : ''}</button>`;
    }
    h += '<span class="pad"></span>'.repeat((7 - ((first + len) % 7)) % 7);
    $('#m-grid').innerHTML = h;
    const minMonth = parse(TODAY);
    $('#m-prev').disabled = y === minMonth.getFullYear() && mo === minMonth.getMonth();
  }

  // Tagesleiste: sieben Tage ab barStart, folgt dem gewählten Tag
  function renderBar() {
    const per = count(EV.filter(matches), 'date');
    const rel = ['Heute', 'Morgen', 'Übermorgen'];
    let h = '';
    for (let i = 0; i < BAR_DAYS; i++) {
      const s = addDays(state.barStart, i);
      const d = parse(s);
      const off = Math.round((d - parse(TODAY)) / 864e5);
      const name = off < 3 ? rel[off] : WD[wdIdx(s)];
      const n = per.get(s) || 0;
      h += `<button type="button" data-day="${s}" aria-pressed="${state.day === s}"${n ? '' : ' disabled'}>`
        + `<span class="db-name">${name}</span><span class="db-date num">${d.getDate()}. ${MO[d.getMonth()].slice(0, 3)}.</span><span class="db-n">${n ? tn(n) : 'keine'}</span></button>`;
    }
    const sat = satFrom(state.barStart);
    const wkN = (per.get(sat) || 0) + (per.get(addDays(sat, 1)) || 0);
    h += `<button type="button" data-range="weekend" aria-pressed="${state.range === 'weekend'}"><span class="db-name">Wochenende</span>`
      + `<span class="db-date num">${parse(sat).getDate()}. bis ${parse(addDays(sat, 1)).getDate()}. ${MO[parse(addDays(sat, 1)).getMonth()].slice(0, 3)}.</span><span class="db-n">${tn(wkN)}</span></button>`;
    h += `<button type="button" data-range="all" aria-pressed="${state.range === 'all'}"><span class="db-name">Alle</span><span class="db-date">ab heute</span><span class="db-n">${tn(EV.filter(matches).length)}</span></button>`;
    $('#daybar').innerHTML = h;
    $('#db-prev').disabled = state.barStart <= TODAY;
  }
  const render = () => { renderBar(); renderMonth(); renderList(); };
  const pick = ({ day = null, range = null }) => {
    state.day = day; state.range = range; state.shown = PAGE;
    if (day) {
      state.month = new Date(parse(day).getFullYear(), parse(day).getMonth(), 1);
      if (day < state.barStart || day > addDays(state.barStart, BAR_DAYS - 1)) state.barStart = day;
    }
    if (range === 'week' || (range === 'all')) state.barStart = TODAY;
    render();
  };

  $('#daybar').addEventListener('click', (e) => {
    const b = e.target.closest('button'); if (!b || b.disabled) return;
    pick(b.dataset.day ? { day: b.dataset.day } : { range: b.dataset.range });
  });
  $('#m-grid').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-day]'); if (!b) return;
    pick({ day: b.dataset.day });
    if (window.matchMedia('(max-width: 60rem)').matches) $('#days').scrollIntoView({ block: 'start' });
  });
  $('#cats').addEventListener('click', (e) => {
    const b = e.target.closest('button'); if (!b) return;
    state.cat = b.dataset.cat; state.shown = PAGE;
    document.querySelectorAll('#cats button').forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.cat === state.cat)));
    render();
  });
  townSel.addEventListener('change', (e) => { state.town = e.target.value; state.shown = PAGE; render(); });
  $('#f-free').addEventListener('change', (e) => { state.free = e.target.checked; state.shown = PAGE; render(); });
  $('#more').addEventListener('click', () => { state.shown += PAGE; renderList(); });
  const step = (n) => {
    const s = addDays(state.barStart, n);
    state.barStart = s < TODAY ? TODAY : s;
    renderBar();
  };
  $('#db-prev').addEventListener('click', () => step(-BAR_DAYS));
  $('#db-next').addEventListener('click', () => step(BAR_DAYS));
  $('#m-prev').addEventListener('click', () => { state.month = new Date(state.month.getFullYear(), state.month.getMonth() - 1, 1); renderMonth(); });
  $('#m-next').addEventListener('click', () => { state.month = new Date(state.month.getFullYear(), state.month.getMonth() + 1, 1); renderMonth(); });
  document.querySelectorAll('.quick-tile[data-range]').forEach((a) => a.addEventListener('click', () => {
    const r = a.dataset.range;
    pick(r === 'today' ? { day: TODAY } : r === 'tomorrow' ? { day: addDays(TODAY, 1) } : { range: r });
  }));
  document.querySelectorAll('.town[data-town]').forEach((a) => a.addEventListener('click', () => {
    state.town = a.dataset.town; townSel.value = state.town; pick({ range: 'all' });
  }));

  // Jahresplaner: ein Monat auf einmal
  const months = [...document.querySelectorAll('.y-month[data-m]')];
  if (months.length) {
    const tabs = $('#year-tabs');
    tabs.innerHTML = months.map((li) => `<button type="button" data-m="${li.dataset.m}" aria-pressed="false">${MO[li.dataset.m - 1].slice(0, 3)}<small>${li.dataset.n}</small></button>`).join('');
    const show = (m) => {
      months.forEach((li) => { li.hidden = li.dataset.m !== m; });
      tabs.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.m === m)));
    };
    tabs.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) show(b.dataset.m); });
    tabs.hidden = false;
    document.querySelector('.year-grid').classList.add('is-single');
    show((months.find((li) => +li.dataset.n > 0) || months[0]).dataset.m);
  }

  // Formular: noch ohne Ziel, nichts wird gesendet
  // Formulare: siehe upload.js

  $('#daybar-wrap').hidden = false;
  $('#side').hidden = false;
  render();
})();
