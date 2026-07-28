from orchestrator import processa_tutti_i_pdf

def main():
    print("\n==============================")
    print("ORDER INTAKE SYSTEM")
    print("==============================")
    processa_tutti_i_pdf()


if __name__ == "__main__":
    main()


'''from revision_manager import rivalida_tutti_i_json_revisionati
    print("1 - Processa nuovi PDF")
    print("2 - Rivalida ordini revisionati")
    print("3 - Esegui entrambi")
    print("0 - Esci")

    scelta = input("\nScegli operazione: ")

    if scelta == "1":
        processa_tutti_i_pdf()

    elif scelta == "2":
        rivalida_tutti_i_json_revisionati()

    elif scelta == "3":
        processa_tutti_i_pdf()
        rivalida_tutti_i_json_revisionati()

    elif scelta == "0":
        print("Programma terminato.")

    else:
        print("Scelta non valida.")'''