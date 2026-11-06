#!/usr/bin/env python3
"""
Costruisce e aggiorna il registro delle società di pattinaggio corsa (dati/societa.yaml).

Da dove vengono i dati, per una stagione (parametro "anno" di fisr.info: 2026 = stagione 2025/26):
  1. Classifiche di società ufficiali su fisr.info → attivita.rollergames.it: Trofeo Tiezzi, Trofeo
     Bonacossa, Campionati Italiani strada/pista/indoor, più i campionati regionali pista e strada
     delle 20 regioni. Ogni riga dà CODICE SOCIETÀ FISR (la chiave del registro), sigla e punti.
  2. Pagine dei risultati di ogni gara della stagione (attivita.rollergames.it/corsa/rrunn/...):
     l'intestazione "Organizzato da ..." dà il nome esteso della società organizzatrice.
  3. Regolamenti di gara (corsa_trofeo_modulo.php?id_manif=N, gli id presi da un JSON di raccolta):
     l'art. 1 dà la sigla della società organizzatrice e il testo spesso riporta il suo sito.

Cosa NON fa: non cerca sul web, non apre i siti delle società, non decide nulla. I siti trovati nei
regolamenti finiscono in `siti_candidati` finché una persona (o l'agente di arricchimento) non li
verifica e li promuove a `sito`. I campi compilati a mano (nome, citta, sito, social, stato_sito,
fonte_sito, note) non vengono mai sovrascritti: lo script aggiunge, non toglie.

Uso:
  python3 script/raccogli_societa.py --anno 2026 --registro dati/societa.yaml \
      [--raccolta registro/AAAA-MM-GG-raccolta-fisr.json] [--rapporto registro/AAAA-MM-GG-societa.md] \
      [--pausa 0.3] [--senza-risultati] [--senza-regolamenti]
  python3 script/raccogli_societa.py --solo-verifica --registro dati/societa.yaml

Controlli: ogni pagina letta deve avere la forma attesa (tabella con codice numerico, intestazione
"Organizzato da"), altrimenti la pagina viene segnalata nel rapporto e ignorata; il registro viene
riletto e validato dopo la scrittura (chiavi, codici unici, URL, date); se qualcosa non torna lo
script si ferma con un messaggio chiaro e non lascia un file a metà.
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
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError as errore:  # pragma: no cover
    sys.exit(f"Manca una dipendenza ({errore}). Installa: pip install -r script/requisiti.txt")

BASE_FISR_INFO = "https://www.fisr.info/attivita/"
BASE_ROLLERGAMES = "https://attivita.rollergames.it/corsa/"
INTESTAZIONE_HTTP = {"User-Agent": "Mozilla/5.0 (calendario pattinaggio corsa; script raccogli_societa.py)"}
REGIONI = {1: "Piemonte", 2: "Valle d'Aosta", 3: "Liguria", 4: "Lombardia", 5: "Trentino-Alto Adige", 6: "Veneto",
           7: "Friuli-Venezia Giulia", 8: "Emilia-Romagna", 9: "Toscana", 10: "Marche", 11: "Umbria", 12: "Lazio",
           13: "Abruzzo", 14: "Molise", 15: "Campania", 16: "Puglia", 17: "Basilicata", 18: "Calabria", 19: "Sicilia", 20: "Sardegna"}
CLASSIFICHE_NAZIONALI = [("tiezzi_red.php?anno={anno}", "Trofeo Tiezzi"), ("bonacossa_red.php?anno={anno}", "Trofeo Bonacossa"),
                         ("italiani_red.php?tipo=IS&anno={anno}", "Campionato Italiano Strada"),
                         ("italiani_red.php?tipo=IP&anno={anno}", "Campionato Italiano Pista"),
                         ("italiani_red.php?tipo=II&anno={anno}", "Campionato Italiano Indoor")]
CHIAVI_SOCIETA = ["codice_fisr", "nome_fisr", "sigle_fisr", "nome", "citta", "regione", "sito", "social", "stato_sito", "fonte_sito",
                  "siti_candidati", "ultima_stagione", "classifiche", "gare_organizzate", "ultimo_controllo", "note"]
STATI_SITO = {"sito_verificato", "sito_da_verificare", "sito_non_raggiungibile", "solo_social", "senza_sito"}
CAMPI_MANUALI = ["nome", "citta", "sito", "social", "stato_sito", "fonte_sito", "note"]
PAROLE_VUOTE = {"ASD", "A", "S", "D", "SSD", "SS", "SRL", "ARL", "POL", "POLISPORTIVA", "PATT", "PATTINATORI", "PATTINAGGIO", "CLUB", "SPORT",
                "SPORTS", "SPORTING", "GRUPPO", "G", "P", "C", "CENTRO", "DIL", "DILETTANTISTICA", "ASSOCIAZIONE", "SOCIETA", "TEAM",
                "ROLLER", "SKATING", "INLINE", "IN", "LINE", "DI", "DEL", "DELLA", "E", "ANSPI", "ADHP", "AHP", "COMITATO", "REGIONALE",
                "FISR", "SKATE", "ITALIA", "TERR", "DELEGATO", "STRUTTURA", "TERRITORIALE", "CUS", "GIO", "RI", "SAN", "SANTA", "SANTO", "ASS", "APD"}
PAROLE_SOCIETARIE = re.compile(r"(?i)\b(a\.?s\.?d|s\.?s\.?d|pol|polisportiva|patt|pattin|skating|skate|roller|rotell|club|gruppo|g\.?s|g\.?p|sport|ass|cus|palestra|centro|team|accademia|circ|inline|in line|anspi|adhp|ahp|csen|uisp|libertas|fiamme)\b")
ESPRESSIONE_URL = re.compile(r"(?:https?://|www\.)[A-Za-z0-9.\-]+\.[A-Za-z]{2,}(?:/[^\s\"'<>,;)]*)?")


def stagione_da_anno(anno: int) -> str:
    return f"{anno - 1}/{str(anno)[-2:]}"


def scarica(url: str, dati: dict | None = None, pausa: float = 0.3) -> str:
    """Scarica una pagina (GET o POST), prova UTF-8 poi cp1252. Solleva RuntimeError se non risponde."""
    corpo = urllib.parse.urlencode(dati).encode() if dati else None
    richiesta = urllib.request.Request(url, data=corpo, headers=INTESTAZIONE_HTTP)
    ultimo_errore: Exception | None = None
    for tentativo in range(3):  # i server federali chiudono la connessione ogni tanto: si riprova
        try:
            with urllib.request.urlopen(richiesta, timeout=40) as risposta:
                grezzo = risposta.read()
            break
        except (urllib.error.URLError, TimeoutError, OSError) as errore:
            ultimo_errore = errore
            time.sleep(pausa * (tentativo + 1) + 1.0)
        finally:
            time.sleep(pausa)
    else:
        raise RuntimeError(f"{url}: {ultimo_errore}")
    try:
        return grezzo.decode("utf-8")
    except UnicodeDecodeError:
        return grezzo.decode("cp1252", errors="replace")


def testo_piatto(pagina: str, separatore: str = " ") -> str:
    senza_codice = re.sub(r"<script.*?</script>|<style.*?</style>", " ", pagina, flags=re.S | re.I)
    testo = html.unescape(re.sub(r"<[^>]+>", separatore, senza_codice)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", testo).strip()


def righe_classifica(pagina: str) -> list[tuple[str, str]]:
    """(codice, sigla) da una tabella 'Pos | Codice | Societa' | Punti'."""
    trovate: list[tuple[str, str]] = []
    for riga in re.findall(r"<tr[^>]*>(.*?)</tr>", pagina, flags=re.S | re.I):
        celle = [testo_piatto(cella) for cella in re.findall(r"<td[^>]*>(.*?)</td>", riga, flags=re.S | re.I)]
        celle = [cella for cella in celle if cella]
        if len(celle) >= 4 and celle[0].isdigit() and celle[1].isdigit() and celle[2]:
            trovate.append((celle[1], celle[2]))
    return trovate


