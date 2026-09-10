#!/usr/bin/env python3
"""Prüft die veröffentlichte Seite im Browser (Live-Deployment)."""
import pathlib
import re
import subprocess

B = "https://kriminalitaet-sicherheit-de.onrender.com"
T = pathlib.Path("/home/c-vantis/jd/40_projects/47_kriminalitaetsdiskrepanz_de/dashboard/_verify")


def hole(url, name):
    r = subprocess.run(
        ["chromium", "--headless=new", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=25000", "--dump-dom", url],
        capture_output=True, text=True, timeout=180)
    (T / name).write_text(r.stdout, encoding="utf-8")
    return r.stdout


def pruefe(name, dom, erwartet):
    print(f"\n=== {name} ===")
    ok = True
    for beschriftung, (muster, minimum) in erwartet.items():
        n = len(re.findall(muster, dom)) if isinstance(muster, str) else muster(dom)
        status = "OK " if n >= minimum else "FEHLT"
        if n < minimum:
            ok = False
        print(f"  {status} {beschriftung}: {n} (erwartet >= {minimum})")
    # Achtung: Plotly ist in die Seite eingebettet. Dort steht "SyntaxError"
    # als Variablenname im Quelltext. Deshalb nur nach echten Ladefehlern
    # suchen, nicht nach dem bloßen Vorkommen des Wortes.
    echt = re.findall(r"Uncaught (?:TypeError|ReferenceError|RangeError|SyntaxError):",
                      dom)
    if echt:
        print(f"  FEHLT echte JavaScript-Fehler: {len(echt)} ({echt[:2]})")
        ok = False
    else:
        print("  OK  keine JavaScript-Fehler")
    return ok


def main():
    ergebnisse = []

    dom = hole(f"{B}/", "live_index.html")
    ergebnisse.append(pruefe("Startseite", dom, {
        "Seitentitel": (r"<title>Kriminalität und Sicherheit", 1),
        "Links zur App": (r'href="deutschland_app(\w*)\.html"', 2),
        "Links zur Zeitreihe": (r'href="zeitreihen_\w+\.html"', 2),
        "Schrift eingebunden": (r"plex-latin-400\.woff2", 1),
    }))

    dom = hole(f"{B}/deutschland_app.html", "live_app.html")
    ergebnisse.append(pruefe("App, Kartenreiter", dom, {
        "Länderflächen (Karte)": (r'class="bl"', 16),
        "Kartenbeschriftungen": (r'class="kl', 16),
        "Kennzahl-Auswahl": (r'id="kennzahl"', 1),
        "Rangliste": (r'id="ranking"', 1),
        "Kopf ohne Kennzahlkacheln": (lambda d: 0 if "hero-kpis" not in d else 1, 0),
    }))

    for reiter in ["kriminalitaet", "furcht", "justiz", "methodik"]:
        dom = hole(f"{B}/deutschland_app.html#{reiter}", f"live_{reiter}.html")
        ziel = {"kriminalitaet": 4, "furcht": 3, "justiz": 1, "methodik": 0}[reiter]
        ergebnisse.append(pruefe(f"App, Reiter {reiter}", dom, {
            "Diagramm-Container": (r'data-fig="[a-z_]+"', ziel),
            "davon gezeichnet": (r'js-plotly-plot', max(ziel - 1, 0)),
            "Inhalt gerendert": (r'class="card"', 1 if reiter != "methodik" else 0),
        }))

    print("\n" + "=" * 46)
    print("Gesamt:", "alle Prüfungen bestanden" if all(ergebnisse)
          else "mindestens eine Prüfung fehlgeschlagen")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    raise SystemExit(main())
