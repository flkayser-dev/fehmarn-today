"""
Social-Media-Bilder aus den Terminen.
  python3 social/social.py vorbereiten [start] [ordner]  -> 7 Tage Posts (Bilder + plan.json mit Text und Zeit)
  python3 social/social.py tag 2026-11-25     -> nur ein Tages-Karussell (social/out/)
  python3 social/social.py woche 2026-11-29   -> Wochenüberblick ab dem folgenden Montag (social/out/<datum>-woche/)
Ohne Datum: heute (tag) bzw. nächster Sonntag (woche).
"""
import json, re, sys, html, pathlib, subprocess, datetime as dt, shutil
from zoneinfo import ZoneInfo

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
EVENTS = ROOT / "prototype_scraper" / "PROTOTYPE_events.json"
URL = "fehmarntoday.de"
CHROME = shutil.which("google-chrome") or shutil.which("chromium") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WD = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MO = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
MAX_EVENTS = 8  # Instagram-Schnittstelle: höchstens 10 Bilder je Karussell (Start + 8 Termine + Schluss)
W, H = 1080, 1350
e_ = lambda s: html.escape(s or "")


def town(t):
    t = (t or "").strip()
    if t.startswith("Fehmarn OT "):
        return t[11:] + " auf Fehmarn"
    return t.replace(" in Holstein", "")


def on_fehmarn(e):
    return "Fehmarn" in (e.get("town") or "")


FAR = re.compile(r"Kiel|Lübeck|Flensburg|Hamburg|HH-|Neumünster|Rendsburg|Schleswig|Husum")  # zu weit weg für "auf Fehmarn"


def load(day, fehmarn_first=True):
    ev = json.loads(EVENTS.read_text())["events"]
    ev = [e for e in ev if e.get("date") == day.isoformat() and not (e.get("title") or "").startswith("Anzeige")
          and not FAR.search(e.get("town") or "")]
    ev.sort(key=lambda e: ((not on_fehmarn(e)) if fehmarn_first else 0, e.get("time") or "99"))
    return ev


CSS = f"""
@import url("{(ROOT / 'site' / 'fonts.css').as_uri()}");
:root{{--ink:#03203D;--red:#EB2F33;--stone:#639CC5;--sink:#3E6F94;--paper:#F6F8FA;--white:#FCFDFE;--rule:#cfdbe6}}
*{{box-sizing:border-box;margin:0}}
body{{width:{W}px;height:{H}px;overflow:hidden;font-family:'Hanken Grotesk',sans-serif;color:var(--ink);background:var(--paper);padding:80px;display:flex;flex-direction:column}}
.sign{{display:inline-flex;align-self:flex-start;font-family:Antonio;font-weight:700;text-transform:uppercase;line-height:1;font-size:44px;color:var(--white)}}
.sign span{{padding:.2em .34em .17em}}.sign .a{{background:var(--ink)}}.sign .b{{background:var(--red)}}
.A{{font-family:Antonio;font-weight:700;text-transform:uppercase;line-height:.95}}
.foot{{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font-size:28px;font-weight:700}}
.foot .n{{color:var(--sink)}}
.dark{{background:var(--ink);color:var(--white)}}
.dark .sign .a{{box-shadow:inset 0 0 0 3px var(--white)}}
"""


def page(body, cls=""):
    return f'<!doctype html><meta charset=utf-8><style>{CSS}</style><body class="{cls}">{body}</body>'


def sign():
    return '<span class=sign><span class=a>Fehmarn</span><span class=b>Today</span></span>'


def datum(d):
    return f"{WD[d.weekday()]}, {d.day}. {MO[d.month-1]}"


def slide_cover(title, sub, n, hint):
    return page(f"""{sign()}
<h1 class=A style="font-size:200px;margin-top:90px">{title}</h1>
<p style="font-size:46px;font-weight:700;color:var(--sink);margin-top:24px">{sub}</p>
<p style="margin-top:70px;display:flex;align-items:center;gap:24px;font-size:40px;font-weight:700">
<span class=A style="background:var(--red);color:var(--white);font-size:96px;padding:.06em .28em .02em">{n}</span>{hint}</p>
<div class=foot><span>{URL}</span><span class=n>Nach rechts wischen</span></div>""")


