#!/usr/bin/env python3
"""
converti_pattinate.py — dal calendario pubblico di Pattiniamo l'Italia alle voci `tipo: pattinata` di dati/eventi.yaml.

La fonte è un Google Calendar pubblico (file ICS): per ogni pattinata dà solo le date e un titolo
nella forma "PPUG - luogo o nome - gruppo che organizza"; niente luogo, niente orari. Le regole che
questo script applica sono le decisioni del proprietario del 2026-11-22 (appunti/decisioni.md).

Uso:
    python3 script/converti_pattinate.py [--eventi dati/eventi.yaml] [--oggi AAAA-MM-GG]
        [--ics FILE.ics] [--rapporto registro/AAAA-MM-GG-pattinate.md] [--scrivi]

Senza --scrivi non tocca eventi.yaml: stampa solo il rapporto. Senza --ics scarica il calendario dalla rete.
Legge solo gli eventi con data d'inizio da --oggi in poi (regola del progetto: gli eventi passati non si toccano).

Che cosa fa:
  - RICONOSCE una voce già presente dall'identificativo (UID) che Google dà all'evento, scritto nelle
    `fonti` della voce come frammento dell'indirizzo del calendario (…/basic.ics#UID): è la chiave stabile,
    come il numero di regolamento per le gare FISR. Se l'UID non c'è più ma una pattinata con la stessa data
    d'inizio e lo stesso titolo sì, è lo stesso evento ricreato nella fonte: la voce prende l'UID nuovo.
  - CREA una voce per ogni evento nuovo: date, nome ricavato dal titolo, `stato: da_verificare`,
    `luogo: "da indicare"`, `paese: IT`. Luogo, paese e organizzatore li compila chi rivede la voce
    (l'agente del martedì o il proprietario), che poi la porta ad `annunciato` oppure, se è fuori
    perimetro o non è una pattinata, a `escluso`.
  - SEGUE le date: se cambiano nella fonte cambiano nella voce, e la data nell'`id` segue `data_inizio`.
  - SEGUE il titolo: `nome_fonte` ricorda il titolo ripulito all'ultima lettura; se le sue parole cambiano,
    `nome` diventa il titolo nuovo e quello vecchio resta in `note_interne`.
  - ANNULLA: un titolo che dice "ANNULLATA" (o un evento con STATUS:CANCELLED) porta la voce ad `annullato`.
  - SEGNALA, senza cancellare né cambiare stato, le voci future che non sono più nella fonte.
  - NON TOCCA le voci `escluso` (sono la memoria di ciò che è stato scartato) e nient'altro di ciò che
    una persona ha scritto: luogo, paese, organizzatore, note, link.

Che cosa non fa mai (regola 9 di CLAUDE.md: niente informazioni personali):
  - non copia l'ultima parte del titolo, dove la fonte scrive il gruppo e spesso i nomi delle persone
    che organizzano; se il titolo ha una parte sola, la tiene e lo segnala nel rapporto;
  - non legge e non copia le descrizioni degli eventi;
  - non scrive titoli grezzi né descrizioni in nessun file, nemmeno nel rapporto.

`note_interne` ha più scrittori: le frasi di questo script vanno prima della traccia "Arricchimento
AAAA-MM-GG: …" lasciata dall'arricchimento, che resta l'ultima frase; prima di scrivere lo script
controlla che la traccia di ogni voce sia rimasta identica, altrimenti si ferma.

Esce con 0 se tutto è andato bene, con 1 se non ha potuto leggere la fonte, se la lettura è sospetta
(troppe voci sparite in una volta) o se il controllo in uscita fallisce: in questi casi eventi.yaml
non viene scritto e il rapporto, se richiesto, riporta l'errore (regola 5).
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import yaml
    from icalendar import Calendar
except ImportError:  # pragma: no cover
    sys.exit("Manca una dipendenza. Installa: pip install -r script/requisiti.txt")

CARTELLA_SCRIPT = Path(__file__).resolve().parent
if not (CARTELLA_SCRIPT / "converti_fisr.py").is_file():
    sys.exit(f"Non trovo converti_fisr.py in {CARTELLA_SCRIPT}: questo script ne riusa la lettura e la scrittura di eventi.yaml")
sys.path.insert(0, str(CARTELLA_SCRIPT))

import converti_fisr  # noqa: E402 — va importato dopo aver aggiunto la cartella degli script al percorso

FUNZIONI_RIUSATE = ("carica_eventi", "emetti_evento", "slug", "senza_accenti", "aggiungi_a_note_interne", "coda_arricchimento")
_mancanti = [nome for nome in FUNZIONI_RIUSATE if not callable(getattr(converti_fisr, nome, None))]
if _mancanti or not isinstance(getattr(converti_fisr, "ORDINE_CAMPI", None), list):
    sys.exit(f"converti_fisr.py non ha più ciò che questo script riusa ({_mancanti or 'ORDINE_CAMPI'}): vanno aggiornati insieme")

URL_CALENDARIO = "https://calendar.google.com/calendar/ical/7bpemuo7vdilljftkjo7iru42c%40group.calendar.google.com/public/basic.ics"
URL_PAGINA_EVENTI = "https://www.pattiniamolitalia.it/eventi/"
NOME_FONTE = "calendario di Pattiniamo l'Italia"
FIRMA = "converti_pattinate.py"
LUOGO_DA_INDICARE = "da indicare"
FUSO_ITALIANO = ZoneInfo("Europe/Rome")

SIGLA = re.compile(r"\bPPUG\b", re.I)
ESPRESSIONE_ANNULLATA = re.compile(r"\bANNULLAT[AOIE]\b", re.I)
# Il trattino che separa le parti del titolo ha almeno uno spazio accanto ("San Candido  -Lienz");
# quello dentro un nome non ne ha ("Sanremo-Ospedaletti") e resta dov'è.
SEPARATORE_PARTI = re.compile(r"\s+[-–—]\s*|\s*[-–—]\s+")
PAROLE_FUORI_DALLO_SLUG = {"pattinata", "pattinate", "ppug", "di", "del", "della", "dei", "delle", "e", "a", "al", "in", "il", "la", "le", "i"}
FRASE_SPARITA = f"l'evento non è più nel {NOME_FONTE}"
FRASE_NON_PIU_ANNULLATA = "il titolo non dice più che è annullata"
MASSIMO_GIORNI_DI_DURATA = 10


class ErroreFonte(Exception):
    """La fonte non si è potuta leggere, o ciò che ha restituito non è utilizzabile."""


@dataclass
class EventoFonte:
    """Ciò che lo script tiene di un evento della fonte. Il titolo grezzo e la descrizione non sono qui di proposito."""
    uid: str
    inizio: date
    fine: date                # ultimo giorno, compreso
    titolo_ripulito: str      # senza la sigla, senza l'ultima parte, senza "ANNULLATA"
    una_sola_parte: bool      # il titolo non aveva una parte finale da togliere: va riletto da una persona
    annullata: bool


# ---------------------------------------------------------------------------
# Lettura della fonte
# ---------------------------------------------------------------------------

def scarica_calendario(indirizzo: str = URL_CALENDARIO, tentativi: int = 3, attesa_secondi: float = 5.0) -> bytes:
    """Scarica il file ICS. Controlla codice di risposta, tipo del contenuto e inizio del file."""
    ultimo_errore = "nessun tentativo fatto"
    for tentativo in range(1, tentativi + 1):
        try:
            richiesta = urllib.request.Request(indirizzo, headers={"User-Agent": "PattinaggioCorsa-calendario-pubblico (script/converti_pattinate.py)"})
            with urllib.request.urlopen(richiesta, timeout=60) as risposta:
                codice = risposta.status
                tipo = risposta.headers.get("Content-Type", "")
                contenuto = risposta.read()
            if codice != 200:
                ultimo_errore = f"risposta HTTP {codice}"
            elif "text/calendar" not in tipo.lower():
                ultimo_errore = f"tipo del contenuto inatteso: {tipo!r}"
            elif not contenuto.lstrip().startswith(b"BEGIN:VCALENDAR"):
                ultimo_errore = "il contenuto non inizia con BEGIN:VCALENDAR"
            else:
                return contenuto
        except (urllib.error.URLError, TimeoutError, OSError) as errore:
            ultimo_errore = f"{type(errore).__name__}: {errore}"
        if tentativo < tentativi:
            time.sleep(attesa_secondi)
    raise ErroreFonte(f"{indirizzo}: non letto dopo {tentativi} tentativi ({ultimo_errore})")


def ripulisci_titolo(titolo: str) -> tuple[str, bool, bool]:
    """Dal titolo della fonte a (titolo ripulito, una sola parte?, annullata?).

    Toglie la sigla PPUG e la parola ANNULLATA, divide il titolo nelle sue parti e butta l'ultima,
    dove la fonte scrive il gruppo che organizza e spesso i nomi delle persone (regola 9). Se la parte
    è una sola la tiene: non c'è modo di sapere che cosa contiene, e il rapporto lo segnala."""
    testo = re.sub(r"\s+", " ", str(titolo or "")).strip()
    annullata = bool(ESPRESSIONE_ANNULLATA.search(testo))
    testo = ESPRESSIONE_ANNULLATA.sub(" ", testo)
    parti = []
    for parte in SEPARATORE_PARTI.split(testo):
        parte = re.sub(r"\s+", " ", SIGLA.sub(" ", parte)).strip(" ,;:.-–—")
        if parte:
            parti.append(parte)
    una_sola_parte = len(parti) <= 1
    if len(parti) >= 2:
        parti = parti[:-1]
    ripulito = " - ".join(parti)
    # Una parola lunga scritta tutta in maiuscolo torna normale ("PESCARA" → "Pescara"); le sigle corte
    # ("TN", "GPM") restano come sono.
    ripulito = re.sub(r"[A-ZÀ-Ý]{5,}", lambda trovata: trovata.group(0).capitalize(), ripulito)
    return ripulito, una_sola_parte, annullata


