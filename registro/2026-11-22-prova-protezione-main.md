# Prova della protezione di `main` (2026-11-22)

Scopo: dopo la modifica del ruleset "Protezione su main" fatta dal proprietario il 2026-11-22, verificare che su `main` possa fondere solo lui e che un'approvazione decada quando arrivano commit nuovi. La pull request che porta questo file tocca solo `registro/`, che in `CODEOWNERS` non ha un responsabile: prima della modifica chiunque avesse accesso in scrittura avrebbe potuto fonderla senza approvazione.

## Ruleset letto dall'API con l'account di Claude

- Regole attive su `main`: `deletion`, `non_fast_forward`, `creation`, `pull_request`, `update`. La regola `update` è "Restrict updates", aggiunta oggi.
- Parametri di `pull_request`: `required_approving_review_count: 0`, `require_code_owner_review: true`, `dismiss_stale_reviews_on_push: true` (attivata oggi), `require_last_push_approval: false`.
- Per l'account di Claude l'API risponde `current_user_can_bypass: never`. L'elenco di chi può scavalcare le regole non è leggibile senza permessi di amministratore.
