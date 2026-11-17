#!/usr/bin/env python3
"""
converti_fisr.py — da raccolta grezza (raccogli_fisr.py) a voci di dati/eventi.yaml.

Livello 2 (normalizzazione + deduplica) e livello 3 "meccanico" (classificazione
con prova): quando il regolamento di gara ha il programma gare (art. 10), le categorie
ammesse sono scritte nero su bianco e lo script le cita testualmente. Dove non c'è
regolamento, lo script NON decide: stato "da_verificare", categorie vuote.

Uso:
    python3 script/converti_fisr.py --raccolta registro/raccolta.json \
        --eventi dati/eventi.yaml [--scrivi] [--rapporto registro/rapporto.md]

Senza --scrivi non tocca eventi.yaml: stampa solo il rapporto. Con --scrivi
riscrive eventi.yaml con le voci esistenti (riordinate per data) più le nuove.
Una gara già presente si riconosce prima di tutto dal numero del regolamento di
gara (id_manif), che la federazione non cambia mai, poi dall'id, poi da stessa
data d'inizio con nome simile o stessa città. Le voci esistenti vincono: se un
evento raccolto corrisponde a una voce già presente, lo script lo segnala e non
la tocca, con due eccezioni (regola 7 di CLAUDE.md):

  - PROMOZIONE: una voce ancora senza prova (da_verificare, non_autorizzato,
    annunciato) che ora ha il regolamento di gara riceve categorie, prova, stato,
    verificato_il e la fonte nuova;
  - REGOLAMENTO CAMBIATO: una voce legata a un regolamento di gara (lo cita in
    url_ufficiale o nelle fonti) segue il regolamento quando cambia: date,
    scadenza delle iscrizioni e, se la prova è la frase scritta da questo script,
    categorie, prova e stato. Se cambia la data d'inizio, la data nell'id la segue.
    Ogni cambio è scritto in note_interne e nel rapporto, prima → dopo.

In entrambi i casi nome, luogo, organizzatore, note e tutto ciò che una persona ha
scritto restano com'erano. Una prova scritta a mano non viene mai riscritta: se il
regolamento non le corrisponde più, lo script lo segnala in note_interne e nel
rapporto ("da controllare") e lascia decidere a chi rivede la PR.

Un regolamento che non ha ancora una riga nella lista (da cui viene la località)
non diventa una voce: resta nel rapporto finché la lista non lo riporta.

note_interne ha due scrittori, questo script e l'arricchimento. La traccia che
l'arricchimento lascia in coda ("Arricchimento AAAA-MM-GG: …") deve restare l'ultima
frase: lo script inserisce le sue frasi subito prima e, prima di scrivere, controlla
che la traccia di ogni voce sia rimasta identica; altrimenti si ferma.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Manca PyYAML. Installa: pip install -r script/requisiti.txt")

URL_LISTA = "https://www.fisr.info/attivita/corsa_calendario.php"
OGGI = date.today().isoformat()

ESPRESSIONE_MASTER = re.compile(r"MASTER|\bOVER\s*\d", re.I)
ESPRESSIONE_AMATORI = re.compile(r"AMATOR|FITNESS|PROMOZION|NON AGONIST", re.I)
DICITURE_DA_TOGLIERE = [
    re.compile(r"\s*-?\s*attivit[aà]'?\s+non\s+ancora\s+autorizzata\.?", re.I),
    re.compile(r"\s*-?\s*in\s+attesa\s+di\s+autorizzazione\.?", re.I),
]
PAROLE_MINUSCOLE = {"di", "del", "della", "dei", "degli", "delle", "dell'", "d'", "e", "con", "in", "su", "per",
                    "la", "il", "lo", "le", "i", "gli", "a", "al", "alla", "da", "dal", "dalla", "tra", "fra", "o", "ed"}
SIGLE_MAIUSCOLE = {"GPG", "IRC", "RSC", "CNO", "AVIS", "CUS", "ASD", "A.S.D.", "FISR", "UNICAL", "DIL", "ASA",
                   "CSI", "UISP", "AICS", "G.P.", "R", "A", "J", "S", "M", "G/E", "A/J/S", "A/J/S/M", "J/S/M", "R12"}
PAROLE_VUOTE_SLUG = {"di", "del", "della", "dei", "degli", "delle", "e", "con", "in", "su", "per", "la", "il", "lo",
                     "le", "i", "gli", "a", "al", "alla", "da", "dal", "tra", "fra", "o", "ed", "citta", "tappa",
                     "gpg", "irc", "rsc", "cat", "edizione", "comune", "collaborazione"}

ORDINE_CAMPI = ["id", "nome", "nome_fonte", "data_inizio", "data_fine", "luogo", "paese", "tipo", "categorie", "distanze",
                "organizzatore", "url_ufficiale", "url_iscrizione", "scadenza_iscrizione", "stato", "fonti",
                "verificato_il", "prova", "note", "note_interne"]


# ---------------------------------------------------------------------------
# Normalizzazione dei testi
# ---------------------------------------------------------------------------

def senza_accenti(testo: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", testo) if not unicodedata.combining(c))


def accenti_da_apostrofo(testo: str) -> str:
    """'CITTA'' → 'CITTÀ', 'Cantu'' → 'Cantù': l'apostrofo a fine parola dopo una vocale è un accento."""
    mappa = {"a": "à", "e": "è", "i": "ì", "o": "ò", "u": "ù", "A": "À", "E": "È", "I": "Ì", "O": "Ò", "U": "Ù"}
    return re.sub(r"(?<=\w)([aeiouAEIOU])'(?=\s|$|[,.;:)\-])", lambda m: mappa[m.group(1)], testo)


def normalizza_ordinali(testo: str) -> str:
    testo = re.sub(r"\b(\d+)\s*[°º^'o]\s*(?=\w)", r"\1° ", testo)      # 3^, 47', 47o, 1º → 1°
    testo = re.sub(r"\b(\d+)\.(?=\s+[A-Za-z])", r"\1°", testo)          # "40. MEMORIAL" → "40° MEMORIAL"
    testo = re.sub(r"\b([IVXL]+)°", r"\1", testo)                         # "I° Trofeo" → "I Trofeo"
    return testo


NOMI_PROPRI_CON_APOSTROFO = {"l'aquila"}


def titolo_italiano(testo: str) -> str:
    """Da TUTTO MAIUSCOLO a maiuscole normali, senza toccare sigle e numeri romani."""
    parole = testo.split(" ")
    risultato = []
    for indice, parola in enumerate(parole):
        if not parola:
            continue
        pezzi = []
        for pezzo in re.split(r"(-)", parola):          # "GPG-CNO" → sigle anche dentro ai trattini
            nudo = pezzo.strip("()-.,;:")
            if pezzo == "-" or not pezzo:
                pezzi.append(pezzo)
            elif pezzo.upper() in SIGLE_MAIUSCOLE or nudo.upper() in SIGLE_MAIUSCOLE or re.fullmatch(r"[IVXL]+", nudo):
                pezzi.append(pezzo.upper() if nudo.upper() in SIGLE_MAIUSCOLE else pezzo)
            elif pezzo.lower() in PAROLE_MINUSCOLE and indice > 0:
                pezzi.append(pezzo.lower())
            elif indice > 0 and re.match(r"[dDlL]'", pezzo) and pezzo.lower() not in NOMI_PROPRI_CON_APOSTROFO:
                # "Paderno D'ADDA" → "Paderno d'Adda", "Internazionali D'ITALIA" → "d'Italia"
                pezzi.append(pezzo[0].lower() + "'" + pezzo[2:3].upper() + pezzo[3:].lower())
            else:
                pezzi.append(re.sub(r"(^|['/])(\w)(\w*)", lambda m: m.group(1) + m.group(2).upper() + m.group(3).lower(), pezzo))
        risultato.append("".join(pezzi))
    return " ".join(risultato)


