# Fehmarn Today

Termine und Ausflugsziele für Fehmarn und Ostholstein. Prototyp.

- `prototype_scraper/scrape.py` holt Termine von der reporter, fehmarn.de und hochberg-flohmarkt.de und führt sie mit den bekannten zusammen.
- `site/build.py` baut daraus `site/index.html`.
- `.github/workflows/taeglich.yml` holt jeden Morgen neue Termine und speichert sie; Netlify baut danach die Seite neu (netlify.toml).

Bilder: Wikimedia Commons (Lizenzen im Fußbereich der Seite), Karten © OpenStreetMap-Mitwirkende, Fotos der Anbieter werden von deren Websites eingebunden.