def _giorno(valore, fine_esclusiva: bool = False) -> date:
    """Il giorno di un DTSTART o DTEND. Un orario con fuso viene letto in ora italiana.
    Per una fine esclusiva (giornata intera, oppure mezzanotte in punto) il giorno è quello prima."""
    if isinstance(valore, datetime):
        locale = valore.astimezone(FUSO_ITALIANO) if valore.tzinfo is not None else valore
        giorno = locale.date()
        if fine_esclusiva and (locale.hour, locale.minute, locale.second) == (0, 0, 0):
            giorno -= timedelta(days=1)
        return giorno
    if isinstance(valore, date):
        return valore - timedelta(days=1) if fine_esclusiva else valore
    raise ValueError(f"valore di data inatteso: {valore!r}")


def leggi_eventi_fonte(contenuto: bytes, oggi: date, anomalie: list[str]) -> tuple[list[EventoFonte], int]:
    """Gli eventi della fonte con data d'inizio da `oggi` in poi, e il numero di eventi totali nel file.
    Ogni evento che non si può usare finisce in `anomalie`, indicato solo con data e UID."""
    if not isinstance(contenuto, (bytes, bytearray)) or not contenuto.strip():
        raise ErroreFonte("il calendario è vuoto")
    try:
        calendario = Calendar.from_ical(bytes(contenuto))
    except Exception as errore:  # icalendar solleva ValueError e sottoclassi proprie
        raise ErroreFonte(f"il calendario non è un file ICS leggibile ({type(errore).__name__}: {errore})") from errore
    componenti = list(calendario.walk("VEVENT"))
    if not componenti:
        raise ErroreFonte("il calendario non contiene nessun evento")
    eventi: list[EventoFonte] = []
    uid_visti: set[str] = set()
    for componente in componenti:
        uid = str(componente.get("UID") or "").strip()
        inizio_grezzo = componente.get("DTSTART")
        if inizio_grezzo is None:
            anomalie.append(f"- evento senza data d'inizio (UID `{uid or '?'}`): saltato")
            continue
        try:
            inizio = _giorno(inizio_grezzo.dt)
        except ValueError as errore:
            anomalie.append(f"- evento con data d'inizio illeggibile (UID `{uid or '?'}`): {errore}; saltato")
            continue
        if inizio < oggi:
            continue
        if not uid:
            anomalie.append(f"- evento del {inizio} senza UID: saltato (senza UID non si può riconoscere alla prossima lettura)")
            continue
        if componente.get("RRULE") is not None or componente.get("RECURRENCE-ID") is not None:
            anomalie.append(f"- evento ricorrente del {inizio} (UID `{uid}`): saltato, le ricorrenze non sono gestite")
            continue
        if uid in uid_visti:
            anomalie.append(f"- UID `{uid}` ripetuto nel calendario ({inizio}): tenuta la prima occorrenza")
            continue
        fine_grezza = componente.get("DTEND")
        try:
            fine = _giorno(fine_grezza.dt, fine_esclusiva=True) if fine_grezza is not None else inizio
        except ValueError as errore:
            anomalie.append(f"- evento del {inizio} (UID `{uid}`) con data di fine illeggibile: {errore}; trattato come evento di un giorno")
            fine = inizio
        if fine < inizio:
            fine = inizio
        if (fine - inizio).days + 1 > MASSIMO_GIORNI_DI_DURATA:
            anomalie.append(f"- evento del {inizio} (UID `{uid}`) lungo {(fine - inizio).days + 1} giorni: saltato, da guardare a mano")
            continue
        ripulito, una_sola_parte, annullata = ripulisci_titolo(str(componente.get("SUMMARY") or ""))
        if str(componente.get("STATUS") or "").strip().upper() == "CANCELLED":
            annullata = True
        if not ripulito:
            anomalie.append(f"- evento del {inizio} (UID `{uid}`): dopo la pulizia il titolo è vuoto; saltato")
            continue
        uid_visti.add(uid)
        eventi.append(EventoFonte(uid=uid, inizio=inizio, fine=fine, titolo_ripulito=ripulito, una_sola_parte=una_sola_parte, annullata=annullata))
    eventi.sort(key=lambda evento: (evento.inizio, evento.titolo_ripulito, evento.uid))
    return eventi, len(componenti)


