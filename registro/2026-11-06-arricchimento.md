# Arricchimento del 2026-11-06 (collaudo a mano, Fase 3)

Esecuzione a mano del prompt `agenti/arricchimento.md` in una sessione Claude (chat), ramo `fase3/arricchimento`, PR #33. Nessuna PR di raccolta aperta: su indicazione del proprietario le 7 voci future pubblicate sono state trattate come "voci nuove" (regola 10 su tutte), quindi il limite di 5 voci vecchie non è entrato in gioco. In parallelo, un sottoagente nuovo e senza contesto ha eseguito il solo Passo 3 sui casi di prova 1 e 2 di `appunti/casi-di-prova.md` (vedi in fondo).

## Voci lavorate

| id | Esito | Campi cambiati | Ricerche | Pagine | Minuti |
|---|---|---|---|---|---|
| 2026-12-06-laquila-internazionali-open-indoor-master-race | sito non trovato | solo `note_interne` | 3 | 0 | n.d. |
| 2026-12-08-imola-gran-premio-indoor | sito non trovato | solo `note_interne` | 3 | 0 | n.d. |
| 2027-04-04-berlino-generali-berlin-half-marathon-inlineskating | sito trovato, pagina dell'edizione giusta, nessuna novità | solo `note_interne` | 0 (pagina già nota) | 1 | n.d. |
| 2027-06-06-terni-memorial-alfonso-zenga | sito non trovato | solo `note_interne` | 3 | 0 | n.d. |
| 2027-07-03-fabriano-trofeo-dellamicizia-memorial-donatella | sito non trovato | solo `note_interne` | 3 | 0 | n.d. |
| 2027-07-31-berlino-adidas-runners-city-night-inlineskating | sito trovato, pagina dell'edizione precedente (condizioni 2026) | solo `note_interne` | 0 (pagina già nota) | 1 (+1 indirizzo costruito a mano, 404: errore di procedura, vedi sotto) | n.d. |
| 2027-09-25-pollenza-memorial-gilda-leoperdi-trofeo | sito non trovato | solo `note_interne` | 3 | 0 | n.d. |

Totali: 7 voci, 15 ricerche, 2 pagine lette (3 aperte), 0 campi pubblici cambiati, 0 promozioni, 0 esclusioni, 5 siti non trovati, 0 siti compromessi o non raggiungibili.

Minuti: non misurabili in modo affidabile da dentro la sessione (l'orologio della shell segnava 12:27→12:29 per tutto il giro, la sessione web non espone l'ora reale). Per le esecuzioni pianificate la durata si legge dai timestamp di inizio e fine dell'esecuzione nella pagina dell'attività.

## Cosa si è visto