def normalizza(nome: str) -> list[str]:
    """Parole significative di un nome di società, per il confronto approssimato."""
    senza_accenti = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().upper()
    compattato = re.sub(r"\b((?:[A-Z]\.){2,})", lambda m: m.group(1).replace(".", "") + " ", senza_accenti)  # C.P.G.A. → CPGA
    parole = re.sub(r"[^A-Z0-9 ]+", " ", compattato.replace(".", " ").replace("'", " ")).split()
    return [parola for parola in parole if parola not in PAROLE_VUOTE and len(parola) >= 3]


def somiglianza(a: str, b: str) -> float:
    """Quota delle parole del nome b (la sigla del registro) ritrovate nel nome a, anche per prefisso: 0..1."""
    parole_a, parole_b = normalizza(a), normalizza(b)
    if not parole_a or not parole_b:
        return 0.0

    def uguali(x: str, y: str) -> bool:
        return x == y or (len(x) >= 4 and len(y) >= 4 and (x.startswith(y) or y.startswith(x)))

    comuni = sum(1 for y in parole_b if any(uguali(x, y) for x in parole_a))
    return comuni / len(parole_b)


def abbina(nome: str, registro: dict[str, dict]) -> str | None:
    """Codice della società che somiglia di più al nome, solo se la scelta è netta."""
    def compatta(testo: str) -> str:
        return re.sub(r"[\s.]+", "", testo).upper()

    for codice, voce in registro.items():  # sigla identica: nessun dubbio
        if compatta(nome) in {compatta(s) for s in [voce["nome_fisr"], voce.get("nome") or "", *voce.get("sigle_fisr", [])] if s}:
            return codice
    candidati: list[tuple[float, int, str]] = []
    for codice, voce in registro.items():
        nomi = [voce["nome_fisr"], voce.get("nome") or ""] + list(voce.get("sigle_fisr") or [])
        migliore = (0.0, 0)
        for altro in nomi:
            if not altro:
                continue
            copertura = somiglianza(nome, altro)
            comuni = round(copertura * len(normalizza(altro)))
            migliore = max(migliore, (copertura, comuni))
        candidati.append((migliore[0], migliore[1], codice))
    candidati.sort(reverse=True)
    if not candidati or candidati[0][0] < 0.6:
        return None
    if len(candidati) > 1:
        primo, secondo = candidati[0], candidati[1]
        if primo[0] - secondo[0] < 0.2 and primo[1] <= secondo[1]:
            return None  # due società troppo simili (es. tre società a Pescara): decide una persona
    return candidati[0][2]


