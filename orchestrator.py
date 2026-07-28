import os
import json
from config import (PDF_FILES,OUTPUT_PATH,load_csv_files)
#from load_data import load_csv_files
from pdf_extractor import estrai_pdf_con_document_intelligence
from mapperOpenAI import (
    classifica_richiesta_con_agente,
    estrai_ordine_con_agente,
    analizza_revisione_con_agente,
    rispondi_richiesta_commerciale_con_agente 
)
from order_validator import valida_ordine_estratto

def crea_nome_fonte_da_pdf(pdf_file):
    nome_file = os.path.basename(pdf_file)
    nome_senza_estensione = os.path.splitext(nome_file)[0]
    nome_senza_estensione = nome_senza_estensione.replace(" ", "_")

    return nome_senza_estensione


def scegli_cartella_output(esito_operativo):
    """
    Divide i JSON finali in cartelle diverse in base all'esito.
    """

    if esito_operativo == "ORDINE_VALIDATO":
        return f"{OUTPUT_PATH}/ORDINE_VALIDATO"

    else:
        return f"{OUTPUT_PATH}/RICHIESTA_REVISIONE"


def salva_json(dati, nome_file):
    """
    Salva il JSON nella cartella corretta:
    - ORDINE_VALIDATO
    - RICHIESTA_REVISIONE
    """

    esito_operativo = dati["esito_operativo"]

    cartella_output = scegli_cartella_output(esito_operativo)

    os.makedirs(cartella_output, exist_ok=True)

    file_path = f"{cartella_output}/{nome_file}"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(dati, file, ensure_ascii=False, indent=4)

    return file_path

def prepara_esito_non_ordine(classificazione, fonte, pdf_file):
    tipo = classificazione["tipo_richiesta"]

    if tipo == "RICHIESTA_QUOTAZIONE":
        azione = (
            "Richiesta quotazione: inoltrare al flusso commerciale "
            "per preparare una bozza di quotazione da listino."
        )

    elif tipo == "RICHIESTA_INFORMAZIONI":
        azione = (
            "Richiesta informazioni: inoltrare al flusso commerciale "
            "per preparare una bozza di risposta da knowledge base."
        )

    elif tipo == "NON_AUTOMATIZZABILE":
        azione = (
            "Richiesta non automatizzabile: inoltrare direttamente "
            "a operatore umano."
        )

    else:
        azione = "Caso non previsto: inoltrare a operatore umano."

    risultato = {
        "fonte": fonte,
        "pdf_file": pdf_file,
        "classificazione": classificazione,
        "esito_operativo": "DA_INVIARE_A_OPERATORE",
        "ordine": None,
        "validazione": None,
        "dettaglio_operatore": {
            "tipo_richiesta": tipo,
            "motivazione": classificazione.get("motivazione", ""),
            "confidence": classificazione.get("confidence", 0),
            "azione_successiva": azione
        }
    }

    return risultato

