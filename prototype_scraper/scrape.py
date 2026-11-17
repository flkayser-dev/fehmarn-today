"""
PROTOTYPE – Wegwerf-Code. Fehmarn Today Event-Scraper, 3 Quellen.

Frage: Lassen sich aus der reporter (Atom-Feed), fehmarn.de und Hochberg-Flohmarkt
zuverlässig strukturierte Events ziehen (Titel, Datum, Uhrzeit, Ort, Link)?

Starten:   python3 prototype_scraper/scrape.py
Ergebnis:  prototype_scraper/PROTOTYPE_events.json  +  PROTOTYPE_report.html
"""
import json, re, time, html, datetime as dt, pathlib, xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from bs4 import BeautifulSoup

UA = "FehmarnToday-Prototype/0.1 (Event-Recherche; respektiert robots.txt)"
HERE = pathlib.Path(__file__).parent
TODAY = dt.date.today()

MONTHS = {"jan": 1, "feb": 2, "mär": 3, "mrz": 3, "maer": 3, "apr": 4, "mai": 5, "jun": 6,
          "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dez": 12}

import ssl, certifi
SSL = ssl.create_default_context(cafile=certifi.where())

def get(url, data=None):
    body = urlencode(data).encode() if data else None
    req = Request(url, data=body, headers={"User-Agent": UA})
    with urlopen(req, timeout=25, context=SSL) as r:
        raw = r.read()
    time.sleep(1)  # höflich bleiben
    return raw.decode("utf-8", errors="replace")

def month_num(word):
    w = word.lower().strip(".")[:3].replace("ä", "ä")
    return MONTHS.get(w) or MONTHS.get(word.lower()[:4])

def infer_year(m, d):
    """Datum ohne Jahr: nächstes Vorkommen ab heute (max. ~2 Monate zurück erlaubt)."""
    y = TODAY.year
    try:
        cand = dt.date(y, m, d)
    except ValueError:
        return None
    if cand < TODAY - dt.timedelta(days=60):
        cand = dt.date(y + 1, m, d)
    return cand

# ---------------------------------------------------------------- der reporter
DATE_RE = re.compile(
    r"(?:(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonnabend|Sonntag),?\s*)?"
    r"(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)"
    r"(?:\s+(20\d\d))?")
DATE_NUM_RE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(20\d\d)?\b")
TIME_RE = re.compile(r"(?:ab|um|von)?\s*(\d{1,2})(?:[.:](\d{2}))?\s*(?:bis\s*(\d{1,2})(?:[.:](\d{2}))?\s*)?Uhr")
PLACE_RE = re.compile(r"(?:im|in der|in den|auf dem|auf der|am|beim|in)\s+([A-ZÄÖÜ][\w\-äöüß]+(?:[ \-][A-ZÄÖÜ][\w\-äöüß.]+){0,4})")

def reporter():
    xml = get("https://www.der-reporter.de/fileadmin/feeds/artikel.atom")
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml)
    out = []
    for e in root.findall("a:entry", ns):
        cats = [c.get("label") for c in e.findall("a:category", ns)]
        if "Veranstaltungen" not in cats:
            continue
        title = e.findtext("a:title", "", ns).strip()
        link = e.find("a:link", ns).get("href")
        text = BeautifulSoup(e.findtext("a:content", "", ns), "lxml").get_text(" ", strip=True)
        # Ortsmarke am Anfang: "Lensahn. Am Samstag ..."
        m_town = re.match(r"([A-ZÄÖÜ][\w\-äöüß/ ]{2,30})\.\s", text)
        town = m_town.group(1) if m_town else next((c for c in cats if c not in
                ("Veranstaltungen", "Allgemein", "Gesellschaft", "Kultur", "Sport", "Vereine", "Ratgeber", "Verbraucherinfos")), None)
        dates = []
        for d, mon, y in DATE_RE.findall(text):
            mn = ["januar","februar","märz","april","mai","juni","juli","august","september","oktober","november","dezember"].index(mon.lower()) + 1
            dd = dt.date(int(y), mn, int(d)) if y else infer_year(mn, int(d))
            if dd: dates.append(dd)
        for d, mo, y in DATE_NUM_RE.findall(text):
            try:
                dd = dt.date(int(y), int(mo), int(d)) if y else infer_year(int(mo), int(d))
                if dd: dates.append(dd)
            except ValueError:
                pass
        tm = TIME_RE.search(text)
        t = None
        if tm:
            t = f"{int(tm.group(1)):02d}:{tm.group(2) or '00'}"
            if tm.group(3): t += f"–{int(tm.group(3)):02d}:{tm.group(4) or '00'}"
        pm = PLACE_RE.search(text[m_town.end() if m_town else 0:])
        # erstes Datum mit Wochentag im Text = meist der Termin
        wm = re.search(r"(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonnabend|Sonntag),?\s*(?:de[nm]\s*)?(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)", text)
        if wm:
            mn = ["januar","februar","märz","april","mai","juni","juli","august","september","oktober","november","dezember"].index(wm.group(2).lower()) + 1
            first = infer_year(mn, int(wm.group(1)))
            if first: dates = [first] + [x for x in dates if x != first]
        pm_venue = None
        out.append(dict(source="der reporter", title=title, date=dates[0].isoformat() if dates else None,
                        dates_found=len(set(dates)), time=t, town=town,
                        venue=pm.group(1) if pm and not re.match(r"(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonnabend|Sonntag|Jahr|Rahmen)", pm.group(1)) else None, url=link, recurring=None,
                        description=text[:300], lnglat=None))
    return out

