// PROTOTYP: Aktivitäten filtern (Wasser, Natur & Ausflüge, Sport & Freizeit) und nachladen
const tileFilter = (prefix, withKids) => {
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

  // "Alle": bunt gemischt, reihum aus den Unterarten; nach Filter: sortiert
  const roundRobin = (lists) => { const q = lists.map((l) => [...l]); const out = []; while (q.some((x) => x.length)) q.forEach((x) => { if (x.length) out.push(x.shift()); }); return out; };
  const byKey = (arr, key) => [...arr.reduce((m, li) => m.set(li.dataset[key], [...(m.get(li.dataset[key]) || []), li]), new Map()).values()];
  // je Bereich reihum über die Unterarten, dann reihum über die Bereiche
  const mixed = roundRobin(byKey(items, 'cat').map((catItems) => roundRobin(byKey(catItems, 'sub'))));
  function render() {
    const order = cat ? items : mixed;
    order.forEach((li) => list.append(li));
    const match = order.filter((li) => inCat(li, cat));
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
tileFilter('akt', true);
tileFilter('night', false);
tileFilter('well', false);
