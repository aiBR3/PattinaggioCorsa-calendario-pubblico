#!/usr/bin/env python3
"""
prove_raccogli_comunicati.py — prove automatiche di raccogli_comunicati.py su pagine costruite.

Non legge la rete e non tocca dati/comunicati.yaml: costruisce un indice e delle pagine d'anno finte, nella forma di quelle di fisr.it, e lavora su file temporanei. Protegge le decisioni del 2026-11-22 e del 2026-11-26:
  - lo script elenca soltanto: i comunicati nuovi entrano come "nuovo" (come "storico" al primo carico), e stato ed esito scritti da chi li ha lavorati restano;
  - i titoli passano ripuliti; un titolo che cambia nella fonte riapre il comunicato già lavorato;
  - l'indirizzo della pagina di un anno si legge dall'indice; si leggono i due anni più recenti, mai uno precedente al primo anno del file;
  - una pagina incompleta, una struttura cambiata, un link fuori posto o una quantità sospetta fermano tutto senza scrivere.
I titoli usati qui sono inventati.

Uso:
    python3 script/prove_raccogli_comunicati.py

Esce con 0 se tutte le prove passano, con 1 altrimenti (dopo averle elencate tutte).
"""

from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

CARTELLA_SCRIPT = Path(__file__).resolve().parent
if not (CARTELLA_SCRIPT / "raccogli_comunicati.py").is_file():
    sys.exit(f"Non trovo raccogli_comunicati.py in {CARTELLA_SCRIPT}")
sys.path.insert(0, str(CARTELLA_SCRIPT))

import raccogli_comunicati as c  # noqa: E402 — va importato dopo aver aggiunto la cartella degli script al percorso

OGGI = date(2026, 11, 30)
PERCORSI = {2024: "/corsa/comunicati-ufficiali/category/528-2024.html", 2025: "/corsa/comunicati-ufficiali/category/565-2025.html", 2026: "/corsa/comunicati-ufficiali/category/601-2026.html", 2027: "/corsa/comunicati-ufficiali/category/644-2027.html"}
MESI_SCRITTI = {numero: nome.capitalize() for nome, numero in c.MESI.items()}


def blocco(numero: int, titolo: str, pubblicato: str | None, anno: int, coda: str = "cu-di-prova", percorso: str | None = None, pulsante_prima: bool = False) -> str:
    """Il blocco HTML di un comunicato, come lo scrive la pagina vera: il link con il titolo, la data in uno span, il pulsante "Download"."""
    indirizzo = f"{percorso or PERCORSI[anno]}?download={numero}:{coda}"
    if pubblicato is None:
        data = ""
    else:
        giorno = date.fromisoformat(pubblicato)
        data = f"<span>{giorno.day:02d} {MESI_SCRITTI[giorno.month]} {giorno.year}</span>"
    link_titolo = f'<a class="" href="{indirizzo}">{titolo}</a>'
    link_pulsante = f'<div class="pd-buttons"><div class="pd-button-download"><a class="btn btn-success" href="{indirizzo}">Download</a></div></div>'
    prima, dopo = (link_pulsante, link_titolo) if pulsante_prima else (link_titolo, link_pulsante)
    return f'<div class="pd-filebox">\n<div class="pd-filenamebox">\n<div class="pd-filename"><div class="pd-float">{prima}</div></div>\n{data}\n</div>\n{dopo}\n<div class="pd-cb"></div>\n</div>\n'


def pagina_anno(anno: int, blocchi: list[str], titolo_pagina: object = None) -> str:
    return (f'<html><body><section id="component"><div id="phoca-dl-category-box" class="pd-category-view"><div class="pd-category">\n<h3 class="pd-ctitle">{titolo_pagina or anno}</h3>\n'
            + "".join(blocchi) + '<form method="post" name="adminForm"><div class="pagination"></div></form></div></div></section></body></html>')