def voce_nuova(codice: str, sigla: str) -> dict:
    return {"codice_fisr": codice, "nome_fisr": sigla, "sigle_fisr": [sigla], "nome": "", "citta": "", "regione": "", "sito": "",
            "social": "", "stato_sito": "senza_sito", "fonte_sito": "", "siti_candidati": [], "ultima_stagione": "", "classifiche": [],
            "gare_organizzate": [], "ultimo_controllo": "", "note": ""}


def carica_registro(percorso: Path) -> dict[str, dict]:
    if not percorso.is_file():
        return {}
    dati = yaml.safe_load(percorso.read_text(encoding="utf-8"))
    if dati is None:
        return {}
    if not isinstance(dati, list):
        sys.exit(f"{percorso}: atteso un elenco di società, trovato {type(dati).__name__}")
    registro: dict[str, dict] = {}
    for voce in dati:
        errori = valida_voce(voce)
        if errori:
            sys.exit(f"{percorso}: voce non valida {voce.get('codice_fisr') if isinstance(voce, dict) else voce!r}: " + "; ".join(errori))
        chiave = voce["codice_fisr"] or f"senza-codice:{voce['nome_fisr']}"
        if chiave in registro:
            sys.exit(f"{percorso}: codice società duplicato: {chiave}")
        registro[chiave] = voce
    return registro


