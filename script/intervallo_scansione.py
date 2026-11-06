#!/usr/bin/env python3
"""
Calcola l'intervallo di id_manif da scandire nella raccolta settimanale.

Gli id dei regolamenti di gara su fisr.info crescono con la data di creazione del documento,
non con la data della gara. Ogni settimana basta quindi scandire gli id oltre l'ultimo già
visto: i regolamenti delle gare future arrivano comunque dal link "modulo" nella lista, che
raccogli_fisr.py segue con --regolamenti. Una scansione completa (es. 6300-7100) resta
possibile a mano con "Run workflow" indicando gli estremi.

L'ultimo id visto si ricava da due posti, e vince il più alto:
  - dati/eventi.yaml: gli URL corsa_trofeo_modulo.php?id_manif=N in url_ufficiale e in fonti;
  - log/*-raccolta-fisr.json: l'estremo superiore dell'intervallo scandito
    (scansione_regolamenti.intervallo) e gli id dei regolamenti scaricati.

Uso:
  python3 script/intervallo_scansione.py [--eventi dati/eventi.yaml] [--log log] [--margine 300] [--ripresa 50]
Stampa su stdout due interi separati da uno spazio: "DA A", con DA = ultimo visto - ripresa + 1
(gli ultimi id già scanditi vengono riletti: molti nascono come bozze vuote e si riempiono dopo)
e A = ultimo visto + margine.
Esce con errore se non trova nessun id (meglio fermarsi che scandire a caso).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError as errore:  # pragma: no cover
    sys.exit(f"Manca una dipendenza ({errore}). Installa: pip install -r script/requisiti.txt")

ESPRESSIONE_ID_MANIF = re.compile(r"id_manif=(\d+)")
ID_MINIMO_PLAUSIBILE = 1000      # sotto non esistono regolamenti utili
ID_MASSIMO_PLAUSIBILE = 100000   # sopra è quasi certamente un errore di lettura


def id_dagli_eventi(percorso: Path) -> set[int]:
    """Tutti gli id_manif citati in eventi.yaml (url_ufficiale, url_iscrizione, fonti)."""
    if not percorso.is_file():
        sys.exit(f"file degli eventi non trovato: {percorso}")
    testo = percorso.read_text(encoding="utf-8")
    eventi = yaml.safe_load(testo)
    if not isinstance(eventi, list):
        sys.exit(f"{percorso}: atteso un elenco di eventi, trovato {type(eventi).__name__}")
    trovati: set[int] = set()
    for evento in eventi:
        if not isinstance(evento, dict):
            sys.exit(f"{percorso}: una voce non è un dizionario: {evento!r}")
        candidati = [str(evento.get("url_ufficiale") or ""), str(evento.get("url_iscrizione") or "")]
        candidati += [str(fonte.get("url") or "") for fonte in (evento.get("fonti") or []) if isinstance(fonte, dict)]
        for url in candidati:
            for numero in ESPRESSIONE_ID_MANIF.findall(url):
                trovati.add(int(numero))
    return trovati


def id_dai_log(cartella: Path) -> set[int]:
    """Gli id visti nelle raccolte precedenti: estremo superiore dell'intervallo e regolamenti scaricati."""
    trovati: set[int] = set()
    if not cartella.is_dir():
        return trovati
    for percorso in sorted(cartella.glob("*-raccolta-fisr.json")):
        try:
            dati = json.loads(percorso.read_text(encoding="utf-8"))
        except (OSError, ValueError) as errore:
            print(f"avviso: {percorso} non leggibile ({errore}), ignorato", file=sys.stderr)
            continue
        if not isinstance(dati, dict):
            print(f"avviso: {percorso} non è un oggetto JSON, ignorato", file=sys.stderr)
            continue
        scansione = dati.get("scansione_regolamenti") or {}
        intervallo = scansione.get("intervallo") if isinstance(scansione, dict) else None
        if isinstance(intervallo, list) and len(intervallo) == 2 and all(isinstance(n, int) for n in intervallo):
            trovati.add(intervallo[1])
        for regolamento in dati.get("regolamenti_scansione") or []:
            if isinstance(regolamento, dict) and str(regolamento.get("id_manif", "")).isdigit():
                trovati.add(int(regolamento["id_manif"]))
        for riga in dati.get("righe") or []:
            if isinstance(riga, dict):
                for numero in ESPRESSIONE_ID_MANIF.findall(json.dumps(riga)):
                    trovati.add(int(numero))
    return trovati


def main() -> None:
    analizzatore = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    analizzatore.add_argument("--eventi", type=Path, default=Path("dati/eventi.yaml"))
    analizzatore.add_argument("--log", type=Path, default=Path("log"), help="cartella dei rapporti di raccolta")
    analizzatore.add_argument("--margine", type=int, default=300, help="quanti id oltre l'ultimo visto scandire")
    analizzatore.add_argument("--ripresa", type=int, default=50, help="quanti degli ultimi id già visti rileggere (bozze riempite dopo)")
    opzioni = analizzatore.parse_args()

    if opzioni.margine < 1 or opzioni.margine > 5000:
        sys.exit(f"--margine fuori misura: {opzioni.margine} (atteso tra 1 e 5000)")
    if opzioni.ripresa < 0 or opzioni.ripresa > 5000:
        sys.exit(f"--ripresa fuori misura: {opzioni.ripresa} (atteso tra 0 e 5000)")

    visti = {n for n in id_dagli_eventi(opzioni.eventi) | id_dai_log(opzioni.log) if ID_MINIMO_PLAUSIBILE <= n <= ID_MASSIMO_PLAUSIBILE}
    if not visti:
        sys.exit("nessun id_manif trovato in eventi.yaml né nei log: indicare l'intervallo a mano")

    ultimo = max(visti)
    da, a = ultimo - opzioni.ripresa + 1, ultimo + opzioni.margine
    if not (ID_MINIMO_PLAUSIBILE < da < a <= ID_MASSIMO_PLAUSIBILE):
        sys.exit(f"intervallo calcolato non plausibile: {da}-{a}")
    print(f"ultimo id visto: {ultimo} (da {len(visti)} id distinti)", file=sys.stderr)
    print(f"{da} {a}")


if __name__ == "__main__":
    main()