def slide_event(e, i, n, d):
    t = e.get("time") or "ganztags"
    t = t.replace("–", " bis ")
    where = ", ".join(x for x in [e_(e.get("venue")), e_(town(e.get("town")))] if x)
    host = re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*", r"\1", e.get("url") or ""))
    region = "Fehmarn" if on_fehmarn(e) else "Ostholstein"
    return page(f"""<div style="display:flex;justify-content:space-between;align-items:center">{sign()}<span style="font-size:28px;font-weight:700;color:var(--sink)">{i} von {n}</span></div>
<p style="margin-top:90px;font-size:34px;font-weight:700;color:var(--red)">{datum(d)}, {region}</p>
<p class=A style="font-size:120px;margin-top:20px">{e_(t)}{" Uhr" if t[:1].isdigit() else ""}</p>
<h2 style="font-size:76px;line-height:1.08;margin-top:44px;font-weight:800;letter-spacing:-.01em">{e_(e.get("title"))}</h2>
<p style="font-size:40px;font-weight:600;color:var(--sink);margin-top:24px">{where}</p>
<p style="font-size:34px;font-weight:600;margin-top:56px;color:var(--ink)">Alle Infos: {e_(host)}</p>
<div class=foot><span class=n>Quelle: {e_(e.get("source"))}</span><span>{URL}</span></div>""")


def slide_cta():
    return page(f"""{sign()}
<h1 class=A style="font-size:170px;margin-top:110px">Dein Event<br>fehlt?</h1>
<p style="font-size:48px;font-weight:700;line-height:1.25;margin-top:50px;max-width:18em">Trag es kostenlos ein. Flohmarkt, Konzert, Kurs oder Fest: Wir nehmen es auf.</p>
<p style="margin-top:60px;align-self:flex-start;background:var(--red);color:var(--white);font-size:46px;font-weight:800;padding:.5em .8em">{URL}</p>
<p style="font-size:34px;font-weight:600;color:var(--stone);margin-top:24px">Auf der Seite unten: „Termin melden“</p>
<div class=foot><span>Fehmarn Today</span><span style="color:var(--stone)">Jeden Tag neu</span></div>""", "dark")


def slide_day(d, ev):
    zug = re.compile(r"konzert|musik|band|markt|party|fest|gospel|jazz|lesung|theater|kino|führung|lichter|feuer", re.I)
    if len(ev) > 5:  # bei vielen Terminen die zugkräftigsten zeigen, in Zeitfolge
        top = sorted(ev, key=lambda e: (not on_fehmarn(e), not zug.search(e.get("title") or "")))[:5]
        ev = sorted(top, key=lambda e: e.get("time") or "99") + [e for e in ev if e not in top]
    rows = "".join(
        f'<li><span class=tm>{e_((e.get("time") or "ganztags").split("–")[0])}</span>'
        f'<span class=ti>{e_(e["title"])}<em>{e_(town(e.get("town")))}</em></span></li>' for e in ev[:5])
    more = f'<p style="font-size:30px;font-weight:700;color:var(--sink);margin-top:26px">Und {len(ev)-5} weitere auf {URL}</p>' if len(ev) > 5 else ""
    empty = "" if ev else '<p style="font-size:40px;font-weight:600;color:var(--sink);margin-top:40px">Noch nichts bekannt. Du weißt etwas? Trag es ein.</p>'
    return page(f"""{sign()}
<h1 class=A style="font-size:150px;margin-top:70px">{WD[d.weekday()]}</h1>
<p style="font-size:44px;font-weight:700;color:var(--red);margin-top:14px">{d.day}. {MO[d.month-1]}</p>
<style>ul{{list-style:none;padding:0;margin-top:50px;border-top:3px solid var(--ink)}}li{{display:grid;grid-template-columns:150px 1fr;gap:20px;padding:22px 0;border-bottom:1.5px solid var(--rule);align-items:baseline}}
.tm{{font-size:34px;font-weight:800}}.ti{{font-size:34px;font-weight:700;line-height:1.2}}em{{display:block;font-style:normal;font-weight:500;color:var(--sink);font-size:28px;margin-top:4px}}</style>
{'<ul>' + rows + '</ul>' if ev else ''}{more}{empty}
<div class=foot><span>{URL}</span><span class=n>Nach rechts wischen</span></div>""")


