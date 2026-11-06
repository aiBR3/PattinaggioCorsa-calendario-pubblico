# CLAUDE.md — regole permanenti per chi lavora in questo repository

Questo file è la memoria permanente di agenti e script. Leggilo per intero prima di fare qualsiasi cosa. Poi leggi `appunti/diario.md` (cosa non ha funzionato, per non riprovarlo) e `appunti/decisioni.md` (perché le cose sono fatte così).

## Scopo

Un calendario pubblico (file ICS) con tutte le gare e gli eventi di pattinaggio corsa che ammettono le categorie **Master** (agonisti dai 30 anni in su, una sotto-categoria ogni 5 anni) e **Amatori/Fitness** (non agonisti; i due termini sono intercambiabili), comprese le pattinate non competitive (notturne, al mare, natalizie, per famiglie).

Perimetro geografico: Italia, Svizzera, Spagna, Portogallo, Francia, Austria, Germania, Slovenia.

Chi lo consulta: chi si iscrive al calendario, da iPhone (app Calendario) o da Android (Google Calendar). Il calendario è utile solo se è **affidabile**: meglio un evento in meno che una data sbagliata.

## Regole inviolabili

1. **Nessuno scrive su `main`.** Ogni modifica è una pull request; il merge lo fa solo il proprietario (aiBR3), a mano. Vale anche per chi agisce con le sue credenziali.
2. **Chi raccoglie non decide.** Un compito di raccolta restituisce dati grezzi con la fonte e la data di lettura; non classifica, non scarta, non corregge, non "migliora" i nomi.
3. **Chi decide cita la prova.** `categorie` si compila solo insieme a `prova`: una frase citata, con l'articolo o la sezione, da un documento di chi fa la gara: il regolamento di gara o del campionato (FISR), il bollettino della federazione internazionale (World Skate), oppure la pagina ufficiale dell'organizzatore (sito del club o della società che organizza), che da sola basta per `amatori`/Fitness, perché quelle gare non hanno regolamento federale. Mai da un aggregatore, da un social o da un articolo. Senza prova: `categorie: []` e `stato: da_verificare`.
4. **Non inventare.** Campo sconosciuto = campo vuoto. Mai dedurre date, luoghi o categorie dal nome dell'evento o dall'edizione precedente.
5. **Ogni esecuzione lascia traccia.** Un file in `registro/` anche in caso di errore; una riga in `appunti/diario.md` se qualcosa non ha funzionato. Per le esecuzioni automatiche di `raccolta.yml` la traccia è l'artefatto allegato al job (90 giorni) e il riassunto del job; i file di `registro/` vengono committati solo quando c'è una PR.
6. **Non ripetere errori.** Prima di tentare un approccio, controlla in `appunti/diario.md` se è già fallito e perché.
7. **Un evento non si duplica.** La chiave è `id`. Se un evento esiste già si aggiorna la voce, si aggiunge la fonte e si ricontrolla `verificato_il`.
8. **Nessun altro repository o sito si tocca.** Questo repository è l'unico posto di lavoro.
9. **Niente informazioni personali.** Il repository è pubblico: nessun nome, contatto, dispositivo o dettaglio su chi lo usa o su chi segnala. Si scrive "il proprietario" (aiBR3) e "segnalazioni volontarie". Vale anche per i dati trovati sui siti degli organizzatori (cellulari, IBAN, indirizzi email di persone): si rimanda alla pagina con il link, non si copiano.
10. **Chi verifica cerca il sito dell'organizzatore.** Le liste federali danno nome, data e organizzatore; i dettagli che servono a chi pattina (link ufficiale, distanze, orari, quote, come iscriversi) e le gare Amatori/Fitness, che il regolamento federale non copre, stanno solo sul sito dell'organizzatore locale. Per ogni evento si cerca quindi il sito dell'organizzatore (nome dell'organizzatore + città + nome della gara) e si legge la pagina dell'evento, controllando che sia dell'edizione giusta (l'anno nell'indirizzo può ingannare) e che il sito non sia compromesso (pagine di spam, lingue estranee): un sito compromesso non si linka. Se la pagina ufficiale di una gara passata è già sparita, si legge dalla Wayback Machine e si cita lo snapshot.

## Struttura del repository

