def valore_mancante(valore):
    if valore is None:
        return True

    if str(valore).strip() == "":
        return True

    return False

def converti_float(valore):
    try:
        if valore is None:
            return None

        valore = str(valore).strip()
        valore = valore.replace(",", ".")

        return float(valore)

    except:
        return None

def aggiungi_anomalia(anomalie, livello, tipo, messaggio, azione):
    anomalie.append({
        "livello": livello,
        "tipo": tipo,
        "messaggio": messaggio,
        "azione": azione
    })

def testo_contiene_parole_sospette(testo):
    if testo is None:
        return False

    testo = str(testo).lower()

    parole_sospette = [
        "da confermare",
        "prezzo da confermare",
        "se diverso dal listino",
        "in alternativa",
        "alternativa",
        "certificata",
        "certificato",
        "certificazione",
        "conformità",
        "conformita",
        "verificare",
        "verifica",
        "disponibilità",
        "disponibilita",
        "urgente",
        "non standard",
        "fuori standard",
        "versione speciale",
        "come da accordi",
        "accordi quadro",
        "condizioni particolari"
    ]

    for parola in parole_sospette:
        if parola in testo:
            return True

    return False


def valida_note_ordine(ordine_json, anomalie):
    ordine = ordine_json["ordine"]
    note_ordine = ordine.get("note_ordine", "")

    if testo_contiene_parole_sospette(note_ordine):
        aggiungi_anomalia(
            anomalie,
            "WARNING",
            "NOTE_ORDINE_DA_REVISIONARE",
            f"Le note ordine contengono condizioni da verificare: {note_ordine}",
            "Richiesta revisione: condizioni commerciali, tecniche o logistiche da controllare."
        )


def valida_note_righe(ordine_json, anomalie):
    righe = ordine_json["righe"]

    for index, riga in enumerate(righe, start=1):
        codice_articolo = riga.get("codice_articolo", "")
        note_riga = riga.get("note_riga", "")

        if testo_contiene_parole_sospette(note_riga):
            aggiungi_anomalia(
                anomalie,
                "WARNING",
                "NOTE_RIGA_DA_REVISIONARE",
                (
                    f"Riga {index}, articolo {codice_articolo}: "
                    f"nota da verificare: {note_riga}"
                ),
                "Richiesta revisione: variante tecnica, prezzo o condizione speciale da controllare."
            )

def valida_cliente(ordine_json, clienti, anomalie):
    cliente = ordine_json["cliente"]

    id_cliente = cliente.get("id_cliente", "")
    partita_iva = cliente.get("partita_iva", "")
    email = cliente.get("email", "")

    if valore_mancante(id_cliente):
        aggiungi_anomalia(
            anomalie,
            "ERRORE",
            "CLIENTE_MANCANTE",
            "Il PDF non contiene un id_cliente valido.",
            "Richiesta revisione operatore."
        )
        return

    cliente_trovato = clienti[clienti["id"] == id_cliente]

    if cliente_trovato.empty:
        aggiungi_anomalia(
            anomalie,
            "ERRORE",
            "CLIENTE_NON_TROVATO",
            f"Il cliente {id_cliente} non esiste in clienti.csv.",
            "Richiesta revisione operatore."
        )
        return

    cliente_catalogo = cliente_trovato.iloc[0]

    if not valore_mancante(partita_iva):
        if str(partita_iva).strip() != str(cliente_catalogo["partita_iva"]).strip():
            aggiungi_anomalia(
                anomalie,
                "WARNING",
                "PARTITA_IVA_NON_CONCORDE",
                (
                    f"Cliente {id_cliente}: partita IVA PDF {partita_iva}, "
                    f"partita IVA anagrafica {cliente_catalogo['partita_iva']}."
                ),
                "Richiesta revisione: dati cliente non concordi."
            )

    if not valore_mancante(email):
        if str(email).strip().lower() != str(cliente_catalogo["email"]).strip().lower():
            aggiungi_anomalia(
                anomalie,
                "WARNING",
                "EMAIL_CLIENTE_NON_CONCORDE",
                (
                    f"Cliente {id_cliente}: email PDF {email}, "
                    f"email anagrafica {cliente_catalogo['email']}."
                ),
                "Richiesta revisione: email cliente non concorde."
            )

