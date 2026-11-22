# Prova della protezione di `main` (2026-11-22)

Scopo: dopo la modifica del ruleset "Protezione su main" fatta dal proprietario il 2026-11-22, verificare che su `main` possa fondere solo lui e che un'approvazione decada quando arrivano commit nuovi. La pull request che porta questo file tocca solo `registro/`, che in `CODEOWNERS` non ha un responsabile: prima della modifica chiunque avesse accesso in scrittura avrebbe potuto fonderla senza approvazione.

## Ruleset letto dall'API con l'account di Claude

- Regole attive su `main`: `deletion`, `non_fast_forward`, `creation`, `pull_request`, `update`. La regola `update` è "Restrict updates", aggiunta oggi.
- Parametri di `pull_request`: `required_approving_review_count: 0`, `require_code_owner_review: true`, `dismiss_stale_reviews_on_push: true` (attivata oggi), `require_last_push_approval: false`.
- Per l'account di Claude l'API risponde `current_user_can_bypass: never`. L'elenco di chi può scavalcare le regole non è leggibile senza permessi di amministratore.

## Prove

Fatte sulla pull request #69, aperta dall'account di Claude. Nessun tentativo di merge da parte dell'account di Claude: gli esiti sono letti dall'API.

| N. | Prova | Atteso | Esito |
|---|---|---|---|
| 1 | Stato della PR visto dall'account di Claude, senza approvazioni | bloccata | `mergeable_state: blocked` con nessun revisore richiesto: il blocco viene da "Restrict updates" |
| 2 | Lo stesso stato dopo l'approvazione del proprietario | ancora bloccata per l'account di Claude | `blocked` anche con la revisione `APPROVED` del proprietario: l'approvazione non permette a un altro account di fondere |
| 3 | Un commit nuovo dell'account di Claude dopo l'approvazione | l'approvazione decade | la revisione del proprietario passa da `APPROVED` a `DISMISSED` subito dopo il push |

La quarta prova è il merge di questa pull request da parte del proprietario: la presenza di questo file su `main` ne è l'esito. Come si presenta il merge (avviso, spunta per scavalcare le regole) è annotato nella riga del 2026-11-22 di `appunti/decisioni.md`, che arriva con una pull request a parte.
