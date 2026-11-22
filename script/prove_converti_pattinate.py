#!/usr/bin/env python3
"""
prove_converti_pattinate.py — prove automatiche di converti_pattinate.py su calendari costruiti.

Non legge la rete e non tocca dati/eventi.yaml: scrive in una cartella temporanea un eventi.yaml con una
gara finta e dei file ICS finti, esegue lo script per intero (come fa raccolta.yml) e rilegge ciò che ha
scritto. Protegge le decisioni del 2026-11-22 sulle pattinate (appunti/decisioni.md):
  - una pattinata nuova entra con le date, il titolo senza la sigla e senza l'ultima parte, `da_verificare`;
  - l'ultima parte del titolo (gruppo e persone) e la descrizione non finiscono in nessun file;
  - la voce si riconosce dall'identificativo dell'evento scritto nelle `fonti`; date, titolo e annullamento
    la seguono; ciò che una persona ha scritto (luogo, paese, organizzatore, stato) resta;
  - una voce `escluso` non viene toccata; una voce sparita dalla fonte viene solo segnalata;
  - una lettura in cui sparisce gran parte delle voci non scrive nulla.
I nomi di gruppi e persone usati qui sono inventati.

Uso:
    python3 script/prove_converti_pattinate.py

Esce con 0 se tutte le prove passano, con 1 altrimenti (dopo averle elencate tutte).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

CARTELLA_SCRIPT = Path(__file__).resolve().parent
PERCORSO_SCRIPT = CARTELLA_SCRIPT / "converti_pattinate.py"
if not PERCORSO_SCRIPT.is_file():
    sys.exit(f"Non trovo {PERCORSO_SCRIPT}: questo file va tenuto accanto a converti_pattinate.py")
sys.path.insert(0, str(CARTELLA_SCRIPT))

import yaml  # noqa: E402
import converti_pattinate as pattinate  # noqa: E402 — va importato dopo aver aggiunto la cartella degli script al percorso

OGGI = "2026-11-22"
PERSONA = "Tizio Caio"                       # nome inventato: non deve mai comparire in ciò che lo script scrive
DESCRIZIONE = "RITROVO-SEGRETO 3330000000"   # idem per la descrizione dell'evento
TRACCIA = "Arricchimento 2026-11-17: sito non trovato; ricerche: nessuna; pagine: nessuna."

GARA_FINTA = """# Intestazione di prova.

- id: 2027-03-29-prova-gara-di-prova
  nome: "Gara di Prova"
  nome_fonte: "GARA DI PROVA"
  data_inizio: 2027-03-29
  data_fine: 2027-03-29
  luogo: "Prova (PR)"
  paese: IT
  tipo: gara
  categorie: []
  distanze: []
  organizzatore: ""
  url_ufficiale: ""
  url_iscrizione: ""
  scadenza_iscrizione: ""
  stato: da_verificare
  fonti:
    - url: https://www.fisr.info/attivita/corsa_calendario.php
      letto_il: 2026-11-16
  verificato_il: ""
  prova: ""
  note: ""
  note_interne: ""
