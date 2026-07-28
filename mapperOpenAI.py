import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from config import (
    FOUNDRY_PROJECT_ENDPOINT,
    AG_REQUEST_ROUTER_NAME,
    AG_ORDER_EXTRACTOR_NAME,
    AG_COMMERCIAL_RESPONDER_NAME,
    AG_REVIEW_ASSISTANT_NAME
)

def log_token_usage(response, agent_name: str) -> dict:
    usage = response.usage
    log = {
        "agente": agent_name,
        "input_tokens": usage.input_tokens,
        "costo input $":usage.input_tokens*0.00000044,
        "output_tokens": usage.output_tokens,
        "costo output $":usage.output_tokens*0.00000176,
        "total_tokens": usage.total_tokens,
        "costo totale $": usage.input_tokens*0.00000044 + usage.output_tokens*0.00000176,
    }
    print(f"💵{agent_name}: {log['total_tokens']} token "
          f"(in: {log['input_tokens']}, out: {log['output_tokens']})"
          f"({log["costo input $"]} $ + {log['costo output $']} $ ={log['costo totale $']} $")
    return log

def crea_openai_client_foundry():

    project_client = AIProjectClient(
        endpoint=FOUNDRY_PROJECT_ENDPOINT,
        credential=DefaultAzureCredential()
    )

    return project_client.get_openai_client()

def estrai_json_da_testo(testo):
    """
    Gli agenti dovrebbero rispondere solo JSON.
    Se però restituiscono ```json ... ```, puliamo il testo.
    """

    testo = testo.strip()

    if testo.startswith("```json"):
        testo = testo.replace("```json", "").replace("```", "").strip()

    elif testo.startswith("```"):
        testo = testo.replace("```", "").strip()

    try:
        return json.loads(testo)

    except json.JSONDecodeError:
        raise ValueError(
            "L'agente non ha restituito JSON valido.\n"
            f"Risposta ricevuta:\n{testo}"
        )

def chiama_agente_foundry(nome_agente, payload):

    if nome_agente is None or str(nome_agente).strip() == "":
        raise ValueError("Nome agente mancante. Controlla il file .env e config.py")

    client = crea_openai_client_foundry()

    response = client.responses.create(
        extra_body={
            "agent_reference": {
                "name": nome_agente,
                "type": "agent_reference"
            }
        },
        input=json.dumps(payload, ensure_ascii=False)
    )

    token_log = log_token_usage(response, nome_agente)

    return estrai_json_da_testo(response.output_text)

def classifica_richiesta_con_agente(dati_pdf):
    """
    Chiama AG-RequestRouter.

    Input:
    - testo OCR
    - tabelle OCR

    Output atteso:
    {
        "tipo_richiesta": "ORDINE",
        "confidence": 0.98,
        "motivazione": "...",
        "azione_successiva": "..."
    }
    """

    payload = {
        "task": "classifica_richiesta",
        "testo_ocr": dati_pdf["testo"],
        "tabelle_ocr": dati_pdf["tabelle"]
    }

    return chiama_agente_foundry(
        nome_agente=AG_REQUEST_ROUTER_NAME,
        payload=payload
    )

def crea_lista_clienti_per_agente(clienti):
    lista = []

    for _, row in clienti.iterrows():
        lista.append({
            "id": row["id"],
            "ragione_sociale": row["ragione_sociale"],
            "partita_iva": row["partita_iva"],
            "email": row["email"]
        })

    return lista


def crea_lista_articoli_per_agente(articoli):
    lista = []

    for _, row in articoli.iterrows():
        lista.append({
            "codice": row["codice"],
            "descrizione": row["descrizione"],
            "categoria": row["categoria"],
            "unita_misura": row["unita_misura"],
            "prezzo_listino": float(row["prezzo_listino"])
        })

    return lista


