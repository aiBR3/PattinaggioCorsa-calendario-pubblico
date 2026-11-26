# Decisioni in vigore: dove sta ogni regola

Indice per tema. Ogni riga dice in quale file sta la regola, cioè dove si legge e dove si cambia, e tra parentesi la data della riga da cercare in `appunti/decisioni.md`, la storia, per il motivo, le alternative scartate e le decisioni superate. Il contenuto delle regole qui non si ripete (decisione del 2026-11-25). Sono scritte per intero, segnate con "Solo qui", le poche decisioni che non hanno un altro posto. Una decisione nuova si scrive nel file dove si applica e, con il motivo, in fondo alla storia; qui si aggiunge o si corregge una riga solo se cambia il posto di una regola, se nasce un tema nuovo o se la decisione non ha un altro posto.

## Perimetro e prodotto

- Categorie, tipi di evento e perimetro geografico: `CLAUDE.md`, "Scopo" (2026-11-05).
- Solo qui. Fuori dal calendario: i campionati regionali e provinciali FISR, anche quando ammettono i Master (2026-11-17); le pattinate che si ripetono ogni settimana nelle città (2026-11-22).
- Solo qui. Il calendario è un file ICS pubblicato via GitHub Pages da questo repository; gli altri siti mettono solo un link `webcal://`; il ritardo di Google Calendar, 12–24 ore, è accettato (2026-11-05).
- Solo qui. Nessuna licenza per ora; niente Releases (2026-11-05).
- Le gare già passate non si ricontrollano: `agenti/arricchimento.md`, tabella "Limiti" (2026-11-06).

## Chi scrive e chi fonde

