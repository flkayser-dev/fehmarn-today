# Fehmarn Today

Termine und Ausflugsziele für Fehmarn und Ostholstein. Prototyp.

- `prototype_scraper/scrape.py` holt Termine von der reporter, fehmarn.de und hochberg-flohmarkt.de und führt sie mit den bekannten zusammen.
- `site/build.py` baut daraus `site/index.html`.
- `.github/workflows/taeglich.yml` macht beides jeden Morgen und veröffentlicht die Seite über GitHub Pages.

Bilder: Wikimedia Commons (Lizenzen im Fußbereich der Seite), Karten © OpenStreetMap-Mitwirkende, Fotos der Anbieter werden von deren Websites eingebunden.
