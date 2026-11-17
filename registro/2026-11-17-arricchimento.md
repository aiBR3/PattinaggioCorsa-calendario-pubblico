# Arricchimento del 2026-11-17

- Ramo: `raccolta/2026-11-16` (PR #55, raccolta del 2026-11-16)
- Esecuzione: attività pianificata; orologio della sessione 05:05-05:15 UTC circa (fa fede la pagina dell'attività)

## Voci

| id | esito | sito da | campi cambiati | ricerche | articoli | pagine aperte | minuti |
|---|---|---|---|---|---|---|---|
| `2027-05-28-laquila-internazionali-ditalia-open-indoor` | sito trovato, pagina dell'evento assente | registro | solo `note_interne` (traccia) | 0 | 0 | 4: https://cpga.net/, https://cpga.net/iio/, https://cpga.net/iio/iio-corsa/, https://cpga.net/iio/memorial-cacciani/ | ~3 |

Voce nuova non lavorata: `2027-07-31-san-benedetto-del-tronto-meeting-san-benedetto-tronto` è `escluso` (prova dal regolamento 7101): le voci escluse non si toccano.

## Totali

- Voci nuove: 2 nella PR; 1 lavorata, 1 esclusa (non si tocca).
- Voci vecchie ricontrollate: 0. Nessuna voce futura senza prova o senza `url_ufficiale` ha l'ultimo controllo più vecchio di 14 giorni: le quattro candidate (Terni 06/06/2027, Fabriano 03/07/2027, City Night Berlino 31/07/2027, Pollenza 25/09/2027) hanno l'ultimo controllo al 2026-11-06 e rientrano dal 2026-11-21.
- Promosse a `confermato`: 0. Passate a `escluso`: 0.
- Siti trovati: 1 (registro). Non trovati: 0. Compromessi o non raggiungibili: 0.
- Società aggiornate nel registro: 0 (C.P.G.A. è già `sito_verificato`).
- Ricerche web: 0. Articoli: 0.

## Dubbi

1. `url_ufficiale` della voce dell'Aquila (maggio 2027) è il regolamento FISR 7073. Il prompt dice di mettere la home dell'organizzatore quando la pagina dell'evento non c'è, ma solo se il campo è vuoto: non l'ho sostituito. Decide il proprietario se preferisce `https://cpga.net/iio/` (pagina degli Internazionali, oggi con le sole edizioni 2026).
2. Fuori perimetro di questa esecuzione, notato aprendo le pagine: `https://cpga.net/iio/memorial-cacciani/` ha in testata "5, 6 Dicembre 2026" ma nel testo "dalla mattina di Sabato 21 a Domenica 22 Novembre 2026" e categorie "da Giovanissimi ad Allievi", senza Master. La voce `2026-12-06-laquila-internazionali-open-indoor-master-race` (regolamento 7047, Master, 06/12) non è stata toccata: il testo della pagina sembra copiato da un'altra gara; conviene ricontrollarla sul regolamento 7047 prima del 6 dicembre.

## Errori

- `pip install -r script/requisiti.txt` installa per Python 3.13 (pip di sistema), mentre `python3` è 3.11: `genera_ics.py` diceva "Manca una dipendenza (icalendar)". Risolto con `python3 -m pip install --ignore-installed -r script/requisiti.txt`. Nota nel diario.