# ---------------------------------------------------------------- fehmarn.de
DE_SHORT = re.compile(r"(\d{1,2})\.\s*([A-Za-zäÄ]{3,4})\.?\s*(20\d\d)")

def fehmarn_de(max_pages=15):
    out, seen = [], set()
    for page in range(1, max_pages + 1):
        s = BeautifulSoup(get(f"https://www.fehmarn.de/veranstaltungen?page={page}&uid=1506"), "lxml")
        items = s.select("li.listItem[data-title]")
        new = [li for li in items if li.get("data-hash") not in seen]
        if not new:
            break
        for li in new:
            seen.add(li.get("data-hash"))
            def slot_text(label):
                for sl in li.select(".listItem__event .slot .text"):
                    hide = sl.select_one(".hide")
                    if hide and label in hide.get_text():
                        hide.extract(); return sl.get_text(" ", strip=True)
                return None
            loc = li.select_one(".listItem__location .text")
            if loc and loc.select_one(".hide"): loc.select_one(".hide").extract()
            date_s, time_s = slot_text("Datum"), slot_text("Uhrzeit")
            rec = next((sl.get_text(strip=True) for sl in li.select(".listItem__event .slot .text") if "Termin" in sl.get_text()), None)
            d = None
            if date_s and (m := DE_SHORT.search(date_s)):
                mn = month_num(m.group(2))
                if mn: d = dt.date(int(m.group(3)), mn, int(m.group(1))).isoformat()
            a = li.select_one(".listItem__button a")
            desc = li.select_one(".Item__description")
            out.append(dict(source="fehmarn.de", title=li["data-title"], date=d, dates_found=1 if d else 0,
                            time=(time_s or "").replace(" Uhr", "").replace(" - ", "–") or None,
                            town=loc.get_text(" ", strip=True) if loc else None, venue=None,
                            url=a["href"] if a else None, recurring=rec,
                            description=desc.get_text(" ", strip=True)[:300] if desc else "",
                            lnglat=li.get("data-lnglat")))
    return out

# ---------------------------------------------------------------- Hochberg Flohmarkt
OSTHOLSTEIN_NEAR = {"Eutin": "Ostholstein", "Lübeck": "Nachbar (HL)", "Reinfeld": "Nachbar (OD)"}

def hochberg(months_ahead=12):
    out, seen = [], set()
    for i in range(months_ahead):
        m = (TODAY.month - 1 + i) % 12 + 1
        y = TODAY.year + (TODAY.month - 1 + i) // 12
        s = BeautifulSoup(get("https://www.hochberg-flohmarkt.de/termine.php",
                              {"FrmJahr": y, "FrmMonat": m, "FrmOrt": "Alle"}), "lxml")
        for td in s.select("td[valign=top]"):
            head = td.find("div")
            dm = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", head.get_text() if head else "")
            if not dm:
                continue
            d = dt.date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1)))
            for a in td.select(".bg_termine a[href*=id_termin]"):
                parts = [p.strip() for p in a.get_text("\n").split("\n") if p.strip()]
                venue, town = (parts + [None, None])[:2]
                key = a["href"]
                if key in seen:
                    continue
                seen.add(key)
                out.append(dict(source="Hochberg Flohmarkt", title=f"Flohmarkt {venue} {town}",
                                date=d.isoformat(), dates_found=1, time=None, town=town, venue=venue,
                                url="https://www.hochberg-flohmarkt.de/" + a["href"], recurring=None,
                                description="", lnglat=None, region=OSTHOLSTEIN_NEAR.get(town, "außerhalb")))
    return out

# ---------------------------------------------------------------- Zusammenführen
def norm(t):
    return re.sub(r"[^a-z0-9äöüß]", "", (t or "").lower())

