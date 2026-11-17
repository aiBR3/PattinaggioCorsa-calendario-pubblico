#!/usr/bin/env python3
"""
Calcola quali regolamenti di gara (id_manif) leggere nella raccolta settimanale.

Gli id dei regolamenti di gara su fisr.info crescono con la data di creazione del documento,
non con la data della gara. Ogni settimana si leggono quindi:

  1. un intervallo attorno all'ultimo regolamento che ESISTE: per trovare quelli nuovi;
  2. i regolamenti delle gare future già in dati/eventi.yaml, uno per uno: per accorgersi
     quando un organizzatore li cambia (date, categorie, scadenza), anche se il loro numero
     è ormai lontano dall'intervallo. Senza questa rilettura converti_fisr.py non vedrebbe
     mai un regolamento cambiato.

Una scansione completa (es. 6300-7100) resta possibile a mano con "Run workflow".

L'ultimo regolamento che esiste si ricava da due posti, e vince il più alto:
  - dati/eventi.yaml: gli URL corsa_trofeo_modulo.php?id_manif=N in url_ufficiale e in fonti;
  - registro/*-raccolta-fisr.json: gli id dei regolamenti scaricati e quelli linkati nelle righe.
NON conta l'estremo superiore dell'intervallo scandito: quei numeri sono stati provati, non
trovati (fino al 2026-11-16 contava, e dopo ogni raccolta committata l'intervallo successivo
saltava in avanti di 300 numeri, lasciando un buco: vedi appunti/diario.md).

Uso:
  python3 script/intervallo_scansione.py [--eventi dati/eventi.yaml] [--registro registro] [--margine 300] [--ripresa 50]
      stampa su stdout due interi separati da uno spazio: "DA A", con DA = ultimo esistente - ripresa + 1
      (gli ultimi vengono riletti: molti nascono come bozze vuote e si riempiono dopo) e A = ultimo esistente + margine;
  python3 script/intervallo_scansione.py --da-rileggere [--eventi dati/eventi.yaml] [--dal AAAA-MM-GG]
      stampa su una riga, separati da spazi, gli id dei regolamenti citati dalle voci con data_inizio >= DAL
      (predefinito: oggi; raccolta.yml passa la stessa data minima della raccolta; riga vuota se non ce ne sono). raccogli_fisr.py li riceve con --rileggi-regolamenti e salta da sé
      quelli già dentro l'intervallo.
Esce con errore se non trova nessun id (meglio fermarsi che scandire a caso).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
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


def regolamenti_delle_voci_future(percorso: Path, dal: date) -> list[int]:
    """Gli id dei regolamenti di gara citati (url_ufficiale, fonti) dalle voci con data_inizio >= dal, in ordine.
    Tutti gli stati: anche una gara oggi esclusa può ricevere le categorie Master in un regolamento rivisto."""
    if not percorso.is_file():
        sys.exit(f"file degli eventi non trovato: {percorso}")
    eventi = yaml.safe_load(percorso.read_text(encoding="utf-8"))
    if not isinstance(eventi, list):
        sys.exit(f"{percorso}: atteso un elenco di eventi, trovato {type(eventi).__name__}")
    trovati: set[int] = set()
    for evento in eventi:
        if not isinstance(evento, dict):
            sys.exit(f"{percorso}: una voce non è un dizionario: {evento!r}")
        inizio = evento.get("data_inizio")
        if not isinstance(inizio, date):
            try:
                inizio = date.fromisoformat(str(inizio))
            except ValueError:
                sys.exit(f"{percorso}: data_inizio non valida nella voce {evento.get('id')!r}: {evento.get('data_inizio')!r}")
        if inizio < dal:
            continue
        candidati = [str(evento.get("url_ufficiale") or "")]
        candidati += [str(fonte.get("url") or "") for fonte in (evento.get("fonti") or []) if isinstance(fonte, dict)]
        for url in candidati:
            for numero in ESPRESSIONE_ID_MANIF.findall(url):
                if ID_MINIMO_PLAUSIBILE <= int(numero) <= ID_MASSIMO_PLAUSIBILE:
                    trovati.add(int(numero))
    return sorted(trovati)


def id_dal_registro(cartella: Path) -> set[int]:
    """Gli id dei regolamenti che le raccolte precedenti hanno trovato: quelli scaricati e quelli linkati nelle righe.
    L'estremo superiore dell'intervallo scandito NON conta: è un numero provato, non un regolamento che esiste."""
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
    analizzatore.add_argument("--registro", type=Path, default=Path("registro"), help="cartella dei rapporti di raccolta")
    analizzatore.add_argument("--margine", type=int, default=300, help="quanti id oltre l'ultimo visto scandire")
    analizzatore.add_argument("--ripresa", type=int, default=50, help="quanti degli ultimi id già visti rileggere (bozze riempite dopo)")
    analizzatore.add_argument("--da-rileggere", action="store_true",
                              help="invece dell'intervallo, stampa gli id dei regolamenti delle voci future (da passare a raccogli_fisr.py --rileggi-regolamenti)")
    analizzatore.add_argument("--dal", type=date.fromisoformat, default=None, help="per --da-rileggere: voci con data_inizio da questa data in poi (predefinita: oggi)")
    opzioni = analizzatore.parse_args()

    if opzioni.da_rileggere:
        dal = opzioni.dal or date.today()
        futuri = regolamenti_delle_voci_future(opzioni.eventi, dal)
        print(f"regolamenti delle voci dal {dal} in poi: {len(futuri)}", file=sys.stderr)
        print(" ".join(str(numero) for numero in futuri))
        return

    if opzioni.margine < 1 or opzioni.margine > 5000:
        sys.exit(f"--margine fuori misura: {opzioni.margine} (atteso tra 1 e 5000)")
    if opzioni.ripresa < 0 or opzioni.ripresa > 5000:
        sys.exit(f"--ripresa fuori misura: {opzioni.ripresa} (atteso tra 0 e 5000)")

    visti = {n for n in id_dagli_eventi(opzioni.eventi) | id_dal_registro(opzioni.registro) if ID_MINIMO_PLAUSIBILE <= n <= ID_MASSIMO_PLAUSIBILE}
    if not visti:
        sys.exit("nessun id_manif trovato in eventi.yaml né nel registro: indicare l'intervallo a mano")

    ultimo = max(visti)
    da, a = ultimo - opzioni.ripresa + 1, ultimo + opzioni.margine
    if not (ID_MINIMO_PLAUSIBILE < da < a <= ID_MASSIMO_PLAUSIBILE):
        sys.exit(f"intervallo calcolato non plausibile: {da}-{a}")
    print(f"ultimo regolamento esistente: {ultimo} (da {len(visti)} id distinti)", file=sys.stderr)
    print(f"{da} {a}")


if __name__ == "__main__":
    main()