# ---------------------------------------------------------------------------
# Dalla fonte alle voci
# ---------------------------------------------------------------------------

def indirizzo_con_uid(uid: str) -> str:
    """L'indirizzo che va nelle `fonti` della voce: il calendario, con l'UID dell'evento come frammento."""
    return URL_CALENDARIO + "#" + urllib.parse.quote(uid, safe="@._-")


def uid_della_voce(voce: dict) -> set[str]:
    """Gli UID del calendario di Pattiniamo l'Italia citati nelle `fonti` di una voce (di norma uno)."""
    trovati: set[str] = set()
    for fonte in voce.get("fonti") or []:
        if not isinstance(fonte, dict):
            continue
        indirizzo = str(fonte.get("url") or "")
        if indirizzo.startswith(URL_CALENDARIO + "#"):
            uid = urllib.parse.unquote(indirizzo[len(URL_CALENDARIO) + 1:])
            if uid:
                trovati.add(uid)
    return trovati


def parole(testo: str) -> list[str]:
    """Le parole di un titolo, per capire se è cambiato davvero: maiuscole, accenti e punteggiatura non contano."""
    return re.findall(r"[a-z0-9]+", converti_fisr.senza_accenti(str(testo or "")).lower())


def nome_proposto(titolo_ripulito: str) -> str:
    """Il nome pubblico: il titolo ripulito, con "Pattinata – " davanti quando non lo dice già da sé."""
    return titolo_ripulito if re.search(r"pattin", titolo_ripulito, re.I) else f"Pattinata – {titolo_ripulito}"