def pagina_indice(anni: dict[int, int | None], etichette: dict[int, str] | None = None) -> str:
    """L'indice: per ogni anno il link alla sua pagina e, tra parentesi, quanti comunicati dichiara (None: non lo dice)."""
    righe = []
    for anno in sorted(anni, reverse=True):
        dichiarati = "" if anni[anno] is None else f" <small>({anni[anno]})</small>"
        righe.append(f'<div class="pd-subcategory" data-com="equalizer">\n<a href="{PERCORSI[anno]}">{(etichette or {}).get(anno, anno)}</a>{dichiarati}\n</div>')
    return '<html><body><div id="phoca-dl-category-box" class="pd-category-view"><div class="pd-category">\n<h3 class="pd-ctitle">Corsa</h3>\n' + "\n".join(righe) + "\n</div></div></body></html>"


def comunicati_di_prova(anno: int, quanti: int, primo_numero: int) -> list[tuple[int, str, str]]:
    return [(primo_numero + indice, f"CU {indice + 1:02d} Campionato di prova numero {indice + 1} - Provopoli (PR)", f"{anno}-{(indice % 11) + 1:02d}-10") for indice in range(quanti)]


def principale() -> int:
    esiti: list[bool] = []

    def verifica(nome: str, condizione: bool, dettaglio: object = "") -> None:
        esiti.append(bool(condizione))
        print(("ok      " if condizione else "FALLITA ") + nome + ("" if condizione else f"  →  {dettaglio!r}"))

    def vietata(*_argomenti, **_parole):
        raise AssertionError("le prove non devono leggere la rete")

    c.scarica_pagina = vietata

    # --- 1. Pulizia dei titoli -------------------------------------------------------------------------------------
    casi = [("  CU  37   Campionato Italiano su Strada cat. A/J/S/M - Vado Ligure (SV) 3-6 settembre 2026 ", "CU 37 Campionato Italiano su Strada cat. A/J/S/M - Vado Ligure (SV) 3-6 settembre 2026"),
            ("CU 31 PRECISAZIONI NORME ATTIVITA’ CORSA – M. 5000 IN LINEA M/F 2025/26", "CU 31 PRECISAZIONI NORME ATTIVITA' CORSA - M. 5000 IN LINEA M/F 2025/26"),
            ("Titolo <b>grasso</b> | tabella `codice` [link](x)", "Titolo b grasso /b tabella 'codice' link (x)"), ("Riga uno\nRiga due\r\n::set-output name=x::y", "Riga uno Riga due ::set-output name x::y"),
            ("${{ secrets.CHIAVE }} @utente #1 \"citazione\"", "secrets.CHIAVE utente 1 citazione"), ("\x00\x1b[31m…", "31m")]
    for numero, (grezzo, atteso) in enumerate(casi, start=1):
        pulito = c.ripulisci_titolo(grezzo)
        verifica(f"1.{numero} titolo ripulito: {atteso!r}", pulito == atteso and c.ripulisci_titolo(pulito) == pulito, pulito)
    lungo = c.ripulisci_titolo("parola " * 80)
    verifica("1. un titolo lungo viene tagliato a fine parola", len(lungo) <= c.MAX_TITOLO and lungo.endswith("parola") and c.ripulisci_titolo(lungo) == lungo, lungo)

    # --- 2. Lettura dell'indice ---------------------------------------------------------------------------------------
    indice = c.leggi_indice(pagina_indice({2026: 3, 2025: 51}), OGGI)
    verifica("2. l'indice dà per ogni anno il percorso della pagina e quanti comunicati dichiara", indice == {2026: {"percorso": PERCORSI[2026], "dichiarati": 3}, 2025: {"percorso": PERCORSI[2025], "dichiarati": 51}}, indice)
    verifica("2. un indice senza il numero dei comunicati si legge lo stesso", c.leggi_indice(pagina_indice({2026: None}), OGGI)[2026]["dichiarati"] is None)
    for nome, pagina in (("senza il riquadro dell'elenco", "<html><body>manutenzione</body></html>"), ("senza anni", pagina_indice({})), ("fermo a due anni fa", pagina_indice({2024: 40})),
                         ("con un'etichetta diversa dall'anno del link", pagina_indice({2026: 3}, {2026: "2025"})), ("con lo stesso anno due volte", pagina_indice({2026: 3}).replace("</div></div></body>", f'<a href="{PERCORSI[2026]}">2026</a></div></div></body>'))):
        try:
            c.leggi_indice(pagina, OGGI)
            verifica(f"2. un indice {nome} ferma la lettura", False, "nessun errore")
        except c.ErroreComunicati:
            verifica(f"2. un indice {nome} ferma la lettura", True)

    # --- 3. Lettura della pagina di un anno ----------------------------------------------------------------------------
    letti = c.leggi_pagina_anno(pagina_anno(2026, [blocco(13287, "CU 37 Campionato di prova cat. A/J/S/M - Provopoli (PR) 3-6 settembre 2026", "2026-07-25", 2026, coda="cu-37-campionato-cant%C3%B9-co"),
                                                 blocco(12617, "Cu 01 Campionato <em>Indoor</em> &amp; Trofeo – Citt&agrave; di Prova", "2026-01-09", 2026, pulsante_prima=True)]), 2026, PERCORSI[2026])
    attesi = [{"id_scaricamento": 13287, "anno": 2026, "pubblicato_il": "2026-07-25", "titolo": "CU 37 Campionato di prova cat. A/J/S/M - Provopoli (PR) 3-6 settembre 2026", "url": f"https://www.fisr.it{PERCORSI[2026]}?download=13287"},
              {"id_scaricamento": 12617, "anno": 2026, "pubblicato_il": "2026-01-09", "titolo": "Cu 01 Campionato Indoor & Trofeo - Città di Prova", "url": f"https://www.fisr.it{PERCORSI[2026]}?download=12617"}]
    verifica("3. dalla pagina: numero, data, titolo senza marcatori e indirizzo senza la coda; il pulsante Download non è mai il titolo", letti == attesi, letti)
    verifica("3. una pagina senza comunicati è valida e vuota", c.leggi_pagina_anno(pagina_anno(2027, []), 2027, PERCORSI[2027]) == [])
    buono = blocco(13000, "CU 10 Comunicato di prova", "2026-03-10", 2026)
    rotte = {
        "senza il riquadro dell'elenco": "<html><body>manutenzione</body></html>",
        "con il titolo di un altro anno": pagina_anno(2026, [buono], titolo_pagina=2025),
        "con un blocco senza data": pagina_anno(2026, [buono, blocco(13001, "CU 11 Senza data", None, 2026)]),
        "con una data impossibile": pagina_anno(2026, [buono.replace("10 Marzo 2026", "31 Febbraio 2026")]),
        "con un mese sconosciuto": pagina_anno(2026, [buono.replace("10 Marzo 2026", "10 Brumaio 2026")]),
        "con un blocco senza link": pagina_anno(2026, [buono, '<div class="pd-filebox"><span>10 Marzo 2026</span></div>']),
        "con un blocco senza titolo": pagina_anno(2026, [blocco(13002, " <b> </b> ", "2026-03-10", 2026)]),
        "con un link verso un altro sito": pagina_anno(2026, [buono.replace('href="/corsa/', 'href="https://esempio.example/corsa/')]),
        "con un link verso la pagina di un altro anno": pagina_anno(2026, [blocco(13003, "CU 12 Altrove", "2026-03-10", 2026, percorso=PERCORSI[2025])]),
        "con un link di scaricamento malformato": pagina_anno(2026, [buono.replace("?download=13000:", "?download=tredicimila:")]),
        "con due link a comunicati diversi nello stesso blocco": pagina_anno(2026, [buono.replace("?download=13000:", "?download=13009:", 1)]),
        "con lo stesso comunicato due volte": pagina_anno(2026, [buono, buono]),
        "con link di scaricamento fuori dai blocchi": pagina_anno(2026, []).replace("<form", f'<a href="{PERCORSI[2026]}?download=13000:x">CU 10</a><form'),
    }
    for nome, pagina in rotte.items():
        try:
            risultato = c.leggi_pagina_anno(pagina, 2026, PERCORSI[2026])
            verifica(f"3. una pagina {nome} ferma la lettura", False, risultato)
        except c.ErroreComunicati:
            verifica(f"3. una pagina {nome} ferma la lettura", True)

    with tempfile.TemporaryDirectory() as temporanea:
        cartella = Path(temporanea)
        pagine = cartella / "pagine"
        pagine.mkdir()
        file = cartella / "comunicati.yaml"
        rapporto = cartella / "rapporto.md"

        def prepara(indice_anni: dict[int, int | None], per_anno: dict[int, list[tuple[int, str, str]]]) -> None:
            for vecchio in pagine.glob("*.html"):
                vecchio.unlink()
            (pagine / "indice.html").write_text(pagina_indice(indice_anni), encoding="utf-8")
            for anno, comunicati in per_anno.items():
                (pagine / f"{anno}.html").write_text(pagina_anno(anno, [blocco(numero, titolo, pubblicato, anno) for numero, titolo, pubblicato in reversed(comunicati)]), encoding="utf-8")

        def aggiorna(*altri: str, oggi: date = OGGI) -> int:
            return c.principale(["aggiorna", "--comunicati", str(file), "--cartella-pagine", str(pagine), "--oggi", oggi.isoformat(), "--rapporto", str(rapporto), *altri])

        def lavora(numero: int, stato: str, esito: str) -> None:
            """Ciò che fa chi lavora un comunicato: cambia stato ed esito con una sostituzione testuale, senza riscrivere il file."""
            testo = file.read_text(encoding="utf-8")
            inizio = testo.index(f"  - id_scaricamento: {numero}\n")
            fine = testo.index("\n\n", inizio) if "\n\n" in testo[inizio:] else len(testo)
            voce = testo[inizio:fine]
            riga_stato = next(riga for riga in voce.split("\n") if riga.startswith("    stato: "))
            riga_esito = next(riga for riga in voce.split("\n") if riga.startswith("    esito: "))
            file.write_text(testo[:inizio] + voce.replace(riga_stato, f"    stato: {stato}").replace(riga_esito, f'    esito: "{esito}"') + testo[fine:], encoding="utf-8")

        def voce(numero: int) -> dict:
            return next(comunicato for comunicato in c.carica_file(file)["comunicati"] if comunicato["id_scaricamento"] == numero)

        # --- 4. Primo carico -----------------------------------------------------------------------------------------
        del_2026 = comunicati_di_prova(2026, 6, 13000)
        prepara({2026: 6, 2025: 51}, {2026: del_2026})      # la pagina del 2025 non c'è: se lo script provasse a leggerla fallirebbe
        verifica("4. senza il file e senza --primo-carico lo script si ferma", aggiorna("--scrivi") == 1 and not file.exists() and "--primo-carico" in rapporto.read_text(encoding="utf-8"))
        verifica("4. primo carico senza --scrivi: solo il rapporto", aggiorna("--primo-carico") == 0 and not file.exists() and "manca `--scrivi`" in rapporto.read_text(encoding="utf-8"))
        codice = aggiorna("--primo-carico", "--scrivi")
        stato = c.carica_file(file)
        verifica("4. primo carico: legge solo l'anno più recente, tutti i comunicati entrano come storico, in ordine di numero",
                 codice == 0 and stato["primo_anno"] == 2026 and [x["id_scaricamento"] for x in stato["comunicati"]] == [numero for numero, _, _ in del_2026]
                 and all(x["stato"] == "storico" and x["esito"] == "" and x["anno"] == 2026 for x in stato["comunicati"]), (codice, stato))
        verifica("4. il rapporto del primo carico non ricopia l'elenco", "Primo carico: 6 comunicati del 2026" in rapporto.read_text(encoding="utf-8") and del_2026[0][1] not in rapporto.read_text(encoding="utf-8"))
        verifica("4. il file scritto supera la verifica", c.principale(["verifica", "--comunicati", str(file)]) == 0)
        verifica("4. un secondo primo carico viene rifiutato", aggiorna("--primo-carico", "--scrivi") == 1)
        prima = file.read_bytes()
        verifica("4. una lettura senza novità non cambia un byte, e il 2025, che è nell'indice ma precede il primo anno del file, non viene letto", aggiorna("--scrivi") == 0 and file.read_bytes() == prima and "Nessuna differenza" in rapporto.read_text(encoding="utf-8"))

        # --- 5. Comunicati nuovi e lavoro di chi li legge ---------------------------------------------------------------
        nuovo_a, nuovo_b = (13050, "CU 07 Campionato Italiano di prova cat. J/S/M - Provopoli (PR)", "2026-11-27"), (13051, "CU 08 Ranking di prova", "2026-11-28")
        prepara({2026: 8, 2025: 51}, {2026: del_2026 + [nuovo_a, nuovo_b]})
        verifica("5. senza --scrivi i comunicati nuovi stanno solo nel rapporto", aggiorna() == 0 and file.read_bytes() == prima and "Comunicati nuovi: 2" in rapporto.read_text(encoding="utf-8"))
        codice = aggiorna("--scrivi")
        stato = c.carica_file(file)
        verifica("5. i comunicati nuovi entrano in fondo come nuovo, gli storici restano",
                 codice == 0 and [(x["id_scaricamento"], x["stato"]) for x in stato["comunicati"][-2:]] == [(13050, "nuovo"), (13051, "nuovo")] and all(x["stato"] == "storico" for x in stato["comunicati"][:6]), stato["comunicati"][-3:])
        verifica("5. il rapporto elenca i nuovi con numero, data, titolo e indirizzo", f"| 13050 | 2026-11-27 | {nuovo_a[1]} | https://www.fisr.it{PERCORSI[2026]}?download=13050 |" in rapporto.read_text(encoding="utf-8"))
        lavora(13050, "abbinato", "Abbinato a 2027-05-23-provopoli-campionato-di-prova: organizzatore e scadenza dal comunicato.")
        lavora(13051, "non_pertinente", "Ranking.")
        verifica("5. dopo il lavoro fatto con sostituzioni testuali il file supera la verifica", c.principale(["verifica", "--comunicati", str(file)]) == 0)
        lavorato = file.read_bytes()
        verifica("5. la lettura successiva non tocca stato ed esito scritti da chi ha lavorato", aggiorna("--scrivi") == 0 and file.read_bytes() == lavorato)

        # --- 6. Titoli che cambiano nella fonte ---------------------------------------------------------------------------
        cambiati = [(13000, "CU 01 Campionato di prova numero 1 - Provopoli (PR) NUOVE DATE", "2026-01-10"), *del_2026[1:],
                    (13050, "CU 07 Campionato Italiano di prova cat. J/S/M - Altrove (AL)", "2026-11-27"), (13051, "cu 08 RANKING di prova.", "2026-11-28")]
        prepara({2026: 8, 2025: 51}, {2026: cambiati})
        codice = aggiorna("--scrivi", oggi=date(2026, 12, 7))
        testo_rapporto = rapporto.read_text(encoding="utf-8")
        verifica("6. titolo cambiato di un comunicato abbinato: riaperto come nuovo, con l'esito precedente conservato",
                 codice == 0 and voce(13050)["stato"] == "nuovo" and voce(13050)["titolo"].endswith("Altrove (AL)") and voce(13050)["esito"].startswith("Riaperto il 2026-12-07 da raccogli_comunicati.py")
                 and "Prima era abbinato: Abbinato a 2027-05-23-provopoli" in voce(13050)["esito"], voce(13050))
        verifica("6. titolo cambiato solo in maiuscole e punteggiatura: aggiornato senza riaprire", voce(13051) == dict(voce(13051), stato="non_pertinente", esito="Ranking.", titolo="cu 08 RANKING di prova."), voce(13051))
        verifica("6. titolo cambiato di un comunicato storico: aggiornato, resta storico", voce(13000)["stato"] == "storico" and voce(13000)["esito"] == "" and voce(13000)["titolo"].endswith("NUOVE DATE"), voce(13000))
        verifica("6. il rapporto dice quali titoli sono cambiati e quale è stato riaperto", "Titoli cambiati nella fonte: 3" in testo_rapporto and "`13050` (abbinato, riaperto come nuovo)" in testo_rapporto and "`13000` (storico)" in testo_rapporto, testo_rapporto)
        lunga = c.frase_di_riapertura(OGGI, "da_decidere", "x" * c.MAX_ESITO)
        verifica("6. la frase di riapertura non supera mai la lunghezza di un esito", len(lunga) == c.MAX_ESITO and lunga.endswith("…"), len(lunga))

        # --- 7. Cambio d'anno ------------------------------------------------------------------------------------------------
        del_2027 = [(13700, "CU 01 Campionato Italiano Indoor di prova - Provopoli (PR)", "2027-01-08")]
        prepara({2027: 1, 2026: 9, 2025: 51}, {2027: del_2027, 2026: cambiati + [(13060, "CU 09 Comunicato di fine anno", "2026-12-28")]})
        codice = aggiorna("--scrivi", oggi=date(2027, 1, 11))
        stato = c.carica_file(file)
        verifica("7. nasce la pagina del 2027: si leggono il 2027 e il 2026, e i nuovi di entrambe entrano come nuovo",
                 codice == 0 and [(x["id_scaricamento"], x["anno"], x["stato"]) for x in stato["comunicati"][-2:]] == [(13060, 2026, "nuovo"), (13700, 2027, "nuovo")] and voce(13700)["url"] == f"https://www.fisr.it{PERCORSI[2027]}?download=13700", stato["comunicati"][-2:])
        verifica("7. il rapporto dice quali anni ha letto", "Anni letti: 2027 (1 comunicato, l'indice ne dichiara 1); 2026 (9 comunicati, l'indice ne dichiara 9)" in rapporto.read_text(encoding="utf-8"), rapporto.read_text(encoding="utf-8"))
        prepara({2026: 9, 2025: 51}, {2026: cambiati + [(13060, "CU 09 Comunicato di fine anno", "2026-12-28")]})
        verifica("7. un anno che nel file ha dei comunicati e sparisce dall'indice ferma tutto",
                 aggiorna("--scrivi", oggi=date(2027, 1, 18)) == 1 and "non elenca più il 2027" in rapporto.read_text(encoding="utf-8"), rapporto.read_text(encoding="utf-8"))

        # --- 8. Letture sospette: nessuna scrittura -----------------------------------------------------------------------------
        completo_2026 = cambiati + [(13060, "CU 09 Comunicato di fine anno", "2026-12-28")]
        prepara({2027: 1, 2026: 9}, {2027: del_2027, 2026: completo_2026})
        verifica("8. punto di partenza: file allineato alla fonte", aggiorna("--scrivi", oggi=date(2027, 1, 18)) == 0)
        fermo = file.read_bytes()

        def si_ferma(nome: str, frase: str, indice_anni: dict[int, int | None], per_anno: dict[int, list[tuple[int, str, str]]]) -> None:
            prepara(indice_anni, per_anno)
            codice = aggiorna("--scrivi", oggi=date(2027, 1, 18))
            testo = rapporto.read_text(encoding="utf-8")
            verifica(f"8. {nome}: errore chiaro, file intatto", codice == 1 and file.read_bytes() == fermo and frase in testo and "non è stato toccato" in testo, (codice, testo[-300:]))

        si_ferma("la pagina mostra meno comunicati di quanti l'indice ne dichiara", "l'indice ne dichiara 12", {2027: 1, 2026: 12}, {2027: del_2027, 2026: completo_2026})
        si_ferma("più della metà dei comunicati noti di un anno è sparita", "lettura sospetta: 6 comunicati del 2026 su 9", {2027: 1, 2026: 3}, {2027: del_2027, 2026: completo_2026[:3]})
        si_ferma("troppi comunicati nuovi in una volta", "comunicati nuovi in una sola lettura", {2027: 22, 2026: 9}, {2027: del_2027 + comunicati_di_prova(2027, 21, 13800), 2026: completo_2026})
        si_ferma("un comunicato noto compare sotto un altro anno", "è nel file sotto il 2026 e nella fonte sotto il 2027", {2027: 2, 2026: 9}, {2027: del_2027 + [(13060, "CU 09 Comunicato di fine anno", "2026-12-28")], 2026: completo_2026})
        si_ferma("manca la pagina di un anno da leggere", "file non trovato", {2027: 1, 2026: 9}, {2027: del_2027})

        prepara({2027: 1, 2026: 8}, {2027: del_2027, 2026: completo_2026[:-1]})
        codice = aggiorna("--scrivi", oggi=date(2027, 1, 18))
        verifica("8. un solo comunicato sparito dalla fonte: resta nel file ed è segnalato nel rapporto",
                 codice == 0 and file.read_bytes() == fermo and "Non più nella fonte: 1" in rapporto.read_text(encoding="utf-8") and "`13060` (nuovo)" in rapporto.read_text(encoding="utf-8"), rapporto.read_text(encoding="utf-8")[-300:])
        prepara({2027: 1, 2026: None}, {2027: del_2027, 2026: completo_2026[:-1] + [(13060, "CU 09 Comunicato di fine anno", "2026-12-29")]})
        verifica("8. una data di pubblicazione che cambia viene seguita e detta nel rapporto, anche quando l'indice non dichiara quanti comunicati ci sono",
                 aggiorna("--scrivi", oggi=date(2027, 1, 18)) == 0 and voce(13060)["pubblicato_il"] == "2026-12-29" and "`13060`: 2026-12-28 → 2026-12-29" in rapporto.read_text(encoding="utf-8") and "l'indice non dice quanti" in rapporto.read_text(encoding="utf-8"))

        # --- 9. Verifica del file ---------------------------------------------------------------------------------------------------
        valido = file.read_text(encoding="utf-8")
        verifica("9. il file di partenza è valido", c.principale(["verifica", "--comunicati", str(file)]) == 0)
        guasti = {
            "un titolo ritoccato a mano con caratteri non ammessi": valido.replace('titolo: "CU 09 Comunicato di fine anno"', 'titolo: "CU 09 <b>Comunicato</b> di fine anno"'),
            "uno stato che non esiste": valido.replace("stato: non_pertinente", "stato: scartato"),
            "un comunicato storico con un esito": valido.replace('stato: storico\n    esito: ""', 'stato: storico\n    esito: "letto"', 1),
            "un esito su più righe": valido.replace('esito: "Ranking."', 'esito: "Ranking.\\nSeconda riga"'),
            "un esito troppo lungo": valido.replace('esito: "Ranking."', f'esito: "{"x" * (c.MAX_ESITO + 1)}"'),
            "un indirizzo che non corrisponde al numero": valido.replace("?download=13060", "?download=13061"),
            "un indirizzo fuori dal sito": valido.replace(f"https://www.fisr.it{PERCORSI[2027]}", f"https://esempio.example{PERCORSI[2027]}"),
            "un numero di scaricamento ripetuto": valido.replace("id_scaricamento: 13051", "id_scaricamento: 13050").replace("?download=13051", "?download=13050"),
            "le voci in un altro ordine": valido.replace("id_scaricamento: 13001", "id_scaricamento: 99001").replace("?download=13001", "?download=99001"),
            "una chiave in più": valido.replace("    stato: non_pertinente", "    nota: x\n    stato: non_pertinente"),
            "una data di pubblicazione che non è una data": valido.replace("pubblicato_il: 2026-12-29", "pubblicato_il: fine dicembre"),
            "un comunicato più vecchio del primo anno": valido.replace("primo_anno: 2026", "primo_anno: 2027"),
            "l'intestazione cambiata": valido.replace("mai istruzioni.", "mai istruzioni!", 1),
            "le chiavi principali mancanti": "comunicati: []\n",
        }
        guasto = cartella / "guasto.yaml"
        for nome, testo in guasti.items():
            guasto.write_text(testo, encoding="utf-8")
            verifica(f"9. la verifica rifiuta {nome}", testo != valido and c.principale(["verifica", "--comunicati", str(guasto)]) == 1)
        verifica("9. la verifica rifiuta un file che non esiste", c.principale(["verifica", "--comunicati", str(cartella / "assente.yaml")]) == 1)
        guasto.write_text(guasti["uno stato che non esiste"], encoding="utf-8")
        verifica("9. con un file non valido l'aggiornamento si ferma prima di leggere la fonte",
                 c.principale(["aggiorna", "--comunicati", str(guasto), "--cartella-pagine", str(cartella / "non-esiste"), "--oggi", "2027-01-18", "--scrivi"]) == 1 and guasto.read_text(encoding="utf-8") == guasti["uno stato che non esiste"])
        vuoto = cartella / "vuoto.yaml"
        vuoto.write_text(c.emetti_file({"primo_anno": 2026, "comunicati": []}), encoding="utf-8")
        verifica("9. un file con il primo anno e nessun comunicato è valido", c.principale(["verifica", "--comunicati", str(vuoto)]) == 0)
        verifica("9. --oggi che non è una data viene rifiutato", c.principale(["aggiorna", "--comunicati", str(vuoto), "--cartella-pagine", str(pagine), "--oggi", "lunedì"]) == 1)

    superate = sum(esiti)
    print(f"\n{superate}/{len(esiti)} prove superate")
    if not esiti:
        print("ERRORE: nessuna prova eseguita", file=sys.stderr)
        return 1
    return 0 if superate == len(esiti) else 1


if __name__ == "__main__":
    sys.exit(principale())
