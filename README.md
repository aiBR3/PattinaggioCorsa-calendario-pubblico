# Calendario pubblico del pattinaggio corsa — Master e Amatori

Un calendario condiviso con le gare e gli eventi di pattinaggio corsa (inline speed
skating) aperti alle categorie **Master** e **Amatori/Fitness**, comprese le pattinate non
competitive, in Italia e nei paesi vicini (Svizzera, Spagna, Portogallo, Francia,
Austria, Germania, Slovenia).

## Iscriversi al calendario

Il calendario è un file `.ics` pubblicato su GitHub Pages e aggiornato a ogni modifica.

- **iPhone, iPad, Mac:** apri
  `webcal://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/calendario.ics`
- **Android / Google Calendar:** da computer, in Google Calendar → *Altri calendari* →
  *Da URL* → incolla
  `https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/calendario.ics`
  (Google aggiorna le sottoscrizioni ogni 12–24 ore circa).

La pagina <https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/> mostra gli
eventi pubblicati e i link qui sopra.

## Cosa trovi nel calendario

Ogni evento ha nel titolo il nome ufficiale e, se serve, un prefisso:

| Prefisso | Significato |
|---|---|
| *(nessuno)* | categorie Master/Amatori verificate sull'indizione o sul regolamento, oppure evento ufficiale in attesa del programma |
| `[da verificare]` | segnalato ma non ancora controllato |
| `[non ancora autorizzata]` | a calendario federale, in attesa di autorizzazione |
| `[RINVIATA]`, `[ANNULLATA]` | come dice |

Nella descrizione: tipo, categorie ammesse, distanze, organizzatore, scadenza iscrizioni,
link all'indizione, la frase del regolamento che prova le categorie, le fonti.

## Segnalare una gara

In arrivo: un modulo per i compagni di squadra. Nel frattempo apri una
[issue](https://github.com/aiBR3/PattinaggioCorsa-calendario-pubblico/issues) con
data, luogo, nome e il link (o il testo del post).

## Come funziona

- `dati/eventi.yaml` è la sorgente di verità: un evento per voce, con fonti, data di
  verifica e la prova delle categorie ammesse.
- `script/genera_ics.py` valida il file e genera `calendario.ics` + `index.html`.
- A ogni modifica su `main`, un workflow GitHub Actions rigenera e pubblica su Pages.
- `dati/fonti.yaml` è il registro delle fonti; `note/` contiene decisioni e diario.
- Le regole per chi lavora qui (persone, script, agenti) sono in `CLAUDE.md`.

Ogni modifica passa da una pull request. Il progetto è in **Fase 1**: inserimento manuale
e verificato; l'automazione arriverà a fasi (vedi `note/decisioni.md`).
