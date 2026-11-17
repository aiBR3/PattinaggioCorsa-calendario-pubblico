#!/usr/bin/env python3
"""
prove_converti_fisr.py — prove automatiche di converti_fisr.py su casi costruiti.

Non legge la rete e non tocca dati/eventi.yaml: costruisce righe di lista e regolamenti
di gara finti e controlla come converti_fisr.py riconosce una voce esistente e cosa fa
quando un regolamento cambia (regola 7 di CLAUDE.md). Il caso reale da cui nascono queste
regole (L'Aquila 2027, regolamento 7073) è il caso 6 di appunti/casi-di-prova.md.

Uso:
    python3 script/prove_converti_fisr.py

Esce con 0 se tutte le prove passano, con 1 alla prima che fallisce (dopo averle elencate tutte).
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

PERCORSO_SCRIPT = Path(__file__).resolve().parent / "converti_fisr.py"
if not PERCORSO_SCRIPT.is_file():
    sys.exit(f"Non trovo {PERCORSO_SCRIPT}: questo file va tenuto accanto a converti_fisr.py")
specifica = importlib.util.spec_from_file_location("converti_fisr", PERCORSO_SCRIPT)
if specifica is None or specifica.loader is None:
    sys.exit(f"Non riesco a caricare {PERCORSO_SCRIPT}")
convertitore = importlib.util.module_from_spec(specifica)
specifica.loader.exec_module(convertitore)

FUNZIONI_ATTESE = ("costruisci_evento", "corrisponde_esistente", "promuovi", "aggiorna_dal_regolamento",
                   "segnala_possibili_doppioni", "emetti_evento", "numeri_regolamento", "aggiorna_nome", "normalizza_nome")
mancanti = [nome for nome in FUNZIONI_ATTESE if not callable(getattr(convertitore, nome, None))]
if mancanti:
    sys.exit(f"converti_fisr.py non ha più le funzioni {mancanti}: le prove vanno aggiornate insieme allo script")


def regolamento_finto(numero: str, categorie: list[str], dal: str = "2027-03-10", al: str = "2027-03-10", entro: str = "2027-03-05") -> dict:
    righe = [{"categoria": categoria, "sesso": sesso, "distanza": "3000 m", "tipo": "punti"} for categoria in categorie for sesso in ("F", "M")]
    return {"id_manif": numero, "url": f"https://www.fisr.info/attivita/corsa_trofeo_modulo.php?id_manif={numero}", "scaricata": True,
            "denominazione": "1° Trofeo di Prova", "dal": dal, "al": al, "societa": "A.S.D. PROVA", "campo_gara": "Pista di prova.",
            "categoria_manifestazione": "B", "disciplina": "pista", "iscrizioni_entro": entro, "righe_programma": righe,
            "categorie_programma": list(categorie), "righe_master_amatori": []}


def riga_finta(data: str = "2027-03-10", non_autorizzata: bool = False, titolo: str = "1° Trofeo di Prova") -> dict:
    return {"evento": titolo, "data_inizio": data, "data_fine": data, "localita": "PROVA", "organizzatore": "A.S.D. PROVA",
            "non_autorizzata": non_autorizzata, "anomalie": [], "scadenza_iscrizioni": "", "stagione": "2026/27", "id_manif": "",
            "formato": "7_celle", "data_grezza": data}


def voce_scritta(proposta: dict) -> dict:
    """La proposta come finirebbe in eventi.yaml: senza i campi di lavoro (quelli che iniziano con '_')."""
    return {chiave: copy.deepcopy(valore) for chiave, valore in proposta.items() if not chiave.startswith("_")}


esiti: list[bool] = []


def verifica(nome: str, condizione: bool, dettaglio: object = "") -> None:
    esiti.append(bool(condizione))
    print(("ok       " if condizione else "FALLITA  ") + nome + (f" — {dettaglio}" if dettaglio != "" and not condizione else ""))


def principale() -> int:
    c = convertitore

    # 1. Regolamento cambiato: gara esclusa che ora ammette i Master e parte un giorno prima (come L'Aquila 2027)
    voce = voce_scritta(c.costruisci_evento(riga_finta("2027-03-10"), regolamento_finto("9000", ["ALLIEVI"]), "2026-11-01"))
    id_vecchio = voce["id"]
    proposta = c.costruisci_evento(riga_finta("2027-03-09", non_autorizzata=True),
                                   regolamento_finto("9000", ["ALLIEVI", "MASTER OVER 30"], dal="2027-03-09", al="2027-03-10", entro="2027-03-04"), "2026-11-16")
    verifica("1. riconosciuta dal numero del regolamento anche con la data cambiata", c.corrisponde_esistente(proposta, [voce]) is voce)
    cambiamenti, dubbi = c.aggiorna_dal_regolamento(voce, proposta, "2026-11-16", {id_vecchio})
    verifica("1. categorie, stato e prova seguono il regolamento", voce["categorie"] == ["master"] and voce["stato"] == "non_autorizzato" and "MASTER OVER 30" in voce["prova"], voce)
    verifica("1. date e scadenza seguono il regolamento", (str(voce["data_inizio"]), str(voce["scadenza_iscrizione"])) == ("2027-03-09", "2027-03-04"), voce)
    verifica("1. la data nell'id segue data_inizio", voce["id"] == "2027-03-09" + id_vecchio[10:], voce["id"])
    verifica("1. il cambio è scritto in note_interne", "Aggiornata il 2026-11-16 da converti_fisr.py" in voce["note_interne"] and id_vecchio in voce["note_interne"])
    verifica("1. nome, luogo e organizzatore non cambiano", (voce["nome"], voce["luogo"], voce["organizzatore"]) == ("1° Trofeo di Prova", "Prova", "A.S.D. Prova"), voce)
    prima = copy.deepcopy(voce)
    verifica("1. una seconda lettura uguale non cambia nulla", c.aggiorna_dal_regolamento(voce, proposta, "2026-11-23", {voce["id"]}) == ([], []) and voce == prima)

    # 2. Prova scritta a mano: non si riscrive, si segnala (una volta sola)
    voce = voce_scritta(c.costruisci_evento(riga_finta(), regolamento_finto("9001", ["ALLIEVI"]), "2026-11-01"))
    voce["prova"] = "Regolamento, art. 9-10: categorie ammesse Allievi."
    proposta = c.costruisci_evento(riga_finta(), regolamento_finto("9001", ["ALLIEVI", "MASTER OVER 30"]), "2026-11-16")
    cambiamenti, dubbi = c.aggiorna_dal_regolamento(voce, proposta, "2026-11-16", {voce["id"]})
    verifica("2. prova a mano: categorie e stato restano", not cambiamenti and voce["categorie"] == [] and voce["stato"] == "escluso", cambiamenti)
    verifica("2. prova a mano: segnalata in note_interne", len(dubbi) == 1 and "Da controllare (converti_fisr.py)" in voce["note_interne"], dubbi)
    nota = voce["note_interne"]
    c.aggiorna_dal_regolamento(voce, proposta, "2026-11-23", {voce["id"]})
    verifica("2. la segnalazione non si ripete ogni settimana", voce["note_interne"] == nota)

    # 3. 'amatori' dalla pagina dell'organizzatore resta quando il regolamento toglie i Master
    voce = voce_scritta(c.costruisci_evento(riga_finta(), regolamento_finto("9002", ["ALLIEVI", "MASTER OVER 30"]), "2026-11-01"))
    voce["categorie"] = ["master", "amatori"]
    voce["prova"] += " Pagina dell'organizzatore, sezione 'Programma': '21K Fitness'."
    proposta = c.costruisci_evento(riga_finta(), regolamento_finto("9002", ["ALLIEVI"]), "2026-11-16")
    c.aggiorna_dal_regolamento(voce, proposta, "2026-11-16", {voce["id"]})
    verifica("3. resta 'amatori', va via 'master'", voce["categorie"] == ["amatori"], voce["categorie"])
    verifica("3. la prova dell'organizzatore resta accanto alla frase nuova", "nessuna riga Master o Amatori." in voce["prova"] and voce["prova"].endswith("'21K Fitness'."), voce["prova"])
    verifica("3. con una categoria rimasta lo stato resta confermato", voce["stato"] == "confermato", voce["stato"])

    # 4. Il regolamento toglie i Master a una gara confermata: esclusa; le distanze vecchie si segnalano, non si cancellano
    voce = voce_scritta(c.costruisci_evento(riga_finta(), regolamento_finto("9003", ["MASTER OVER 30"]), "2026-11-01"))
    proposta = c.costruisci_evento(riga_finta(), regolamento_finto("9003", ["ALLIEVI"]), "2026-11-16")
    cambiamenti, dubbi = c.aggiorna_dal_regolamento(voce, proposta, "2026-11-16", {voce["id"]})
    verifica("4. confermato → escluso", voce["stato"] == "escluso" and voce["categorie"] == [], (voce["stato"], voce["categorie"]))
    verifica("4. distanze vecchie segnalate, non cancellate", voce["distanze"] != [] and any("distanze" in dubbio for dubbio in dubbi), dubbi)

    # 5. Riga senza regolamento con la data cambiata: non si unisce, si scrive il sospetto
    vecchia = voce_scritta(c.costruisci_evento(riga_finta("2027-03-10"), None, "2026-11-01"))
    nuova = c.costruisci_evento(riga_finta("2027-03-17"), None, "2026-11-16")
    verifica("5. senza numero di regolamento una data diversa non viene riconosciuta", c.corrisponde_esistente(nuova, [vecchia]) is None)
    segnalazioni = c.segnala_possibili_doppioni([nuova], [vecchia], set(), "2026-11-02")
    verifica("5. sospetto di doppione scritto nella voce nuova", len(segnalazioni) == 1 and "Possibile doppione di " + vecchia["id"] in nuova["note_interne"], segnalazioni)
    altra = c.costruisci_evento(riga_finta("2027-03-17"), None, "2026-11-16")
    verifica("5. nessun sospetto se la voce vecchia è ancora in lista (due gare vere con lo stesso nome)", c.segnala_possibili_doppioni([altra], [vecchia], {id(vecchia)}, "2026-11-02") == [])

    # 6. Autorizza solo la lista: un regolamento senza riga in lista non promuove una voce non_autorizzato
    voce = voce_scritta(c.costruisci_evento(riga_finta(non_autorizzata=True), regolamento_finto("9005", ["MASTER OVER 30"]), "2026-11-01"))
    verifica("6. premessa: non_autorizzato con prova", voce["stato"] == "non_autorizzato" and bool(voce["prova"]), voce["stato"])
    solo_regolamento = c.costruisci_evento(None, regolamento_finto("9005", ["MASTER OVER 30"]), "2026-11-16")
    verifica("6. riconosciuta dal numero anche senza riga in lista", c.corrisponde_esistente(solo_regolamento, [voce]) is voce)
    verifica("6. senza la lista nessuna promozione", c.promuovi(voce, solo_regolamento, "2026-11-16") == [] and voce["stato"] == "non_autorizzato", voce["stato"])
    dalla_lista = c.costruisci_evento(riga_finta(non_autorizzata=False), regolamento_finto("9005", ["MASTER OVER 30"]), "2026-11-16")
    c.promuovi(voce, dalla_lista, "2026-11-16")
    verifica("6. promossa quando la lista non la segna più come non autorizzata", voce["stato"] == "confermato", voce["stato"])

    # 7. Cambio di data con l'id nuovo già occupato
    voce = voce_scritta(c.costruisci_evento(riga_finta("2027-03-10"), regolamento_finto("9006", ["MASTER OVER 30"]), "2026-11-01"))
    proposta = c.costruisci_evento(riga_finta("2027-03-12"), regolamento_finto("9006", ["MASTER OVER 30"], dal="2027-03-12", al="2027-03-12"), "2026-11-16")
    occupati = {voce["id"], "2027-03-12" + voce["id"][10:]}
    c.aggiorna_dal_regolamento(voce, proposta, "2026-11-16", occupati)
    verifica("7. l'id nuovo non ne copre un altro", voce["id"] == "2027-03-12" + proposta["id"][10:] + "-2", voce["id"])

    # 8. Voce legata a un altro regolamento: non si tocca
    voce = voce_scritta(c.costruisci_evento(riga_finta(), regolamento_finto("9007", ["ALLIEVI"]), "2026-11-01"))
    proposta = c.costruisci_evento(riga_finta(), regolamento_finto("9099", ["MASTER OVER 30"]), "2026-11-16")
    prima = copy.deepcopy(voce)
    verifica("8. regolamento diverso: nessun cambio", c.aggiorna_dal_regolamento(voce, proposta, "2026-11-16", {voce["id"]}) == ([], []) and voce == prima)

    # 9. I campi di lavoro non finiscono in eventi.yaml
    testo = c.emetti_evento(proposta)
    verifica("9. nessun campo di lavoro nel testo scritto", not any(chiave in testo for chiave in proposta if chiave.startswith("_")), testo)

    # 10. Voce nata dalla sola lista (senza prova); poi arriva il regolamento, che dà un'altra data d'inizio
    voce = voce_scritta(c.costruisci_evento(riga_finta("2027-03-10", non_autorizzata=True), None, "2026-11-01"))
    id_vecchio = voce["id"]
    proposta = c.costruisci_evento(riga_finta("2027-03-10"), regolamento_finto("9010", ["MASTER OVER 30"], dal="2027-03-11", al="2027-03-11"), "2026-11-16")
    verifica("10. riconosciuta dalla data della lista anche se il regolamento ne dà un'altra", c.corrisponde_esistente(proposta, [voce]) is voce, proposta["id"])
    promozione = c.promuovi(voce, proposta, "2026-11-16")
    cambiamenti, dubbi = c.aggiorna_dal_regolamento(voce, proposta, "2026-11-16", {id_vecchio})
    verifica("10. promossa con la prova del regolamento", bool(promozione) and voce["categorie"] == ["master"] and voce["stato"] == "confermato", promozione)
    verifica("10. una volta legata al regolamento ne segue la data, e l'id con lei", str(voce["data_inizio"]) == "2027-03-11" and voce["id"].startswith("2027-03-11-"), (voce["id"], cambiamenti))

    # 11. Il nome segue la fonte quando la lista federale cambia il titolo (e solo allora)
    voce = voce_scritta(c.costruisci_evento(riga_finta(titolo="GRAN PREMIO DI PROVA - VI Memorial Tizio Caio"), regolamento_finto("9011", ["MASTER OVER 30"]), "2026-11-01"))
    voce["nome"] = "Gran Premio di Prova — VI Memorial Tizio Caio"       # ritoccato a mano
    id_prima = voce["id"]
    stessa = c.costruisci_evento(riga_finta(titolo="Gran premio  di prova - VI MEMORIAL TIZIO CAIO Attivita' non ancora autorizzata"), regolamento_finto("9011", ["MASTER OVER 30"]), "2026-11-09")
    verifica("11. stesse parole (cambiano solo maiuscole, spazi e la dicitura 'non autorizzata'): il ritocco a mano resta",
             c.aggiorna_nome(voce, stessa, "2026-11-09", True) == ([], False) and voce["nome"] == "Gran Premio di Prova — VI Memorial Tizio Caio", voce["nome"])
    cambiata = c.costruisci_evento(riga_finta(titolo="MEMORIAL TIZIO CAIO - GRAN PREMIO DI PROVA - VII edizione"), regolamento_finto("9011", ["MASTER OVER 30"]), "2026-11-16")
    rinomina, registrato = c.aggiorna_nome(voce, cambiata, "2026-11-16", True)
    verifica("11. titolo cambiato: il nome diventa quello nuovo, con maiuscole normali", bool(rinomina) and voce["nome"] == "Memorial Tizio Caio - Gran Premio di Prova - VII edizione", voce["nome"])
    verifica("11. nome_fonte ricorda il titolo nuovo com'è nella fonte", voce["nome_fonte"] == "MEMORIAL TIZIO CAIO - GRAN PREMIO DI PROVA - VII edizione", voce["nome_fonte"])
    verifica("11. il nome vecchio resta scritto in note_interne e l'id non cambia", "Gran Premio di Prova — VI Memorial Tizio Caio" in voce["note_interne"] and voce["id"] == id_prima, voce["id"])
    verifica("11. una seconda lettura uguale non cambia nulla", c.aggiorna_nome(voce, cambiata, "2026-11-23", True) == ([], False))

    # 12. Prima lettura: il titolo si registra, il nome non cambia
    voce = voce_scritta(c.costruisci_evento(riga_finta(titolo="1° Trofeo di Prova"), None, "2026-11-01"))
    voce["nome"], voce["nome_fonte"] = "Primo Trofeo di Prova (a mano)", ""
    proposta = c.costruisci_evento(riga_finta(titolo="1° TROFEO DI PROVA BIS"), None, "2026-11-16")
    rinomina, registrato = c.aggiorna_nome(voce, proposta, "2026-11-16", True)
    verifica("12. nome_fonte vuoto: titolo registrato, nome intatto", rinomina == [] and registrato and voce["nome"] == "Primo Trofeo di Prova (a mano)" and voce["nome_fonte"] == "1° TROFEO DI PROVA BIS", voce)

    # 13. Più righe della lista per la stessa voce, o proposta dal solo regolamento: il nome non si tocca
    voce = voce_scritta(c.costruisci_evento(riga_finta(titolo="Trofeo Alfa"), None, "2026-11-01"))
    prima = copy.deepcopy(voce)
    altra_gara = c.costruisci_evento(riga_finta(titolo="Trofeo Beta"), None, "2026-11-16")
    verifica("13. due righe per la stessa voce: non si sceglie un titolo", c.aggiorna_nome(voce, altra_gara, "2026-11-16", False) == ([], False) and voce == prima)
    solo_regolamento = c.costruisci_evento(None, regolamento_finto("9013", ["MASTER OVER 30"]), "2026-11-16")
    verifica("13. proposta dal solo regolamento: il nome non si tocca", c.aggiorna_nome(voce, solo_regolamento, "2026-11-16", True) == ([], False) and voce == prima)

    # 14. Maiuscole tratto per tratto, e posizione del campo nel file
    verifica("14. titolo maiuscolo solo in parte", c.normalizza_nome("INTERNAZIONALI D'ITALIA OPEN INDOOR -VII Memorial Tizio Caio") == "Internazionali d'Italia Open Indoor - VII Memorial Tizio Caio",
             c.normalizza_nome("INTERNAZIONALI D'ITALIA OPEN INDOOR -VII Memorial Tizio Caio"))
    verifica("14. un titolo già scritto bene resta com'è", c.normalizza_nome("3° Trofeo della Befana - Tappa GPG") == "3° Trofeo della Befana - Tappa GPG", c.normalizza_nome("3° Trofeo della Befana - Tappa GPG"))
    righe_scritte = c.emetti_evento(altra_gara).split("\n")
    verifica("14. nome_fonte è scritto subito dopo nome", righe_scritte[1].startswith("  nome: ") and righe_scritte[2] == '  nome_fonte: "Trofeo Beta"', righe_scritte[:3])

    superate = sum(esiti)
    print(f"\n{superate}/{len(esiti)} prove superate")
    if not esiti:
        print("ERRORE: nessuna prova eseguita", file=sys.stderr)
        return 1
    return 0 if superate == len(esiti) else 1


if __name__ == "__main__":
    sys.exit(principale())