def valida_voce(voce) -> list[str]:
    errori: list[str] = []
    if not isinstance(voce, dict):
        return [f"non è un dizionario: {voce!r}"]
    mancanti = [chiave for chiave in CHIAVI_SOCIETA if chiave not in voce]
    estranee = [chiave for chiave in voce if chiave not in CHIAVI_SOCIETA]
    if mancanti:
        errori.append(f"chiavi mancanti: {mancanti}")
    if estranee:
        errori.append(f"chiavi sconosciute: {estranee}")
    if mancanti or estranee:
        return errori
    if not isinstance(voce["codice_fisr"], str) or (voce["codice_fisr"] and not voce["codice_fisr"].isdigit()):
        errori.append("codice_fisr deve essere una stringa di cifre o vuota")
    if not isinstance(voce["nome_fisr"], str) or not voce["nome_fisr"].strip():
        errori.append("nome_fisr obbligatorio")
    for chiave in ("sigle_fisr", "siti_candidati", "classifiche", "gare_organizzate"):
        if not isinstance(voce[chiave], list) or not all(isinstance(x, str) for x in voce[chiave]):
            errori.append(f"{chiave} deve essere una lista di testi")
    for chiave in ("nome", "citta", "regione", "social", "fonte_sito", "ultima_stagione", "note", "sito"):
        if not isinstance(voce[chiave], str):
            errori.append(f"{chiave} deve essere un testo")
    for chiave in ("sito", "social"):
        if isinstance(voce[chiave], str) and voce[chiave] and not re.match(r"^https?://", voce[chiave]):
            errori.append(f"{chiave} deve iniziare con http(s)://")
    if voce["stato_sito"] not in STATI_SITO:
        errori.append(f"stato_sito deve essere uno tra {sorted(STATI_SITO)}")
    if voce["stato_sito"] in {"sito_verificato", "sito_da_verificare", "sito_non_raggiungibile"} and not voce["sito"]:
        errori.append(f"stato_sito {voce['stato_sito']} richiede un sito")
    if voce["stato_sito"] == "solo_social" and not voce["social"]:
        errori.append("stato_sito solo_social richiede un social")
    if voce["stato_sito"] == "senza_sito" and voce["sito"]:
        errori.append("stato_sito senza_sito ma sito compilato")
    controllo = voce["ultimo_controllo"]
    if not (controllo == "" or isinstance(controllo, date)):
        errori.append("ultimo_controllo deve essere una data ISO o vuoto")
    return errori


def scrivi_registro(percorso: Path, registro: dict[str, dict]) -> None:
    """YAML ordinato per codice, chiavi nell'ordine dello schema, testi tra doppi apici; poi rilettura e validazione."""
    def ordine(chiave: str) -> tuple[int, str]:
        voce = registro[chiave]
        return (0, voce["codice_fisr"].zfill(6)) if voce["codice_fisr"] else (1, voce["nome_fisr"])

    def testo_yaml(valore: str) -> str:
        return json.dumps(valore, ensure_ascii=False)

    righe = ["# Registro delle società di pattinaggio corsa (chiave: codice società FISR).",
             "# Generato e aggiornato da script/raccogli_societa.py; i campi nome, citta, sito, social, stato_sito,",
             "# fonte_sito e note si compilano a mano o dall'arricchimento e lo script non li tocca. Schema in CLAUDE.md.", ""]
    for chiave in sorted(registro, key=ordine):
        voce = registro[chiave]
        righe.append(f"- codice_fisr: {testo_yaml(voce['codice_fisr'])}")
        for campo in CHIAVI_SOCIETA[1:]:
            valore = voce[campo]
            if isinstance(valore, list):
                righe.append(f"  {campo}: [{', '.join(testo_yaml(x) for x in valore)}]")
            elif isinstance(valore, date):
                righe.append(f"  {campo}: {valore.isoformat()}")
            else:
                righe.append(f"  {campo}: {testo_yaml(valore)}")
        righe.append("")
    contenuto = "\n".join(righe)
    riletto = yaml.safe_load(contenuto)
    if not isinstance(riletto, list) or len(riletto) != len(registro):
        sys.exit("errore interno: il registro riletto non corrisponde a quello scritto")
    for voce in riletto:
        errori = valida_voce(voce)
        if errori:
            sys.exit(f"errore interno: voce non valida dopo la scrittura ({voce.get('codice_fisr')}): {errori}")
    percorso.write_text(contenuto, encoding="utf-8")


