# Script, raccolta e pagina: come funzionano

Questo file si legge prima di toccare uno script, un workflow o la pagina, e prima di eseguire a mano raccolta o conversione. Le regole che valgono sempre e lo schema di `dati/eventi.yaml` stanno in `CLAUDE.md`. Il testo qui sotto è stato spostato da `CLAUDE.md` il 2026-11-22 senza cambiare le parole (decisione "Avvio leggero").

## Gli script

```
script/raccogli_fisr.py    ← livello 1: lista + regolamenti di gara di fisr.info → JSON grezzo (non decide)
script/converti_fisr.py    ← livelli 2-3: JSON grezzo → voci di eventi.yaml, con prova citata dall'art. 10
script/prove_converti_fisr.py ← prove automatiche di converti_fisr.py su casi costruiti (le esegue anche verifica.yml)
script/converti_pattinate.py ← calendario pubblico di Pattiniamo l'Italia (file ICS) → voci `tipo: pattinata` di eventi.yaml; non copia nomi di persone né descrizioni
script/prove_converti_pattinate.py ← prove automatiche di converti_pattinate.py su calendari costruiti (le esegue anche verifica.yml)
script/raccogli_segnalazioni.py ← modulo pubblico delle segnalazioni (API di Tally) → candidati ripuliti di dati/segnalazioni.yaml; è il filtro tra il testo del pubblico e il repository
script/prove_raccogli_segnalazioni.py ← prove automatiche di raccogli_segnalazioni.py su risposte costruite (le esegue anche verifica.yml)
script/genera_ics.py       ← eventi.yaml → calendario.ics + index.html (valida ingresso e uscita)
script/prove_genera_ics.py ← prove automatiche dei link scritti da genera_ics.py, su voci costruite (le esegue anche verifica.yml)
script/intervallo_scansione.py ← quali regolamenti leggere questa settimana: l'intervallo attorno all'ultimo che esiste e quelli delle gare future, da rileggere
script/prove_intervallo_scansione.py ← prove automatiche di intervallo_scansione.py su dati costruiti (le esegue anche verifica.yml)
script/raccogli_societa.py ← registro delle società dalle classifiche, dai risultati e dai regolamenti di fisr.info
script/requisiti.txt       ← dipendenze Python
```

## Come si lavora in locale

```
pip install -r script/requisiti.txt

# 1. Raccolta grezza da fisr.info (lista della stagione + regolamenti di gara; la scansione degli id trova anche i regolamenti di gara che la lista non linka più: gare passate e "non autorizzate")
python3 script/raccogli_fisr.py --anno 2026 --da 2026-01-01 --regolamenti --scansione-regolamenti 6300 7100 --uscita registro/AAAA-MM-GG-raccolta-fisr.json

# 2. Conversione in voci di eventi.yaml (prima senza --scrivi, per leggere il rapporto)
python3 script/converti_fisr.py --raccolta registro/AAAA-MM-GG-raccolta-fisr.json --rapporto registro/AAAA-MM-GG-conversione-fisr.md [--scrivi]

# 3. Revisione a mano delle voci nuove (nomi, luoghi, organizzatori), poi:
python3 script/genera_ics.py --ingresso dati/eventi.yaml --uscita uscita --url-base https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico

# Dopo ogni modifica a genera_ics.py: prove sui link di ogni evento (descrizione, proprietà URL, pagina)
python3 script/prove_genera_ics.py

# Dopo ogni modifica a converti_fisr.py: prove su casi costruiti (riconoscimento, regolamento cambiato, doppioni)
python3 script/prove_converti_fisr.py

# Pattinate: dal calendario pubblico di Pattiniamo l'Italia alle voci tipo: pattinata (prima senza --scrivi, per leggere il rapporto)
python3 script/converti_pattinate.py --rapporto registro/AAAA-MM-GG-pattinate.md [--scrivi]

# Dopo ogni modifica a converti_pattinate.py: prove su calendari costruiti (titoli, date, annullamenti, voci escluse)
python3 script/prove_converti_pattinate.py

# Settimanalmente (è ciò che fa raccolta.yml) si leggono l'intervallo attorno all'ultimo regolamento che esiste e, uno per uno, i regolamenti delle gare future già in eventi.yaml (per accorgersi quando cambiano):
python3 script/intervallo_scansione.py                  # stampa "DA A", es. 7052 7401
python3 script/intervallo_scansione.py --da-rileggere   # stampa gli id per raccogli_fisr.py --rileggi-regolamenti

# A ogni stagione (o quando servono società nuove): registro delle società dalle classifiche federali, dai risultati ("Organizzato da") e dai regolamenti (siti citati); i campi a mano restano
python3 script/raccogli_societa.py --anno 2026 --registro dati/societa.yaml --raccolta registro/AAAA-MM-GG-raccolta-fisr.json --rapporto registro/AAAA-MM-GG-societa.md
```