def stampa_esito_sintetico(risultato):
    fonte = risultato["fonte"]
    esito = risultato["esito_operativo"]
    classificazione = risultato["classificazione"]

    print("\n==============================")
    print("ESITO PDF:", fonte)
    print("==============================")
    print("Tipo richiesta:", classificazione["tipo_richiesta"])
    print("Esito operativo:", esito)

    if risultato["ordine"] is not None:
        ordine = risultato["ordine"]
        cliente = ordine["cliente"]
        testata = ordine["ordine"]
        righe = ordine["righe"]

        print("Cliente:", cliente.get("ragione_sociale", ""), "-", cliente.get("id_cliente", ""))
        print("Riferimento cliente:", testata.get("riferimento_cliente", ""))
        print("Data ordine:", testata.get("data_ordine", ""))
        print("Numero righe:", len(righe))

    if esito == "ORDINE_VALIDATO":
        print("Stato: ordine caricabile automaticamente.")

    elif esito == "RICHIESTA_REVISIONE":
        print("\nPROBLEMI TROVATI:")

        anomalie = risultato["validazione"]["anomalie"]

        for anomalia in anomalie:
            print(
                f"- [{anomalia['livello']}] "
                f"{anomalia['tipo']}: "
                f"{anomalia['messaggio']}"
            )

        print("\nAzione richiesta:")
        print("- Revisione operatore umano")

        if risultato.get("revisione_assistita") is not None:
            revisione = risultato["revisione_assistita"]

            print("\nAG-ReviewAssistant:")
            print("Riepilogo:", revisione.get("riepilogo", ""))

            problemi = revisione.get("problemi", [])

            if len(problemi) > 0:
                print("\nDomande / correzioni suggerite:")

                for problema in problemi:
                    print("-", problema.get("domanda_operatore", ""))

        if risultato.get("ordine_corretto_proposto") is not None:
            print("\nOrdine corretto proposto:")
            validazione_proposta = risultato.get("validazione_ordine_corretto_proposto")

            if validazione_proposta is not None:
                print("Stato proposta:", validazione_proposta["stato_validazione"])

                if validazione_proposta["stato_validazione"] == "VALIDATO":
                    print("La proposta dell'agente passerebbe la validazione Python.")
                else:
                    print("La proposta dell'agente richiede ancora controllo.")

    elif esito == "DA_INVIARE_A_OPERATORE":
        dettaglio = risultato["dettaglio_operatore"]

        print("\nRichiesta non processabile come ordine.")
        print("Motivo:", dettaglio["motivazione"])
        print("Azione:", dettaglio["azione_successiva"])

        if risultato.get("risposta_commerciale") is not None:
            risposta = risultato["risposta_commerciale"]

            print("\nAG-CommercialResponder:")
            print("Oggetto:", risposta.get("oggetto", ""))
            print("Azione:", risposta.get("azione_successiva", ""))

            criticita = risposta.get("criticita", [])

            if len(criticita) > 0:
                print("\nCriticità:")
                for item in criticita:
                    print("-", item.get("messaggio", ""))

def processa_pdf(
    pdf_file,
    clienti,
    articoli,
    ordini_storici,
    righe_ordini_storici
):
    fonte = crea_nome_fonte_da_pdf(pdf_file)

    print("\nProcesso PDF:", fonte)

    # 1. OCR
    dati_pdf = estrai_pdf_con_document_intelligence(pdf_file)
    print("OCR completato con Azure Document Intelligence")
    print("Caratteri testo OCR estratti:", len(dati_pdf["testo"]))
    print("Numero tabelle OCR estratte:", len(dati_pdf["tabelle"]))

    # 2. AGENTE ROUTER
    classificazione = classifica_richiesta_con_agente(dati_pdf)

    tipo_richiesta = classificazione["tipo_richiesta"]
    print("Tipo richiesta rilevato dal router:", tipo_richiesta)


    # 3. CASO ORDINE
    if tipo_richiesta == "ORDINE":
        ordine_json = estrai_ordine_con_agente(
            dati_pdf=dati_pdf,
            clienti=clienti,
            articoli=articoli,
            fonte=fonte
        )

        # 4. VALIDAZIONE PYTHON
        validazione = valida_ordine_estratto(
            ordine_json=ordine_json,
            clienti=clienti,
            articoli=articoli,
            ordini_storici=ordini_storici,
            righe_ordini_storici=righe_ordini_storici
        )

        if validazione["stato_validazione"] == "VALIDATO":
            esito_operativo = "ORDINE_VALIDATO"
            dettaglio_operatore = None

        else:
            esito_operativo = "RICHIESTA_REVISIONE"
            dettaglio_operatore = {
                "motivo": "Ordine con errori, valori mancanti o valori non concordi.",
                "azione": "Inviare ordine a operatore umano per revisione."
            }

        risultato = {
            "fonte": fonte,
            "pdf_file": pdf_file,
            "classificazione": classificazione,
            "esito_operativo": esito_operativo,
            "ordine": ordine_json,
            "validazione": validazione,
            "dettaglio_operatore": dettaglio_operatore
        }

    # 4. CASO NON ORDINE
    else:
        risultato = prepara_esito_non_ordine(
            classificazione=classificazione,
            fonte=fonte,
            pdf_file=pdf_file
        )

    if tipo_richiesta in ["RICHIESTA_QUOTAZIONE", "RICHIESTA_INFORMAZIONI"]:
        print("Analisi richiesta commerciale con AG-CommercialResponder...")

        risposta_commerciale = rispondi_richiesta_commerciale_con_agente(
            dati_pdf=dati_pdf,
            classificazione=classificazione,
            clienti=clienti,
            articoli=articoli,
            fonte=fonte
        )

        risultato["risposta_commerciale"] = risposta_commerciale

    else:
        risultato["risposta_commerciale"] = None

    # 5. SE L'ORDINE È IN REVISIONE, CHIAMIAMO AG-ReviewAssistant
    if risultato["esito_operativo"] == "RICHIESTA_REVISIONE" and risultato["ordine"] is not None:
        print("Analisi revisione con AG-ReviewAssistant...")

        revisione_assistita = analizza_revisione_con_agente(
            risultato=risultato,
            articoli=articoli,
            righe_ordini_storici=righe_ordini_storici
        )

        #risultato["ordine_originale_errato"] = risultato["ordine"]
        risultato["revisione_assistita"] = revisione_assistita

        ordine_corretto_proposto = revisione_assistita.get("ordine_corretto_proposto")

        risultato["ordine_corretto_proposto"] = ordine_corretto_proposto

        if ordine_corretto_proposto is not None:
            validazione_proposta = valida_ordine_estratto(
                ordine_json=ordine_corretto_proposto,
                clienti=clienti,
                articoli=articoli,
                ordini_storici=ordini_storici,
                righe_ordini_storici=righe_ordini_storici
            )

            risultato["validazione_ordine_corretto_proposto"] = validazione_proposta

        else:
            risultato["validazione_ordine_corretto_proposto"] = None

    else:
        #risultato["ordine_originale_errato"] = None
        risultato["revisione_assistita"] = None
        risultato["ordine_corretto_proposto"] = None
        risultato["validazione_ordine_corretto_proposto"] = None

    # 6. STAMPA SINTETICA
    stampa_esito_sintetico(risultato)

    # 7. SALVATAGGIO JSON COMPLETO
    nome_output = f"risultato_{fonte}.json"
    file_salvato = salva_json(risultato, nome_output)

    print("Risultato salvato in:", file_salvato)

    return risultato

