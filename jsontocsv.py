import os
import json
import csv

from config import OUTPUT_PATH


CARTELLA_JSON_VALIDATI = f"{OUTPUT_PATH}/ORDINE_VALIDATO"

ORDINI_CSV = f"{OUTPUT_PATH}/ordini_validati.csv"
RIGHE_CSV = f"{OUTPUT_PATH}/righe_ordini_validati.csv"


def leggi_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def converti_float(valore):
    try:
        return float(valore)
    except:
        return 0.0


def converti_json_validati_in_csv():
    ordini = []
    righe_ordini = []

    if not os.path.exists(CARTELLA_JSON_VALIDATI):
        print("Cartella non trovata:", CARTELLA_JSON_VALIDATI)
        return

    file_json = []

    for nome_file in os.listdir(CARTELLA_JSON_VALIDATI):
        if nome_file.endswith(".json"):
            file_json.append(nome_file)

    if len(file_json) == 0:
        print("Nessun JSON trovato in:", CARTELLA_JSON_VALIDATI)
        return

    for nome_file in file_json:
        file_path = f"{CARTELLA_JSON_VALIDATI}/{nome_file}"

        dati = leggi_json(file_path)

        ordine_json = dati.get("ordine")

        if ordine_json is None:
            print("File ignorato, ordine mancante:", nome_file)
            continue

        fonte = dati.get("fonte", "")
        pdf_file = dati.get("pdf_file", "")
        esito_operativo = dati.get("esito_operativo", "")

        cliente = ordine_json.get("cliente", {})
        testata = ordine_json.get("ordine", {})
        righe = ordine_json.get("righe", [])

        id_ordine = fonte

        ordini.append({
            "id_ordine": id_ordine,
            "fonte": fonte,
            "pdf_file": pdf_file,
            "esito_operativo": esito_operativo,
            "id_cliente": cliente.get("id_cliente", ""),
            "ragione_sociale": cliente.get("ragione_sociale", ""),
            "partita_iva": cliente.get("partita_iva", ""),
            "email": cliente.get("email", ""),
            "cliente_originale_pdf": cliente.get("cliente_originale_pdf", ""),
            "data_ordine": testata.get("data_ordine", ""),
            "riferimento_cliente": testata.get("riferimento_cliente", ""),
            "riferimento_originale_pdf": testata.get("riferimento_originale_pdf", ""),
            "note_ordine": testata.get("note_ordine", "")
        })

        for riga in righe:
            quantita = converti_float(riga.get("quantita"))
            prezzo_unitario = converti_float(riga.get("prezzo_unitario"))
            importo_riga = quantita * prezzo_unitario

            righe_ordini.append({
                "id_ordine": id_ordine,
                "fonte": fonte,
                "numero_riga": riga.get("numero_riga", ""),
                "codice_articolo": riga.get("codice_articolo", ""),
                "codice_originale_pdf": riga.get("codice_originale_pdf", ""),
                "descrizione_articolo": riga.get("descrizione_articolo", ""),
                "descrizione_originale_pdf": riga.get("descrizione_originale_pdf", ""),
                "quantita": quantita,
                "quantita_originale_pdf": riga.get("quantita_originale_pdf", ""),
                "prezzo_unitario": prezzo_unitario,
                "prezzo_originale_pdf": riga.get("prezzo_originale_pdf", ""),
                "importo_riga": round(importo_riga, 2),
                "note_riga": riga.get("note_riga", "")
            })

    if len(ordini) > 0:
        with open(ORDINI_CSV, "w", encoding="utf-8", newline="") as file:
            colonne_ordini = ordini[0].keys()
            writer = csv.DictWriter(file, fieldnames=colonne_ordini)
            writer.writeheader()
            writer.writerows(ordini)

    if len(righe_ordini) > 0:
        with open(RIGHE_CSV, "w", encoding="utf-8", newline="") as file:
            colonne_righe = righe_ordini[0].keys()
            writer = csv.DictWriter(file, fieldnames=colonne_righe)
            writer.writeheader()
            writer.writerows(righe_ordini)

    print("\nConversione completata.")
    print("Ordini esportati:", len(ordini))
    print("Righe ordine esportate:", len(righe_ordini))
    print("CSV ordini:", ORDINI_CSV)
    print("CSV righe:", RIGHE_CSV)


if __name__ == "__main__":
    converti_json_validati_in_csv()