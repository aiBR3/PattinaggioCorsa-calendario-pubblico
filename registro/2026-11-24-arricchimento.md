# Arricchimento del 2026-11-24

- Ramo: `raccolta/2026-11-23` (PR #93, raccolta del 2026-11-23)
- Esecuzione: attività pianificata; orologio della sessione 05:07-05:13 UTC circa (fa fede la pagina dell'attività)

## Voci

| id | esito | sito da | campi cambiati | ricerche | articoli | pagine aperte | minuti |
|---|---|---|---|---|---|---|---|
| `2027-02-14-laquila-internazionali-open-indoor-master-race` (nuova) | sito non raggiungibile | registro | `prova` (righe Master ora da Over 30 a Over 60), `verificato_il`, `letto_il` del regolamento, `note_interne` | 0 | 0 | 2: https://cpga.net/ (502), regolamento 7047 | ~2 |
| `2026-12-08-imola-gran-premio-indoor` | sito non trovato | — | `note_interne` (indizio sull'impianto, da confermare) | 2 | 0 | 1: regolamento 7046 | ~2 |
| `2027-06-06-terni-memorial-alfonso-zenga` | sito trovato, pagina dell'evento assente | registro | `url_ufficiale` (home della società), `fonti`, `note_interne` | 0 | 0 | 2: https://www.eurosportclub.it/, https://www.eurosportclub.it/category/news/ | ~1 |
| `2027-07-03-fabriano-trofeo-dellamicizia-memorial-donatella` | sito trovato, pagina dell'evento assente | registro | `url_ufficiale` (home del sito del registro), `fonti`, `note_interne` | 0 | 0 | 2: https://www.rollerspeedcentro.it, https://www.rollerspeedcentro.it/le-gare/ | ~1 |
| `2027-07-31-berlino-adidas-runners-city-night-inlineskating` | sito trovato, pagina dell'edizione precedente | registro | `letto_il`, `note_interne` | 0 | 0 | 1: https://www.berlin-citynight.de/en/registration/10k-inline-skating | ~1 |
| `2027-09-25-pollenza-memorial-gilda-leoperdi-trofeo` | solo social (Fase 4) | registro | `note_interne` | 0 | 0 | 0 | <1 |

Altra voce cambiata dalla PR, non lavorata: `2027-07-31-san-benedetto-del-tronto-meeting-san-benedetto-tronto` (solo `nome_fonte` registrato; è `escluso`).

## Totali

- Voci nuove: 1 lavorata (L'Aquila, febbraio 2027: è la gara del regolamento 7047 spostata dal 06/12/2026, quindi con `id` nuovo).
- Voci vecchie ricontrollate: 5 (limite raggiunto; nessuna rimasta fuori: le altre candidate hanno l'ultimo controllo a meno di 14 giorni).
- Pattinate: 0 da lavorare (nessuna nuova né segnalata dallo script). Segnalazioni: 0 candidati.
- Promosse a `confermato`: 0. Passate a `escluso`: 0.
- Siti trovati: 3 dal registro (Terni, Fabriano, Berlino). Non trovati: 1 (Imola). Non raggiungibili: 1 (cpga.net). Solo social: 1 (Pollenza).
- Società aggiornate nel registro: 1 (`808` Gruppo Imolese P.: nota con le ricerche nuove).
- Ricerche web: 2. Articoli aperti: 0.

## Dubbi

1. L'Aquila (14/02/2027, regolamento 7047): il regolamento è cambiato anche nelle categorie, non solo nella data. Il titolo dice "Master Race", ma il programma ora ha Allievi, Ragazzi, Ragazzi 12, Esordienti, Giovanissimi e Master solo da Over 30 a Over 60 (niente più Over 65-75). `master` resta provato; la `prova` è stata riscritta sulle righe di oggi. In `note_interne` resta la frase vecchia "Scadenza iscrizioni 30/11, termine depennamenti 01/12" (edizione di dicembre): non cancellata, segnalata nella frase di arricchimento.
2. Fabriano: il sito del registro per Fortitudo Fabriano è quello del circuito Roller Speed Centro (citato nel regolamento 6711), non un sito proprio della società; ora è `url_ufficiale` della voce come home dell'organizzatore. Decide il proprietario se va bene.
3. Imola: un sito turistico del comune colloca in via Benedetto Croce 34 l'impianto Ricci Petitoni; scritto solo in `note_interne` come indizio da confermare.

## Errori

- cpga.net non raggiungibile dalla shell (502 dal proxy, due tentativi); il 2026-11-17 si apriva. Non riprovato per altre vie: si riprende al prossimo ricontrollo.
