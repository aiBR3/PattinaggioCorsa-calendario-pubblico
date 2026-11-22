# Skate Terminal: prima lettura come pista — 2026-11-22

Fonte indicata dal proprietario, che ha scelto di usarla solo come pista, letta a mano una volta al mese (decisione del 2026-11-22 in `appunti/decisioni.md`). Lettura eseguita a mano in una sessione di lavoro. Modifica `dati/eventi.yaml` (6 voci nuove), `dati/fonti.yaml` (fonte `skate-terminal`) e `appunti/decisioni.md`; raccolta, script e prompt non cambiano.

## Metodo

- Su Skate Terminal sono state lette la ricerca filtrata registrata in `dati/fonti.yaml` (due pagine, 24 schede) e le 9 schede delle piste dentro il perimetro, solo per ricavare nome, data dichiarata e sito dell'organizzatore. Lette anche le condizioni d'uso e il `robots.txt` del sito. Nessuna lettura automatica e nessuna chiamata all'API della sua applicazione.
- Per ogni pista è stato aperto dalla shell il sito dell'organizzatore linkato dalla scheda, nella lingua originale: pagina della gara, una pagina interna, condizioni di partecipazione, pagina di iscrizione, programma. L'edizione è stata riconosciuta dalle date nel testo e dai documenti linkati, non dall'anno nel titolo (diario del 2026-11-06).
- Nessun dato di Skate Terminal è entrato in una voce: date, luoghi, orari, quote e prove vengono dai siti degli organizzatori. In `note_interne` la pista è nominata come tale.
- Limite: una sola lettura, fatta da una sessione. I programmi di Spreewald e Lausitz sono immagini: sono stati letti a vista e confrontati con le rispettive pagine di iscrizione, che riportano le stesse date e gli stessi orari.

## Le 24 schede

| Scheda | Data nella scheda | Esito |
|---|---|---|
| 8 gare ISU su ghiaccio (Heerenveen, Stavanger, Dresda, Danzica, Baselga di Piné, Tilburg) | dicembre 2026 - febbraio 2027 | Fuori tema: la disciplina "speed skating" del sito comprende il ghiaccio |
| HUS Knock Out Battle (Amsterdam), Winterclash (Eindhoven) | 28/11/2026, 25-27/02/2027 | Fuori tema (aggressive) e fuori perimetro |
| Berlin Inline Skating Half Marathon | 04/04/2027 | Già nel calendario |
| Bonn Inline Half Marathon | 11/04/2027 | **Scartata**: vedi sotto |
| Linz Inline Skating Half Marathon | 11/04/2027 | **Voce nuova**, `confermato` |
| arena geisingen international | 15-18/04/2027 | **In sospeso**: vedi sotto |
| Spreewaldmarathon | 24/04/2027 | **Voce nuova**, `confermato` |
| SKS Bike Marathon (Sundern) | 24/04/2027 | Fuori tema: gara di bici |
| 28. Rhein-Ruhr-Inline-Marathon (Duisburg) | 02/05/2027 | **Voce nuova**, `confermato` |
| Wrotkarska Majówka (Poznań) | 03/05/2027 | Fuori perimetro (Polonia) |
| 26. Lausitz-Marathon | 08/05/2027 | **Voce nuova**, `confermato` |
| Rennes sur Roulettes | 22-23/05/2027 | **Voce nuova**, `annunciato` |
| Salzburg Marathon | 23/05/2027 | **Scartata**: vedi sotto |
| Roll'Athlon100 | 19/06/2027 | **Voce nuova**, `annunciato`, con la data del sito ufficiale: 20/06/2027 |
| FEST CUP Karlsruhe | 21-24/07/2027 | Fuori tema (action sports) |
| adidas Runners City Night Inlineskating (Berlino) | 31/07/2027 | Già nel calendario |

## Voci nuove

