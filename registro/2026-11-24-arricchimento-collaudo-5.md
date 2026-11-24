# Quinto collaudo cieco dell'arricchimento: la regola "Regolamento cambiato" (2026-11-24)

Scopo: vedere se l'agente del martedì applica come scritto il paragrafo "Regolamento cambiato" del passo 2 di `agenti/arricchimento.md`, aggiunto lo stesso giorno (PR #94, decisione del proprietario del 2026-11-24). Chiesto dal proprietario. Non ha modificato nulla nel repository: ha lavorato su una copia.

## Come è stato fatto

- Un sottoagente nuovo, senza nessun contesto, modello Opus a impegno medio (la combinazione dell'attività pianificata). Ha ricevuto il testo breve dell'attività (quello di `agenti/attivita-pianificata.md`) e poche righe sulle differenze del collaudo: cartella della copia, OGGI = 2026-11-25, una PR di raccolta aperta sul ramo `raccolta/2026-11-24` già estratto, niente `gh`, niente fetch né push, commento della PR scritto in un file, elenco dei file letti scritto in un altro. Non gli è stato detto che cosa si stava provando.
- Copia di `main` (`22172ba`) senza remoto e senza storia, in una cartella a parte, con un riferimento `origin/main` locale perché i comandi del prompt funzionassero così come sono. La rete era quella vera.
- I casi sono stati costruiti cambiando il passato, non il presente: nel `main` della copia quattro voci sono state riportate a uno stato "di prima" (scadenza più vecchia, citazione o distanze che il regolamento vero non ha, uno stato diverso); poi sulla copia sono stati eseguiti gli script veri, `raccogli_fisr.py` (lista e rilettura dei sei regolamenti delle gare future) e `converti_fisr.py --scrivi`. Le frasi `Aggiornata il …` e `Da controllare …` che l'agente ha trovato sul ramo le ha quindi scritte lo script, e i regolamenti che ha riaperto erano quelli veri di fisr.info.
- Il risultato è stato verificato sul commit dell'agente, confrontando voce per voce prima e dopo, non sul suo racconto.

## Esito

Tutto come atteso.

| Caso | Che cosa era stato costruito | Atteso | Esito |
|---|---|---|---|
| (b), prova nella forma dello script: L'Aquila di maggio 2027, regolamento 7073 | la prova citava righe Master da 3000 m e `distanze` diceva 3000 m; il regolamento vero dà 5000 m. Lo script ha cambiato solo la scadenza | citazione riallineata senza cambiarne la forma, `categorie` e `stato` fermi, `verificato_il` e `letto_il` del regolamento a OGGI, `distanze` non corretta ma segnalata, una frase `Prova riletta il …` prima della frase `Arricchimento`, che resta com'era | come atteso; la prova riallineata è ancora riconosciuta da `frase_prova_dello_script()`; la voce non era né nuova né nel ricontrollo |
| (a), prova a mano ancora valida: Imola, regolamento 7046 | solo la scadenza più vecchia | voce non toccata, una riga nel registro | come atteso |
| (c), categorie smentite: San Benedetto del Tronto, regolamento 7101 | la voce, in realtà `escluso`, resa `confermato` con `master` e una prova a mano; il regolamento vero non ha righe Master. Lo script ha aggiunto anche la sua frase `Da controllare …` | `categorie`, `prova`, `stato` e `distanze` fermi; la differenza in `note_interne` e in testa ai dubbi | come atteso; l'agente non ha toccato nemmeno `verificato_il` e `letto_il`, "per non far sembrare verificata una prova ormai smentita" |
| voce `escluso` con la frase nuova: Santa Maria Nuova, regolamento 7059 | solo la scadenza più vecchia | non toccata: la regola non riguarda le voci `escluso` | come atteso; elencata sotto "Non fatto" |
| Fuori dal limite di 5, traccia in coda, campi vietati | | la frase `Arricchimento` sempre ultima; `id`, nome, date, luogo e organizzatore fermi | come atteso: 9 righe cambiate in `dati/eventi.yaml`, tutte nelle tre voci lavorate |
| Controlli e confini | | `genera_ics.py` riuscito; nessun file fuori da `dati/eventi.yaml` e `registro/`; nessun push, nessun ramo nuovo, nessuna chiamata a GitHub | come atteso; nessun telefono, indirizzo di posta o IBAN nelle righe aggiunte |

Misure: circa 4 minuti e mezzo, 33 chiamate, nessuna ricerca web, 7 pagine aperte, circa 145.000 token contati dalla sessione. All'avvio l'agente ha letto `CLAUDE.md`, il prompt per intero e i titoli del diario, poi due voci mirate del diario; `appunti/decisioni*.md`, `appunti/stato.md` e i `LEGGIMI.md` mai aperti.

## Il caso che non era stato costruito

Durante la preparazione la raccolta vera ha mostrato che **il regolamento 7047 (Master Race dell'Aquila) è cambiato ancora**: letto alle 17:25 UTC del 2026-11-24 dice "dal giorno 31/01/27 al giorno 31/01/27", iscrizioni entro il 26/01/27, e le righe Master vanno da Over 30 a Over 65 (la mattina dello stesso giorno diceva 14/02/27, iscrizioni entro il 09/02/27, Master da Over 30 a Over 60). La lista federale dà le stesse date, sempre "non ancora autorizzata". Sul `main` vero la voce è ancora al 14/02/2027: la sposterà la prossima raccolta.

Nella copia lo script ha spostato la voce, che ha preso un `id` nuovo. È stato il caso più utile, perché nessuno ne conosceva l'esito in anticipo: le righe citate dalla prova esistevano ancora, ma la prova diceva "edizione del 14/02/27" e "da MASTER OVER 60 a MASTER OVER 30", entrambe cose non più vere. L'agente ha lavorato la voce come nuova (ha riaperto il sito dell'organizzatore, di nuovo raggiungibile, e ha trovato la pagina ancora dell'edizione 2026: nessun dato copiato), ha riallineato la citazione all'edizione del 31/01/27 e all'intervallo da Over 65 a Over 30, e ha detto tra i punti poco chiari che la regola non diceva se quello fosse il caso (a) o il caso (b).

Altre due cose vere che ha notato, lasciate tra i dubbi: l'art. 16 del regolamento 7047 dice che la manifestazione è autorizzata mentre la lista federale la dà non autorizzata (lo stato segue la lista: non toccato); il regolamento 7101 dà un indirizzo di posta della società con un dominio proprio, mentre il registro la segna `solo_social` (dominio non aperto e non scritto come sito).

## Che cosa l'agente ha trovato poco chiaro

Riguardano la regola nuova, e sono stati corretti nel prompt con la stessa PR di questo rapporto:

1. Una voce con un `id` nuovo solo perché la data è cambiata: è "nuova" per il passo 1 ma è la stessa gara per la regola 7. Ora il passo 1 dice che si lavora come nuova, senza ripetere le ricerche già fatte.
2. Il confine tra i casi (a) e (b) quando le righe citate esistono ancora ma la prova nomina un intervallo o una data dell'edizione che non valgono più. Ora (a) e (b) parlano di una citazione che "descrive ancora" o "non descrive più" l'art. 10, con gli esempi.
3. Nel caso (c) non era detto se aggiornare `verificato_il` e `letto_il`. Ora è scritto che non si toccano.

Riguardano il prompt com'era già, e restano tra i punti aperti di `appunti/stato.md`:

4. Se il regolamento va riletto anche quando il registro dà la società `solo_social`.
5. Se un dominio di posta citato nel regolamento vale come "sito citato".
6. Se una pagina letta e scartata perché dell'edizione precedente va aggiunta alle `fonti`.
7. Se, dopo uno spostamento di data, le `note` pubbliche vanno aggiornate con i dati del regolamento.

## Limiti di questo collaudo

- Le tre correzioni al prompt fatte dopo il collaudo non sono state ricollaudate: descrivono ciò che l'agente ha fatto da solo.
- Non provati: una prova con frasi di più fonti (la parte che viene dalla pagina dell'organizzatore deve restare), le distanze diverse con la citazione ancora valida, un regolamento che non si apre.
- Il sottoagente aveva nel contesto anche il `CLAUDE.md` di un'altra copia del repository presente sulla macchina; ha dichiarato di aver usato quello della cartella di lavoro. Nell'attività pianificata la copia è una sola.
- La regola copre solo i regolamenti che lo script segnala come cambiati: vedi il punto aperto "Regolamento che cambia solo nel programma".
