from genera_tabella import crea_tabella

if __name__ == "__main__":
    # Define the output path for the PDF
    output_path = "scheda_oraria_operatori_test.pdf"

    # Dati da inviare alla funzione
    mese = 9  # Ottobre come numero
    anno = 2024
    pattern_settimanale = {
        0: ["08:00 - 14:00","14:00 - 18:00", ],  # Lunedì
        1: ["08:00 - 12:00", "14:00 - 18:00"],  # Martedì
        2: ["00:00 - 21:30"],                    # Mercoledì
        3: [],                                   # Giovedì (codice eccezione)
        4: ["13:00 - 5:00"],                    # Venerdì
        5: [],                                   # Sabato (codice eccezione)
        6: []                                     # Domenica
    }
    eccezioni = {
        3: ["FE"],  # Codice eccezione per il giorno 3 (giovedì)
        5: ["ST"],  # Codice eccezione per il giorno 5 (sabato)
        10: ["10:00 - 12:00", "14:00 - 16:00"],  # Esempio di turni con codice eccezione (non mescolare)
    }
    nome_lavoratore = "Francesca Porcedda"
    persona_assistita = "Teodolinda Massa"
    comune = "Serrenti"
    attivita = "A1: igiene personale"
    servizio = "SAD"

    # Invoca la funzione con i dati
    crea_tabella(output_path, mese, anno, pattern_settimanale, eccezioni, nome_lavoratore, persona_assistita, comune, attivita, servizio)

    print(f"PDF '{output_path}' creato con successo.")
