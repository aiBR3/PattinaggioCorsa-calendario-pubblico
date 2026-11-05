# CLAUDE.md — regole permanenti per chi lavora in questo repository

Questo file è la memoria permanente di agenti e script. Leggilo per intero prima di
fare qualsiasi cosa. Poi leggi `note/diario.md` (cosa non ha funzionato, per non
riprovarlo) e `note/decisioni.md` (perché le cose sono fatte così).

## Scopo

Un calendario pubblico (file ICS) con tutte le gare e gli eventi di pattinaggio corsa
che ammettono le categorie **Master** (agonisti dai 30 anni in su, una sotto-categoria
ogni 5 anni) e **Amatori/Fitness** (non agonisti; i due termini sono intercambiabili),
comprese le pattinate non competitive (notturne, al mare, natalizie, per famiglie).

Perimetro geografico: Italia, Svizzera, Spagna, Portogallo, Francia, Austria,
Germania, Slovenia.

Chi lo consulta: la squadra. T (aiBR3) su iPhone (app Calendario), compagni su
Android (Google Calendar). Il calendario è utile solo se è **affidabile**: meglio un
evento in meno che una data sbagliata.

## Regole inviolabili

1. **Nessuno scrive su `main`.** Ogni modifica è una pull request; il merge lo fa
   solo T, a mano. Vale anche per chi agisce con le credenziali di T.
2. **Chi raccoglie non decide.** Un compito di raccolta restituisce dati grezzi con la
   fonte e la data di lettura; non classifica, non scarta, non corregge, non
   "migliora" i nomi.
3. **Chi decide cita la prova.** `categorie` si compila solo insieme a `prova`: una
   frase citata dal regolamento o dall'indizione, con l'articolo. Senza prova:
   `categorie: []` e `stato: da_verificare`.
4. **Non inventare.** Campo sconosciuto = campo vuoto. Mai dedurre date, luoghi o
   categorie dal nome dell'evento o dall'edizione precedente.
5. **Ogni esecuzione lascia traccia.** Un file in `log/` anche in caso di errore; una
   riga in `note/diario.md` se qualcosa non ha funzionato.
6. **Non ripetere errori.** Prima di tentare un approccio, controlla in
   `note/diario.md` se è già fallito e perché.
7. **Un evento non si duplica.** La chiave è `id`. Se un evento esiste già si aggiorna
   la voce, si aggiunge la fonte e si ricontrolla `verificato_il`.
8. **Il sito Hugo della squadra non si tocca.** Questo repository è l'unico posto di
   lavoro.

## Struttura del repository

```
CLAUDE.md                  ← questo file
README.md                  ← per le persone: cos'è e come iscriversi
note/decisioni.md          ← decisioni prese, con data e motivo
note/diario.md             ← cosa non ha funzionato
dati/eventi.yaml           ← SORGENTE DI VERITÀ degli eventi
dati/fonti.yaml            ← registro delle fonti e di come si leggono
script/genera_ics.py       ← eventi.yaml → calendario.ics + index.html (valida ingresso e uscita)
script/requisiti.txt       ← dipendenze Python
.github/workflows/         ← verifica.yml (sulle PR), pubblica.yml (su main → Pages)
agenti/                    ← prompt dei compiti (da creare in Fase 2+)
log/                       ← un rapporto per esecuzione (da creare in Fase 2+)
uscita/                    ← generato localmente, ignorato da git
```

`calendario.ics` non è mai committato: lo genera il workflow a ogni merge su `main`
e lo pubblica su GitHub Pages.

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
| `categorie` | lista | sottoinsieme di `[master, amatori]`; **vuota finché non c'è `prova`** |
| `distanze` | lista di testi | es. `["maratona", "10 km"]`; vuota se ignote |
| `organizzatore` | testo | può essere vuoto |
| `url_ufficiale`, `url_iscrizione` | URL http(s) o `""` | |
| `scadenza_iscrizione` | data o `""` | |
| `stato` | enum | vedi sotto |
| `fonti` | lista, **almeno una** | ogni voce: `url` + `letto_il` (data) |
| `verificato_il` | data o `""` | obbligatoria per `confermato` ed `escluso` |
| `prova` | testo | obbligatoria se `categorie` non è vuota e per `confermato`/`escluso` |
| `note` | testo | tutto ciò che non entra negli altri campi |

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

Una voce per fonte: `id`, `nome`, `url`, `paese`, `metodo` (`script`, `agente`,
`browser`, `manuale`), `frequenza`, `copre` (`gare`, `pattinate`, `verifica`),
`affidabilita` (`ufficiale`, `organizzatore`, `aggregatore`, `social`), `stato`
(`attiva`, `da_verificare`, `scartata`), `note`, `ultimo_controllo` (data o `""`).

## Convenzioni

- Lingua: italiano ovunque, anche nel codice (nomi di variabili, funzioni, file,
  messaggi). Le date in ISO 8601.
- Gli script non danno nulla per scontato: controllano cosa ricevono in ingresso e
  cosa producono in uscita, e si fermano con un messaggio chiaro.
- Messaggi di commit in italiano, al presente, un argomento per PR
  ("Aggiunge le gare di dicembre da fisr.info").
- Ogni PR dice nel testo: cosa cambia, da quali fonti, cosa resta in dubbio.

## Come si genera il calendario in locale

```
pip install -r script/requisiti.txt
python3 script/genera_ics.py --ingresso dati/eventi.yaml --uscita uscita \
    --url-base https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico
```

## Fase attuale

**Fase 1 — a mano, insieme.** Nessun agente autonomo è attivo. Ogni voce in
`eventi.yaml` è stata letta e verificata da una persona con Claude nella stessa
conversazione. Le fasi successive sono descritte in `note/decisioni.md`.
