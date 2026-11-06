# Decisioni

Una riga per decisione, con data e motivo. Le decisioni si cambiano con una nuova riga, non cancellando quella vecchia.

| Data | Tema | Decisione | Motivo |
|---|---|---|---|
| 2026-11-05 | Perimetro | Master + Amatori/Fitness, gare e pattinate; Italia + CH, ES, PT, FR, AT, DE, SI | È il perimetro d'interesse del proprietario |
| 2026-11-05 | Piattaforma | File ICS pubblicato via GitHub Pages da questo repository; altri siti si limitano a un link `webcal://` e non vengono toccati | Separare il lavoro degli agenti dal sito di produzione |
| 2026-11-05 | Ritardo Android | Accettato: Google Calendar aggiorna le sottoscrizioni ICS ogni 12–24 h (talvolta di più) | Non dipende da noi |
| 2026-11-05 | Memoria degli agenti | Il repository stesso: `CLAUDE.md` + `appunti/diario.md` + `appunti/decisioni.md` | Versionata, leggibile dal proprietario, nessun servizio in più |
| 2026-11-05 | Scrittura | Nessun agente o script scrive su `main`: solo pull request; merge solo del proprietario (aiBR3) | Il proprietario approva ogni modifica |
| 2026-11-05 | Pubblicazione (opzione A) | Un workflow Actions genera `calendario.ics` da `eventi.yaml` a ogni merge su `main` e lo pubblica su Pages (sorgente "GitHub Actions"); l'ICS non è committato | Mai stantio, nessun file derivato nel repo |
| 2026-11-05 | Releases | Niente: l'ICS non va negli allegati delle release | Redirect + Content-Type non garantito, una release a settimana non ha senso; eventuale snapshot a fine stagione |
| 2026-11-05 | Licenza | Nessuna per ora; si aggiunge quando il calendario funziona davvero | Decisione rimandata |
| 2026-11-05 | Protezione di `main` | Provato con la PR #1: con "Restrict updates" e 1 approvazione il merge era bloccato (`mergeable_state: blocked`). Il proprietario ha tolto "Restrict updates" e portato le approvazioni a 0; la revisione del code owner e l'approvazione extra per modifiche non attribuite sono rimaste attive e **non hanno bloccato** il merge (contano solo con approvazioni ≥ 1) | Verificato di persona |
| 2026-11-05 | Stato `escluso` | Aggiunto allo schema: evento verificato che NON ammette Master/Amatori; resta nel file con la prova ma non viene pubblicato | Memoria per non riproporre lo stesso evento |
| 2026-11-05 | Eventi non confermati | Pubblicati con un prefisso nel titolo (`[da verificare]`, `[non ancora autorizzata]`, `[RINVIATA]`, `[ANNULLATA]`) invece di nasconderli | A chi consulta il calendario serve sapere cosa c'è all'orizzonte; `STATUS:CANCELLED` non usato perché alcune app nascondono gli eventi cancellati |
| 2026-11-05 | DTSTAMP | Deterministico: l'ultima tra `verificato_il` e le `letto_il` delle fonti | Nessun rumore a ogni generazione; i client vedono una modifica solo quando i dati cambiano |
| 2026-11-05 | Segnalazioni volontarie | Modulo Tally con campo obbligatorio "incolla il testo del post"; lettura via API; copia su Google Sheet | Facebook/Instagram non sono scriptabili |
| 2026-11-05 | Scoperta di nuove gare | Ricerca aperta ogni 2 settimane | |
| 2026-11-05 | Content-Type | GitHub Pages serve `calendario.ics` come `text/calendar` (verificato con curl dopo il primo deploy) | Nessun accorgimento necessario |
| 2026-11-05 | Informazioni personali | Il repository è pubblico: niente nomi, contatti, dispositivi o dettagli su chi lo usa. Si scrive "il proprietario" (aiBR3) e "segnalazioni volontarie" | Non pubblicare più del dovuto |
| 2026-11-05 | Prova dal titolo ufficiale | Per i campionati FISR senza regolamento di gara, il titolo nel calendario federale ('Campionato Italiano Maratona cat. J/S/M') vale come prova delle categorie: M → `confermato` con `categorie: [master]`; `cat.` senza M → `escluso` | Il calendario federale è ufficiale; il regolamento del campionato si cercherà nei comunicati per distanze e dettagli |
| 2026-11-05 | Scansione degli id dei regolamenti di gara | I regolamenti di gara restano online anche senza link: si scandisce l'intervallo di id (6300–7100 nel 2026) e si abbinano alle righe della lista per data e nome | Unico modo per avere la prova delle gare passate e di quelle 'non autorizzate' |
| 2026-11-05 | Conversione automatica con revisione | `converti_fisr.py` propone le voci (categorie e prova dalle righe dell'art. 10); nomi, luoghi e organizzatori vengono rivisti a mano prima della PR; le voci già presenti non si toccano | Evita errori di battitura su decine di voci; la decisione resta tracciabile |
| 2026-11-05 | Descrizione degli eventi | Solo ciò che serve a chi pattina: categorie e distanze, organizzatore, scadenza, un solo link ("Informazioni"), note. Niente prova, fonti, stato, link al calendario | Troppe informazioni confondevano; i dati di lavoro restano nell'YAML |
| 2026-11-05 | Link dell'evento | Proprietà `URL` dell'evento (RFC 5545) **e** stessa riga nella descrizione | Calendario di Apple mostra `URL`, Google Calendar la ignora |
| 2026-11-05 | Pagina Pages | Testo in `pagina/modello_index.html` (segnaposto controllati dallo script), CSS in `pagina/stile.css`; ogni file di `pagina/` viene copiato nella cartella pubblicata e lo script verifica che i file citati da `href`/`src` esistano | Modificabile senza toccare Python |
| 2026-11-05 | `note` e `note_interne` | `note` = pubbliche (descrizione dell'evento), `note_interne` = dati di lavoro mai pubblicati. Migrate le 59 voci: 22 frasi spostate | Le note erano l'unico campo libero visibile a tutti e mescolavano le due cose |
| 2026-11-05 | Cartella appunti | `note/` rinominata `appunti/` | Richiesta del proprietario |
| 2026-11-06 | Cartella `pagina_web` | `pagina/` rinominata `pagina_web/` (riferimenti aggiornati in `CLAUDE.md`, `genera_ics.py` e nei due workflow); trattino basso come nei nomi dei file del repo, niente spazi | Richiesta del proprietario: il nome deve dire che è la pagina web pubblicata |
| 2026-11-05 | Parola "indizione" | Sostituita ovunque (testi, dati, codice, parametri degli script, chiavi JSON) con "regolamento di gara" / "regolamento" | Incomprensibile per chi non vive nel gergo federale; il documento stesso si intitola "Regolamento particolare" |
| 2026-11-05 | Testo della pagina | Tutto nel modello HTML, compresi pulsante di iscrizione e istruzioni per Google; lo script passa solo `url_webcal`, `url_ics`, `numero_eventi`, `righe_tabella`, `generato_il` (più `titolo`/`descrizione`, facoltativi). Tabella in ordine cronologico inverso | Il proprietario deve poter cambiare il testo senza toccare Python |
| 2026-11-06 | Etichette della descrizione | Tra parentesi quadre (`[Categorie ammesse] Master`), non seguite dai due punti | I due punti li usano gli organizzatori nei loro testi: si confondevano con le etichette |
| 2026-11-05 | Righe della descrizione | Il link è preceduto da `URL:`, le note pubbliche da `Informazioni:` | Richiesta del proprietario |
| 2026-11-05 | Scartato | Submodule del solo file ICS (un submodule punta a un repository intero); profilo Facebook fittizio (viola i termini di Meta, viene bloccato) | |
| 2026-11-06 | Sito dell'organizzatore | Regola 10: per ogni evento si cerca il sito dell'organizzatore locale e si legge la pagina dell'evento; è un passo a sé dell'architettura ("arricchimento", livello 2b) | Le liste federali non dicono link, distanze, quote né le gare Amatori/Fitness: Pordenone 24/05 ha una 21 km Fitness solo sul sito del club; Vado Ligure ha un sito proprio; Berlino e Napoli non stanno su fisr.info |
| 2026-11-06 | Prova per Amatori/Fitness | La pagina ufficiale dell'organizzatore vale come prova (regola 3), insieme ai bollettini World Skate | Le gare Fitness non hanno regolamento FISR: senza questa fonte gli amatori non comparirebbero mai |
| 2026-11-06 | Gare aperte per anno di nascita | Una gara aperta a tutti i nati entro un certo anno, senza categorie agonistiche obbligatorie (Berlino: "Jahrgänge 2012 und älter"), vale `[master, amatori]` con quella frase come prova | All'estero non esiste la distinzione italiana Master/Amatori |
| 2026-11-06 | `organizzatore` | È la società o il club che organizza sul posto, non "FISR": la federazione approva e rende campionato, ma i dettagli li comunica solo l'organizzatore locale | Richiesta del proprietario |
| 2026-11-06 | Siti compromessi | Un sito dell'organizzatore con pagine di spam non si linka (vadosustrada2026.it); si annota in `note_interne` e si ricontrolla | Non mandare chi pattina su pagine di gioco d'azzardo |
| 2026-11-06 | Più gare nello stesso giorno | Una voce sola quando lo stesso organizzatore fa più gare nello stesso giorno e luogo (Napoli: 42 km Pro/Master + 20 km Amatori); le distanze dicono chi corre cosa | Un evento in calendario, non due |
| 2026-11-06 | Pagine sparite | Le pagine ufficiali delle gare passate vengono tolte (Berlino 2026): si leggono dalla Wayback Machine e si cita lo snapshot in `fonti` | L'unica copia verificabile |
| 2026-11-06 | Casi di prova | `appunti/casi-di-prova.md` raccoglie gli eventi reali che la scoperta e l'arricchimento devono saper trovare, con il motivo per cui erano sfuggiti | Misurare i livelli 2b e 6 quando saranno automatici |

## Fasi

- **Fase 0 — fatta (2026-11-05):** schema, piattaforma, perimetro, repository.
- **Fase 1 — in corso:** a mano, insieme: fisr.info → `eventi.yaml` → `calendario.ics` → Pages → iscrizione dal telefono. Zero autonomia. Pubblicazione fatta con la PR #1 (2026-11-05); con la PR #4 tutte le gare FISR dal 1° gennaio 2026 (59 voci, 16 pubblicate) per la verifica del proprietario, che ad alcune ha partecipato. La verifica dal telefono (2026-11-06) ha fatto emergere quattro eventi o dettagli che solo i siti degli organizzatori e le fonti estere danno: da qui la regola 10 e i casi di prova.
- **Fase 2:** la stessa cosa come attività pianificata settimanale che apre una PR.
- **Fase 3:** arricchimento (cerca il sito dell'organizzatore, regola 10) + verifica (apre regolamento e pagina dell'organizzatore, cita la prova) + supervisore (assembla la PR con riassunto e dubbi). I casi di `appunti/casi-di-prova.md` sono il collaudo.
- **Fase 4:** scoperta di nuove fonti, registro fonti, segnalazioni Tally, Facebook via Claude in Chrome.

## Architettura: chi fa cosa

| Livello | Compito | Chi | Quando |
|---|---|---|---|
| 0 | `eventi.yaml` + `fonti.yaml` in git | — | sorgente di verità |
| 1 | Raccolta: legge una pagina, restituisce dati grezzi, non interpreta | script; modello economico solo per pagine irregolari | settimanale |
| 2 | Normalizzazione + deduplica | codice | ogni giro |
| 2b | Arricchimento: dal nome dell'organizzatore cerca il suo sito e la pagina dell'evento (regola 10); raccoglie link, distanze, orari, quote, gare Amatori/Fitness; segnala siti compromessi e pagine dell'edizione sbagliata | modello capace (serve giudizio) | solo su candidati nuovi o cambiati |
| 3 | Verifica e classificazione: apre il regolamento di gara e la pagina dell'organizzatore, decide se ammette Master/Amatori, cita la prova | modello capace | solo su candidati nuovi o cambiati |
| 4 | Supervisore: assembla la PR con riassunto e dubbi evidenziati | modello capace | ogni giro |
| 5 | Pubblicazione: ICS + pagina via Pages | workflow Actions, dopo il merge del proprietario | — |
| 6 | Scoperta: ricerca aperta di nuove gare e nuove fonti → propone aggiunte a `fonti.yaml` | modello capace | ogni 2 settimane |
| 7 | Segnalazioni: legge le nuove risposte Tally → candidati | script | settimanale |

## Punti aperti

- Chi esegue gli script deterministici delle fasi 2+: GitHub Actions a orario (segreti nei GitHub Secrets) oppure attività pianificate Claude. Proposta: Actions per gli script (le PR sarebbero di `github-actions[bot]`, che il proprietario può approvare), Claude per i compiti di giudizio.
- Le due voci `da_verificare` ancora pubblicate (Speed Track European Series 14-17/05, Cardano al Campo 12-13/09) e i due campionati `confermato` dal solo titolo (Pordenone 24/05, Vado Ligure 3-6/09): cercare il regolamento nei comunicati FISR. Per Pordenone la pagina del club ha intanto dato distanze e Fitness; per Vado Ligure il sito dell'organizzatore è compromesso (2026-11-06): ricontrollare.
- Nessuna gara FISR 2026 prevede la categoria Amatori nel programma: gli Amatori stanno nei siti degli organizzatori (Fitness), negli Enti di promozione, nelle tappe Challenger del World Skate Marathon Tour e nelle pattinate.
- `url_iscrizione` per le gare FISR: le iscrizioni passano "esclusivamente attraverso il sito Internet federale"; quale pagina linkare?
- Il Google Calendar di pattiniamolitalia.it è pubblico? Ha un ICS diretto?
- World Skate Marathon Tour 2026: la tappa Challenger di Pamplona (ES, 07/06/2026) è in perimetro e va letta (bollettino + sito dell'organizzatore); Napoli è fatta.
- Gli Enti di promozione (AICS, UISP, CSEN…) hanno circuiti con categoria Amatori: da censire come fonti.
- Berlin-Marathon 2027 (Generali, 26/09/2027): il programma ufficiale non elenca l'inline, ma manca un annuncio esplicito; ricontrollare prima di decidere se creare la voce.
- Il calendario SCC Events offre un file `.ics` di tutti i suoi eventi: valutare se leggerlo da script (livello 1) invece della pagina HTML.
- Dal 2027 il repository avrà gare estere (DE): i testi pubblici restano in italiano; decidere se le `note` devono riportare anche i termini originali (es. "Jahrgang").
