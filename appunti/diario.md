# Diario: cosa non ha funzionato

Scopo: non risolvere lo stesso problema due volte. Prima di tentare qualcosa, cerca qui.

Una voce per problema: data, cosa si voleva fare, cosa è successo, cosa fare invece.

Quando un problema si risolve per sempre, si aggiorna la voce invece di cancellarla.

## 2026-11-05 — Sessione Claude (web): API GitHub bloccate dal proxy

- **Volevo:** attivare GitHub Pages e leggere le impostazioni di Actions via `gh api`.
- **Successo:** `GET/POST /repos/…/pages`, `/actions/permissions`, `/collaborators` → HTTP 403 "Access to this GitHub API path is not permitted through this proxy". Anche `gh api` verso repository non collegati alla sessione (es. `actions/checkout`) → 403.
- **Invece:** Pages la attiva il proprietario dalle impostazioni (Settings → Pages → Source: GitHub Actions). Le versioni delle azioni si leggono dalla documentazione GitHub, non dall'API. I ruleset invece si leggono (`/rulesets`, `/rules/branches/main`).

## 2026-11-05 — Sessione Claude: GraphQL non disponibile

- **Volevo:** `gh repo view --json …`.
- **Successo:** HTTP 403 "GitHub GraphQL is not available from Claude Code sessions".
- **Invece:** solo REST: `gh api repos/{owner}/{repo}/…`.

## 2026-11-05 — Sessione Claude: estensione Chrome non collegata

- **Volevo:** usare Claude in Chrome (con il login del proprietario) per attivare Pages.
- **Successo:** "Browser extension is not connected".
- **Invece:** per ora le operazioni nell'interfaccia GitHub le fa il proprietario. Da riprovare quando servirà per Facebook (Fase 4): l'estensione va collegata allo stesso account claude.ai.

## 2026-11-05 — Sessione Claude: WebFetch legge solo URL già comparsi nella conversazione

- **Volevo:** aprire `fisr.info/attivita/corsa_calendario.php` direttamente.
- **Successo:** "URL_NOT_ON_ALLOWLIST".
- **Invece:** prima una ricerca web che faccia comparire l'URL tra i risultati (es. `fisr.info corsa_calendario.php`), poi la lettura. Vale anche per le pagine delle regolamenti di gara (`corsa_trofeo_modulo.php?id_manif=N`).

## 2026-11-05 — fisr.info: i link ai regolamenti di gara spariscono, ma le pagine restano

