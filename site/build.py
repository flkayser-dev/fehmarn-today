"""
PROTOTYP: baut site/index.html aus prototype_scraper/PROTOTYPE_events.json und data/events-2027.json.
Starten:  python3 site/build.py   (vorher: python3 prototype_scraper/scrape.py)
"""
import json, re, html, pathlib, datetime as dt
from collections import Counter

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
DATA = json.loads((ROOT / "prototype_scraper" / "PROTOTYPE_events.json").read_text())
YEAR_FILE = ROOT / "data" / "events-2027.json"
from zoneinfo import ZoneInfo
TODAY = dt.datetime.now(ZoneInfo("Europe/Berlin")).date()

WD = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MO = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

CATS = [
    ("Märkte", r"markt|flohmarkt|basar|bazar|trödel"),
    ("Kinder & Familie", r"kinder|familie|bücherzwerge|basteln|bastel|laterne|märchen|eltern"),
    ("Musik & Bühne", r"konzert|party|\bdj\b|disco|musik|jazz|\bchor|\bband\b|theater|comedy|lesung|\bkino|\bfilm|\bshow\b|kabarett|orgel"),
    ("Draußen & Führungen", r"führung|\btour\b|wanderung|radtour|natur|vogel|\bwatt|strand|deich|infocenter|kite|surf|segel"),
    ("Kurse & Workshops", r"workshop|kurs|yoga|malen|meditation|keramik|töpfer|schmuck|perlen|leinw|stricken|nähen"),
]
FEHMARN = {"Fehmarn", "Burg", "Burgtiefe", "Burgstaaken", "Lemkenhafen", "Petersdorf", "Landkirchen", "Orth", "Puttgarden",
           "Avendorf", "Gammendorf", "Bannesdorf", "Gold", "Wulfen", "Westermarkelsdorf", "Katharinenhof", "Meeschendorf",
           "Strukkamp", "Klausdorf", "Sulsdorf", "Dänschendorf", "Vadersdorf", "Albertsdorf", "Presen", "Staberdorf", "Todendorf",
           "Neue Tiefe", "Fehmarnsund", "Gahlendorf", "Lemkendorf", "Bisdorf", "Mummendorf", "Niendorf", "Altenteil"}
FREE_RX = r"eintritt (ist )?(frei|kostenfrei|kostenlos)|freier eintritt|kostenlos|kostenfrei|ohne eintritt"

def cat(e):
    for t in (e["title"].lower(), (e.get("description") or "")[:300].lower()):
        for name, rx in CATS:
            if re.search(rx, t):
                return name
    return "Sonstiges"

def town(e):
    t = (e.get("town") or "").replace("Fehmarn OT ", "")
    if re.match(r"^(Am|Im|In|Der|Die|Das)\b", t):
        t = ""
    t = re.sub(r"\s*in Holstein", "", t).replace("Burg auf Fehmarn", "Burg")
    if e["source"] == "fehmarn.de" and t == "":
        t = "Fehmarn"
    return t.strip() or "Ostholstein"

def title(s):
    s = re.sub(r'"([^"]+)"', "„\\1“", s.strip())
    return re.sub(r"\s+[–-]\s+", ": ", s, count=1).replace("–", "-")

events = []
for e in DATA["events"]:
    if not e["date"]:
        continue
    d = dt.date.fromisoformat(e["date"])
    if d < TODAY or d > TODAY + dt.timedelta(days=75):
        continue
    if e["source"] == "Hochberg Flohmarkt" and e.get("region") == "außerhalb":
        continue
    t = town(e)
    events.append({
        "date": e["date"], "time": (e.get("time") or "").replace("–", " bis ").strip() or None,
        "title": title(e["title"]), "town": t, "venue": None,  # Prototyp: Regex-Venue zu unzuverlässig, später KI-Extraktion
        "fehmarn": e["source"] == "fehmarn.de" or t in FEHMARN,
        "free": bool(re.search(FREE_RX, (e.get("description") or "").lower())),
        "url": e["url"], "source": e["source"], "cat": cat(e), "recurring": e.get("recurring"),
    })
events.sort(key=lambda e: (e["date"], e["time"] or "00"))

esc = html.escape
iso = lambda d: d.isoformat()
tomorrow = TODAY + dt.timedelta(days=1)
sat = TODAY + dt.timedelta(days=(5 - TODAY.weekday()) % 7 or 7)
sun = sat + dt.timedelta(days=1)
n_on = lambda a, b: sum(1 for e in events if iso(a) <= e["date"] <= iso(b))

def fmt_day(d):
    return f"{WD[d.weekday()]}, {d.day}. {MO[d.month-1]}"

# --- Fotos: jede Kachel bekommt ein echtes Foto (Motiv passend zum Termin, sonst ein Foto vom Ort)
CC = {"BY-SA 3.0 de": "https://creativecommons.org/licenses/by-sa/3.0/de/", "BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/", "BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
      "BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/", "BY 2.0": "https://creativecommons.org/licenses/by/2.0/",
      "BY-SA 2.0 de": "https://creativecommons.org/licenses/by-sa/2.0/de/", "CC0": "https://creativecommons.org/publicdomain/zero/1.0/"}