| Voce | Stato | Prova e fonti | Che cosa manca |
|---|---|---|---|
| `2027-04-11-linz-fischer-brot-inline-skating-halbmarathon` | `confermato`, `[master, amatori]` | Condizioni di partecipazione del Linz Marathon: può partecipare chiunque abbia compiuto 18 anni, i minorenni con il consenso dei genitori. Pagina della gara con orari e quote 2027; data nella home | Niente: scadenza 18/03/2027, 200 posti |
| `2027-04-24-burg-spreewaldmarathon-skate-marathon` | `confermato`, `[master, amatori]` | Condizioni generali dell'organizzatore: può partecipare chiunque, anche senza una società. Programma 2027 e pagina di iscrizione: sabato 24/04, ore 17:00 e 17:05 | Niente: scadenza 04/04/2027 |
| `2027-05-02-duisburg-rhein-ruhr-inline-marathon` | `confermato`, `[master, amatori]` | Pagina delle classi d'età: età minima 16 anni, classifiche per anno di nascita fino ai Masters U80. Pagina della gara con quote fino al 02/05/2027 | Una frase esplicita sui non tesserati (vedi i dubbi); scadenza lasciata vuota: le quote arrivano fino al giorno della gara |
| `2027-05-08-klettwitz-lausitz-marathon-skate-marathon` | `confermato`, `[master, amatori]` | Condizioni generali dell'organizzatore: può partecipare chiunque, anche senza una società. Programma 2027 e pagina di iscrizione: sabato 08/05, ore 09:00 e 14:45 | Niente: iscrizioni online fino al 04/05/2027, poi sul posto |
| `2027-05-22-rennes-rennes-sur-roulettes` | `annunciato`, senza categorie | La home annuncia la 45ª edizione per il 22-23 maggio 2027 | Programma e condizioni 2027: le pagine di dettaglio linkano ancora i documenti del 2026 |
| `2027-06-20-seyssel-rollathlon100` | `annunciato`, senza categorie | La home annuncia la 12ª edizione per domenica 20 giugno 2027 | Formule, distanze, iscrizioni e organizzatore: le altre pagine sono del 2025; il luogo viene da una di quelle |

Dopo questa lettura `dati/eventi.yaml` ha 111 voci, 64 pubblicate.

## Piste scartate

- **Bonn, 11/04/2027.** Il sito ufficiale della Deutsche Post Marathon Bonn conferma la data, ma tra le gare del 2027 (maratona, mezza maratona, staffetta, 10 km, gare per aziende e scuole) non ce n'è una sui pattini; la ricerca interna del sito con la parola "inline" dà solo notizie di corsa. La parola compare soltanto in una vecchia descrizione nascosta nell'intestazione della pagina. Nessuna voce.
- **Salisburgo, 23/05/2027.** Il sito ufficiale della Salzburg Marathon elenca solo gare di corsa; nessuna gara sui pattini. Nessuna voce.

Le due piste sono scritte nella nota della fonte in `dati/fonti.yaml`, per non riproporle alla prossima lettura.

## In sospeso

- **arena geisingen international, 15-18/04/2027.** La pagina dell'impianto conferma le date, ma i documenti linkati sono ancora quelli dell'edizione 2026 e il bando 2027 non c'è. È una gara internazionale su pista; l'impianto organizza una gara a parte per i Master (l'ultima il 23/10/2026, nessuna data 2027). Nessuna voce finché il bando non dice le categorie. La gara era già stata vista nel censimento del 2026-11-17.

## Difetti della fonte visti in questa lettura

- Date sfasate di un giorno tra la scheda e il testo della scheda stessa: Roll'Athlon100 (19/06 contro 20/06, che è la data ufficiale) e FEST CUP Karlsruhe.
- Orari scritti con il fuso orario di New York per eventi europei; nei dati strutturati l'organizzatore è sempre il sito stesso.
- Descrizioni rimaste all'edizione precedente (Bonn: la data del 2026 dentro una scheda intitolata 2027).
- Due maratone di sola corsa presentate come gare sui pattini (Bonn, Salisburgo) e una gara di bici classificata "speed skating".
- Senza il filtro per categoria la ricerca dà 56 eventi, in gran parte pattinate settimanali di città, alcune elencate a stagione finita.
- Copertura: nessuna gara italiana su rotelle; manca la 24 Heures Rollers di Le Mans.

## Dubbi per il proprietario

1. **Duisburg:** la prova è l'ammissione per età (minimo 16 anni, classi per anno di nascita), come per le gare di Berlino; il sito non ha una frase esplicita sui non tesserati e cita il regolamento della federazione tedesca per la misura delle ruote. Se non basta, la voce torna ad `annunciato`.
2. **Roll'Athlon100:** il luogo (Seyssel) viene da una pagina dell'edizione 2025; l'annuncio del 2027 non lo ripete. L'`id` contiene la città: se nel 2027 il villaggio di gara cambiasse, l'`id` resterebbe comunque quello.
3. **Nomi:** per Spreewald e Lausitz la voce si chiama "… – Skate-Marathon" e raccoglie tutte le gare sui pattini dello stesso giorno (una voce sola, decisione del 2026-11-06).
4. **Piste scartate:** sono scritte nella nota della fonte e in questo rapporto, non come voci `escluso` in `dati/eventi.yaml`. Se il proprietario preferisce tenerle lì come memoria, come le uscite escluse delle pattinate, si aggiungono.
5. **arena geisingen international:** resta fuori finché non esce il bando 2027; in alternativa può entrare come `annunciato`.
6. **Ricontrollo:** Rennes e Roll'Athlon100 sono `annunciato` senza prova, quindi entrano nel ricontrollo del martedì (dal 2026-12-08) e contano nel limite di 5 voci per esecuzione.
