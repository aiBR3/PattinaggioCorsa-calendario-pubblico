# Decisioni

Una riga per decisione, con data e motivo. Le decisioni si cambiano con una nuova riga,
non cancellando quella vecchia.

| Data | Tema | Decisione | Motivo |
|---|---|---|---|
| 2026-11-05 | Perimetro | Master + Amatori/Fitness, gare e pattinate; Italia + CH, ES, PT, FR, AT, DE, SI | È quello che interessa alla squadra |
| 2026-11-05 | Piattaforma | File ICS pubblicato via GitHub Pages da questo repository; il sito Hugo della squadra ha solo un link `webcal://` e non viene toccato | Separare il lavoro degli agenti dal sito di produzione |
| 2026-11-05 | Ritardo Android | Accettato: Google Calendar aggiorna le sottoscrizioni ICS ogni 12–24 h (talvolta di più) | Non dipende da noi |
| 2026-11-05 | Memoria degli agenti | Il repository stesso: `CLAUDE.md` + `note/diario.md` + `note/decisioni.md` | Versionata, leggibile da T, nessun servizio in più |
| 2026-11-05 | Scrittura | Nessun agente o script scrive su `main`: solo pull request; merge solo di T | T approva ogni modifica |
| 2026-11-05 | Pubblicazione (opzione A) | Un workflow Actions genera `calendario.ics` da `eventi.yaml` a ogni merge su `main` e lo pubblica su Pages (sorgente "GitHub Actions"); l'ICS non è committato | Mai stantio, nessun file derivato nel repo |
| 2026-11-05 | Releases | Niente: l'ICS non va negli allegati delle release | Redirect + Content-Type non garantito, una release a settimana non ha senso; eventuale snapshot a fine stagione |
| 2026-11-05 | Licenza | Nessuna per ora; si aggiunge quando il calendario funziona davvero | Decisione rimandata |
| 2026-11-05 | Protezione di `main` | Ruleset attivo così com'è (restrict updates, 1 approvazione, code owner): **in prova** con la PR #1, che secondo Claude non sarà mergeabile. Se blocca, si corregge: 0 approvazioni + niente "restrict updates" | T vuole verificare di persona |
| 2026-11-05 | Stato `escluso` | Aggiunto allo schema: evento verificato che NON ammette Master/Amatori; resta nel file con la prova ma non viene pubblicato | Memoria per non riproporre lo stesso evento |
| 2026-11-05 | Eventi non confermati | Pubblicati con un prefisso nel titolo (`[da verificare]`, `[non ancora autorizzata]`, `[RINVIATA]`, `[ANNULLATA]`) invece di nasconderli | Alla squadra serve sapere cosa c'è all'orizzonte; `STATUS:CANCELLED` non usato perché alcune app nascondono gli eventi cancellati |
| 2026-11-05 | DTSTAMP | Deterministico: l'ultima tra `verificato_il` e le `letto_il` delle fonti | Nessun rumore a ogni generazione; i client vedono una modifica solo quando i dati cambiano |
| 2026-11-05 | Segnalazioni dai compagni | Modulo Tally con campo obbligatorio "incolla il testo del post"; lettura via API; copia su Google Sheet | Facebook/Instagram non sono scriptabili |
| 2026-11-05 | Scoperta di nuove gare | Ricerca aperta ogni 2 settimane | |
| 2026-11-05 | Scartato | Submodule del solo file ICS (un submodule punta a un repository intero); profilo Facebook fittizio (viola i termini di Meta, viene bloccato) | |

## Fasi

- **Fase 0 — fatta (2026-11-05):** schema, piattaforma, perimetro, repository.
- **Fase 1 — in corso:** a mano, insieme: fisr.info → `eventi.yaml` → `calendario.ics` → Pages → iscrizione su iPhone. Zero autonomia.
- **Fase 2:** la stessa cosa come attività pianificata settimanale che apre una PR.
- **Fase 3:** verifica (apre l'indizione, cita la prova) + supervisore (assembla la PR con riassunto e dubbi).
- **Fase 4:** scoperta di nuove fonti, registro fonti, segnalazioni Tally, Facebook via Claude in Chrome.

## Architettura: chi fa cosa

| Livello | Compito | Chi | Quando |
|---|---|---|---|
| 0 | `eventi.yaml` + `fonti.yaml` in git | — | sorgente di verità |
| 1 | Raccolta: legge una pagina, restituisce dati grezzi, non interpreta | script; modello economico solo per pagine irregolari | settimanale |
| 2 | Normalizzazione + deduplica | codice | ogni giro |
| 3 | Verifica e classificazione: apre l'indizione, decide se ammette Master/Amatori, cita la prova | modello capace | solo su candidati nuovi o cambiati |
| 4 | Supervisore: assembla la PR con riassunto e dubbi evidenziati | modello capace | ogni giro |
| 5 | Pubblicazione: ICS + pagina via Pages | workflow Actions, dopo il merge di T | — |
| 6 | Scoperta: ricerca aperta di nuove gare e nuove fonti → propone aggiunte a `fonti.yaml` | modello capace | ogni 2 settimane |
| 7 | Segnalazioni: legge le nuove risposte Tally → candidati | script | settimanale |

## Punti aperti

- Chi esegue gli script deterministici delle fasi 2+: GitHub Actions a orario (segreti nei GitHub Secrets) oppure attività pianificate Claude. Proposta: Actions per gli script (le PR sarebbero di `github-actions[bot]`, che T può approvare), Claude per i compiti di giudizio.
- Verificare il `Content-Type` del file `.ics` servito da Pages al primo deploy.
- Il Google Calendar di pattiniamolitalia.it è pubblico? Ha un ICS diretto?
- Quali tappe del World Skate Marathon Tour ammettono Master/amatori.
- Gli Enti di promozione (AICS, UISP, CSEN…) hanno circuiti con categoria Amatori: da censire come fonti.