PH = {  # Datei: (Alt-Text, Fotograf, Lizenz)
    "strand-bruecke": ("Strand am Fehmarnsund", "Dguendel", "BY 4.0"),
    "kites-sund": ("Kiter im Fehmarnsund", "Superbass", "BY-SA 4.0"),
    "burgtiefe-luft": ("Burgtiefe von oben, Südstrand und Yachthafen", "Fabian Horst", "BY-SA 4.0"),
    "moewe-strandkorb": ("Möwe auf einem Strandkorb", "Superbass", "BY-SA 4.0"),
    "fluegge-behrens": ("Leuchtturm Flügge", "Torsten Behrens", "BY 2.0"),
    "orth-superbass": ("Hafen Orth", "Superbass", "BY-SA 4.0"),
    "muehle-ellgaard": ("Mühle Jachen Flünk in Lemkenhafen", "Holger Ellgaard", "BY-SA 3.0"),
    "nikolai-kirchhof": ("Kirche St. Nikolai in Burg", "Dguendel", "BY 4.0"),
    "weihnachtsmarkt": ("Weihnachtsmarkt, Symbolfoto aus Lübeck", "Robert Barten", "gemeinfrei"),
    "flohmarkt": ("Flohmarkt, Symbolfoto aus Lübeck", "Dietmar Rabich", "BY-SA 4.0"),
    "orgel-nikolai": ("Orgel in St. Nikolai, Burg", "Hans-Jörg Gemeinholzer", "BY-SA 4.0"),
}
for k, v in json.loads((HERE / "img" / "orte" / "credits.json").read_text()).items():
    PH["ort-" + k] = (v["title"][5:].rsplit(".", 1)[0].replace(" - panoramio", ""), v["artist"], v["license"].replace("CC ", ""))
TOWN_PH = {"Neustadt": "ort-neustadt", "Neustadt-Pelzerhaken": "ort-neustadt", "Grömitz": "ort-groemitz", "Eutin": "ort-eutin",
           "Ratekau": "ort-ratekau", "Kellenhusen": "ort-kellenhusen", "Scharbeutz": "ort-scharbeutz", "Sierksdorf": "ort-sierksdorf",
           "Grube": "ort-grube", "Heiligenhafen": "ort-heiligenhafen", "Burgtiefe": "burgtiefe-luft", "Lemkenhafen": "muehle-ellgaard",
           "Burg": "nikolai-kirchhof", "Orth": "orth-superbass"}
POOL_F = ["strand-bruecke", "moewe-strandkorb", "fluegge-behrens", "orth-superbass", "burgtiefe-luft", "kites-sund"]
POOL_O = ["ort-kellenhusen", "ort-sierksdorf", "ort-scharbeutz", "ort-groemitz"]
THEMEN_ALT = {"basar": "Weihnachtsbuden mit Lichtern", "trecker": "Geschmückter Traktor bei einem Lichterumzug", "tannenbaum": "Christbaumschmuck",
    "anbaden": "Menschen am Strand beim Neujahrsbaden", "yoga": "Yogakurs in einem Saal", "meditation": "Klangschale", "toepfern": "Töpfer an der Drehscheibe",
    "malen": "Kind malt mit Wasserfarben", "stricken": "Hände beim Stricken", "naehen": "Alte Nähmaschine", "perlen": "Glasperlen", "basteln": "Gefaltete Papierkraniche",
    "theater": "Puppenbühne", "klassik": "Geigerin bei einem Konzert", "chor": "Chor beim Singen", "jazz": "Jazzband auf der Bühne", "party": "Discokugel",
    "band": "Rockband auf der Bühne", "tanz": "Tanzpaar", "vortrag": "Zuhörer bei einem Vortrag", "sitzung": "Sitzung an einem großen Tisch",
    "ausstellung": "Besucher in einer Fotoausstellung", "buecherei": "Kinderbücher im Regal", "spiele": "Menschen beim Brettspiel", "blutspende": "Blutspende",
    "hund": "Hund beim Training", "fuehrung": "Gruppe bei einer Führung", "sanddorn": "Sanddorn mit Beeren", "selbstverteidigung": "Selbstverteidigungskurs",
    "wein": "Weingläser bei einer Weinprobe", "bier": "Bier im Glas", "gedenken": "Kranzniederlegung an einem Denkmal"}
for k, v in json.loads((HERE / "img" / "k" / "themen-credits.json").read_text()).items():
    lic = v["license"].replace("CC ", "").replace("Public domain", "gemeinfrei")
    who = re.sub(r"\s+", " ", v["artist"].replace("Unknown authorUnknown author", "unbekannt")).strip()[:60]
    PH["t-" + k] = (THEMEN_ALT[k], who, lic)