def leggi_classifiche(anno: int, pausa: float, rapporto: list[str]) -> dict[str, dict]:
    """Codice → {sigle, classifiche, regioni} dalle classifiche nazionali e regionali della stagione."""
    trovate: dict[str, dict] = {}

    def aggiungi(righe: list[tuple[str, str]], etichetta: str, regione: str = "") -> None:
        for codice, sigla in righe:
            voce = trovate.setdefault(codice, {"sigle": set(), "classifiche": set(), "regioni": set()})
            voce["sigle"].add(sigla)
            voce["classifiche"].add(etichetta)
            if regione:
                voce["regioni"].add(regione)

    for percorso, etichetta in CLASSIFICHE_NAZIONALI:
        url = BASE_ROLLERGAMES + percorso.format(anno=anno)
        try:
            righe = righe_classifica(scarica(url, pausa=pausa))
        except RuntimeError as errore:
            rapporto.append(f"- classifica {etichetta}: NON LETTA ({errore})")
            continue
        if not righe:
            rapporto.append(f"- classifica {etichetta}: nessuna riga riconosciuta ({url})")
        aggiungi(righe, f"{etichetta} {stagione_da_anno(anno)}")
        rapporto.append(f"- classifica {etichetta}: {len(righe)} società")
    for numero, regione in REGIONI.items():
        for tipo, nome_tipo in (("P", "pista"), ("S", "strada")):
            try:
                pagina = scarica(BASE_FISR_INFO + "corsa_campionati_locali.php", {"anno": anno, "cosa": "R", "id_regione": numero, "tipo": tipo}, pausa)
            except RuntimeError as errore:
                rapporto.append(f"- campionato regionale {nome_tipo} {regione}: NON LETTO ({errore})")
                continue
            righe = righe_classifica(pagina)
            aggiungi(righe, f"Campionato regionale {nome_tipo} {regione} {stagione_da_anno(anno)}", regione)
            if righe:
                rapporto.append(f"- campionato regionale {nome_tipo} {regione}: {len(righe)} società")
    return trovate


def leggi_risultati(anno: int, pausa: float, rapporto: list[str]) -> list[dict]:
    """Per ogni gara della stagione: titolo, luogo e data, 'Organizzato da'."""
    try:
        lista = scarica(BASE_FISR_INFO + "corsa_risultati.php", {"anno": anno}, pausa)
    except RuntimeError as errore:
        rapporto.append(f"- risultati: lista NON LETTA ({errore})")
        return []
    collegamenti = [c.replace("/media/../", "/") for c in re.findall(r'href="(https?://attivita\.rollergames\.it[^"]+)"', lista)]
    gare: list[dict] = []
    for url in collegamenti:
        try:
            testo = testo_piatto(scarica(url, pausa=pausa), " | ")
        except RuntimeError as errore:
            rapporto.append(f"- gara non letta: {url} ({errore})")
            continue
        corrispondenza = re.search(r"\| ([^|]+?) \| ([^|]+?) \| Organizzato da ([^|]+?) \|", testo)
        if not corrispondenza:
            rapporto.append(f"- gara senza 'Organizzato da': {url}")
            continue
        gare.append({"url": url, "titolo": corrispondenza.group(1).strip(), "luogo_data": corrispondenza.group(2).strip(),
                     "organizzato_da": corrispondenza.group(3).strip()})
    rapporto.append(f"- risultati: {len(collegamenti)} gare nella lista, {len(gare)} con organizzatore")
    return gare


