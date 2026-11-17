#!/usr/bin/env python3
"""
prove_genera_ics.py — prove automatiche dei link che genera_ics.py scrive per ogni evento, su voci costruite.

Non legge la rete e non tocca il repository: costruisce voci finte, le fa passare dalla validazione di
genera_ics.py e controlla i link; l'ultima prova scrive un eventi.yaml in una cartella temporanea, esegue
lo script per intero e rilegge il file .ics prodotto. Protegge la decisione del 2026-11-17:
  - nella descrizione, in fondo, [URL] è la pagina dell'organizzatore e [Regolamento FISR] è il regolamento
    di gara (preso da url_ufficiale o dalle fonti), ciascuno solo se c'è, in quest'ordine;
  - una voce che ha solo il regolamento mostra solo [Regolamento FISR];
  - la proprietà URL dell'evento resta un solo link, quello principale.

Uso:
    python3 script/prove_genera_ics.py

Esce con 0 se tutte le prove passano, con 1 altrimenti.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

CARTELLA_SCRIPT = Path(__file__).resolve().parent
PERCORSO_SCRIPT = CARTELLA_SCRIPT / "genera_ics.py"
if not PERCORSO_SCRIPT.is_file():
    sys.exit(f"Non trovo {PERCORSO_SCRIPT}: questo file va tenuto accanto a genera_ics.py")
sys.path.insert(0, str(CARTELLA_SCRIPT))

import genera_ics  # noqa: E402 — va importato dopo aver aggiunto la cartella degli script al percorso
from icalendar import Calendar  # noqa: E402 — genera_ics ha già controllato che la dipendenza ci sia

REGOLAMENTO = "https://www.fisr.info/attivita/corsa_trofeo_modulo.php?id_manif=7047"
ALTRO_REGOLAMENTO = "https://www.fisr.info/attivita/corsa_trofeo_modulo.php?id_manif=7073"
LISTA = "https://www.fisr.info/attivita/corsa_calendario.php"
ORGANIZZATORE = "https://club-di-prova.example/gara-2027"
ISCRIZIONE = "https://club-di-prova.example/iscrizioni"

VALORI_BASE = {
    "id": "2027-05-28-prova-gara-di-prova",
    "nome": "Gara di prova",
    "data_inizio": "2027-05-28",
    "data_fine": "2027-05-29",
    "luogo": "Prova (PR)",
    "paese": "IT",
    "tipo": "gara",
    "categorie": ["master"],
    "distanze": ["5000 m"],
    "organizzatore": "Club di prova",
    "url_ufficiale": "",
    "url_iscrizione": "",
    "scadenza_iscrizione": "",
    "stato": "confermato",
    "fonti": [{"url": LISTA, "letto_il": "2026-11-17"}],
    "verificato_il": "2026-11-17",
    "prova": "Art. 10: MASTER OVER 30",
    "note": "Ritrovo alle 8.",
    "note_interne": "",
}


def voce_grezza(**modifiche) -> dict:
    """Una voce completa secondo lo schema di genera_ics.py: le chiavi che lo schema dovesse
    aggiungere in futuro e che qui non hanno un valore vengono scritte vuote."""
    voce = {chiave: VALORI_BASE.get(chiave, "") for chiave in genera_ics.CHIAVI_EVENTO}
    sconosciute = set(modifiche) - set(voce)
    if sconosciute:
        raise ValueError(f"campi non previsti dallo schema: {sorted(sconosciute)}")
    voce.update(modifiche)
    return voce


def fonti(*indirizzi: str) -> list[dict]:
    return [{"url": indirizzo, "letto_il": "2026-11-17"} for indirizzo in indirizzi]


def evento_valido(**modifiche) -> tuple[genera_ics.Evento, genera_ics.Esito]:
    esito = genera_ics.Esito()
    evento = genera_ics.converti_evento(voce_grezza(**modifiche), 1, esito)
    if evento is None:
        raise AssertionError(f"la voce di prova non supera la validazione: {esito.errori}")
    return evento, esito


def righe_link(**modifiche) -> list[tuple[str, str]]:
    evento, _ = evento_valido(**modifiche)
    return genera_ics.collegamenti_descrizione(evento)


def uguale(ottenuto, atteso, cosa: str) -> None:
    if ottenuto != atteso:
        raise AssertionError(f"{cosa}: ottenuto {ottenuto!r}, atteso {atteso!r}")


# ---------------------------------------------------------------------------
# Prove
# ---------------------------------------------------------------------------

def prova_riconosce_il_regolamento() -> None:
    casi = {
        REGOLAMENTO: "7047",
        "http://fisr.info/attivita/corsa_trofeo_modulo.php?id_manif=12": "12",
        "https://www.fisr.info/attivita/corsa_trofeo_modulo.php?anno=2026&id_manif=7047": "7047",
        "https://www.fisr.info/attivita/corsa_trofeo_modulo.php?id_manif=7047&stampa=1": "7047",
        "https://www.fisr.info/attivita/corsa_trofeo_modulo.php?id_manif=": "",
        "https://www.fisr.info/attivita/corsa_trofeo_modulo.php?id_manif=abc": "",
        LISTA: "",
        "https://club-di-prova.example/corsa_trofeo_modulo.php?id_manif=7047": "",
        ORGANIZZATORE: "",
        "": "",
    }
    for indirizzo, atteso in casi.items():
        uguale(genera_ics.numero_regolamento(indirizzo), atteso, f"numero_regolamento({indirizzo!r})")


def prova_solo_regolamento() -> None:
    righe = righe_link(url_ufficiale=REGOLAMENTO, fonti=fonti(LISTA, REGOLAMENTO))
    uguale(righe, [("Regolamento FISR", REGOLAMENTO)], "voce con il solo regolamento")
    evento, _ = evento_valido(url_ufficiale=REGOLAMENTO, fonti=fonti(LISTA, REGOLAMENTO))
    uguale(genera_ics.collegamento_evento(evento), REGOLAMENTO, "link principale della voce con il solo regolamento")


def prova_organizzatore_e_regolamento() -> None:
    righe = righe_link(url_ufficiale=ORGANIZZATORE, fonti=fonti(LISTA, REGOLAMENTO, ORGANIZZATORE))
    uguale(righe, [("URL", ORGANIZZATORE), ("Regolamento FISR", REGOLAMENTO)], "voce con organizzatore e regolamento")
    evento, _ = evento_valido(url_ufficiale=ORGANIZZATORE, fonti=fonti(LISTA, REGOLAMENTO, ORGANIZZATORE))
    uguale(genera_ics.collegamento_evento(evento), ORGANIZZATORE, "link principale con organizzatore e regolamento")


def prova_solo_organizzatore() -> None:
    righe = righe_link(url_ufficiale=ORGANIZZATORE, fonti=fonti(ORGANIZZATORE))
    uguale(righe, [("URL", ORGANIZZATORE)], "voce con la sola pagina dell'organizzatore")


def prova_nessun_link() -> None:
    righe = righe_link(fonti=fonti(LISTA))
    uguale(righe, [], "voce senza link (la lista federale non è un regolamento)")
    evento, _ = evento_valido(fonti=fonti(LISTA))
    descrizione = genera_ics.descrizione_evento(evento)
    if "[URL]" in descrizione or "[Regolamento FISR]" in descrizione:
        raise AssertionError(f"una voce senza link non deve avere righe di link: {descrizione!r}")


def prova_iscrizione_al_posto_del_link_ufficiale() -> None:
    righe = righe_link(url_iscrizione=ISCRIZIONE, fonti=fonti(LISTA, REGOLAMENTO))
    uguale(righe, [("URL", ISCRIZIONE), ("Regolamento FISR", REGOLAMENTO)], "voce senza url_ufficiale, con iscrizione e regolamento")


def prova_regolamento_ufficiale_con_iscrizione() -> None:
    # Come prima della decisione: se url_ufficiale c'è, url_iscrizione non compare.
    righe = righe_link(url_ufficiale=REGOLAMENTO, url_iscrizione=ISCRIZIONE, fonti=fonti(LISTA, REGOLAMENTO))
    uguale(righe, [("Regolamento FISR", REGOLAMENTO)], "voce con regolamento in url_ufficiale e una pagina d'iscrizione")


def prova_due_regolamenti_diversi() -> None:
    evento, esito = evento_valido(url_ufficiale=ORGANIZZATORE, fonti=fonti(REGOLAMENTO, ALTRO_REGOLAMENTO))
    uguale(genera_ics.collegamenti_descrizione(evento), [("URL", ORGANIZZATORE), ("Regolamento FISR", REGOLAMENTO)],
           "voce con due regolamenti: vale il primo")
    if not any("regolamenti di gara diversi" in avviso for avviso in esito.avvisi):
        raise AssertionError(f"manca l'avviso sui due regolamenti: {esito.avvisi}")
    _, esito_uno = evento_valido(url_ufficiale=REGOLAMENTO, fonti=fonti(LISTA, REGOLAMENTO))
    if esito_uno.avvisi:
        raise AssertionError(f"lo stesso regolamento in url_ufficiale e nelle fonti non deve dare avvisi: {esito_uno.avvisi}")


def prova_indirizzo_che_somiglia_a_un_regolamento() -> None:
    strano = "https://www.fisr.info/attivita/corsa_trofeo_modulo.php?id_manif="
    evento, esito = evento_valido(url_ufficiale=strano, fonti=fonti(LISTA))
    uguale(genera_ics.collegamenti_descrizione(evento), [("URL", strano)], "indirizzo non riconosciuto come regolamento")
    if not any("somiglia a un regolamento" in avviso for avviso in esito.avvisi):
        raise AssertionError(f"manca l'avviso sull'indirizzo non riconosciuto: {esito.avvisi}")


def prova_i_link_chiudono_la_descrizione() -> None:
    evento, _ = evento_valido(url_ufficiale=ORGANIZZATORE, fonti=fonti(LISTA, REGOLAMENTO))
    righe = genera_ics.descrizione_evento(evento).split("\n")
    uguale(righe[-2:], [f"[URL] {ORGANIZZATORE}", f"[Regolamento FISR] {REGOLAMENTO}"], "ultime due righe della descrizione")
    uguale(righe[-3], "[Informazioni] Ritrovo alle 8.", "riga prima dei link")
    uguale(righe[0], "[Categorie ammesse] Master", "prima riga della descrizione")


def testo_yaml(voce: dict) -> str:
    righe = []
    for indice, (chiave, valore) in enumerate(voce.items()):
        inizio = "- " if indice == 0 else "  "
        if chiave == "fonti":
            righe.append(f"{inizio}fonti:")
            for fonte in valore:
                righe.append(f"    - url: \"{fonte['url']}\"")
                righe.append(f"      letto_il: {fonte['letto_il']}")
        elif isinstance(valore, list):
            righe.append(f"{inizio}{chiave}: [" + ", ".join(f'"{elemento}"' for elemento in valore) + "]")
        elif chiave in {"data_inizio", "data_fine", "scadenza_iscrizione", "verificato_il"} and valore:
            righe.append(f"{inizio}{chiave}: {valore}")
        else:
            righe.append(f"{inizio}{chiave}: \"{valore}\"")
    return "\n".join(righe) + "\n"


def prova_file_ics_per_intero() -> None:
    voci = [
        voce_grezza(id="2027-05-28-prova-con-due-link", nome="Gara con due link", url_ufficiale=ORGANIZZATORE,
                    fonti=fonti(LISTA, REGOLAMENTO, ORGANIZZATORE)),
        voce_grezza(id="2027-05-28-prova-con-il-solo-regolamento", nome="Gara con il solo regolamento", url_ufficiale=ALTRO_REGOLAMENTO,
                    fonti=fonti(LISTA, ALTRO_REGOLAMENTO)),
        voce_grezza(id="2027-05-28-prova-esclusa", nome="Gara esclusa", stato="escluso", categorie=[], url_ufficiale=REGOLAMENTO,
                    fonti=fonti(LISTA, REGOLAMENTO)),
    ]
    with tempfile.TemporaryDirectory() as cartella:
        ingresso = Path(cartella) / "eventi.yaml"
        uscita = Path(cartella) / "uscita"
        ingresso.write_text("".join(testo_yaml(voce) for voce in voci), encoding="utf-8")
        esecuzione = subprocess.run([sys.executable, str(PERCORSO_SCRIPT), "--ingresso", str(ingresso), "--uscita", str(uscita),
                                     "--url-base", "https://prova.example/calendario"], capture_output=True, text=True, timeout=120)
        if esecuzione.returncode != 0:
            raise AssertionError(f"genera_ics.py è uscito con {esecuzione.returncode}:\n{esecuzione.stdout}\n{esecuzione.stderr}")
        calendario = Calendar.from_ical((uscita / "calendario.ics").read_bytes())
        eventi = {str(componente.get("summary")): componente for componente in calendario.walk("VEVENT")}
        pagina = (uscita / "index.html").read_text(encoding="utf-8")
    uguale(sorted(eventi), ["Gara con due link", "Gara con il solo regolamento"], "eventi pubblicati nel file .ics")

    due_link = eventi["Gara con due link"]
    uguale(str(due_link.get("description")).split("\n")[-2:], [f"[URL] {ORGANIZZATORE}", f"[Regolamento FISR] {REGOLAMENTO}"],
           "ultime righe della descrizione riletta dal file (due link)")
    uguale(str(due_link.get("url")), ORGANIZZATORE, "proprietà URL riletta dal file (due link)")

    solo_regolamento = eventi["Gara con il solo regolamento"]
    uguale(str(solo_regolamento.get("description")).split("\n")[-1], f"[Regolamento FISR] {ALTRO_REGOLAMENTO}",
           "ultima riga della descrizione riletta dal file (solo regolamento)")
    if "[URL]" in str(solo_regolamento.get("description")):
        raise AssertionError("la voce con il solo regolamento non deve avere la riga [URL]")
    uguale(str(solo_regolamento.get("url")), ALTRO_REGOLAMENTO, "proprietà URL riletta dal file (solo regolamento)")

    if f'<a href="{ORGANIZZATORE}">Gara con due link</a>' not in pagina:
        raise AssertionError("nella pagina il nome dell'evento con due link deve puntare alla pagina dell'organizzatore")


PROVE = [
    prova_riconosce_il_regolamento,
    prova_solo_regolamento,
    prova_organizzatore_e_regolamento,
    prova_solo_organizzatore,
    prova_nessun_link,
    prova_iscrizione_al_posto_del_link_ufficiale,
    prova_regolamento_ufficiale_con_iscrizione,
    prova_due_regolamenti_diversi,
    prova_indirizzo_che_somiglia_a_un_regolamento,
    prova_i_link_chiudono_la_descrizione,
    prova_file_ics_per_intero,
]


def principale() -> int:
    fallite = 0
    for prova in PROVE:
        try:
            prova()
        except AssertionError as errore:
            fallite += 1
            print(f"FALLITA  {prova.__name__}: {errore}")
        except Exception as errore:  # noqa: BLE001 — un errore imprevisto è una prova fallita, non un'interruzione
            fallite += 1
            print(f"ERRORE   {prova.__name__}: {type(errore).__name__}: {errore}")
        else:
            print(f"ok       {prova.__name__}")
    print(f"{len(PROVE) - fallite}/{len(PROVE)} prove superate")
    return 1 if fallite else 0


if __name__ == "__main__":
    sys.exit(principale())