def valida_testata_ordine(ordine_json, ordini_storici, anomalie):
    ordine = ordine_json["ordine"]

    data_ordine = ordine.get("data_ordine", "")
    riferimento_cliente = ordine.get("riferimento_cliente", "")

    if valore_mancante(data_ordine):
        aggiungi_anomalia(
            anomalie,
            "ERRORE",
            "DATA_ORDINE_MANCANTE",
            "La data ordine è mancante.",
            "Richiesta revisione operatore."
        )

    if valore_mancante(riferimento_cliente):
        aggiungi_anomalia(
            anomalie,
            "ERRORE",
            "RIFERIMENTO_CLIENTE_MANCANTE",
            "Il riferimento ordine cliente è mancante.",
            "Richiesta revisione operatore."
        )
        return

    if "riferimento_cliente" in ordini_storici.columns:
        duplicato = ordini_storici[
            ordini_storici["riferimento_cliente"].astype(str) == str(riferimento_cliente)
        ]

        if not duplicato.empty:
            aggiungi_anomalia(
                anomalie,
                "WARNING",
                "RIFERIMENTO_CLIENTE_GIA_PRESENTE",
                f"Il riferimento cliente {riferimento_cliente} è già presente nello storico.",
                "Richiesta revisione: possibile ordine duplicato."
            )


def valida_riferimento_commerciale(ordine_json, anomalie):
    ordine = ordine_json["ordine"]
    riferimento_cliente = ordine.get("riferimento_cliente", "")

    riferimento_lower = str(riferimento_cliente).lower()

    if riferimento_lower.startswith("off") or "offerta" in riferimento_lower:
        aggiungi_anomalia(
            anomalie,
            "WARNING",
            "RIFERIMENTO_SEMBRA_OFFERTA",
            (
                f"Il riferimento cliente '{riferimento_cliente}' sembra riferirsi "
                "a un'offerta/preventivo, non a un numero ordine cliente."
            ),
            "Richiesta revisione: verificare se è ordine confermato o riferimento a offerta."
        )

def trova_articolo_catalogo(codice_articolo, articoli):
    articolo_catalogo = articoli[articoli["codice"] == codice_articolo]

    if articolo_catalogo.empty:
        return None

    return articolo_catalogo.iloc[0]


def controlla_mapping_articolo(index, riga, anomalie):
    codice_articolo = riga.get("codice_articolo", "")
    codice_originale_pdf = riga.get("codice_originale_pdf", "")

    if not valore_mancante(codice_originale_pdf):
        if str(codice_originale_pdf).strip() != str(codice_articolo).strip():
            aggiungi_anomalia(
                anomalie,
                "WARNING",
                "MAPPING_ARTICOLO_DA_VERIFICARE",
                (
                    f"Riga {index}: codice originale PDF '{codice_originale_pdf}', "
                    f"codice mappato '{codice_articolo}'."
                ),
                "Richiesta revisione: mapping articolo da verificare."
            )


def controlla_prezzo_listino(
    index,
    codice_articolo,
    prezzo_unitario,
    prezzo_listino,
    anomalie
):
    if prezzo_unitario is None:
        return

    differenza = abs(prezzo_unitario - prezzo_listino)

    if differenza > 0.01:
        aggiungi_anomalia(
            anomalie,
            "WARNING",
            "PREZZO_NON_CONCORDE_CON_LISTINO",
            (
                f"Riga {index}, articolo {codice_articolo}: "
                f"prezzo PDF {prezzo_unitario}, prezzo listino {prezzo_listino}."
            ),
            "Richiesta revisione: valori non concordi con il catalogo articoli."
        )


