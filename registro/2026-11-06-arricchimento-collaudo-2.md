# Arricchimento: secondo collaudo cieco (2026-11-06, prompt con registro delle società)

Dopo le decisioni del proprietario (articolo per il nome + quarta ricerca mirata; regolamento FISR apribile; ricontrollo anche delle voci con prova ma senza link; ordine registro → regolamento → web), lo stesso collaudo cieco del mattino: un sottoagente nuovo con `CLAUDE.md`, il prompt aggiornato, `dati/societa.yaml` e `raccogli_societa.py`, sui casi di prova 1 e 2 con organizzatore ignoto (la lista federale dice "FISR") e senza regolamento. Rapporto integrale nel commento alla PR #38.

| Caso | Atteso | Ottenuto | Via | Ricerche | Articoli | Pagine | Durata |
|---|---|---|---|---|---|---|---|
| 1 Vado Ligure | organizzatore "A.S.D. Roller Sports Vado Ligure", impianto "Stadio Chittolina", sito dell'evento riconosciuto compromesso e non linkato | **superato a metà**: organizzatore trovato nel registro (`gare_organizzate` della voce 4333) e scritto; sito dell'evento non linkato perché il registro lo segna compromesso; impianto non trovato (l'unico articolo utile, ivg.it, risponde 403 Cloudflare); Wayback non raggiunta (ha provato l'API CDX, bloccata) | registro (organizzatore), nessun sito | 3 + 1 mirata | 1 (non leggibile) | 0 | 2 min 24 s |
| 2 Pordenone | `[master, amatori]` con prova dalla pagina del club (Fitness 21 km), organizzatore "Skating Club Comina A.S.D." | **superato**: dal registro (`gare_organizzate` della voce 173) al sito `skatingclubcomina.eu`, pagina dell'evento (quella con "2025" nell'indirizzo, come dice la nota del registro), `[master, amatori]` con prova citata ("21K Cat. Allievi + Fitness", "Cat. Fitness euro 25.00"), organizzatore, link, distanze, orari, quote, note pubbliche; telefono ed email del club non copiati | registro | 0 | 0 | 4 (+1 locandina) | 2 min 37 s |

Lettura iniziale di regole, prompt, script e registro: circa 2 minuti. Totale sessione: circa 7 minuti.

## Cosa si è visto

- Il registro funziona come primo passo anche quando `organizzatore` è vuoto, grazie a `gare_organizzate`; ma per una gara davvero futura quella riga non c'è ancora (viene dai risultati), e l'organizzatore di un campionato sta nel regolamento del campionato nei comunicati FISR: fonte `fisr-it-comunicati`, ancora `da_verificare`. È il prossimo buco da chiudere per i campionati; per i trofei l'organizzatore è nella lista.
- Siti renderizzati via JavaScript (Aruba SuperSite): `curl` restituisce una pagina vuota; con `?_escaped_fragment_=`, parametro che la pagina dichiara per i crawler, il contenuto arriva. Scritto nel prompt e nel diario.
- WebFetch accetta solo indirizzi usciti da una ricerca web: la home presa dal registro si apre solo dalla shell. Wayback: usare l'indirizzo dello snapshot dalla shell, non l'API CDX.
- Discordanza di date per Vado Ligure: calendario fisr.info 03-06/09/2026, risultati federali 04-07/09/2026. Da chiarire a mano.
- Le 12 osservazioni del sottoagente sul prompt sono quasi tutte applicate (registro con organizzatore vuoto; quarta ricerca anche con il nome dal registro; WebFetch e Wayback; `?_escaped_fragment_=`; note delle ricerche fallite nel registro; siti compromessi riprovati al ricontrollo; articoli bloccati non consumano il limite; virgolette nelle query; maiuscole normali; `url_iscrizione` vuoto se l'iscrizione è sulla pagina dell'evento). Aperte: `distanze` dal titolo federale; regolamento del campionato dai comunicati FISR.

## Conclusione

Con il registro delle società l'arricchimento produce, per le gare il cui organizzatore è noto, quello che prima richiedeva una persona: nel caso 2 la voce è completa e la gara Fitness è provata. Resta scoperto il caso "campionato futuro senza organizzatore nella lista": lì serve la fonte dei comunicati FISR (Fase 4). Misure: circa 2,5 minuti per voce; con 5 voci vecchie + le nuove della raccolta l'esecuzione sta sotto la mezz'ora. I limiti provvisori (5, 3+1, 14) reggono.