def id_libero(base: str, occupati: set[str]) -> str:
    candidato, contatore = base, 2
    while candidato in occupati:
        candidato = f"{base}-{contatore}"
        contatore += 1
    return candidato


def id_proposto(inizio: date, titolo_ripulito: str, occupati: set[str]) -> str:
    coda = converti_fisr.slug(titolo_ripulito, massimo_parole=5, parole_vuote=PAROLE_FUORI_DALLO_SLUG)
    base = f"{inizio.isoformat()}-pattinata" + (f"-{coda}" if coda else "")
    return id_libero(base, occupati)


def voce_nuova(evento: EventoFonte, oggi: date, occupati: set[str]) -> dict:
    avviso = " Il titolo ha una parte sola: controllare che il nome non contenga nomi di persone." if evento.una_sola_parte else ""
    return {
        "id": id_proposto(evento.inizio, evento.titolo_ripulito, occupati),
        "nome": nome_proposto(evento.titolo_ripulito),
        "nome_fonte": evento.titolo_ripulito,
        "data_inizio": evento.inizio.isoformat(),
        "data_fine": evento.fine.isoformat(),
        "luogo": LUOGO_DA_INDICARE,
        "paese": "IT",
        "tipo": "pattinata",
        "categorie": [],
        "distanze": [],
        "organizzatore": "",
        "url_ufficiale": URL_PAGINA_EVENTI,
        "url_iscrizione": "",
        "scadenza_iscrizione": "",
        "stato": "annullato" if evento.annullata else "da_verificare",
        "fonti": [{"url": indirizzo_con_uid(evento.uid), "letto_il": oggi.isoformat()}],
        "verificato_il": "",
        "prova": "",
        "note": "",
        "note_interne": f"Proposta il {oggi.isoformat()} da {FIRMA} dal {NOME_FONTE}, che dà solo date e titolo: luogo, paese e organizzatore "
                        f"sono da compilare leggendo il titolo nella fonte, senza copiare nomi di persone (regola 9).{avviso}",
    }