def controlla_storico(
    index,
    codice_articolo,
    quantita,
    prezzo_unitario,
    righe_ordini_storici,
    anomalie
):
    righe_storiche_articolo = righe_ordini_storici[
        righe_ordini_storici["codice_articolo"] == codice_articolo
    ]

    if righe_storiche_articolo.empty:
        aggiungi_anomalia(
            anomalie,
            "WARNING",
            "ARTICOLO_SENZA_STORICO",
            f"Articolo {codice_articolo} presente a catalogo ma senza storico ordini.",
            "Richiesta controllo operatore."
        )
        return

    if quantita is not None:
        quantita_massima_storica = float(righe_storiche_articolo["quantita"].max())

        if quantita > quantita_massima_storica * 3:
            aggiungi_anomalia(
                anomalie,
                "WARNING",
                "QUANTITA_NON_CONVINCENTE",
                (
                    f"Riga {index}, articolo {codice_articolo}: "
                    f"quantità PDF {quantita}, massimo storico {quantita_massima_storica}."
                ),
                "Richiesta revisione: quantità molto superiore allo storico."
            )

    if prezzo_unitario is not None:
        prezzo_min_storico = float(righe_storiche_articolo["prezzo_unitario"].min())
        prezzo_max_storico = float(righe_storiche_articolo["prezzo_unitario"].max())

        limite_basso = prezzo_min_storico * 0.85
        limite_alto = prezzo_max_storico * 1.15

        if prezzo_unitario < limite_basso or prezzo_unitario > limite_alto:
            aggiungi_anomalia(
                anomalie,
                "WARNING",
                "PREZZO_NON_CONCORDE_CON_STORICO",
                (
                    f"Riga {index}, articolo {codice_articolo}: "
                    f"prezzo PDF {prezzo_unitario}, "
                    f"range storico {prezzo_min_storico} - {prezzo_max_storico}."
                ),
                "Richiesta revisione: valori non concordi con lo storico."
            )


def valida_righe_ordine(ordine_json, articoli, righe_ordini_storici, anomalie):
    righe = ordine_json["righe"]

    if len(righe) == 0:
        aggiungi_anomalia(
            anomalie,
            "ERRORE",
            "NESSUNA_RIGA_ORDINE",
            "L'ordine non contiene righe articolo.",
            "Richiesta revisione operatore."
        )
        return

    for index, riga in enumerate(righe, start=1):
        codice_articolo = riga.get("codice_articolo", "")
        descrizione_articolo = riga.get("descrizione_articolo", "")
        quantita = converti_float(riga.get("quantita"))
        prezzo_unitario = converti_float(riga.get("prezzo_unitario"))

        if valore_mancante(codice_articolo):
            aggiungi_anomalia(
                anomalie,
                "ERRORE",
                "CODICE_ARTICOLO_MANCANTE",
                f"Riga {index}: codice articolo mancante.",
                "Richiesta revisione operatore."
            )
            continue

        controlla_mapping_articolo(
            index=index,
            riga=riga,
            anomalie=anomalie
        )

        if valore_mancante(descrizione_articolo):
            aggiungi_anomalia(
                anomalie,
                "WARNING",
                "DESCRIZIONE_ARTICOLO_MANCANTE",
                f"Riga {index}, articolo {codice_articolo}: descrizione mancante.",
                "Richiesta revisione operatore."
            )

        if quantita is None:
            aggiungi_anomalia(
                anomalie,
                "ERRORE",
                "QUANTITA_NON_VALIDA",
                f"Riga {index}, articolo {codice_articolo}: quantità mancante o non numerica.",
                "Richiesta revisione operatore."
            )

        elif quantita <= 0:
            aggiungi_anomalia(
                anomalie,
                "ERRORE",
                "QUANTITA_NON_VALIDA",
                f"Riga {index}, articolo {codice_articolo}: quantità {quantita} non valida.",
                "Richiesta revisione operatore."
            )

        if prezzo_unitario is None:
            aggiungi_anomalia(
                anomalie,
                "ERRORE",
                "PREZZO_NON_VALIDO",
                f"Riga {index}, articolo {codice_articolo}: prezzo mancante o non numerico.",
                "Richiesta revisione operatore."
            )

        elif prezzo_unitario <= 0:
            aggiungi_anomalia(
                anomalie,
                "ERRORE",
                "PREZZO_NON_VALIDO",
                f"Riga {index}, articolo {codice_articolo}: prezzo {prezzo_unitario} non valido.",
                "Richiesta revisione operatore."
            )

        articolo_catalogo = trova_articolo_catalogo(codice_articolo, articoli)

        if articolo_catalogo is None:
            aggiungi_anomalia(
                anomalie,
                "ERRORE",
                "ARTICOLO_NON_TROVATO",
                f"Riga {index}: articolo {codice_articolo} non presente in articoli.csv.",
                "Richiesta revisione operatore."
            )
            continue

        prezzo_listino = float(articolo_catalogo["prezzo_listino"])

        controlla_prezzo_listino(
            index=index,
            codice_articolo=codice_articolo,
            prezzo_unitario=prezzo_unitario,
            prezzo_listino=prezzo_listino,
            anomalie=anomalie
        )

        controlla_storico(
            index=index,
            codice_articolo=codice_articolo,
            quantita=quantita,
            prezzo_unitario=prezzo_unitario,
            righe_ordini_storici=righe_ordini_storici,
            anomalie=anomalie
        )