KURZ = ["MO", "DI", "MI", "DO", "FR", "SA", "SO"]


def highlight(ev):
    """Ein Termin pro Tag für die Übersicht: zuerst Fehmarn, abends vor tagsüber."""
    if not ev:
        return None
    zug = re.compile(r"konzert|musik|band|markt|party|fest|gospel|jazz|lesung|theater|kino|führung|lichter|feuer", re.I)
    return sorted(ev, key=lambda e: (not on_fehmarn(e), not zug.search(e.get("title") or ""),
                                     not (e.get("time") or "").startswith(("18", "19", "20", "21")), e.get("time") or "99"))[0]


def slide_week_overview(days, evs):
    a, b = days[0], days[-1]
    total = sum(len(x) for x in evs)
    rows = ""
    for d, ev in zip(days, evs):
        h = highlight(ev)
        what = (f'<span class=t>{e_(h["title"])}</span><em>{e_((h.get("time") or "ganztags").split("–")[0])}{" Uhr" if (h.get("time") or "")[:1].isdigit() else ""}, {e_(town(h.get("town")))}</em>'
                if h else '<span class=t style="color:var(--sink)">Noch nichts bekannt</span>')
        rows += (f'<li><span class=dd><b>{KURZ[d.weekday()]}</b>{d.day}.{d.month}.</span>'
                 f'<span class=wt>{what}</span><span class=nn>{len(ev)}</span></li>')
    span = f"{a.day}. {MO[a.month-1]} bis {b.day}. {MO[b.month-1]}" if a.month != b.month else f"{a.day}. bis {b.day}. {MO[b.month-1]}"
    return page(f"""{sign()}
<h1 class=A style="font-size:112px;margin-top:40px">Die Woche<br>auf Fehmarn</h1>
<p style="font-size:38px;font-weight:700;color:var(--sink);margin-top:14px">{span}, {total} Termine</p>
<style>ul{{list-style:none;padding:0;margin-top:34px;border-top:3px solid var(--ink)}}
li{{display:grid;grid-template-columns:132px minmax(0,1fr) 64px;gap:22px;align-items:center;padding:13px 0;border-bottom:1.5px solid var(--rule)}}
.dd{{font-family:Antonio;font-weight:700;font-size:30px;line-height:1;display:flex;flex-direction:column;gap:4px;color:var(--sink)}}
.dd b{{font-size:44px;background:var(--red);color:var(--white);padding:.08em .2em .02em;align-self:flex-start}}
.wt{{min-width:0}}.wt .t{{display:block;font-size:31px;font-weight:700;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.wt em{{display:block;font-style:normal;font-weight:500;color:var(--sink);font-size:26px;margin-top:3px}}
.nn{{font-family:Antonio;font-weight:700;font-size:46px;text-align:right}}</style>
<ul>{rows}</ul>
<div class=foot><span>{URL}</span><span class=n>Wischen für jeden Tag</span></div>""")


HASH_BASE = ["#fehmarn", "#ostsee", "#ostholstein", "#fehmarntoday"]
HASH_RULES = [(r"konzert|musik|band|jazz|gospel|rock|chor|singen", "#livemusik"), (r"weihnacht|advent", "#weihnachtsmarkt"),
              (r"flohmarkt|trödel", "#flohmarkt"), (r"markt", "#markt"), (r"workshop|kurs|basteln|malen|nähen", "#workshop"),
              (r"kinder|familie", "#familienzeit"), (r"yoga|meditation|achtsam", "#yoga"), (r"lesung|vortrag|museum", "#kultur"),
              (r"führung|wanderung|radtour", "#draussen")]


