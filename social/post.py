"""
Veröffentlicht fällige Posts aus plan.json auf Instagram und Facebook (Meta Graph API).
  python3 social/post.py <ordner-mit-plan.json> <bild-basis-url>
Braucht die GitHub-Secrets META_PAGE_TOKEN, META_PAGE_ID, META_IG_USER_ID.
Ohne Token passiert nichts (Vorbereitungsphase). Bereits gepostete IDs stehen in social/posted.json.
"""
import json, os, sys, time, pathlib, urllib.request, urllib.parse, datetime as dt
from zoneinfo import ZoneInfo

GRAPH = "https://graph.facebook.com/v21.0"
HERE = pathlib.Path(__file__).parent
POSTED = HERE / "posted.json"
FENSTER = dt.timedelta(hours=3)  # verspätete Läufe holen bis zu 3 Stunden nach


def api(path, **params):
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(f"{GRAPH}/{path}", data=data), timeout=120) as r:
        return json.loads(r.read())


def api_get(path, **params):
    with urllib.request.urlopen(f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}", timeout=60) as r:
        return json.loads(r.read())


def instagram(ig, token, urls, caption):
    kids = [api(f"{ig}/media", image_url=u, is_carousel_item="true", access_token=token)["id"] for u in urls]
    box = api(f"{ig}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption, access_token=token)["id"]
    for _ in range(30):  # Meta verarbeitet die Bilder erst
        if api_get(box, fields="status_code", access_token=token).get("status_code") == "FINISHED":
            break
        time.sleep(10)
    return api(f"{ig}/media_publish", creation_id=box, access_token=token)["id"]


def facebook(page, token, urls, caption):
    ids = [api(f"{page}/photos", url=u, published="false", access_token=token)["id"] for u in urls]
    return api(f"{page}/feed", message=caption, attached_media=json.dumps([{"media_fbid": i} for i in ids]), access_token=token)["id"]


def main():
    folder, base = pathlib.Path(sys.argv[1]), sys.argv[2].rstrip("/")
    token, page, ig = (os.environ.get(k) for k in ("META_PAGE_TOKEN", "META_PAGE_ID", "META_IG_USER_ID"))
    plan = json.loads((folder / "plan.json").read_text())["posts"]
    posted = json.loads(POSTED.read_text()) if POSTED.exists() else {}
    now = dt.datetime.now(ZoneInfo("Europe/Berlin")).replace(tzinfo=None)
    due = [p for p in plan if p["id"] not in posted
           and dt.timedelta(0) <= now - dt.datetime.fromisoformat(p["when"]) <= FENSTER]
    if not due:
        print("Nichts fällig.")
        return
    if not (token and page and ig):
        print("Noch kein Meta-Zugang hinterlegt, fällig wäre:", ", ".join(p["id"] for p in due))
        return
    for p in sorted(due, key=lambda p: p["when"]):
        urls = [f"{base}/{i}" for i in p["images"]]
        res = {"when": now.isoformat(timespec="minutes")}
        for name, fn, acc in (("instagram", instagram, ig), ("facebook", facebook, page)):
            try:
                res[name] = fn(acc, token, urls, p["caption"])
            except Exception as e:  # ein Kanal darf den anderen nicht blockieren
                res[name + "_fehler"] = repr(e)[:300]
        posted[p["id"]] = res
        print(p["id"], res)
    POSTED.write_text(json.dumps(posted, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