def anomalia_bloccante(anomalia):
    """
    Decide se una anomalia deve bloccare l'ordine
    e mandarlo in revisione umana.

    Non tutte le anomalie devono bloccare.
    Alcune sono solo segnalazioni operative.
    """

    tipo = anomalia["tipo"]
    livello = anomalia["livello"]

    # Tutti gli errori veri bloccano
    if livello == "ERRORE":
        return True

    # Warning che devono bloccare davvero
    tipi_bloccanti = [
        "PREZZO_NON_CONCORDE_CON_LISTINO",
        "PREZZO_NON_CONCORDE_CON_STORICO",
        "QUANTITA_NON_CONVINCENTE",
        "ARTICOLO_NON_TROVATO",
        "CLIENTE_NON_TROVATO",
        "PARTITA_IVA_NON_CONCORDE",
        "EMAIL_CLIENTE_NON_CONCORDE",
        "MAPPING_ARTICOLO_DA_VERIFICARE"
    ]

    if tipo in tipi_bloccanti:
        return True

    return False


def valida_ordine_estratto(
    ordine_json,
    clienti,
    articoli,
    ordini_storici,
    righe_ordini_storici
):
    anomalie = []

    valida_cliente(
        ordine_json=ordine_json,
        clienti=clienti,
        anomalie=anomalie
    )

    valida_testata_ordine(
        ordine_json=ordine_json,
        ordini_storici=ordini_storici,
        anomalie=anomalie
    )

    valida_righe_ordine(
        ordine_json=ordine_json,
        articoli=articoli,
        righe_ordini_storici=righe_ordini_storici,
        anomalie=anomalie
    )

    anomalie_bloccanti = []

    for anomalia in anomalie:
        if anomalia_bloccante(anomalia):
            anomalie_bloccanti.append(anomalia)

    if len(anomalie_bloccanti) > 0:
        stato_validazione = "RICHIESTA_REVISIONE"

    elif len(anomalie) > 0:
        stato_validazione = "VALIDATO_CON_SEGNALAZIONI"

    else:
        stato_validazione = "VALIDATO"

    return {
        "stato_validazione": stato_validazione,
        "numero_anomalie": len(anomalie),
        "numero_anomalie_bloccanti": len(anomalie_bloccanti),
        "anomalie": anomalie,
        "anomalie_bloccanti": anomalie_bloccanti
    }