Il workflow `raccolta.yml` esegue questi stessi passi ogni lunedì (05:17 UTC) con `--da` = 14 giorni prima, l'intervallo di `intervallo_scansione.py` (gli ultimi 50 numeri fino all'ultimo regolamento che esiste davvero e i 300 successivi) e la rilettura, uno per uno, dei regolamenti delle gare da quella data in poi già in `eventi.yaml` (`--rileggi-regolamenti`: senza, un regolamento cambiato non verrebbe visto); poi esegue `converti_pattinate.py` sul calendario di Pattiniamo l'Italia (se quella lettura fallisce le pattinate non vengono toccate e la raccolta delle gare prosegue, con l'errore nel riassunto del job) e aggiunge a `dati/segnalazioni.yaml` i candidati che un job a parte ha letto dal modulo pubblico delle segnalazioni (è l'unico job che conosce la chiave di Tally, che sta nel segreto dell'environment `segnalazioni`, consegnato solo al ramo `main`); se `eventi.yaml` o `segnalazioni.yaml` cambiano apre una PR dal ramo `raccolta/AAAA-MM-GG`, una sola alla volta (se la precedente è ancora aperta non ne apre un'altra). Quella PR è aperta dal bot di Actions: finché tocca solo `dati/eventi.yaml`, `dati/societa.yaml`, `dati/segnalazioni.yaml` e `registro/`, che in `CODEOWNERS` non hanno un responsabile, il proprietario la fonde senza doverla prima approvare (decisione 2026-11-17, vedi `appunti/decisioni.md`); se tocca altro, per esempio una voce nuova in `appunti/diario.md`, deve prima approvarla ("Approve"). Da "Actions → Run workflow" si può lanciare a mano, anche con un intervallo di id esplicito per una scansione completa. Su una PR aperta con il token di Actions `verifica.yml` non parte da sola: GitHub crea l'esecuzione ma la tiene ferma finché chi ha accesso in scrittura non preme "Approve workflows to run"; per questo il workflow esegue da sé `genera_ics.py` prima di aprirla. I push successivi sullo stesso ramo fatti con le credenziali del proprietario (l'arricchimento del martedì) fanno partire `verifica.yml` normalmente.

Cosa decide `converti_fisr.py` e cosa no:
- regolamento di gara con righe `MASTER …` nell'art. 10 → `confermato`, `categorie: [master]`, prova = le righe citate;
- regolamento di gara senza righe Master/Amatori → `escluso`, prova = l'elenco delle categorie;
- nessun regolamento di gara ma titolo ufficiale con `cat. …/M` (campionati FISR) → `confermato` con prova = il titolo; con `cat.` senza M → `escluso`;
- tutto il resto → `da_verificare`, categorie vuote;
- **promozione** (regola 7): una voce già presente ma senza prova (`da_verificare`, `non_autorizzato`, `annunciato`) che ora ha il regolamento di gara riceve categorie, prova, stato, `verificato_il`, la fonte nuova e i campi vuoti (link, distanze, scadenza); una voce `non_autorizzato` con prova che la lista non segna più come "non ancora autorizzata" passa a `confermato`/`escluso`. Nome, luogo, organizzatore, note e tutto ciò che una persona ha scritto restano com'erano;
- **riconoscimento** (regola 7): una voce già presente è la stessa gara se cita lo stesso regolamento di gara (`id_manif` in `url_ufficiale` o nelle `fonti`), poi se ha lo stesso `id`, poi se ha la stessa `data_inizio` con nome simile o stessa città;
- **regolamento cambiato** (regola 7): una voce legata a un regolamento di gara lo segue quando cambia: date, scadenza delle iscrizioni e, se la prova è la frase scritta dallo script, categorie, prova e stato (una gara `escluso` può così entrare nel calendario, e viceversa); se cambia `data_inizio` la data nell'`id` la segue; ogni cambio è scritto in `note_interne` e nel rapporto, prima → dopo. Una prova scritta a mano non viene mai riscritta: la differenza va in `note_interne` e nel rapporto come "da controllare". Limite (2026-11-24): lo script confronta l'insieme delle categorie, non le righe citate: se il programma cambia senza cambiare le categorie, la prova (anche quella scritta dallo script) e le `distanze` restano com'erano; quando lo stesso cambio porta anche una data o una scadenza nuova, la citazione la riallinea l'arricchimento (`agenti/arricchimento.md`, passo 2, "Regolamento cambiato");
- **nome** (decisione 2026-11-16): `nome_fonte` ricorda il titolo della lista federale all'ultima lettura. Se le parole del titolo cambiano (maiuscole, accenti, spazi e punteggiatura non contano), `nome` diventa il titolo nuovo ripulito dallo script, `nome_fonte` si aggiorna e il nome vecchio resta scritto in `note_interne` e nel rapporto; l'`id` non cambia. Finché il titolo non cambia, il nome ritoccato a mano resta. Non vale quando a una voce corrispondono più righe della lista (più gare nello stesso giorno) né per le proposte nate dal solo regolamento;
- **regolamento senza riga nella lista**: non diventa una voce (la località viene dalla lista e l'`id` la contiene); resta nel rapporto, "in attesa della lista", finché la lista non lo riporta;
- **possibile doppione**: una voce nuova senza regolamento, con stessa città e nome simile a una voce sparita dalla lista, viene creata con il sospetto scritto in `note_interne` e nel rapporto; unire due voci tocca a chi rivede la PR;
- **note interne**: le frasi che lo script scrive in `note_interne` ("Promossa il …", "Aggiornata il …", "Nome aggiornato il …", "Da controllare …") vanno prima della traccia `Arricchimento AAAA-MM-GG: …` lasciata dall'arricchimento, che resta sempre l'ultima frase: l'agente la legge e la sostituisce a ogni ricontrollo. Se alla fine la traccia di una voce risulta cambiata o spostata, lo script si ferma senza scrivere `eventi.yaml`.

Per il resto le voci già presenti in `eventi.yaml` non vengono modificate dallo script: una voce che ha già la prova cambia solo se cambia il regolamento di gara che la prova, e sempre dentro una PR; luogo, organizzatore e note non cambiano mai da soli, il nome solo quando la lista federale cambia il titolo. `python3 script/prove_converti_fisr.py` prova queste regole su casi costruiti. Le voci `tipo: pattinata` non sono gare FISR: `converti_fisr.py` non le considera mai quando cerca la voce di una gara, nemmeno nello stesso giorno e nella stessa città.

Cosa fa `converti_pattinate.py` e cosa no (decisioni del 2026-11-22):
- **fonte**: il calendario pubblico di Pattiniamo l'Italia (Google Calendar, file ICS), che di ogni pattinata dà solo le date e un titolo nella forma "PPUG - luogo o nome - gruppo che organizza"; si leggono gli eventi con inizio da oggi in poi;
- **riconoscimento** (regola 7): una voce è la stessa pattinata se nelle `fonti` cita lo stesso identificativo dell'evento (`…/basic.ics#UID`); se l'identificativo non c'è più ma una pattinata con la stessa `data_inizio` e lo stesso titolo sì, l'evento è stato ricreato nella fonte e la voce prende l'identificativo nuovo;
- **voce nuova**: date, `nome` e `nome_fonte` dal titolo, `stato: da_verificare`, `luogo: "da indicare"`, `paese: IT`, link alla pagina degli eventi del movimento. Chi la rivede (l'agente del martedì o il proprietario) legge il titolo nella fonte, compila luogo, paese e organizzatore e la porta ad `annunciato`, oppure a `escluso` se è fuori perimetro o non è una pattinata;
- **regola 9**: l'ultima parte del titolo (il gruppo e spesso le persone che organizzano) non viene mai copiata, le descrizioni non vengono lette, e nessun titolo grezzo finisce in un file. Se il titolo ha una parte sola lo script la tiene e lo segnala nel rapporto: va riletta da una persona;
- **date e titolo cambiati**: la voce segue la fonte (se cambia `data_inizio` la data nell'`id` la segue; se cambiano le parole del titolo, `nome` diventa il titolo nuovo e quello vecchio resta in `note_interne`, con l'avviso di ricontrollare luogo e organizzatore);
- **annullamento**: un titolo che dice "ANNULLATA" porta la voce ad `annullato`; se poi la parola sparisce, lo script lo segnala e non cambia lo stato;
- **evento sparito dalla fonte**: la voce resta com'è; lo script lo scrive una volta in `note_interne` ("Da controllare …") e nel rapporto. Se in una sola lettura sparisce più della metà delle voci seguite, lo script si ferma senza scrivere: è più probabile una lettura sbagliata;
- **mai**: toccare una voce `escluso` (è la memoria di ciò che è stato scartato), una voce che non è una pattinata, oppure luogo, paese, organizzatore, note e link scritti da una persona; cambiare la data di lettura di una voce che non è cambiata (altrimenti ogni settimana ci sarebbe una PR senza novità). Le sue frasi in `note_interne` vanno prima della traccia `Arricchimento …`, come quelle di `converti_fisr.py`.

`python3 script/prove_converti_pattinate.py` prova queste regole su calendari costruiti.

## La pagina pubblicata

`calendario.ics` e `index.html` non sono mai committati: li genera il workflow a ogni merge su `main` e li pubblica su GitHub Pages insieme ai file di `pagina_web/`. Tutto il testo della pagina sta in `pagina_web/modello_index.html`, l'aspetto in `pagina_web/stile.css` (una PR come le altre); lo script fornisce solo i segnaposto che dipendono dai dati (`{{righe_tabella}}`, l'unico obbligatorio; `{{numero_eventi}}`, `{{url_webcal}}`, `{{url_ics}}`, `{{generato_il}}`, `{{titolo}}`, `{{descrizione}}`). Nella tabella gli eventi sono in ordine cronologico inverso: il più recente in alto.

## Cosa vede chi consulta il calendario

Per ogni evento: titolo (con eventuale prefisso di stato), date, luogo, e una descrizione breve, una riga per voce con l'etichetta tra parentesi quadre (mai seguita dai due punti, che gli organizzatori usano nei loro testi), in quest'ordine: `[Categorie ammesse]` (o "Non ancora pubblicate" per `annunciato`, "Da verificare" negli altri casi senza categorie, "Pattinata non competitiva" per le pattinate), `[Distanze]`, `[Organizzatore]`, `[Scadenza iscrizioni]`, le `note` in `[Informazioni]` e per ultimi **i link**, ciascuno solo se c'è: `[URL]`, la pagina dell'organizzatore (`url_ufficiale`, altrimenti `url_iscrizione`, quando non è un regolamento di gara), poi `[Regolamento FISR]`, il regolamento di gara su fisr.info (preso da `url_ufficiale` o dalle `fonti`). L'etichetta dice sempre che cos'è il link: una voce che ha solo il regolamento mostra solo `[Regolamento FISR]` (decisione 2026-11-17). Nella proprietà `URL` dell'evento (Calendario di Apple la mostra, Google la ignora) e sul nome nella tabella della pagina va **un solo link**, quello principale: `url_ufficiale`, altrimenti `url_iscrizione`. `nome_fonte`, `prova`, `fonti`, `stato`, `verificato_il` e `note_interne` sono dati di lavoro: restano nell'YAML e non vanno nella descrizione, tranne l'indirizzo del regolamento di gara, che il generatore prende dalle `fonti`. Le `note` sono visibili a tutti: scriverle per chi pattina (impianto, orari, quote, come ci si iscrive); tutto il resto (dubbi, doppioni, anomalie di lettura, cosa ricontrollare) va in `note_interne`.