def segna_lettura(voce: dict, uid: str, oggi: date) -> None:
    """Aggiorna la data di lettura della fonte della voce (solo quando la voce è cambiata: altrimenti
    ogni settimana cambierebbero tutte le voci senza che sia successo nulla)."""
    atteso = indirizzo_con_uid(uid)
    for fonte in voce.get("fonti") or []:
        if isinstance(fonte, dict) and str(fonte.get("url") or "").startswith(URL_CALENDARIO + "#"):
            fonte["url"] = atteso
            fonte["letto_il"] = oggi.isoformat()
            return
    voce.setdefault("fonti", []).append({"url": atteso, "letto_il": oggi.isoformat()})


def aggiorna_voce(voce: dict, evento: EventoFonte, oggi: date, occupati: set[str]) -> list[str]:
    """Porta nella voce ciò che è cambiato nella fonte: date (e la data nell'id), titolo, annullamento.
    Restituisce le frasi per il rapporto; lista vuota se non è cambiato nulla."""
    cambiamenti: list[str] = []
    frasi: list[str] = []
    inizio_prima, fine_prima = str(voce["data_inizio"]), str(voce["data_fine"])
    inizio_dopo, fine_dopo = evento.inizio.isoformat(), evento.fine.isoformat()
    if (inizio_prima, fine_prima) != (inizio_dopo, fine_dopo):
        dettagli = []
        if inizio_prima != inizio_dopo:
            dettagli.append(f"data_inizio {inizio_prima} → {inizio_dopo}")
            voce["data_inizio"] = inizio_dopo
            id_prima = str(voce["id"])
            coda = id_prima[len(inizio_prima):] if id_prima.startswith(inizio_prima) else "-" + id_prima
            occupati.discard(id_prima)
            voce["id"] = id_libero(inizio_dopo + coda, occupati)
            occupati.add(voce["id"])
            dettagli.append(f"id {id_prima} → {voce['id']}")
        if fine_prima != fine_dopo:
            dettagli.append(f"data_fine {fine_prima} → {fine_dopo}")
            voce["data_fine"] = fine_dopo
        cambiamenti.append("date cambiate nella fonte: " + "; ".join(dettagli))
        frasi.append(f"Aggiornata il {oggi.isoformat()} da {FIRMA} (date cambiate nel {NOME_FONTE}): " + "; ".join(dettagli) + ".")
    titolo_prima = str(voce.get("nome_fonte") or "")
    if not titolo_prima:
        voce["nome_fonte"] = evento.titolo_ripulito
        cambiamenti.append("titolo della fonte registrato per la prima volta (il nome non cambia)")
    elif parole(titolo_prima) != parole(evento.titolo_ripulito):
        nome_prima = str(voce["nome"])
        voce["nome_fonte"] = evento.titolo_ripulito
        voce["nome"] = nome_proposto(evento.titolo_ripulito)
        cambiamenti.append(f"titolo cambiato nella fonte: nome «{nome_prima}» → «{voce['nome']}» (luogo e organizzatore da ricontrollare)")
        frasi.append(f"Nome aggiornato il {oggi.isoformat()} da {FIRMA} (titolo cambiato nel {NOME_FONTE}): prima «{nome_prima}». "
                     f"Da controllare: luogo e organizzatore erano stati letti dal titolo precedente.")
    stato = str(voce.get("stato") or "")
    if evento.annullata and stato != "annullato":
        voce["stato"] = "annullato"
        cambiamenti.append(f"annullata nella fonte: stato {stato} → annullato")
        frasi.append(f"Annullata il {oggi.isoformat()} da {FIRMA}: nel {NOME_FONTE} il titolo dice che è annullata (stato prima: {stato}).")
    elif not evento.annullata and stato == "annullato" and FRASE_NON_PIU_ANNULLATA not in str(voce.get("note_interne") or ""):
        cambiamenti.append("la voce è `annullato` ma nella fonte il titolo non dice più che è annullata: da controllare")
        frasi.append(f"Da controllare ({FIRMA}, {oggi.isoformat()}): nel {NOME_FONTE} {FRASE_NON_PIU_ANNULLATA}; lo stato non è stato toccato.")
    for frase in frasi:
        voce["note_interne"] = converti_fisr.aggiungi_a_note_interne(voce.get("note_interne"), frase)
    if cambiamenti:
        segna_lettura(voce, evento.uid, oggi)
    return cambiamenti


