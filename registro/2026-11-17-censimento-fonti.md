# Censimento delle fonti (Fase 4) — 2026-11-17

Primo passo della Fase 4, chiesto dal proprietario: capire dove stanno le gare e le pattinate che oggi il calendario non vede. Eseguito a mano in una sessione di lavoro. Produce solo proposte per `dati/fonti.yaml`: la raccolta settimanale, `dati/eventi.yaml` e gli script non cambiano.

## Metodo

- Ogni fonte è stata aperta dalla shell (`curl`) e letta; per trovare gli indirizzi che il registro non aveva sono servite 12 ricerche web. In tutto 95 pagine o documenti aperti.
- Nel registro una fonte dice "Letta il 2026-11-17" solo se il contenuto è stato letto e riassunto; dice "Aperta ma non letta davvero" quando è stato solo verificato che la pagina esiste (quattro federazioni estere).
- Gli indirizzi scritti nel registro sono stati tutti aperti. Due file ICS vengono da uno schema pubblico e documentato del servizio che ospita il calendario (Google Calendar, Teamup) applicato all'identificativo trovato nella pagina: entrambi rispondono come `text/calendar`.
- Limite: "raggiungibile" vuol dire dalla shell di questa sessione. I runner di GitHub e l'ambiente dell'attività pianificata hanno un'altra rete: ogni fonte va riprovata da lì prima di affidarla a uno script.

## Risultato in breve

Il registro passa da 19 a 30 fonti: 8 attive (come prima), 18 `da_verificare`, 4 `scartata`. Dopo la decisione del proprietario sui campionati regionali (in fondo) le `da_verificare` sono 14 e le `scartata` 8.

| Fonte | Che cosa offre | Proposta |
|---|---|---|
| `fisr-it-comunicati` | Per ogni campionato: società organizzatrice, impianto, scadenze, gare per categoria (Master compresi), sito dell'organizzatore; indice per anno con titoli e PDF | **Prima da attivare** |
| `pattiniamolitalia-eventi` | File ICS pubblico con 40 pattinate non competitive future (fino al 05/12/2027) | **Seconda da attivare**, dopo aver deciso come entrano le pattinate |
| `fisr-fvg-corsa`, `fisr-toscana-corsa`, `fisr-veneto-corsa`, `fisr-comitati-regionali` | Campionati regionali e provinciali, alcuni con i Master, assenti dalla lista nazionale | Scartate: il proprietario ha deciso che questi campionati non entrano nel calendario |
| `world-inline-cup`, `german-inline-cup`, `worldskate-europe-calendario` | Indici delle maratone europee e del campionato europeo Master di maratona; ogni scheda porta al sito dell'organizzatore | Lettura mensile di un agente da dicembre: i calendari 2027 non sono ancora usciti |
| `ffrs-calendario`, `rfep-velocidad`, `fpp-velocidade`, `rollsport-austria`, `driv-speedskating`, `skateresults` | Calendari delle federazioni di Francia, Spagna, Portogallo, Austria, Germania e una piattaforma tedesca | Una alla volta, più avanti; quattro sono state solo aperte |
| `aics-pattinaggio-corsa` | Circuito a tappe nel Bresciano; gli "Amatori" fanno un giro non competitivo | Bassa priorità |
| `scc-events-calendario` (già attiva) | Il file `.ics` c'è ma non dice la disciplina | Resta la pagina HTML; il file serve solo come controllo delle date |
| `fisr-it-calendario-eventi`, `rollergames-calendario-corsa`, `uisp-pattinaggio-corsa`, `swiss-skate-tour` | Niente di utile oggi | Scartate, con il motivo nel registro |

## Che cosa è emerso

1. **I comunicati FISR chiudono il buco dei campionati.** Per un campionato futuro la lista federale dice solo "FISR" e il registro delle società conosce l'organizzatore solo dopo la gara. Il comunicato lo dice prima: il CU 37 del 2026 (Campionato Italiano su strada) riporta società organizzatrice, impianto, scadenze, gare dei Master e sito dell'organizzatore. L'indice dell'anno è una pagina semplice, con un link per comunicato: uno script può segnalare i comunicati nuovi e l'arricchimento può aprire il PDF.
2. **I campionati regionali e provinciali ammettono i Master e non stanno su fisr.info.** Visto in Friuli Venezia Giulia ("Campionato Regionale Pista R12/R/A/J/S/M", "Campionato Regionale Strada R12/R/A/J/S/M") e in Toscana ("Campionato Provinciale Pista & Strada cat. R12RAJSM"). Ogni comitato pubblica a modo suo e solo 7 su 20 hanno il sito nell'elenco federale. È una scelta di perimetro prima che di fonti: sono gare per soli tesserati della regione.
3. **Le pattinate hanno un calendario pubblico.** Il Google Calendar di Pattiniamo l'Italia è pubblico e ha un file ICS: 242 eventi dal 2021, 40 futuri, in media tre al mese. Dà data, luogo e gruppo organizzatore nel titolo, quasi mai altro; alcune uscite sono all'estero, anche fuori perimetro.
4. **All'estero i calendari 2027 non sono ancora pubblicati**, tranne quello di SCC Events, già nel registro. La Swiss Skate Tour chiude ("2027 wird es keine Tour mehr geben"). Gli indici utili sono tre: World Inline Cup, German Inline Cup, calendario di World Skate Europe.
5. **Negli Enti di promozione c'è poco.** AICS ha un circuito a tappe, ma senza categoria Master e con gli Amatori in una prova non competitiva di un giro; il sito nazionale UISP ha le ultime pagine di corsa nel 2019-2020; per CSEN una ricerca web non ha trovato nessuna pagina del settore. Le gare Fitness per adulti restano sui siti degli organizzatori (regola 10) e nelle maratone estere.
6. **Il file `.ics` di SCC Events non basta**: 12 eventi con data e titolo, senza la disciplina. Non sostituisce la pagina HTML.