THEMEN = [  # Reihenfolge zählt: das Spezifische zuerst
    (r"weihnachtsmarkt|christkindl|wintermarkt", "weihnachtsmarkt"), (r"floh|trödel", "flohmarkt"),
    (r"basar|adventsmarkt|martinsmarkt", "t-basar"), (r"lichterzauber|trecker|traktor", "t-trecker"),
    (r"tannenbaum|weihnachtsschmuck|schmücken", "t-tannenbaum"), (r"anbaden|neujahrsbaden", "t-anbaden"),
    (r"kite|surf", "kites-sund"), (r"yoga|qigong", "t-yoga"), (r"meditation|achtsam|soundbath|gong|klang", "t-meditation"),
    (r"keramik|töpfer", "t-toepfern"), (r"malen|leinw", "t-malen"), (r"strick|häkel", "t-stricken"), (r"nähen|musselin", "t-naehen"),
    (r"perlen|schmuck", "t-perlen"), (r"bastel|kreativ|windspiel|plotter|fensterbild|schneeflocke|schneekugel", "t-basteln"),
    (r"weintasting|weinprobe|\bwein", "t-wein"), (r"frühschoppen|\bbier", "t-bier"),
    (r"jazz|washboard|blues|trio\b|duo\b|jubiläumskonzert", "t-jazz"),
    (r"violine|klassik|salon|herrenhaus|blasorchester|orchester", "t-klassik"), (r"theater|puppen", "t-theater"),
    (r"gospel|\bchor|singen|weihnachtslieder|adventskonzert|kirchenkonzert", "t-chor"),
    (r"party|disco|\bdj\b|silvester", "t-party"),
    (r"konzert|\bband\b|rock|livemusik|irish", "t-band"), (r"tanz", "t-tanz"),
    (r"vortrag|lounge|forum|tourismusabend|vorr?ausschau|netzwerk", "t-vortrag"),
    (r"sitzung|versammlung|gemeindevertretung|bürgerrat|sprechstunde|ausschuss|stadtverordnet", "t-sitzung"),
    (r"ausstellung|dokumentation|museum", "t-ausstellung"), (r"bücherei|vorlese|lesung", "t-buecherei"),
    (r"bingo|spielenachmittag|tischfußball|seniorennachmittag", "t-spiele"), (r"blutspende", "t-blutspende"),
    (r"\bhund", "t-hund"), (r"führung|tour\b|infocenter", "t-fuehrung"), (r"sanddorn", "t-sanddorn"),
    (r"selbstverteidigung", "t-selbstverteidigung"), (r"volkstrauertag|gedenk", "t-gedenken"),
    (r"strandkorb|strand", "moewe-strandkorb"), (r"mühle", "muehle-ellgaard"),
]
# Weitere Fotos je Thema (geprüft, aus img/k/bibliothek.json): ein Titel bekommt ein eigenes Foto
LIB_FILE = HERE / "img" / "k" / "bibliothek.json"
LIB = json.loads(LIB_FILE.read_text()) if LIB_FILE.exists() else {}
for topic, items in LIB.items():
    for it in items:
        PH[it["key"]] = (it["alt"], it["artist"], it["license"])
def topic_of(e):
    t = e["title"].lower()
    for rx, p in THEMEN:
        if re.search(rx, t):
            return p
    if re.search(r"kirche|orgel|gottesdienst", t) and e["town"] in ("Burg", "Fehmarn"):
        return "orgel-nikolai"
    if e["town"] in TOWN_PH:
        return TOWN_PH[e["town"]]
    return "pool-f" if e["fehmarn"] else "pool-o"
def candidates(topic):
    base = {"pool-f": POOL_F, "pool-o": POOL_O}.get(topic, [topic])
    extra = [it["key"] for it in LIB.get(topic.replace("t-", "").replace("ort-", ""), [])]
    return base + extra
RELATED = {"band": ["jazz", "party"], "jazz": ["band"], "party": ["band"], "sitzung": ["vortrag"], "vortrag": ["sitzung"],
           "basteln": ["malen", "perlen"], "meditation": ["yoga"], "yoga": ["meditation"], "ausstellung": ["fuehrung"], "klassik": ["chor"], "chor": ["klassik"]}
owner, by_title = {}, {}
for e in sorted(events, key=lambda e: (e["date"], e["title"])):
    key = re.sub(r"\W+", " ", e["title"].lower()).strip()[:40]
    if key not in by_title:
        topic = topic_of(e)
        cands = candidates(topic)
        free = [c for c in cands if c not in owner]
        if not free:  # verwandtes Thema, solange dort noch ein Foto frei ist (z. B. Konzert und Jazz)
            for rel in RELATED.get(topic.replace("t-", ""), []):
                free = [c for c in candidates("t-" + rel) if c not in owner]
                if free: break
        pick = free[0] if free else cands[sum(map(ord, key)) % len(cands)]
        owner.setdefault(pick, key)
        by_title[key] = pick
    e["img"] = by_title[key]; e["alt"] = PH[e["img"]][0]

ICON_PIN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>'
ICON_CAL = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>'
ICON_EURO = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10h12M4 14h9M19 6a7.7 7.7 0 0 0-5.2-2A7.9 7.9 0 0 0 6 12c0 4.4 3.5 8 7.8 8 2 0 3.8-.8 5.2-2"/></svg>'
ICON_CLOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>'
def card(e):
    free = '<span class="card-free">Eintritt frei</span>' if e["free"] else ""
    return (f'<li class="card"><a class="card-link" href="{esc(e["url"])}"><span class="card-photo">'
            f'<img src="img/k/{e["img"]}.jpg" alt="{esc(e["alt"])}" loading="lazy" width="900" height="600"><span class="card-cat">{esc(e["cat"])}</span></span>'
            f'<span class="card-body"><span class="card-title">{esc(e["title"])}</span><span class="card-meta">'
            f'<span>{ICON_PIN}{esc(e["town"])}</span><span>{ICON_CAL}{WD[dt.date.fromisoformat(e["date"]).weekday()]}, {dt.date.fromisoformat(e["date"]).day}. {MO[dt.date.fromisoformat(e["date"]).month-1]}</span>'
            f'<span>{ICON_CLOCK}{esc(e["time"] + " Uhr" if e["time"] else "ganztags")}</span>{free}</span></span></a></li>')

def day_block(dstr, evs):
    d = dt.date.fromisoformat(dstr)
    return (f'<section class="day" aria-labelledby="d{dstr}"><h3 class="day-head" id="d{dstr}">{WD[d.weekday()]}, {d.day}. {MO[d.month-1]}'
            f'<span class="day-n">{len(evs)} {"Termin" if len(evs) == 1 else "Termine"}</span></h3><ul class="cards">{"".join(card(e) for e in evs)}</ul></section>')
