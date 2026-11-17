// PROTOTYP: "Jetzt geöffnet / geschlossen" aus Öffnungszeiten im OpenStreetMap-Format (gängige Teilmenge).
// Verstanden: Monate und Monatslisten (Apr-May,Sep-Oct), Tagesbereiche (Apr 15-Oct 15, Nov 03-Mar 26),
// Jahresbereiche (2026 Nov 01-2027 Mar 18), Ostern (easter -7 days-Oct 31), Wochentage, Zeiten (auch über
// Mitternacht, offenes Ende 18:00+, sunset), "off", closed/unknown mit Kommentar. Spätere Regeln überschreiben frühere.
(() => {
  const DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
  const DE_DAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const DE_MON = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
  // Sonnenuntergang auf Fehmarn, grob je Monat (Minuten), reicht für "geöffnet bis Sonnenuntergang"
  const SUNSET = [990, 1040, 1100, 1215, 1265, 1305, 1300, 1250, 1180, 1110, 990, 960];
  const wd = (d) => (d.getDay() + 6) % 7;
  const dayNum = (d) => Math.floor(new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime() / 864e5);

  function easter(y) { // Gauß/Meeus
    const a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4, f = Math.floor((b + 8) / 25);
    const g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30, i = Math.floor(c / 4), k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451);
    const month = Math.floor((h + l - 7 * m + 114) / 31) - 1, day = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(y, month, day);
  }
  // Punkt im Jahr: liefert (Jahr) -> Datum
  function point(s) {
    let m = s.match(/^easter(?:\s*([+-]\d+) days?)?$/);
    if (m) return (y) => { const e = easter(y); e.setDate(e.getDate() + Number(m[1] || 0)); return e; };
    m = s.match(/^(\w{3}) (\d{1,2})$/);
    if (m && MON.includes(m[1])) return (y) => new Date(y, MON.indexOf(m[1]), Number(m[2]));
    return null;
  }
  function parseSelector(sel) {
    const parts = sel.split(',').map((p) => p.trim());
    const tests = parts.map((p) => {
      let m = p.match(/^(\d{4}) (\w{3}) (\d{1,2})-(?:(\d{4}) )?(\w{3}) (\d{1,2})$/);
      if (m) {
        const a = dayNum(new Date(+m[1], MON.indexOf(m[2]), +m[3])); const b = dayNum(new Date(+(m[4] || m[1]), MON.indexOf(m[5]), +m[6]));
        return (d) => dayNum(d) >= a && dayNum(d) <= b;
      }
      m = p.match(/^(easter(?:\s*[+-]\d+ days?)?|\w{3} \d{1,2})-(easter(?:\s*[+-]\d+ days?)?|\w{3} \d{1,2})$/);
      if (m && point(m[1]) && point(m[2])) {
        const A = point(m[1]), B = point(m[2]);
        return (d) => {
          const y = d.getFullYear(), n = dayNum(d);
          const a = dayNum(A(y)), b = dayNum(B(y));
          return a <= b ? n >= a && n <= b : n >= a || n <= b; // über den Jahreswechsel
        };
      }
      m = p.match(/^(\w{3})-(\w{3})$/);
      if (m && MON.includes(m[1]) && MON.includes(m[2])) {
        const a = MON.indexOf(m[1]), b = MON.indexOf(m[2]);
        return (d) => (a <= b ? d.getMonth() >= a && d.getMonth() <= b : d.getMonth() >= a || d.getMonth() <= b);
      }
      if (MON.includes(p)) return (d) => d.getMonth() === MON.indexOf(p);
      return null;
    });
    return tests.every(Boolean) ? (d) => tests.some((t) => t(d)) : null;
  }
  function parseDays(s) {
    const set = new Set();
    for (const part of s.split(',')) {
      const [a, b] = part.split('-').map((x) => DAYS.indexOf(x.trim()));
      if (a < 0 || b === -1) return null;
      if (b === undefined) { set.add(a); continue; }
      for (let i = a; ; i = (i + 1) % 7) { set.add(i); if (i === b) break; }
    }
    return set;
  }
  const tmin = (s) => (s === 'sunset' ? 'sunset' : ((m) => (m ? Number(m[1]) * 60 + Number(m[2]) : NaN))(s.match(/^(\d{1,2}):(\d{2})$/)));
  function parseTimes(s) {
    const out = [];
    for (const r of s.split(',')) {
      let m = r.trim().match(/^(\d{1,2}:\d{2})\+$/);
      if (m) { out.push({ a: tmin(m[1]), b: 1440, openEnd: true }); continue; }
      m = r.trim().match(/^(\d{1,2}:\d{2})-(\d{1,2}:\d{2}|sunset)\+?$/);
      if (!m || Number.isNaN(tmin(m[1])) || Number.isNaN(tmin(m[2]))) return null;
      out.push({ a: tmin(m[1]), b: tmin(m[2]) });
    }
    return out;
  }
  const SEL = new RegExp(`^((?:(?:\\d{4} )?(?:${MON.join('|')}) \\d{1,2}|easter(?:\\s*[+-]\\d+ days?)?|(?:${MON.join('|')}))(?:-(?:(?:\\d{4} )?(?:${MON.join('|')}) \\d{1,2}|easter(?:\\s*[+-]\\d+ days?)?|(?:${MON.join('|')})))?(?:\\s*,\\s*(?:(?:${MON.join('|')}) \\d{1,2}|(?:${MON.join('|')}))(?:-(?:(?:${MON.join('|')}) \\d{1,2}|(?:${MON.join('|')})))?)*)\\s*:?\\s*(.*)$`);

  function parse(oh) {
    const rules = [];
    let note = '';
    let unknownRules = 0;
    for (let raw of oh.split(';')) {
      raw = raw.trim(); if (!raw || /^(PH|SH)\b/.test(raw) || /\b(PH|SH)\b/.test(raw.split(' ')[0])) continue;
      const c = raw.match(/"([^"]*)"/); if (c) note = c[1];
      raw = raw.replace(/"[^"]*"/g, '').trim();
      let date = () => true;
      const s = raw.match(SEL);
      if (s && parseSelector(s[1])) { date = parseSelector(s[1]); raw = s[2].trim(); }
      let days = new Set([0, 1, 2, 3, 4, 5, 6]);
      raw = raw.replace(/,(PH|SH)\b/g, '');
      const dm = raw.match(/^((?:Mo|Tu|We|Th|Fr|Sa|Su)(?:[-,](?:Mo|Tu|We|Th|Fr|Sa|Su))*)\s*(.*)$/);
      if (dm) { days = parseDays(dm[1]); raw = dm[2].trim(); if (!days) continue; }
      else if (/^(?:\d{4} )?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}\+?/.test(raw) || /^(?:Dec|Jan) \d{1,2}(?:[,-]|$)/.test(raw)) continue; // einzelne Sondertage überspringen
      const tail = raw.match(/\s*(off|closed|unknown)$/);
      if (/^(off|closed)$/.test(raw)) { rules.push({ date, days, times: [], off: true, note }); continue; }
      if (raw === 'unknown') return { unknown: true, note };
      if (tail && tail[1] === 'unknown') return { unknown: true, note };
      const times = raw === '24/7' ? [{ a: 0, b: 1440 }] : parseTimes(raw);
      if (!times || !times.length) { unknownRules += 1; continue; } // einzelne unbekannte Regel überspringen
      rules.push({ date, days, times, off: false, note });
    }
    return rules.length && unknownRules <= 1 ? { rules } : null;
  }
  const resolve = (iv, d) => ({ ...iv, b: iv.b === 'sunset' ? SUNSET[d.getMonth()] : iv.b });
  function dayIntervals(rules, d) {
    let res = null;
    for (const r of rules) if (r.date(d) && r.days.has(wd(d))) res = r.off ? [] : r.times.map((iv) => resolve(iv, d));
    return res || [];
  }
  function openAt(rules, t) { // liefert das Intervall, falls geöffnet
    const d = new Date(t.getFullYear(), t.getMonth(), t.getDate());
    const min = t.getHours() * 60 + t.getMinutes();
    const today = dayIntervals(rules, d).find(({ a, b }) => (b > a ? min >= a && min < b : min >= a));
    if (today) return today;
    const y = new Date(d); y.setDate(y.getDate() - 1); // über Mitternacht vom Vortag
    return dayIntervals(rules, y).find(({ a, b }) => b <= a && min < b) || null;
  }
  function nextChange(rules, now, open) {
    const t = new Date(now); t.setSeconds(0, 0); t.setMinutes(Math.ceil(t.getMinutes() / 15) * 15);
    for (let i = 0; i < 400 * 96; i++) {
      if (!!openAt(rules, t) !== open) return t;
      t.setMinutes(t.getMinutes() + 15);
    }
    return null;
  }
  const hm = (t) => (t.getHours() === 0 && t.getMinutes() === 0 ? 'Mitternacht' : `${t.getHours()}${t.getMinutes() ? ':' + String(t.getMinutes()).padStart(2, '0') : ''} Uhr`);
  function when(t, now) {
    const days = dayNum(t) - dayNum(now);
    if (days === 0) return `heute ${hm(t)}`;
    if (days === 1) return `morgen ${hm(t)}`;
    if (days < 7) return `${DE_DAYS[wd(t)]} ${hm(t)}`;
    return `am ${t.getDate()}. ${DE_MON[t.getMonth()]}`;
  }

  const now = new Date();
  document.querySelectorAll('[data-oh]').forEach((el) => {
    const p = parse(el.dataset.oh);
    if (!p || p.unknown) return;
    const iv = openAt(p.rules, now);
    const open = !!iv;
    const next = nextChange(p.rules, now, open);
    el.classList.add(open ? 'is-open' : 'is-closed');
    if (open) el.textContent = iv.openEnd ? 'Jetzt geöffnet' : `Jetzt geöffnet${next ? `, bis ${hm(next)}` : ''}`;
    else el.textContent = next ? `Jetzt geschlossen, öffnet ${when(next, now)}` : 'Derzeit geschlossen';
    el.hidden = false;
  });
})();