- **Volevo:** leggere il regolamento di gara di tutte le gare dal 1° gennaio 2026.
- **Successo:** nella lista solo 3 gare su 66 avevano il link 'modulo' (quelle future). Le pagine `corsa_trofeo_modulo.php?id_manif=N` però esistono ancora, anche per le gare 'non ancora autorizzate' (es. 7047 = L'Aquila 06/12/2026). Gli id non sono cronologici e molti sono vuoti o bozze (`[[denom]]`, date mancanti).
- **Invece:** `raccogli_fisr.py --scansione-regolamenti 6300 7100` scarica tutto l'intervallo (≈800 richieste, ~10 minuti con pausa 0,2 s), tiene solo i regolamenti di gara completi nel periodo, e `converti_fisr.py` le abbina alle righe per data (±1 giorno) e somiglianza del nome o dell'organizzatore. Trovati 46 regolamenti di gara completi per il 2026.

## 2026-11-05 — fisr.info: trappole nella lista

- `?anno=2026` restituisce la stagione 2025/26 **più** i mesi già noti della 2026/27: chiedere anche `?anno=2027` produce righe doppie.
- Campionati e attività nazionale stanno in righe a 2 celle (`nome - località`, a volte `-Torino` senza spazio), spesso ripetute accanto alla riga a 7 celle con date leggermente diverse (04-07/06 vs 05-07/06). `converti_fisr.py` le unisce (stessa data ±2 giorni e nomi simili).
- Un nome era in **base64** nella fonte (`MbBtYWdnaW8g…` = "1°maggio Ferrara Inlne…"): decodificato.
- Lo stesso evento può comparire due volte con nomi diversi (Cardano al Campo 12-13/09 e 13/09) o con la stessa numerazione in due date (Montesilvano 13/09 e 04/10; Imola 08/11 e 08/12, entrambe "49°").
- Le pagine dei regolamenti di gara hanno codifica mista: decodificare come cp1252 e riparare il mojibake UTF-8 parola per parola.

## 2026-11-05 — fisr.info: la lista non dice le categorie, il regolamento di gara sì

- **Volevo:** capire dalla lista `corsa_calendario.php` quali gare ammettono i Master.
- **Successo:** la lista ha solo data, nome, località, organizzatore, scadenze. Le categorie sono nel regolamento di gara (`corsa_trofeo_modulo.php?id_manif=N`, link "modulo" nella riga), art. 9-10. Gli eventi "Attività non ancora autorizzata" non hanno ancora il modulo. Esempio: Imola 08/11 e 08/12 hanno lo stesso nome e numero (49°), ma solo quella di dicembre ha le categorie Master.
- **Invece:** la lista serve a scoprire; la decisione sulle categorie si prende solo sul regolamento di gara. La pagina ha errori di codifica ("CITTÃ" per "CITTÀ"): normalizzare i nomi.

## 2026-11-06 — vadosustrada2026.it: sito dell'organizzatore compromesso

- **Volevo:** mettere il sito del Campionato Italiano su strada (Vado Ligure, 3-6/09/2026) in `url_ufficiale`.
- **Successo:** la home è integra (date, impianto, organizzatore), ma `/programma/`, `/contatti/` e `/area-camper/` servono pagine di spam su gioco d'azzardo in indonesiano e "La manifestazione" risponde 404 "Halaman tidak ditemukan". WordPress compromesso.
- **Invece:** nessun link nel calendario, nota in `note_interne`, ricontrollo periodico. Regola generale: prima di linkare un sito di un organizzatore, aprire almeno una pagina interna oltre alla home e cercare parole estranee (slot, togel, lingue non attese).

## 2026-11-06 — Pagine ufficiali che spariscono dopo la gara

- **Volevo:** citare la pagina di iscrizione della BMW Berlin-Marathon Inlineskating 2026 (26/09/2026).
- **Successo:** `skating.bmw-berlin-marathon.com` e `/en/registration/inlineskating` rispondono 404 sei settimane dopo la gara; il sito è già passato all'edizione 2027 con un altro nome di dominio.
- **Invece:** Wayback Machine dalla shell: `https://web.archive.org/web/AAAAMMGG/URL` restituisce lo snapshot più vicino (qui 2026-09-27); `http://archive.org/wayback/available?url=…&timestamp=…` dice se esiste. L'API CDX (`web.archive.org/cdx/search/cdx`) è bloccata dal proxy ("Blocked by egress policy"). Per le gare future: leggere e citare la pagina ufficiale prima che la gara passi.

## 2026-11-06 — Pagine dell'edizione sbagliata

- **Volevo:** leggere la pagina 2026 del Campionato Italiano Maratona (Skating Club Comina) e quella 2027 delle gare SCC Events.
- **Successo:** su skatingclubcomina.eu il menu punta a `/campionati-italiani-maratona-2026`, che è vuota: i dati 2026 stanno nella pagina con `2025` nell'indirizzo. Su generali-berliner-halbmarathon.de l'intestazione dice "2026" ma il periodo di iscrizione arriva all'11/03/2027: è la pagina 2027. Su berlin-citynight.de la pagina mostra ancora quote e condizioni 2026 per l'evento del 31/07/2027.
- **Invece:** l'edizione si riconosce dalle date nel testo (data della gara, periodo di iscrizione), mai dall'anno nell'indirizzo o nel titolo. Se il testo è dell'edizione passata, la voce resta `annunciato` con la data presa dal calendario dell'organizzatore.

## 2026-11-06 — Traduzioni inglesi inaffidabili sui siti tedeschi

- **Volevo:** citare la frase di ammissione della Generali Berlin Half Marathon Inlineskating.
- **Successo:** la versione inglese dice "born in 2012 and later", il tedesco "Jahrgänge 2012 und älter" (nati nel 2012 o prima): la traduzione rovescia il senso.
- **Invece:** per la prova si cita la lingua originale del sito.

## 2026-11-06 — Cosa raggiunge la shell (aggiornamento)

- Oltre a fisr.info e github.io, la shell raggiunge i siti degli organizzatori provati finora (vadosustrada2026.it, skatingclubcomina.eu, rollerskatingfestivalnapoli.it, bmw-berlin-marathon.com, generali-berlin-marathon.com, generali-berliner-halbmarathon.de, berlin-citynight.de, scc-events.com) e web.archive.org. Bloccato: adidas-runners-city-night.de (il sito vero della City Night è comunque berlin-citynight.de). Il blocco si vede come `CONNECT tunnel failed, response 502`.

## 2026-11-06 — GitHub segna "conflitto" dopo il rinomina di una cartella

- **Volevo:** aprire la PR #17 (modifica a `pagina/modello_index.html`) basata su `main` mentre la PR #16 rinominava la cartella in `pagina_web/`; in locale `git merge` fondeva le tre PR in ogni ordine senza conflitti.
- **Successo:** appena la #16 è stata fusa, GitHub ha marcato la #17 `mergeable_state: dirty`: il calcolo di GitHub non riconosce "file rinominato da una parte, modificato dall'altra" come fa git in locale.
- **Invece:** dopo un rinomina, le PR aperte che toccano i file rinominati vanno ribasate (`git rebase origin/main`, che applica la modifica al nuovo percorso) e spinte con `--force-with-lease=ramo:sha-remoto` (il `--force-with-lease` semplice fallisce con "stale info" dopo un `git fetch`). Meglio ancora: fondere prima la PR del rinomina, poi aprire le altre.

## 2026-11-06 — Collaudo cieco dell'arricchimento: la ricerca web non trova i siti dei club

- **Volevo:** far trovare a un agente nuovo, con il solo prompt `agenti/arricchimento.md`, i siti degli organizzatori dei casi di prova 1 (Vado Ligure) e 2 (Pordenone), e dei 5 club italiani delle voci future pubblicate.
- **Successo:** 0 siti su 7. Con 3 ricerche per evento (organizzatore + città; nome + anno; parte distintiva + "pattinaggio corsa") la ricerca web della sessione restituisce solo giornali locali, agenzie, PDF di FIDAL e Federciclismo, calcio e Formula 1; i siti delle piccole società non compaiono. Nemmeno le query esatte che il 2026-11-06 avevano portato a vadosustrada2026.it e skatingclubcomina.eu li fanno uscire. I giornali nell'estratto nominano però l'organizzatore e l'impianto (ivg.it: "Roller Sports Vado Ligure", stadio Chittolina).
- **Invece:** per gli organizzatori già noti (SCC Events) la rilettura della pagina costa zero ricerche e funziona. Per i club italiani le strade da valutare (decisione del proprietario, PR #33): leggere un articolo di giornale al solo scopo di ricavare nome e dominio dell'organizzatore, poi una ricerca mirata con il nome esatto; aprire il regolamento di gara FISR (art. 1 nomina la società organizzatrice); cercare il club nell'elenco delle società affiliate FISR; oppure rimandare i piccoli club ai social della Fase 4 e non spendere ricerche. Dettagli in `registro/2026-11-06-arricchimento.md`.

## 2026-11-06 — fisr.info: le classifiche di società danno il codice FISR, i regolamenti danno i siti

- **Volevo:** un elenco delle società di pattinaggio corsa con i loro siti, per non cercare ogni organizzatore sul web.
- **Successo:** `fisr.it` non ha un elenco pubblico delle affiliate (ricerca web senza esito). Su `fisr.info` la pagina `corsa_classifiche.php` (POST `anno=2026` per la 2025/26) linka 5 classifiche nazionali su `attivita.rollergames.it` e, con `corsa_campionati_locali.php` (POST `anno`, `cosa=R`, `id_regione` 1-20, `tipo` P/S), 40 regionali: tutte con **codice società** e sigla (158 società, nessun codice con sigle diverse). Le pagine dei risultati (`corsa_risultati.php`, POST `anno`; 111 gare → `rollergames.it/corsa/rrunn/...`) hanno l'intestazione "Organizzato da NOME ESTESO". I regolamenti di gara citano il sito dell'organizzatore in 12 casi su 46 (es. `cpga.net`, `eurosportclub.it`, `rollerspeedcentro.it`: proprio i siti che la ricerca web non aveva trovato la mattina). La shell raggiunge `attivita.rollergames.it`; i server federali chiudono ogni tanto la connessione ("Connection reset by peer"): serve riprovare.
- **Invece:** `script/raccogli_societa.py` fa tutto questo a ogni stagione. Le sigle federali sono troncate ("PATT.RI S.SIRO", "C.SP.P.PESCARA"): l'abbinamento tra sigla e nome esteso va per parole e si rifiuta quando due società della stessa città si somigliano (tre a Pescara, due a Priolo, due a Civitanova, due a Elmas): quelle si fissano a mano nel campo `nome`.

## 2026-11-06 — Ricerca web dei siti delle società con quattro sottoagenti

- **Volevo:** il sito o il social delle 152 società senza sito nei regolamenti.
- **Successo:** 50 siti e 32 social trovati, 70 società senza traccia; alla verifica (apertura dalla shell) 44 siti confermati, 11 non raggiungibili dalla shell (HTTP 999, 406, 500, timeout: anti-bot o server lenti, non per forza morti), 1 da verificare. Tre sottoagenti su quattro sono stati fermati dal limite orario dell'account mentre scrivevano l'uscita, ma i file erano già su disco. Consiglio di un sottoagente: con questo motore il nome tra virgolette e la modalità estesa danno risultati utili, la modalità normale restituisce giornali e pattinaggio su ghiaccio.
- **Invece:** i siti vanno verificati sempre da chi li raccoglie (titolo, dominio e testo), non ci si fida del risultato di ricerca; i siti di blog e `altervista` sono fragili; le società del Sud e delle isole non lasciano traccia oltre alle classifiche.


## 2026-11-06 — Siti renderizzati via JavaScript, WebFetch e Wayback nel secondo collaudo cieco

- **Volevo:** leggere dalla shell la home e la pagina dell'evento di skatingclubcomina.eu (Aruba SuperSite) e, per Vado Ligure, un articolo di ivg.it e uno snapshot della Wayback Machine.
- **Successo:** `curl` sul sito Aruba restituisce una pagina vuota (contenuto caricato via JavaScript); la pagina dichiara `<meta name="fragment" content="!">` e con `?_escaped_fragment_=` arriva il testo completo. ivg.it risponde 403 con la sfida di Cloudflare ("Enable JavaScript and cookies"). WebFetch rifiuta ogni indirizzo che non sia uscito da una ricerca web della sessione, anche la home presa dal registro. web.archive.org: il sottoagente ha provato l'API CDX (bloccata dal proxy, come già scritto) e non l'indirizzo dello snapshot.
- **Invece:** per i siti con `<meta name="fragment">` si rilegge lo stesso indirizzo con `?_escaped_fragment_=` (non è un indirizzo indovinato: lo dichiara la pagina); i giornali dietro anti-bot non si riprovano, si passa a un altro; le pagine prese dal registro o dal regolamento si aprono solo dalla shell; la Wayback Machine solo come `https://web.archive.org/web/AAAAMMGG/URL` dalla shell. Tutto scritto nel prompt dell'arricchimento.


## 2026-11-06 — Scelta dell'articolo nel terzo collaudo cieco (Opus, impegno medio)

- **Volevo:** per Vado Ligure, leggere il nome esteso e il dominio dell'organizzatore da un articolo, come consente il passo 3 del prompt.
- **Successo:** i risultati di ricerca davano solo il nome del sito (`www.ivg.it`) senza titolo né estratto; il primo tentativo (ivg.it) non si è aperto, il secondo, scelto a caso, era un articolo del 2025 su un'altra gara, e ha consumato il limite di un articolo senza dare nulla. La ricerca mirata con il nome preso dal registro ha ripetuto esattamente la ricerca (a). L'orologio della sessione dava 10-30 secondi per evento: non è una misura.
- **Invece:** si apre un articolo solo se il titolo o l'estratto nominano la gara, la città o l'organizzatore; se nessun risultato lo fa, nessun articolo. La ricerca mirata si salta quando il nome esatto è già stato usato nella ricerca (a). Per la durata fa fede la pagina dell'attività pianificata. Tutto scritto nel prompt.


## 2026-11-06 — Prima esecuzione dell'attività pianificata: il ramo `claude/…`

- **Volevo:** la prova dell'attività pianificata "Arricchimento calendario pattinaggio corsa" (Opus 5.5, impegno medio, ambiente con rete completa), lanciata a mano dal proprietario.
- **Successo:** 36 secondi, Passi 0-2 eseguiti, nessuna PR aperta e nessuna voce da ricontrollare (le 4 voci future senza prova o senza link hanno la traccia di oggi e rientrano dal 2026-11-21), niente ramo e niente PR, come previsto; `gh api` risponde; fisr.info 200 e skatingclubcomina.eu 301 dalla shell. Un'anomalia: l'agente ha letto nelle istruzioni della sessione pianificata che deve spingere solo su un ramo `claude/…` generato dalla piattaforma, in contrasto con il prompt (ramo della PR di raccolta oppure `arricchimento/OGGI`), e ha chiesto quale usare.
- **Invece:** la documentazione delle attività pianificate dice che Claude spinge su un ramo `claude/…` "a meno che il prompt non indichi un altro ramo": il prompt dell'attività ora lo indica esplicitamente (punto 3). Da verificare alla prima esecuzione con lavoro vero che il push sul ramo `raccolta/…` passi; se la piattaforma lo bloccasse, l'alternativa è aprire la PR dell'arricchimento dal ramo `claude/…` verso il ramo di raccolta.