```
CLAUDE.md                  ← questo file
README.md                  ← per le persone: cos'è e come iscriversi
appunti/decisioni.md       ← decisioni prese, con data e motivo
appunti/diario.md          ← cosa non ha funzionato
appunti/casi-di-prova.md   ← eventi reali che la scoperta e l'arricchimento devono saper trovare
dati/eventi.yaml           ← SORGENTE DI VERITÀ degli eventi
dati/fonti.yaml            ← registro delle fonti e di come si leggono
dati/societa.yaml          ← registro delle società (codice FISR, sigle, nome, sito, social): dove cercare l'organizzatore
script/raccogli_fisr.py    ← livello 1: lista + regolamenti di gara di fisr.info → JSON grezzo (non decide)
script/converti_fisr.py    ← livelli 2-3: JSON grezzo → voci di eventi.yaml, con prova citata dall'art. 10
script/genera_ics.py       ← eventi.yaml → calendario.ics + index.html (valida ingresso e uscita)
script/intervallo_scansione.py ← quali id di regolamento scandire questa settimana (oltre l'ultimo visto)
script/raccogli_societa.py ← registro delle società dalle classifiche, dai risultati e dai regolamenti di fisr.info
script/requisiti.txt       ← dipendenze Python
pagina_web/modello_index.html ← testo della pagina pubblicata (segnaposto {{...}})
pagina_web/stile.css        ← CSS della pagina; ogni altro file in pagina_web/ viene pubblicato così com'è
.github/workflows/         ← verifica.yml (sulle PR), pubblica.yml (su main → Pages), raccolta.yml (ogni lunedì → PR)
agenti/                    ← prompt dei compiti (da creare in Fase 2+)
registro/                  ← un rapporto per esecuzione: AAAA-MM-GG-raccolta-fisr.json, AAAA-MM-GG-conversione-fisr.md
uscita/                    ← generato localmente, ignorato da git
```

`calendario.ics` e `index.html` non sono mai committati: li genera il workflow a ogni merge su `main` e li pubblica su GitHub Pages insieme ai file di `pagina_web/`. Tutto il testo della pagina sta in `pagina_web/modello_index.html`, l'aspetto in `pagina_web/stile.css` (una PR come le altre); lo script fornisce solo i segnaposto che dipendono dai dati (`{{righe_tabella}}`, l'unico obbligatorio; `{{numero_eventi}}`, `{{url_webcal}}`, `{{url_ics}}`, `{{generato_il}}`, `{{titolo}}`, `{{descrizione}}`). Nella tabella gli eventi sono in ordine cronologico inverso: il più recente in alto.

## Cosa vede chi consulta il calendario

Per ogni evento: titolo (con eventuale prefisso di stato), date, luogo, e una descrizione breve, una riga per voce con l'etichetta tra parentesi quadre (mai seguita dai due punti, che gli organizzatori usano nei loro testi), in quest'ordine: `[Categorie ammesse]` (o "Non ancora pubblicate" per `annunciato`, "Da verificare" negli altri casi senza categorie, "Pattinata non competitiva" per le pattinate), `[Distanze]`, `[Organizzatore]`, `[Scadenza iscrizioni]`, le `note` in `[Informazioni]` e per ultimo **un solo link** in `[URL]` (`url_ufficiale`, altrimenti `url_iscrizione`). Lo stesso link va anche nella proprietà `URL` dell'evento (Calendario di Apple la mostra, Google la ignora). `prova`, `fonti`, `stato`, `verificato_il` e `note_interne` sono dati di lavoro: restano nell'YAML e non vanno nella descrizione. Le `note` sono visibili a tutti: scriverle per chi pattina (impianto, orari, quote, come ci si iscrive); tutto il resto (dubbi, doppioni, anomalie di lettura, cosa ricontrollare) va in `note_interne`.

## Schema di `dati/eventi.yaml`

Lista di eventi. Tutte le chiavi vanno sempre scritte, anche vuote (`""` o `[]`).

Lo script rifiuta chiavi sconosciute, chiavi mancanti e valori incoerenti.

