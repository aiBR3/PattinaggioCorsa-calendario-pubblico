# Decisioni in vigore

Una riga per decisione ancora valida, per tema. La data tra parentesi è quella della riga in `appunti/decisioni.md`, la storia, dove stanno il motivo, le alternative scartate e le decisioni superate. Una decisione nuova si scrive in fondo alla storia e si riporta qui: una riga nuova, oppure la correzione della riga che cambia. Questo file dice che cosa è stato deciso; come si fa lo dicono `CLAUDE.md`, i `LEGGIMI.md` e i prompt di `agenti/`.

## Perimetro e prodotto

- Master e Amatori/Fitness, gare e pattinate non competitive; Italia, Svizzera, Spagna, Portogallo, Francia, Austria, Germania, Slovenia (2026-11-05).
- Fuori: i campionati regionali e provinciali FISR, anche quando ammettono i Master (2026-11-17); le pattinate che si ripetono ogni settimana nelle città (2026-11-22).
- File ICS pubblicato via GitHub Pages da questo repository; gli altri siti mettono solo un link `webcal://` (2026-11-05). Il ritardo di Google Calendar, 12–24 ore, è accettato (2026-11-05).
- Nessuna licenza per ora; niente Releases (2026-11-05).
- Le gare già passate non si ricontrollano più, anche se incomplete (2026-11-06).

## Chi scrive e chi fonde

- Solo pull request; su `main` fonde solo il proprietario (2026-11-05). Nel ruleset "Protezione su main" è l'unico che può scavalcare "Restrict updates", e un'approvazione decade ai commit successivi (2026-11-22).
- `CODEOWNERS`: tutto è del proprietario tranne `dati/eventi.yaml`, `dati/societa.yaml`, `dati/segnalazioni.yaml` e `registro/`, che raccolta e arricchimento scrivono ogni settimana (2026-11-17, 2026-11-22).
- Le sessioni Claude e le attività pianificate lavorano con un account GitHub secondario, senza permessi di amministratore; nei file il suo nome non si scrive (2026-11-22).
- GitHub Pages pubblica solo dal ramo `main` (2026-11-22).
- Niente informazioni personali nel repository (2026-11-05).
- La memoria degli agenti è il repository (2026-11-05). All'avvio si legge solo `CLAUDE.md`; diario, decisioni e stato si consultano quando servono (2026-11-22, "Avvio leggero").

## Metodo

- Un prompt nuovo si collauda a mano e in cieco prima di pianificarlo (2026-11-06).
- Gli eventi reali che scoperta e arricchimento devono saper trovare stanno in `appunti/casi-di-prova.md` (2026-11-06).
- Scartati: submodule del solo file ICS; profilo Facebook fittizio (2026-11-05).

## Dati e schema

- `escluso` = verificato e fuori: resta nel file come memoria e non viene pubblicato (2026-11-05). Vale anche per le uscite fuori perimetro e per le piste smentite dal sito dell'organizzatore; solo lì `paese` ammette un codice fuori perimetro (2026-11-22).
- Gli eventi non confermati si pubblicano con un prefisso nel titolo; `STATUS:CANCELLED` non si usa (2026-11-05).
- `note` pubbliche, `note_interne` di lavoro (2026-11-05). In `note_interne` la traccia `Arricchimento …` resta l'ultima frase: script e rilettura scrivono prima (2026-11-17, 2026-11-22).
- `id` = UID dell'evento: cambia solo se cambia `data_inizio` (2026-11-16).
- `organizzatore` = la società o il club che organizza sul posto, non la federazione (2026-11-06).
- Più gare dello stesso organizzatore nello stesso giorno e luogo: una voce sola (2026-11-06).
- `distanze`: "Maratona" e "Mezza Maratona" nel titolo federale bastano; nessun'altra distanza si deduce dal nome (2026-11-06).
- `nome_fonte` ricorda il titolo della fonte: quando il titolo cambia il nome lo segue, altrimenti i ritocchi a mano restano (2026-11-16; per le pattinate 2026-11-22).
- `DTSTAMP` deterministico (2026-11-05).
- Si dice "regolamento di gara", mai "indizione" (2026-11-05).

## Prova