def estrai_ordine_con_agente(dati_pdf, clienti, articoli, fonte):
    """
    Chiama AG-OrderExtractor.

    Input:
    - testo OCR
    - tabelle OCR
    - clienti ufficiali
    - articoli ufficiali

    Output:
    ordine JSON strutturato.
    """

    payload = {
        "task": "estrai_ordine",
        "fonte": fonte,
        "testo_ocr": dati_pdf["testo"],
        "tabelle_ocr": dati_pdf["tabelle"],
        "clienti_ufficiali": crea_lista_clienti_per_agente(clienti),
        "articoli_ufficiali": crea_lista_articoli_per_agente(articoli)
    }

    return chiama_agente_foundry(
        nome_agente=AG_ORDER_EXTRACTOR_NAME,
        payload=payload
    )

def crea_storico_rilevante_per_agente(ordine_json, righe_ordini_storici):
    """
    Prende solo le righe storiche degli articoli presenti nell'ordine.
    Così AG-ReviewAssistant non riceve tutto lo storico, ma solo quello utile.
    """

    if ordine_json is None:
        return []

    codici_articolo = []

    for riga in ordine_json.get("righe", []):
        codice = riga.get("codice_articolo", "")

        if str(codice).strip() != "" and codice not in codici_articolo:
            codici_articolo.append(codice)

    if len(codici_articolo) == 0:
        return []

    storico_filtrato = righe_ordini_storici[
        righe_ordini_storici["codice_articolo"].isin(codici_articolo)
    ]

    return storico_filtrato.to_dict(orient="records")


def analizza_revisione_con_agente(risultato, articoli, righe_ordini_storici):
    """
    Chiama AG-ReviewAssistant per analizzare un ordine in RICHIESTA_REVISIONE.

    L'agente non corregge automaticamente l'ordine originale.
    Produce:
    - analisi problemi
    - consigli operativi
    - ordine_corretto_proposto
    """

    payload = {
        "task": "analizza_revisione_e_proponi_correzione",
        "fonte": risultato["fonte"],
        "classificazione": risultato["classificazione"],
        "ordine_originale_errato": risultato["ordine"],
        "validazione": risultato["validazione"],
        "dettaglio_operatore": risultato["dettaglio_operatore"],
        "articoli_ufficiali": crea_lista_articoli_per_agente(articoli),
        "storico_righe_rilevante": crea_storico_rilevante_per_agente(
            ordine_json=risultato["ordine"],
            righe_ordini_storici=righe_ordini_storici
        ),
        "istruzione_importante": (
            "Restituisci anche ordine_corretto_proposto. "
            "Non modificare l'ordine originale. "
            "Se un dato manca e non può essere dedotto con certezza, lascialo vuoto."
        )
    }

    return chiama_agente_foundry(
        nome_agente=AG_REVIEW_ASSISTANT_NAME,
        payload=payload
    )

def rispondi_richiesta_commerciale_con_agente(
    dati_pdf,
    classificazione,
    clienti,
    articoli,
    fonte
):
    """
    Chiama AG-CommercialResponder per richieste non ordine:
    - RICHIESTA_QUOTAZIONE
    - RICHIESTA_INFORMAZIONI

    L'agente prepara una bozza operativa per l'operatore umano.
    """

    payload = {
        "task": "gestisci_richiesta_commerciale",
        "fonte": fonte,
        "tipo_richiesta": classificazione["tipo_richiesta"],
        "classificazione": classificazione,
        "testo_ocr": dati_pdf["testo"],
        "tabelle_ocr": dati_pdf["tabelle"],
        "clienti_ufficiali": crea_lista_clienti_per_agente(clienti),
        "articoli_ufficiali": crea_lista_articoli_per_agente(articoli),
        "istruzione_importante": (
            "Prepara solo una bozza per operatore umano. "
            "Non inviare risposta finale al cliente. "
            "Non inventare prezzi, certificazioni o disponibilità."
        )
    }

    return chiama_agente_foundry(
        nome_agente=AG_COMMERCIAL_RESPONDER_NAME,
        payload=payload
    )