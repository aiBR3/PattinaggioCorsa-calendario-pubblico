# Calendario pubblico del pattinaggio corsa per Master e Amatori (generato automaticamente)

Un calendario pubblico (compilato periodicamente da script e IA) con le gare e gli eventi di pattinaggio corsa aperti alle categorie **Master** e **Amatori/Fitness**, comprese le pattinate non competitive, in Italia e nei paesi vicini (Svizzera, Spagna, Portogallo, Francia, Austria, Germania, Slovenia).

Il calendario è un file `.ics` pubblicato con *GitHub Pages* e aggiornato ad ogni modifica.

## Scaricare il calendario

La [pagina web](https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/) mostra queste istruzioni (e una lista delle gare trovate):

- se usi l'app Calendario di Apple, incolla nel browser `webcal://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/calendario.ics`
- se usi l'app Calendario di Google, apri *Google Calendar → Altri calendari → Da URL* e incolla `https://aibr3.github.io/PattinaggioCorsa-calendario-pubblico/calendario.ics` (Google aggiorna le sottoscrizioni ogni 12–24 ore circa)
- dopo che ti sei iscritto al calendario, riceverai gli aggiornamenti in automatico

## Segnalazioni

Per segnalare gare mancanti o correzioni, usa [questo modulo](https://tally.so/r/peDGAP).

## Come funziona

- le regole per chi lavora al progetto (persone, script, agenti) sono in [CLAUDE.md](CLAUDE.md)
- a ogni modifica sul ramo `main`, il workflow [pubblica.yml](.github/workflows/pubblica.yml) rigenera la pagina web e il calendario pubblici
    - in particolare [script/genera_ics.py](script/genera_ics.py) genera `calendario.ics` e `index.html`
