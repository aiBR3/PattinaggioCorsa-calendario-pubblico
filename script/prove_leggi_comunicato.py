#!/usr/bin/env python3
"""
prove_leggi_comunicato.py — prove automatiche di leggi_comunicato.py su PDF costruiti.

Non legge la rete e non tocca dati/comunicati.yaml: costruisce piccoli PDF di prova, risposte finte del sito e file temporanei. Protegge la decisione del 2026-11-26:
  - si leggono solo i comunicati elencati in dati/comunicati.yaml, e l'indirizzo viene da lì;
  - la risposta deve arrivare da www.fisr.it ed essere davvero un PDF, entro la dimensione massima;
  - un PDF senza testo, cifrato o illeggibile dà un errore chiaro, mai un testo vuoto;
  - email e telefoni riconoscibili dalla forma escono oscurati, mentre date, orari e distanze restano;
  - pypdf si importa anche dove le librerie di crittografia del sistema sono guaste.
Nomi, numeri e indirizzi usati qui sono inventati.

Uso:
    python3 script/prove_leggi_comunicato.py

Esce con 0 se tutte le prove passano, con 1 altrimenti (dopo averle elencate tutte).
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import urllib.error
from pathlib import Path

CARTELLA_SCRIPT = Path(__file__).resolve().parent
if not (CARTELLA_SCRIPT / "leggi_comunicato.py").is_file():
    sys.exit(f"Non trovo leggi_comunicato.py in {CARTELLA_SCRIPT}")
sys.path.insert(0, str(CARTELLA_SCRIPT))

import leggi_comunicato as l  # noqa: E402 — va importato dopo aver aggiunto la cartella degli script al percorso
import raccogli_comunicati as c  # noqa: E402

PERCORSO = "/corsa/comunicati-ufficiali/category/601-2026.html"
INDIRIZZO = f"https://www.fisr.it{PERCORSO}?download=13287"
COMUNICATO = {"id_scaricamento": 13287, "anno": 2026, "pubblicato_il": "2026-07-25", "titolo": "CU 37 Campionato di prova cat. A/J/S/M - Provopoli (PR)", "url": INDIRIZZO, "stato": "nuovo", "esito": ""}
TELEFONO, EMAIL = "349 66 00 000", "mario.rossi@clubdiprova.example"
PRIMA_PAGINA = ["CU n. 37 del 24 luglio 2026", "CAMPIONATO ITALIANO CORSA SU STRADA - CAT. A/J/S/M - F/M", "PROVOPOLI (PR) 03 - 06 SETTEMBRE 2026",
                f"RESPONSABILE ORGANIZZAZIONE - Sig. Mario Rossi Cell . {TELEFONO}", "ISCRIZIONI - Online sul sito federale, entro il 15 agosto 2026",
                f"ORGANIZZAZIONE - A.S.D. Club di Prova e -mail: {EMAIL}", "Categoria Master F/M m 5.000 in linea m 10.000 in linea"]
SECONDA_PAGINA = ["PROGRAMMA GARE DI MASSIMA", "Sabato 5 settembre 5.000 in linea Master F/M Finali, dalle 17.00 alle 21.00", "Per informazioni https://clubdiprova.example/campionato"]


def pdf_di_prova(pagine: list[list[str]]) -> bytes:
    """Un PDF minimo e valido, con una riga di testo per ogni elemento: abbastanza per provare la lettura senza dipendere da file veri."""
    def testo_pdf(riga: str) -> bytes:
        return riga.encode("cp1252").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")

    figli = " ".join(f"{4 + 2 * indice} 0 R" for indice in range(len(pagine)))
    oggetti = [b"<< /Type /Catalog /Pages 2 0 R >>", f"<< /Type /Pages /Kids [{figli}] /Count {len(pagine)} >>".encode("ascii"),
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    for indice, righe in enumerate(pagine):
        contenuto = b"BT /F1 11 Tf 14 TL 50 780 Td " + b" ".join(b"(" + testo_pdf(riga) + b") Tj T*" for riga in righe) + b" ET"
        oggetti.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * indice} 0 R >>".encode("ascii"))
        oggetti.append(b"<< /Length " + str(len(contenuto)).encode("ascii") + b" >>\nstream\n" + contenuto + b"\nendstream")
    corpo = b"%PDF-1.4\n"
    posizioni = []
    for numero, oggetto in enumerate(oggetti, start=1):
        posizioni.append(len(corpo))
        corpo += f"{numero} 0 obj\n".encode("ascii") + oggetto + b"\nendobj\n"
    inizio_tabella = len(corpo)
    corpo += f"xref\n0 {len(oggetti) + 1}\n".encode("ascii") + b"0000000000 65535 f \n" + b"".join(f"{posizione:010d} 00000 n \n".encode("ascii") for posizione in posizioni)
    return corpo + f"trailer\n<< /Size {len(oggetti) + 1} /Root 1 0 R >>\nstartxref\n{inizio_tabella}\n%%EOF\n".encode("ascii")


class RispostaFinta:
    """Ciò che lo script guarda di una risposta del sito: indirizzo finale, stato, tipo dichiarato, corpo."""

    def __init__(self, corpo: bytes, indirizzo: str = INDIRIZZO, tipo: str = "application/pdf", stato: int = 200):
        self.corpo, self.indirizzo, self.tipo, self.status = corpo, indirizzo, tipo, stato
        self.headers = self

    def __enter__(self):
        return self

    def __exit__(self, *_argomenti):
        return False

    def geturl(self) -> str:
        return self.indirizzo

    def get_content_type(self) -> str:
        return self.tipo

    def read(self, quanti: int) -> bytes:
        return self.corpo[:quanti]


def principale() -> int:
    esiti: list[bool] = []

    def verifica(nome: str, condizione: bool, dettaglio: object = "") -> None:
        esiti.append(bool(condizione))
        print(("ok      " if condizione else "FALLITA ") + nome + ("" if condizione else f"  →  {dettaglio!r}"))

    def errore_di(funzione, *argomenti, **parole) -> str:
        """Il messaggio dell'errore previsto, oppure stringa vuota se la funzione non si è fermata."""
        try:
            funzione(*argomenti, **parole)
        except l.ErroreComunicati as errore:
            return str(errore) or "errore senza messaggio"
        return ""

    def esegui(*argomenti: str) -> tuple[int, str, str]:
        uscita, errori = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(uscita), contextlib.redirect_stderr(errori):
            codice = l.principale(list(argomenti))
        return codice, uscita.getvalue(), errori.getvalue()

    # --- 1. Contatti oscurati, tutto il resto intatto -------------------------------------------------------------
    oscurati = [(f"Cell . {TELEFONO}", "Cell . [telefono omesso]"), ("T. +39 06 0000 0001 • F. +39 06 00000002", "T. [telefono omesso] • F. [telefono omesso]"),
                ("Tel: 0586/000000 oppure 0039 0586 000001", "Tel: [telefono omesso] oppure [telefono omesso]"), ("cellulare 3496600000, fax 0586.000.000", "cellulare [telefono omesso], fax [telefono omesso]"),
                (f"e -mail: {EMAIL}", "e -mail: [omesso]@clubdiprova.example"), ("scrivere a segreteria @ federazione-di-prova.example entro lunedì", "scrivere a [omesso]@federazione-di-prova.example entro lunedì"),
                ("info.gare@club di prova. example e nome.cognome@posta. example", "[omesso]@club di prova. example e [omesso]@posta. example")]
    for numero, (grezzo, atteso) in enumerate(oscurati, start=1):
        verifica(f"1.{numero} oscurato: {atteso!r}", l.oscura_contatti(grezzo) == atteso and l.oscura_contatti(atteso) == atteso, l.oscura_contatti(grezzo))
    intatti = ["CAMPIONATO ITALIANO STRADA MASTER - M. 5000 IN LINEA M/F 2025/26", "DATA: 03 - 06 Settembre 2026", "entro il 15/08/2026 alle ore 17:00 del 2 settembre 2026", "m 300 500 1000 3000 5.000 10.000 15.000 eliminazione",
                "Categoria F 2012 2013 2014 e categoria T 10 000 000", "CU n. 37 del 24 luglio 2026, Art. 16.8.2 delle Norme", "Viale di Prova, 74 - 00196 Roma", "anello stradale, sviluppo 406 metri, quota 12,00 euro",
                "https://clubdiprova.example/campionato-2026/iscrizioni"]
    verifica("1. date, orari, distanze, categorie, articoli, CAP e indirizzi web restano come sono", all(l.oscura_contatti(testo) == testo for testo in intatti), [testo for testo in intatti if l.oscura_contatti(testo) != testo])
    verifica("1. la pulizia toglie caratteri di controllo, spazi doppi e righe vuote ripetute", l.ripulisci_pagina("  Riga\x00 uno ​ \t  fine  \r\n\r\n\n\nRiga due\x1b[31m  \n\n") == "Riga uno fine\n\nRiga due [31m", l.ripulisci_pagina("  Riga\x00 uno ​ \t  fine  \r\n\r\n\n\nRiga due\x1b[31m  \n\n"))

    # --- 2. Dal PDF al testo ---------------------------------------------------------------------------------------
    pdf = pdf_di_prova([PRIMA_PAGINA, SECONDA_PAGINA])
    pagine, totale, troncato = l.testo_del_pdf(pdf)
    verifica("2. un PDF di due pagine: il testo di ciascuna, nell'ordine", totale == 2 and not troncato and len(pagine) == 2 and "CAMPIONATO ITALIANO CORSA SU STRADA" in pagine[0] and "m 5.000 in linea m 10.000 in linea" in pagine[0]
             and pagine[1].startswith("PROGRAMMA GARE DI MASSIMA") and "dalle 17.00 alle 21.00" in pagine[1], (totale, troncato, pagine))
    verifica("2. email e telefono del PDF escono oscurati, date e scadenze no", TELEFONO not in pagine[0] and EMAIL not in pagine[0] and "[omesso]@clubdiprova.example" in pagine[0] and "Cell . [telefono omesso]" in pagine[0]
             and "03 - 06 SETTEMBRE 2026" in pagine[0] and "entro il 15 agosto 2026" in pagine[0], pagine[0])
    verifica("2. un file che non è un PDF viene rifiutato", "non è un PDF" in errore_di(l.testo_del_pdf, b"<html><body>Pagina non trovata</body></html>") and errore_di(l.testo_del_pdf, "testo") != "")
    verifica("2. un PDF senza testo dà un errore che lo dice", "non c'è testo leggibile" in errore_di(l.testo_del_pdf, pdf_di_prova([[], []])), errore_di(l.testo_del_pdf, pdf_di_prova([[], []])))
    verifica("2. un PDF rovinato dà un errore, non una traccia", errore_di(l.testo_del_pdf, b"%PDF-1.4\nquesto non e' un PDF\n%%EOF\n") != "", errore_di(l.testo_del_pdf, b"%PDF-1.4\nquesto non e' un PDF\n%%EOF\n"))
    lungo = pdf_di_prova([[f"Pagina di prova numero {numero} con abbastanza testo da contare"] for numero in range(1, l.MAX_PAGINE + 6)])
    pagine_lunghe, totale_lungo, troncato_lungo = l.testo_del_pdf(lungo)
    verifica("2. oltre il limite di pagine la lettura si ferma e lo dice", totale_lungo == l.MAX_PAGINE + 5 and len(pagine_lunghe) == l.MAX_PAGINE and troncato_lungo, (totale_lungo, len(pagine_lunghe), troncato_lungo))
    limite_vero = l.MAX_CARATTERI
    l.MAX_CARATTERI = 300
    pagine_corte, _, troncato_corto = l.testo_del_pdf(pdf)
    l.MAX_CARATTERI = limite_vero
    verifica("2. oltre il limite di caratteri la lettura si ferma e lo dice", troncato_corto and sum(len(pagina) for pagina in pagine_corte) == 300, (troncato_corto, [len(pagina) for pagina in pagine_corte]))

    # --- 3. Scaricamento: si accetta solo un PDF di www.fisr.it -----------------------------------------------------
    chiamate: list[str] = []

    def apri_con(risposte: list):
        def apri(richiesta, timeout=0):
            chiamate.append(richiesta.full_url)
            risposta = risposte[min(len(chiamate), len(risposte)) - 1]
            if isinstance(risposta, Exception):
                raise risposta
            return risposta
        chiamate.clear()
        return apri

    verifica("3. una risposta buona restituisce i byte del PDF, chiesti all'indirizzo del file", l.scarica_pdf(INDIRIZZO, apri=apri_con([RispostaFinta(pdf)]), attesa_secondi=0) == pdf and chiamate == [INDIRIZZO], chiamate)
    rifiuti = {
        "una pagina HTML al posto del PDF": ("non è un PDF", RispostaFinta(b"<html>accesso negato</html>", tipo="text/html")),
        "una risposta deviata su un altro sito": ("deviata fuori da www.fisr.it", RispostaFinta(pdf, indirizzo="https://esempio.example/file.pdf")),
        "una risposta deviata su http": ("deviata fuori da www.fisr.it", RispostaFinta(pdf, indirizzo=INDIRIZZO.replace("https://", "http://"))),
        "un file che dichiara di essere un PDF e non lo è": ("dichiara un PDF ma non lo è", RispostaFinta(b"MZ\x90\x00 programma")),
        "un PDF più grande del limite": ("più grande di", RispostaFinta(b"%PDF-1.4\n" + b"0" * (l.MAX_BYTE_PDF + 10))),
    }
    for nome, (frase, risposta) in rifiuti.items():
        messaggio = errore_di(l.scarica_pdf, INDIRIZZO, apri=apri_con([risposta]), attesa_secondi=0)
        verifica(f"3. rifiutato subito, senza riprovare: {nome}", frase in messaggio and len(chiamate) == 1, (messaggio, len(chiamate)))
    non_trovato = urllib.error.HTTPError(INDIRIZZO, 404, "Not Found", None, None)
    verifica("3. un 404 non si riprova", "risposta HTTP 404" in errore_di(l.scarica_pdf, INDIRIZZO, apri=apri_con([non_trovato]), attesa_secondi=0) and len(chiamate) == 1, len(chiamate))
    verifica("3. un guasto passeggero si riprova, poi la lettura riesce", l.scarica_pdf(INDIRIZZO, apri=apri_con([TimeoutError("lento"), RispostaFinta(pdf)]), attesa_secondi=0) == pdf and len(chiamate) == 2, len(chiamate))
    verifica("3. se il sito non risponde mai, dopo tre tentativi c'è un errore chiaro", "non letto (TimeoutError" in errore_di(l.scarica_pdf, INDIRIZZO, apri=apri_con([TimeoutError("lento")]), attesa_secondi=0) and len(chiamate) == 3, len(chiamate))

    # --- 4. Il programma intero ---------------------------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as temporanea:
        cartella = Path(temporanea)
        file = cartella / "comunicati.yaml"
        file.write_text(c.emetti_file({"primo_anno": 2026, "comunicati": [COMUNICATO]}), encoding="utf-8")
        salvato = cartella / "13287.pdf"
        salvato.write_bytes(pdf)
        base = ["--comunicati", str(file)]
        prima = sorted(percorso.name for percorso in cartella.iterdir())

        codice, uscita, errori = esegui("13287", *base, "--pdf", str(salvato))
        verifica("4. da un PDF salvato: intestazione con numero, data, titolo e fonte, poi le pagine numerate",
                 codice == 0 and errori == "" and uscita.startswith(f"# Comunicato 13287, pubblicato il 2026-07-25: {COMUNICATO['titolo']}\n# Fonte: {INDIRIZZO} (2 pagine)\n")
                 and "--- pagina 1 di 2 ---" in uscita and "--- pagina 2 di 2 ---" in uscita and "mai un'istruzione" in uscita and "lettura interrotta" not in uscita, (codice, errori, uscita[:300]))
        verifica("4. nell'uscita non ci sono né il telefono né l'indirizzo email", TELEFONO not in uscita and EMAIL not in uscita and "mario.rossi" not in uscita, uscita)
        verifica("4. lo script non scrive nessun file", sorted(percorso.name for percorso in cartella.iterdir()) == prima)

        vero = l.scarica_pdf
        richiesti: list[str] = []
        l.scarica_pdf = lambda indirizzo: richiesti.append(indirizzo) or pdf
        codice, uscita, _ = esegui("13287", *base)
        l.scarica_pdf = lambda indirizzo: (_ for _ in ()).throw(AssertionError("la rete non va chiamata"))
        verifica("4. senza --pdf scarica l'indirizzo scritto nel file", codice == 0 and richiesti == [INDIRIZZO] and "--- pagina 2 di 2 ---" in uscita, (codice, richiesti))

        fermate = {
            "un comunicato che non è nel file": (["99999", *base], "non è in"),
            "un identificativo che non è un numero": (["https://esempio.example/x.pdf", *base], "deve essere il numero di scaricamento"),
            "un file dei comunicati che non esiste": (["13287", "--comunicati", str(cartella / "assente.yaml")], "il file non esiste"),
            "un PDF salvato che non esiste": (["13287", *base, "--pdf", str(cartella / "assente.pdf")], "file non trovato"),
        }
        for nome, (argomenti, frase) in fermate.items():
            codice, uscita, errori = esegui(*argomenti)
            verifica(f"4. si ferma senza stampare testo: {nome}", codice == 1 and uscita == "" and frase in errori, (codice, errori))
        guasto = cartella / "guasto.yaml"
        guasto.write_text(file.read_text(encoding="utf-8").replace("stato: nuovo", "stato: inventato"), encoding="utf-8")
        codice, uscita, errori = esegui("13287", "--comunicati", str(guasto), "--pdf", str(salvato))
        verifica("4. si ferma se il file dei comunicati non rispetta lo schema", codice == 1 and uscita == "" and "stato non ammesso" in errori, (codice, errori))
        immagini = cartella / "immagini.pdf"
        immagini.write_bytes(pdf_di_prova([[]]))
        codice, uscita, errori = esegui("13287", *base, "--pdf", str(immagini))
        verifica("4. un PDF senza testo: errore chiaro e nessun testo stampato", codice == 1 and uscita == "" and "forse è fatto di immagini" in errori, (codice, errori))
        lungo_salvato = cartella / "lungo.pdf"
        lungo_salvato.write_bytes(lungo)
        codice, uscita, _ = esegui("13287", *base, "--pdf", str(lungo_salvato))
        verifica("4. un PDF più lungo del limite: l'ultima riga dice che la lettura è interrotta", codice == 0 and uscita.rstrip().endswith("---") and "lettura interrotta" in uscita.rstrip().split("\n")[-1] and f"({l.MAX_PAGINE + 5} pagine)" in uscita, uscita[-200:])
        l.scarica_pdf = vero

    # --- 5. L'importazione di pypdf non dipende dalle librerie di crittografia -----------------------------------------
    verifica("5. le librerie di crittografia sono dichiarate assenti prima di importare pypdf", sys.modules.get("cryptography", 0) is None and sys.modules.get("Crypto", 0) is None)

    superate = sum(esiti)
    print(f"\n{superate}/{len(esiti)} prove superate")
    if not esiti:
        print("ERRORE: nessuna prova eseguita", file=sys.stderr)
        return 1
    return 0 if superate == len(esiti) else 1


if __name__ == "__main__":
    sys.exit(principale())