def hashtags(ev):
    text = " ".join((e.get("title") or "") for e in ev).lower()
    tags = [t for rx, t in HASH_RULES if re.search(rx, text)]
    return " ".join(HASH_BASE + list(dict.fromkeys(tags))[:4] + ["#fehmarnurlaub"])


def zeile(e, mit_tag=False, d=None):
    t = (e.get("time") or "").split("–")[0]
    pre = f"{KURZ[d.weekday()].capitalize()} " if mit_tag and d else ""
    return f"{pre}{t + ' ' if t else ''}{e['title']} ({town(e.get('town'))})".replace("  ", " ")


def caption_tag(d, ev):
    open_ = ["Was ist heute los auf Fehmarn?", "Heute auf der Insel:", "Dein Tag auf Fehmarn:", "Plan für heute gesucht?",
             "Das steht heute an:", "Heute geht was auf Fehmarn:", "Für heute vorgemerkt:"][d.toordinal() % 7]
    lines = "\n".join(zeile(e) for e in ev[:4])
    more = f"\nUnd {len(ev) - 4} weitere im Karussell." if len(ev) > 4 else ""
    return (f"{open_} {datum(d)}, {len(ev)} Termine.\n\n{lines}{more}\n\n"
            f"Zeiten und Orte: einfach durchwischen. Alles Weitere auf {URL}\n"
            f"Dein Termin fehlt? Auf {URL} kostenlos eintragen.\n\n{hashtags(ev)}")


def caption_woche(days, evs):
    a, b = days[0], days[-1]
    total = sum(len(x) for x in evs)
    hl = [(d, highlight(ev)) for d, ev in zip(days, evs) if highlight(ev)]
    zug = re.compile(r"konzert|musik|band|markt|party|fest|gospel|jazz|lesung|theater|kino|führung|lichter|feuer", re.I)
    hl = [x for x in hl if on_fehmarn(x[1])] or hl
    hl = sorted(sorted(hl, key=lambda x: (not zug.search(x[1]["title"]), x[0]))[:5], key=lambda x: x[0])
    lines = "\n".join(zeile(h, True, d) for d, h in hl)
    return (f"Die Woche auf Fehmarn: {total} Termine vom {a.day}.{a.month}. bis {b.day}.{b.month}.\n\n"
            f"Ein paar Tipps:\n{lines}\n\nJeder Tag im Karussell, jeden Morgen um 10 der Tagesplan.\n"
            f"Dein Termin fehlt? Auf {URL} kostenlos eintragen.\n\n{hashtags([e for x in evs for e in x])}")


def render(pages, out, jpg=False, size=(W, H)):
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("*.png")) + list(out.glob("*.jpg")):
        old.unlink()
    files = []
    for i, p in enumerate(pages, 1):
        f = out / f"{i:02d}.html"
        f.write_text(p)
        png = out / f"{i:02d}.png"
        subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", "--allow-file-access-from-files", "--virtual-time-budget=5000",
                        f"--window-size={size[0]},{size[1]}", f"--screenshot={png}", f.as_uri()],
                       capture_output=True, check=True)
        f.unlink()
        if jpg:  # Instagram nimmt über die Schnittstelle nur JPEG
            from PIL import Image
            Image.open(png).convert("RGB").save(out / f"{i:02d}.jpg", quality=88)
            png.unlink()
            files.append(f"{i:02d}.jpg")
        else:
            files.append(png.name)
    print(out, len(pages), "Bilder")
    return files


# --- Reel (9:16 Video, ohne Ton: den Sound wählt man in der App)
RW, RH = 1080, 1920
REEL_FOTOS = [  # Datei in site/img, Fotograf, Lizenz
    ("moewe-strandkorb", "Superbass", "CC BY-SA 4.0"), ("strand-bruecke", "Dguendel", "CC BY 4.0"),
    ("kites-sund", "Superbass", "CC BY-SA 4.0"), ("fluegge-behrens", "Torsten Behrens", "CC BY 2.0"),
    ("orth-superbass", "Superbass", "CC BY-SA 4.0"), ("burgtiefe-luft", "Fabian Horst", "CC BY-SA 4.0"),
    ("bruecke-korn", "Superbass", "CC BY-SA 4.0")]
