# Calendario pubblico del pattinaggio corsa per Master e Amatori (generato automaticamente)

Un calendario pubblico (compilato periodicamente da script e IA) con le gare e gli eventi di pattinaggio corsa aperti alle categorie **Master** e **Amatori/Fitness**, comprese le pattinate non competitive, in Italia e nei paesi vicini (Svizzera, Spagna, Portogallo, Francia, Austria, Germania, Slovenia).

## Scaricare il calendario

Il calendario è un file `.ics` pubblicato con *GitHub Pages* e aggiornato ad ogni modifica:

- se usi l'app Calendario di Apple, incolla nel browser `webcal://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/calendario.ics`
- se usi l'app Calendario di Google, apri *Google Calendar → Altri calendari → Da URL* e incolla `https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/calendario.ics` (Google aggiorna le sottoscrizioni ogni 12–24 ore circa)

Dopo che ti sei iscritto al calendario, riceverai gli aggiornamenti in automatico.

La [pagina web](https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/) mostra queste istruzioni e gli eventi trovati.

## Segnalare una gara

Un modulo per le segnalazioni volontarie è *in arrivo*.

Nel frattempo apri una [issue](https://github.com/aiBR3/PattinaggioCorsa-calendario-pubblico/issues) con data, luogo, nome e il link della gara (o il testo del post sui social).

## Come funziona

- le regole per chi lavora qui (persone, script, agenti) sono in [CLAUDE.md](CLAUDE.md)
- [script/genera_ics.py](script/genera_ics.py) valida il file e genera `calendario.ics` e `index.html`
- a ogni modifica su `main`, il workflow [pubblica.yml](.github/workflows/pubblica.yml) rigenera la pagina web
