#!/usr/bin/env python3
"""
38_app_pruefen.py — Die englische Fassung im Browser prüfen
===========================================================
Lädt index-en.html in einem echten Chromium, wartet auf das Rendern und
prüft, was der Nutzer tatsächlich sieht:
  - Wird die Karte gezeichnet (Flächen, Beschriftungen)?
  - Werden die Diagramme gezeichnet (Plotly-Container mit Inhalt)?
  - Lassen sich die Reiter umschalten und erscheint dann Inhalt?
  - Gibt es JavaScript-Fehler?

Die Ausgabe ist bewusst ausführlich: Bei einem Sprachwechsel können Fehler
auftreten, die in einer reinen Textprüfung unsichtbar bleiben.

Aufruf:  python3 scripts/38_app_pruefen.py [deutsch|englisch]
"""
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARBEIT = ROOT / "dashboard" / "_verify"

PRUEFSKRIPT = r"""
<script>
(function(){
  window.__befund = {fehler: [], schritte: []};
  window.addEventListener('error', e => window.__befund.fehler.push(e.message));
  window.addEventListener('unhandledrejection',
    e => window.__befund.fehler.push('Promise: ' + e.reason));

  function zaehle(sel){ return document.querySelectorAll(sel).length; }
  function melde(name, wert){ window.__befund.schritte.push(name + '=' + wert); }

  setTimeout(function(){
    melde('kartenflaechen', zaehle('path.bl, path[class*="bl"]'));
    melde('kartenlabels', zaehle('text.kl, g.lbl text'));
    melde('wappen', zaehle('svg.wappen'));
    melde('diagramme', zaehle('.js-plotly-plot'));
    melde('plotly_gezeichnet', zaehle('.js-plotly-plot .plot-container'));
    melde('rank_zeilen', zaehle('.rank-zeile'));
    melde('tabs', zaehle('.tab'));
    melde('tab_aktiv', (document.querySelector('.tab.active')||{}).textContent || '-');
    melde('inhalt_laenge', (document.getElementById('inhalt')||{innerHTML:''}).innerHTML.length);
    // Ersten Reiter anklicken und prüfen, ob Inhalt erscheint
    const tabs = document.querySelectorAll('.tab');
    if (tabs.length > 3) {
      tabs[3].click();
      setTimeout(function(){
        melde('nach_klick_aktiv', (document.querySelector('.tab.active')||{}).textContent || '-');
        melde('nach_klick_diagramme', zaehle('.js-plotly-plot'));
        melde('nach_klick_inhalt', (document.getElementById('inhalt')||{innerHTML:''}).innerHTML.length);
        const el = document.createElement('div');
        el.id = '__befund';
        el.textContent = JSON.stringify(window.__befund);
        document.body.appendChild(el);
      }, 2500);
    } else {
      const el = document.createElement('div');
      el.id = '__befund';
      el.textContent = JSON.stringify(window.__befund);
      document.body.appendChild(el);
    }
  }, 6000);
})();
</script>
</body>
"""


def main():
    fassung = (sys.argv[1] if len(sys.argv) > 1 else "englisch").lower()
    quelle = "index-en.html" if fassung.startswith("e") else "index.html"
    pfad = ROOT / "dashboard" / quelle
    html = pfad.read_text(encoding="utf-8")
    html = html.replace("</body>", PRUEFSKRIPT, 1)
    ARBEIT.mkdir(exist_ok=True)
    test = ARBEIT / f"_test_{fassung}.html"
    test.write_text(html, encoding="utf-8")

    r = subprocess.run(["chromium", "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--virtual-time-budget=30000", "--window-size=1440,1200",
                        "--dump-dom", f"file://{test}"],
                       capture_output=True, text=True, timeout=300)
    dom = r.stdout
    treffer = None
    import re
    m = re.search(r'<div id="__befund">(.*?)</div>', dom, re.S)
    if m:
        treffer = json.loads(m.group(1).strip())

    print(f"Prüfung der Fassung: {quelle}\n" + "=" * 46)
    if not treffer:
        print("  Kein Befund erhalten — das Prüfskript lief nicht durch.")
        print("  Das deutet auf einen Fehler vor dem Rendern hin.")
        fehler = re.findall(r"Uncaught \w+Error[^\"<]{0,90}", dom)
        for f in fehler[:5]:
            print("   ", f)
        return 1
    for s in treffer["schritte"]:
        print(f"  {s}")
    if treffer["fehler"]:
        print("\n  JavaScript-Fehler:")
        for f in treffer["fehler"][:8]:
            print(f"    {f[:130]}")
    else:
        print("\n  keine JavaScript-Fehler")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