static_html = day_block(iso(TODAY), [e for e in events if e["date"] == iso(TODAY)])

# --- Tagesleiste: heute, morgen, übermorgen, dann Wochentage, dazu Wochenende und Alle
def daybar():
    out = []
    for i in range(8):
        d = TODAY + dt.timedelta(days=i)
        name = ["Heute", "Morgen", "Übermorgen"][i] if i < 3 else WD[d.weekday()][:2] + "."
        n = n_on(d, d)
        out.append(f'<button type="button" data-day="{iso(d)}" aria-pressed="{str(i == 0).lower()}"{" disabled" if not n else ""}>'
                   f'<span class="db-name">{name}</span><span class="db-date num">{d.day}.{d.month}.</span><span class="db-n">{n} Termine</span></button>')
    out.append(f'<button type="button" data-range="weekend" aria-pressed="false"><span class="db-name">Wochenende</span><span class="db-date num">{sat.day}. bis {sun.day}.</span><span class="db-n">{n_on(sat, sun)} Termine</span></button>')
    out.append(f'<button type="button" data-range="all" aria-pressed="false"><span class="db-name">Alle</span><span class="db-date">nächste Wochen</span><span class="db-n">{len(events)} Termine</span></button>')
    return "".join(out)

def credits_html():
    used = sorted({e["img"] for e in events} | {"bruecke-korn", "kites-sund", "strand-bruecke"})
    PH.setdefault("bruecke-korn", ("Fehmarnsundbrücke im Kornfeld", "Superbass", "BY-SA 4.0"))
    parts = []
    for k in used:
        alt, who, lic = PH[k]
        l = f'<a href="{CC[lic]}">CC {lic}</a>' if lic in CC else lic
        parts.append(f"{esc(alt)}: {esc(who)} ({l})")
    rc = rain_credits()
    op = open_credits()
    return (("Fotos aus der Touristischen Landesdatenbank Schleswig-Holstein (TA.SH, Open Data), verkleinert: " + op + ". ") if op else "") + "Fotos über Wikimedia Commons. " + "; ".join(parts) + (". Regen-Ziele: " + rc if rc else "") + ((". Aktivitäten: " + akt_credits()) if akt_credits() else "") + ((". Strände: " + beach_credits()) if beach_credits() else "") + ((". Nightlife: " + night_credits()) if night_credits() else "") + ((". Wellness: " + well_credits()) if well_credits() else "") + "."

# --- Orte: Fehmarn und Umgebung getrennt
def towns_html(fehmarn):
    c = Counter(e["town"] for e in events if e["fehmarn"] == fehmarn and e["town"] != "Ostholstein")
    return "".join(f'<li><a class="town" href="#kalender" data-town="{esc(t)}"><span class="town-name">{esc(t)}</span>'
                   f'<span class="town-n num">{n} Termine</span></a></li>' for t, n in c.most_common(6))

# --- Jahresplaner 2027
def short(d):
    return f"{d.day}.{d.month}."
def year_html():
    if not YEAR_FILE.exists():
        return '<li class="year-empty">Die Termine für 2027 werden gerade zusammengestellt.</li>'
    y = json.loads(YEAR_FILE.read_text())
    out = []
    for m in range(1, 13):
        evs = sorted([e for e in y["events"] if dt.date.fromisoformat(e["date_start"]).month == m and e["date_start"].startswith("2027")],
                     key=lambda e: e["date_start"])
        hol = [h for h in y.get("holidays", []) if h.get("kind", "").startswith(("Schulferien SH", "Skoleferie"))
               and dt.date.fromisoformat(h["date_start"]).month == m and h["date_start"].startswith("2027")]
        items = []
        for e in evs:
            a = dt.date.fromisoformat(e["date_start"]); b = dt.date.fromisoformat(e.get("date_end") or e["date_start"])
            when = short(a) if a == b else f"{short(a)} bis {short(b)}"
            vor = '<span class="y-est">voraussichtlich</span>' if e.get("status") != "bestätigt" else ""
            link = f'<a href="{esc(e["source_url"])}">{esc(title(e["title"]))}</a>' if e.get("source_url") else esc(title(e["title"]))
            items.append(f'<li><span class="y-when num">{when}</span><span class="y-what">{link}<span class="y-where">{esc(e.get("town") or "")}</span>{vor}</span></li>')
        more = ""
        ferien = ""
        if hol:
            lab = {"Schulferien SH": "Ferien Schleswig-Holstein", "Skoleferie DK": "Ferien Dänemark"}
            ferien = '<p class="y-hol">' + ", ".join(f'{lab.get(h["kind"], h["kind"])} ab {short(dt.date.fromisoformat(h["date_start"]))}' for h in hol) + "</p>"
        body = "".join(items) or '<li class="y-none">Noch keine großen Termine bekannt</li>'
        out.append(f'<li class="y-month" data-m="{m}" data-n="{len(evs)}"><h3>{MO[m-1]}</h3><ul>{body}</ul>{more}{ferien}</li>')
    return "".join(out)


# --- Wenn es regnet: Kacheln mit Foto, Ort, Preis, Link zur Website
REGEN_FILE = ROOT / "data" / "regen.json"
REGEN_CREDITS = json.loads((HERE / "img" / "regen" / "credits.json").read_text()) if (HERE / "img" / "regen" / "credits.json").exists() else {}
def short_town(t):
    return t.replace(" auf Fehmarn", "")
