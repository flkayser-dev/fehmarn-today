// PROTOTYP: Aktivitäten filtern (Wasser, Natur & Ausflüge, Sport & Freizeit) und nachladen
const tileFilter = (prefix, withKids, withTown) => {
  const list = document.getElementById(`${prefix}-list`);
  const bar = document.getElementById(`${prefix}-filter`);
  const more = document.getElementById(`${prefix}-more`);
  if (!list || !bar) return;
  const items = [...list.querySelectorAll('.akt-item')];
  if (!items.length) return;
  const PAGE = 12;
  let cat = '';
  let shown = PAGE;

  const counts = items.reduce((m, li) => m.set(li.dataset.cat, (m.get(li.dataset.cat) || 0) + 1), new Map());
  const kidsN = withKids ? items.filter((li) => li.dataset.kids).length : 0;
  bar.innerHTML = `<button type="button" data-cat="" aria-pressed="true">Alle <small>${items.length}</small></button>`
    + [...counts].map(([c, n]) => `<button type="button" data-cat="${c}" aria-pressed="false">${c} <small>${n}</small></button>`).join('')
    + (kidsN ? `<button type="button" data-cat="Kinder" aria-pressed="false">Kinder <small>${kidsN}</small></button>` : '');
  const inCat = (li, c) => !c || (c === 'Kinder' ? !!li.dataset.kids : li.dataset.cat === c);

  // Orts-Auswahl rechts neben den Filtern: ganze Region oder einzelner Ort
  let town = '';
  let sel = null;
  if (withTown) {
    const regions = new Map();
    items.forEach((li) => {
      const r = li.dataset.region || 'Fehmarn';
      const m = regions.get(r) || new Map();
      m.set(li.dataset.town, (m.get(li.dataset.town) || 0) + 1);
      regions.set(r, m);
    });
    const opt = (v, label, n) => `<option value="${v}">${label} (${n})</option>`;
    sel = document.createElement('select');
    sel.className = 'town-select';
    sel.id = `${prefix}-town`;
    sel.setAttribute('aria-label', 'Nach Ort filtern');
    sel.innerHTML = '<option value="">Alle Orte</option>' + ['Fehmarn', 'Ostholstein'].filter((r) => regions.has(r)).map((r) => {
      const m = regions.get(r);
      const total = [...m.values()].reduce((a, b) => a + b, 0);
      const towns = [...m].sort((a, b) => a[0].localeCompare(b[0], 'de'));
      return `<optgroup label="${r}">${opt(`r:${r}`, `Ganz ${r}`, total)}${towns.map(([t, n]) => opt(`t:${t}`, t, n)).join('')}</optgroup>`;
    }).join('');
    const row = document.createElement('div');
    row.className = 'akt-tools';
    bar.before(row);
    row.append(bar, sel);
    sel.addEventListener('change', () => { town = sel.value; shown = PAGE; render(); });
  }
  const inTown = (li) => !town || (town.startsWith('r:') ? (li.dataset.region || 'Fehmarn') === town.slice(2) : li.dataset.town === town.slice(2));

  // "Alle": bunt gemischt, reihum aus den Unterarten; nach Filter: sortiert
  const roundRobin = (lists) => { const q = lists.map((l) => [...l]); const out = []; while (q.some((x) => x.length)) q.forEach((x) => { if (x.length) out.push(x.shift()); }); return out; };
  const byKey = (arr, key) => [...arr.reduce((m, li) => m.set(li.dataset[key], [...(m.get(li.dataset[key]) || []), li]), new Map()).values()];
  // je Bereich reihum über die Unterarten, dann reihum über die Bereiche
  const mixed = roundRobin(byKey(items, 'cat').map((catItems) => roundRobin(byKey(catItems, 'sub'))));
  function render() {
    const order = cat ? items : mixed;
    order.forEach((li) => list.append(li));
    const match = order.filter((li) => inCat(li, cat) && inTown(li));
    list.dataset.empty = match.length ? '' : '1';
    items.forEach((li) => { li.hidden = true; });
    match.slice(0, shown).forEach((li) => { li.hidden = false; });
    more.hidden = match.length <= shown;
    bar.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.cat === cat)));
  }
  bar.addEventListener('click', (e) => {
    const b = e.target.closest('button'); if (!b) return;
    cat = b.dataset.cat; shown = PAGE; render();
  });
  more.addEventListener('click', () => { shown += PAGE; render(); });
  bar.hidden = false;
  render();
};
tileFilter('akt', true, true);
tileFilter('night', false, true);
tileFilter('well', false);
