# Deployment

Die App ist eine **statische Website** — eine Handvoll HTML-Dateien ohne Server,
ohne Datenbank, ohne Build auf dem Server. Damit ist jedes Static-Hosting möglich.

## Inhalt des Ordners (das ist alles, was hochgeladen wird)

| Datei | Größe | Inhalt |
|---|---|---|
| `index.html` | 3 KB | Startseite mit Links zu allen Fassungen |
| `deutschland_app.html` | 5,0 MB | Bundesland-App, Plotly eingebettet, offline nutzbar |
| `deutschland_app_cdn.html` | 0,2 MB | gleiche App, Plotly per CDN (klein, braucht Internet) |
| `deutschland_app_static.html` | 0,09 MB | Tabellenfassung ohne JavaScript |
| `zeitreihen_interaktiv.html` | 5,1 MB | Auswertungen 1987–2025 (18 Diagramme) |
| `zeitreihen_static.html` | 0,9 MB | dieselben Auswertungen als Bilder |

Nicht hochladen: `build_*.py`, `data/`, `_verify/`, `README*.md`, `texte.py`,
`deutschland_app_static.html`-Bausteine. Der Upload kann trotzdem den ganzen
Ordner enthalten — schädlich ist nur Ballast, nicht die Funktion.

## Variante A — Netlify Drop (am schnellsten, ohne Konto-Zwang)

1. <https://app.netlify.com/drop> öffnen
2. Den Ordner `dashboard/` in das Feld ziehen
3. Fertig — Netlify gibt sofort eine URL aus (z. B. `https://xyz.netlify.app`)
4. Optional: kostenloses Konto anlegen, um die URL zu behalten und umzubenennen

## Variante B — Cloudflare Pages

1. <https://pages.cloudflare.com> → „Create application" → „Upload assets"
2. Projektname wählen, den Ordner `dashboard/` hochladen
3. Ausgeliefert unter `<projekt>.pages.dev`

## Variante C — GitHub Pages (versioniert, empfohlen für Dauerhaftigkeit)

```bash
cd ~/jd/40_projects/47_kriminalitaetsdiskrepanz_de
git init                       # falls noch kein Repository
git add dashboard/*.html
git commit -m "Kriminalität und Sicherheit in Deutschland: App und Auswertungen"
git remote add origin git@github.com:<benutzer>/<repo>.git
git push -u origin main
```

Danach im Repository unter *Settings → Pages* als Quelle den Branch `main` und
den Ordner `/dashboard` wählen. Die Seite erscheint unter
`https://<benutzer>.github.io/<repo>/`.

**Achtung bei GitHub Pages:** Dateien über 100 MB sind nicht erlaubt (wir liegen
bei 5 MB, unkritisch), und GitHub Pages liefert standardmäßig mit
`Content-Type: text/html` — die eingebetteten Daten laufen also ohne Zutun.

## Variante D — Render (wie das Werteprofil-Projekt)

Als **Static Site** anlegen, nicht als Web Service:

1. Render-Dashboard → „New" → „Static Site"
2. Repository verbinden
3. *Build Command*: leer lassen · *Publish Directory*: `dashboard`
4. Deploy

Ein `render.yaml` für eine Static Site:

```yaml
services:
  - type: web
    name: kriminalitaet-sicherheit-de
    runtime: static
    staticPublishPath: dashboard
    buildCommand: ""
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
```

## Variante E — eigener Server (falls vorhanden)

```bash
cd ~/jd/40_projects/47_kriminalitaetsdiskrepanz_de/dashboard
python3 -m http.server 8080        # nur zum Testen
```
Für Dauerbetrieb hinter nginx: den Ordner als Document Root setzen.
Ein Python-Server ist hier nicht nötig und nicht zu empfehlen — die Dateien
sind statisch.

## Vor dem Upload prüfen

```bash
cd ~/jd/40_projects/47_kriminalitaetsdiskrepanz_de/dashboard
python3 -c "import pathlib,re,sys
for f in ['index.html','deutschland_app.html','deutschland_app_static.html',
          'zeitreihen_interaktiv.html','zeitreihen_static.html']:
    h = pathlib.Path(f).read_text(encoding='utf-8')
    fehlend = [l for l in re.findall(r'href=\"([^\"]+)\"', h)
               if not l.startswith(('http','#','data:')) and not pathlib.Path(l).exists()]
    print(('OK   ' if not fehlend else 'FEHLT'), f, fehlend)"
```

## Was im Betrieb zu beachten ist

- **Kein Tracking, keine Cookies, keine externen Aufrufe** — außer in
  `deutschland_app_cdn.html` und `zeitreihen_cdn.html`, die Plotly vom
  CDN-Netz `cdn.plot.ly` laden. Wenn du volle Unabhängigkeit willst, nur die
  eingebetteten Fassungen ausliefern.
- **Ladezeit:** 5 MB für die eingebettete Fassung sind für Mobilfunk viel. Für
  die Startseite ist deshalb die CDN-Fassung (0,2 MB) verlinkt; sie kommt mit
  Plotly vom CDN deutlich schneller.
- **Sprache:** Alles auf Deutsch, `lang="de"` gesetzt.
- **Barrierefreiheit:** Karte mit `role="button"`, `tabindex` und
  Tastatursteuerung (Enter); Tabellen mit Kopfzeilen.