REEL_MAX = 5
# Unten (~380 px) und rechts (~140 px) liegen bei Instagram und TikTok Knöpfe und Text: dort nichts Wichtiges.
RCSS = f"body{{width:{RW}px;height:{RH}px;padding:150px 150px 380px 80px}}"


def rpage(body, cls=""):
    return page(f"<style>{RCSS}</style>{body}", cls)


def reel_cover(d, n, foto):
    f, who, lic = foto
    bg = (ROOT / "site" / "img" / f"{f}.jpg").as_uri()
    return rpage(f"""<style>body.dark{{background:linear-gradient(180deg,rgba(3,32,61,.15) 0%,rgba(3,32,61,.55) 38%,rgba(3,32,61,.92) 70%),url('{bg}') center/cover;color:var(--white)}}</style>
{sign()}
<div style="margin-top:auto">
<p style="font-size:44px;font-weight:700;color:var(--white);opacity:.9">{datum(d)}</p>
<h1 class=A style="font-size:210px;margin-top:18px">Heute auf<br>Fehmarn</h1>
<p style="margin-top:44px;display:flex;align-items:center;gap:26px;font-size:46px;font-weight:700">
<span class=A style="background:var(--red);color:var(--white);font-size:110px;padding:.06em .28em .02em">{n}</span>Tipps für deinen Tag</p>
</div>
<p style="position:absolute;left:80px;bottom:60px;font-size:20px;opacity:.7">Foto: {e_(who)}, {lic}</p>""", "dark")


def reel_event(e, i, n, d):
    t = (e.get("time") or "ganztags").replace("–", " bis ")
    where = ", ".join(x for x in [e_(e.get("venue")), e_(town(e.get("town")))] if x)
    title = e_(e.get("title"))
    fs = 108 if len(title) < 40 else 88 if len(title) < 70 else 70
    return rpage(f"""<div style="display:flex;justify-content:space-between;align-items:center">{sign()}<span class=A style="font-size:52px;color:var(--sink)">{i}/{n}</span></div>
<div style="margin-top:auto;margin-bottom:auto">
<p style="font-size:46px;font-weight:700;color:var(--red)">{"Fehmarn" if on_fehmarn(e) else "Ostholstein"}</p>
<p class=A style="font-size:{180 if len(t) < 12 else 130}px;margin-top:16px">{e_(t)}{" Uhr" if t[:1].isdigit() else ""}</p>
<h2 style="font-size:{fs}px;line-height:1.08;margin-top:40px;font-weight:800;letter-spacing:-.01em">{title}</h2>
<p style="font-size:52px;font-weight:600;color:var(--sink);margin-top:32px">{where}</p>
</div>""")


def reel_cta(n_all):
    more = f"Alle {n_all} Termine von heute" if n_all > REEL_MAX else "Alle Termine, jeden Tag neu"
    return rpage(f"""{sign()}
<div style="margin-top:auto;margin-bottom:auto">
<h1 class=A style="font-size:150px">{more.split(",")[0]}</h1>
<p style="margin-top:56px;align-self:flex-start;display:inline-block;background:var(--red);color:var(--white);font-size:64px;font-weight:800;padding:.4em .6em">{URL}</p>
<p style="font-size:42px;font-weight:600;color:var(--stone);margin-top:40px">Folgen für den Tagesplan jeden Morgen</p>
</div>""", "dark")


def reel(d, out, fps=30):
    """Reel für einen Tag als MP4 (ohne Ton). Gibt den Pfad zurück oder None bei zu wenig Terminen."""
    ev = load(d)
    if len(ev) < MIN_TAG:
        return None
    top = ev[:REEL_MAX]
    foto = REEL_FOTOS[d.toordinal() % len(REEL_FOTOS)]
    pages = [reel_cover(d, len(top), foto)] + [reel_event(e, i, len(top), d) for i, e in enumerate(top, 1)] + [reel_cta(len(ev))]
    return video(pages, [2.6] + [2.2] * len(top) + [2.8], out, fps)