def normalizza_nome(grezzo: str) -> str:
    testo = grezzo.strip()
    for espressione in DICITURE_DA_TOGLIERE:
        testo = espressione.sub("", testo)
    testo = re.sub(r"\s+", " ", testo).strip(" -.,")
    testo = re.sub(r"\s*-\s*(?=[A-Za-z])", " - ", re.sub(r"(?<=[A-Za-z0-9])-\s+", " - ", testo))  # "-Tappa" → " - Tappa"
    testo = re.sub(r"(\d)°(?=[A-Za-z])", r"\1° ", testo)                                      # "1°maggio" → "1° maggio"
    testo = accenti_da_apostrofo(testo)
    testo = normalizza_ordinali(testo)
    testo = re.sub(r"\bcitta\b", "città", testo, flags=re.I)
    testo = re.sub(r"Ã(?=\s|$)", "À", testo)   # residuo di codifica non riparabile: in un nome è sempre una À
    # Maiuscole: un titolo (o un suo tratto tra due " - ") scritto quasi tutto in maiuscolo torna a maiuscole normali.
    # Tratto per tratto, perché la federazione mescola: "INTERNAZIONALI D'ITALIA OPEN INDOOR - VII Memorial Romano ...".
    tratti = []
    for tratto in testo.split(" - "):
        lettere = [c for c in tratto if c.isalpha()]
        if lettere and sum(1 for c in lettere if c.isupper()) / len(lettere) > 0.7 and len(lettere) > 3:
            tratto = titolo_italiano(tratto)
        tratti.append(tratto)
    return " - ".join(tratti)


def titolo_della_fonte(grezzo: str) -> str:
    """Il titolo com'è scritto nella fonte federale, per il campo nome_fonte: senza la dicitura
    'non ancora autorizzata' (che va e viene da sola) e con gli spazi in ordine; nient'altro viene toccato."""
    testo = str(grezzo or "")
    for espressione in DICITURE_DA_TOGLIERE:
        testo = espressione.sub("", testo)
    return re.sub(r"\s+", " ", testo).strip()


def parole_del_titolo(titolo: str) -> list[str]:
    """Le parole di un titolo, per capire se la fonte lo ha cambiato davvero: maiuscole, accenti, spazi e
    punteggiatura non contano ('CITTA'' e 'Città', '1°maggio' e '1° maggio' sono lo stesso titolo)."""
    return re.findall(r"[a-z0-9]+", senza_accenti(accenti_da_apostrofo(titolo)).lower())


def normalizza_luogo(grezzo: str) -> str:
    testo = accenti_da_apostrofo(grezzo.strip())
    testo = re.sub(r"\s*\(\s*", " (", testo)
    testo = re.sub(r"\s*\)\s*", ") ", testo).strip()
    lettere = [c for c in testo if c.isalpha()]
    if lettere and sum(1 for c in lettere if c.isupper()) / len(lettere) > 0.7:
        testo = titolo_italiano(testo)
    # la sigla di provincia è sempre maiuscola: "(bs)", "(An)" → "(BS)", "(AN)"
    return re.sub(r"\(([A-Za-z]{2})\)", lambda m: f"({m.group(1).upper()})", testo)


def slug(testo: str, massimo_parole: int | None = None, parole_vuote: set[str] = frozenset()) -> str:
    testo = senza_accenti(testo).lower().replace("'", "")
    parole = [p for p in re.split(r"[^a-z0-9]+", testo) if p and p not in parole_vuote]
    if massimo_parole:
        parole = parole[:massimo_parole]
    return "-".join(parole)


def citta_da_localita(localita: str) -> str:
    parti = [p.strip() for p in localita.split(" - ") if p.strip()]
    parti = [p for p in parti if not re.match(r"(via|viale|piazza|piazzale|corso|largo)\b", p, re.I)] or parti
    base = re.split(r"\(|\b(?:via|viale|piazza|piazzale|corso|largo)\b", parti[0] if parti else localita, maxsplit=1, flags=re.I)[0]
    return base.strip(" ,")


def slug_citta(localita: str) -> str:
    return slug(citta_da_localita(localita)) or "luogo-ignoto"


def slug_nome(nome: str) -> str:
    senza_numeri = re.sub(r"\b\d+°?\b|\b[IVXL]+\b", " ", nome)
    return slug(senza_numeri, massimo_parole=4, parole_vuote=PAROLE_VUOTE_SLUG) or slug(nome, massimo_parole=4)


def gettoni(testo: str) -> set[str]:
    return {p for p in re.split(r"[^a-z0-9]+", senza_accenti(testo).lower()) if len(p) > 2 and p not in PAROLE_VUOTE_SLUG}


