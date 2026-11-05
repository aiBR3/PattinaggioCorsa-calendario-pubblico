# Diario: cosa non ha funzionato

Scopo: non risolvere lo stesso problema due volte. Prima di tentare qualcosa, cerca qui.
Una voce per problema: data, cosa si voleva fare, cosa è successo, cosa fare invece.
Quando un problema si risolve per sempre, si aggiorna la voce invece di cancellarla.

## 2026-11-05 — Sessione Claude (web): API GitHub bloccate dal proxy

- **Volevo:** attivare GitHub Pages e leggere le impostazioni di Actions via `gh api`.
- **Successo:** `GET/POST /repos/…/pages`, `/actions/permissions`, `/collaborators` → HTTP 403
  "Access to this GitHub API path is not permitted through this proxy". Anche `gh api`
  verso repository non collegati alla sessione (es. `actions/checkout`) → 403.
- **Invece:** Pages la attiva T dalle impostazioni (Settings → Pages → Source: GitHub
  Actions). Le versioni delle azioni si leggono dalla documentazione GitHub, non dall'API.
  I ruleset invece si leggono (`/rulesets`, `/rules/branches/main`).

## 2026-11-05 — Sessione Claude: GraphQL non disponibile

- **Volevo:** `gh repo view --json …`.
- **Successo:** HTTP 403 "GitHub GraphQL is not available from Claude Code sessions".
- **Invece:** solo REST: `gh api repos/{owner}/{repo}/…`.

## 2026-11-05 — Sessione Claude: estensione Chrome non collegata

- **Volevo:** usare Claude in Chrome (con il login di T) per attivare Pages.
- **Successo:** "Browser extension is not connected".
- **Invece:** per ora le operazioni nell'interfaccia GitHub le fa T. Da riprovare quando
  servirà per Facebook (Fase 4): l'estensione va collegata allo stesso account claude.ai.

## 2026-11-05 — Sessione Claude: WebFetch legge solo URL già comparsi nella conversazione

- **Volevo:** aprire `fisr.info/attivita/corsa_calendario.php` direttamente.
- **Successo:** "URL_NOT_ON_ALLOWLIST".
- **Invece:** prima una ricerca web che faccia comparire l'URL tra i risultati
  (es. `fisr.info corsa_calendario.php`), poi la lettura. Vale anche per le pagine delle
  indizioni (`corsa_trofeo_modulo.php?id_manif=N`).

## 2026-11-05 — fisr.info: la lista non dice le categorie, l'indizione sì

- **Volevo:** capire dalla lista `corsa_calendario.php` quali gare ammettono i Master.
- **Successo:** la lista ha solo data, nome, località, organizzatore, scadenze. Le categorie
  sono nell'indizione (`corsa_trofeo_modulo.php?id_manif=N`, link "modulo" nella riga),
  art. 9-10. Gli eventi "Attività non ancora autorizzata" non hanno ancora il modulo.
  Esempio: Imola 08/11 e 08/12 hanno lo stesso nome e numero (49°), ma solo quella di
  dicembre ha le categorie Master.
- **Invece:** la lista serve a scoprire; la decisione sulle categorie si prende solo
  sull'indizione. La pagina ha errori di codifica ("CITTÃ" per "CITTÀ"): normalizzare i nomi.