def id_regolamenti(percorso: Path) -> list[str]:
    dati = json.loads(percorso.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for riga in dati.get("righe") or []:
        if riga.get("id_manif"):
            ids.add(str(riga["id_manif"]))
    for regolamento in dati.get("regolamenti_scansione") or []:
        if regolamento.get("id_manif"):
            ids.add(str(regolamento["id_manif"]))
    return sorted(ids, key=int)


def leggi_regolamenti(ids: list[str], pausa: float, rapporto: list[str]) -> list[dict]:
    """Per ogni regolamento: sigla della società (art. 1) e siti non federali citati nel testo."""
    trovati: list[dict] = []
    for id_manif in ids:
        url = f"{BASE_FISR_INFO}corsa_trofeo_modulo.php?id_manif={id_manif}"
        try:
            testo = testo_piatto(scarica(url, pausa=pausa))
        except RuntimeError as errore:
            rapporto.append(f"- regolamento {id_manif} non letto ({errore})")
            continue
        societa = re.search(r"La Societ\S* Sportiva (.+?) con l'approvazione", testo)
        if not societa:
            continue  # bozza vuota o pagina diversa
        siti = sorted({u.rstrip(".") for u in ESPRESSIONE_URL.findall(testo) if "fisr" not in u.lower() and "federazione" not in u.lower()})
        trovati.append({"id_manif": id_manif, "societa": societa.group(1).strip(), "siti": siti})
    rapporto.append(f"- regolamenti: {len(ids)} letti, {sum(1 for r in trovati if r['siti'])} con un sito non federale")
    return trovati


def url_normale(url: str) -> str:
    url = url if url.lower().startswith("http") else "https://" + url
    return url.rstrip("?")


def aggiorna_registro(registro: dict[str, dict], anno: int, classifiche: dict[str, dict], gare: list[dict], regolamenti: list[dict],
                      oggi: date, rapporto: list[str]) -> None:
    stagione = stagione_da_anno(anno)
    nuove = 0
    for codice, trovata in classifiche.items():
        voce = registro.get(codice)
        if voce is None:
            voce = registro[codice] = voce_nuova(codice, sorted(trovata["sigle"])[0])
            nuove += 1
        voce["sigle_fisr"] = sorted(set(voce["sigle_fisr"]) | trovata["sigle"])
        if voce["nome_fisr"] not in voce["sigle_fisr"]:
            voce["sigle_fisr"].append(voce["nome_fisr"])
        if not voce["regione"] and trovata["regioni"]:
            voce["regione"] = ", ".join(sorted(trovata["regioni"]))
        if voce["ultima_stagione"] == stagione:
            voce["classifiche"] = sorted(set(voce["classifiche"]) | trovata["classifiche"])  # stessa stagione: si aggiunge, non si toglie
        else:
            voce["classifiche"] = sorted(trovata["classifiche"])
        voce["ultima_stagione"] = stagione
        voce["gare_organizzate"] = []  # i risultati si rileggono tutti: l'elenco si ricostruisce
    rapporto.append(f"- società nelle classifiche: {len(classifiche)}, nuove nel registro: {nuove}")

    non_abbinati: set[str] = set()
    senza_sigla = 0
    for gara in gare:
        for parte in re.split(r"\s+-\s+(?=A\.S\.D|ASD)|/", gara["organizzato_da"]):
            nome = parte.strip()
            if not nome or re.match(r"(?i)^(comitato|struttura|skate italia|delegato)", nome):
                continue
            codice = abbina(nome, registro)
            if codice is None:
                if PAROLE_SOCIETARIE.search(nome):
                    non_abbinati.add(nome)
                else:
                    senza_sigla += 1  # probabile nome di persona: non va trascritto da nessuna parte (regola 9)
                continue
            voce = registro[codice]
            if nome.upper() != voce["nome_fisr"].upper() and (not voce["nome"] or (voce["nome"].upper() == voce["nome_fisr"].upper())):
                voce["nome"] = nome  # il nome esteso dei risultati vale solo se dice più della sigla
            etichetta = f"{gara['titolo']} ({gara['luogo_data']})"
            if etichetta not in voce["gare_organizzate"]:
                voce["gare_organizzate"].append(etichetta)
    if non_abbinati:
        rapporto.append("- organizzatori nei risultati NON abbinati a un codice (da sistemare a mano): " + "; ".join(sorted(non_abbinati)))
    if senza_sigla:
        rapporto.append(f"- organizzatori senza sigla societaria (probabili nomi di persona), ignorati e non trascritti: {senza_sigla}")

    for regolamento in regolamenti:
        codice = abbina(regolamento["societa"], registro)
        if codice is None:
            if regolamento["siti"]:
                rapporto.append(f"- regolamento {regolamento['id_manif']}: società '{regolamento['societa']}' non abbinata, siti {regolamento['siti']}")
            continue
        voce = registro[codice]
        for sito in regolamento["siti"]:
            sito = url_normale(sito)
            if sito != voce["sito"] and sito not in voce["siti_candidati"]:
                voce["siti_candidati"].append(sito)
                rapporto.append(f"- {voce['nome_fisr']} ({codice}): sito candidato {sito} dal regolamento {regolamento['id_manif']}")
    for voce in registro.values():
        voce["ultimo_controllo"] = voce["ultimo_controllo"] or ""
        if voce["codice_fisr"] in classifiche:
            voce["ultimo_controllo"] = oggi


def principale(argomenti: list[str] | None = None) -> int:
    analizzatore = argparse.ArgumentParser(description="Registro delle società di pattinaggio corsa da fisr.info.")
    analizzatore.add_argument("--anno", type=int, help="parametro 'anno' di fisr.info: 2026 = stagione 2025/26")
    analizzatore.add_argument("--registro", type=Path, default=Path("dati/societa.yaml"))
    analizzatore.add_argument("--raccolta", type=Path, help="JSON di raccogli_fisr.py da cui prendere gli id dei regolamenti")
    analizzatore.add_argument("--rapporto", type=Path, help="file Markdown del rapporto (altrimenti su stdout)")
    analizzatore.add_argument("--pausa", type=float, default=0.3)
    analizzatore.add_argument("--senza-risultati", action="store_true", help="non leggere le pagine dei risultati")
    analizzatore.add_argument("--senza-regolamenti", action="store_true", help="non leggere i regolamenti")
    analizzatore.add_argument("--solo-verifica", action="store_true", help="valida il registro e basta")
    opzioni = analizzatore.parse_args(argomenti)

    registro = carica_registro(opzioni.registro)
    if opzioni.solo_verifica:
        print(f"{opzioni.registro}: {len(registro)} società, nessun errore")
        return 0
    if not opzioni.anno or opzioni.anno < 2002:
        sys.exit("serve --anno (es. 2026 per la stagione 2025/26)")
    oggi = date.today()
    rapporto = [f"# Registro delle società: aggiornamento del {oggi.isoformat()} (stagione {stagione_da_anno(opzioni.anno)})", ""]
    classifiche = leggi_classifiche(opzioni.anno, opzioni.pausa, rapporto)
    if not classifiche:
        sys.exit("nessuna società letta dalle classifiche: mi fermo senza toccare il registro")
    gare = [] if opzioni.senza_risultati else leggi_risultati(opzioni.anno, opzioni.pausa, rapporto)
    regolamenti: list[dict] = []
    if not opzioni.senza_regolamenti and opzioni.raccolta:
        if not opzioni.raccolta.is_file():
            sys.exit(f"file di raccolta non trovato: {opzioni.raccolta}")
        regolamenti = leggi_regolamenti(id_regolamenti(opzioni.raccolta), opzioni.pausa, rapporto)
    aggiorna_registro(registro, opzioni.anno, classifiche, gare, regolamenti, oggi, rapporto)
    scrivi_registro(opzioni.registro, registro)
    con_sito = sum(1 for v in registro.values() if v["sito"])
    con_candidati = sum(1 for v in registro.values() if v["siti_candidati"])
    rapporto += ["", f"Registro scritto: {len(registro)} società, {con_sito} con sito, {con_candidati} con siti candidati da verificare."]
    testo = "\n".join(rapporto) + "\n"
    if opzioni.rapporto:
        opzioni.rapporto.write_text(testo, encoding="utf-8")
    print(testo)
    return 0


if __name__ == "__main__":
    sys.exit(principale())
