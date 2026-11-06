# Calendario pubblico del pattinaggio corsa per Master e Amatori (generato automaticamente)

Un calendario pubblico con le gare e gli eventi di pattinaggio corsa aperti alle categorie **Master** e **Amatori/Fitness**, comprese le pattinate non competitive, in Italia e nei paesi vicini (Svizzera, Spagna, Portogallo, Francia, Austria, Germania, Slovenia).

## Iscriversi al calendario

Il calendario è un file `.ics` pubblicato con *GitHub Pages* e aggiornato a ogni modifica.

- per **iPhone, iPad, Mac / Apple Calendar**: aprire `webcal://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/calendario.ics`
- per **Android / Google Calendar**: in Google Calendar → *Altri calendari* → *Da URL* → incollare `https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/calendario.ics` (Google aggiorna le sottoscrizioni ogni 12–24 ore circa)

La pagina web [https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/](https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/) mostra queste istruzioni con i link qui sopra e gli eventi pubblicati.

## Segnalare una gara

Un modulo per le segnalazioni volontarie è in arrivo.

Nel frattempo apri una [issue](https://github.com/aiBR3/PattinaggioCorsa-calendario-pubblico/issues) con data, luogo, nome e il link della gara (o il testo del post sui social).

## Come funziona

- le regole per chi lavora qui (persone, script, agenti) sono in [CLAUDE.md](CLAUDE.md)
- [dati/fonti.yaml](dati/fonti.yaml) è il registro delle fonti
- [dati/eventi.yaml](dati/eventi.yaml) è la sorgente di verità, un evento per voce con fonti, data di verifica e la prova delle categorie ammesse
- [script/genera_ics.py](script/genera_ics.py) valida il file e genera `calendario.ics` e `index.html`
- a ogni modifica su `main`, un workflow *GitHub Actions* rigenera e pubblica la pagina web