def somiglianza(a: str, b: str) -> float:
    ga, gb = gettoni(a), gettoni(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


# ---------------------------------------------------------------------------
# Lettura della raccolta e deduplica
# ---------------------------------------------------------------------------

def carica_raccolta(percorso: Path) -> dict:
    documento = json.loads(percorso.read_text(encoding="utf-8"))
    for chiave in ("righe", "regolamenti_scansione", "fonte"):
        if chiave not in documento:
            sys.exit(f"{percorso}: manca la chiave '{chiave}': non è l'uscita di raccogli_fisr.py?")
    return documento


def ripara_base64(testo: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9+/]{32,}={0,2}", testo):
        return testo
    import base64
    try:
        grezzo = base64.b64decode(testo + "=" * (-len(testo) % 4))
        return grezzo.decode("utf-8") if b"\xc3" in grezzo else grezzo.decode("latin-1")
    except (ValueError, UnicodeDecodeError):
        return testo


def deduplica_righe(righe: list[dict], rapporto: list[str]) -> list[dict]:
    """Righe doppie (stagioni sovrapposte, doppioni nella fonte, formato a 2 celle accanto a quello a 7)."""
    tenute: list[dict] = []
    for riga in righe:
        riga["evento"] = ripara_base64(riga["evento"])
        if not riga["data_inizio"]:
            rapporto.append(f"- riga scartata, data non interpretabile: {riga['data_grezza']!r} {riga['evento'][:60]!r} ({riga['anomalie']})")
            continue
        doppione = None
        for tenuta in tenute:
            stesso_periodo = abs((date.fromisoformat(tenuta["data_inizio"]) - date.fromisoformat(riga["data_inizio"])).days) <= 2
            if stesso_periodo and somiglianza(tenuta["evento"], riga["evento"]) >= 0.5:
                doppione = tenuta
                break
        if doppione is None:
            tenute.append(riga)
            continue
        # Tiene la più ricca: 7 celle batte 2 celle; a parità, quella con più campi pieni.
        punteggio = lambda r: (r["formato"] == "7_celle", bool(r["id_manif"]), bool(r["scadenza_iscrizioni"]), bool(r["organizzatore"]))
        if punteggio(riga) > punteggio(doppione):
            tenute[tenute.index(doppione)] = riga
        rapporto.append(f"- doppione unito: {riga['data_grezza']} {riga['evento'][:50]!r} ↔ {doppione['data_grezza']} {doppione['evento'][:50]!r}")
    return tenute


# ---------------------------------------------------------------------------
# Abbinamento lista ↔ regolamenti
# ---------------------------------------------------------------------------

def abbina_regolamenti(righe: list[dict], regolamenti: list[dict], rapporto: list[str]) -> tuple[dict[int, dict], list[dict]]:
    """Restituisce {indice_riga: regolamento} e i regolamenti rimasti senza riga."""
    abbinate: dict[int, dict] = {}
    usate: set[str] = set()
    for indice, riga in enumerate(righe):
        if riga.get("regolamento") and riga["regolamento"].get("scaricata") and riga["regolamento"].get("dal"):
            abbinate[indice] = riga["regolamento"]
            usate.add(riga["regolamento"]["id_manif"])
            continue
        migliore, punteggio_migliore = None, 0.0
        for regolamento in regolamenti:
            if regolamento["id_manif"] in usate or not regolamento["dal"]:
                continue
            distanza_giorni = abs((date.fromisoformat(regolamento["dal"]) - date.fromisoformat(riga["data_inizio"])).days)
            if distanza_giorni > 1:
                continue
            punteggio = max(somiglianza(regolamento["denominazione"], riga["evento"]), somiglianza(regolamento["societa"], riga["organizzatore"]) * 0.9)
            if punteggio > punteggio_migliore:
                migliore, punteggio_migliore = regolamento, punteggio
        if migliore is not None and punteggio_migliore >= 0.34:
            abbinate[indice] = migliore
            usate.add(migliore["id_manif"])
            if punteggio_migliore < 0.6:
                rapporto.append(f"- abbinamento debole ({punteggio_migliore:.2f}): lista {riga['evento'][:45]!r} ↔ regolamento {migliore['id_manif']} {migliore['denominazione'][:45]!r}")
    rimaste = [i for i in regolamenti if i["id_manif"] not in usate]
    return abbinate, rimaste


# ---------------------------------------------------------------------------
# Classificazione con prova
# ---------------------------------------------------------------------------

def classifica(regolamento: dict) -> tuple[list[str], list[str], str]:
    """Dalle righe dell'art. 10: categorie ammesse, distanze dei Master/Amatori, prova citata."""
    righe = regolamento["righe_programma"]
    righe_master = [r for r in righe if ESPRESSIONE_MASTER.search(r["categoria"])]
    righe_amatori = [r for r in righe if ESPRESSIONE_AMATORI.search(r["categoria"])]
    categorie: list[str] = []
    if righe_master:
        categorie.append("master")
    if righe_amatori:
        categorie.append("amatori")

    distanze: list[str] = []
    for r in righe_master + righe_amatori:
        voce = f"{r['distanza']} {r['tipo']}".strip().lower().replace(" g ", " giri ")
        voce = re.sub(r"^(\d+) g$", r"\1 giri", voce)
        if voce and voce not in distanze:
            distanze.append(voce)

    def riga_testuale(r: dict) -> str:
        return f"{r['categoria']} | {r['sesso']} | {r['distanza']} | {r['tipo']}"

    riferimento = f"Regolamento di gara id_manif {regolamento['id_manif']}, art. 10 'Programma gare'"
    if categorie:
        nomi_categorie = []
        for r in righe_master + righe_amatori:
            if r["categoria"] not in nomi_categorie:
                nomi_categorie.append(r["categoria"])
        esempi = "; ".join(f"'{riga_testuale(r)}'" for r in (righe_master + righe_amatori)[:2])
        prova = f"{riferimento}: righe {esempi}" + (" e seguenti" if len(righe_master + righe_amatori) > 2 else "") + f". Categorie elencate: {', '.join(nomi_categorie)}."
    else:
        prova = f"{riferimento}: categorie elencate {', '.join(regolamento['categorie_programma'])}; nessuna riga Master o Amatori."
    return categorie, distanze, prova


def categorie_dal_titolo(nome: str) -> list[str] | None:
    """'Campionato Italiano maratona cat. J/S/M' → ['J', 'S', 'M']; None se il titolo non indica categorie."""
    sigle: list[str] = []
    for corrispondenza in re.finditer(r"\bcat\.?\s*([A-Z0-9]{1,3}(?:/[A-Z0-9]{1,3})*)", nome):
        for sigla in corrispondenza.group(1).split("/"):
            if sigla not in sigle:
                sigle.append(sigla)
    return sigle or None


def costruisci_evento(riga: dict | None, regolamento: dict | None, letto_il: str) -> dict:
    """Una voce di eventi.yaml. Se riga è None, l'evento viene dalla solo regolamento (non è nella lista)."""
    assert riga is not None or regolamento is not None
    if riga is not None:
        nome = normalizza_nome(riga["evento"])
        data_inizio, data_fine = riga["data_inizio"], riga["data_fine"]
        luogo = normalizza_luogo(riga["localita"])
        organizzatore = normalizza_luogo(riga["organizzatore"]) if riga["organizzatore"] else ""
    else:
        nome = normalizza_nome(regolamento["denominazione"])
        data_inizio, data_fine = regolamento["dal"], regolamento["al"] or regolamento["dal"]
        luogo = ""
        organizzatore = normalizza_luogo(regolamento["societa"]) if regolamento["societa"] else ""
    if regolamento and not organizzatore and regolamento.get("societa"):
        organizzatore = normalizza_luogo(regolamento["societa"])

    note: list[str] = []            # per chi pattina: finiscono nella descrizione dell'evento
    note_interne: list[str] = []    # per chi lavora sui dati: restano nell'YAML
    categorie: list[str] = []
    distanze: list[str] = []
    prova = ""
    verificato_il = ""
    url_ufficiale = ""
    fonti = []
    if riga is not None:
        fonti.append({"url": URL_LISTA, "letto_il": letto_il})
    if regolamento:
        url_ufficiale = regolamento["url"]
        fonti.append({"url": regolamento["url"], "letto_il": letto_il})
        categorie, distanze, prova = classifica(regolamento)
        verificato_il = letto_il
        if regolamento.get("categoria_manifestazione") or regolamento.get("disciplina"):
            note.append(f"Manifestazione di categoria {regolamento.get('categoria_manifestazione') or '?'} su {regolamento.get('disciplina') or '?'}.")
        if regolamento.get("campo_gara"):
            campo = re.sub(r"\s+", " ", regolamento["campo_gara"]).strip()
            campo = re.sub(r"\.?\.? ?CAP della localit[àa]? \d{5}\.?$", ".", campo)   # rumore del modulo, inutile per chi legge
            note.append("Campo di gara: " + (campo[:220] + "…" if len(campo) > 220 else campo))
        if not luogo and regolamento.get("campo_gara"):
            luogo = "da indicare (vedi note)"
        if riga is None:
            note_interne.append("Non compare nella lista corsa_calendario.php: trovato solo tra i regolamenti.")
        righe_extra = [r for r in regolamento.get("righe_master_amatori", []) if " | " not in r]
        if righe_extra and not categorie:
            note_interne.append("Nel testo del regolamento compaiono righe con Master/Amatori fuori dal programma gare (da leggere): " + " / ".join(r[:120] for r in righe_extra[:2]))
        if riga is not None and riga["data_inizio"] != regolamento["dal"]:
            note_interne.append(f"Date: la lista dice {riga['data_inizio']}, il regolamento {regolamento['dal']}–{regolamento['al']}.")
            data_inizio, data_fine = regolamento["dal"], regolamento["al"] or regolamento["dal"]

    categorie_nel_titolo = categorie_dal_titolo(riga["evento"]) if riga is not None and not regolamento else None
    if riga is not None and riga["non_autorizzata"] and (not regolamento or categorie):
        stato = "non_autorizzato"
        note_interne.append("Nella lista FISR compare come 'Attività non ancora autorizzata'" + (" (il regolamento esiste già)." if regolamento else "."))
    elif regolamento:
        stato = "confermato" if categorie else "escluso"
        if riga is not None and riga["non_autorizzata"]:
            note_interne.append("Nella lista FISR compare come 'Attività non ancora autorizzata'; il regolamento (bozza) non prevede Master/Amatori.")
    elif categorie_nel_titolo is not None:
        # Campionati e attività nazionale: la lista FISR non ha il regolamento, ma il titolo ufficiale dice le categorie.
        sigle = categorie_nel_titolo
        categorie = ["master"] if "M" in sigle else []
        stato = "confermato" if categorie else "escluso"
        verificato_il = letto_il
        prova = f"Calendario FISR {riga['stagione']} ({URL_LISTA}), titolo ufficiale: '{riga['evento']}'. Categorie indicate nel titolo: {'/'.join(sigle)}" + (" (M = Master)." if categorie else "; nessuna M (Master).")
        note_interne.append("Categorie prese dal titolo ufficiale nel calendario FISR; regolamento del campionato non letto: distanze e dettagli da verificare.")
    else:
        stato = "da_verificare"
        note_interne.append("Regolamento di gara non trovato: categorie ammesse sconosciute.")
    if riga is not None and riga["anomalie"]:
        note_interne.append("Anomalie di lettura: " + "; ".join(riga["anomalie"]))

    scadenza = (riga["scadenza_iscrizioni"] if riga else "") or (regolamento["iscrizioni_entro"] if regolamento else "") or ""
    categorie_regolamento, _, prova_regolamento = classifica(regolamento) if regolamento else ([], [], "")
    nome_fonte = titolo_della_fonte(riga["evento"]) if riga is not None else ""   # solo il titolo della LISTA: è quello che si rilegge ogni settimana
    return {
        # Campi di lavoro (iniziano con "_"): servono al confronto con le voci esistenti, non vengono mai scritti.
        "_dalla_lista": riga is not None,
        "_data_lista": riga["data_inizio"] if riga is not None else "",   # la lista può dare una data diversa dal regolamento
        "_non_autorizzata": bool(riga is not None and riga["non_autorizzata"]),
        "_regolamento": str(regolamento["id_manif"]) if regolamento else "",
        "_categorie_regolamento": categorie_regolamento,
        "_prova_regolamento": prova_regolamento,
        "id": f"{data_inizio}-{slug_citta(luogo) if luogo and not luogo.startswith('da indicare') else 'luogo-ignoto'}-{slug_nome(nome)}",
        "nome": nome, "nome_fonte": nome_fonte, "data_inizio": data_inizio, "data_fine": data_fine, "luogo": luogo or "da indicare",
        "paese": "IT", "tipo": "gara", "categorie": categorie, "distanze": distanze, "organizzatore": organizzatore,
        "url_ufficiale": url_ufficiale, "url_iscrizione": "", "scadenza_iscrizione": scadenza, "stato": stato,
        "fonti": fonti, "verificato_il": verificato_il, "prova": prova, "note": " ".join(note),
        "note_interne": " ".join(note_interne),
    }


# ---------------------------------------------------------------------------
# Unione con eventi.yaml e scrittura
# ---------------------------------------------------------------------------

def carica_eventi(percorso: Path) -> tuple[str, list[dict]]:
    testo = percorso.read_text(encoding="utf-8") if percorso.exists() else ""
    intestazione = testo.split("\n- id:", 1)[0] if "- id:" in testo else testo
    eventi = yaml.safe_load(testo) or []
    if not isinstance(eventi, list):
        sys.exit(f"{percorso}: deve contenere una lista")
    return intestazione.rstrip("\n") + "\n", eventi


ESPRESSIONE_NUMERO_REGOLAMENTO = re.compile(r"[?&]id_manif=(\d+)")


def numeri_regolamento(evento: dict) -> set[str]:
    """I numeri di regolamento di gara (id_manif) citati da una voce, in url_ufficiale e nelle fonti.
    La federazione non cambia mai il numero di una gara: è la chiave più stabile che abbiamo."""
    testi = [str(evento.get("url_ufficiale") or "")]
    for fonte in evento.get("fonti") or []:
        if isinstance(fonte, dict):
            testi.append(str(fonte.get("url") or ""))
    numeri: set[str] = set()
    for testo in testi:
        numeri.update(ESPRESSIONE_NUMERO_REGOLAMENTO.findall(testo))
    return numeri


def giorni_tra(a, b) -> int:
    return abs((date.fromisoformat(str(a)) - date.fromisoformat(str(b))).days)


def corrisponde_esistente(nuovo: dict, esistenti: list[dict]) -> dict | None:
    """La voce già presente che descrive la stessa gara, o None. In ordine: stesso numero di regolamento
    (vale anche se nel frattempo sono cambiati data e nome), stesso id, stessa data d'inizio con nome simile
    o stessa città."""
    numeri = numeri_regolamento(nuovo)
    if numeri:
        stesso_regolamento = [e for e in esistenti if numeri_regolamento(e) & numeri]
        if stesso_regolamento:
            # di norma è una sola; se fossero più d'una, la più vicina per data
            return min(stesso_regolamento, key=lambda e: giorni_tra(e["data_inizio"], nuovo["data_inizio"]))
    date_possibili = {str(nuovo["data_inizio"]), str(nuovo.get("_data_lista") or nuovo["data_inizio"])}
    for esistente in esistenti:
        if esistente["id"] == nuovo["id"]:
            return esistente
        stesso_giorno = str(esistente["data_inizio"]) in date_possibili
        if stesso_giorno and (somiglianza(str(esistente["nome"]), nuovo["nome"]) >= 0.4 or slug_citta(str(esistente["luogo"])) == slug_citta(nuovo["luogo"])):
            return esistente
    return None


STATI_PROMUOVIBILI = {"da_verificare", "non_autorizzato", "annunciato"}
FRASE_SENZA_REGOLAMENTO = "Regolamento di gara non trovato: categorie ammesse sconosciute."

# La traccia dell'arricchimento (agenti/arricchimento.md, passo 3, punto 9): "Arricchimento AAAA-MM-GG: esito; …".
# L'agente la tiene in coda a note_interne e la sostituisce a ogni ricontrollo: le frasi dello script non
# devono finirle dietro, altrimenti la traccia non è più l'ultima e la sostituzione può cancellarle.
ESPRESSIONE_TRACCIA_ARRICCHIMENTO = re.compile(r"Arricchimento \d{4}-\d{2}-\d{2}:")


def coda_arricchimento(note_interne) -> str:
    """La traccia dell'arricchimento: dall'ultima "Arricchimento AAAA-MM-GG:" alla fine di note_interne.
    Stringa vuota se la traccia non c'è."""
    testo = str(note_interne or "").strip()
    inizi = [trovata.start() for trovata in ESPRESSIONE_TRACCIA_ARRICCHIMENTO.finditer(testo)]
    return testo[inizi[-1]:] if inizi else ""


def aggiungi_a_note_interne(note_interne, frase: str) -> str:
    """Aggiunge una frase dello script a note_interne lasciando in coda la traccia dell'arricchimento:
    la frase va subito prima della traccia; se la traccia non c'è, in fondo."""
    testo = str(note_interne or "").strip()
    frase = str(frase or "").strip()
    if not frase:
        return testo
    traccia = coda_arricchimento(testo)
    prima = testo[: len(testo) - len(traccia)].strip() if traccia else testo
    return " ".join(parte for parte in (prima, frase, traccia) if parte)


def promuovi(esistente: dict, proposta: dict, letto_il: str) -> list[str]:
    """Promozione di una voce esistente (regola 7): aggiorna SUL POSTO la voce e ritorna l'elenco
    di cosa è cambiato (vuoto = niente da fare). Due soli casi, entrambi senza giudizio:
      1. la voce non ha prova e la proposta ne porta una (regolamento di gara o titolo ufficiale):
         prende categorie, prova, stato, verificato_il, e riempie i campi vuoti (url, distanze, scadenza);
      2. la voce è non_autorizzato con prova già citata e la lista ora non la segna più come
         "non ancora autorizzata": cambia solo lo stato (confermato/escluso), se coerente con le categorie.
    Nome, luogo, organizzatore, note pubbliche, url_iscrizione, date: mai toccati."""
    stato_vecchio = str(esistente.get("stato") or "")
    if stato_vecchio not in STATI_PROMUOVIBILI:
        return []
    cambiamenti: list[str] = []
    stato_nuovo = proposta["stato"]
    if not esistente.get("prova") and proposta.get("prova"):
        esistente["categorie"] = list(proposta["categorie"])
        esistente["prova"] = proposta["prova"]
        cambiamenti.append(f"categorie {esistente['categorie']}")
        for campo in ("distanze", "url_ufficiale", "scadenza_iscrizione"):
            if not esistente.get(campo) and proposta.get(campo):
                esistente[campo] = list(proposta[campo]) if isinstance(proposta[campo], list) else proposta[campo]
                cambiamenti.append(f"{campo} riempito")
        if stato_nuovo not in ("confermato", "escluso", "non_autorizzato"):
            # non dovrebbe succedere: una proposta con prova ha sempre uno di questi stati
            return []
    elif stato_vecchio == "non_autorizzato" and esistente.get("prova") and stato_nuovo in ("confermato", "escluso") \
            and bool(esistente.get("categorie")) == bool(proposta.get("categorie")) and proposta.get("_dalla_lista", True):
        pass  # cambia solo lo stato, sotto (solo se la proposta viene da una riga della lista: è la lista che autorizza)
    else:
        return []
    if stato_nuovo != stato_vecchio:
        esistente["stato"] = stato_nuovo
        cambiamenti.append(f"stato {stato_vecchio} → {stato_nuovo}")
    if not cambiamenti:
        return []
    esistente["verificato_il"] = letto_il
    fonti_esistenti = esistente.setdefault("fonti", [])
    for fonte in proposta.get("fonti", []):
        presente = next((f for f in fonti_esistenti if f.get("url") == fonte["url"]), None)
        if presente:
            presente["letto_il"] = fonte["letto_il"]
        else:
            fonti_esistenti.append({"url": fonte["url"], "letto_il": fonte["letto_il"]})
            cambiamenti.append(f"fonte aggiunta {fonte['url']}")
    note_interne = str(esistente.get("note_interne") or "").replace(FRASE_SENZA_REGOLAMENTO, "").strip()
    regolamento = proposta["url_ufficiale"].rsplit("=", 1)[-1] if "id_manif=" in str(proposta.get("url_ufficiale") or "") else ""
    frase = f"Promossa il {letto_il} da converti_fisr.py: " + "; ".join(cambiamenti) + (f"; regolamento di gara id_manif {regolamento}." if regolamento else ".")
    esistente["note_interne"] = aggiungi_a_note_interne(note_interne, frase)
    return cambiamenti


# ---------------------------------------------------------------------------
# Regolamento di gara cambiato dopo la prima lettura
# ---------------------------------------------------------------------------

STATI_RICALCOLABILI = {"confermato", "escluso", "non_autorizzato"}
# Frasi scritte da questo script quando il regolamento non aveva righe Master/Amatori: se poi le righe arrivano non sono più vere.
FRASI_SUPERATE_DA_CATEGORIE = [
    re.compile(r"\s*Nella lista FISR compare come 'Attività non ancora autorizzata'; il regolamento(?: di gara)? \(bozza\) non prevede Master/Amatori\."),
]


def frase_prova_dello_script(prova: str, numero: str) -> str | None:
    """La frase che questo script ha scritto come prova per il regolamento `numero`, se è ancora nella voce.
    None se la prova è scritta a mano o viene da un'altra fonte: in quel caso non la si riscrive."""
    inizio = re.escape(f"Regolamento di gara id_manif {numero}, art. 10 'Programma gare': ")
    trovata = re.search(inizio + r"(?:righe .*? Categorie elencate: [^.]*\.|categorie elencate [^;]*; nessuna riga Master o Amatori\.)", prova, flags=re.S)
    return trovata.group(0) if trovata else None


def categorie_della_frase(frase: str) -> list[str]:
    """Le categorie che il regolamento dava quando lo script ha scritto la frase di prova."""
    if "nessuna riga Master o Amatori" in frase:
        return []
    elenco = frase.rsplit("Categorie elencate: ", 1)[-1]
    categorie = []
    if ESPRESSIONE_MASTER.search(elenco):
        categorie.append("master")
    if ESPRESSIONE_AMATORI.search(elenco):
        categorie.append("amatori")
    return categorie


def aggiorna_dal_regolamento(esistente: dict, proposta: dict, letto_il: str, id_occupati: set[str]) -> tuple[list[str], list[str]]:
    """Regolamento cambiato (regola 7): se la voce è legata allo stesso regolamento di gara della proposta
    (stesso id_manif), la allinea SUL POSTO a ciò che il regolamento e la lista dicono oggi.
    Ritorna (cambiamenti fatti, cose da controllare a mano); due liste vuote = niente da fare.
      - date e scadenza delle iscrizioni: sempre; se cambia la data d'inizio, la data nell'id la segue;
      - categorie, prova e stato: solo se la prova è la frase scritta da questo script per quel regolamento
        (frase_prova_dello_script). Le categorie arrivate da altre fonti (es. 'amatori' dalla pagina
        dell'organizzatore) e il testo aggiunto alla prova restano;
      - prova scritta a mano e regolamento che oggi dà altre categorie: nessun cambio, solo "da controllare".
    Nome, luogo, organizzatore, note pubbliche e url: mai toccati (tranne le frasi di questo script non più vere)."""
    numero = str(proposta.get("_regolamento") or "")
    if not numero or numero not in numeri_regolamento(esistente):
        return [], []
    cambiamenti: list[str] = []
    da_controllare: list[str] = []
    categorie_voce = [str(c) for c in (esistente.get("categorie") or [])]
    categorie_nuove = list(proposta.get("_categorie_regolamento") or [])
    prova_voce = str(esistente.get("prova") or "")
    frase_vecchia = frase_prova_dello_script(prova_voce, numero)
    stato_vecchio = str(esistente.get("stato") or "")

    # 1. Categorie, prova e stato
    if frase_vecchia is not None:
        categorie_vecchie = categorie_della_frase(frase_vecchia)
        if set(categorie_vecchie) != set(categorie_nuove):
            tolte = [c for c in categorie_vecchie if c not in categorie_nuove]
            aggiornate = [c for c in ("master", "amatori") if (c in categorie_voce and c not in tolte) or c in categorie_nuove]
            esistente["prova"] = prova_voce.replace(frase_vecchia, proposta["_prova_regolamento"])
            esistente["categorie"] = aggiornate
            cambiamenti.append(f"categorie {categorie_voce} → {aggiornate}")
            if not esistente.get("distanze") and proposta.get("distanze"):
                esistente["distanze"] = list(proposta["distanze"])
                cambiamenti.append(f"distanze {esistente['distanze']}")
            elif esistente.get("distanze") and list(esistente["distanze"]) != list(proposta.get("distanze") or []):
                da_controllare.append(f"le distanze della voce ({list(esistente['distanze'])}) non sono quelle che il regolamento {numero} dà oggi per Master/Amatori ({list(proposta.get('distanze') or [])})")
            if aggiornate and not categorie_voce:
                for campo in ("note", "note_interne"):
                    testo = str(esistente.get(campo) or "")
                    for espressione in FRASI_SUPERATE_DA_CATEGORIE:
                        testo = espressione.sub("", testo)
                    if testo.strip() != str(esistente.get(campo) or "").strip():
                        esistente[campo] = testo.strip()
                        cambiamenti.append(f"tolta da '{campo}' la frase sul regolamento senza Master/Amatori")
            if stato_vecchio in STATI_RICALCOLABILI:
                if not aggiornate:
                    stato_nuovo = "escluso"
                elif proposta.get("_non_autorizzata") or (stato_vecchio == "non_autorizzato" and not proposta.get("_dalla_lista")):
                    stato_nuovo = "non_autorizzato"   # autorizza solo la lista: senza riga in lista lo stato non migliora
                else:
                    stato_nuovo = "confermato"
                if stato_nuovo != stato_vecchio:
                    esistente["stato"] = stato_nuovo
                    cambiamenti.append(f"stato {stato_vecchio} → {stato_nuovo}")
            else:
                da_controllare.append(f"lo stato è '{stato_vecchio}' e non viene ricalcolato, ma le categorie del regolamento {numero} sono cambiate")
    elif prova_voce:
        manca_nella_voce = [c for c in categorie_nuove if c not in categorie_voce]
        master_sparito = "master" in categorie_voce and "master" not in categorie_nuove
        if manca_nella_voce or master_sparito:
            da_controllare.append(f"il regolamento {numero} oggi dà categorie {categorie_nuove}, la voce ha {categorie_voce} con una prova scritta a mano")

    # 2. Date (e id, se cambia la data d'inizio)
    date_vecchie = (str(esistente["data_inizio"]), str(esistente["data_fine"]))
    date_nuove = (str(proposta["data_inizio"]), str(proposta["data_fine"]))
    if date_nuove != date_vecchie:
        esistente["data_inizio"], esistente["data_fine"] = date_nuove
        cambiamenti.append(f"date {date_vecchie[0]}–{date_vecchie[1]} → {date_nuove[0]}–{date_nuove[1]}")
        if date_nuove[0] != date_vecchie[0]:
            id_vecchio = str(esistente["id"])
            resto = id_vecchio[11:] if re.match(r"\d{4}-\d{2}-\d{2}-.", id_vecchio) else id_vecchio
            base = f"{date_nuove[0]}-{resto}"
            id_nuovo, contatore = base, 2
            while id_nuovo in id_occupati:
                id_nuovo = f"{base}-{contatore}"
                contatore += 1
            id_occupati.discard(id_vecchio)
            id_occupati.add(id_nuovo)
            esistente["id"] = id_nuovo
            cambiamenti.append(f"id {id_vecchio} → {id_nuovo}")

    # 3. Scadenza delle iscrizioni
    scadenza_vecchia, scadenza_nuova = str(esistente.get("scadenza_iscrizione") or ""), str(proposta.get("scadenza_iscrizione") or "")
    if scadenza_nuova and scadenza_nuova != scadenza_vecchia:
        esistente["scadenza_iscrizione"] = scadenza_nuova
        cambiamenti.append(f"scadenza iscrizioni {scadenza_vecchia or 'vuota'} → {scadenza_nuova}")

    note_interne = str(esistente.get("note_interne") or "").strip()
    if cambiamenti:
        esistente["verificato_il"] = letto_il
        fonti_esistenti = esistente.setdefault("fonti", [])
        for fonte in proposta.get("fonti", []):
            presente = next((f for f in fonti_esistenti if f.get("url") == fonte["url"]), None)
            if presente:
                presente["letto_il"] = fonte["letto_il"]
            else:
                fonti_esistenti.append({"url": fonte["url"], "letto_il": fonte["letto_il"]})
        note_interne = aggiungi_a_note_interne(note_interne, f"Aggiornata il {letto_il} da converti_fisr.py, il regolamento di gara id_manif {numero} è cambiato: " + "; ".join(cambiamenti) + ".")
    for cosa in da_controllare:
        frase = f"Da controllare (converti_fisr.py): {cosa}."
        if frase not in note_interne:      # la stessa segnalazione non si ripete ogni settimana
            note_interne = aggiungi_a_note_interne(note_interne, frase)
    if note_interne != str(esistente.get("note_interne") or "").strip():
        esistente["note_interne"] = note_interne
    return cambiamenti, da_controllare


def aggiorna_nome(esistente: dict, proposta: dict, letto_il: str, unica_riga: bool, solo_registrare: bool = False) -> tuple[list[str], bool]:
    """Il nome segue la fonte quando la fonte cambia il titolo (decisione 2026-11-16).
    nome_fonte ricorda il titolo com'era nella lista federale all'ultima lettura:
      - se è vuoto, lo si registra e il nome non cambia (prima lettura: non c'è nulla con cui confrontare);
      - se le parole del titolo sono le stesse (maiuscole, accenti e punteggiatura non contano), niente:
        i ritocchi fatti a mano al nome restano;
      - se le parole sono cambiate, il nome diventa il titolo nuovo ripulito dallo script, nome_fonte si aggiorna
        e il nome vecchio resta scritto in note_interne. L'id non cambia.
    Vale solo per le proposte che vengono da una riga della lista, e solo se a quella voce corrisponde una sola
    riga (più gare dello stesso giorno in una voce sola hanno più titoli: non si sceglie).
    Ritorna (cambiamenti, titolo registrato per la prima volta)."""
    if not proposta.get("_dalla_lista") or not unica_riga:
        return [], False
    titolo_nuovo = str(proposta.get("nome_fonte") or "")
    if not titolo_nuovo:
        return [], False
    titolo_vecchio = str(esistente.get("nome_fonte") or "")
    if not titolo_vecchio:
        esistente["nome_fonte"] = titolo_nuovo
        return [], True
    if solo_registrare or parole_del_titolo(titolo_vecchio) == parole_del_titolo(titolo_nuovo):
        return [], False
    nome_vecchio = str(esistente.get("nome") or "")
    esistente["nome"] = proposta["nome"]
    esistente["nome_fonte"] = titolo_nuovo
    for fonte in esistente.get("fonti") or []:
        if isinstance(fonte, dict) and fonte.get("url") == URL_LISTA:
            fonte["letto_il"] = letto_il
    frase = (f"Nome aggiornato il {letto_il} da converti_fisr.py perché la lista federale ha cambiato il titolo: "
             f"da «{titolo_vecchio}» a «{titolo_nuovo}»; il nome della voce era «{nome_vecchio}».")
    esistente["note_interne"] = aggiungi_a_note_interne(esistente.get("note_interne"), frase)
    return [f"nome «{nome_vecchio}» → «{proposta['nome']}»"], False


def segnala_possibili_doppioni(nuovi: list[dict], esistenti: list[dict], ancora_in_lista: set[int], filtro_da: str) -> list[str]:
    """Una voce nuova senza regolamento può essere una gara già presente a cui la lista ha cambiato la data:
    senza il numero del regolamento non si può dire con certezza, quindi lo script non unisce: scrive il sospetto
    in note_interne della voce nuova e nel rapporto. Sospetto = una voce esistente, sparita dalla lista letta oggi,
    con stessa città, nome simile e data entro 60 giorni."""
    segnalazioni: list[str] = []
    for nuovo in nuovi:
        for esistente in esistenti:
            if id(esistente) in ancora_in_lista or str(esistente.get("stato")) == "annullato":
                continue
            if filtro_da and str(esistente["data_inizio"]) < filtro_da:
                continue    # più vecchia di ciò che la raccolta ha letto: è normale che non sia in lista
            giorni = giorni_tra(esistente["data_inizio"], nuovo["data_inizio"])
            if giorni == 0 or giorni > 60:
                continue
            if slug_citta(str(esistente["luogo"])) != slug_citta(nuovo["luogo"]) or somiglianza(str(esistente["nome"]), nuovo["nome"]) < 0.6:
                continue
            frase = f"Possibile doppione di {esistente['id']} (stessa città, nome simile, data {esistente['data_inizio']}; quella voce non è più nella lista FISR): controllare prima del merge."
            nuovo["note_interne"] = aggiungi_a_note_interne(nuovo.get("note_interne"), frase)
            segnalazioni.append(f"- `{nuovo['id']}` ↔ `{esistente['id']}`: possibile doppione (stessa città, nome simile, {giorni} giorni di distanza; la voce esistente non è più nella lista)")
    return segnalazioni


def testo_yaml(valore) -> str:
    if isinstance(valore, bool):
        return "true" if valore else "false"
    if isinstance(valore, date):
        return valore.isoformat()
    if isinstance(valore, str):
        if valore == "":
            return '""'
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", valore):
            return valore
        return json.dumps(valore, ensure_ascii=False)
    return json.dumps(valore, ensure_ascii=False)


def emetti_evento(evento: dict) -> str:
    righe = []
    for campo in ORDINE_CAMPI:
        valore = evento.get(campo, "" if campo not in ("categorie", "distanze", "fonti") else [])
        prefisso = "- " if campo == "id" else "  "
        if campo == "fonti":
            righe.append(f"{prefisso}fonti:")
            for fonte in valore:
                righe.append(f"    - url: {fonte['url']}")
                righe.append(f"      letto_il: {testo_yaml(fonte['letto_il'])}")
        elif campo in ("categorie", "distanze"):
            righe.append(f"{prefisso}{campo}: [" + ", ".join(testo_yaml(v) for v in valore) + "]")
        elif campo == "paese":
            righe.append(f"{prefisso}paese: {valore}")
        elif campo in ("tipo", "stato"):
            righe.append(f"{prefisso}{campo}: {valore}")
        elif campo == "id":
            righe.append(f"- id: {valore}")
        else:
            righe.append(f"{prefisso}{campo}: {testo_yaml(valore)}")
    return "\n".join(righe) + "\n"


def principale(argomenti: list[str] | None = None) -> int:
    analizzatore = argparse.ArgumentParser(description="Converte la raccolta fisr.info in voci di eventi.yaml")
    analizzatore.add_argument("--raccolta", type=Path, required=True)
    analizzatore.add_argument("--eventi", type=Path, default=Path("dati/eventi.yaml"))
    analizzatore.add_argument("--scrivi", action="store_true", help="riscrive eventi.yaml (senza: solo rapporto)")
    analizzatore.add_argument("--rapporto", type=Path, default=None, help="scrive il rapporto in Markdown in questo file")
    analizzatore.add_argument("--solo-nome-fonte", action="store_true",
                              help="non crea, non promuove e non aggiorna nulla: registra soltanto nome_fonte dove è vuoto, dal titolo della lista "
                                   "(serve una volta, per dare alle voci già presenti il titolo di una raccolta precedente)")
    opzioni = analizzatore.parse_args(argomenti)

    raccolta = carica_raccolta(opzioni.raccolta)
    letto_il = raccolta["generato_il"][:10]
    rapporto: list[str] = [f"# Conversione raccolta fisr.info del {letto_il}", ""]

    righe = deduplica_righe(raccolta["righe"], rapporto)
    rapporto.append(f"\nRighe: {len(raccolta['righe'])} raccolte → {len(righe)} dopo la deduplica.\n")

    regolamenti = [i for i in raccolta["regolamenti_scansione"] if i.get("dal") and i.get("righe_programma")]
    abbinate, rimaste = abbina_regolamenti(righe, regolamenti, rapporto)
    rapporto.append(f"\nRegolamenti di gara: {len(regolamenti)} dalla scansione; {len(abbinate)} righe con regolamento; {len(rimaste)} regolamenti senza riga nella lista.\n")

    intestazione, esistenti = carica_eventi(opzioni.eventi)
    tracce_prima = {id(voce): coda_arricchimento(voce.get("note_interne")) for voce in esistenti}   # per il controllo in uscita
    nuovi: list[dict] = []
    promossi: list[str] = []
    aggiornati: list[str] = []
    da_controllare: list[str] = []
    in_attesa: list[str] = []
    conteggio_stati: dict[str, int] = {}
    righe_presenti: list[str] = []
    proposte_per_esistente: list[tuple[dict, dict]] = []
    for indice, riga in enumerate(righe):
        evento = costruisci_evento(riga, abbinate.get(indice), letto_il)
        esistente = corrisponde_esistente(evento, esistenti)
        if esistente:
            proposte_per_esistente.append((esistente, evento))
            continue
        nuovi.append(evento)
    for regolamento in rimaste:
        evento = costruisci_evento(None, regolamento, letto_il)
        esistente = corrisponde_esistente(evento, esistenti + nuovi)
        if esistente:
            if any(esistente is voce for voce in esistenti):
                proposte_per_esistente.append((esistente, evento))
            continue
        # Senza la riga della lista manca la località (e l'id la contiene): non diventa una voce, aspetta la lista.
        in_attesa.append(f"- regolamento {regolamento['id_manif']}: {evento['nome']!r}, {evento['data_inizio']}, società {regolamento.get('societa') or '?'}; "
                         f"Master/Amatori nel programma: {', '.join(evento['categorie']) or 'no'}")
    ancora_in_lista = {id(esistente) for esistente, _ in proposte_per_esistente}
    id_occupati = {str(e["id"]) for e in esistenti}
    righe_per_voce: dict[int, int] = {}    # quante righe della lista corrispondono a ciascuna voce
    for esistente, evento in proposte_per_esistente:
        if evento["_dalla_lista"]:
            righe_per_voce[id(esistente)] = righe_per_voce.get(id(esistente), 0) + 1
    rinominati: list[str] = []
    titoli_registrati: list[str] = []
    if opzioni.solo_nome_fonte:
        # Modalità di servizio: solo il titolo della fonte dove manca; tutto il resto della voce resta com'è.
        for esistente, evento in proposte_per_esistente:
            _, registrato = aggiorna_nome(esistente, evento, letto_il, righe_per_voce.get(id(esistente), 0) == 1, solo_registrare=True)
            if registrato:
                titoli_registrati.append(f"- `{esistente['id']}`: «{esistente['nome_fonte']}»")
        proposte_per_esistente, nuovi, in_attesa = [], [], []
    for esistente, evento in proposte_per_esistente:
        id_prima = str(esistente["id"])
        promozione = promuovi(esistente, evento, letto_il)
        if promozione:
            promossi.append(f"- `{id_prima}` ↔ {evento['nome'][:50]!r}: " + "; ".join(promozione))
        # Anche una voce appena promossa è ora legata al regolamento: se le date non coincidono, lo segue subito.
        cambiamenti, dubbi = aggiorna_dal_regolamento(esistente, evento, letto_il, id_occupati)
        for dubbio in dubbi:
            da_controllare.append(f"- `{esistente['id']}`: {dubbio}")
        if cambiamenti:
            aggiornati.append(f"- `{id_prima}` (regolamento {evento['_regolamento']}): " + "; ".join(cambiamenti))
        rinomina, registrato = aggiorna_nome(esistente, evento, letto_il, righe_per_voce.get(id(esistente), 0) == 1)
        if rinomina:
            rinominati.append(f"- `{esistente['id']}`: " + "; ".join(rinomina))
        if registrato:
            titoli_registrati.append(f"- `{esistente['id']}`: «{esistente['nome_fonte']}»")
        if promozione or cambiamenti or rinomina:
            continue
        differenze = []
        if evento["categorie"] and list(esistente.get("categorie") or []) != evento["categorie"]:
            differenze.append(f"categorie proposte {evento['categorie']} (presenti {esistente.get('categorie')})")
        if evento["stato"] != esistente.get("stato"):
            differenze.append(f"stato proposto {evento['stato']} (presente {esistente.get('stato')})")
        righe_presenti.append(f"- `{esistente['id']}` ↔ {evento['nome'][:50]!r}" + (": " + "; ".join(differenze) if differenze else ""))
    da_controllare.extend(segnala_possibili_doppioni(nuovi, esistenti, ancora_in_lista, str(raccolta.get("filtro_da") or "")))
    rapporto.append(f"\n## Voci promosse (prova o autorizzazione arrivate dopo la prima lettura): {len(promossi)}\n")
    rapporto.extend(promossi)
    rapporto.append(f"\n## Regolamenti cambiati (voci aggiornate, prima → dopo): {len(aggiornati)}\n")
    rapporto.extend(aggiornati)
    rapporto.append(f"\n## Nomi aggiornati (la lista federale ha cambiato il titolo): {len(rinominati)}\n")
    rapporto.extend(rinominati)
    if titoli_registrati:
        rapporto.append(f"\n## Titoli della fonte registrati per la prima volta (il nome non cambia): {len(titoli_registrati)}\n")
        rapporto.extend(titoli_registrati)
    rapporto.append(f"\n## Da controllare a mano prima del merge: {len(da_controllare)}\n")
    rapporto.extend(da_controllare)
    rapporto.append("\n## Eventi già presenti (non toccati)\n")
    rapporto.extend(righe_presenti)
    rapporto.append(f"\n## Regolamenti in attesa della lista (nessuna voce creata): {len(in_attesa)}\n")
    rapporto.extend(in_attesa)

    id_visti = {e["id"] for e in esistenti}
    for evento in nuovi:
        base, contatore = evento["id"], 2
        while evento["id"] in id_visti:
            evento["id"] = f"{base}-{contatore}"
            contatore += 1
        id_visti.add(evento["id"])
        conteggio_stati[evento["stato"]] = conteggio_stati.get(evento["stato"], 0) + 1

    rapporto.append(f"\n## Nuovi eventi: {len(nuovi)}\n")
    for stato in sorted(conteggio_stati):
        rapporto.append(f"- {stato}: {conteggio_stati[stato]}")
    rapporto.append("\n| Data | Evento | Luogo | Stato | Categorie | Regolamento |\n|---|---|---|---|---|---|")
    for evento in sorted(nuovi, key=lambda e: e["data_inizio"]):
        id_manif = evento["url_ufficiale"].rsplit("=", 1)[-1] if evento["url_ufficiale"] else "—"
        rapporto.append(f"| {evento['data_inizio']} | {evento['nome']} | {evento['luogo']} | {evento['stato']} | {', '.join(evento['categorie']) or '—'} | {id_manif} |")

    testo_rapporto = "\n".join(rapporto) + "\n"
    if opzioni.rapporto:
        opzioni.rapporto.parent.mkdir(parents=True, exist_ok=True)
        opzioni.rapporto.write_text(testo_rapporto, encoding="utf-8")
    print(testo_rapporto)

    # Controllo in uscita: qualunque cosa lo script abbia scritto in note_interne, la traccia dell'arricchimento
    # deve essere ancora lì, identica e in coda (è ciò che l'agente legge e sostituisce al prossimo ricontrollo).
    tracce_toccate = [str(voce["id"]) for voce in esistenti if coda_arricchimento(voce.get("note_interne")) != tracce_prima[id(voce)]]
    if tracce_toccate:
        print(f"ERRORE: la traccia 'Arricchimento …' in note_interne è cambiata o non è più l'ultima frase in: {tracce_toccate}; eventi.yaml non è stato scritto", file=sys.stderr)
        return 1

    if opzioni.scrivi:
        tutti = sorted(esistenti + nuovi, key=lambda e: (str(e["data_inizio"]), e["id"]))
        contenuto = intestazione + "\n" + "\n".join(emetti_evento(e) for e in tutti)
        opzioni.eventi.write_text(contenuto, encoding="utf-8")
        riletti = yaml.safe_load(opzioni.eventi.read_text(encoding="utf-8"))
        if len(riletti) != len(tutti):
            print(f"ERRORE: scritti {len(tutti)} eventi, riletti {len(riletti)}", file=sys.stderr)
            return 1
        id_riletti = [str(e["id"]) for e in riletti]
        doppi = sorted({i for i in id_riletti if id_riletti.count(i) > 1})
        if doppi:
            print(f"ERRORE: id ripetuti dopo la scrittura: {doppi}", file=sys.stderr)
            return 1
        fuori_data = [str(e["id"]) for e in riletti if not str(e["id"]).startswith(str(e["data_inizio"]) + "-")]
        if fuori_data:
            print(f"ERRORE: la data nell'id non coincide con data_inizio: {fuori_data}", file=sys.stderr)
            return 1
        for prima, dopo in zip(esistenti, [e for e in riletti if e["id"] in {x["id"] for x in esistenti}]):
            pass  # le voci esistenti sono state riemesse: il controllo di contenuto lo fa il diff di git
        print(f"scritto {opzioni.eventi}: {len(esistenti)} esistenti (di cui {len(promossi)} promossi, {len(aggiornati)} aggiornati dal regolamento, {len(rinominati)} rinominati) + {len(nuovi)} nuovi = {len(tutti)} eventi", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(principale())