def processa_tutti_i_pdf():
    clienti, articoli, ordini_storici, righe_ordini_storici = load_csv_files()

    risultati = []

    print("\nPDF trovati:")
    for pdf_file in PDF_FILES:
        print("-", pdf_file)

    if len(PDF_FILES) == 0:
        print("\nNessun PDF trovato.")
        return risultati

    for pdf_file in PDF_FILES:
        risultato = processa_pdf(
            pdf_file=pdf_file,
            clienti=clienti,
            articoli=articoli,
            ordini_storici=ordini_storici,
            righe_ordini_storici=righe_ordini_storici
        )

        risultati.append(risultato)

    stampa_riepilogo_finale(risultati)

    return risultati

def stampa_riepilogo_finale(risultati):
    print("\n==============================")
    print("RIEPILOGO FINALE")
    print("==============================")

    totale_validati = 0
    totale_revisione = 0
    totale_operatore = 0

    problematici = []

    for risultato in risultati:
        if risultato["esito_operativo"] == "ORDINE_VALIDATO":
            totale_validati += 1

        elif risultato["esito_operativo"] == "RICHIESTA_REVISIONE":
            totale_revisione += 1
            problematici.append(risultato)

        else:
            totale_operatore += 1
            problematici.append(risultato)

    print("PDF processati:", len(risultati))
    print("Ordini validati:", totale_validati)
    print("Ordini con richiesta revisione:", totale_revisione)
    print("Richieste non ordine da inviare a operatore:", totale_operatore)

    if len(problematici) > 0:
        print("\nORDINI / RICHIESTE DA CONTROLLARE:")

        for risultato in problematici:
            print("\n-", risultato["fonte"])
            print("  Esito:", risultato["esito_operativo"])

            if risultato["validazione"] is not None:
                for anomalia in risultato["validazione"]["anomalie"]:
                    print(
                        f"  - {anomalia['tipo']}: "
                        f"{anomalia['messaggio']}"
                    )

            else:
                dettaglio = risultato["dettaglio_operatore"]
                print("  - Motivo:", dettaglio["motivazione"])