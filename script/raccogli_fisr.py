#!/usr/bin/env python3
"""
raccogli_fisr.py — raccolta (livello 1) dal calendario corsa di fisr.info.

Legge la lista per stagione (corsa_calendario.php) e, a richiesta, l'indizione di
ogni gara (corsa_trofeo_modulo.php?id_manif=N). Restituisce dati GREZZI in JSON:
non classifica, non scarta, non corregge i nomi. Chi decide è un altro passo.

Uso:
    python3 script/raccogli_fisr.py --uscita log/raccolta.json \
        [--anno 2026] [--anno 2027] [--da 2026-01-01] [--indizioni] [--pausa 0.5]

  --anno N      parametro "anno" di fisr.info: N=2026 dà la stagione 2025/26,
                N=2027 la 2026/27, e così via. Senza --anno: la stagione corrente.
  --da DATA     tiene solo le righe con data di inizio >= DATA (dopo il parsing).
  --indizioni   scarica anche la pagina dell'indizione di ogni gara che ha il link.
  --pausa S     secondi di attesa tra una richiesta e l'altra (educazione verso il sito).
  --scansione-indizioni DA A
                scarica le indizioni con id_manif da DA ad A anche se la lista non le
                linka più (succede per le gare passate e per quelle "non ancora
                autorizzate"): tiene solo quelle complete (data, nome, programma) e nel
                periodo. L'abbinamento alle righe della lista lo fa converti_fisr.py.
  Nota: la pagina ?anno=2026 (stagione 2025/26) contiene anche i mesi della 2026/27;
  chiedere due stagioni consecutive produce righe doppie.

Controlli: la lista deve avere almeno un mese e ogni riga 7 celle; le date vengono
interpretate ma la stringa originale è sempre conservata; ogni anomalia finisce
nel campo "anomalie" della riga, mai scartata in silenzio. Il JSON scritto viene
riletto e contato prima di uscire. Codice di uscita: 0 ok, 1 anomalie gravi, 2 uso.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

URL_BASE = "https://www.fisr.info/attivita/"
URL_LISTA = URL_BASE + "corsa_calendario.php"
URL_MODULO = URL_BASE + "corsa_trofeo_modulo.php?id_manif="
AGENTE_UTENTE = "PattinaggioCorsa-calendario-pubblico/raccolta (+https://github.com/aiBR3/PattinaggioCorsa-calendario-pubblico)"
COLONNE_ATTESE = 7  # Data, Evento, localita', Organizzato da, Scadenza iscrizioni, Termine depennamenti, Dettagli

ESPRESSIONE_MESE = re.compile(r'<div id="t_mese_(\d{4})"[^>]*>(.*?)</div>', re.S)
ESPRESSIONE_RIGA = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
ESPRESSIONE_CELLA = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
ESPRESSIONE_MODULO = re.compile(r"corsa_trofeo_modulo\.php\?id_manif=(\d+)")
ESPRESSIONE_STAGIONE = re.compile(r"Calendario (\d{4})/(\d{2})")
ESPRESSIONE_RIGA_PROGRAMMA = re.compile(r"^(?P<categoria>[^|]+?)\s*\|\s*(?P<sesso>[FM]|M/F|F/M)\s*\|\s*(?P<distanza>[^|]*?)\s*\|\s*(?P<tipo>[^|]*?)\s*\|?$")


@dataclass
class Indizione:
    id_manif: str
    url: str
    scaricata: bool = False
    codifica: str = ""
    denominazione: str = ""
    dal: str = ""                    # AAAA-MM-GG se interpretabile
    al: str = ""
    dal_grezzo: str = ""
    categoria_manifestazione: str = ""   # es. "B"
    disciplina: str = ""                 # es. "pista", "strada"
    societa: str = ""
    campo_gara: str = ""
    orario_inizio: str = ""
    iscrizioni_entro: str = ""
    righe_programma: list[dict] = field(default_factory=list)   # art. 10, grezze
    categorie_programma: list[str] = field(default_factory=list)  # prime celle uniche, nell'ordine
    righe_master_amatori: list[str] = field(default_factory=list)  # qualunque riga con MASTER/AMATORI/FITNESS/OVER
    anomalie: list[str] = field(default_factory=list)


@dataclass
class RigaLista:
    stagione: str
    mese_tabella: str            # AAAA-MM
    data_grezza: str
    data_inizio: str = ""        # AAAA-MM-GG
    data_fine: str = ""
    evento_grezzo: str = ""
    evento: str = ""             # con la codifica riparata, ma senza altre modifiche
    localita: str = ""
    organizzatore: str = ""
    scadenza_iscrizioni_grezza: str = ""
    scadenza_iscrizioni: str = ""
    termine_depennamenti_grezzo: str = ""
    non_autorizzata: bool = False
    formato: str = "7_celle"
    id_manif: str = ""
    url_modulo: str = ""
    anomalie: list[str] = field(default_factory=list)
    indizione: Indizione | None = None


# ---------------------------------------------------------------------------
# Rete
# ---------------------------------------------------------------------------

def scarica(url: str, pausa: float) -> bytes:
    richiesta = urllib.request.Request(url, headers={"User-Agent": AGENTE_UTENTE})
    with urllib.request.urlopen(richiesta, timeout=60) as risposta:
        if risposta.status != 200:
            raise RuntimeError(f"HTTP {risposta.status} per {url}")
        contenuto = risposta.read()
    if pausa > 0:
        time.sleep(pausa)
    if not contenuto:
        raise RuntimeError(f"risposta vuota per {url}")
    return contenuto


def decodifica(grezzo: bytes) -> tuple[str, str]:
    """fisr.info mescola codifiche: la lista è UTF-8 (con BOM), le indizioni no."""
    try:
        return grezzo.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        return grezzo.decode("cp1252", errors="replace"), "cp1252"


def ripara_codifica(testo: str) -> str:
    """Ripara il mojibake tipico ('CITTÃ\\x80' → 'CITTÀ'). Se non è riparabile, lascia com'è."""
    if "Ã" not in testo and "Â" not in testo:
        return testo
    try:
        return testo.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    # Riparazione parola per parola: le parti sane restano com'erano.
    riparato = []
    for parola in testo.split(" "):
        try:
            riparato.append(parola.encode("latin-1").decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            riparato.append(parola)
    return " ".join(riparato)


def ripara_base64(testo: str) -> tuple[str, bool]:
    """A volte la fonte mostra il nome codificato in base64 (es. '1°maggio Ferrara...'): lo decodifica."""
    if not re.fullmatch(r"[A-Za-z0-9+/]{32,}={0,2}", testo):
        return testo, False
    import base64
    try:
        grezzo = base64.b64decode(testo + "=" * (-len(testo) % 4))
    except (ValueError, TypeError):
        return testo, False
    try:
        decodificato = grezzo.decode("utf-8")
    except UnicodeDecodeError:
        decodificato = grezzo.decode("latin-1")
    if not decodificato.isprintable() or len(decodificato) < 5:
        return testo, False
    return decodificato, True


def pulisci_html(frammento: str) -> str:
    testo = re.sub(r"<[^>]+>", " ", frammento)
    testo = ripara_codifica(html.unescape(testo)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", testo).strip()


# ---------------------------------------------------------------------------
# Date
# ---------------------------------------------------------------------------

def interpreta_data_lista(grezza: str, anno: int, mese: int) -> tuple[str, str, list[str]]:
    """'08/11' → un giorno; '28-29/11' → intervallo; '27/02-01/03' → intervallo a cavallo di mesi.
    L'anno viene dal mese della tabella; se il mese finale è minore di quello iniziale, l'anno finale è +1."""
    anomalie: list[str] = []
    grezza = grezza.strip()
    if corrispondenza := re.fullmatch(r"(\d{1,2})/(\d{1,2})", grezza):
        giorno, mese_data = int(corrispondenza[1]), int(corrispondenza[2])
        inizio = fine = (giorno, mese_data)
    elif corrispondenza := re.fullmatch(r"(\d{1,2})-(\d{1,2})/(\d{1,2})", grezza):
        inizio = (int(corrispondenza[1]), int(corrispondenza[3]))
        fine = (int(corrispondenza[2]), int(corrispondenza[3]))
    elif corrispondenza := re.fullmatch(r"(\d{1,2})/(\d{1,2})-(\d{1,2})/(\d{1,2})", grezza):
        inizio = (int(corrispondenza[1]), int(corrispondenza[2]))
        fine = (int(corrispondenza[3]), int(corrispondenza[4]))
    else:
        return "", "", [f"data non interpretabile: {grezza!r}"]

    if inizio[1] != mese:
        anomalie.append(f"il mese della data ({inizio[1]:02d}) non è quello della tabella ({mese:02d})")
    anno_inizio = anno
    anno_fine = anno + 1 if fine[1] < inizio[1] else anno
    try:
        data_inizio = date(anno_inizio, inizio[1], inizio[0])
        data_fine = date(anno_fine, fine[1], fine[0])
    except ValueError as errore:
        return "", "", [f"data non valida ({grezza!r}): {errore}"]
    if data_fine < data_inizio:
        anomalie.append(f"data di fine ({data_fine}) precedente all'inizio ({data_inizio}): probabile refuso nella fonte")
        data_inizio, data_fine = data_fine, data_inizio
    return data_inizio.isoformat(), data_fine.isoformat(), anomalie


def interpreta_data_breve(grezza: str, anno_riferimento: int, mese_riferimento: int) -> str:
    """'27/09' → AAAA-MM-GG, con l'anno del mese di riferimento (anno precedente se la scadenza
    è in un mese successivo a quello della gara, cioè a cavallo d'anno)."""
    corrispondenza = re.fullmatch(r"(\d{1,2})/(\d{1,2})", grezza.strip())
    if not corrispondenza:
        return ""
    giorno, mese = int(corrispondenza[1]), int(corrispondenza[2])
    anno = anno_riferimento - 1 if mese > mese_riferimento else anno_riferimento
    try:
        return date(anno, mese, giorno).isoformat()
    except ValueError:
        return ""


def interpreta_data_indizione(grezza: str) -> str:
    """'08/12/26' → '2026-12-08'."""
    corrispondenza = re.fullmatch(r"(\d{2})/(\d{2})/(\d{2})", grezza.strip())
    if not corrispondenza:
        return ""
    try:
        return date(2000 + int(corrispondenza[3]), int(corrispondenza[2]), int(corrispondenza[1])).isoformat()
    except ValueError:
        return ""


# ---------------------------------------------------------------------------
# Lista per stagione
# ---------------------------------------------------------------------------

def analizza_lista(pagina: str, etichetta_richiesta: str) -> tuple[str, list[RigaLista], list[str]]:
    anomalie_globali: list[str] = []
    corrispondenza = ESPRESSIONE_STAGIONE.search(pagina)
    if not corrispondenza:
        return "", [], [f"{etichetta_richiesta}: intestazione 'Calendario AAAA/AA' non trovata: la pagina è cambiata?"]
    stagione = f"{corrispondenza[1]}/{corrispondenza[2]}"

    mesi = ESPRESSIONE_MESE.findall(pagina)
    if not mesi:
        return stagione, [], [f"{etichetta_richiesta}: nessuna tabella mensile (t_mese_AAMM) trovata"]

    righe: list[RigaLista] = []
    for codice_mese, blocco in mesi:
        anno, mese = 2000 + int(codice_mese[:2]), int(codice_mese[2:])
        for frammento_riga in ESPRESSIONE_RIGA.findall(blocco):
            celle_grezze = ESPRESSIONE_CELLA.findall(frammento_riga)
            if not celle_grezze or 'class="table_header"' in frammento_riga or "Scadenza iscrizioni" in frammento_riga:
                continue
            celle = [pulisci_html(cella) for cella in celle_grezze]
            riga = RigaLista(stagione=stagione, mese_tabella=f"{anno:04d}-{mese:02d}", data_grezza=celle[0] if celle else "")
            if len(celle) == 2:
                # Formato ridotto usato per campionati e attività nazionale: "nome - località"
                riga.formato = "2_celle"
                # La località è dopo l'ULTIMO trattino con almeno uno spazio accanto ("... cat. R12 -Torino")
                pezzi = re.split(r"\s+-\s*|\s*-\s+", celle[1])
                if len(pezzi) >= 2:
                    nome, localita = " - ".join(pezzi[:-1]), pezzi[-1]
                else:
                    nome, localita = celle[1], ""
                    riga.anomalie.append("riga a 2 celle senza trattino: località non separabile dal nome")
                celle = [celle[0], nome.strip(), localita.strip(), "", "", "", ""]
            if len(celle) != COLONNE_ATTESE:
                riga.anomalie.append(f"attese {COLONNE_ATTESE} celle, trovate {len(celle)}: {celle}")
                righe.append(riga)
                continue
            riga.data_inizio, riga.data_fine, anomalie_data = interpreta_data_lista(celle[0], anno, mese)
            riga.anomalie.extend(anomalie_data)
            riga.evento_grezzo = celle[1]
            riga.evento, era_base64 = ripara_base64(ripara_codifica(celle[1]))
            if era_base64:
                riga.anomalie.append("nome evento in base64 nella fonte: decodificato")
            riga.non_autorizzata = "non ancora autorizzata" in celle[1].lower() or "in attesa di autorizzazione" in celle[1].lower()
            riga.localita = ripara_codifica(celle[2])
            riga.organizzatore = ripara_codifica(celle[3])
            riga.scadenza_iscrizioni_grezza = celle[4]
            riga.scadenza_iscrizioni = interpreta_data_breve(celle[4], anno, mese) if celle[4] else ""
            if celle[4] and not riga.scadenza_iscrizioni:
                riga.anomalie.append(f"scadenza iscrizioni non interpretabile: {celle[4]!r}")
            riga.termine_depennamenti_grezzo = celle[5]
            if corrispondenza_modulo := ESPRESSIONE_MODULO.search(celle_grezze[1]):
                riga.id_manif = corrispondenza_modulo[1]
                riga.url_modulo = URL_MODULO + riga.id_manif
            if not riga.evento:
                riga.anomalie.append("nome evento vuoto")
            righe.append(riga)
    if not righe:
        anomalie_globali.append(f"{etichetta_richiesta}: tabelle presenti ma nessuna riga evento")
    return stagione, righe, anomalie_globali


# ---------------------------------------------------------------------------
# Indizione
# ---------------------------------------------------------------------------

def testo_da_html(pagina: str) -> list[str]:
    testo = re.sub(r"<script.*?</script>", "", pagina, flags=re.S | re.I)
    testo = re.sub(r"<br\s*/?>", "\n", testo, flags=re.I)
    testo = re.sub(r"</(tr|p|div|h\d|li|table)>", "\n", testo, flags=re.I)
    testo = re.sub(r"</td>", " | ", testo, flags=re.I)
    testo = html.unescape(re.sub(r"<[^>]+>", "", testo))
    righe = [re.sub(r"[ \t]+", " ", ripara_codifica(riga).replace("\xa0", " ")).strip() for riga in testo.splitlines()]
    return [riga for riga in righe if riga and riga != "|"]


def analizza_indizione(id_manif: str, grezzo: bytes) -> Indizione:
    indizione = Indizione(id_manif=id_manif, url=URL_MODULO + id_manif, scaricata=True)
    pagina, indizione.codifica = decodifica(grezzo)
    righe = testo_da_html(pagina)
    testo_intero = "\n".join(righe)

    if corrispondenza := re.search(
        r"DENOMINAZIONE\s*-\s*La Societ\S*\s*Sportiva\s+(?P<societa>.+?)\s+con l'approvazione.*?"
        r"dal giorno (?P<dal>\d{2}/\d{2}/\d{2}) al giorno (?P<al>\d{2}/\d{2}/\d{2})\s+"
        r"una manifestazione di categoria (?P<categoria>\S+?) di corsa su (?P<disciplina>\w+)\s+denominata:?\s*\n(?P<nome>[^\n|]+)",
        testo_intero, flags=re.S,
    ):
        indizione.societa = ripara_codifica(corrispondenza["societa"].strip())
        indizione.dal_grezzo = f"{corrispondenza['dal']} - {corrispondenza['al']}"
        indizione.dal = interpreta_data_indizione(corrispondenza["dal"])
        indizione.al = interpreta_data_indizione(corrispondenza["al"])
        indizione.categoria_manifestazione = corrispondenza["categoria"]
        indizione.disciplina = corrispondenza["disciplina"].lower()
        indizione.denominazione = ripara_codifica(corrispondenza["nome"].strip().rstrip("."))
        if not indizione.dal or not indizione.al:
            indizione.anomalie.append(f"date dell'indizione non interpretabili: {indizione.dal_grezzo!r}")
    else:
        indizione.anomalie.append("blocco DENOMINAZIONE non riconosciuto: la pagina ha un formato diverso")

    if corrispondenza := re.search(r"ART\. 3 .*?con inizio alle ore (?P<ora>[\d.,: ]+?) del giorno.*?descritto:\s*\n(?P<campo>[^\n]+)", testo_intero, flags=re.S):
        indizione.orario_inizio = corrispondenza["ora"].strip()
        indizione.campo_gara = ripara_codifica(corrispondenza["campo"].strip(" |"))
    else:
        indizione.anomalie.append("ART. 3 (campo di gara) non riconosciuto")

    if corrispondenza := re.search(r"ART\. 4 .*?entro le ore \S+ del (\d{2}/\d{2}/\d{2})", testo_intero, flags=re.S):
        indizione.iscrizioni_entro = interpreta_data_indizione(corrispondenza[1])
    else:
        indizione.anomalie.append("ART. 4 (scadenza iscrizioni) non riconosciuto")

    # ART. 10: righe della tabella del programma, finché somigliano a "Categoria | Sesso | Distanza | Tipo |"
    indice_programma = next((i for i, riga in enumerate(righe) if riga.startswith("ART. 10")), None)
    if indice_programma is None:
        indizione.anomalie.append("ART. 10 (programma gare) non trovato")
    else:
        for riga in righe[indice_programma + 1:]:
            if riga.startswith("Categoria |"):
                continue
            corrispondenza = ESPRESSIONE_RIGA_PROGRAMMA.match(riga)
            if not corrispondenza:
                if indizione.righe_programma:
                    break
                continue
            voce = {chiave: valore.strip() for chiave, valore in corrispondenza.groupdict().items()}
            voce["categoria"] = ripara_codifica(voce["categoria"])
            indizione.righe_programma.append(voce)
            if voce["categoria"] not in indizione.categorie_programma:
                indizione.categorie_programma.append(voce["categoria"])
        if not indizione.righe_programma:
            indizione.anomalie.append("ART. 10 trovato ma nessuna riga di programma riconosciuta")

    for riga in righe:
        if re.search(r"MASTER|AMATOR|FITNESS|\bOVER\b|NON AGONIST", riga, flags=re.I):
            indizione.righe_master_amatori.append(ripara_codifica(riga)[:300])
    return indizione


# ---------------------------------------------------------------------------
# Programma principale
# ---------------------------------------------------------------------------

def principale(argomenti: list[str] | None = None) -> int:
    analizzatore = argparse.ArgumentParser(description="Raccolta grezza dal calendario corsa di fisr.info")
    analizzatore.add_argument("--anno", type=int, action="append", help="parametro 'anno' di fisr.info (ripetibile); senza: stagione corrente")
    analizzatore.add_argument("--da", type=date.fromisoformat, default=None, help="tiene solo le righe con data_inizio >= AAAA-MM-GG")
    analizzatore.add_argument("--indizioni", action="store_true", help="scarica anche l'indizione di ogni gara con il link")
    analizzatore.add_argument("--pausa", type=float, default=0.5, help="secondi tra una richiesta e l'altra")
    analizzatore.add_argument("--scansione-indizioni", nargs=2, type=int, metavar=("DA", "A"), default=None,
                              help="scarica le indizioni con id_manif da DA ad A (inclusi) anche senza link nella lista; tiene solo quelle complete e con data >= --da")
    analizzatore.add_argument("--uscita", type=Path, required=True, help="file JSON da scrivere")
    opzioni = analizzatore.parse_args(argomenti)

    richieste = [(f"{URL_LISTA}?anno={anno}", f"anno={anno}") for anno in opzioni.anno] if opzioni.anno else [(URL_LISTA, "stagione corrente")]
    righe_totali: list[RigaLista] = []
    anomalie_globali: list[str] = []
    stagioni_lette: list[str] = []

    for url, etichetta in richieste:
        try:
            pagina, _ = decodifica(scarica(url, opzioni.pausa))
        except (urllib.error.URLError, RuntimeError, TimeoutError) as errore:
            anomalie_globali.append(f"{etichetta}: scaricamento fallito ({errore})")
            continue
        stagione, righe, anomalie = analizza_lista(pagina, etichetta)
        anomalie_globali.extend(anomalie)
        if stagione:
            stagioni_lette.append(stagione)
        print(f"{etichetta}: stagione {stagione or '?'}, {len(righe)} righe", file=sys.stderr)
        righe_totali.extend(righe)

    if opzioni.da:
        prima = len(righe_totali)
        righe_totali = [riga for riga in righe_totali if riga.data_inizio and date.fromisoformat(riga.data_inizio) >= opzioni.da or not riga.data_inizio]
        print(f"filtro --da {opzioni.da}: {prima} → {len(righe_totali)} righe (le righe con data non interpretabile restano)", file=sys.stderr)

    if opzioni.indizioni:
        for riga in righe_totali:
            if not riga.id_manif:
                continue
            try:
                riga.indizione = analizza_indizione(riga.id_manif, scarica(riga.url_modulo, opzioni.pausa))
            except (urllib.error.URLError, RuntimeError, TimeoutError) as errore:
                riga.indizione = Indizione(id_manif=riga.id_manif, url=riga.url_modulo, scaricata=False, anomalie=[f"scaricamento fallito ({errore})"])
            # Controllo incrociato lista ↔ indizione: non corregge, segnala.
            if riga.indizione.scaricata and riga.indizione.dal and riga.data_inizio and riga.indizione.dal != riga.data_inizio:
                riga.anomalie.append(f"la lista dice {riga.data_inizio}, l'indizione {riga.indizione.dal}")
        print(f"indizioni scaricate: {sum(1 for r in righe_totali if r.indizione and r.indizione.scaricata)}", file=sys.stderr)

    indizioni_scansione: list[dict] = []
    scartate_scansione = 0
    if opzioni.scansione_indizioni:
        primo, ultimo = opzioni.scansione_indizioni
        if primo > ultimo or primo < 1:
            print("ERRORE: --scansione-indizioni vuole DA <= A, entrambi positivi", file=sys.stderr)
            return 2
        for id_manif in range(primo, ultimo + 1):
            try:
                indizione = analizza_indizione(str(id_manif), scarica(URL_MODULO + str(id_manif), opzioni.pausa))
            except (urllib.error.URLError, RuntimeError, TimeoutError) as errore:
                anomalie_globali.append(f"scansione id {id_manif}: scaricamento fallito ({errore})")
                continue
            completa = bool(indizione.dal and indizione.denominazione and indizione.righe_programma)
            nel_periodo = not opzioni.da or date.fromisoformat(indizione.dal) >= opzioni.da if indizione.dal else False
            if completa and nel_periodo:
                indizioni_scansione.append(asdict(indizione))
            else:
                scartate_scansione += 1
        print(f"scansione id {primo}-{ultimo}: {len(indizioni_scansione)} indizioni complete nel periodo, {scartate_scansione} scartate (vuote, bozze o fuori periodo)", file=sys.stderr)

    documento = {
        "generato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": URL_LISTA,
        "richieste": [etichetta for _, etichetta in richieste],
        "stagioni": stagioni_lette,
        "filtro_da": opzioni.da.isoformat() if opzioni.da else "",
        "anomalie_globali": anomalie_globali,
        "righe": [asdict(riga) for riga in righe_totali],
        "scansione_indizioni": {"intervallo": opzioni.scansione_indizioni or [], "scartate": scartate_scansione},
        "indizioni_scansione": indizioni_scansione,
    }
    opzioni.uscita.parent.mkdir(parents=True, exist_ok=True)
    opzioni.uscita.write_text(json.dumps(documento, ensure_ascii=False, indent=1), encoding="utf-8")

    # Verifica dell'uscita: rilettura e conteggio.
    riletto = json.loads(opzioni.uscita.read_text(encoding="utf-8"))
    if len(riletto["indizioni_scansione"]) != len(indizioni_scansione):
        print("ERRORE: le indizioni scansionate rilette non corrispondono a quelle scritte", file=sys.stderr)
        return 1
    if len(riletto["righe"]) != len(righe_totali):
        print(f"ERRORE: scritte {len(righe_totali)} righe ma rilette {len(riletto['righe'])}", file=sys.stderr)
        return 1
    con_anomalie = sum(1 for riga in righe_totali if riga.anomalie or (riga.indizione and riga.indizione.anomalie))
    print(f"scritto {opzioni.uscita}: {len(righe_totali)} righe, {con_anomalie} con anomalie, {len(anomalie_globali)} anomalie globali", file=sys.stderr)
    for anomalia in anomalie_globali:
        print(f"  ANOMALIA: {anomalia}", file=sys.stderr)
    return 1 if anomalie_globali or not righe_totali else 0


if __name__ == "__main__":
    sys.exit(principale())