## Ordine proposto

1. `fisr-it-comunicati`: serve subito all'arricchimento per i campionati 2027.
2. `pattiniamolitalia-eventi`: una categoria intera, oggi assente dal calendario, con uno script semplice.
3. Campionati regionali, se il proprietario li vuole: prima `fisr-fvg-corsa` (pagina regolare), poi Toscana, poi gli altri comitati.
4. Indici esteri (`world-inline-cup`, `german-inline-cup`, `worldskate-europe-calendario`): lettura mensile di un agente da dicembre.
5. Federazioni estere, una alla volta, cominciando da quelle con un calendario leggibile da script.

## Decisioni che servono dal proprietario

- **Campionati regionali e provinciali**: entrano nel calendario? Tutti, o solo quelli di alcune regioni?
- **Pattinate**: con quale `stato` entrano (non hanno categorie da provare), che cosa vale come prova, che cosa fare delle uscite fuori perimetro e degli eventi con la sola data.
- **Stato delle fonti lette**: in questa proposta restano `da_verificare` con `ultimo_controllo` compilato, e l'intestazione di `fonti.yaml` spiega la differenza. L'alternativa è uno stato nuovo (per esempio `proposta`), che richiede di cambiare lo schema in `CLAUDE.md`.
- **Fonti scartate**: quattro, ciascuna con il motivo. Se una va tenuta, basta dirlo.
- **Quale fonte attivare per prima**: l'ordine qui sopra è una proposta.

## Decisioni del proprietario dopo il censimento (2026-11-17)

- **Campionati regionali e provinciali FISR: non entrano nel calendario.** Le quattro fonti che li riguardano (`fisr-fvg-corsa`, `fisr-toscana-corsa`, `fisr-veneto-corsa`, `fisr-comitati-regionali`) passano a `scartata`, con la decisione scritta in testa alla nota e ciò che è stato letto conservato come memoria. Nell'ordine proposto qui sopra il punto 3 cade.
- Le altre decisioni (pattinate, stato delle fonti lette, quale fonte attivare per prima) sono ancora aperte.

## Eventi visti durante il censimento

Non sono stati aggiunti a `dati/eventi.yaml`: nessuno ha ancora una prova letta sulla pagina dell'organizzatore.

- Rennes sur Roulettes 2027 (FR), 22-23/05/2027: dal titolo del sito dell'organizzatore, rennessurroulettes.com.
- Mittelland rollt (Wolfwil, CH), 20/06/2027: dalla notizia di chiusura della Swiss Skate Tour.
- arena geisingen international 2027 (DE), 15-18/04/2027, e summer cup, 10/07/2027: dall'elenco di Skate Results; gare su pista.
- 40 pattinate di Pattiniamo l'Italia tra il 06/12/2026 e il 05/12/2027.

## Non trovato o non raggiungibile

- CSEN, settore corsa: una ricerca web, nessuna pagina.
- Federazione svizzera e federazione slovena: non trovate (per la Slovenia una ricerca senza esito; l'indirizzo provato per la Svizzera porta a un sito estraneo).
- `ahotu.com` (aggregatore di gare, ha una sezione di pattinaggio in linea): risponde 403 con la sfida anti-bot; è comunque un aggregatore.
- Siti dei comitati FISR di Abruzzo e Puglia: nessuna risposta alla shell.
- `fisr.info` ha chiuso la connessione una volta; al secondo tentativo ha risposto (già noto dal diario).

## Misure

12 ricerche web, 95 pagine o documenti aperti, 3 PDF letti (comunicato FISR n. 37 del 2026, circolare AICS 2026, calendario 2026 di World Skate Europe), 3 file ICS letti (Pattiniamo l'Italia, SCC Events, FFRS).