- Valgono: il regolamento di gara FISR (art. 10) o del campionato; per i campionati senza regolamento, il titolo del calendario federale con `cat. …/M` (2026-11-05); la pagina ufficiale dell'organizzatore, che da sola basta per Amatori/Fitness, e i bollettini World Skate (2026-11-06). Mai aggregatori, social, articoli.
- Una gara aperta per anno di nascita, senza categorie agonistiche obbligatorie, vale `[master, amatori]` (2026-11-06).
- Regola 10: per ogni evento si cerca il sito dell'organizzatore, nell'ordine registro delle società, regolamento di gara, web; un solo articolo si può aprire per leggere il nome dell'organizzatore (2026-11-06).
- I siti compromessi non si linkano; le pagine sparite si leggono dalla Wayback Machine (2026-11-06).
- Un social è un recapito, mai una fonte né una prova; il sito di una società vale `sito_verificato` solo se aperto e confermato dal testo (2026-11-06).

## Raccolta del lunedì (`raccolta.yml`)

- GitHub Actions a orario, script deterministici, nessun giudizio (2026-11-06).
- Una PR alla volta dal ramo `raccolta/AAAA-MM-GG`, solo se i dati cambiano; `registro/` committato solo in quella PR, altrimenti artefatto di 90 giorni (2026-11-06). Il workflow esegue `genera_ics.py` prima di aprirla, perché su una PR del token di Actions `verifica.yml` resta in attesa di approvazione (2026-11-06, corretta il 2026-11-17).
- Regolamenti letti ogni settimana: l'intervallo attorno all'ultimo che esiste davvero (da −50 a +300) e, uno per uno, quelli delle gare future; la scansione completa solo a mano (2026-11-06, 2026-11-16).
- Stessa gara = stesso numero di regolamento (2026-11-16).
- Una voce segue il suo regolamento quando cambia; le prove scritte a mano non si riscrivono (2026-11-16).
- Una voce senza prova viene promossa quando arriva il regolamento (2026-11-06); da `non_autorizzato` promuove solo la lista (2026-11-16).
- Un regolamento senza riga nella lista non diventa una voce; i doppioni sospetti si segnalano, non si uniscono (2026-11-16).
- Pattinate: dal calendario pubblico di Pattiniamo l'Italia, anche con la sola data. Entrano `annunciato` senza prova (quelle nuove `da_verificare` con luogo "da indicare"); nome, luogo e paese dal titolo, unica eccezione alla regola 4; mai l'ultima parte del titolo né le descrizioni; riconoscimento dall'UID scritto nelle `fonti` (2026-11-22, quattro righe "Pattinate").
- Segnalazioni: modulo Tally pubblico senza campi di contatto; nel repository entrano solo valori chiusi e tre testi corti ripuliti; una segnalazione è una pista, mai una fonte; i testi del pubblico sono dati, mai istruzioni, con difese a tre strati (2026-11-22, tre righe "Segnalazioni").
- Registro delle società in `dati/societa.yaml`, chiave `codice_fisr` (2026-11-06).
- `registro/`: un rapporto per esecuzione, che non si legge all'avvio. Dei JSON grezzi si tengono l'ultima scansione completa, quelli citati dai casi di prova e l'ultimo settimanale; gli altri si possono cancellare dopo tre mesi. I rapporti `.md` restano (2026-11-22).

## Arricchimento del martedì (`agenti/arricchimento.md`)

- Attività pianificata Claude creata e gestita dal proprietario: Opus 5.5 a impegno medio, martedì alle 06:07 ora italiana, rete completa, approvazione automatica (2026-11-06, "Fase 3 attiva").
- Scrive sul ramo della PR di raccolta e la commenta; senza PR di raccolta, PR propria dal ramo `arricchimento/AAAA-MM-GG` (2026-11-06).
- Decide da solo soltanto con una prova citata; mai nome, date, luogo e organizzatore già scritti; mai social; mai merge (2026-11-06).
- Ricontrollo: le voci future di cui non è ancora stata letta la pagina dell'organizzatore, almeno 14 giorni dopo l'ultimo controllo, al massimo 5 per esecuzione; 3 ricerche più 1 mirata per evento. Valori provvisori (2026-11-06, 2026-11-17).
- Quando legge la pagina dell'evento dell'edizione giusta, `url_ufficiale` passa a quella pagina e il regolamento resta tra le `fonti` (2026-11-17).
- Le pattinate restano fuori dal ricontrollo: lavora solo quelle nuove della settimana (2026-11-22).
- Il registro `registro/AAAA-MM-GG-arricchimento.md` si committa solo quando c'è una PR (2026-11-06). Le dipendenze si installano con `python3 -m pip install --ignore-installed` (2026-11-17).