- Solo pull request, e su `main` fonde solo il proprietario: `CLAUDE.md`, regola 1 (2026-11-05).
- Solo qui. Come fonde: nel ruleset "Protezione su main" il proprietario è l'unico che può scavalcare "Restrict updates", quindi fonde ogni PR scavalcando le regole del ramo; un'approvazione decade ai commit successivi (2026-11-22).
- Solo qui. Chi deve rivedere che cosa: tutto è del proprietario tranne i file elencati in `CODEOWNERS`, quelli che raccolta e arricchimento scrivono ogni settimana (2026-11-17, 2026-11-22); `appunti/diario.md` resta del proprietario (2026-11-24). Finché una PR tocca solo quei file GitHub non chiede nessuna revisione; se tocca altro chiede quella del proprietario: è l'avviso che nella PR c'è qualcosa da guardare oltre ai dati (verificato sulla PR #93).
- Solo qui. Le sessioni Claude e le attività pianificate lavorano con un account GitHub secondario, senza permessi di amministratore; nei file il suo nome non si scrive (2026-11-22).
- Solo qui. GitHub Pages pubblica solo dal ramo `main` (2026-11-22).
- Niente informazioni personali: `CLAUDE.md`, regola 9 (2026-11-05).
- La memoria degli agenti è il repository, e che cosa si legge all'avvio: `CLAUDE.md`, primi due paragrafi (2026-11-05; 2026-11-22, "Avvio leggero").
- Che cosa va nel diario e che cosa nel registro: `CLAUDE.md`, regola 5 (2026-11-24).
- Un'informazione in un posto solo: `CLAUDE.md`, Convenzioni (2026-11-25).

## Metodo

- Solo qui. Un prompt nuovo si collauda a mano e in cieco prima di pianificarlo (2026-11-06).
- Gli eventi reali che scoperta e arricchimento devono saper trovare: `appunti/casi-di-prova.md` (2026-11-06).
- Solo qui. Scartati: submodule del solo file ICS; profilo Facebook fittizio (2026-11-05).

## Dati e schema

- Campi, stati e prefissi nel titolo delle voci: `dati/LEGGIMI.md`, "Schema di `dati/eventi.yaml`" (stati e `note` 2026-11-05; `organizzatore`, `distanze` e gare aperte per anno di nascita 2026-11-06; `id` e `nome_fonte` 2026-11-16; `url_ufficiale` 2026-11-17; codici di paese fuori perimetro e pattinate 2026-11-22; spostato da `CLAUDE.md` 2026-11-26).
- L'ordine delle frasi in `note_interne`, con la traccia dell'arricchimento per ultima: `script/LEGGIMI.md`, "Cosa decide `converti_fisr.py` e cosa no", voce "note interne" (2026-11-17, 2026-11-22).
- Schemi di fonti, società e segnalazioni: `dati/LEGGIMI.md` (registro delle società 2026-11-06; segnalazioni 2026-11-22).
- Le parole da usare ("regolamento di gara"): `CLAUDE.md`, Convenzioni (2026-11-05).
- Solo qui. Più gare dello stesso organizzatore nello stesso giorno e luogo: una voce sola (2026-11-06).
- Solo qui. `DTSTAMP` deterministico (2026-11-05).

## Prova

- Che cosa vale come prova e che cosa no: `CLAUDE.md`, regola 3 (2026-11-05, 2026-11-06). Il titolo federale con `cat. …/M` per i campionati senza regolamento: `script/LEGGIMI.md`, "Cosa decide `converti_fisr.py` e cosa no" (2026-11-05).
- La ricerca del sito dell'organizzatore, i siti compromessi, le pagine sparite: `CLAUDE.md`, regola 10 (2026-11-06).
- Social e siti delle società (`stato_sito`): `dati/LEGGIMI.md`, "Schema di `dati/societa.yaml`" (2026-11-06).

## Raccolta del lunedì

- La raccolta è un workflow a orario di soli script, senza giudizio: `CLAUDE.md`, regola 2 e "Come gira il calendario" (2026-11-06). L'orario è nel cron di `raccolta.yml`.
- Che cosa fa `raccolta.yml`, quali regolamenti legge, quando apre la PR e perché esegue da sé `genera_ics.py`: `script/LEGGIMI.md`, paragrafo "Il workflow `raccolta.yml`" (2026-11-06, 2026-11-16, 2026-11-17).
- Che cosa decide `converti_fisr.py` (riconoscimento, promozione, regolamento cambiato, nome, doppioni): `script/LEGGIMI.md`, "Cosa decide `converti_fisr.py` e cosa no" (2026-11-06, 2026-11-16, 2026-11-24). Stessa gara, stesso numero di regolamento: `CLAUDE.md`, regola 7 (2026-11-16).
- Pattinate di Pattiniamo l'Italia: `script/LEGGIMI.md`, "Cosa fa `converti_pattinate.py` e cosa no"; il luogo letto dal titolo: `CLAUDE.md`, regola 4 (2026-11-22, quattro righe "Pattinate").
- Segnalazioni, che cosa entra nel repository e come si trattano i testi del pubblico: `dati/LEGGIMI.md`, "Schema di `dati/segnalazioni.yaml`", e `CLAUDE.md`, Convenzioni. Solo qui: il modulo Tally è pubblico e non ha campi di contatto (2026-11-22, tre righe "Segnalazioni").
- Comunicati FISR: che cosa elenca `raccogli_comunicati.py`, che cosa controlla e quando i comunicati entrano in una PR: `script/LEGGIMI.md`, "Cosa fa `raccogli_comunicati.py` e cosa no" e paragrafo "Il workflow `raccolta.yml`"; schema e stati: `dati/LEGGIMI.md`, "Schema di `dati/comunicati.yaml`" (2026-11-26). Come si leggono: `script/LEGGIMI.md`, "Cosa fa `leggi_comunicato.py` e cosa no"; che cosa ne fa l'agente del martedì: `agenti/comunicati.md` (2026-11-26, riga sulla lettura).
- Quando si committa `registro/`: `CLAUDE.md`, regola 5 (2026-11-06).
- Solo qui. Che cosa si conserva in `registro/`: un rapporto per esecuzione, che non si legge all'avvio; dei JSON grezzi si tengono l'ultima scansione completa, quelli citati dai casi di prova e l'ultimo settimanale, e gli altri si possono cancellare dopo tre mesi; i rapporti `.md` restano (2026-11-22).

## Arricchimento del martedì

- Procedimento, limiti, che cosa l'agente decide da solo e che cosa non tocca mai, su quale ramo scrive: `agenti/arricchimento.md` (2026-11-06, 2026-11-17; pattinate 2026-11-22; regolamento cambiato 2026-11-24; revisione dopo i collaudi 4, 5 e 6, note pubbliche dopo uno spostamento di data, sito di un altro soggetto nel registro, "FISR" come organizzatore 2026-11-26). La procedura per i comunicati FISR sta in un file a parte, `agenti/comunicati.md`, letto solo quando ce ne sono di nuovi (2026-11-26).
- Modello, impegno, orario, rete, approvazione: `agenti/attivita-pianificata.md`, "Configurazione" (2026-11-06, "Fase 3 attiva").

## Rilettura

- Quali voci, quali giri, che cosa scrive e che cosa segnala soltanto: `agenti/rilettura-mensile.md`; la configurazione dell'attività: `agenti/attivita-pianificata.md` (2026-11-22).

## Calendario e pagina

- Che cosa mostra ogni evento, le etichette, i link: `script/LEGGIMI.md`, "Cosa vede chi consulta il calendario" (2026-11-05, 2026-11-06, 2026-11-17).
- Testo e aspetto della pagina, che cosa viene generato a ogni merge: `script/LEGGIMI.md`, "La pagina pubblicata" (2026-11-05).
- Solo qui. Pages serve l'ICS come `text/calendar` (2026-11-05).

## Fonti nuove

- Skate Terminal, come si usa e perché solo a mano: `dati/fonti.yaml`, fonte `skate-terminal` (2026-11-22).
- Solo qui. Scoperta di nuove gare: ricerca aperta ogni 2 settimane (2026-11-05). Se è in funzione lo dice `appunti/stato.md`.

## Architettura: chi fa cosa

Quando gira ogni livello: `CLAUDE.md`, "Come gira il calendario".

| Livello | Compito | Chi |
|---|---|---|
| 0 | `eventi.yaml` + `fonti.yaml` in git: sorgente di verità | — |
| 1 | Raccolta: legge una pagina, restituisce dati grezzi, non interpreta | script; modello economico solo per pagine irregolari |
| 2 | Normalizzazione + deduplica | codice |
| 2b | Arricchimento: dal nome dell'organizzatore al suo sito e alla pagina dell'evento (regola 10) | modello capace (serve giudizio) |
| 2c | Rilettura delle gare future già confermate o non ancora autorizzate | modello (nessuna ricerca, nessuna decisione sulle categorie: può essere più economico di quello del livello 2b) |
| 3 | Verifica e classificazione: decide se la gara ammette Master/Amatori e cita la prova | script per i regolamenti di gara FISR (`converti_fisr.py`, art. 10); modello capace per le pagine degli organizzatori |
| 4 | Supervisore: commenta la PR con riassunto e dubbi evidenziati | modello capace |
| 5 | Pubblicazione: ICS + pagina via Pages | workflow Actions, dopo il merge del proprietario |
| 6 | Scoperta: ricerca aperta di nuove gare e nuove fonti → propone aggiunte a `fonti.yaml` | modello capace |
| 7 | Segnalazioni: dal modulo pubblico ai candidati ripuliti di `dati/segnalazioni.yaml` | script (`raccogli_segnalazioni.py`); i candidati li lavora il modello capace del livello 2b |