"""


def evento_ics(uid: str, titolo: str, dal: str, al_escluso: str, altre_righe: tuple[str, ...] = ()) -> list[str]:
    """Un evento di una o più giornate intere, come li scrive Google Calendar (la fine è esclusa)."""
    return ["BEGIN:VEVENT", f"UID:{uid}", "DTSTAMP:20261101T000000Z", f"DTSTART;VALUE=DATE:{dal.replace('-', '')}",
            f"DTEND;VALUE=DATE:{al_escluso.replace('-', '')}", f"SUMMARY:{titolo}", f"DESCRIPTION:{DESCRIZIONE}",
            "STATUS:CONFIRMED", *altre_righe, "END:VEVENT"]


def calendario_ics(*eventi: list[str]) -> bytes:
    righe = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//prova//IT"]
    for evento in eventi:
        righe.extend(evento)
    righe.append("END:VCALENDAR")
    return ("\r\n".join(righe) + "\r\n").encode("utf-8")


VALLE = evento_ics("valle@google.com", f"PPUG - Val di Prova TN - Gruppo Finto e {PERSONA}", "2027-05-16", "2027-05-17")
MARE = evento_ics("mare@google.com", "PPUG -  Pasquetta al Mare - Gruppo Finto", "2027-03-29", "2027-03-30")
TRE_GIORNI = evento_ics("roma@google.com", "PPUG - Pattinata di Provopoli - Gruppo Finto", "2027-04-16", "2027-04-19")
ESTERO = evento_ics("estero@google.com", f"PPUG - Lontanopoli - Gruppo Finto ({PERSONA})", "2027-07-17", "2027-07-19")
BASE = (VALLE, MARE, TRE_GIORNI, ESTERO)


class Banco:
    """Una cartella temporanea con eventi.yaml e i file ICS; esegue lo script e rilegge."""

    def __init__(self, cartella: Path):
        self.cartella = cartella
        self.eventi = cartella / "eventi.yaml"
        self.eventi.write_text(GARA_FINTA, encoding="utf-8")
        self.rapporto = cartella / "rapporto.md"

    def esegui(self, *eventi_ics: list[str], oggi: str = OGGI, scrivi: bool = True) -> int:
        ics = self.cartella / "calendario.ics"
        ics.write_bytes(calendario_ics(*eventi_ics))
        argomenti = ["--eventi", str(self.eventi), "--ics", str(ics), "--oggi", oggi, "--rapporto", str(self.rapporto)]
        if scrivi:
            argomenti.append("--scrivi")
        return pattinate.principale(argomenti)

    def voci(self) -> list[dict]:
        return yaml.safe_load(self.eventi.read_text(encoding="utf-8"))

    def voce(self, uid: str) -> dict | None:
        trovate = [voce for voce in self.voci() if uid in pattinate.uid_della_voce(voce)]
        return trovate[0] if len(trovate) == 1 else None

    def correggi(self, uid: str, **modifiche) -> None:
        """Una correzione a mano di una voce, come la farebbe chi la rivede: cambia solo i campi indicati."""
        voce = self.voce(uid)
        if voce is None:
            raise ValueError(f"nessuna voce (o più di una) con l'identificativo {uid!r}")
        sconosciuti = set(modifiche) - set(voce)
        if sconosciuti:
            raise ValueError(f"campi non previsti: {sorted(sconosciuti)}")
        blocco_prima = pattinate.converti_fisr.emetti_evento(voce)
        testo = self.eventi.read_text(encoding="utf-8")
        if testo.count(blocco_prima) != 1:
            raise ValueError(f"la voce {voce['id']} non è scritta nel file nella forma attesa")
        voce.update(modifiche)
        self.eventi.write_text(testo.replace(blocco_prima, pattinate.converti_fisr.emetti_evento(voce)), encoding="utf-8")

    def testo(self) -> str:
        return self.eventi.read_text(encoding="utf-8") + self.rapporto.read_text(encoding="utf-8")


def principale() -> int:
    esiti: list[bool] = []

    def verifica(nome: str, condizione: bool, dettaglio: object = "") -> None:
        esiti.append(bool(condizione))
        print(("ok      " if condizione else "FALLITA ") + nome + ("" if condizione else f"  →  {dettaglio!r}"))

    # --- Titoli -----------------------------------------------------------------------------------------------
    casi = [
        (f"PPUG - Val di Prova TN - Gruppo Finto e {PERSONA}", ("Val di Prova TN", False, False)),
        ("PPUG - Città che Pattina", ("Città che Pattina", True, False)),
        ("PPUG Befane - Gruppo Finto", ("Befane", False, False)),
        (f"PPUG - San Finto  -Lienz - {PERSONA} e Gruppo", ("San Finto - Lienz", False, False)),
        ("PPUG - Mare-Monti GE - Gruppo Finto", ("Mare-Monti GE", False, False)),
        ("ANNULLATA - PPUG - Provopoli - Gruppo Finto", ("Provopoli", False, True)),
        ("PPUG - PROVAGRANDE e dintorni ", ("Provagrande e dintorni", True, False)),
        ("PPUG - Provopoli Babbi PPUG", ("Provopoli Babbi", True, False)),
        ("Giro di prova BL,  evento Bici e pattini", ("Giro di prova BL, evento Bici e pattini", True, False)),
    ]
    for numero, (titolo, atteso) in enumerate(casi, start=1):
        ottenuto = pattinate.ripulisci_titolo(titolo)
        verifica(f"1.{numero} titolo ripulito: {atteso[0]!r}", ottenuto == atteso, ottenuto)
    verifica("1. 'Pattinata – ' davanti solo quando il titolo non lo dice già",
             pattinate.nome_proposto("Provopoli") == "Pattinata – Provopoli" and pattinate.nome_proposto("Pattinata di Provopoli") == "Pattinata di Provopoli"
             and pattinate.nome_proposto("Città che Pattina") == "Città che Pattina")

    # --- Lettura del calendario ---------------------------------------------------------------------------------
    anomalie: list[str] = []
    ricorrente = evento_ics("ricorre@google.com", "PPUG - Ogni settimana - Gruppo", "2027-02-01", "2027-02-02", ("RRULE:FREQ=WEEKLY",))
    passato = evento_ics("ieri@google.com", "PPUG - Passata - Gruppo", "2026-11-21", "2026-11-22")
    senza_uid = [riga for riga in evento_ics("x", "PPUG - Senza identificativo - Gruppo", "2027-02-03", "2027-02-04") if not riga.startswith("UID:")]
    con_orario = ["BEGIN:VEVENT", "UID:orario@google.com", "DTSTAMP:20261101T000000Z", "DTSTART:20270610T213000Z", "DTEND:20270610T233000Z",
                  "SUMMARY:PPUG - Notturna di prova - Gruppo", "END:VEVENT"]
    letti, totale = pattinate.leggi_eventi_fonte(calendario_ics(*BASE, ricorrente, passato, senza_uid, con_orario), date.fromisoformat(OGGI), anomalie)
    per_uid = {evento.uid: evento for evento in letti}
    verifica("2. letti solo gli eventi futuri utilizzabili", sorted(per_uid) == ["estero@google.com", "mare@google.com", "orario@google.com", "roma@google.com", "valle@google.com"] and totale == 8, (sorted(per_uid), totale))
    verifica("2. la fine di un evento di più giorni è l'ultimo giorno compreso",
             (str(per_uid["roma@google.com"].inizio), str(per_uid["roma@google.com"].fine)) == ("2027-04-16", "2027-04-18"), per_uid["roma@google.com"])
    verifica("2. un evento di un giorno ha inizio e fine uguali", per_uid["valle@google.com"].inizio == per_uid["valle@google.com"].fine)
    verifica("2. un evento con orario viene letto in ora italiana (23:30-01:30: due giorni, in UTC sarebbe uno)", (str(per_uid["orario@google.com"].inizio), str(per_uid["orario@google.com"].fine)) == ("2027-06-10", "2027-06-11"),
             per_uid["orario@google.com"])
    verifica("2. ricorrenze ed eventi senza identificativo: saltati e segnalati", len(anomalie) == 2 and "ricorrente" in anomalie[0] and "senza UID" in anomalie[1], anomalie)
    try:
        pattinate.leggi_eventi_fonte(b"<html>errore</html>", date.fromisoformat(OGGI), [])
        letto_male = False
    except pattinate.ErroreFonte:
        letto_male = True
    verifica("2. un contenuto che non è un calendario viene rifiutato", letto_male)

    with tempfile.TemporaryDirectory() as temporanea:
        banco = Banco(Path(temporanea))

        # --- Primo giro: voci nuove ---------------------------------------------------------------------------
        codice = banco.esegui(*BASE)
        valle, mare, roma = banco.voce("valle@google.com"), banco.voce("mare@google.com"), banco.voce("roma@google.com")
        verifica("3. primo giro riuscito: 4 pattinate nuove più la gara", codice == 0 and len(banco.voci()) == 5 and None not in (valle, mare, roma), (codice, len(banco.voci())))
        verifica("3. voce nuova: da_verificare, pattinata, luogo da indicare, senza categorie né prova",
                 valle is not None and (valle["stato"], valle["tipo"], valle["luogo"], valle["paese"], valle["categorie"], valle["prova"], valle["organizzatore"])
                 == ("da_verificare", "pattinata", "da indicare", "IT", [], "", ""), valle)
        verifica("3. nome, titolo della fonte e id", valle is not None and (valle["nome"], valle["nome_fonte"], valle["id"])
                 == ("Pattinata – Val di Prova TN", "Val di Prova TN", "2027-05-16-pattinata-val-prova-tn"), valle)
        verifica("3. il nome che dice già 'Pattinata' non viene raddoppiato, nemmeno nell'id",
                 roma is not None and (roma["nome"], roma["id"], str(roma["data_fine"])) == ("Pattinata di Provopoli", "2027-04-16-pattinata-provopoli", "2027-04-18"), roma)
        verifica("3. link pubblico = pagina degli eventi; fonte = calendario con l'identificativo",
                 valle is not None and valle["url_ufficiale"] == pattinate.URL_PAGINA_EVENTI and valle["fonti"][0]["url"] == pattinate.URL_CALENDARIO + "#valle@google.com"
                 and str(valle["fonti"][0]["letto_il"]) == OGGI, valle)
        verifica("3. regola 9: né l'ultima parte del titolo né la descrizione finiscono nei file",
                 PERSONA not in banco.testo() and "Gruppo Finto" not in banco.testo() and "RITROVO" not in banco.testo() and "3330000000" not in banco.testo())
        gara = [voce for voce in banco.voci() if voce["tipo"] == "gara"]
        verifica("3. la gara dello stesso giorno non viene toccata né scambiata per una pattinata",
                 len(gara) == 1 and gara[0]["id"] == "2027-03-29-prova-gara-di-prova" and GARA_FINTA.split("- id:", 1)[1] in banco.eventi.read_text(encoding="utf-8"))
        verifica("3. l'intestazione del file resta", banco.eventi.read_text(encoding="utf-8").startswith("# Intestazione di prova.\n\n- id:"))
        generatore = subprocess.run([sys.executable, str(CARTELLA_SCRIPT / "genera_ics.py"), "--ingresso", str(banco.eventi), "--uscita", str(Path(temporanea) / "uscita"),
                                     "--url-base", "https://prova.example"], capture_output=True, text=True)
        verifica("3. genera_ics.py accetta il file scritto", generatore.returncode == 0, generatore.stderr[-400:])

        # --- Secondo giro identico: niente cambia --------------------------------------------------------------
        prima = banco.eventi.read_bytes()
        codice = banco.esegui(*BASE, oggi="2026-11-29")
        verifica("4. stessa fonte una settimana dopo: il file non cambia di un byte", codice == 0 and banco.eventi.read_bytes() == prima)

        # --- Revisione a mano, poi la fonte cambia ---------------------------------------------------------------
        banco.correggi("valle@google.com", luogo="Val di Prova (TN)", organizzatore="Gruppo di prova", stato="annunciato", note_interne=f"Rivista a mano. {TRACCIA}")
        spostata = evento_ics("valle@google.com", f"PPUG - Val di Prova TN - Gruppo Finto e {PERSONA}", "2027-05-23", "2027-05-25")
        codice = banco.esegui(spostata, MARE, TRE_GIORNI, ESTERO, oggi="2026-12-06")
        valle = banco.voce("valle@google.com")
        verifica("5. date cambiate nella fonte: la voce le segue e la data nell'id segue data_inizio",
                 codice == 0 and valle is not None and (str(valle["data_inizio"]), str(valle["data_fine"]), valle["id"]) == ("2027-05-23", "2027-05-24", "2027-05-23-pattinata-val-prova-tn"), valle)
        verifica("5. ciò che è stato scritto a mano resta: luogo, organizzatore, stato, nome",
                 valle is not None and (valle["luogo"], valle["organizzatore"], valle["stato"], valle["nome"]) == ("Val di Prova (TN)", "Gruppo di prova", "annunciato", "Pattinata – Val di Prova TN"), valle)
        verifica("5. la frase dello script va prima della traccia dell'arricchimento, che resta in coda",
                 valle is not None and "Aggiornata il 2026-12-06 da converti_pattinate.py" in valle["note_interne"] and "data_inizio 2027-05-16 → 2027-05-23" in valle["note_interne"]
                 and valle["note_interne"].endswith(TRACCIA), valle and valle["note_interne"])
        verifica("5. la data di lettura cambia solo nella voce cambiata",
                 valle is not None and str(valle["fonti"][0]["letto_il"]) == "2026-12-06" and str(banco.voce("mare@google.com")["fonti"][0]["letto_il"]) == OGGI)
        verifica("5. le voci restano in ordine di data", [str(v["data_inizio"]) for v in banco.voci()] == sorted(str(v["data_inizio"]) for v in banco.voci()))

        # --- Titolo cambiato e annullamento -----------------------------------------------------------------------
        rinominata = evento_ics("mare@google.com", "PPUG - Pasquetta in Collina - Gruppo Finto", "2027-03-29", "2027-03-30")
        annullata = evento_ics("roma@google.com", "ANNULLATA - PPUG - Pattinata di Provopoli - Gruppo Finto", "2027-04-16", "2027-04-19")
        codice = banco.esegui(spostata, rinominata, annullata, ESTERO, oggi="2026-12-13")
        mare, roma = banco.voce("mare@google.com"), banco.voce("roma@google.com")
        verifica("6. titolo cambiato: nome e nome_fonte seguono, il nome vecchio resta in note_interne, l'id no",
                 codice == 0 and mare is not None and (mare["nome"], mare["nome_fonte"], mare["id"]) == ("Pattinata – Pasquetta in Collina", "Pasquetta in Collina", "2027-03-29-pattinata-pasquetta-mare")
                 and "prima «Pattinata – Pasquetta al Mare»" in mare["note_interne"], mare)
        verifica("7. 'ANNULLATA' nel titolo: stato annullato, nome senza la parola",
                 roma is not None and (roma["stato"], roma["nome"]) == ("annullato", "Pattinata di Provopoli") and "Annullata il 2026-12-13" in roma["note_interne"], roma)
        prima = banco.eventi.read_bytes()
        codice = banco.esegui(spostata, rinominata, annullata, ESTERO, oggi="2026-12-20")
        verifica("7. le stesse novità rilette non producono altre modifiche", codice == 0 and banco.eventi.read_bytes() == prima)

        # --- Voce esclusa: memoria che non si tocca ---------------------------------------------------------------
        banco.correggi("estero@google.com", luogo="Lontanopoli", paese="PL", stato="escluso", verificato_il="2026-12-20", prova="Fuori perimetro: Lontanopoli (Polonia).")
        estero_spostato = evento_ics("estero@google.com", "PPUG - Lontanopoli Nuova - Gruppo Finto", "2027-08-01", "2027-08-03")
        prima = banco.eventi.read_bytes()
        codice = banco.esegui(spostata, rinominata, annullata, estero_spostato, oggi="2026-12-27")
        verifica("8. una voce escluso non viene toccata, nemmeno se nella fonte cambiano date e titolo", codice == 0 and banco.eventi.read_bytes() == prima)

        # --- Evento sparito dalla fonte ---------------------------------------------------------------------------
        codice = banco.esegui(spostata, annullata, estero_spostato, oggi="2027-01-03")
        mare = banco.voce("mare@google.com")
        verifica("9. evento sparito: la voce resta com'è, con la segnalazione in note_interne",
                 codice == 0 and mare is not None and mare["stato"] == "da_verificare" and "non è più nel calendario di Pattiniamo l'Italia" in mare["note_interne"], mare)
        prima = banco.eventi.read_bytes()
        codice = banco.esegui(spostata, annullata, estero_spostato, oggi="2027-01-10")
        verifica("9. la segnalazione si scrive una volta sola", codice == 0 and banco.eventi.read_bytes() == prima)

        # --- Evento ricreato nella fonte con un identificativo nuovo ------------------------------------------------
        ricreata = evento_ics("valle-nuovo@google.com", "PPUG - Val di Prova TN - Altro Gruppo", "2027-05-23", "2027-05-25")
        quante_prima = len(banco.voci())
        codice = banco.esegui(ricreata, annullata, estero_spostato, oggi="2027-01-17")
        valle = banco.voce("valle-nuovo@google.com")
        verifica("10. evento ricreato (stessa data, stesso titolo, identificativo nuovo): stessa voce, nessun doppione",
                 codice == 0 and len(banco.voci()) == quante_prima and valle is not None and valle["luogo"] == "Val di Prova (TN)" and banco.voce("valle@google.com") is None, valle)

        # --- Lettura sospetta -------------------------------------------------------------------------------------
        prima = banco.eventi.read_bytes()
        solo_uno = evento_ics("altro@google.com", "PPUG - Altrove - Gruppo", "2027-09-01", "2027-09-02")
        codice = banco.esegui(solo_uno, oggi="2027-01-24")
        verifica("11. se sparisce gran parte delle voci lo script si ferma senza scrivere",
                 codice == 1 and banco.eventi.read_bytes() == prima and "lettura sospetta" in banco.rapporto.read_text(encoding="utf-8"), codice)

        # --- Senza --scrivi ----------------------------------------------------------------------------------------
        nuova = evento_ics("nuova@google.com", "PPUG - Nuovopoli - Gruppo", "2027-10-01", "2027-10-02")
        codice = banco.esegui(ricreata, annullata, estero_spostato, nuova, oggi="2027-01-31", scrivi=False)
        verifica("12. senza --scrivi il file non cambia e il rapporto elenca la voce nuova",
                 codice == 0 and banco.eventi.read_bytes() == prima and "2027-10-01-pattinata-nuovopoli" in banco.rapporto.read_text(encoding="utf-8"))

    superate = sum(esiti)
    print(f"\n{superate}/{len(esiti)} prove superate")
    if not esiti:
        print("ERRORE: nessuna prova eseguita", file=sys.stderr)
        return 1
    return 0 if superate == len(esiti) else 1


if __name__ == "__main__":
    sys.exit(principale())
