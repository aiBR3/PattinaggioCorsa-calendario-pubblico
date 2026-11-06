# Attività pianificata "Arricchimento calendario pattinaggio corsa"

L'attività pianificata Claude che ogni martedì esegue `agenti/arricchimento.md` la crea e la gestisce il proprietario dalla pagina delle attività pianificate (claude.ai/code/routines, oppure dall'app Claude per computer, scheda Code → Scheduled). Questo file è la memoria della sua configurazione: se l'attività va ricreata, si ricopia da qui. Il testo del prompt è volutamente corto: tutto il procedimento sta in `agenti/arricchimento.md`, nel repository, così si cambia con una PR senza toccare l'attività.

## Testo del prompt (da incollare tale e quale)

```
Sei l'agente di arricchimento del calendario pubblico delle gare di pattinaggio corsa (Fase 3 del progetto). Lavora in italiano.

Il repository GitHub `aiBR3/PattinaggioCorsa-calendario-pubblico` è già clonato nella cartella di lavoro: entra nella cartella che contiene `CLAUDE.md` e `.git`. Se non c'è, aggiungilo alla sessione con `add_repo` (accesso push), clonalo come dice lo strumento e registralo con `register_repo_root`.

1. Leggi per intero `CLAUDE.md`, poi `appunti/diario.md` e `appunti/decisioni.md`.
2. Leggi per intero `agenti/arricchimento.md` ed eseguilo alla lettera, dal Passo 0 al Passo 4, rispettando la tabella "Limiti". È il tuo unico compito: non fare altro.
3. Regole che prevalgono su tutto: non scrivere mai su `main`; non fondere e non approvare pull request; non inventare (campo sconosciuto = campo vuoto); non copiare contatti di persone; modifica `dati/eventi.yaml` e `dati/societa.yaml` solo con sostituzioni testuali mirate; commit e push ogni 5 voci; lascia traccia in `registro/` e, se qualcosa non ha funzionato, in `appunti/diario.md`.
4. Finisci con un messaggio in italiano: i numeri (voci nuove lavorate, voci vecchie ricontrollate, siti trovati e per quale via, confermate, escluse, dubbi) e il link alla PR. Se un passo si blocca, scrivi cosa è successo e dove ti sei fermato, poi fermati.
```

## Configurazione

| Campo del modulo | Valore | Perché |
|---|---|---|
| Nome | `Arricchimento calendario pattinaggio corsa` | |
| Prompt | il testo qui sopra | |
| Trigger | Schedule, ogni settimana, martedì alle 06:07 (ora locale del proprietario, Europe/Rome) | Dopo la raccolta del lunedì (05:17 UTC); il proprietario ha chiesto "intorno alle 6"; non in punto, perché le esecuzioni in punto possono partire in ritardo |
| Repository | `aiBR3/PattinaggioCorsa-calendario-pubblico` | Viene clonato all'avvio di ogni esecuzione |
| Cloud environment | un ambiente dedicato (nome suggerito `Calendario pattinaggio`) con Network access = **Full** | L'ambiente `Default` ha accesso di rete `Trusted`: solo registri di pacchetti e GitHub. L'agente deve raggiungere dalla shell fisr.info, attivita.rollergames.it, web.archive.org e i siti degli organizzatori, che non si conoscono in anticipo: con `Trusted` ogni `curl` fallisce e l'arricchimento non trova nulla. In alternativa a `Full`: `Custom` con `fisr.info`, `www.fisr.info`, `attivita.rollergames.it`, `web.archive.org` e la casella "Also include default list of common package managers"; ma i siti degli organizzatori resterebbero fuori |
| Variabili d'ambiente, setup script | nessuno | `pip install` lo fa il Passo 0 del prompt |
| Modello | Opus 5.5 | Scelta del proprietario (2026-11-06) |
| Effort | Medium (Medio) | Idem; è il livello con cui è passato il terzo collaudo cieco (`registro/2026-11-06-arricchimento-collaudo-3.md`) |
| Connettori | nessuno (togliere tutti quelli proposti) | GitHub non serve come connettore: le chiamate `gh api` passano dal proxy git della sessione. Meno connettori, meno cose che l'agente può toccare |
| Approvazione | automatica (modalità predefinita delle esecuzioni pianificate: un classificatore approva o blocca le azioni) | Senza, l'esecuzione si fermerebbe alla prima richiesta di permesso, di notte |

## Dopo la creazione

- La prima esecuzione utile è martedì 2026-11-10. Per provarla subito: "Run now" nella pagina dell'attività; senza una PR `raccolta/…` aperta l'agente resta su `main` e fa solo il ricontrollo delle voci vecchie (Passo 1 del prompt), aprendo al massimo una PR `arricchimento/AAAA-MM-GG`.
- Ogni esecuzione compare in "History" nella pagina dell'attività e si apre come una sessione: lì si legge cosa ha fatto. "Succeeded" dice solo che la sessione è finita senza errore, non che il lavoro è giusto: la verifica è la PR.
- Per sospendere: l'interruttore in alto nella pagina dell'attività. Per cambiare orario, modello, ambiente o prompt: menu accanto al nome → Edit → Save changes.
- Il testo del prompt si cambia qui e poi nell'attività; `agenti/arricchimento.md` si cambia solo con una PR.