def elabora(esistenti: list[dict], eventi_fonte: list[EventoFonte], oggi: date) -> dict:
    """Confronta la fonte con le voci presenti. Modifica `esistenti` sul posto e restituisce il resoconto:
    voci nuove, aggiornate, sparite, già escluse, invariate, da rileggere a mano."""
    pattinate = [voce for voce in esistenti if str(voce.get("tipo")) == "pattinata" and uid_della_voce(voce)]
    per_uid: dict[str, dict] = {}
    for voce in pattinate:
        for uid in uid_della_voce(voce):
            per_uid.setdefault(uid, voce)
    uid_nella_fonte = {evento.uid for evento in eventi_fonte}
    occupati = {str(voce["id"]) for voce in esistenti}
    resoconto: dict = {"nuove": [], "aggiornate": [], "sparite": [], "escluse": [], "invariate": 0, "una_sola_parte": []}
    viste: set[int] = set()
    for evento in eventi_fonte:
        voce = per_uid.get(evento.uid)
        if voce is None:
            # Stesso evento ricreato nella fonte (UID nuovo): stessa data d'inizio e stesso titolo di una voce
            # il cui UID non è più nel calendario.
            for candidata in pattinate:
                if id(candidata) in viste or uid_della_voce(candidata) & uid_nella_fonte:
                    continue
                if str(candidata["data_inizio"]) == evento.inizio.isoformat() and parole(candidata.get("nome_fonte")) == parole(evento.titolo_ripulito):
                    voce = candidata
                    if str(voce.get("stato")) != "escluso":
                        segna_lettura(voce, evento.uid, oggi)
                        resoconto["aggiornate"].append(f"- `{voce['id']}`: l'evento è stato ricreato nella fonte (identificativo nuovo); la voce è la stessa")
                    break
        if voce is not None:
            viste.add(id(voce))
            if str(voce.get("stato")) == "escluso":
                resoconto["escluse"].append(f"- `{voce['id']}`")
                continue
            id_prima = str(voce["id"])
            cambiamenti = aggiorna_voce(voce, evento, oggi, occupati)
            if cambiamenti:
                resoconto["aggiornate"].append(f"- `{id_prima}`: " + "; ".join(cambiamenti))
            else:
                resoconto["invariate"] += 1
            continue
        nuova = voce_nuova(evento, oggi, occupati)
        occupati.add(nuova["id"])
        resoconto["nuove"].append(nuova)
        if evento.una_sola_parte:
            resoconto["una_sola_parte"].append(f"- `{nuova['id']}`: «{nuova['nome']}»")
    for voce in pattinate:
        if id(voce) in viste or str(voce.get("stato")) == "escluso" or str(voce["data_inizio"]) < oggi.isoformat():
            continue
        resoconto["sparite"].append(voce)
    return resoconto


def segnala_sparite(sparite: list[dict], oggi: date) -> list[str]:
    """Scrive in `note_interne` (una volta sola) che l'evento non è più nella fonte. La voce resta com'è."""
    righe = []
    for voce in sparite:
        if FRASE_SPARITA in str(voce.get("note_interne") or ""):
            righe.append(f"- `{voce['id']}`: ancora assente dalla fonte (già segnalata)")
            continue
        frase = f"Da controllare ({FIRMA}, {oggi.isoformat()}): {FRASE_SPARITA}; la voce resta com'è finché qualcuno non decide."
        voce["note_interne"] = converti_fisr.aggiungi_a_note_interne(voce.get("note_interne"), frase)
        righe.append(f"- `{voce['id']}`: non è più nella fonte; segnalata in `note_interne`, stato non toccato")
    return righe


def controlla_voce(voce: dict) -> list[str]:
    """Controllo in uscita di una voce creata o modificata da questo script."""
    errori = []
    mancanti = [campo for campo in converti_fisr.ORDINE_CAMPI if campo not in voce]
    if mancanti:
        errori.append(f"{voce.get('id')}: campi mancanti {mancanti}")
        return errori
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*", str(voce["id"])):
        errori.append(f"{voce['id']}: id di forma inattesa")
    if not str(voce["id"]).startswith(str(voce["data_inizio"]) + "-"):
        errori.append(f"{voce['id']}: la data nell'id non coincide con data_inizio ({voce['data_inizio']})")
    if str(voce["data_fine"]) < str(voce["data_inizio"]):
        errori.append(f"{voce['id']}: data_fine prima di data_inizio")
    if not str(voce["nome"]).strip() or not str(voce["luogo"]).strip():
        errori.append(f"{voce['id']}: nome o luogo vuoti")
    if not uid_della_voce(voce):
        errori.append(f"{voce['id']}: manca la fonte con l'identificativo dell'evento")
    return errori