FEHMARN_X = FEHMARN | {"Wallnau", "Flügge", "Marienleuchte", "Blieschendorf", "Gollendorf", "Johannisberg", "Sahrensdorf", "Staberhuk", "Grüner Brink"}
def town_attrs(a):
    """Ort für den Orts-Filter: Klammerzusätze und 'in Holstein' weg, Region dazu."""
    t = re.sub(r"\s*\(.*\)", "", a.get("town") or "Fehmarn").replace(" in Holstein", "").replace(" auf Fehmarn", "").strip()
    reg = "Fehmarn" if t in FEHMARN_X else "Ostholstein"
    return f' data-town="{esc(t)}" data-region="{reg}"'
def nodash(s):
    return re.sub(r"\s*–\s*", " bis ", re.sub(r"\s+–\s+", ": ", s or ""))
def rain_html():
    if not REGEN_FILE.exists():
        return ""
    out = []
    for it in json.loads(REGEN_FILE.read_text())["items"]:
        slug = it.get("slug", "")
        opening = re.sub(r"\s*\([^)]*\)", "", re.split(r";|\.\s+[A-ZÄÖÜ0-9]", it.get("opening") or "")[0]).strip().rstrip(".")
        if len(opening) > 70:
            opening = opening[:70].rsplit(" ", 1)[0] + " …"
        sym = " (Symbolfoto)" if REGEN_CREDITS.get(slug, {}).get("symbol") else ""
        kids = it.get("price_child") or ""
        it = {k: (nodash(v) if isinstance(v, str) and k not in ("url", "source_url", "slug") else v) for k, v in it.items()}
        opening = nodash(opening); kids = nodash(kids)
        out.append(
            f'<li class="rcard"><a class="rcard-link" href="{esc(it["url"])}" rel="noopener" target="_blank">'
            + ((lambda wp: f'<span class="rcard-photo card-photo"><img src="{esc(wp[0])}" alt="{esc(it["name"])}" loading="lazy" width="900" height="600" referrerpolicy="no-referrer"><span class="map-credit">Foto: {esc(wp[1])}</span></span>')(_wp) if (_wp := web_pic(it)) is not None else
               f'<span class="rcard-photo"><img src="img/regen/{slug}.jpg" alt="{esc(it["name"])}{sym}" loading="lazy" width="900" height="600"></span>')
            + f'<span class="rcard-body"><span class="rcard-title">{esc(it["name"])}</span>'
            f'<span class="card-meta"><span>{ICON_PIN}{esc(short_town(it["town"]))}</span>'
            f'<span>{ICON_EURO}Erwachsene {esc(it.get("price_adult") or "siehe Website")}</span>'
            + (f'<span>{ICON_EURO}Kinder {esc(kids)}</span>' if kids else "")
            + (f'<span>{ICON_CLOCK}{esc(opening)}</span>' if opening else "")
            + f'</span><span class="rcard-go">Zur Website</span></span></a></li>')
    regen_names = {norm_name(x["name"]) for x in json.loads(REGEN_FILE.read_text())["items"]} if REGEN_FILE.exists() else set()
    for a in AKT:  # Ziele für Regentage aus ganz Ostholstein
        if a.get("category") == "Bei Regen" and norm_name(a["name"]) not in regen_names:
            out.append(venue_card(a, "akt", "Bei Regen", a.get("subcategory") or "Bei Regen"))
    return "".join(out)
def rain_credits():
    return "; ".join(f'{esc(v["title"][5:].rsplit(".", 1)[0])}: {esc(re.sub(r"\s+", " ", v["artist"])[:50])} ({esc(v["license"])})' for v in REGEN_CREDITS.values())


# --- Aktivitäten, die immer gehen (data/aktiv-*.json)
AKT = []
for f in sorted((ROOT / "data").glob("aktiv-*.json")):
    AKT += json.loads(f.read_text()).get("items", [])
AKT_ORDER = ["Wasser", "Natur & Ausflüge", "Sport & Freizeit"]
SUB_ORDER = ["Kiten", "Surfen", "Wingfoil", "SUP", "Segeln", "Wakeboard", "Bootsausflug", "Fähre", "Angeln", "Bootsverleih", "Tauchen", "Tretboot",
             "Natur", "Wandern", "Radfahren", "Radverleih", "Reiten", "Bauernhof", "Tiere", "Leuchtturm",
             "Golf", "Minigolf", "Klettern", "Spielplatz", "Führung", "Padel", "Tennis", "Wellness", "Yoga", "Fitness", "Kurse"]
AKT.sort(key=lambda a: (AKT_ORDER.index(a["category"]) if a.get("category") in AKT_ORDER else 9,
                        SUB_ORDER.index(a.get("subcategory")) if a.get("subcategory") in SUB_ORDER else 50, a["name"]))
ICON_SUN = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
KIDS_SUB = {"Spielplatz", "Kinderprogramm", "Tiere", "Bauernhof", "Minigolf", "Tretboot", "Reiten"}
KIDS_RX = r"kinder|kids|familie|pony|streichel|abenteuer|barfu|alpaka|schmetterling|tretboot|spielpl"
def for_kids(a):
    if a.get("subcategory") == "Radverleih" or "Hofladen" in a["name"]:
        return False
    return a.get("subcategory") in KIDS_SUB or bool(re.search(KIDS_RX, (a["name"] + " " + (a.get("text") or "")).lower()))
