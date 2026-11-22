#!/usr/bin/env python3
"""
prove_intervallo_scansione.py — prove automatiche di intervallo_scansione.py su dati costruiti.

Non legge la rete e non tocca il repository: scrive un eventi.yaml e un registro finti in una cartella temporanea e controlla ciò che intervallo_scansione.py stampa. Protegge due regole:
  - l'ultimo regolamento "esistente" è l'ultimo trovato davvero, non l'ultimo numero provato (l'errore del 2026-11-16: vedi appunti/diario.md);
  - i regolamenti delle gare future vengono elencati per essere riletti ogni settimana.

Uso:
    python3 script/prove_intervallo_scansione.py

Esce con 0 se tutte le prove passano, con 1 altrimenti.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PERCORSO_SCRIPT = Path(__file__).resolve().parent / "intervallo_scansione.py"
if not PERCORSO_SCRIPT.is_file():
    sys.exit(f"Non trovo {PERCORSO_SCRIPT}: questo file va tenuto accanto a intervallo_scansione.py")

URL_REGOLAMENTO = "https://www.fisr.info/attivita/corsa_trofeo_modulo.php?id_manif="
URL_LISTA = "https://www.fisr.info/attivita/corsa_calendario.php"


def voce_finta(identificativo: str, data: str, numero: int | None, stato: str = "confermato") -> str:
    fonti = f"    - url: {URL_LISTA}\n      letto_il: 2026-11-01\n"
    if numero is not None:
        fonti += f"    - url: {URL_REGOLAMENTO}{numero}\n      letto_il: 2026-11-01\n"
    url = f'"{URL_REGOLAMENTO}{numero}"' if numero is not None else '""'
    return (f"- id: {identificativo}\n  nome: \"Gara di prova\"\n  data_inizio: {data}\n  data_fine: {data}\n  luogo: \"Prova\"\n"
            f"  url_ufficiale: {url}\n  stato: {stato}\n  fonti:\n{fonti}")


def esegui(argomenti: list[str]) -> tuple[int, str, str]:
    esito = subprocess.run([sys.executable, str(PERCORSO_SCRIPT), *argomenti], capture_output=True, text=True, timeout=60)
    return esito.returncode, esito.stdout.strip(), esito.stderr.strip()


esiti: list[bool] = []


def verifica(nome: str, condizione: bool, dettaglio: object = "") -> None:
    esiti.append(bool(condizione))
    print(("ok       " if condizione else "FALLITA  ") + nome + (f" — {dettaglio}" if dettaglio != "" and not condizione else ""))


def principale() -> int:
    with tempfile.TemporaryDirectory() as cartella_testo:
        cartella = Path(cartella_testo)
        eventi = cartella / "eventi.yaml"
        registro = cartella / "registro"
        registro.mkdir()
        eventi.write_text("\n".join([
            voce_finta("2026-06-01-prova-passata", "2026-06-01", 6800),
            voce_finta("2026-12-06-prova-vicina", "2026-12-06", 7047),
            voce_finta("2027-05-28-prova-esclusa", "2027-05-28", 7073, stato="escluso"),
            voce_finta("2027-07-03-prova-senza-regolamento", "2027-07-03", None, stato="da_verificare"),
        ]), encoding="utf-8")
        # Una raccolta committata: ha provato i numeri fino al 7380, ma l'ultimo regolamento trovato è il 7101.
        (registro / "2026-11-16-raccolta-fisr.json").write_text(json.dumps({
            "righe": [],
            "scansione_regolamenti": {"intervallo": [7031, 7380], "scartate": 343},
            "regolamenti_scansione": [{"id_manif": "7073"}, {"id_manif": "7101"}],
        }), encoding="utf-8")
        comuni = ["--eventi", str(eventi), "--registro", str(registro)]

        codice, uscita, errori = esegui(comuni)
        verifica("1. l'intervallo parte dall'ultimo regolamento trovato (7101), non dall'ultimo numero provato (7380)",
                 codice == 0 and uscita == "7052 7401", (codice, uscita, errori))

        codice, uscita, errori = esegui(comuni + ["--da-rileggere", "--dal", "2026-11-16"])
        verifica("2. regolamenti delle gare future, in ordine, compresa la gara esclusa; non quello della gara passata",
                 codice == 0 and uscita == "7047 7073", (codice, uscita, errori))

        codice, uscita, errori = esegui(comuni + ["--da-rileggere", "--dal", "2027-06-01"])
        verifica("3. nessun regolamento da rileggere: riga vuota, nessun errore", codice == 0 and uscita == "", (codice, uscita, errori))

        vuoto = cartella / "vuoto.yaml"
        vuoto.write_text(voce_finta("2027-07-03-prova-senza-regolamento", "2027-07-03", None, stato="da_verificare"), encoding="utf-8")
        registro_vuoto = cartella / "registro_vuoto"
        registro_vuoto.mkdir()
        codice, uscita, errori = esegui(["--eventi", str(vuoto), "--registro", str(registro_vuoto)])
        verifica("4. senza nessun regolamento noto si ferma con un errore, senza stampare un intervallo", codice != 0 and uscita == "", (codice, uscita, errori))

        codice, uscita, errori = esegui(["--eventi", str(cartella / "non_esiste.yaml"), "--registro", str(registro)])
        verifica("5. file degli eventi mancante: errore chiaro", codice != 0 and "non trovato" in errori, (codice, uscita, errori))

    superate = sum(esiti)
    print(f"\n{superate}/{len(esiti)} prove superate")
    if not esiti:
        print("ERRORE: nessuna prova eseguita", file=sys.stderr)
        return 1
    return 0 if superate == len(esiti) else 1


if __name__ == "__main__":
    sys.exit(principale())
