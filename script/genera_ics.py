#!/usr/bin/env python3
"""
genera_ics.py — genera calendario.ics e index.html a partire da dati/eventi.yaml.

Uso:
    python3 script/genera_ics.py --ingresso dati/eventi.yaml --uscita uscita \
        [--url-base https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico]

Cosa fa, nell'ordine:
  1. legge il file YAML e lo valida campo per campo; al primo gruppo di errori
     si ferma e li elenca tutti, con l'id dell'evento e il campo sbagliato;
  2. costruisce il calendario: gli eventi con stato "escluso" non vengono
     pubblicati, tutti gli altri sì (con un prefisso nel titolo se lo stato
     non è "confermato" o "annunciato");
  3. scrive calendario.ics e index.html nella cartella di uscita (il testo della pagina
     viene da pagina/modello_index.html) e vi copia gli altri file di pagina/ (stile.css…);
  4. rilegge il file .ics appena scritto e verifica che contenga esattamente
     gli eventi attesi, con le proprietà obbligatorie e righe conformi.

Esce con codice 0 solo se tutto è andato bene; altrimenti 1 (errori nei dati
o nell'uscita) o 2 (errori di uso o di sistema).
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    import yaml
    from icalendar import Calendar, Event
except ImportError as errore:  # pragma: no cover
    sys.exit(f"Manca una dipendenza ({errore}). Installa: pip install -r script/requisiti.txt")

# ---------------------------------------------------------------------------
# Regole del dominio (devono coincidere con CLAUDE.md)
# ---------------------------------------------------------------------------

PAESI_AMMESSI = {"IT", "CH", "ES", "PT", "FR", "AT", "DE", "SI"}
TIPI_AMMESSI = {"gara", "pattinata"}
CATEGORIE_AMMESSE = {"master", "amatori"}
STATI_AMMESSI = {
    "da_verificare",
    "annunciato",
    "confermato",
    "rinviato",
    "annullato",
    "non_autorizzato",
    "escluso",
}
STATI_NON_PUBBLICATI = {"escluso"}
# Prefisso nel titolo per gli stati che il lettore deve notare subito.
PREFISSO_TITOLO = {
    "da_verificare": "[da verificare] ",
    "non_autorizzato": "[non ancora autorizzata] ",
    "rinviato": "[RINVIATA] ",
    "annullato": "[ANNULLATA] ",
}
# STATUS iCalendar. Per "annullato" non usiamo CANCELLED perché alcune app
# nascondono gli eventi cancellati: meglio il prefisso visibile nel titolo.
STATUS_ICAL = {
    "confermato": "CONFIRMED",
    "annunciato": "TENTATIVE",
    "da_verificare": "TENTATIVE",
    "non_autorizzato": "TENTATIVE",
    "rinviato": "TENTATIVE",
}

CHIAVI_EVENTO = [
    "id", "nome", "data_inizio", "data_fine", "luogo", "paese", "tipo",
    "categorie", "distanze", "organizzatore", "url_ufficiale",
    "url_iscrizione", "scadenza_iscrizione", "stato", "fonti",
    "verificato_il", "prova", "note", "note_interne",
]
CHIAVI_FONTE = ["url", "letto_il"]

ESPRESSIONE_ID = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*$")
ESPRESSIONE_URL = re.compile(r"^https?://\S+$")

SUFFISSO_UID = "@pattinaggiocorsa-calendario-pubblico"
NOME_CALENDARIO = "Pattinaggio corsa — gare ed eventi Master/Amatori"
DESCRIZIONE_CALENDARIO = (
    "Gare ed eventi di pattinaggio corsa aperti alle categorie Master e "
    "Amatori/Fitness in Italia e paesi vicini. Generato automaticamente da "
    "dati/eventi.yaml del repository PattinaggioCorsa-calendario-pubblico."
)
NOME_FILE_ICS = "calendario.ics"
NOME_FILE_HTML = "index.html"
CARTELLA_PAGINA = Path(__file__).resolve().parent.parent / "pagina"   # modello HTML, CSS e altri file statici
PERCORSO_MODELLO_HTML = CARTELLA_PAGINA / "modello_index.html"
LUNGHEZZA_MASSIMA_RIGA_ICS = 75  # ottetti, RFC 5545 §3.1


# ---------------------------------------------------------------------------
# Strutture
# ---------------------------------------------------------------------------

@dataclass
class Fonte:
    url: str
    letto_il: date


@dataclass
class Evento:
    id: str
    nome: str
    data_inizio: date
    data_fine: date
    luogo: str
    paese: str
    tipo: str
    categorie: list[str]
    distanze: list[str]
    organizzatore: str
    url_ufficiale: str
    url_iscrizione: str
    scadenza_iscrizione: date | None
    stato: str
    fonti: list[Fonte]
    verificato_il: date | None
    prova: str
    note: str            # visibili a tutti: finiscono nella descrizione dell'evento
    note_interne: str    # dati di lavoro: restano nell'YAML

    @property
    def pubblicato(self) -> bool:
        return self.stato not in STATI_NON_PUBBLICATI

    @property
    def uid(self) -> str:
        return f"{self.id}{SUFFISSO_UID}"

    @property
    def ultima_modifica(self) -> datetime:
        """Data deterministica: l'ultima data in cui abbiamo toccato l'evento.
        Serve per DTSTAMP/LAST-MODIFIED senza rumore a ogni generazione."""
        date_note = [fonte.letto_il for fonte in self.fonti]
        if self.verificato_il:
            date_note.append(self.verificato_il)
        giorno = max(date_note)
        return datetime(giorno.year, giorno.month, giorno.day, tzinfo=timezone.utc)


@dataclass
class Esito:
    errori: list[str] = field(default_factory=list)
    avvisi: list[str] = field(default_factory=list)

    def errore(self, messaggio: str) -> None:
        self.errori.append(messaggio)

    def avviso(self, messaggio: str) -> None:
        self.avvisi.append(messaggio)


# ---------------------------------------------------------------------------
# 1. Lettura e validazione
# ---------------------------------------------------------------------------

def converti_data(valore, campo: str, contesto: str, esito: Esito, obbligatoria: bool) -> date | None:
    """Accetta una data YAML (già date), una stringa AAAA-MM-GG o "" se facoltativa."""
    if isinstance(valore, datetime):
        return valore.date()
    if isinstance(valore, date):
        return valore
    if valore is None or valore == "":
        if obbligatoria:
            esito.errore(f"{contesto}: '{campo}' è obbligatorio")
        return None
    if isinstance(valore, str):
        try:
            return date.fromisoformat(valore)
        except ValueError:
            esito.errore(f"{contesto}: '{campo}' non è una data AAAA-MM-GG: {valore!r}")
            return None
    esito.errore(f"{contesto}: '{campo}' deve essere una data, trovato {type(valore).__name__}")
    return None


def converti_testo(valore, campo: str, contesto: str, esito: Esito, obbligatorio: bool) -> str:
    if valore is None:
        valore = ""
    if not isinstance(valore, str):
        esito.errore(f"{contesto}: '{campo}' deve essere testo, trovato {type(valore).__name__}")
        return ""
    valore = valore.strip()
    if obbligatorio and not valore:
        esito.errore(f"{contesto}: '{campo}' è obbligatorio e non può essere vuoto")
    return valore


def converti_url(valore, campo: str, contesto: str, esito: Esito, obbligatorio: bool) -> str:
    testo = converti_testo(valore, campo, contesto, esito, obbligatorio)
    if testo and not ESPRESSIONE_URL.match(testo):
        esito.errore(f"{contesto}: '{campo}' non è un URL http(s): {testo!r}")
    return testo


def converti_lista_testi(valore, campo: str, contesto: str, esito: Esito, ammessi: set[str] | None) -> list[str]:
    if valore is None:
        return []
    if not isinstance(valore, list):
        esito.errore(f"{contesto}: '{campo}' deve essere una lista (anche vuota: [])")
        return []
    risultato: list[str] = []
    for indice, voce in enumerate(valore):
        if not isinstance(voce, str) or not voce.strip():
            esito.errore(f"{contesto}: '{campo}[{indice}]' deve essere testo non vuoto")
            continue
        voce = voce.strip()
        if ammessi is not None and voce not in ammessi:
            esito.errore(f"{contesto}: '{campo}' contiene {voce!r}; ammessi: {sorted(ammessi)}")
            continue
        if voce in risultato:
            esito.errore(f"{contesto}: '{campo}' contiene {voce!r} due volte")
            continue
        risultato.append(voce)
    return risultato


def converti_fonti(valore, contesto: str, esito: Esito) -> list[Fonte]:
    if not isinstance(valore, list) or not valore:
        esito.errore(f"{contesto}: 'fonti' deve essere una lista con almeno una voce (url + letto_il)")
        return []
    fonti: list[Fonte] = []
    for indice, voce in enumerate(valore):
        sotto_contesto = f"{contesto}, fonti[{indice}]"
        if not isinstance(voce, dict):
            esito.errore(f"{sotto_contesto}: deve essere una mappa con 'url' e 'letto_il'")
            continue
        sconosciute = set(voce) - set(CHIAVI_FONTE)
        mancanti = set(CHIAVI_FONTE) - set(voce)
        if sconosciute:
            esito.errore(f"{sotto_contesto}: chiavi sconosciute {sorted(sconosciute)}")
        if mancanti:
            esito.errore(f"{sotto_contesto}: chiavi mancanti {sorted(mancanti)}")
            continue
        url = converti_url(voce.get("url"), "url", sotto_contesto, esito, obbligatorio=True)
        letto_il = converti_data(voce.get("letto_il"), "letto_il", sotto_contesto, esito, obbligatoria=True)
        if url and letto_il:
            fonti.append(Fonte(url=url, letto_il=letto_il))
    return fonti


def converti_evento(grezzo, posizione: int, esito: Esito) -> Evento | None:
    contesto = f"evento #{posizione}"
    if not isinstance(grezzo, dict):
        esito.errore(f"{contesto}: deve essere una mappa di campi, trovato {type(grezzo).__name__}")
        return None
    if isinstance(grezzo.get("id"), str) and grezzo["id"].strip():
        contesto = f"evento '{grezzo['id'].strip()}'"

    sconosciute = set(grezzo) - set(CHIAVI_EVENTO)
    mancanti = set(CHIAVI_EVENTO) - set(grezzo)
    if sconosciute:
        esito.errore(f"{contesto}: chiavi sconosciute {sorted(sconosciute)} (errore di battitura?)")
    if mancanti:
        esito.errore(f"{contesto}: chiavi mancanti {sorted(mancanti)} (anche vuote vanno scritte)")
    if sconosciute or mancanti:
        return None

    errori_prima = len(esito.errori)

    identificativo = converti_testo(grezzo["id"], "id", contesto, esito, obbligatorio=True)
    corrispondenza = ESPRESSIONE_ID.match(identificativo)
    if identificativo and not corrispondenza:
        esito.errore(f"{contesto}: 'id' deve avere la forma AAAA-MM-GG-citta-slug (minuscole, trattini): {identificativo!r}")

    nome = converti_testo(grezzo["nome"], "nome", contesto, esito, obbligatorio=True)
    data_inizio = converti_data(grezzo["data_inizio"], "data_inizio", contesto, esito, obbligatoria=True)
    data_fine = converti_data(grezzo["data_fine"], "data_fine", contesto, esito, obbligatoria=True)
    if data_inizio and data_fine and data_fine < data_inizio:
        esito.errore(f"{contesto}: 'data_fine' ({data_fine}) precede 'data_inizio' ({data_inizio})")
    if data_inizio and corrispondenza and corrispondenza.group(1) != data_inizio.isoformat():
        esito.errore(f"{contesto}: la data nell''id' ({corrispondenza.group(1)}) non coincide con 'data_inizio' ({data_inizio})")

    luogo = converti_testo(grezzo["luogo"], "luogo", contesto, esito, obbligatorio=True)
    paese = converti_testo(grezzo["paese"], "paese", contesto, esito, obbligatorio=True)
    if paese and paese not in PAESI_AMMESSI:
        esito.errore(f"{contesto}: 'paese' {paese!r} fuori perimetro; ammessi: {sorted(PAESI_AMMESSI)} (se il perimetro cambia, aggiorna CLAUDE.md e questo script)")

    tipo = converti_testo(grezzo["tipo"], "tipo", contesto, esito, obbligatorio=True)
    if tipo and tipo not in TIPI_AMMESSI:
        esito.errore(f"{contesto}: 'tipo' {tipo!r} non ammesso; ammessi: {sorted(TIPI_AMMESSI)}")

    categorie = converti_lista_testi(grezzo["categorie"], "categorie", contesto, esito, CATEGORIE_AMMESSE)
    distanze = converti_lista_testi(grezzo["distanze"], "distanze", contesto, esito, None)
    organizzatore = converti_testo(grezzo["organizzatore"], "organizzatore", contesto, esito, obbligatorio=False)
    url_ufficiale = converti_url(grezzo["url_ufficiale"], "url_ufficiale", contesto, esito, obbligatorio=False)
    url_iscrizione = converti_url(grezzo["url_iscrizione"], "url_iscrizione", contesto, esito, obbligatorio=False)
    scadenza_iscrizione = converti_data(grezzo["scadenza_iscrizione"], "scadenza_iscrizione", contesto, esito, obbligatoria=False)

    stato = converti_testo(grezzo["stato"], "stato", contesto, esito, obbligatorio=True)
    if stato and stato not in STATI_AMMESSI:
        esito.errore(f"{contesto}: 'stato' {stato!r} non ammesso; ammessi: {sorted(STATI_AMMESSI)}")

    fonti = converti_fonti(grezzo["fonti"], contesto, esito)
    verificato_il = converti_data(grezzo["verificato_il"], "verificato_il", contesto, esito, obbligatoria=False)
    prova = converti_testo(grezzo["prova"], "prova", contesto, esito, obbligatorio=False)
    note = converti_testo(grezzo["note"], "note", contesto, esito, obbligatorio=False)
    note_interne = converti_testo(grezzo["note_interne"], "note_interne", contesto, esito, obbligatorio=False)

    # Regole di coerenza: chi decide cita la prova.
    if categorie and not prova:
        esito.errore(f"{contesto}: 'categorie' è compilato ma 'prova' è vuota (chi decide cita la prova)")
    if stato in {"confermato", "escluso"}:
        if not prova:
            esito.errore(f"{contesto}: stato '{stato}' richiede una 'prova'")
        if not verificato_il:
            esito.errore(f"{contesto}: stato '{stato}' richiede 'verificato_il'")
    if stato == "confermato" and not categorie:
        esito.errore(f"{contesto}: stato 'confermato' senza 'categorie': cosa abbiamo confermato?")
    if verificato_il and not prova:
        esito.avviso(f"{contesto}: 'verificato_il' è compilato ma 'prova' è vuota")
    if scadenza_iscrizione and data_inizio and scadenza_iscrizione > data_inizio:
        esito.avviso(f"{contesto}: la scadenza iscrizioni ({scadenza_iscrizione}) è dopo l'inizio ({data_inizio})")

    if len(esito.errori) > errori_prima:
        return None
    assert data_inizio is not None and data_fine is not None  # garantito dai controlli sopra
    return Evento(
        id=identificativo, nome=nome, data_inizio=data_inizio, data_fine=data_fine,
        luogo=luogo, paese=paese, tipo=tipo, categorie=categorie, distanze=distanze,
        organizzatore=organizzatore, url_ufficiale=url_ufficiale, url_iscrizione=url_iscrizione,
        scadenza_iscrizione=scadenza_iscrizione, stato=stato, fonti=fonti,
        verificato_il=verificato_il, prova=prova, note=note, note_interne=note_interne,
    )


def carica_eventi(percorso: Path, esito: Esito) -> list[Evento]:
    if not percorso.is_file():
        esito.errore(f"file di ingresso non trovato: {percorso}")
        return []
    try:
        grezzo = yaml.safe_load(percorso.read_text(encoding="utf-8"))
    except yaml.YAMLError as errore:
        esito.errore(f"YAML non valido in {percorso}: {errore}")
        return []
    if grezzo is None:
        esito.avviso(f"{percorso} è vuoto: il calendario non avrà eventi")
        return []
    if not isinstance(grezzo, list):
        esito.errore(f"{percorso}: il contenuto deve essere una lista di eventi, trovato {type(grezzo).__name__}")
        return []

    eventi: list[Evento] = []
    for posizione, voce in enumerate(grezzo, start=1):
        evento = converti_evento(voce, posizione, esito)
        if evento is not None:
            eventi.append(evento)

    visti: dict[str, int] = {}
    for evento in eventi:
        if evento.id in visti:
            esito.errore(f"evento '{evento.id}': id duplicato")
        visti[evento.id] = visti.get(evento.id, 0) + 1
    return eventi


# ---------------------------------------------------------------------------
# 2. Costruzione del calendario
# ---------------------------------------------------------------------------

def formatta_data_it(giorno: date) -> str:
    return giorno.strftime("%d/%m/%Y")


def intervallo_date(evento: Evento) -> str:
    if evento.data_inizio == evento.data_fine:
        return formatta_data_it(evento.data_inizio)
    return f"{formatta_data_it(evento.data_inizio)} – {formatta_data_it(evento.data_fine)}"


def titolo_evento(evento: Evento) -> str:
    return PREFISSO_TITOLO.get(evento.stato, "") + evento.nome


def collegamento_evento(evento: Evento) -> str:
    """Un solo URL per l'evento: il sito ufficiale o il regolamento di gara; in mancanza, la pagina d'iscrizione."""
    return evento.url_ufficiale or evento.url_iscrizione


def descrizione_evento(evento: Evento) -> str:
    """Testo per chi consulta il calendario: poche righe, niente dati di lavoro
    (prova, fonti, stato: lo stato è già nel titolo come prefisso)."""
    righe: list[str] = []
    if evento.tipo == "pattinata":
        prima_riga = "Pattinata non competitiva"
    elif evento.categorie:
        prima_riga = "Categorie ammesse: " + ", ".join(c.capitalize() for c in evento.categorie)
    else:
        prima_riga = "Categorie ammesse: da verificare"
    if evento.distanze:
        prima_riga += " · Distanze: " + ", ".join(evento.distanze)
    righe.append(prima_riga)
    if evento.organizzatore:
        righe.append(f"Organizzatore: {evento.organizzatore}")
    if evento.scadenza_iscrizione:
        righe.append(f"Scadenza iscrizioni: {formatta_data_it(evento.scadenza_iscrizione)}")
    if collegamento := collegamento_evento(evento):
        righe.append(f"URL: {collegamento}")
    if evento.note:
        righe.append(f"Informazioni: {evento.note}")
    return "\n".join(righe)


def costruisci_calendario(eventi: list[Evento], url_base: str) -> Calendar:
    calendario = Calendar()
    calendario.add("prodid", "-//PattinaggioCorsa-calendario-pubblico//genera_ics//IT")
    calendario.add("version", "2.0")
    calendario.add("calscale", "GREGORIAN")
    calendario.add("method", "PUBLISH")
    calendario.add("x-wr-calname", NOME_CALENDARIO)
    calendario.add("x-wr-caldesc", DESCRIZIONE_CALENDARIO)
    calendario.add("x-wr-timezone", "Europe/Rome")
    # Suggerimento di aggiornamento per i client (RFC 7986 + estensione storica).
    calendario.add("refresh-interval", timedelta(hours=12), parameters={"value": "DURATION"})
    calendario.add("x-published-ttl", "PT12H")
    if url_base:
        calendario.add("url", f"{url_base}/{NOME_FILE_ICS}")

    for evento in sorted(eventi, key=lambda e: (e.data_inizio, e.id)):
        if not evento.pubblicato:
            continue
        voce = Event()
        voce.add("uid", evento.uid)
        voce.add("dtstamp", evento.ultima_modifica)
        voce.add("last-modified", evento.ultima_modifica)
        voce.add("dtstart", evento.data_inizio)                      # VALUE=DATE: evento di giornata intera
        voce.add("dtend", evento.data_fine + timedelta(days=1))      # DTEND escluso, come da RFC 5545
        voce.add("summary", titolo_evento(evento))
        voce.add("description", descrizione_evento(evento))
        voce.add("location", f"{evento.luogo} ({evento.paese})")
        if collegamento := collegamento_evento(evento):
            # Proprietà URL (RFC 5545 §3.8.4.6): Calendario di Apple la mostra come campo "URL";
            # Google Calendar la ignora, per questo lo stesso link sta anche nella descrizione.
            voce.add("url", collegamento)
        voce.add("categories", [evento.tipo, *evento.categorie])
        if evento.stato in STATUS_ICAL:
            voce.add("status", STATUS_ICAL[evento.stato])
        voce.add("transp", "TRANSPARENT")   # non segna "occupato" nelle agende
        calendario.add_component(voce)
    return calendario


# ---------------------------------------------------------------------------
# 3. Uscita: file .ics e pagina index.html
# ---------------------------------------------------------------------------

def genera_indice_html(eventi: list[Evento], url_base: str, generato_il: datetime) -> str:
    pubblicati = sorted((e for e in eventi if e.pubblicato), key=lambda e: (e.data_inizio, e.id))
    url_ics_https = f"{url_base}/{NOME_FILE_ICS}" if url_base else NOME_FILE_ICS
    url_ics_webcal = url_ics_https.replace("https://", "webcal://", 1) if url_base else ""

    righe_tabella: list[str] = []
    for evento in pubblicati:
        nome = html.escape(titolo_evento(evento))
        if evento.url_ufficiale:
            nome = f'<a href="{html.escape(evento.url_ufficiale)}">{nome}</a>'
        categorie = ", ".join(evento.categorie) if evento.categorie else "da verificare"
        righe_tabella.append(
            "<tr>"
            f"<td>{html.escape(intervallo_date(evento))}</td>"
            f"<td>{nome}</td>"
            f"<td>{html.escape(evento.luogo)} ({html.escape(evento.paese)})</td>"
            f"<td>{html.escape(evento.tipo)}</td>"
            f"<td>{html.escape(categorie)}</td>"
            f"<td>{html.escape(evento.stato.replace('_', ' '))}</td>"
            "</tr>"
        )
    if not righe_tabella:
        righe_tabella.append('<tr><td colspan="6">Nessun evento pubblicato al momento.</td></tr>')

    blocco_iscrizione = (
        f'<p><a class="bottone" href="{html.escape(url_ics_webcal)}">Iscriviti al calendario (iPhone, iPad, Mac)</a></p>\n'
        f"<p>Su Android/Google Calendar: apri <a href=\"https://calendar.google.com/\">Google Calendar dal computer</a> → "
        f"<em>Altri calendari</em> → <em>Da URL</em> e incolla:<br><code>{html.escape(url_ics_https)}</code><br>"
        f"<small>Google aggiorna le sottoscrizioni ogni 12–24 ore circa.</small></p>"
        if url_base else
        f'<p>File del calendario: <a href="{html.escape(url_ics_https)}">{html.escape(NOME_FILE_ICS)}</a></p>'
    )

    segnaposto = {
        "titolo": html.escape(NOME_CALENDARIO),
        "descrizione": html.escape(DESCRIZIONE_CALENDARIO),
        "blocco_iscrizione": blocco_iscrizione,
        "numero_eventi": str(len(pubblicati)),
        "righe_tabella": "\n".join(righe_tabella),
        "generato_il": generato_il.strftime("%d/%m/%Y alle %H:%M"),
    }
    if not PERCORSO_MODELLO_HTML.is_file():
        raise FileNotFoundError(f"modello della pagina non trovato: {PERCORSO_MODELLO_HTML}")
    pagina = PERCORSO_MODELLO_HTML.read_text(encoding="utf-8")
    mancanti = [chiave for chiave in segnaposto if f"{{{{{chiave}}}}}" not in pagina]
    if mancanti:
        raise ValueError(f"{PERCORSO_MODELLO_HTML}: segnaposto mancanti {mancanti}")
    for chiave, valore in segnaposto.items():
        pagina = pagina.replace(f"{{{{{chiave}}}}}", valore)
    if residui := re.findall(r"\{\{\s*[a-z_]+\s*\}\}", pagina):
        raise ValueError(f"{PERCORSO_MODELLO_HTML}: segnaposto sconosciuti {sorted(set(residui))}")
    return pagina


def file_statici_pagina() -> list[Path]:
    """Tutto ciò che sta in pagina/ tranne il modello: CSS, immagini, favicon…"""
    if not CARTELLA_PAGINA.is_dir():
        return []
    return sorted(p for p in CARTELLA_PAGINA.iterdir() if p.is_file() and p != PERCORSO_MODELLO_HTML and not p.name.startswith("."))


def scrivi_uscita(cartella: Path, calendario: Calendar, pagina: str) -> tuple[Path, Path, list[Path]]:
    cartella.mkdir(parents=True, exist_ok=True)
    percorso_ics = cartella / NOME_FILE_ICS
    percorso_html = cartella / NOME_FILE_HTML
    percorso_ics.write_bytes(calendario.to_ical())
    percorso_html.write_text(pagina, encoding="utf-8")
    copiati: list[Path] = []
    for sorgente in file_statici_pagina():
        destinazione = cartella / sorgente.name
        destinazione.write_bytes(sorgente.read_bytes())
        copiati.append(destinazione)
    return percorso_ics, percorso_html, copiati


# ---------------------------------------------------------------------------
# 4. Verifica dell'uscita: rileggiamo quello che abbiamo scritto
# ---------------------------------------------------------------------------

def verifica_ics(percorso_ics: Path, eventi: list[Evento], esito: Esito) -> None:
    grezzo = percorso_ics.read_bytes()
    if not grezzo:
        esito.errore(f"{percorso_ics}: file vuoto")
        return
    try:
        testo = grezzo.decode("utf-8")
    except UnicodeDecodeError as errore:
        esito.errore(f"{percorso_ics}: non è UTF-8 valido ({errore})")
        return

    righe = testo.split("\r\n")
    if righe and righe[-1] == "":
        righe.pop()
    if "\n" in testo.replace("\r\n", ""):
        esito.errore(f"{percorso_ics}: trovate righe non terminate da CRLF")
    if not righe or righe[0] != "BEGIN:VCALENDAR" or righe[-1] != "END:VCALENDAR":
        esito.errore(f"{percorso_ics}: deve iniziare con BEGIN:VCALENDAR e finire con END:VCALENDAR")
    for numero, riga in enumerate(righe, start=1):
        if len(riga.encode("utf-8")) > LUNGHEZZA_MASSIMA_RIGA_ICS:
            esito.errore(f"{percorso_ics}: riga {numero} supera {LUNGHEZZA_MASSIMA_RIGA_ICS} ottetti (manca il folding)")
            break

    try:
        calendario = Calendar.from_ical(grezzo)
    except Exception as errore:  # noqa: BLE001 — qualunque errore di parsing è un fallimento
        esito.errore(f"{percorso_ics}: non si rilegge come iCalendar ({errore})")
        return

    attesi = {evento.uid: evento for evento in eventi if evento.pubblicato}
    trovati: dict[str, int] = {}
    for componente in calendario.walk("VEVENT"):
        uid = str(componente.get("uid", ""))
        trovati[uid] = trovati.get(uid, 0) + 1
        for proprieta in ("dtstart", "dtend", "summary", "dtstamp"):
            if componente.get(proprieta) is None:
                esito.errore(f"{percorso_ics}: l'evento {uid or '(senza uid)'} non ha {proprieta.upper()}")
        inizio = componente.get("dtstart")
        if inizio is not None and not isinstance(inizio.dt, date):
            esito.errore(f"{percorso_ics}: DTSTART di {uid} non è una data")
        if uid in attesi and inizio is not None and inizio.dt != attesi[uid].data_inizio:
            esito.errore(f"{percorso_ics}: DTSTART di {uid} è {inizio.dt}, atteso {attesi[uid].data_inizio}")

    for uid, conteggio in trovati.items():
        if conteggio > 1:
            esito.errore(f"{percorso_ics}: UID {uid} compare {conteggio} volte")
    mancanti = set(attesi) - set(trovati)
    in_piu = set(trovati) - set(attesi)
    if mancanti:
        esito.errore(f"{percorso_ics}: eventi attesi ma assenti: {sorted(mancanti)}")
    if in_piu:
        esito.errore(f"{percorso_ics}: eventi presenti ma non attesi: {sorted(in_piu)}")


def verifica_html(percorso_html: Path, eventi: list[Evento], copiati: list[Path], esito: Esito) -> None:
    testo = percorso_html.read_text(encoding="utf-8")
    if NOME_FILE_ICS not in testo:
        esito.errore(f"{percorso_html}: non contiene il collegamento a {NOME_FILE_ICS}")
    for copiato in copiati:
        sorgente = CARTELLA_PAGINA / copiato.name
        if not copiato.is_file() or copiato.stat().st_size != sorgente.stat().st_size:
            esito.errore(f"{copiato}: copia di {sorgente} mancante o incompleta")
    for riferimento in re.findall(r'(?:href|src)="([^"/:]+\.(?:css|js|png|svg|ico|jpg|webp))"', testo):
        if not (percorso_html.parent / riferimento).is_file():
            esito.errore(f"{percorso_html}: fa riferimento a '{riferimento}' che non è nella cartella di uscita (va messo in {CARTELLA_PAGINA})")
    for evento in eventi:
        if evento.pubblicato and html.escape(evento.nome) not in testo:
            esito.errore(f"{percorso_html}: manca l'evento '{evento.id}'")


# ---------------------------------------------------------------------------
# Programma principale
# ---------------------------------------------------------------------------

def stampa_rapporto(eventi: list[Evento], esito: Esito, percorso_ics: Path | None) -> None:
    pubblicati = [e for e in eventi if e.pubblicato]
    per_stato: dict[str, int] = {}
    for evento in eventi:
        per_stato[evento.stato] = per_stato.get(evento.stato, 0) + 1
    print("Rapporto genera_ics")
    print(f"  eventi letti:      {len(eventi)}")
    print(f"  eventi pubblicati: {len(pubblicati)}")
    for stato in sorted(per_stato):
        print(f"    - {stato}: {per_stato[stato]}")
    if percorso_ics is not None and percorso_ics.exists():
        print(f"  file scritto:      {percorso_ics} ({percorso_ics.stat().st_size} byte)")
        print(f"  file di pagina:    {', '.join(p.name for p in file_statici_pagina()) or 'nessuno'}")
    for avviso in esito.avvisi:
        print(f"  AVVISO: {avviso}")
    for errore in esito.errori:
        print(f"  ERRORE: {errore}")


def principale(argomenti: list[str] | None = None) -> int:
    analizzatore = argparse.ArgumentParser(description="Genera calendario.ics e index.html da dati/eventi.yaml")
    analizzatore.add_argument("--ingresso", type=Path, default=Path("dati/eventi.yaml"), help="file YAML degli eventi")
    analizzatore.add_argument("--uscita", type=Path, default=Path("uscita"), help="cartella dove scrivere calendario.ics e index.html")
    analizzatore.add_argument("--url-base", default="", help="URL pubblico della cartella (es. https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico); senza, i collegamenti sono relativi")
    opzioni = analizzatore.parse_args(argomenti)

    url_base = opzioni.url_base.strip().rstrip("/")
    if url_base and not url_base.startswith("https://"):
        print(f"ERRORE: --url-base deve iniziare con https:// (trovato {url_base!r})", file=sys.stderr)
        return 2

    esito = Esito()
    eventi = carica_eventi(opzioni.ingresso, esito)
    if esito.errori:
        stampa_rapporto(eventi, esito, None)
        return 1
    if not url_base:
        esito.avviso("nessun --url-base: la pagina avrà collegamenti relativi e nessun link webcal://")

    calendario = costruisci_calendario(eventi, url_base)
    pagina = genera_indice_html(eventi, url_base, datetime.now(timezone.utc))
    percorso_ics, percorso_html, copiati = scrivi_uscita(opzioni.uscita, calendario, pagina)

    verifica_ics(percorso_ics, eventi, esito)
    verifica_html(percorso_html, eventi, copiati, esito)
    stampa_rapporto(eventi, esito, percorso_ics)
    return 1 if esito.errori else 0


if __name__ == "__main__":
    sys.exit(principale())