def norm_name(s):
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u"))[:14]
def akt_html():
    out = []
    well_names = {norm_name(w["name"]) for w in WELL}
    for a in AKT:
        if norm_name(a["name"]) in well_names or a.get("category") == "Bei Regen":
            continue
        ph = a.get("photo") or {}
        src = ph.get("file") or ""
        if not src or not (HERE / src).exists() or a.get("opening_hours") is not None or a.get("lat") is not None:
            kids = ' data-kids="1"' if (a.get("kids") or for_kids(a)) else ' data-kids=""'
            out.append(venue_card(a, "akt", a.get("category", ""), a.get("subcategory") or a.get("category", ""), kids))
            continue
        sym = " (Symbolfoto)" if ph.get("kind") == "symbol" else ""
        wp = web_pic(a)
        credit = ""
        if wp:
            src, sym, credit = wp[0], "", f'<span class="map-credit">Foto: {esc(wp[1])}</span>'
        price = nodash(a.get("price") or "")
        season = nodash(a.get("season") or "")
        out.append(
            f'<li class="rcard akt-item" data-cat="{esc(a.get("category", ""))}" data-sub="{esc(a.get("subcategory") or "")}" data-kids="{"1" if for_kids(a) else ""}"{town_attrs(a)}><a class="rcard-link" href="{esc(a["url"])}" rel="noopener" target="_blank">'
            f'<span class="rcard-photo card-photo"><img src="{esc(src)}" alt="{esc(a["name"])}{sym}" loading="lazy" width="900" height="600" referrerpolicy="no-referrer">'
            f'<span class="card-cat">{esc(a.get("subcategory") or a.get("category", ""))}</span>{credit}</span>'
            f'<span class="rcard-body"><span class="rcard-title">{esc(nodash(a["name"]))}</span>'
            f'<span class="card-meta"><span>{ICON_PIN}{esc(short_town(a.get("town") or "Fehmarn"))}</span>'
            + (f'<span>{ICON_EURO}{esc(price)}</span>' if price else "")
            + (f'<span>{ICON_SUN}{esc(season)}</span>' if season else "")
            + '</span><span class="rcard-go">Zur Website</span></span></a></li>')
    return "".join(out)
def akt_credits():
    seen, parts = set(), []
    for a in AKT:
        ph = a.get("photo") or {}
        if ph.get("commons_title") and ph["commons_title"] not in seen and (HERE / ph.get("file", "x")).exists():
            seen.add(ph["commons_title"])
            parts.append(f'{esc(ph["commons_title"].replace("File:", "").rsplit(".", 1)[0])}: {esc(re.sub(r"\s+", " ", ph.get("author") or "")[:50])} ({esc(ph.get("license") or "")})')
    return "; ".join(parts)


# --- Nightlife (data/nightlife.json)
NIGHT_FILE = ROOT / "data" / "nightlife.json"
NIGHT = json.loads(NIGHT_FILE.read_text())["items"] if NIGHT_FILE.exists() else []
NIGHT_ORDER = ["Bar", "Cocktailbar", "Strandbar", "Kneipe", "Club", "Livemusik", "Weinbar", "Party-Reihe", "Sonstiges"]
NIGHT.sort(key=lambda a: (NIGHT_ORDER.index(a.get("subcategory")) if a.get("subcategory") in NIGHT_ORDER else 99, a["name"]))

from urllib.parse import urlparse
USED_IMG = set()
OPEN_LIC = {"CC-BY-SA": "https://creativecommons.org/licenses/by-sa/4.0/", "CC-BY": "https://creativecommons.org/licenses/by/4.0/", "CC0": "https://creativecommons.org/publicdomain/zero/1.0/"}
def open_credits():
    seen, parts = set(), []
    for f in sorted((ROOT / "data").glob("*.json")):
        try:
            items = json.loads(f.read_text()).get("items", [])
        except Exception:
            continue
        for a in items:
            o = a.get("open_photo") or {}
            if o.get("file") and o["file"] not in seen and (HERE / o["file"]).exists():
                seen.add(o["file"])
                lic = o.get("license", "")
                l = f'<a href="{OPEN_LIC[lic]}">{esc(lic)}</a>' if lic in OPEN_LIC else esc(lic)
                parts.append(f'{esc(nodash(a["name"]))}: {esc(o.get("author") or "TA.SH")} ({l})')
    return "; ".join(parts)
def web_pic(a):
    """Bild von der Website des Anbieters oder seiner Portalseite: nur eingebunden (nicht kopiert), mit Quelle."""
    o = a.get("open_photo") or {}  # offen lizenziert (Touristische Landesdatenbank SH), lokal gespeichert
    if o.get("file") and (HERE / o["file"]).exists() and o["file"] not in USED_IMG:
        USED_IMG.add(o["file"])
        return o["file"], f'{o.get("author") or "TA.SH"} ({o.get("license", "")})'
    w = a.get("web_photo") or {}
    if not w.get("ok") or not w.get("src") or w["src"] in USED_IMG:
        return None
    USED_IMG.add(w["src"])
    dom = urlparse(w.get("page") or a.get("url") or "").netloc.replace("www.", "")
    return w["src"], dom
def venue_pic(a, folder):
    wp = web_pic(a)
    if wp:
        return wp[0], esc(a["name"]), f'<span class="map-credit">Foto: {esc(wp[1])}</span>'
    ph = a.get("photo") or {}
    if ph.get("file") and (HERE / ph["file"]).exists() and ph.get("kind") in ("echt", "ort") and ph["file"] not in USED_IMG:
        USED_IMG.add(ph["file"])
        return ph["file"], esc(a["name"]), ""
    karte = f'img/{folder}/{a["slug"]}-karte.jpg'
    if (HERE / karte).exists():
        return karte, f'Lage von {esc(a["name"])} auf der Karte', '<span class="map-credit">Karte: OpenStreetMap</span>'
    if ph.get("file") and (HERE / ph["file"]).exists():
        return ph["file"], esc(a["name"]) + " (Symbolfoto)", ""
    return None, "", ""
