#!/usr/bin/env python3
"""
35_js_pruefen.py — Das eingebettete JavaScript auf Syntaxfehler prüfen
======================================================================
Ein Syntaxfehler im Seitenskript führt dazu, dass der Browser den *ganzen*
Block verwirft — die Seite sieht dann teilweise in Ordnung aus, weil nur der
Teil läuft, der aus einem anderen Block stammt. Dieses Werkzeug zieht die
Skriptblöcke aus index.html und prüft sie einzeln mit node.

Ausgabe: Exit-Code 1, wenn ein Block nicht übersetzt werden kann.
"""
import pathlib
import re
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUELLE = ROOT / "dashboard" / "index.html"


def main():
    html = QUELLE.read_text(encoding="utf-8")
    bloecke = re.findall(r"<script(?![^>]*type=\"application/json\")[^>]*>(.*?)</script>",
                         html, re.S)
    print(f"{len(bloecke)} Skriptblock/‑blöcke gefunden")
    fehler = 0
    for i, code in enumerate(bloecke):
        if len(code.strip()) < 20:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(code)
            pfad = fh.name
        r = subprocess.run(["node", "--check", pfad], capture_output=True, text=True)
        groesse = len(code) / 1024
        if r.returncode == 0:
            print(f"  Block {i+1}: {groesse:8.1f} KB — Syntax in Ordnung")
        else:
            fehler += 1
            print(f"  Block {i+1}: {groesse:8.1f} KB — SYNTAXFEHLER")
            for z in (r.stderr or "").splitlines()[:6]:
                print(f"      {z}")
        pathlib.Path(pfad).unlink(missing_ok=True)
    print("\nErgebnis:", "alle Blöcke übersetzbar" if not fehler else f"{fehler} fehlerhaft")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