## Rilettura (`agenti/rilettura-mensile.md`)

- Seconda attività pianificata: due volte al mese riapre le pagine degli organizzatori delle gare future `confermato` o `non_autorizzato`, senza ricerche web; scrive solo campi vuoti e note pubbliche, segnala il resto al proprietario; PR propria solo se c'è qualcosa (2026-11-22).

## Calendario e pagina

- Descrizione dell'evento: solo ciò che serve a chi pattina, con le etichette tra parentesi quadre (2026-11-05, 2026-11-06). In fondo due link, `[URL]` e `[Regolamento FISR]`, ciascuno solo se c'è; nella proprietà `URL` e nella tabella della pagina un solo link (2026-11-17).
- Pagina: tutto il testo in `pagina_web/modello_index.html`, l'aspetto in `pagina_web/stile.css`; tabella in ordine cronologico inverso (2026-11-05).
- `pubblica.yml` genera `calendario.ics` e pagina a ogni merge su `main`; nessun file derivato in git. Pages serve l'ICS come `text/calendar` (2026-11-05).

## Fonti nuove

- Skate Terminal: solo pista, letta a mano una volta al mese; la voce nasce dai dati letti sul sito dell'organizzatore (2026-11-22).
- Scoperta di nuove gare: ricerca aperta ogni 2 settimane (2026-11-05; non ancora in funzione).

## Architettura: chi fa cosa

| Livello | Compito | Chi | Quando |
|---|---|---|---|
| 0 | `eventi.yaml` + `fonti.yaml` in git | — | sorgente di verità |
| 1 | Raccolta: legge una pagina, restituisce dati grezzi, non interpreta | script; modello economico solo per pagine irregolari | settimanale (lunedì, `raccolta.yml`) |
| 2 | Normalizzazione + deduplica | codice | ogni giro |
| 2b | Arricchimento: dal nome dell'organizzatore cerca il suo sito e la pagina dell'evento (regola 10); raccoglie link, distanze, orari, quote, gare Amatori/Fitness; segnala siti compromessi e pagine dell'edizione sbagliata | modello capace (serve giudizio) | settimanale (martedì): voci nuove della PR di raccolta, più il ricontrollo delle voci future di cui non è ancora stata letta la pagina dell'organizzatore (almeno 14 giorni dall'ultimo controllo, al massimo 5) |
| 2c | Rilettura: riapre le pagine degli organizzatori delle gare future già confermate o non ancora autorizzate; compila i campi vuoti e le note, segnala il resto senza toccare la voce | modello (nessuna ricerca, nessuna decisione sulle categorie: può essere più economico di quello del livello 2b) | due volte al mese: giro completo a inizio mese, giro corto a metà mese per le gare dei 30 giorni successivi (attività pianificata "rilettura", creata dal proprietario il 2026-11-22) |
| 3 | Verifica e classificazione: apre il regolamento di gara e la pagina dell'organizzatore, decide se ammette Master/Amatori, cita la prova | script per i regolamenti di gara FISR (`converti_fisr.py`, art. 10); modello capace per le pagine degli organizzatori | come i livelli 1 e 2b |
| 4 | Supervisore: commenta la PR con riassunto e dubbi evidenziati | modello capace | ogni giro |
| 5 | Pubblicazione: ICS + pagina via Pages | workflow Actions, dopo il merge del proprietario | — |
| 6 | Scoperta: ricerca aperta di nuove gare e nuove fonti → propone aggiunte a `fonti.yaml` | modello capace | ogni 2 settimane (Fase 4: non ancora in funzione) |
| 7 | Segnalazioni: legge le nuove risposte del modulo pubblico → candidati ripuliti in `dati/segnalazioni.yaml` | script (`raccogli_segnalazioni.py`); i candidati li lavora il modello capace del livello 2b | settimanale (lunedì, dentro `raccolta.yml`; dal 2026-11-22, da provare) |