def clean_hours(s):
    s = re.sub(r"\s*\((?:[^()]*?(?:OSM|fehmarn\.de|Stand|lt\.|laut|geprüft|Website)[^()]*?)\)", "", s or "")
    s = re.sub(r"\s*;?\s*Stand:?[^;]*$", "", s)
    return s.strip(" ;,")
def fmt_addr(s):
    s = (s or "").replace("–", "-")
    s = re.sub(r"Fehmarn OT ([\wäöüÄÖÜß-]+)", r"\1 (Fehmarn)", s)
    return s
FREE_NATURE = ("Natur & Ausflüge",)
def venue_card(a, folder, cat_attr, label, extra_attrs=""):
    src, alt, credit = venue_pic(a, folder)
    if not src or a.get("closed"):
        return ""
    hours, price = nodash(clean_hours(a.get("hours"))), nodash(a.get("price") or "")
    season = nodash(a.get("season") or "")
    oh = a.get("opening_hours") or ""
    addr = fmt_addr(a.get("address") or short_town(a.get("town") or "Fehmarn"))
    status = f'<span class="oh-status" data-oh="{esc(oh)}" hidden></span>' if oh else '<span class="oh-status" hidden></span>'
    gq = f'{a["name"]}, {a.get("address") or a.get("town") or "Fehmarn"}'
    return (f'<li class="rcard akt-item" data-cat="{esc(cat_attr)}" data-sub="{esc(a.get("subcategory") or a.get("town") or "")}" data-gq="{esc(gq)}"{extra_attrs}{town_attrs(a)}>'
            f'<a class="rcard-link" href="{esc(a.get("url") or a.get("source_url") or "#")}" rel="noopener" target="_blank">'
            f'<span class="rcard-photo card-photo{" is-map" if "karte" in src else ""}"><img src="{esc(src)}" alt="{alt}" loading="lazy" width="900" height="560" referrerpolicy="no-referrer">'
            f'<span class="card-cat">{esc(label)}</span>{credit}</span>'
            f'<span class="rcard-body"><span class="rcard-title">{esc(nodash(a["name"]))}</span>{status}'
            f'<span class="card-meta"><span>{ICON_PIN}{esc(addr)}</span>'
            + (f'<span>{ICON_CLOCK}{esc(hours)}</span>' if hours else (f'<span>{ICON_SUN}{esc(season)}</span>' if season else ("" if a.get("category") in FREE_NATURE or "Kneipp" in a["name"] else f'<span>{ICON_CLOCK}Öffnungszeiten auf der Website</span>')))
            + (f'<span>{ICON_EURO}{esc(price)}</span>' if price else "")
            + '</span><span class="rcard-go">Zur Website</span></span></a></li>')
def night_html():
    return "".join(venue_card(a, "night", a.get("subcategory") or "Sonstiges", a.get("subcategory") or "") for a in NIGHT)

# --- Wellness (data/wellness.json)
WELL_FILE = ROOT / "data" / "wellness.json"
WELL = json.loads(WELL_FILE.read_text())["items"] if WELL_FILE.exists() else []
WELL_ORDER = ["Therme & Bad", "Sauna", "Day Spa", "Massage", "Ayurveda", "Salzgrotte", "Yoga & Retreat", "Kosmetik", "Sonstiges"]
WELL.sort(key=lambda a: (WELL_ORDER.index(a.get("subcategory")) if a.get("subcategory") in WELL_ORDER else 99, a["name"]))
def well_html():
    return "".join(venue_card(a, "well", a.get("subcategory") or "Sonstiges", a.get("subcategory") or "") for a in WELL)
def well_credits():
    parts = [f'{esc(nodash(a["name"]))}: {esc(re.sub(r"\\s+", " ", a["photo"].get("author") or "")[:50])} ({esc(a["photo"].get("license") or "")})'
             for a in WELL if (a.get("photo") or {}).get("file") and (HERE / a["photo"]["file"]).exists()]
    return "; ".join(parts)
def night_credits():
    parts = [f'{esc(nodash(a["name"]))}: {esc(re.sub(r"\\s+", " ", a["photo"].get("author") or "")[:50])} ({esc(a["photo"].get("license") or "")})'
             for a in NIGHT if (a.get("photo") or {}).get("kind") == "echt" and (HERE / a["photo"]["file"]).exists()]
    parts.append("Lagekarten © OpenStreetMap-Mitwirkende (ODbL)")
    return "; ".join(parts)

# --- Strände: Liste und Daten für die Karte
BEACH_FILE = ROOT / "data" / "straende.json"
BEACHES = json.loads(BEACH_FILE.read_text())["beaches"] if BEACH_FILE.exists() else []
BEACH_PH_FILE = HERE / "img" / "strand" / "credits.json"
BEACH_PH = json.loads(BEACH_PH_FILE.read_text()) if BEACH_PH_FILE.exists() else {}
for bch in BEACHES:
    bc = BEACH_PH.get(bch["name"], {})
    if bc.get("file") and (HERE / bc["file"]).exists():
        bch["img"] = bc["file"]
def beach_credits():
    parts = []
    for n, v in BEACH_PH.items():
        for g in [v] + v.get("gallery", []):
            if g.get("file") and (HERE / g["file"]).exists():
                parts.append(f'{esc(n)}: {esc(re.sub(r"\\s+", " ", g.get("author") or "")[:50])} ({esc(g.get("license") or "")})')
    return "; ".join(parts)
