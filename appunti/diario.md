# Diario: cosa non ha funzionato

Scopo: non risolvere lo stesso problema due volte. Prima di tentare qualcosa, cerca qui.
Una voce per problema: data, cosa si voleva fare, cosa è successo, cosa fare invece.
Quando un problema si risolve per sempre, si aggiorna la voce invece di cancellarla.

## 2026-11-05 — Sessione Claude (web): API GitHub bloccate dal proxy

- **Volevo:** attivare GitHub Pages e leggere le impostazioni di Actions via `gh api`.
- **Successo:** `GET/POST /repos/…/pages`, `/actions/permissions`, `/collaborators` → HTTP 403
  "Access to this GitHub API path is not permitted through this proxy". Anche `gh api`
  verso repository non collegati alla sessione (es. `actions/checkout`) → 403.
- **Invece:** Pages la attiva il proprietario dalle impostazioni (Settings → Pages → Source: GitHub
  Actions). Le versioni delle azioni si leggono dalla documentazione GitHub, non dall'API.
  I ruleset invece si leggono (`/rulesets`, `/rules/branches/main`).

## 2026-11-05 — Sessione Claude: GraphQL non disponibile

- **Volevo:** `gh repo view --json …`.
- **Successo:** HTTP 403 "GitHub GraphQL is not available from Claude Code sessions".
- **Invece:** solo REST: `gh api repos/{owner}/{repo}/…`.

## 2026-11-05 — Sessione Claude: estensione Chrome non collegata

- **Volevo:** usare Claude in Chrome (con il login del proprietario) per attivare Pages.
- **Successo:** "Browser extension is not connected".
- **Invece:** per ora le operazioni nell'interfaccia GitHub le fa il proprietario. Da riprovare quando
  servirà per Facebook (Fase 4): l'estensione va collegata allo stesso account claude.ai.

## 2026-11-05 — Sessione Claude: WebFetch legge solo URL già comparsi nella conversazione

- **Volevo:** aprire `fisr.info/attivita/corsa_calendario.php` direttamente.
- **Successo:** "URL_NOT_ON_ALLOWLIST".
- **Invece:** prima una ricerca web che faccia comparire l'URL tra i risultati
  (es. `fisr.info corsa_calendario.php`), poi la lettura. Vale anche per le pagine delle
  regolamenti di gara (`corsa_trofeo_modulo.php?id_manif=N`).

## 2026-11-05 — fisr.info: i link ai regolamenti di gara spariscono, ma le pagine restano

- **Volevo:** leggere il regolamento di gara di tutte le gare dal 1° gennaio 2026.
- **Successo:** nella lista solo 3 gare su 66 avevano il link 'modulo' (quelle future). Le pagine
  `corsa_trofeo_modulo.php?id_manif=N` però esistono ancora, anche per le gare 'non ancora
  autorizzate' (es. 7047 = L'Aquila 06/12/2026). Gli id non sono cronologici e molti sono vuoti o bozze
  (`[[denom]]`, date mancanti).
- **Invece:** `raccogli_fisr.py --scansione-regolamenti 6300 7100` scarica tutto l'intervallo (≈800
  richieste, ~10 minuti con pausa 0,2 s), tiene solo i regolamenti di gara completi nel periodo, e
  `converti_fisr.py` le abbina alle righe per data (±1 giorno) e somiglianza del nome o dell'organizzatore.
  Trovati 46 regolamenti di gara completi per il 2026.

## 2026-11-05 — fisr.info: trappole nella lista

- `?anno=2026` restituisce la stagione 2025/26 **più** i mesi già noti della 2026/27: chiedere anche
  `?anno=2027` produce righe doppie.
- Campionati e attività nazionale stanno in righe a 2 celle (`nome - località`, a volte `-Torino`
  senza spazio), spesso ripetute accanto alla riga a 7 celle con date leggermente diverse (04-07/06 vs
  05-07/06). `converti_fisr.py` le unisce (stessa data ±2 giorni e nomi simili).
- Un nome era in **base64** nella fonte (`MbBtYWdnaW8g…` = "1°maggio Ferrara Inlne…"): decodificato.
- Lo stesso evento può comparire due volte con nomi diversi (Cardano al Campo 12-13/09 e 13/09) o
  con la stessa numerazione in due date (Montesilvano 13/09 e 04/10; Imola 08/11 e 08/12, entrambe "49°").
- Le pagine dei regolamenti di gara hanno codifica mista: decodificare come cp1252 e riparare il mojibake
  UTF-8 parola per parola.

## 2026-11-05 — fisr.info: la lista non dice le categorie, il regolamento di gara sì

- **Volevo:** capire dalla lista `corsa_calendario.php` quali gare ammettono i Master.
- **Successo:** la lista ha solo data, nome, località, organizzatore, scadenze. Le categorie
  sono nel regolamento di gara (`corsa_trofeo_modulo.php?id_manif=N`, link "modulo" nella riga),
  art. 9-10. Gli eventi "Attività non ancora autorizzata" non hanno ancora il modulo.
  Esempio: Imola 08/11 e 08/12 hanno lo stesso nome e numero (49°), ma solo quella di
  dicembre ha le categorie Master.
- **Invece:** la lista serve a scoprire; la decisione sulle categorie si prende solo
  sul regolamento di gara. La pagina ha errori di codifica ("CITTÃ" per "CITTÀ"): normalizzare i nomi.