def main():
    results, errors = [], {}
    for name, fn in [("der reporter", reporter), ("fehmarn.de", fehmarn_de), ("Hochberg Flohmarkt", hochberg)]:
        t0 = time.time()
        try:
            ev = fn()
            print(f"{name:20s} {len(ev):4d} Events  ({time.time()-t0:.1f}s)")
            results += ev
        except Exception as ex:
            errors[name] = repr(ex)
            print(f"{name:20s} FEHLER {ex!r}")
    # Dubletten: gleicher normalisierter Titel + Datum
    uniq, dupes = {}, 0
    for e in results:
        k = (norm(e["title"]), e["date"])
        if k in uniq: dupes += 1
        else: uniq[k] = e
    # Mit dem letzten Lauf zusammenführen: bekannte Termine behalten ihr "first_seen",
    # neue bekommen das heutige Datum. Der reporter-Feed zeigt nur die letzten Artikel,
    # daher bleiben seine kommenden Termine erhalten; ebenso alles von Quellen mit Fehler.
    prev_file = HERE / "PROTOTYPE_events.json"
    prev = json.loads(prev_file.read_text())["events"] if prev_file.exists() else []
    seen_before = {(norm(e["title"]), e["date"]): e.get("first_seen") for e in prev}
    keep_src = {"der reporter"} | set(errors)
    for e in prev:
        k = (norm(e["title"]), e["date"])
        if e["source"] in keep_src and (e["date"] or "") >= TODAY.isoformat() and k not in uniq:
            uniq[k] = e
    new_n = 0
    for k, e in uniq.items():
        if seen_before.get(k): e["first_seen"] = seen_before[k]
        elif k in seen_before or not prev: e["first_seen"] = e.get("first_seen") or TODAY.isoformat()
        else: e["first_seen"] = TODAY.isoformat(); new_n += 1
    events = sorted(uniq.values(), key=lambda e: (e["date"] or "9999", e["source"]))
    stats = {}
    for src in {e["source"] for e in events}:
        ev = [e for e in events if e["source"] == src]
        n = len(ev)
        stats[src] = {"events": n, **{f: round(100 * sum(1 for e in ev if e.get(f)) / n) for f in ("date", "time", "town", "venue", "url")}}
    data = {"generated": dt.datetime.now().isoformat(timespec="seconds"), "dupes_removed": dupes,
            "errors": errors, "new": new_n, "stats": stats, "events": events}
    (HERE / "PROTOTYPE_events.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    (HERE / "PROTOTYPE_report.html").write_text(report(data))
    print("\nFelder gefüllt (%):")
    for s, v in stats.items():
        print(f"  {s:20s} " + "  ".join(f"{k}={v[k]}" for k in ("date", "time", "town", "venue", "url")))
    print(f"Dubletten entfernt: {dupes}")
    print(f"Neu seit dem letzten Lauf: {new_n}")
    with open(HERE / "laufprotokoll.csv", "a") as f:
        f.write(f"{data['generated']};{len(events)} Termine;{new_n} neu;Fehler: {', '.join(errors) or 'keine'}\n")
    if len(errors) == 3: raise SystemExit("Alle Quellen ohne Antwort")

def report(d):
    esc = lambda x: html.escape(str(x)) if x else '<span class="miss">–</span>'
    rows = "".join(
        f"<tr class='s{abs(hash(e['source']))%3}'><td>{esc(e['date'])}</td><td>{esc(e['time'])}</td>"
        f"<td><a href='{html.escape(e['url'] or '#')}'>{esc(e['title'])}</a>"
        f"{'<small> · ' + html.escape(e['recurring']) + '</small>' if e.get('recurring') else ''}</td>"
        f"<td>{esc(e['town'])}{'<small> · ' + html.escape(e['venue']) + '</small>' if e.get('venue') else ''}</td>"
        f"<td>{html.escape(e['source'])}{'<small> · ' + e['region'] + '</small>' if e.get('region') else ''}</td></tr>"
        for e in d["events"])
    st = "".join(f"<tr><th>{s}</th><td>{v['events']}</td>" + "".join(f"<td>{v[k]} %</td>" for k in ("date", "time", "town", "venue", "url")) + "</tr>"
                 for s, v in d["stats"].items())
    return f"""<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prototyp Event-Scraper</title>
<style>
body{{font:14px/1.45 ui-monospace,Menlo,monospace;margin:0 auto;max-width:1100px;padding:24px 16px;color:#1d2a30;background:#f6f3ec}}
h1{{font:600 22px Georgia,serif;margin:0 0 4px}} p{{margin:0 0 18px;color:#5b666b}}
table{{border-collapse:collapse;width:100%;margin-bottom:28px;background:#fff}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid #e4dfd3;vertical-align:top}}
th{{font-weight:600;background:#ece6d8}} small{{color:#7a8387}} a{{color:#0b5d75}}
.miss{{color:#c2410c;font-weight:700}} .warn{{background:#fff4e5;padding:8px 10px;border-left:3px solid #c2410c;margin-bottom:18px}}
.wrap{{overflow-x:auto}}
</style>
<h1>PROTOTYP · Fehmarn Today Event-Scraper</h1>
<p>Lauf: {d['generated']} · {len(d['events'])} Events · {d['dupes_removed']} Dubletten entfernt · Wegwerf-Code, nicht produktiv</p>
{''.join(f"<div class='warn'>Fehler bei {k}: {html.escape(v)}</div>" for k, v in d['errors'].items())}
<div class="wrap"><table><tr><th>Quelle</th><th>Events</th><th>Datum</th><th>Uhrzeit</th><th>Ort</th><th>Venue</th><th>Link</th></tr>{st}</table></div>
<div class="wrap"><table><tr><th>Datum</th><th>Zeit</th><th>Titel</th><th>Ort</th><th>Quelle</th></tr>{rows}</table></div>
</html>"""

if __name__ == "__main__":
    main()