| Campo | Tipo | Regola |
|---|---|---|
| `id` | testo | `AAAA-MM-GG-citta-slug`, minuscolo, senza accenti; la data è `data_inizio`; diventa l'UID nell'ICS, quindi **non cambia mai** |
| `nome` | testo | nome ufficiale, con maiuscole normali (non TUTTO MAIUSCOLO) |
| `data_inizio`, `data_fine` | data | ISO `AAAA-MM-GG`; evento di un giorno: uguali |
| `luogo` | testo | città (provincia) e, se noto, impianto o indirizzo |
| `paese` | codice | uno tra `IT CH ES PT FR AT DE SI` |
| `tipo` | enum | `gara` oppure `pattinata` |
| `categorie` | lista | sottoinsieme di `[master, amatori]`; **vuota finché non c'è `prova`**. Una gara aperta a tutti per anno di nascita, senza categorie agonistiche obbligatorie (tipiche all'estero: "Jahrgänge 2012 und älter"), vale `[master, amatori]` |
| `distanze` | lista di testi | es. `["maratona", "10 km"]`; vuota se ignote |
| `organizzatore` | testo | la società o il club che organizza materialmente la gara sul posto (es. "Skating Club Comina A.S.D."), non la federazione che la approva o la rende campionato; può essere vuoto |
| `url_ufficiale`, `url_iscrizione` | URL http(s) o `""` | |
| `scadenza_iscrizione` | data o `""` | |
| `stato` | enum | vedi sotto |
| `fonti` | lista, **almeno una** | ogni voce: `url` + `letto_il` (data) |
| `verificato_il` | data o `""` | obbligatoria per `confermato` ed `escluso` |
| `prova` | testo | obbligatoria se `categorie` non è vuota e per `confermato`/`escluso` |
| `note` | testo | **pubbliche**: vanno nella descrizione dell'evento; solo cose utili a chi pattina |
| `note_interne` | testo | dati di lavoro: dubbi, doppioni nella fonte, anomalie, cosa ricontrollare; mai pubblicate |

Stati:

| `stato` | Significato | Nel calendario |
|---|---|---|
| `da_verificare` | trovato, non ancora controllato | sì, titolo con `[da verificare]` |
| `annunciato` | fonte ufficiale, ma categorie non ancora pubblicate | sì |
| `confermato` | categorie verificate con prova | sì |
| `rinviato` | | sì, titolo con `[RINVIATA]` |
| `annullato` | | sì, titolo con `[ANNULLATA]` (non usiamo STATUS:CANCELLED: alcune app lo nasconderebbero) |
| `non_autorizzato` | a calendario federale "in attesa di autorizzazione" | sì, titolo con `[non ancora autorizzata]` |
| `escluso` | **verificato**: non ammette Master/Amatori | **no**; resta nel file come memoria, con la prova |

## Schema di `dati/fonti.yaml`

Una voce per fonte: `id`, `nome`, `url`, `paese`, `metodo` (`script`, `agente`, `browser`, `manuale`), `frequenza`, `copre` (`gare`, `pattinate`, `verifica`), `affidabilita` (`ufficiale`, `organizzatore`, `aggregatore`, `social`), `stato` (`attiva`, `da_verificare`, `scartata`), `note`, `ultimo_controllo` (data o `""`).

## Schema di `dati/societa.yaml`