- Per i cinque club italiani (CPGA L'Aquila, Gruppo Imolese Pattinaggio, Euro Sport Club Terni, Fortitudo Fabriano, Polisportiva Juvenilia Pollenza) le tre formulazioni della regola 10 hanno restituito solo giornali locali (giulianovanews, umbriaon, terninrete, il Resto del Carlino, quotidiano.net) e rumore (Imolese Calcio, GP di Formula 1, pattinaggio su ghiaccio). Nessun sito proprio è emerso: o non esiste (molte società usano solo i social, materia della Fase 4) o il motore non lo indicizza. Il limite di 3 ricerche è stato raggiunto 5 volte su 5: è il caso che costa di più e rende di meno.
- I giornali danno indizi utili ma non usabili come fonte (nome esteso della società, impianto abituale, circuito di appartenenza, un Campionato CSEN accanto agli Internazionali dell'Aquila): sono finiti in `note_interne` come "da confermare su una fonte ufficiale".
- Le due voci SCC Events avevano già la pagina dell'organizzatore in `url_ufficiale`: zero ricerche, una pagina ciascuna. Half Marathon: periodo di iscrizione 02/04/2026–11/03/2027 e quote 66–73 € invariati. City Night: la pagina mostra ancora "Participation fee 2026" e ammissione "from YOB 2014": resta `annunciato`.
- Errore di procedura da non ripetere: per la City Night ho costruito a mano l'indirizzo tedesco `/anmelden/10k-inline-skating` (404). Il prompt già vieta di aprire pagine non comparse nei risultati o nelle pagine lette; va detto esplicitamente che gli indirizzi non si indovinano.
- Nel prompt la traccia è descritta come "riga" di `note_interne`, ma `note_interne` è una stringa YAML su una riga sola: la traccia è una frase in coda, e le ricerche vanno tra apici singoli perché la stringa è tra doppi apici.

## Dubbi per il proprietario

- Nessuna modifica ai campi pubblici: niente da approvare nei dati, solo le tracce in `note_interne`.
- Per le gare dei piccoli club FISR la regola 10 via motore di ricerca non trova nulla: vale la pena spendere 3 ricerche per voce ogni settimana, o conviene segnarle "sito non trovato" e riprovare solo quando la Fase 4 porterà i social?

## Non fatto

- Voci passate: nessuna lavorata (2 `da_verificare` passate restano com'erano, per decisione del 2026-11-06).
- Caso di prova 5 (Pamplona 07/06/2026): evento passato e caso di scoperta (livello 6), fuori dall'arricchimento.

## Collaudo cieco dei casi di prova 1 e 2

Un sottoagente nuovo, senza contesto, con solo `CLAUDE.md` e il Passo 3 del prompt, ha ricevuto i punti di partenza dei casi 1 (Vado Ligure, 3-6/09/2026) e 2 (Pordenone, 24/05/2026) come righe di fisr.info (nome, date, città, organizzatore ignoto), con l'istruzione di ignorare il limite sugli eventi passati. Non ha potuto leggere `eventi.yaml`, il diario né i casi di prova, dove le risposte stanno scritte.

| Caso | Atteso | Ottenuto | Ricerche | Pagine | Durata |
|---|---|---|---|---|---|
| 1 Vado Ligure | organizzatore "A.S.D. Roller Sports Vado Ligure", impianto "Stadio Chittolina", sito vadosustrada2026.it riconosciuto compromesso | **fallito**: sito non trovato; `confermato` `[master]` dal solo titolo; organizzatore, impianto, link vuoti | 3 | 0 | 53 s |
| 2 Pordenone | `[master, amatori]` con prova dalla pagina di skatingclubcomina.eu (gara Fitness 21 km), organizzatore "Skating Club Comina A.S.D." | **fallito**: sito non trovato; `confermato` `[master]` dal solo titolo; niente Fitness | 3 | 0 | 66 s |

Durata totale della sessione del sottoagente: 5 min 18 s (lettura delle istruzioni compresa); il rapporto integrale è nel commento alla PR #33. In entrambi i casi l'unico risultato ricorrente era un articolo di giornale (ivg.it per Vado) che il prompt non permette di aprire: il sottoagente l'ha segnalato come dubbio, correttamente. Controprova fatta a mano con le query esatte dei casi di prova ("Vado Ligure campionato italiano strada 2026", "campionato italiano maratona Pordenone 2026"): nemmeno queste fanno uscire i due siti oggi; il primo risultato per Vado (ivg.it) nomina però nell'estratto l'organizzatore "Roller Sports Vado Ligure" e lo stadio Chittolina.

Le 11 osservazioni del sottoagente sul prompt, in sintesi: ricerca (a) non formulabile con organizzatore vuoto; i titoli federali generici vanno cercati con città e sport; i giornali "suggeriscono il dominio" ma non si possono aprire; il motore di ricerca è il collo di bottiglia; il regolamento di gara FISR non è tra le pagine apribili; formato della traccia senza pagine; le voci con prova ma senza link non vengono mai ricontrollate; `distanze` leggibili dal titolo ("Maratona"); `verificato_il` quando la prova è il titolo; `luogo` senza provincia; la regola "cat. …/M" non è nel prompt. Le osservazioni 1, 2, 6 e 11 sono già corrette nel prompt (commit di questo collaudo); le altre sono decisioni per il proprietario.

## Conclusione del collaudo

Con la ricerca web disponibile nella sessione Claude, la regola 10 così com'è scritta trova 0 siti di organizzatori su 7 club italiani (5 voci future + 2 casi di prova in cieco): l'attività pianificata, se creata oggi, costerebbe 3 ricerche a voce e non produrrebbe quasi nulla. Funziona invece per gli organizzatori già noti (SCC Events: rilettura a costo zero). Prima di pianificare servono le decisioni elencate nel commento alla PR.
