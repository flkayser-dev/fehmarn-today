"""
PROTOTYP: Lagekarten für Lokale ohne eigenes Foto (Kacheln von OpenStreetMap, © OpenStreetMap-Mitwirkende, ODbL).
Starten: python3 site/lagekarte.py   (liest data/nightlife.json, schreibt site/img/night/<slug>-karte.jpg)
Nur wenige Kacheln, mit Pause, nach den Nutzungsregeln von tile.openstreetmap.org; vorhandene Karten werden nicht neu geladen.
"""
import json, math, io, os, time, pathlib, ssl, urllib.request
import certifi
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data" / "nightlife.json"
SSL = ssl.create_default_context(cafile=certifi.where())
UA = {"User-Agent": "FehmarnToday-Prototype/0.1 (Lagekarten, wenige Kacheln)"}
Z, W, H = 17, 900, 560
INK, PAPER = (3, 32, 61), (252, 253, 254)
CACHE = HERE / "img" / "night" / ".tiles"

def tile(x, y):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{Z}-{x}-{y}.png"
    if not f.exists():
        req = urllib.request.Request(f"https://tile.openstreetmap.org/{Z}/{x}/{y}.png", headers=UA)
        f.write_bytes(urllib.request.urlopen(req, context=SSL, timeout=30).read())
        time.sleep(0.4)
    return Image.open(f).convert("RGB")

def karte(lat, lon, out):
    n = 2 ** Z
    fx = (lon + 180) / 360 * n
    fy = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    px, py = fx * 256, fy * 256
    x0, y0 = int((px - W / 2) // 256), int((py - H / 2) // 256)
    x1, y1 = int((px + W / 2) // 256), int((py + H / 2) // 256)
    big = Image.new("RGB", ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            big.paste(tile(x, y), ((x - x0) * 256, (y - y0) * 256))
    left, top = px - x0 * 256 - W / 2, py - y0 * 256 - H / 2
    img = big.crop((int(left), int(top), int(left) + W, int(top) + H))
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    d.ellipse((cx - 34, cy - 34, cx + 34, cy + 34), fill=PAPER)
    d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), fill=INK)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=PAPER)
    img.save(out, quality=82)

SETS = [("nightlife.json", "night"), ("wellness.json", "well"), ("aktiv-ostholstein.json", "akt")]

if __name__ == "__main__":
    items = []
    for fname, folder in SETS:
        f = HERE.parent / "data" / fname
        if f.exists():
            items += [dict(a, _folder=folder) for a in json.loads(f.read_text())["items"]
                      if not ((a.get("photo") or {}).get("file") and (HERE / a["photo"]["file"]).exists())]
    for a in items:
        if a.get("lat") is None or a.get("lon") is None:
            print("ohne Koordinaten:", a["name"]); continue
        (HERE / "img" / a["_folder"]).mkdir(parents=True, exist_ok=True)
        out = HERE / "img" / a["_folder"] / f'{a["slug"]}-karte.jpg'
        if not out.exists() or os.environ.get("NEU"):
            karte(float(a["lat"]), float(a["lon"]), out)
            print("Karte:", a["name"])