Una voce per società, chiave `codice_fisr` (il numero che la federazione assegna alla società: non cambia, le sigle sì). Campi: `nome_fisr` (sigla nelle classifiche), `sigle_fisr` (tutte le sigle viste), `nome` (esteso, dai risultati, dal regolamento o dal sito), `citta`, `regione`, `sito`, `social`, `stato_sito` (`sito_verificato` = aperto e il testo conferma nome e pattinaggio; `sito_da_verificare`; `sito_non_raggiungibile` = dalla shell, non per forza morto; `solo_social`; `senza_sito`), `fonte_sito` (da dove viene l'indirizzo e quando è stato aperto), `siti_candidati` (trovati nei regolamenti, non ancora verificati), `ultima_stagione`, `classifiche` e `gare_organizzate` (di quella stagione), `ultimo_controllo`, `note`. `codice_fisr` vuoto solo per organizzatori non affiliati (es. SCC Events). Lo script `raccogli_societa.py` compila la parte federale e non tocca mai `nome`, `citta`, `sito`, `social`, `stato_sito`, `fonte_sito`, `note`. Un social è un recapito, mai una fonte né una prova (regola 3). Niente contatti di persone (regola 9).

## Convenzioni

- Lingua: italiano ovunque, anche nel codice (nomi di variabili, funzioni, file, messaggi). Le date in ISO 8601.
- Parole: il documento FISR `corsa_trofeo_modulo.php?id_manif=N` si chiama **regolamento di gara** (o "regolamento"), mai "indizione" (gergo federale, incomprensibile ai più); "regolamento del campionato" è invece quello pubblicato nei comunicati FISR.
- Gli script non danno nulla per scontato: controllano cosa ricevono in ingresso e cosa producono in uscita, e si fermano con un messaggio chiaro.
- Messaggi di commit in italiano, al presente, un argomento per PR ("Aggiunge le gare di dicembre da fisr.info").
- Ogni PR dice nel testo: cosa cambia, da quali fonti, cosa resta in dubbio.

## Come si lavora in locale

```
pip install -r script/requisiti.txt

# 1. Raccolta grezza da fisr.info (lista della stagione + regolamenti di gara; la scansione degli id
#    trova anche i regolamenti di gara che la lista non linka più: gare passate e "non autorizzate")
python3 script/raccogli_fisr.py --anno 2026 --da 2026-01-01 --regolamenti \
    --scansione-regolamenti 6300 7100 --uscita registro/AAAA-MM-GG-raccolta-fisr.json

# 2. Conversione in voci di eventi.yaml (prima senza --scrivi, per leggere il rapporto)
python3 script/converti_fisr.py --raccolta registro/AAAA-MM-GG-raccolta-fisr.json \
    --rapporto registro/AAAA-MM-GG-conversione-fisr.md [--scrivi]

# 3. Revisione a mano delle voci nuove (nomi, luoghi, organizzatori), poi:
python3 script/genera_ics.py --ingresso dati/eventi.yaml --uscita uscita \
    --url-base https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico

# Settimanalmente serve solo l'intervallo di id oltre l'ultimo visto (è ciò che fa raccolta.yml):
python3 script/intervallo_scansione.py        # stampa "DA A", es. 7031 7380

# A ogni stagione (o quando servono società nuove): registro delle società dalle classifiche federali,
# dai risultati ("Organizzato da") e dai regolamenti (siti citati); i campi a mano restano
python3 script/raccogli_societa.py --anno 2026 --registro dati/societa.yaml \
    --raccolta registro/AAAA-MM-GG-raccolta-fisr.json --rapporto registro/AAAA-MM-GG-societa.md
```

Il workflow `raccolta.yml` esegue questi stessi passi ogni lunedì (05:17 UTC) con `--da` = 14 giorni prima e l'intervallo di `intervallo_scansione.py`; se `eventi.yaml` cambia apre una PR dal ramo `raccolta/AAAA-MM-GG`, una sola alla volta (se la precedente è ancora aperta non ne apre un'altra). Da "Actions → Run workflow" si può lanciare a mano, anche con un intervallo di id esplicito per una scansione completa. Le PR aperte dal token di Actions non fanno partire `verifica.yml`: per questo il workflow esegue da sé `genera_ics.py` prima di aprirle.

Cosa decide `converti_fisr.py` e cosa no:
- regolamento di gara con righe `MASTER …` nell'art. 10 → `confermato`, `categorie: [master]`, prova = le righe citate;
- regolamento di gara senza righe Master/Amatori → `escluso`, prova = l'elenco delle categorie;
- nessun regolamento di gara ma titolo ufficiale con `cat. …/M` (campionati FISR) → `confermato` con prova = il titolo; con `cat.` senza M → `escluso`;
- tutto il resto → `da_verificare`, categorie vuote;
- **promozione** (regola 7): una voce già presente ma senza prova (`da_verificare`, `non_autorizzato`, `annunciato`) che ora ha il regolamento di gara riceve categorie, prova, stato, `verificato_il`, la fonte nuova e i campi vuoti (link, distanze, scadenza); una voce `non_autorizzato` con prova che la lista non segna più come "non ancora autorizzata" passa a `confermato`/`escluso`. Nome, luogo, organizzatore, note e tutto ciò che una persona ha scritto restano com'erano.

Per il resto le voci già presenti in `eventi.yaml` non vengono modificate dallo script: una voce che ha già la prova non cambia mai da sola, e le differenze con quanto raccolto finiscono solo nel rapporto.

## Fase attuale

**Fase 2 — raccolta automatica, revisione a mano.** Il workflow `raccolta.yml` raccoglie da fisr.info ogni lunedì e apre una PR con le voci nuove; nessun modello decide: le categorie vengono solo da ciò che `converti_fisr.py` dimostra con il regolamento di gara, il resto è `da_verificare`. Il proprietario rivede la PR (nomi, luoghi, organizzatori, regola 10) e la fonde. La Fase 1 (tutto a mano, 63 voci al 2026-11-06) è chiusa; i siti degli organizzatori e le fonti estere restano letti a mano finché non arriva la Fase 3 (arricchimento e verifica con un modello), i cui casi di collaudo stanno in `appunti/casi-di-prova.md`. Le fasi sono descritte in `appunti/decisioni.md`.
