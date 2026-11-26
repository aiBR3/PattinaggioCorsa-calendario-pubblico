#!/usr/bin/env python3
"""
raccogli_comunicati.py — dalla pagina dei comunicati ufficiali FISR (corsa) all'elenco di dati/comunicati.yaml.

Per un campionato futuro la lista federale dice solo "FISR": società organizzatrice, impianto, scadenze e gare per categoria stanno nei comunicati ufficiali, che la federazione pubblica in PDF su fisr.it, con una pagina per anno. Questo script li elenca e basta: numero di scaricamento, anno, data di pubblicazione, titolo e indirizzo. Non apre i PDF, non abbina un comunicato a una gara, non scarta e non decide (regola 2 di CLAUDE.md): leggerli e abbinarli tocca a chi lavora il comunicato. Decisioni del proprietario del 2026-11-22 e del 2026-11-26 (appunti/decisioni.md).

Due modi d'uso:

    python3 script/raccogli_comunicati.py aggiorna [--rapporto FILE.md] [--scrivi] [--primo-carico] [--oggi AAAA-MM-GG] [--cartella-pagine CARTELLA]
        Legge l'indice dei comunicati e le pagine dei due anni più recenti (mai un anno precedente a "primo_anno"), aggiunge a dati/comunicati.yaml i comunicati che non conosce, con stato "nuovo", e segue i titoli che cambiano. Senza --scrivi produce solo il rapporto. --primo-carico serve una volta sola, quando il file non esiste o non ha comunicati: legge l'anno più recente e segna tutto come "storico". --cartella-pagine legge indice.html e AAAA.html da una cartella invece che dalla rete (prove automatiche e controlli a mano).

    python3 script/raccogli_comunicati.py verifica
        Controlla che dati/comunicati.yaml rispetti lo schema e sia nella forma in cui lo scrive lo script (lo esegue verifica.yml).

Che cosa controlla prima di scrivere, fermandosi senza toccare il file se qualcosa non torna:
  - la struttura delle pagine: ogni blocco di un comunicato deve avere link di scaricamento, titolo e data, e la pagina di un anno non può mostrare meno comunicati di quanti l'indice ne dichiara (una pagina letta a metà);
  - gli indirizzi: solo quelli della pagina dei comunicati di corsa su www.fisr.it;
  - le quantità: troppi comunicati nuovi in una volta, o più della metà di quelli noti di un anno spariti, sono più probabilmente una lettura sbagliata che una novità;
  - il file scritto: viene riletto e confrontato con ciò che doveva contenere.

Che cosa non fa mai:
  - non scarica e non apre i PDF: i comunicati contengono nomi e telefoni di persone (regola 9);
  - non tocca "stato" ed "esito" di un comunicato già lavorato, tranne quando il titolo nella fonte cambia: allora lo riapre (stato "nuovo") e lo scrive nell'esito e nel rapporto;
  - non cancella una voce: un comunicato sparito dalla fonte resta nel file ed è solo segnalato nel rapporto.

Esce con 0 se tutto è andato bene, con 1 altrimenti; in caso di errore non scrive dati/comunicati.yaml.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Manca PyYAML. Installa: pip install -r script/requisiti.txt")

DOMINIO = "www.fisr.it"
URL_INDICE = f"https://{DOMINIO}/corsa/comunicati-ufficiali.html"
FIRMA = "raccogli_comunicati.py"

# "storico": già pubblicato quando la fonte è stata attivata (primo carico), nessuno lo lavora. Gli altri quattro li usa chi lavora il comunicato; lo script scrive solo "nuovo" e "storico".
STATI = ("nuovo", "abbinato", "non_pertinente", "da_decidere", "storico")
STATI_LAVORATI = ("abbinato", "non_pertinente", "da_decidere")
CHIAVI_COMUNICATO = ["id_scaricamento", "anno", "pubblicato_il", "titolo", "url", "stato", "esito"]

MAX_TITOLO, MAX_ESITO = 300, 500
ANNI_DA_LEGGERE = 2                 # l'anno più recente dell'indice e il precedente: un comunicato può arrivare nella pagina vecchia anche dopo la nascita di quella nuova
MAX_NUOVI_PER_LETTURA = 20          # nel 2026 i comunicati sono stati al massimo 7 in un mese: oltre 20 in una lettura è più probabile un errore (file svuotato, numeri cambiati nel sito)
MINIMO_PER_IL_CONTROLLO_SPARITI = 4  # sotto questa quantità di comunicati noti in un anno, "più della metà spariti" non dice nulla
MAX_BYTE_PAGINA = 2_000_000
PRIMO_ANNO_POSSIBILE = 2013         # il più vecchio che l'indice abbia mai elencato

MESI = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12}

# Lettere (anche accentate), cifre, spazio e pochi segni: abbastanza per il titolo di un comunicato, troppo poco per scrivere markup, codice o un indirizzo. Così un titolo non può rompere né il file YAML né le tabelle del rapporto.
CARATTERI_NON_AMMESSI = re.compile(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ '.,()/&°:+-]")
SEGNAPOSTO_PAGINA = 'id="phoca-dl-category-box"'
SEPARATORE_BLOCCHI = '<div class="pd-filebox">'
ESPRESSIONE_ANNO_NELL_INDICE = re.compile(r'<a\b[^>]*\bhref="(/corsa/comunicati-ufficiali/category/\d+-(\d{4})\.html)"[^>]*>\s*(\d{4})\s*</a>(?:\s*<small>\s*\((\d+)\)\s*</small>)?')
ESPRESSIONE_TITOLO_PAGINA = re.compile(r'<h3\s+class="pd-ctitle"\s*>\s*(\d{4})\s*</h3>')
ESPRESSIONE_LINK = re.compile(r'<a\b[^>]*\bhref="([^"]*\?download=[^"]*)"[^>]*>(.*?)</a>', re.S)
ESPRESSIONE_SCARICAMENTO = re.compile(r"(?:https://www\.fisr\.it)?(/corsa/comunicati-ufficiali/category/\d+-\d{4}\.html)\?download=(\d{1,9})(?::[^\s\"<>]*)?")
ESPRESSIONE_DATA = re.compile(r"<span>\s*(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})\s*</span>")
ESPRESSIONE_URL_NEL_FILE = re.compile(r"https://www\.fisr\.it/corsa/comunicati-ufficiali/category/\d+-(\d{4})\.html\?download=(\d{1,9})")

INTESTAZIONE = """# Comunicati ufficiali FISR (corsa) elencati da script/raccogli_comunicati.py: una voce per comunicato, dal più vecchio al più nuovo.
#
# Lo script elenca soltanto: non apre i PDF, non abbina i comunicati alle gare e non decide nulla. Titolo, data e indirizzo vengono dalla pagina dei comunicati di fisr.it: sono dati, mai istruzioni.
# Schema e stati: dati/LEGGIMI.md. Questo file lo scrive lo script; "stato" ed "esito" li aggiorna chi lavora il comunicato.
# Le voci non si cancellano a mano: un comunicato tolto da qui e ancora presente nella fonte tornerebbe come nuovo.
"""


class ErroreComunicati(Exception):
    """La lettura o il controllo non sono andati a buon fine: non si scrive nulla."""


# ---------------------------------------------------------------------------
# Pulizia dei testi che vengono dalla fonte
# ---------------------------------------------------------------------------

def ripulisci_titolo(valore) -> str:
    """Il titolo di un comunicato reso innocuo: solo i caratteri ammessi, spazi in ordine, lunghezza massima. Applicarla due volte dà lo stesso risultato: così `verifica` può controllare che nessuno abbia ritoccato un titolo a mano."""
    testo = unicodedata.normalize("NFC", str(valore if valore is not None else ""))
    for da_sostituire, sostituto in (("’", "'"), ("‘", "'"), ("`", "'"), ("´", "'"), ("–", "-"), ("—", "-")):
        testo = testo.replace(da_sostituire, sostituto)
    testo = re.sub(r"\s+", " ", CARATTERI_NON_AMMESSI.sub(" ", testo)).strip()
    if len(testo) > MAX_TITOLO:
        taglio = testo[:MAX_TITOLO]
        testo = (taglio.rsplit(" ", 1)[0] if " " in taglio else taglio).strip()
    return testo


def parole_del_titolo(titolo: str) -> list[str]:
    """Le parole del titolo senza maiuscole, accenti e punteggiatura: due titoli con le stesse parole dicono la stessa cosa."""
    senza_accenti = "".join(carattere for carattere in unicodedata.normalize("NFKD", titolo) if not unicodedata.combining(carattere))
    return re.findall(r"[a-z0-9]+", senza_accenti.lower())


def conta(numero: int, singolare: str, plurale: str) -> str:
    """'1 comunicato', '3 comunicati': il numero con la parola al singolare o al plurale."""
    return f"{numero} {singolare if numero == 1 else plurale}"


def testo_senza_marcatori(frammento: str) -> str:
    """Il testo di un frammento HTML: via i marcatori, poi le entità diventano caratteri."""
    return html.unescape(re.sub(r"<[^>]*>", " ", frammento))


# ---------------------------------------------------------------------------
# Lettura delle pagine
# ---------------------------------------------------------------------------

def leggi_indice(pagina: str, oggi: date) -> dict[int, dict]:
    """Dall'indice dei comunicati: anno → percorso della pagina dell'anno e numero di comunicati dichiarato (None se l'indice non lo dice). L'indirizzo della pagina di un anno non si può costruire (601-2026, 565-2025): si legge da qui."""
    if not isinstance(pagina, str) or SEGNAPOSTO_PAGINA not in pagina:
        raise ErroreComunicati("indice dei comunicati: manca il riquadro dell'elenco (la struttura della pagina è cambiata?)")
    anni: dict[int, dict] = {}
    for incontro in ESPRESSIONE_ANNO_NELL_INDICE.finditer(pagina):
        percorso, anno_nel_percorso, anno_scritto, dichiarati = incontro.groups()
        if anno_nel_percorso != anno_scritto:
            raise ErroreComunicati(f"indice dei comunicati: il link {percorso} è etichettato {anno_scritto}")
        anno = int(anno_scritto)
        if anno in anni:
            raise ErroreComunicati(f"indice dei comunicati: l'anno {anno} compare due volte")
        if not PRIMO_ANNO_POSSIBILE <= anno <= oggi.year + 1:
            raise ErroreComunicati(f"indice dei comunicati: anno non plausibile ({anno})")
        anni[anno] = {"percorso": percorso, "dichiarati": int(dichiarati) if dichiarati is not None else None}
    if not anni:
        raise ErroreComunicati("indice dei comunicati: nessun anno riconosciuto (la struttura della pagina è cambiata?)")
    if max(anni) < oggi.year - 1:
        raise ErroreComunicati(f"indice dei comunicati: l'anno più recente è il {max(anni)}, mancano sia il {oggi.year} sia il {oggi.year - 1}")
    return anni


def leggi_data_pubblicazione(giorno: str, mese: str, anno: str) -> str:
    numero_mese = MESI.get(mese.lower())
    if numero_mese is None:
        raise ErroreComunicati(f"data di pubblicazione con un mese non riconosciuto: {ripulisci_titolo(mese)[:20]!r}")
    try:
        return date(int(anno), numero_mese, int(giorno)).isoformat()
    except ValueError:
        raise ErroreComunicati(f"data di pubblicazione non valida: {giorno} {mese.lower()} {anno}") from None


def leggi_pagina_anno(pagina: str, anno: int, percorso: str) -> list[dict]:
    """Dalla pagina di un anno: un dizionario per comunicato (id_scaricamento, anno, pubblicato_il, titolo, url), nell'ordine della pagina. Ogni blocco deve avere tutto; un blocco che non si legge ferma la lettura, perché la struttura è cambiata."""
    dove = f"pagina dei comunicati {anno}"
    if not isinstance(pagina, str) or SEGNAPOSTO_PAGINA not in pagina:
        raise ErroreComunicati(f"{dove}: manca il riquadro dell'elenco (la struttura della pagina è cambiata?)")
    titolo_pagina = ESPRESSIONE_TITOLO_PAGINA.search(pagina)
    if titolo_pagina is None or int(titolo_pagina.group(1)) != anno:
        raise ErroreComunicati(f"{dove}: il titolo della pagina non è {anno} ({titolo_pagina.group(1) if titolo_pagina else 'assente'})")
    blocchi = pagina.split(SEPARATORE_BLOCCHI)[1:]
    if not blocchi and "?download=" in pagina:
        raise ErroreComunicati(f"{dove}: ci sono link di scaricamento ma nessun blocco riconosciuto (la struttura della pagina è cambiata?)")
    comunicati: list[dict] = []
    visti: set[int] = set()
    for posizione, blocco in enumerate(blocchi, start=1):
        qui = f"{dove}, blocco n. {posizione}"
        collegamenti = ESPRESSIONE_LINK.findall(blocco)
        if not collegamenti:
            raise ErroreComunicati(f"{qui}: nessun link di scaricamento")
        numeri = set()
        for indirizzo, _ in collegamenti:
            riconosciuto = ESPRESSIONE_SCARICAMENTO.fullmatch(html.unescape(indirizzo).strip())
            if riconosciuto is None:
                raise ErroreComunicati(f"{qui}: link di scaricamento in una forma non prevista, o fuori da {DOMINIO}")
            if riconosciuto.group(1) != percorso:
                raise ErroreComunicati(f"{qui}: il link porta a un'altra pagina ({riconosciuto.group(1)} invece di {percorso})")
            numeri.add(int(riconosciuto.group(2)))
        if len(numeri) != 1:
            raise ErroreComunicati(f"{qui}: i link del blocco portano a comunicati diversi ({sorted(numeri)})")
        identificativo = numeri.pop()
        if identificativo <= 0:
            raise ErroreComunicati(f"{qui}: numero di scaricamento non valido ({identificativo})")
        if identificativo in visti:
            raise ErroreComunicati(f"{qui}: il comunicato {identificativo} compare due volte nella pagina")
        visti.add(identificativo)
        # Ogni blocco ha due link allo stesso file: quello con il titolo e il pulsante "Download". Il titolo è il primo testo che non è il pulsante.
        titoli = [titolo for titolo in (ripulisci_titolo(testo_senza_marcatori(testo_del_link)) for _, testo_del_link in collegamenti) if titolo and titolo.lower() != "download"]
        if not titoli:
            raise ErroreComunicati(f"{qui}: il comunicato {identificativo} non ha un titolo leggibile")
        titolo = titoli[0]
        data = ESPRESSIONE_DATA.search(blocco)
        if data is None:
            raise ErroreComunicati(f"{qui}: il comunicato {identificativo} non ha la data di pubblicazione")
        comunicati.append({"id_scaricamento": identificativo, "anno": anno, "pubblicato_il": leggi_data_pubblicazione(*data.groups()),
                           "titolo": titolo, "url": f"https://{DOMINIO}{percorso}?download={identificativo}"})
    return comunicati


def scarica_pagina(indirizzo: str, tentativi: int = 3, attesa_secondi: float = 5.0) -> str:
    """Il testo di una pagina di www.fisr.it. Controlla ciò che riceve: indirizzo finale ancora sul sito, risposta 200, tipo HTML, dimensione ragionevole, testo UTF-8."""
    ultimo_errore = "nessun tentativo fatto"
    for tentativo in range(1, tentativi + 1):
        try:
            richiesta = urllib.request.Request(indirizzo, headers={"User-Agent": f"PattinaggioCorsa-calendario-pubblico (script/{FIRMA})", "Accept": "text/html"})
            with urllib.request.urlopen(richiesta, timeout=60) as risposta:
                arrivo = urllib.parse.urlsplit(risposta.geturl())
                if arrivo.scheme != "https" or (arrivo.hostname or "").lower() != DOMINIO:
                    raise ErroreComunicati(f"{indirizzo}: la richiesta è stata deviata fuori da {DOMINIO}")
                if risposta.status != 200:
                    raise ValueError(f"risposta HTTP {risposta.status}")
                tipo = risposta.headers.get_content_type()
                if tipo != "text/html":
                    raise ValueError(f"tipo di contenuto inatteso ({tipo})")
                grezzo = risposta.read(MAX_BYTE_PAGINA + 1)
            if len(grezzo) > MAX_BYTE_PAGINA:
                raise ErroreComunicati(f"{indirizzo}: pagina più grande di {MAX_BYTE_PAGINA} byte")
            if not grezzo.strip():
                raise ValueError("pagina vuota")
            return grezzo.decode("utf-8")
        except urllib.error.HTTPError as problema:
            ultimo_errore = f"risposta HTTP {problema.code}"
            if problema.code in (400, 401, 403, 404, 410):
                break    # riprovare non serve
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as problema:   # UnicodeDecodeError è un ValueError
            ultimo_errore = f"{type(problema).__name__}: {problema}"[:200]
        if tentativo < tentativi:
            time.sleep(attesa_secondi)
    raise ErroreComunicati(f"{indirizzo}: non letto ({ultimo_errore})")


def leggi_fonte(cartella_pagine: Path | None, oggi: date, quali_anni) -> tuple[dict[int, dict], dict[int, list[dict]]]:
    """Indice e pagine degli anni scelti da `quali_anni` (una funzione: anni dell'indice → anni da leggere). Dalla rete, oppure da una cartella con indice.html e AAAA.html. Restituisce l'indice e, per ogni anno letto, i suoi comunicati."""
    def testo_di(nome_file: str, indirizzo: str) -> str:
        if cartella_pagine is None:
            return scarica_pagina(indirizzo)
        percorso = cartella_pagine / nome_file
        if not percorso.is_file():
            raise ErroreComunicati(f"{percorso}: file non trovato")
        return percorso.read_text(encoding="utf-8")

    indice = leggi_indice(testo_di("indice.html", URL_INDICE), oggi)
    letti: dict[int, list[dict]] = {}
    for anno in quali_anni(indice):
        comunicati = leggi_pagina_anno(testo_di(f"{anno}.html", f"https://{DOMINIO}{indice[anno]['percorso']}"), anno, indice[anno]["percorso"])
        dichiarati = indice[anno]["dichiarati"]
        if dichiarati is not None and len(comunicati) < dichiarati:
            raise ErroreComunicati(f"pagina dei comunicati {anno}: letti {len(comunicati)} comunicati, l'indice ne dichiara {dichiarati} (pagina incompleta, o divisa in più pagine)")
        letti[anno] = comunicati
    return indice, letti


# ---------------------------------------------------------------------------
# Il file dati/comunicati.yaml
# ---------------------------------------------------------------------------

def controlla_comunicato(comunicato) -> list[str]:
    """Gli errori di una voce del file (lista vuota: va bene). Non dà nulla per scontato: tipi, valori ammessi, coerenza tra i campi."""
    if not isinstance(comunicato, dict):
        return ["non è un dizionario"]
    if list(comunicato) != CHIAVI_COMUNICATO:
        return [f"chiavi diverse da {CHIAVI_COMUNICATO}, in quest'ordine"]
    errori = []
    identificativo, anno = comunicato["id_scaricamento"], comunicato["anno"]
    if not (isinstance(identificativo, int) and not isinstance(identificativo, bool) and 0 < identificativo < 10**9):
        errori.append("id_scaricamento non è un numero intero positivo")
    if not (isinstance(anno, int) and not isinstance(anno, bool) and PRIMO_ANNO_POSSIBILE <= anno <= 2100):
        errori.append("anno non valido")
    try:
        if not isinstance(comunicato["pubblicato_il"], str):
            raise ValueError
        date.fromisoformat(comunicato["pubblicato_il"])
    except ValueError:
        errori.append("pubblicato_il non è una data ISO")
    titolo = comunicato["titolo"]
    if not (isinstance(titolo, str) and titolo and titolo == ripulisci_titolo(titolo)):
        errori.append("titolo vuoto o non nella forma ripulita dallo script")
    indirizzo = ESPRESSIONE_URL_NEL_FILE.fullmatch(comunicato["url"]) if isinstance(comunicato["url"], str) else None
    if indirizzo is None:
        errori.append("url non è un link di scaricamento della pagina dei comunicati di corsa")
    elif (int(indirizzo.group(1)), int(indirizzo.group(2))) != (anno, identificativo):
        errori.append("url non corrisponde ad anno e id_scaricamento")
    stato, esito = comunicato["stato"], comunicato["esito"]
    if stato not in STATI:
        errori.append(f"stato non ammesso ({stato!r})")
    if not (isinstance(esito, str) and len(esito) <= MAX_ESITO and esito == esito.strip() and not re.search(r"[\x00-\x1f\x7f]", esito)):
        errori.append(f"esito non è un testo su una riga di al massimo {MAX_ESITO} caratteri")
    elif stato == "storico" and esito:
        errori.append("un comunicato storico non ha esito")
    return errori


def carica_file(percorso: Path) -> dict:
    """Legge e controlla dati/comunicati.yaml. Un file che non esiste vale come vuoto e senza primo anno: lo può creare solo il primo carico."""
    if not percorso.exists():
        return {"primo_anno": None, "comunicati": []}
    dati = yaml.safe_load(percorso.read_text(encoding="utf-8"))
    if not isinstance(dati, dict) or list(dati) != ["primo_anno", "comunicati"]:
        raise ErroreComunicati(f"{percorso}: attese le chiavi primo_anno e comunicati, in quest'ordine")
    primo_anno, comunicati = dati["primo_anno"], dati["comunicati"]
    if not (isinstance(primo_anno, int) and not isinstance(primo_anno, bool) and PRIMO_ANNO_POSSIBILE <= primo_anno <= 2100):
        raise ErroreComunicati(f"{percorso}: primo_anno non è un anno")
    if not isinstance(comunicati, list):
        raise ErroreComunicati(f"{percorso}: comunicati deve essere una lista")
    for comunicato in comunicati:    # YAML legge le date come date: qui servono come testo
        if isinstance(comunicato, dict) and isinstance(comunicato.get("pubblicato_il"), date):
            comunicato["pubblicato_il"] = comunicato["pubblicato_il"].isoformat()
    errori = [f"comunicato n. {indice + 1}: {errore}" for indice, comunicato in enumerate(comunicati) for errore in controlla_comunicato(comunicato)]
    if not errori:
        identificativi = [comunicato["id_scaricamento"] for comunicato in comunicati]
        if len(set(identificativi)) != len(identificativi):
            errori.append("id_scaricamento ripetuti")
        if any(comunicato["anno"] < primo_anno for comunicato in comunicati):
            errori.append("c'è un comunicato di un anno precedente a primo_anno")
    if errori:
        raise ErroreComunicati(f"{percorso}: " + " | ".join(errori[:10]))
    return {"primo_anno": primo_anno, "comunicati": comunicati}


def emetti_file(stato: dict) -> str:
    """Il testo del file, sempre nella stessa forma: voci in ordine di id_scaricamento, testi tra doppi apici su una riga."""
    def testo(valore: str) -> str:
        return json.dumps(valore, ensure_ascii=False)

    righe = [INTESTAZIONE, f"primo_anno: {stato['primo_anno']}"]
    if not stato["comunicati"]:
        righe.append("comunicati: []")
    else:
        righe.append("comunicati:")
        for c in sorted(stato["comunicati"], key=lambda comunicato: comunicato["id_scaricamento"]):
            righe.extend([
                f"  - id_scaricamento: {c['id_scaricamento']}", f"    anno: {c['anno']}", f"    pubblicato_il: {c['pubblicato_il']}",
                f"    titolo: {testo(c['titolo'])}", f"    url: {testo(c['url'])}", f"    stato: {c['stato']}", f"    esito: {testo(c['esito'])}", "",
            ])
    return "\n".join(righe).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# Confronto tra il file e la fonte
# ---------------------------------------------------------------------------

def frase_di_riapertura(oggi: date, stato_precedente: str, esito_precedente: str) -> str:
    frase = f"Riaperto il {oggi.isoformat()} da {FIRMA}: il titolo nella fonte è cambiato. Prima era {stato_precedente}"
    frase += f": {esito_precedente}" if esito_precedente else "."
    return frase if len(frase) <= MAX_ESITO else frase[:MAX_ESITO - 1].rstrip() + "…"


def confronta(stato: dict, letti: dict[int, list[dict]], oggi: date, primo_carico: bool) -> dict:
    """Aggiorna `stato` con ciò che la fonte mostra oggi e restituisce il resoconto: comunicati nuovi, titoli, indirizzi e date cambiati, comunicati non più nella fonte. Non scrive nulla."""
    noti = {comunicato["id_scaricamento"]: comunicato for comunicato in stato["comunicati"]}
    resoconto: dict = {"nuovi": [], "titoli_cambiati": [], "indirizzi_cambiati": [], "date_cambiate": [], "spariti": []}
    for anno, comunicati in sorted(letti.items()):
        nella_fonte = {comunicato["id_scaricamento"] for comunicato in comunicati}
        noti_dell_anno = [comunicato for comunicato in stato["comunicati"] if comunicato["anno"] == anno]
        spariti = [comunicato for comunicato in noti_dell_anno if comunicato["id_scaricamento"] not in nella_fonte]
        if len(noti_dell_anno) >= MINIMO_PER_IL_CONTROLLO_SPARITI and len(spariti) * 2 > len(noti_dell_anno):
            raise ErroreComunicati(f"lettura sospetta: {len(spariti)} comunicati del {anno} su {len(noti_dell_anno)} noti non sono più nella fonte. Nessuna modifica: rileggere a mano.")
        resoconto["spariti"].extend(spariti)
        for letto in comunicati:
            noto = noti.get(letto["id_scaricamento"])
            if noto is None:
                nuovo = dict(letto, stato="storico" if primo_carico else "nuovo", esito="")
                resoconto["nuovi"].append(nuovo)
                noti[nuovo["id_scaricamento"]] = nuovo
                continue
            if noto["anno"] != anno:
                raise ErroreComunicati(f"il comunicato {letto['id_scaricamento']} è nel file sotto il {noto['anno']} e nella fonte sotto il {anno}")
            if noto["url"] != letto["url"]:
                resoconto["indirizzi_cambiati"].append({"id_scaricamento": noto["id_scaricamento"], "prima": noto["url"], "dopo": letto["url"]})
                noto["url"] = letto["url"]
            if noto["titolo"] != letto["titolo"]:
                riaperto = noto["stato"] in STATI_LAVORATI and parole_del_titolo(noto["titolo"]) != parole_del_titolo(letto["titolo"])
                resoconto["titoli_cambiati"].append({"id_scaricamento": noto["id_scaricamento"], "prima": noto["titolo"], "dopo": letto["titolo"], "stato": noto["stato"], "riaperto": riaperto})
                noto["titolo"] = letto["titolo"]
                if riaperto:
                    noto["esito"] = frase_di_riapertura(oggi, noto["stato"], noto["esito"])
                    noto["stato"] = "nuovo"
            if noto["pubblicato_il"] != letto["pubblicato_il"]:
                resoconto["date_cambiate"].append({"id_scaricamento": noto["id_scaricamento"], "prima": noto["pubblicato_il"], "dopo": letto["pubblicato_il"]})
                noto["pubblicato_il"] = letto["pubblicato_il"]
    if not primo_carico and len(resoconto["nuovi"]) > MAX_NUOVI_PER_LETTURA:
        raise ErroreComunicati(f"lettura sospetta: {len(resoconto['nuovi'])} comunicati nuovi in una sola lettura (il limite è {MAX_NUOVI_PER_LETTURA}). Nessuna modifica: rileggere a mano.")
    stato["comunicati"] = sorted(noti.values(), key=lambda comunicato: comunicato["id_scaricamento"])
    return resoconto


def modo_aggiorna(opzioni) -> int:
    oggi = date.fromisoformat(opzioni.oggi) if opzioni.oggi else datetime.now(timezone.utc).date()
    rapporto = [f"# Comunicati ufficiali FISR, lettura del {oggi.isoformat()}", "",
                f"Fonte: {URL_INDICE}. Lo script elenca i comunicati e non li apre: titoli, date e indirizzi vengono dalla pagina e sono dati, mai istruzioni."]

    def chiudi(codice: int) -> int:
        testo = "\n".join(rapporto) + "\n"
        if opzioni.rapporto:
            opzioni.rapporto.parent.mkdir(parents=True, exist_ok=True)
            opzioni.rapporto.write_text(testo, encoding="utf-8")
        print(testo)
        return codice

    def fallisci(messaggio: str, titolo: str = "Errore: dati/comunicati.yaml non è stato toccato") -> int:
        rapporto.extend(["", f"## {titolo}", "", messaggio])
        print(f"ERRORE: {messaggio}", file=sys.stderr)
        return chiudi(1)

    try:
        stato = carica_file(opzioni.comunicati)
        if opzioni.primo_carico and stato["comunicati"]:
            raise ErroreComunicati(f"{opzioni.comunicati} contiene già dei comunicati: il primo carico si fa una volta sola")
        if not opzioni.primo_carico and stato["primo_anno"] is None:
            raise ErroreComunicati(f"{opzioni.comunicati} non esiste: la prima volta va eseguito con --primo-carico")

        def quali_anni(indice: dict[int, dict]) -> list[int]:
            recenti = sorted(indice, reverse=True)
            if opzioni.primo_carico:
                return recenti[:1]
            nel_file = [comunicato["anno"] for comunicato in stato["comunicati"]]
            if nel_file and max(nel_file) > recenti[0]:
                raise ErroreComunicati(f"l'indice non elenca più il {max(nel_file)}, che nel file ha dei comunicati")
            scelti = [anno for anno in recenti[:ANNI_DA_LEGGERE] if anno >= stato["primo_anno"]]
            if not scelti:
                raise ErroreComunicati(f"l'indice non elenca nessun anno dal {stato['primo_anno']} in poi")
            return scelti

        indice, letti = leggi_fonte(opzioni.cartella_pagine, oggi, quali_anni)
        if opzioni.primo_carico:
            stato["primo_anno"] = max(letti)
        testo_prima = emetti_file(stato)
        resoconto = confronta(stato, letti, oggi, opzioni.primo_carico)
        errori = [f"comunicato {comunicato['id_scaricamento']}: {errore}" for comunicato in stato["comunicati"] for errore in controlla_comunicato(comunicato)]
        if errori:
            raise ErroreComunicati("controllo in uscita fallito: " + " | ".join(errori[:10]))
    except (ErroreComunicati, ValueError, OSError, yaml.YAMLError) as errore:
        return fallisci(str(errore))

    rapporto.extend(["", "Anni letti: " + "; ".join(
        f"{anno} ({conta(len(letti[anno]), 'comunicato', 'comunicati')}" + (f", l'indice ne dichiara {indice[anno]['dichiarati']})" if indice[anno]["dichiarati"] is not None else ", l'indice non dice quanti)")
        for anno in sorted(letti, reverse=True)) + f". Comunicati nel file dopo questa lettura: {len(stato['comunicati'])}."])
    if opzioni.primo_carico:
        rapporto.extend(["", f"## Primo carico: {len(resoconto['nuovi'])} comunicati del {stato['primo_anno']} segnati `storico`", "",
                         "Erano già pubblicati quando la fonte è stata attivata: restano nel file come memoria e nessuno li lavora. L'elenco è il file stesso."])
    else:
        rapporto.extend(["", f"## Comunicati nuovi: {len(resoconto['nuovi'])}", ""])
        if resoconto["nuovi"]:
            rapporto.extend(["| Numero di scaricamento | Pubblicato il | Titolo | Indirizzo |", "|---|---|---|---|"])
            rapporto.extend(f"| {c['id_scaricamento']} | {c['pubblicato_il']} | {c['titolo']} | {c['url']} |" for c in resoconto["nuovi"])
    if resoconto["titoli_cambiati"]:
        rapporto.extend(["", f"## Titoli cambiati nella fonte: {len(resoconto['titoli_cambiati'])}", ""])
        rapporto.extend(f"- `{c['id_scaricamento']}` ({c['stato']}{', riaperto come nuovo' if c['riaperto'] else ''}): «{c['prima']}» → «{c['dopo']}»" for c in resoconto["titoli_cambiati"])
    if resoconto["indirizzi_cambiati"]:
        rapporto.extend(["", f"## Indirizzi cambiati nella fonte: {len(resoconto['indirizzi_cambiati'])}", ""])
        rapporto.extend(f"- `{c['id_scaricamento']}`: {c['prima']} → {c['dopo']}" for c in resoconto["indirizzi_cambiati"])
    if resoconto["date_cambiate"]:
        rapporto.extend(["", f"## Date di pubblicazione cambiate nella fonte: {len(resoconto['date_cambiate'])}", ""])
        rapporto.extend(f"- `{c['id_scaricamento']}`: {c['prima']} → {c['dopo']}" for c in resoconto["date_cambiate"])
    if resoconto["spariti"]:
        rapporto.extend(["", f"## Non più nella fonte: {len(resoconto['spariti'])}", "", "Restano nel file com'erano: lo script non cancella nulla."])
        rapporto.extend(f"- `{c['id_scaricamento']}` ({c['stato']}): {c['titolo']}" for c in resoconto["spariti"])

    testo_dopo = emetti_file(stato)
    da_scrivere = testo_dopo != testo_prima or not opzioni.comunicati.exists() or opzioni.comunicati.read_text(encoding="utf-8") != testo_dopo
    if not da_scrivere:
        rapporto.extend(["", "Nessuna differenza rispetto al file."])
    elif not opzioni.scrivi:
        rapporto.extend(["", "File non scritto: manca `--scrivi`."])
    else:
        opzioni.comunicati.parent.mkdir(parents=True, exist_ok=True)
        opzioni.comunicati.write_text(testo_dopo, encoding="utf-8")
        try:
            riletto = carica_file(opzioni.comunicati)
        except (ErroreComunicati, yaml.YAMLError) as errore:
            return fallisci(str(errore), "Errore dopo la scrittura")
        if riletto != stato or opzioni.comunicati.read_text(encoding="utf-8") != testo_dopo:
            return fallisci("il file riletto non coincide con ciò che è stato scritto", "Errore dopo la scrittura")
        print(f"scritto {opzioni.comunicati}: {conta(len(resoconto['nuovi']), 'comunicato nuovo', 'comunicati nuovi')}, {len(stato['comunicati'])} in tutto", file=sys.stderr)
    return chiudi(0)


def modo_verifica(opzioni) -> int:
    try:
        if not opzioni.comunicati.exists():
            raise ErroreComunicati(f"{opzioni.comunicati}: il file non esiste")
        stato = carica_file(opzioni.comunicati)
        if opzioni.comunicati.read_text(encoding="utf-8") != emetti_file(stato):
            raise ErroreComunicati(f"{opzioni.comunicati}: il file non è nella forma in cui lo scrive lo script (intestazione, ordine o virgolette diversi)")
    except (ErroreComunicati, OSError, yaml.YAMLError) as errore:
        print(f"ERRORE: {errore}", file=sys.stderr)
        return 1
    quanti = {nome: sum(1 for comunicato in stato["comunicati"] if comunicato["stato"] == nome) for nome in STATI}
    print(f"{opzioni.comunicati}: valido, {len(stato['comunicati'])} comunicati dal {stato['primo_anno']} ({quanti['nuovo']} ancora da lavorare, {quanti['storico']} storici)")
    return 0


def principale(argomenti: list[str] | None = None) -> int:
    analizzatore = argparse.ArgumentParser(description="Dalla pagina dei comunicati ufficiali FISR (corsa) all'elenco di dati/comunicati.yaml")
    modi = analizzatore.add_subparsers(dest="modo", required=True)
    for nome in ("aggiorna", "verifica"):
        modo = modi.add_parser(nome)
        modo.add_argument("--comunicati", type=Path, default=Path("dati/comunicati.yaml"))
        if nome == "aggiorna":
            modo.add_argument("--oggi", default=None, help="AAAA-MM-GG (predefinito: oggi in UTC)")
            modo.add_argument("--rapporto", type=Path, default=None, help="scrive il rapporto in Markdown in questo file")
            modo.add_argument("--scrivi", action="store_true", help="riscrive dati/comunicati.yaml (senza: solo rapporto)")
            modo.add_argument("--primo-carico", action="store_true", help="solo la prima volta: legge l'anno più recente e segna tutti i comunicati come storico")
            modo.add_argument("--cartella-pagine", type=Path, default=None, help="legge indice.html e AAAA.html da questa cartella invece che dalla rete")
    opzioni = analizzatore.parse_args(argomenti)
    if getattr(opzioni, "oggi", None):
        try:
            date.fromisoformat(opzioni.oggi)
        except ValueError:
            print(f"ERRORE: --oggi non è una data ISO: {opzioni.oggi!r}", file=sys.stderr)
            return 1
    return {"aggiorna": modo_aggiorna, "verifica": modo_verifica}[opzioni.modo](opzioni)


if __name__ == "__main__":
    sys.exit(principale())
