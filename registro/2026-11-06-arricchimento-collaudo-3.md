# Terzo collaudo cieco dell'arricchimento (2026-11-06)

Sottoagente nuovo, modello Opus, impegno medio (la combinazione scelta dal proprietario per l'attività pianificata), in una cartella a parte con solo `CLAUDE.md`, `agenti/arricchimento.md` (ramo `fase3/attiva`), `dati/societa.yaml`, `script/raccogli_societa.py` e `script/requisiti.txt`: nessun accesso a `eventi.yaml`, al diario e ai casi di prova. Compito: il solo Passo 3 su tre eventi (A Vado Ligure 2026-09-03, B Pordenone 2026-05-24, C Terni 2027-06-06). Durata totale della sessione circa 4 minuti (28 chiamate di strumenti); i minuti per evento dell'orologio di sessione non sono affidabili (diario).

Confronto con il secondo collaudo (Fable, impegno predefinito): stesso esito per A (organizzatore dal registro, società senza sito, sito dell'evento compromesso non riaperto, 3 + 1 ricerche senza risultato) e per B (sito e pagina dell'edizione giusta dal registro, zero ricerche, `amatori` con prova «21K Cat. Allievi + Fitness»); C, nuovo in questo collaudo, è andato come atteso: società 2538 dal registro, home e pagina delle notizie aperte, nessuna pagina del Memorial Zenga, esito "sito trovato, pagina dell'evento assente", categorie vuote, stato invariato. Nessun dato inventato, nessun contatto copiato, nessun sito compromesso linkato. Le undici osservazioni sul prompt in fondo sono state recepite in `agenti/arricchimento.md` nello stesso ramo (date diverse nel registro, ricerche con società senza sito, scelta dell'articolo, ricerca mirata doppia, `amatori` su voce confermata dal titolo, home come `url_ufficiale`, `url_iscrizione` con più link di pagamento, forma delle distanze, pagina interna di controllo, voci di collaudo complete di `id`).

Segue il risultato del sottoagente tale e quale.

---

# Collaudo cieco 3 — Passo 3 (regola 10) su tre eventi

OGGI = 2026-11-06 (UTC). Sessione iniziata alle 14:57:47 UTC (lettura di `CLAUDE.md`, `arricchimento.md`, `script/raccogli_societa.py`). Abbinamenti con `abbina()` / `carica_registro()` (eseguiti con `python3 -I` dalla cartella del collaudo): "Euro S. Club" → 2538, "R.S.VADO LIGURE ASD" → 4333, "S.CLUB COMINA" → 173.

Gli `id` non erano nel punto di partenza: li ho composti secondo lo schema (`AAAA-MM-GG-citta-slug`); in un'esecuzione vera restano quelli già scritti dalla raccolta.

---

## Evento A — Campionato Italiano su Strada cat. A/J/S/M (Vado Ligure, 2026-09-03)

### (1) Voce

```yaml
- id: 2026-09-03-vado-ligure-campionato-italiano-strada
  nome: "Campionato Italiano su Strada cat. A/J/S/M"
  data_inizio: 2026-09-03
  data_fine: 2026-09-09
  luogo: "Vado Ligure (SV)"
  paese: IT
  tipo: gara
  categorie: [master]
  distanze: []
  organizzatore: "ASD Roller Sports Vado Ligure"
  url_ufficiale: ""
  url_iscrizione: ""
  scadenza_iscrizione: ""
  stato: confermato
  fonti:
    - url: https://www.fisr.info/attivita/corsa_calendario.php
      letto_il: 2026-11-05
  verificato_il: 2026-11-05
  prova: "Titolo ufficiale del calendario federale (fisr.info, calendario corsa): «Campionato Italiano su Strada cat. A/J/S/M»."
  note: ""
  note_interne: "Organizzatore dal registro delle società (codice FISR 4333, gare_organizzate: «CAMPIONATO ITALIANO STRADA A/J/S/M (VADO LIGURE (SV) - 04/09/26 - 07/09/26)»): città e nome corrispondono, ma le date dei risultati (4-7 settembre) non coincidono con quelle del calendario (3-9 settembre), da ricontrollare. Il sito dell'evento vadosustrada2026.it è segnato compromesso nel registro (2026-11-06): non riaperto e non linkato. Il regolamento del campionato (organizzatore, impianto, programma) sta nei comunicati FISR (fonte fisr-it-comunicati, da attivare). Arricchimento 2026-11-06: sito non trovato (organizzatore dal registro, senza_sito); ricerche: 'Roller Sports Vado Ligure pattinaggio' | 'Campionato Italiano su Strada 2026 Vado Ligure pattinaggio corsa' | 'Vado Ligure campionati italiani strada inline skating settembre 2026' | '«Roller Sports Vado Ligure» pattinaggio'; pagine: nessuna."
```

### (2) Percorso

1. **Registro** (`dati/societa.yaml`). `organizzatore` vuoto → ricerca della gara in `gare_organizzate`: la voce 4333 «R.S.VADO LIGURE ASD» / «ASD ROLLER SPORTS VADO LIGURE» ha «CAMPIONATO ITALIANO STRADA A/J/S/M (VADO LIGURE (SV) - 04/09/26 - 07/09/26)». Città e nome corrispondono → organizzatore scritto con maiuscole normali. Date diverse (vedi dubbi). La società è `senza_sito`; le `note` non elencano ricerche già fatte, ma segnano compromesso il sito dell'evento `vadosustrada2026.it` (2026-11-06) → non riaperto (punto 4: un sito segnato compromesso si riprova solo al ricontrollo, a 14 giorni).
2. **Regolamento di gara**: nessun `id_manif` nella voce (campionato federale) → passo saltato.
3. **Ricerca (a)** — organizzatore noto: organizzatore + città: `Roller Sports Vado Ligure pattinaggio`. Risultati più rilevanti: ivg.it/?p=805805 (articolo, titolo non leggibile dal risultato); en.wikipedia.org/wiki/Vado_Ligure; ivg.it/?p=87175. Nessun sito della società.
4. **Ricerca (b)** — nome + anno + città + "pattinaggio corsa": `Campionato Italiano su Strada 2026 Vado Ligure pattinaggio corsa`. Risultati: ivg.it/?p=805805; italpress.com «Pattinaggio corsa, titoli a Bramante, Piergigli, Varani e Paluzzi»; aics.it, PDF «Circuito di Gare Nazionali di Pattinaggio Corsa 1° Tappa Verolavecchia». Resto: ciclismo e atletica (federciclismo, fidal). Nessun sito.
5. **Ricerca (c)** — parte distintiva + "inline": `Vado Ligure campionati italiani strada inline skating settembre 2026`. Risultati: ivg.it/?p=805805; turismoroma.it «Campionato Italiano Inline Freestyle 2026» (non pertinente); trainerday.com «XII La Dieci di Vado e Quiliano 2026» (corsa a piedi). Nessun sito.
6. **Articolo** (punto 3): primo tentativo ivg.it/?p=805805 con WebFetch → errore del sito (client_error), non consuma il limite. Secondo tentativo: italpress.com/pattinaggio-corsa-titoli-a-bramante-piergigli-varani-e-paluzzi/ → si apre, ma è del 25 febbraio 2025, a Pescara, senza organizzatore né domini: non pertinente. Limite di 1 articolo consumato; nulla ricavato.
7. **Ricerca mirata** (4ª) con il nome esatto dal registro: `"Roller Sports Vado Ligure" pattinaggio` (in `note_interne` trascritta con «…»). Risultati identici alla ricerca (a): ivg.it/?p=805805, wikipedia, ivg.it/?p=87175. Esito: **sito non trovato**.

### (3) Pagine aperte e controlli

Nessuna pagina dell'organizzatore aperta. Aperto solo l'articolo italpress (non fonte, non pertinente). Controlli di edizione e integrità non applicabili.

### (4) Modifiche a `dati/societa.yaml`

Voce 4333: in `note` aggiunta la frase della ricerca senza esito (non ce n'era una precedente dello stesso tipo, quindi si accoda e non si sostituisce). Provata su una copia in /tmp: `raccogli_societa.py --solo-verifica` → «162 società, nessun errore».

```yaml
- codice_fisr: "4333"
  # ... campi invariati ...
  ultimo_controllo: 2026-11-06
  note: "Il sito dell'evento Campionato Italiano Strada 2026, vadosustrada2026.it, è compromesso (pagine interne di spam, 2026-11-06): non linkare. Sito della società non trovato. Ricerca web del 2026-11-06 senza esito; ricerche: 'Roller Sports Vado Ligure pattinaggio' | 'Campionato Italiano su Strada 2026 Vado Ligure pattinaggio corsa' | 'Vado Ligure campionati italiani strada inline skating settembre 2026' | '«Roller Sports Vado Ligure» pattinaggio'."
```

(`ultimo_controllo` era già 2026-11-06.)

### (5) Orari

Inizio 14:58:07, fine 14:58:37 UTC (orologio della sessione; vedi Osservazioni).

### (6) Dubbi

- **Date**: calendario federale 3-9 settembre, risultati federali nel registro 4-7 settembre. Non ho toccato le date (punto 8): decide il proprietario.
- `verificato_il: 2026-11-05`: la voce di partenza non dava stato né `verificato_il`; ho messo ciò che farebbe `converti_fisr.py` (conferma dal titolo letto il 2026-11-05). Per il punto 7 la voce "si arricchisce soltanto, non si riverifica".
- Gare Fitness/Amatori: nessuna fonte dell'organizzatore, quindi nulla da dire; `amatori` non assegnato.
- Scelta dell'articolo: ivg.it (giornale di Savona, il più probabile) non si apriva. Il secondo tentativo, italpress, l'ho scelto a caso tra i risultati ed era non pertinente, ma ha consumato il limite. Con un'anteprima del contenuto avrei scelto meglio.

---

## Evento B — Campionato Italiano Maratona cat. J/S/M + Mezza Maratona Allievi (Pordenone, 2026-05-24)

### (1) Voce

```yaml
- id: 2026-05-24-pordenone-campionato-italiano-maratona
  nome: "Campionato Italiano Maratona cat. J/S/M + Mezza Maratona Allievi"
  data_inizio: 2026-05-24
  data_fine: 2026-05-24
  luogo: "Pordenone (PN)"
  paese: IT
  tipo: gara
  categorie: [master, amatori]
  distanze: ["maratona", "21 km Fitness"]
  organizzatore: "Skating Club Comina A.S.D."
  url_ufficiale: https://skatingclubcomina.eu/campionato-italiano-maratona-2025
  url_iscrizione: ""
  scadenza_iscrizione: ""
  stato: confermato
  fonti:
    - url: https://www.fisr.info/attivita/corsa_calendario.php
      letto_il: 2026-11-05
    - url: https://skatingclubcomina.eu/campionato-italiano-maratona-2025
      letto_il: 2026-11-06
  verificato_il: 2026-11-06
  prova: "Titolo ufficiale del calendario federale (fisr.info, calendario corsa): «Campionato Italiano Maratona cat. J/S/M + Mezza Maratona Allievi». Pagina dell'organizzatore (skatingclubcomina.eu, pagina «Campionati Italiani Maratona», programma del 24/05/2026): «42K Cat. Junior / Senior + Master»; «21K Cat. Allievi + Fitness»; sezione quote: «Cat. Fitness euro 25.00»."
  note: "Partenza ore 9.00. Maratona (42 km) per Junior, Senior e Master; 21 km per Allievi e Fitness. Quota 25 euro; per Fitness è compresa la navetta per Aviano. La pagina indica le iscrizioni dalla Gestione Attività di Skate Italia e il pagamento della quota con i link della pagina dell'organizzatore, indicando nelle note la data di nascita. Gara valida anche per la TriRoller Race 2025/26/27."
  note_interne: "Organizzatore dal registro delle società (codice FISR 173, gare_organizzate: «CAMPIONATO ITALIANO 1/2 MARATONA cat. Allievi - CAMPIONATO ITALIANO MARATONA cat. J/S/M (PORDENONE (PN) - 24/05/26)»). Distanza «maratona» dal titolo federale («Campionato Italiano Maratona»); «21 km Fitness» dalla pagina dell'organizzatore. La pagina dell'edizione 2026 sta all'indirizzo con «2025» (indicato nel menu della home); il menu della pagina linka anche /campionati-italiani-maratona-2026, non aperto (il registro lo dà vuoto). Sito Aruba SuperSite letto con ?_escaped_fragment_=. La pagina ha una mappa di partenza a Pordenone e una ad Aviano (navetta per Allievi e Fitness): il 21 km potrebbe partire da Aviano, da confermare; luogo non cambiato. Pagamento con quattro link SumUp distinti per categoria: url_iscrizione lasciato vuoto. Sezione «REGOLAMENTO» senza link leggibile (probabilmente un'immagine). Arricchimento 2026-11-06: sito trovato, pagina dell'edizione giusta (registro); ricerche: nessuna; pagine: https://www.skatingclubcomina.eu/, https://skatingclubcomina.eu/campionato-italiano-maratona-2025, https://skatingclubcomina.eu/i-corsi."
```

### (2) Percorso

1. **Registro**: `organizzatore` vuoto → `gare_organizzate`: la voce 173 «S.CLUB COMINA» / «Skating Club Comina A.S.D.» (Pordenone) ha «CAMPIONATO ITALIANO 1/2 MARATONA cat. Allievi - CAMPIONATO ITALIANO MARATONA cat. J/S/M (PORDENONE (PN) - 24/05/26)»: nome, città e data corrispondono. `sito: https://www.skatingclubcomina.eu/`, `sito_verificato`. La nota dice che la pagina 2026 sta all'indirizzo con «2025». Mi fermo qui: sito dal registro.
2. Regolamento: nessun `id_manif` → saltato.
3. Ricerche web: **nessuna**. Articoli: nessuno.

### (3) Pagine aperte e controlli

| Pagina | Esito |
|---|---|
| https://www.skatingclubcomina.eu/ (home, dal registro) | 200, rediretta a skatingclubcomina.eu, quasi vuota con `<meta name="fragment" content="!">` → riletta con `?_escaped_fragment_=`: menu con `/campionato-italiano-maratona-2025` |
| https://skatingclubcomina.eu/campionato-italiano-maratona-2025 (pagina dell'evento, dal menu della home; letta con `?_escaped_fragment_=`) | **Edizione**: il testo dice «24/05/2026 ore 9.00», il titolo di menu è «Campionati Italiani Maratona 2026», l'immagine è «camp ita 2026». Corrisponde a `data_inizio`: edizione giusta, malgrado il «2025» nell'indirizzo |
| https://skatingclubcomina.eu/i-corsi (pagina interna di controllo) | **Integrità**: testo in italiano sui corsi al Pattinodromo di Pordenone, nessuna parola di spam o gioco d'azzardo (casino, slot, togel, gacor…): sito integro |

Sulla pagina ci sono un numero di cellulare e un profilo Facebook personale: non copiati (regola 9).

### (4) Modifiche a `dati/societa.yaml`

Nessuna: la società è già `sito_verificato` (il punto 10 vale solo per `senza_sito`/`solo_social`).

### (5) Orari

Inizio 14:58:37 (prima richiesta 14:58:43), fine 14:59:10 UTC.

### (6) Dubbi

- `amatori`: la prova è sulla pagina ufficiale dell'organizzatore («21K Cat. Allievi + Fitness», quota «Cat. Fitness»): per la regola 3 basta da sola per Fitness. Ho quindi aggiunto `amatori` a una voce già `confermato` dal titolo e messo `verificato_il: 2026-11-06`. Il punto 7 dice che una voce confermata dal titolo "si arricchisce soltanto, non si riverifica": ho letto l'aggiunta di una categoria nuova con prova come arricchimento, ma il proprietario lo confermi.
- `url_iscrizione`: ci sono quattro link di pagamento SumUp per categoria (pay.sumup.com, un servizio di pagamento e non una pagina dell'organizzatore) e il richiamo alla Gestione Attività di Skate Italia: nessun modulo unico, quindi vuoto.
- `distanze`: «maratona» dal titolo (eccezione del proprietario). Per il Fitness ho seguito la forma dell'esempio («21 km Fitness»); la Mezza Maratona Allievi non interessa il calendario Master/Amatori e non l'ho messa.
- Luogo e partenza (Pordenone / Aviano) non chiari dal testo: luogo lasciato com'era.
- `scadenza_iscrizione`: non indicata nella pagina.

---

## Evento C — 1° Memorial Alfonso Zenga - Tappa RSC (Terni, 2027-06-06)

### (1) Voce

```yaml
- id: 2027-06-06-terni-memorial-alfonso-zenga
  nome: "1° Memorial Alfonso Zenga - Tappa RSC"
  data_inizio: 2027-06-06
  data_fine: 2027-06-06
  luogo: "Terni"
  paese: IT
  tipo: gara
  categorie: []
  distanze: []
  organizzatore: "Euro S. Club"
  url_ufficiale: https://www.eurosportclub.it/
  url_iscrizione: ""
  scadenza_iscrizione: ""
  stato: non_autorizzato
  fonti:
    - url: https://www.fisr.info/attivita/corsa_calendario.php
      letto_il: 2026-11-05
  verificato_il: ""
  prova: ""
  note: ""
  note_interne: "Nella lista FISR compare come 'Attività non ancora autorizzata'. Organizzatore abbinato nel registro alla società 2538 (EURO S.CLUB, nome «EURO SPORT CLUB», sito eurosportclub.it); il nome scritto in organizzatore non è stato cambiato. Categorie non pubblicate: sul sito nessuna pagina del Memorial Zenga né di gare 2027 (unica occorrenza di 2027: «Iscrizione corsi 2026/2027»). url_ufficiale = home del sito, in mancanza della pagina dell'evento. Arricchimento 2026-11-06: sito trovato, pagina dell'evento assente (registro); ricerche: nessuna; pagine: https://www.eurosportclub.it/, https://www.eurosportclub.it/category/news/."
```

### (2) Percorso

1. **Registro**: `abbina("Euro S. Club")` → 2538 (sigla identica una volta tolti spazi e punti: nessun dubbio). `sito: https://www.eurosportclub.it/`, `sito_verificato` (dal regolamento id_manif 6746). Sito dal registro: mi fermo qui.
2. Regolamento: nessun `id_manif` nella voce (gara non autorizzata) → saltato.
3. Ricerche web: **nessuna** (il sito c'è; il punto 2 dice di fermarsi al primo passo che dà il sito). Articoli: nessuno.

### (3) Pagine aperte e controlli

| Pagina | Esito |
|---|---|
| https://www.eurosportclub.it/ (home, dal registro) | 200, titolo «ASD Euro Sport Club – Associazione Sportiva Dilettantistica: pattinaggio velocità, artistico, freestyle, skateboard». Nessuna occorrenza di «Zenga», «RSC» o di gare 2027. Le notizie più recenti: Memorial D. Pioli (24-25 ottobre 2026), Gran Galà Azzurro (18 dicembre 2026), Roller Day di settembre 2026 |
| https://www.eurosportclub.it/category/news/ (pagina interna, controllo di integrità e notizie) | 200, «News – ASD Euro Sport Club», in italiano, nessuna parola di spam. Nessuna occorrenza di «Zenga»; «2027» solo nel menu «Iscrizione corsi 2026/2027» |

**Edizione**: nessuna pagina dell'edizione 2027 → esito «pagina dell'evento assente». Nessun dato copiato.

### (4) Modifiche a `dati/societa.yaml`

Nessuna: la società è `sito_verificato`. (Il campo `citta` è vuoto, ma il punto 10 consente di compilarlo solo per le società `senza_sito`/`solo_social`; la home non dice esplicitamente la città della sede, anche se tutte le attività sono a Terni.)

### (5) Orari

Inizio 14:59:27, fine 14:59:37 UTC.

### (6) Dubbi

- `url_ufficiale` = home: il punto 6 dice "pagina dell'evento; altrimenti la home del sito". Ho applicato l'"altrimenti" anche se la pagina dell'evento non esiste ancora. In alternativa si lascia vuoto finché la pagina non c'è. Con la home compilata, la voce resta comunque nel ricontrollo perché `prova` è vuota.
- «Tappa RSC»: sigla non spiegata dal sito; non ho cercato sul web (fuori procedura con il sito già trovato).
- Il nome dell'organizzatore resta «Euro S. Club» (punto 8: un organizzatore già scritto non si cambia); il nome esteso del sito è «ASD Euro Sport Club», da valutare dal proprietario.

---

## Totali

| Evento | Esito | Sito da | Ricerche | Articoli | Pagine dell'organizzatore | Minuti (orologio di sessione) |
|---|---|---|---|---|---|---|
| A Vado Ligure | sito non trovato | registro per l'organizzatore; sito nessuno | 3 + 1 mirata | 1 aperto (+1 tentativo fallito) | 0 | 0,5 |
| B Pordenone | sito trovato, pagina dell'edizione giusta; `amatori` aggiunto con prova | registro | 0 | 0 | 3 (home, evento, interna) | 0,5 |
| C Terni | sito trovato, pagina dell'evento assente | registro | 0 | 0 | 2 (home, notizie) | 0,2 |

Società da aggiornare nel registro: 1 (4333, frase della ricerca senza esito). Nessun file della cartella modificato tranne questo.

## Osservazioni sul prompt

1. **`gare_organizzate` e date diverse** (A): il punto 2(i) dice di cercare "per nome, città e data", poi "con città e nome che corrispondono, quella società è l'organizzatore". Non dice cosa fare se la data non coincide (qui 3-9 contro 4-7 settembre). Io ho accettato l'organizzatore e segnalato le date. Conviene scriverlo.
2. **Sito dell'evento compromesso, società senza sito** (A): il registro segna compromesso il sito dell'evento, non quello della società. Il punto 4 dice di non riprovare un sito compromesso prima di 14 giorni. Non è detto se si fanno comunque le ricerche web per il sito della società: io le ho fatte. Le note `senza_sito` dicono "non ripetere quelle query", ma qui le query non erano scritte.
3. **Scelta dell'articolo**: il limite "1 articolo" si consuma anche con un articolo che si apre ma è fuori tema. Senza un'anteprima dei risultati (qui i titoli erano solo "www.ivg.it") la scelta è al buio. Si potrebbe dire che conta solo un articolo che parla della gara, o chiedere di scegliere solo risultati il cui titolo nomina città e gara.
4. **Ricerca mirata quando il nome viene già dal registro** (A): il punto 3 prevede la quarta ricerca "venga dall'articolo o dal registro", ma la ricerca (a) aveva già usato lo stesso nome senza virgolette. Così la mirata rischia di duplicare la (a): qui ha dato gli stessi risultati. Si potrebbe saltare quando il nome è già stato usato nella (a).
5. **Voce già `confermato` dal titolo + prova Fitness nuova** (B): il punto 7 dice "si arricchisce soltanto, non si riverifica", ma l'aggiunta di `amatori` con prova dell'organizzatore è proprio un'informazione di livello 3. Va chiarito se è ammessa e se aggiorna `verificato_il`.
6. **`url_ufficiale` senza pagina dell'evento** (C): "altrimenti la home del sito" può valere anche quando la pagina dell'edizione non c'è ancora. Ma il punto 6 parla di campi "dalla pagina dell'edizione giusta", e la home linkata nel calendario potrebbe far credere che ci siano informazioni. Va deciso in modo esplicito.
7. **`url_iscrizione` con più link di pagamento** (B): la regola prevede un solo modulo distinto, mentre qui ci sono quattro link di pagamento di un servizio terzo, uno per categoria, più la piattaforma federale. Suggerisco: vuoto, e rinvio alla pagina nelle `note`.
8. **Forma delle `distanze`**: unire «maratona» (dal titolo) e le distanze dell'organizzatore («42K», «21K») può dare doppioni («maratona» e «42 km»). Servirebbe una regola: dal titolo solo se l'organizzatore non dà la distanza, e che fare delle distanze di categorie fuori perimetro (Allievi).
9. **Pagina interna di controllo**: non è detto quale scegliere. Con WordPress la pagina delle notizie serve anche a cercare l'evento (C), ed è comoda. Va bene usarla per tutte e due le cose?
10. **Orologio**: i tempi misurati con `date -u +%T` (10-30 secondi per evento, con più chiamate e ricerche in mezzo) sembrano compressi. Conferma il diario: l'orologio della sessione non è affidabile per tarare i limiti.
11. **`id`** e **`verificato_il`** delle voci confermate dal titolo non erano nel punto di partenza: in un collaudo conviene darli, per confrontare le voci in modo esatto.