def beach_list():
    out = []
    for i, bch in enumerate(BEACHES, 1):
        g = f'https://www.google.com/maps/search/?api=1&query={bch["lat"]},{bch["lon"]}'
        tags = "".join(f'<span class="tag">{esc(x)}</span>' for x in bch.get("tags", []))
        bc = BEACH_PH.get(bch["name"], {})
        gal = [g for g in ([dict(file=bc.get("file"))] + bc.get("gallery", [])) if g.get("file") and (HERE / g["file"]).exists()]
        img = ""
        if gal:
            thumbs = "".join(f'<span class="bthumb" role="button" tabindex="0" data-src="{esc(g["file"])}" aria-label="Foto {k + 1} von {len(gal)} zeigen" aria-pressed="{str(k == 0).lower()}">'
                             f'<img src="{esc(g["file"])}" alt="" loading="lazy" width="160" height="107"></span>' for k, g in enumerate(gal)) if len(gal) > 1 else ""
            img = (f'<span class="bphoto"><img class="bbig" src="{esc(gal[0]["file"])}" alt="{esc(bch["name"])}" loading="lazy" width="900" height="600"></span>'
                   + (f'<span class="bthumbs">{thumbs}</span>' if thumbs else ""))
        out.append(f'<li class="bitem" data-i="{i-1}"><button type="button" class="bitem-btn" data-i="{i-1}"><span class="bnum num">{i}</span>'
                   f'<span class="bmain"><span class="bname">{esc(bch["name"])}</span><span class="bside">{esc(bch.get("side", ""))}küste</span>'
                   f'<span class="btext">{esc(bch.get("text", ""))}</span><span class="btags">{tags}</span></span></button>'
                   f'<span class="bgallery">{img}</span><a class="bgoogle" href="{g}" target="_blank" rel="noopener">In Google Maps öffnen</a></li>')
    return "".join(out)

page = (HERE / "index.template.html").read_text()
for k, v in {
    "TODAY_LONG": fmt_day(TODAY), "TODAY_ISO": iso(TODAY),
    "TODAY_N": str(n_on(TODAY, TODAY)), "TOMORROW_N": str(n_on(tomorrow, tomorrow)),
    "WEEKEND_N": str(n_on(sat, sun)), "WEEK_N": str(n_on(TODAY, TODAY + dt.timedelta(days=6))),
    "TOTAL": str(len(events)), "STATIC_DAYS": static_html,
    "DAYBAR": daybar(), "RAIN": rain_html(), "AKTIV": akt_html(), "NIGHT": night_html(), "WELL": well_html(), "BEACH_LIST": beach_list(), "BEACH_JSON": json.dumps(BEACHES, ensure_ascii=False), "CREDITS": re.sub(r"&quot;(.*?)&quot;", "„\\1“", re.sub(r"\s+-{1,2}\s+|\s*–\s*", ", ", credits_html())), "TOWNS_F": towns_html(True), "TOWNS_O": towns_html(False), "YEAR_MONTHS": year_html(),
    "EVENTS_JSON": json.dumps(events, ensure_ascii=False).replace("</", "<\\/"),
    "GENERATED": (lambda d: f"{d.day}. {MO[d.month-1]} {d.year}")(dt.date.fromisoformat(DATA["generated"][:10])),
}.items():
    page = page.replace("{{" + k + "}}", v)
import time as _t
_v = str(int(_t.time()))
for f in ["style.css", "app.js", "strand.js", "aktiv.js", "upload.js", "night.js"]:
    page = page.replace(f'"{f}"', f'"{f}?v={_v}"')  # Browser-Cache umgehen
page = re.sub(r"(\d) €", "\\1\u00a0€", page)
(HERE / "index.html").write_text(page)
print(f"{len(events)} Events · heute {n_on(TODAY, TODAY)} · Wochenende {n_on(sat, sun)} · frei {sum(e['free'] for e in events)} · "
      f"Kategorien {dict(Counter(e['cat'] for e in events))}")

# --- Rechtsseiten (Texte aus eRecht24, Projekt "Fehmarn Today", in legal/*.frag.html)
LEGAL = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex, nofollow">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Fehmarn Today</title>
<meta name="theme-color" content="#F6F8FA">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link href="fonts.css" rel="stylesheet">
<link rel="stylesheet" href="style.css?v={v}">
</head>
<body>
<header class="nav">
  <div class="container">
    <a class="wordmark" href="./" aria-label="Fehmarn Today, zur Startseite">
      <span class="wm-c"><span class="wm-1">Fehmarn</span><span class="wm-2">Today</span></span>
    </a>
    <a class="legal-back" href="./">Zur Startseite</a>
  </div>
</header>
<main class="legal container">
{body}
</main>
<footer class="foot legal-foot">
  <div class="container">
    <ul class="legal-links"><li><a href="./">Startseite</a></li><li><a href="impressum.html">Impressum</a></li><li><a href="datenschutz.html">Datenschutz</a></li><li><a href="nutzungsbedingungen.html">Nutzungsbedingungen</a></li></ul>
  </div>
</footer>
</body>
</html>
"""
for slug, title in (("impressum", "Impressum"), ("datenschutz", "Datenschutz"), ("nutzungsbedingungen", "Nutzungsbedingungen")):
    frag = HERE / "legal" / f"{slug}.frag.html"
    if frag.exists():
        (HERE / f"{slug}.html").write_text(LEGAL.format(title=title, body=frag.read_text(), v=_v))
