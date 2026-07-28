import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

from config import (
    AZ_DOCINT_ENDPOINT,
    AZ_DOCINT_KEY,
    PDF_FILES
)

def estrai_pdf_con_document_intelligence(pdf_path):

    client = DocumentIntelligenceClient(
        endpoint=AZ_DOCINT_ENDPOINT,
        credential=AzureKeyCredential(AZ_DOCINT_KEY)
    )

    with open(pdf_path, "rb") as file:
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=file
        )

    result = poller.result()

    testo = ""
    tabelle = []

    # ESTRAZIONE TESTO

    for page in result.pages:
        if page.lines:
            for line in page.lines:
                testo += line.content + "\n"

    # ESTRAZIONE TABELLE

    if result.tables:
        for table_index, table in enumerate(result.tables):
            tabella = {
                "table_index": table_index,
                "row_count": table.row_count,
                "column_count": table.column_count,
                "cells": []
            }

            for cell in table.cells:
                tabella["cells"].append({
                    "row_index": cell.row_index,
                    "column_index": cell.column_index,
                    "content": cell.content
                })

            tabelle.append(tabella)

    dati_pdf = {
        "pdf_path": pdf_path,
        "testo": testo,
        "tabelle": tabelle
    }

    return dati_pdf


def stampa_risultato_pdf(dati_pdf):
    """
    Stampa un riassunto leggibile del risultato OCR.
    """

    print("\n==============================")
    print("PDF ANALIZZATO")
    print("==============================")
    print("File:", dati_pdf["pdf_path"])

    print("\n--- TESTO ESTRATTO, primi 1500 caratteri ---")
    print(dati_pdf["testo"][:1500])

    print("\n--- TABELLE TROVATE ---")
    print("Numero tabelle:", len(dati_pdf["tabelle"]))

    for tabella in dati_pdf["tabelle"]:
        print("\nTabella:", tabella["table_index"])
        print("Righe:", tabella["row_count"])
        print("Colonne:", tabella["column_count"])

        for cella in tabella["cells"][:20]:
            print(
                f"riga={cella['row_index']} | "
                f"colonna={cella['column_index']} | "
                f"contenuto={cella['content']}"
            )


def salva_ocr_json(dati_pdf, output_file):
    """
    Salva il risultato OCR in un file JSON.
    Utile per controllare cosa ha letto Azure.
    """

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(dati_pdf, file, ensure_ascii=False, indent=4)


def test_pdf_extractor():
    for pdf_file in PDF_FILES:
        print("\nAnalizzo PDF:", pdf_file)

        dati_pdf = estrai_pdf_con_document_intelligence(pdf_file)
        stampa_risultato_pdf(dati_pdf)


if __name__ == "__main__":
    test_pdf_extractor()