def principale(argomenti: list[str] | None = None) -> int:
    analizzatore = argparse.ArgumentParser(description="Dal calendario di Pattiniamo l'Italia alle pattinate di eventi.yaml")
    analizzatore.add_argument("--eventi", type=Path, default=Path("dati/eventi.yaml"))
    analizzatore.add_argument("--ics", type=Path, default=None, help="legge il calendario da questo file invece che dalla rete")
    analizzatore.add_argument("--oggi", default=None, help="AAAA-MM-GG (predefinito: oggi in UTC); si leggono gli eventi da questa data in poi")
    analizzatore.add_argument("--scrivi", action="store_true", help="riscrive eventi.yaml (senza: solo rapporto)")
    analizzatore.add_argument("--rapporto", type=Path, default=None, help="scrive il rapporto in Markdown in questo file")
    opzioni = analizzatore.parse_args(argomenti)

    try:
        oggi = date.fromisoformat(opzioni.oggi) if opzioni.oggi else datetime.now(timezone.utc).date()
    except ValueError:
        print(f"ERRORE: --oggi non è una data ISO: {opzioni.oggi!r}", file=sys.stderr)
        return 1

    rapporto: list[str] = [f"# Pattinate dal {NOME_FONTE}, lettura del {oggi.isoformat()}", "",
                           f"Fonte: {URL_CALENDARIO} (pagina pubblica: {URL_PAGINA_EVENTI}). Eventi letti: quelli con inizio dal {oggi.isoformat()} in poi. "
                           "Di ogni evento lo script tiene date, identificativo e titolo senza l'ultima parte; le descrizioni non vengono lette."]

    def chiudi(codice: int) -> int:
        testo = "\n".join(rapporto) + "\n"
        if opzioni.rapporto:
            opzioni.rapporto.parent.mkdir(parents=True, exist_ok=True)
            opzioni.rapporto.write_text(testo, encoding="utf-8")
        print(testo)
        return codice

    def fallisci(messaggio: str) -> int:
        rapporto.extend(["", "## Errore: eventi.yaml non è stato toccato", "", messaggio])
        print(f"ERRORE: {messaggio}", file=sys.stderr)
        return chiudi(1)

    if not opzioni.eventi.is_file():
        return fallisci(f"{opzioni.eventi}: file non trovato")
    anomalie: list[str] = []
    try:
        if opzioni.ics is not None:
            if not opzioni.ics.is_file():
                return fallisci(f"{opzioni.ics}: file non trovato")
            contenuto = opzioni.ics.read_bytes()
        else:
            contenuto = scarica_calendario()
        eventi_fonte, totale_nel_file = leggi_eventi_fonte(contenuto, oggi, anomalie)
    except ErroreFonte as errore:
        return fallisci(str(errore))

    intestazione, esistenti = converti_fisr.carica_eventi(opzioni.eventi)
    for indice, voce in enumerate(esistenti):
        if not isinstance(voce, dict) or not {"id", "data_inizio", "data_fine", "nome"} <= set(voce):
            return fallisci(f"{opzioni.eventi}: la voce n. {indice + 1} non ha i campi id, nome, data_inizio, data_fine")
        fonti = voce.get("fonti")
        if not isinstance(fonti, list) or not all(isinstance(fonte, dict) and {"url", "letto_il"} <= set(fonte) for fonte in fonti):
            return fallisci(f"{opzioni.eventi}: nella voce {voce['id']} 'fonti' non è una lista di voci con url e letto_il")
    tracce_prima = {id(voce): converti_fisr.coda_arricchimento(voce.get("note_interne")) for voce in esistenti}
    testo_prima = {id(voce): converti_fisr.emetti_evento(voce) for voce in esistenti}

    resoconto = elabora(esistenti, eventi_fonte, oggi)
    seguite = sum(1 for voce in esistenti if str(voce.get("tipo")) == "pattinata" and uid_della_voce(voce)
                  and str(voce.get("stato")) != "escluso" and str(voce["data_inizio"]) >= oggi.isoformat())
    # Una lettura in cui sparisce gran parte delle voci è più probabilmente un calendario letto male che un fatto.
    if len(resoconto["sparite"]) > max(2, seguite // 2):
        return fallisci(f"lettura sospetta: {len(resoconto['sparite'])} voci future su {seguite} non sono più nella fonte "
                        f"(eventi futuri letti: {len(eventi_fonte)}). Nessuna modifica: rileggere a mano.")
    righe_sparite = segnala_sparite(resoconto["sparite"], oggi)
    nuove: list[dict] = resoconto["nuove"]

    rapporto.extend(["", f"Eventi nel calendario: {totale_nel_file}; futuri letti: {len(eventi_fonte)}. "
                         f"Voci nuove: {len(nuove)}; aggiornate: {len(resoconto['aggiornate'])}; invariate: {resoconto['invariate']}; "
                         f"già escluse (non toccate): {len(resoconto['escluse'])}; non più nella fonte: {len(resoconto['sparite'])}; "
                         f"eventi saltati: {len(anomalie)}."])
    rapporto.extend(["", f"## Voci nuove: {len(nuove)}", ""])
    if nuove:
        rapporto.append("Entrano come `da_verificare` con `luogo: \"da indicare\"`: chi le rivede compila luogo, paese e organizzatore leggendo il titolo nella fonte "
                        "e le porta ad `annunciato`, oppure a `escluso` se sono fuori perimetro o non sono pattinate.")
        rapporto.extend(["", "| Inizio | Fine | Nome proposto | Stato | `id` |", "|---|---|---|---|---|"])
        for voce in sorted(nuove, key=lambda v: (v["data_inizio"], v["id"])):
            rapporto.append(f"| {voce['data_inizio']} | {voce['data_fine']} | {voce['nome']} | {voce['stato']} | `{voce['id']}` |")
    rapporto.extend(["", f"## Voci aggiornate (date, titolo, annullamento): {len(resoconto['aggiornate'])}", ""])
    rapporto.extend(resoconto["aggiornate"])
    rapporto.extend(["", f"## Da controllare a mano prima del merge: {len(resoconto['una_sola_parte']) + len(righe_sparite)}", ""])
    if resoconto["una_sola_parte"]:
        rapporto.append("Titoli con una parte sola (lo script non ha potuto togliere la parte finale: controllare che il nome non contenga nomi di persone):")
        rapporto.extend(resoconto["una_sola_parte"])
    if righe_sparite:
        rapporto.append("Voci future che non sono più nella fonte:")
        rapporto.extend(righe_sparite)
    rapporto.extend(["", f"## Eventi della fonte saltati: {len(anomalie)}", ""])
    rapporto.extend(anomalie)
    rapporto.extend(["", f"## Voci già escluse, non toccate: {len(resoconto['escluse'])}", ""])
    rapporto.extend(resoconto["escluse"])

    errori = [errore for voce in nuove for errore in controlla_voce(voce)]
    modificate = [voce for voce in esistenti if converti_fisr.emetti_evento(voce) != testo_prima[id(voce)]]
    errori.extend(errore for voce in modificate for errore in controlla_voce(voce))
    estranee = [str(voce["id"]) for voce in modificate if str(voce.get("tipo")) != "pattinata"]
    if estranee:
        errori.append(f"modificate voci che non sono pattinate: {estranee}")
    tracce_toccate = [str(voce["id"]) for voce in esistenti if converti_fisr.coda_arricchimento(voce.get("note_interne")) != tracce_prima[id(voce)]]
    if tracce_toccate:
        errori.append(f"la traccia 'Arricchimento …' in note_interne è cambiata o non è più l'ultima frase in: {tracce_toccate}")
    tutti = sorted(esistenti + nuove, key=lambda voce: (str(voce["data_inizio"]), str(voce["id"])))
    identificativi = [str(voce["id"]) for voce in tutti]
    doppi = sorted({i for i in identificativi if identificativi.count(i) > 1})
    if doppi:
        errori.append(f"id ripetuti: {doppi}")
    if errori:
        return fallisci("controllo in uscita fallito: " + " | ".join(errori))

    if opzioni.scrivi and (nuove or modificate):
        contenuto_nuovo = intestazione + "\n" + "\n".join(converti_fisr.emetti_evento(voce) for voce in tutti)
        opzioni.eventi.write_text(contenuto_nuovo, encoding="utf-8")
        riletti = yaml.safe_load(opzioni.eventi.read_text(encoding="utf-8"))
        if not isinstance(riletti, list) or len(riletti) != len(tutti):
            return fallisci(f"scritti {len(tutti)} eventi, riletti {len(riletti) if isinstance(riletti, list) else 'un contenuto che non è una lista'}")
        if [str(voce["id"]) for voce in riletti] != identificativi:
            return fallisci("dopo la scrittura gli id riletti non coincidono con quelli scritti")
        print(f"scritto {opzioni.eventi}: {len(nuove)} pattinate nuove, {len(modificate)} voci aggiornate o segnalate, {len(tutti)} eventi in tutto", file=sys.stderr)
    elif opzioni.scrivi:
        print(f"{opzioni.eventi}: nessuna modifica, file non riscritto", file=sys.stderr)
    return chiudi(0)


if __name__ == "__main__":
    sys.exit(principale())
