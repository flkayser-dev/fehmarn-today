"""
PROTOTYP: Findet das Vorschaubild (og:image) auf der EIGENEN Website eines Anbieters.
Das Bild wird NICHT kopiert oder veröffentlicht: In den Daten steht nur die Adresse, die Seite bindet es
direkt vom Server des Anbieters ein und nennt die Quelle. Für die Prüfung wird eine Vorschau lokal im
Scratch-Ordner abgelegt (nicht im Projekt).
Starten: python3 site/webbilder.py <scratch-ordner-für-vorschauen>
"""
import json, re, ssl, sys, time, pathlib, io, urllib.request, urllib.parse, urllib.robotparser
import certifi
from html.parser import HTMLParser
from PIL import Image

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
SETS = ["nightlife.json", "wellness.json", "aktiv-ostholstein.json", "aktiv-wasser.json", "aktiv-natur.json", "aktiv-sport.json", "regen.json"]
SSL = ssl.create_default_context(cafile=certifi.where())
UA = "Mozilla/5.0 (Macintosh) FehmarnToday-Prototype/0.1"
# Portale und Netzwerke: deren Bilder gehören nicht dem Anbieter
SKIP = re.compile(r"fehmarn\.de|heiligenhafen-touristik|hamburg-tourism|rausgegangen|facebook|instagram|google|ostsee-schleswig-holstein|grossenbrode\.de|stadtfehmarn|tripadvisor|wikipedia")
PREVIEW = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
if len(sys.argv) > 2: SETS = sys.argv[2].split(",")  # nur bestimmte Dateien

class Meta(HTMLParser):
    def __init__(self):
        super().__init__(); self.found = []; self.imgs = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and (a.get("property") or a.get("name") or "").lower() in ("og:image", "og:image:url", "twitter:image", "twitter:image:src"):
            if a.get("content"): self.found.append(a["content"])
        if tag == "link" and (a.get("rel") or "").lower() == "image_src" and a.get("href"):
            self.found.append(a["href"])
        if tag == "img":
            src = a.get("data-src") or a.get("data-lazy-src") or a.get("src") or ""
            ss = a.get("srcset") or a.get("data-srcset") or ""
            if ss:  # größte Variante aus srcset
                parts = [p.strip().split(" ") for p in ss.split(",") if p.strip()]
                best = max(parts, key=lambda x: int(re.sub(r"\D", "", x[1]) or 0) if len(x) > 1 else 0)
                src = best[0] or src
            if src and not src.startswith("data:"):
                self.imgs.append(src)

robots = {}
def allowed(url):
    p = urllib.parse.urlparse(url); base = f"{p.scheme}://{p.netloc}"
    if base not in robots:
        rp = urllib.robotparser.RobotFileParser(); rp.set_url(base + "/robots.txt")
        try: rp.read()
        except Exception: rp = None
        robots[base] = rp
    rp = robots[base]
    return True if rp is None else rp.can_fetch(UA, url)

def get(url, limit=3_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "de"})
    with urllib.request.urlopen(req, context=SSL, timeout=20) as r:
        return r.geturl(), r.read(limit)

for fname in SETS:
    f = DATA / fname
    if not f.exists(): continue
    d = json.loads(f.read_text())
    for a in d["items"]:
        url = a.get("url") or ""
        wp0 = a.get("web_photo") or {}
        if not url or SKIP.search(url) or wp0.get("ok") or ("note" in wp0 and not wp0.get("rejected")): continue
        try:
            if not allowed(url): a["web_photo"] = {"note": "robots.txt verbietet Abruf"}; continue
            final, html = get(url)
            m = Meta(); m.feed(html.decode("utf-8", "ignore"))
            cands = [urllib.parse.urljoin(final, u) for u in m.found + m.imgs]
            rej = set((a.get("web_photo") or {}).get("rejected", []))
            cands = [c for c in dict.fromkeys(cands) if c not in rej and not re.search(r"logo|favicon|icon|placeholder|sprite|banner-ad|\.svg|\.gif|pixel|tracking|badge|siegel|award|map", c, re.I)]
            if not cands: a["web_photo"] = {"note": "kein Bild auf der Website"}; continue
            src, w, h, ok, im = None, 0, 0, False, None
            for c in cands[:8]:
                try:
                    _, raw = get(c, 8_000_000)
                    im = Image.open(io.BytesIO(raw)); w, h = im.size
                except Exception:
                    continue
                src, ok = c, w >= 700 and w >= h * 1.25
                if ok: break
                time.sleep(0.5)
            if not src: a["web_photo"] = {"note": "Bilder nicht ladbar"}; continue
            a["web_photo"] = {"src": src, "page": final, "w": w, "h": h, "ok": ok, "rejected": sorted(rej), "recheck": bool(rej)}
            if PREVIEW and ok:
                PREVIEW.mkdir(parents=True, exist_ok=True)
                im.convert("RGB").resize((300, int(300 * h / w))).save(PREVIEW / f'{a["slug"] if "slug" in a else re.sub("[^a-z0-9]+", "-", a["name"].lower())}.jpg')
            print("Bild:", a["name"], w, "x", h, "ok" if ok else "zu klein/hochkant", flush=True)
        except Exception as e:
            a["web_photo"] = {"note": f"nicht abrufbar: {type(e).__name__}"}
        time.sleep(1)
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1))