def hochkant(p):
    """Eine 4:5-Seite als 9:16-Seite (Sicherheitsabstände für die App-Knöpfe, kein 'Wischen'-Hinweis)."""
    for s in ("Nach rechts wischen", "Wischen für jeden Tag"):
        p = p.replace(s, "")
    z = 1.22  # alles größer: auf dem Handy im Hochformat sonst zu klein
    css = (f"body{{zoom:{z};width:{RW / z:.0f}px;height:{RH / z:.0f}px;"
           f"padding:{150 / z:.0f}px {130 / z:.0f}px {400 / z:.0f}px {70 / z:.0f}px}}")
    return p.replace("<body", f"<style>{css}</style><body", 1)


def reel_woche(start, out, fps=30):
    """Reel: erst die Wochenübersicht (start + 6 Tage), dann jeder Tag mit Terminen einzeln."""
    days = [start + dt.timedelta(days=i) for i in range(7)]
    evs = [load(x, fehmarn_first=False) for x in days]
    voll = [(x, ev) for x, ev in zip(days, evs) if ev]
    if len(voll) < 2:
        return None
    pages = [hochkant(slide_week_overview(days, evs))] + [hochkant(slide_day(x, ev)) for x, ev in voll] + [reel_cta(0)]
    return video(pages, [4.0] + [2.6] * len(voll) + [2.8], out, fps)


def video(pages, durs, out, fps=30):
    tmp = out / "_reel"
    files = render(pages, tmp, size=(RW, RH))
    X = 0.35  # Überblendung
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for f, s in zip(files, durs):
        cmd += ["-loop", "1", "-t", f"{s + X:.2f}", "-i", str(tmp / f)]
    flt = []
    for i, s in enumerate(durs):  # langsamer Zoom auf jedem Bild
        z = 0.04 if i == 0 else 0.02
        flt.append(f"[{i}:v]scale=w='trunc({RW}*(1+{z}*t/{s + X:.2f})/2)*2':h=-2:eval=frame,crop={RW}:{RH},fps={fps},format=yuv420p,setsar=1[v{i}]")
    last, off = "v0", 0.0
    for i in range(1, len(durs)):
        off += durs[i - 1]
        flt.append(f"[{last}][v{i}]xfade=transition=slideleft:duration={X}:offset={off - X * (i - 1):.2f}[x{i}]")
        last = f"x{i}"
    mp4 = out / "reel.mp4"
    cmd += ["-filter_complex", ";".join(flt), "-map", f"[{last}]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-r", str(fps), str(mp4)]
    subprocess.run(cmd, check=True)
    shutil.copy(tmp / files[0], out / "reel-cover.png")
    shutil.rmtree(tmp)
    print(mp4)
    return mp4


def caption_reel(d, ev):
    lines = "\n".join(zeile(e) for e in ev[:REEL_MAX])
    return (f"Heute auf Fehmarn, {datum(d)}:\n\n{lines}\n\nAlle Termine auf {URL}\n\n{hashtags(ev)}")


def pages_tag(d):
    ev = load(d)[:MAX_EVENTS]
    hint = "Termine auf Fehmarn" if all(on_fehmarn(e) for e in ev) else "Termine auf Fehmarn und in der Nähe"
    pages = [slide_cover("Heute auf<br>Fehmarn", datum(d), len(ev), hint)]
    pages += [slide_event(e, i, len(ev), d) for i, e in enumerate(ev, 1)]
    return ev, pages + [slide_cta()]


def pages_woche(sunday, ab_heute=False):
    first = sunday if ab_heute else sunday + dt.timedelta(days=1)
    days = [first + dt.timedelta(days=i) for i in range(7)]
    evs = [load(x, fehmarn_first=False) for x in days]
    pages = [slide_week_overview(days, evs)] + [slide_day(x, ev) for x, ev in zip(days, evs)] + [slide_cta()]
    return days, evs, pages


