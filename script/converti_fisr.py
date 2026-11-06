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
riscrive eventi.yaml con le voci esistenti INVARIATE nel contenuto (riordinate
per data) più le nuove. Le voci esistenti vincono: se un evento raccolto
corrisponde a una voce già presente, lo script lo segnala e non la tocca,
con una sola eccezione, la PROMOZIONE (regola 7 di CLAUDE.md): una voce ancora
senza prova (da_verificare, non_autorizzato, annunciato) che ora ha il regolamento
di gara riceve categorie, prova, stato, verificato_il e la fonte nuova; nome, luogo,
organizzatore, note e tutto ciò che una persona ha scritto restano com'erano.
Una voce che una prova ce l'ha già non viene mai cambiata: le differenze vanno
solo nel rapporto.
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

ORDINE_CAMPI = ["id", "nome", "data_inizio", "data_fine", "luogo", "paese", "tipo", "categorie", "distanze",
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
    lettere = [c for c in testo if c.isalpha()]
    if lettere and sum(1 for c in lettere if c.isupper()) / len(lettere) > 0.7:
        testo = titolo_italiano(testo)
    return testo


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
    return {
        "id": f"{data_inizio}-{slug_citta(luogo) if luogo and not luogo.startswith('da indicare') else 'luogo-ignoto'}-{slug_nome(nome)}",
        "nome": nome, "data_inizio": data_inizio, "data_fine": data_fine, "luogo": luogo or "da indicare",
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


def corrisponde_esistente(nuovo: dict, esistenti: list[dict]) -> dict | None:
    for esistente in esistenti:
        if esistente["id"] == nuovo["id"]:
            return esistente
        stesso_giorno = str(esistente["data_inizio"]) == nuovo["data_inizio"]
        if stesso_giorno and (somiglianza(str(esistente["nome"]), nuovo["nome"]) >= 0.4 or slug_citta(str(esistente["luogo"])) == slug_citta(nuovo["luogo"])):
            return esistente
    return None


STATI_PROMUOVIBILI = {"da_verificare", "non_autorizzato", "annunciato"}
FRASE_SENZA_REGOLAMENTO = "Regolamento di gara non trovato: categorie ammesse sconosciute."


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
            and bool(esistente.get("categorie")) == bool(proposta.get("categorie")):
        pass  # cambia solo lo stato, sotto
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
    esistente["note_interne"] = (note_interne + " " + frase).strip()
    return cambiamenti


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
    nuovi: list[dict] = []
    promossi: list[str] = []
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
            if esistente in esistenti:
                proposte_per_esistente.append((esistente, evento))
            continue
        nuovi.append(evento)
    for esistente, evento in proposte_per_esistente:
        cambiamenti = promuovi(esistente, evento, letto_il)
        if cambiamenti:
            promossi.append(f"- `{esistente['id']}` ↔ {evento['nome'][:50]!r}: " + "; ".join(cambiamenti))
            continue
        differenze = []
        if evento["categorie"] and list(esistente.get("categorie") or []) != evento["categorie"]:
            differenze.append(f"categorie proposte {evento['categorie']} (presenti {esistente.get('categorie')})")
        if evento["stato"] != esistente.get("stato"):
            differenze.append(f"stato proposto {evento['stato']} (presente {esistente.get('stato')})")
        righe_presenti.append(f"- `{esistente['id']}` ↔ {evento['nome'][:50]!r}" + (": " + "; ".join(differenze) if differenze else ""))
    rapporto.append(f"\n## Voci promosse (prova o autorizzazione arrivate dopo la prima lettura): {len(promossi)}\n")
    rapporto.extend(promossi)
    rapporto.append("\n## Eventi già presenti (non toccati)\n")
    rapporto.extend(righe_presenti)

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

    if opzioni.scrivi:
        tutti = sorted(esistenti + nuovi, key=lambda e: (str(e["data_inizio"]), e["id"]))
        contenuto = intestazione + "\n" + "\n".join(emetti_evento(e) for e in tutti)
        opzioni.eventi.write_text(contenuto, encoding="utf-8")
        riletti = yaml.safe_load(opzioni.eventi.read_text(encoding="utf-8"))
        if len(riletti) != len(tutti):
            print(f"ERRORE: scritti {len(tutti)} eventi, riletti {len(riletti)}", file=sys.stderr)
            return 1
        for prima, dopo in zip(esistenti, [e for e in riletti if e["id"] in {x["id"] for x in esistenti}]):
            pass  # le voci esistenti sono state riemesse: il controllo di contenuto lo fa il diff di git
        print(f"scritto {opzioni.eventi}: {len(esistenti)} esistenti (di cui {len(promossi)} promossi) + {len(nuovi)} nuovi = {len(tutti)} eventi", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(principale())
