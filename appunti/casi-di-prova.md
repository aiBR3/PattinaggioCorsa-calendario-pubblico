# Casi di prova per la scoperta e l'arricchimento

Scopo: eventi reali, verificati dal proprietario, che le liste federali non davano o davano a metà. Quando la scoperta (livello 6) e l'arricchimento (livello 2b) diventeranno automatici, dovranno trovare questi casi da soli, partendo dalle sole informazioni nella colonna "Punto di partenza". Un caso si considera superato quando l'automatismo produce la voce indicata senza che una persona gli suggerisca il sito.

Ogni caso: cosa mancava, perché era sfuggito, qual era la strada per trovarlo, cosa deve uscire.

| # | Evento | Punto di partenza | Cosa mancava | Perché era sfuggito | Strada per trovarlo | Risultato atteso | Stato |
|---|---|---|---|---|---|---|---|
| 1 | Campionato Italiano su Strada cat. A/J/S/M, Vado Ligure, 3-6/09/2026 | riga di fisr.info (nome, date, "Vado Ligure") | sito dell'organizzatore, impianto, organizzatore locale | fisr.info non linka i siti degli organizzatori; la Fase 1 ha letto solo fisr.info | ricerca web "Vado Ligure campionato italiano strada 2026" → vadosustrada2026.it | organizzatore "A.S.D. Roller Sports Vado Ligure", impianto "Stadio Chittolina"; **sito riconosciuto come compromesso e non linkato** (pagine interne di spam) | fatto a mano 2026-11-06 |
| 2 | Campionato Italiano Maratona cat. J/S/M + Mezza Maratona Allievi, Pordenone, 24/05/2026 | riga di fisr.info | link ufficiale, distanze, orario, quota, **gara Fitness da 21 km** | la categoria Fitness non sta nel titolo FISR né in un regolamento di gara: solo sul sito del club | ricerca web "campionato italiano maratona Pordenone 2026" → skatingclubcomina.eu; la pagina giusta ha "2025" nell'indirizzo, quella con "2026" è vuota | `categorie: [master, amatori]`, prova dalla pagina del club, organizzatore "Skating Club Comina A.S.D." | fatto a mano 2026-11-06 |
| 3 | BMW Berlin-Marathon Inlineskating, Berlino, 26/09/2026 | niente: assente da fisr.info (paese DE) | tutto l'evento | nessuna fonte estera era attiva | fonte scc-events.com (calendario con disciplina "Inline skating") oppure world-inline-cup.com; pagina ufficiale già sparita → Wayback Machine | voce `confermato` `[master, amatori]`, prova dalla frase di ammissione per anno di nascita; nota interna sull'edizione 2027 senza inline | fatto a mano 2026-11-06 |
| 4 | World Skate Marathon Tour 2026, Naples Challenger Stage (42 km Pro/Master + 20 km Amatori), Napoli, 31/10/2026 | niente: assente da fisr.info nonostante sia in Italia | tutto l'evento | la gara è sotto World Skate, non nel calendario FISR; l'organizzatore è un'associazione locale (ASD SEBS Fiera dello Sport) | fonte worldskate.org (eventi "Marathon Tour") → bollettino PDF → sito dell'organizzatore rollerskatingfestivalnapoli.it, che ha anche la pagina amatori | una voce sola `confermato` `[master, amatori]`, prova dal bollettino World Skate e dalla pagina amatori | fatto a mano 2026-11-06 |
| 5 | World Skate Marathon Tour 2026, Pamplona Challenger Stage, 07/06/2026 (ES) | la lista eventi di worldskate.org | tutto l'evento | come il caso 4 | bollettino World Skate → sito dell'organizzatore | da leggere: probabilmente `[master, amatori]` come Napoli | **aperto** |

## Come usare questo file

- Quando un livello automatico viene messo in funzione, lo si lancia sui soli punti di partenza di questa tabella e si confronta ciò che produce con il risultato atteso; l'esito va in `registro/` e, se diverso dall'atteso, in `appunti/diario.md`.
- Ogni evento che il proprietario segnala come mancante o incompleto diventa una riga qui, prima ancora di correggere `eventi.yaml`.
