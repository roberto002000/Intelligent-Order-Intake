import os
from dotenv import load_dotenv
import glob
import pandas as pd

load_dotenv("ProjectWork/.env")

AZ_DOCINT_ENDPOINT = os.getenv("AZ_DOCINT_ENDPOINT")
AZ_DOCINT_KEY = os.getenv("AZ_DOCINT_KEY")
FOUNDRY_OPEN_AI_ENDPOINT = os.getenv("FOUNDRY_OPEN_AI_ENDPOINT")
FOUNDRY_PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
FOUNDRY_API_KEY = os.getenv("FOUNDRY_API_KEY")
FOUNDRY_MODEL_NAME = os.getenv("FOUNDRY_MODEL_NAME")

AG_REQUEST_ROUTER_NAME = os.getenv("AG_REQUEST_ROUTER_NAME")
AG_ORDER_EXTRACTOR_NAME = os.getenv("AG_ORDER_EXTRACTOR_NAME")
AG_COMMERCIAL_RESPONDER_NAME = os.getenv("AG_COMMERCIAL_RESPONDER_NAME")
AG_REVIEW_ASSISTANT_NAME = os.getenv("AG_REVIEW_ASSISTANT_NAME")

DATA_PATH = "/Users/bengala/Desktop/materialiprogetto"

CLIENTI_FILE = f"{DATA_PATH}/clienti.csv"
ARTICOLI_FILE = f"{DATA_PATH}/articoli.csv"
ORDINI_STORICI_FILE = f"{DATA_PATH}/ordini_storici.csv"
RIGHE_ORDINI_STORICI_FILE = f"{DATA_PATH}/righe_ordini_storici.csv"
PDF_FILES = glob.glob(f"{DATA_PATH}/*.pdf")

# CARTELLA OUTPUT

OUTPUT_PATH = "/Users/bengala/Desktop/COrso/AI-900/ProjectWork/output"

ORDINI_FINALI_FILE = f"{OUTPUT_PATH}/ordini_finali.csv"
RIGHE_ORDINI_FINALI_FILE = f"{OUTPUT_PATH}/righe_ordini_finali.csv"
CLIENTI_FINALI_FILE = f"{OUTPUT_PATH}/clienti_finali.csv"
ARTICOLI_FINALI_FILE = f"{OUTPUT_PATH}/articoli_finali.csv"

def test_config():
    print("AZ_DOCINT_ENDPOINT:", AZ_DOCINT_ENDPOINT is not None)
    print("AZ_DOCINT_KEY:", AZ_DOCINT_KEY is not None)

    print("FOUNDRY_OPEN_AI_ENDPOINT:", FOUNDRY_OPEN_AI_ENDPOINT is not None)
    print("FOUNDRY_PROJECT_ENDPOINT:", FOUNDRY_PROJECT_ENDPOINT is not None)
    print("FOUNDRY_API_KEY:", FOUNDRY_API_KEY is not None)
    print("FOUNDRY_MODEL_NAME:", FOUNDRY_MODEL_NAME)

    print("\nFile dati:")
    print("Clienti:", CLIENTI_FILE)
    print("Articoli:", ARTICOLI_FILE)
    print("Ordini storici:", ORDINI_STORICI_FILE)
    print("Righe ordini storici:", RIGHE_ORDINI_STORICI_FILE)
    print("PDF:", PDF_FILES)

def load_csv_files():
    clienti = pd.read_csv(CLIENTI_FILE)
    articoli = pd.read_csv(ARTICOLI_FILE)
    ordini_storici = pd.read_csv(ORDINI_STORICI_FILE)
    righe_ordini_storici = pd.read_csv(RIGHE_ORDINI_STORICI_FILE)

    return clienti, articoli, ordini_storici, righe_ordini_storici


def test_load_data():
    clienti, articoli, ordini_storici, righe_ordini_storici = load_csv_files()

    print("\n--- CLIENTI ---")
    print(clienti.head())
    print(clienti.columns)

    print("\n--- ARTICOLI ---")
    print(articoli.head())
    print(articoli.columns)

    print("\n--- ORDINI STORICI ---")
    print(ordini_storici.head())
    print(ordini_storici.columns)

    print("\n--- RIGHE ORDINI STORICI ---")
    print(righe_ordini_storici.head())
    print(righe_ordini_storici.columns)

    print("\n--- PDF ---")
    print("PDF:", PDF_FILES)

if __name__ == "__main__":
    test_config()
    test_load_data()