MIN_TAG = 2  # weniger Termine: kein Tagespost
START = dt.date(2026, 11, 23)  # Starttag: Wochenübersicht ab heute statt Tagespost


def vorbereiten(start, out_root, n_days=8):  # 8 Tage: sonntags auch der nächste Sonntag (TikTok-Planung)
    """Posts für n_days Tage ab start als Bilder + plan.json (Zeiten in deutscher Zeit)."""
    out_root.mkdir(parents=True, exist_ok=True)
    plan = []
    for i in range(n_days):
        d = start + dt.timedelta(days=i)
        if d == START:
            days, evs, pages = pages_woche(d, ab_heute=True)
            pid = f"{d.isoformat()}-start"
            files = render(pages, out_root / pid, jpg=True)
            plan.append({"id": pid, "kind": "start", "when": f"{d.isoformat()}T10:00", "images": [f"{pid}/{f}" for f in files],
                         "caption": caption_woche(days, evs)})
            continue
        if d.weekday() == 6:
            days, evs, pages = pages_woche(d)
            pid = f"{d.isoformat()}-woche"
            files = render(pages, out_root / pid, jpg=True)
            plan.append({"id": pid, "kind": "woche", "when": f"{d.isoformat()}T10:00", "images": [f"{pid}/{f}" for f in files],
                         "caption": caption_woche(days, evs)})
        ev, pages = pages_tag(d)
        if len(ev) >= MIN_TAG:
            pid = f"{d.isoformat()}-tag"
            files = render(pages, out_root / pid, jpg=True)
            plan.append({"id": pid, "kind": "tag", "when": f"{d.isoformat()}T{'10:30' if d.weekday() == 6 else '10:00'}",
                         "images": [f"{pid}/{f}" for f in files], "caption": caption_tag(d, ev)})
            try:  # Reel zum Selbstposten (Sound in der App wählen); ein Fehler hier darf die Bilder nicht verhindern
                if reel_woche(d, out_root / pid):  # Wochenübersicht ab diesem Tag, dann jeder Tag einzeln
                    plan[-1]["reel"] = f"{pid}/reel.mp4"
                    wk = [d + dt.timedelta(days=k) for k in range(7)]
                    (out_root / pid / "reel-caption.txt").write_text(caption_woche(wk, [load(x, fehmarn_first=False) for x in wk]).replace("Jeder Tag im Karussell", "Jeder Tag im Video"))
            except Exception as err:
                print("Reel fehlgeschlagen:", d, err)
    (out_root / "plan.json").write_text(json.dumps({"generated": dt.datetime.now(ZoneInfo("Europe/Berlin")).isoformat(timespec="minutes"),
                                                   "posts": plan}, ensure_ascii=False, indent=1))
    print(out_root / "plan.json", len(plan), "Posts")


if __name__ == "__main__":
    today = dt.datetime.now(ZoneInfo("Europe/Berlin")).date()
    kind = sys.argv[1] if len(sys.argv) > 1 else "vorbereiten"
    d = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else None
    if kind == "tag":
        render(pages_tag(d or today)[1], HERE / "out" / f"{(d or today).isoformat()}-tag")
    elif kind == "reel":
        d = d or today
        o = HERE / "out" / f"{d.isoformat()}-reel"
        o.mkdir(parents=True, exist_ok=True)
        if reel(d, o):
            (o / "caption.txt").write_text(caption_reel(d, load(d)))
    elif kind == "reelwoche":
        d = d or today
        o = HERE / "out" / f"{d.isoformat()}-reelwoche"
        o.mkdir(parents=True, exist_ok=True)
        if reel_woche(d, o):
            days = [d + dt.timedelta(days=i) for i in range(7)]
            (o / "caption.txt").write_text(caption_woche(days, [load(x, fehmarn_first=False) for x in days]))
    elif kind == "woche":
        s = d or today + dt.timedelta(days=(6 - today.weekday()) % 7)
        render(pages_woche(s)[2], HERE / "out" / f"{s.isoformat()}-woche")
    else:  # vorbereiten [startdatum] [zielordner]
        vorbereiten(d or today, pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else HERE / "posts")
